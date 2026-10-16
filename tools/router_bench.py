"""Benchmark for the PowerLab router (docs/powerlab-router-plan.md).

Strips the unlocked tracks of a board's Default-class nets, routes them again with the
router in the installed kicad MCP checkout, and prints one line per connection plus a
JSON summary: routed/left per group, time, search nodes, retries, new DRC errors
(kicad-cli, against the stripped board), track length and vias.

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/router_bench.py <board.kicad_pcb> <out.kicad_pcb> [nets,comma,separated] [grid pitch mm]

The board's .kicad_pro and .kicad_dru are copied next to the output, so the router and
DRC use the same custom rules. Costs can be set with the environment variables TURN, RUN
(min straight cells between turns), VIA, NODES (node limit per search), ORDER
("bus", "length" or "constrained"), RIPUP (1/0), FINISH (1/0, the shortcut pass) and LAYERS
(cost factor per copper layer, top first, e.g. "1.3,1.0").
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.environ["LOCALAPPDATA"], "PowerLabKiCadAssistant", "KiCAD-MCP-Server", "python"))
import pcbnew  # noqa: E402
from commands.powerlab_router.router import Router  # noqa: E402
from commands.powerlab_router.search import Costs  # noqa: E402
from commands.route_cleanup import Drc  # noqa: E402

CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"


def main(src, out, only=None, pitch=0.1):
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
        if os.path.isfile(os.path.splitext(src)[0] + ext):
            for dst in (stripped, out):
                shutil.copy(os.path.splitext(src)[0] + ext, os.path.splitext(dst)[0] + ext)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(stripped)
    b = pcbnew.LoadBoard(stripped)
    drc = Drc(stripped, CLI)
    base = drc.errors(b)

    env = os.environ.get
    costs = Costs(turn=float(env("TURN", "1.5")), via=float(env("VIA", "4.0")), min_run=int(env("RUN", "2")),
                  layer_factor=dict(enumerate(float(f) for f in env("LAYERS", "1.0,1.2").split(","))),
                  max_nodes=int(env("NODES", "1000000")), weight=float(env("WEIGHT", "1.0")))
    router = Router(b, pitch=pitch, costs=costs, order=env("ORDER", "bus"), ripup=env("RIPUP", "1") == "1",
                    finish=env("FINISH", "1") == "1")

    def log(r):
        print(r["net"], r["connection"], r["group"], r["event"], r.get("nodes"), r.get("seconds"))

    report = router.run(nets, log=log)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(out)
    after = Drc(out, CLI)
    new = after.errors(pcbnew.LoadBoard(out)) - base
    kinds = {}
    for k, _ in new:
        kinds[k] = kinds.get(k, 0) + 1
    length = sum(pcbnew.ToMM(t.GetLength()) for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname() in nets)
    vias = sum(1 for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() in nets)
    report.pop("connections_list")
    report.update(pitch=pitch, new_drc_errors=kinds, track_mm=round(length, 1), vias=vias)
    print(json.dumps(report, indent=1))
    drc.close()
    after.close()


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3].split(",") if len(a) > 3 and a[3] else None, float(a[4]) if len(a) > 4 else 0.1)
