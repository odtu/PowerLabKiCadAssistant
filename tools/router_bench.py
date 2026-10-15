"""Benchmark for the PowerLab router (docs/powerlab-router-plan.md, milestone 0 onwards).

Strips the unlocked tracks of a board's Default-class nets, routes them again with the
router in the installed kicad MCP checkout, and prints one line per connection plus a
JSON summary: routed/failed, time, search nodes, exact-check violations, new DRC errors
(kicad-cli, against the stripped board), track length and vias.

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/router_bench.py <board.kicad_pcb> <out.kicad_pcb> [nets,comma,separated] [grid pitch mm]

The board's .kicad_pro and .kicad_dru are copied next to the output. Costs can be set with
the environment variables TURN, RUN (min straight cells between turns) and RES (cost of
crossing another unrouted pin's escape lane; 0 = off). Clearance rules from .kicad_dru are
read only in the form "pads of footprints X, Y: clearance N" (milestone 0).
"""
import json, math, os, shutil, sys, time
mcp = os.path.join(os.environ["LOCALAPPDATA"], "PowerLabKiCadAssistant", "KiCAD-MCP-Server", "python")
sys.path.insert(0, mcp)
import pcbnew
from commands.powerlab_router.model import RouterBoard
from commands.powerlab_router.search import Costs
from commands.route_cleanup import Drc

src, out = sys.argv[1], sys.argv[2]
only = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else None
pitch = float(sys.argv[4]) if len(sys.argv) > 4 else 0.1
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
b = pcbnew.LoadBoard(src)
ns = b.GetDesignSettings().m_NetSettings
nets = sorted({p.GetNetname() for fp in b.GetFootprints() for p in fp.Pads()
               if p.GetNetname() and ns.GetEffectiveNetClass(p.GetNetname()).GetName() == "Default"})
if only:
    nets = [n for n in nets if n in only]
for t in list(b.GetTracks()):
    if t.GetNetname() in nets and not t.IsLocked():
        b.Delete(t)
stripped = out.replace(".kicad_pcb", "_stripped.kicad_pcb")
for ext in (".kicad_pro", ".kicad_dru"):
    shutil.copy(os.path.splitext(src)[0] + ext, os.path.splitext(stripped)[0] + ext)
    shutil.copy(os.path.splitext(src)[0] + ext, os.path.splitext(out)[0] + ext)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(stripped)
b = pcbnew.LoadBoard(stripped)
drc = Drc(stripped, CLI)
base = drc.errors(b)

t_all = time.time()
import re
dru = os.path.splitext(src)[0] + ".kicad_dru"
pad_clr = {}
if os.path.isfile(dru):  # spike: only "pads of footprints X, Y: clearance N" rules
    for cond, val in re.findall(r"condition \"([^\"]*)\"\)\s*\(constraint clearance \(min ([0-9.]+)mm\)", open(dru).read()):
        if "A.Type == 'Pad'" in cond:
            for ref in re.findall(r"memberOfFootprint\('([^']+)'\)", cond):
                pad_clr[ref] = float(val)
print("pad clearance overrides", pad_clr)
rb = RouterBoard(b, pitch=pitch, pad_clearance=pad_clr)
TURN = float(os.environ.get("TURN", "0.4")); RUN = int(os.environ.get("RUN", "2")); RES = float(os.environ.get("RES", "0"))
costs = Costs(turn=TURN, via=2.0, layer_factor={1: 1.2}, min_run=RUN, reserved=RES)
print("costs: turn", TURN, "min_run", RUN, "reserved", RES)

def mst(pads):
    pts = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for p in pads]
    inside, edges = {0}, []
    while len(inside) < len(pads):
        best = min(((math.dist(pts[i], pts[j]), i, j) for i in inside for j in range(len(pads)) if j not in inside))
        edges.append((best[1], best[2], best[0])); inside.add(best[2])
    return edges

jobs = []
for net in nets:
    pads = [p for p in rb.pads if p.GetNetname() == net]
    if len(pads) >= 2:
        e = mst(pads)
        jobs.append((sum(x[2] for x in e), net, pads, e))
jobs.sort(key=lambda j: j[0])
rows, raster_s, search_s, total_nodes, routed, failed, exact_bad = [], 0.0, 0.0, 0, 0, 0, 0
todo = [j[1] for j in jobs]
for _len, net, pads, edges in jobs:
    todo.remove(net)
    t0 = time.time(); blocked, via_ok = rb.obstacles(net)
    reserved = rb.reserve([p for p in rb.pads if p.GetNetname() in todo], net) if RES > 0 else None
    rt = time.time() - t0; raster_s += rt
    for i, j, d in edges:
        geo, info = rb.route(net, pads[i], pads[j], blocked, via_ok, costs, reserved=reserved)
        search_s += info["seconds"]; total_nodes += info["nodes"]
        name = f"{pads[i].GetParentFootprint().GetReference()}.{pads[i].GetNumber()}-{pads[j].GetParentFootprint().GetReference()}.{pads[j].GetNumber()}"
        if geo is None:
            failed += 1
            rows.append((net, name, round(d, 1), info.get("fail"), info["lanes"], info["nodes"], info["seconds"]))
            continue
        pieces, vias = geo
        items = rb.add(net, pieces, vias)
        bad = rb.violations(net, items)
        retries = 0
        for extra in (0.05, 0.1):
            if not bad:
                break
            retries += 1
            rb.remove(items); items = []
            t1 = time.time(); bl2, vo2 = rb.obstacles(net, extra); raster_s += time.time() - t1
            geo, info2 = rb.route(net, pads[i], pads[j], bl2, vo2, costs, reserved=reserved)
            search_s += info2["seconds"]; total_nodes += info2["nodes"]
            if geo is None:
                bad = None
                break
            items = rb.add(net, *geo)
            bad = rb.violations(net, items)
        if bad is None:
            failed += 1
            rows.append((net, name, round(d, 1), "no path with margin", retries))
            continue
        exact_bad += len(bad)
        routed += 1
        rows.append((net, name, round(d, 1), "ok", len(geo[1]), info["nodes"], info["seconds"], info.get("window_mm"), "retries", retries, "left", len(bad)))
total = time.time() - t_all
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
after = Drc(out, CLI)
errs = after.errors(pcbnew.LoadBoard(out))
new = errs - base
kinds = {}
for k, _ in new:
    kinds[k] = kinds.get(k, 0) + 1
for r in rows:
    print(*r)
L = sum(pcbnew.ToMM(t.GetLength()) for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() in nets)
V = sum(1 for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() in nets)
print(json.dumps({"pitch": pitch, "connections": routed + failed, "routed": routed, "failed": failed,
                  "seconds_total": round(total, 1), "raster_s": round(raster_s, 1), "search_s": round(search_s, 1),
                  "nodes": total_nodes, "exact_violations": exact_bad, "new_drc_errors": kinds,
                  "track_mm": round(L, 1), "vias": V}, indent=1))
drc.close(); after.close()
