"""Bank score of a routed board: one number for "how good is this routing", to compare
router runs with each other and with hand routing (step 1 of the bank idea: the score is the
referee before any router change uses it).

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/route_bank.py <board.kicad_pcb> [<board2> ...]
      [--nets-from <board>] [--schematic <sch>] [--pours GND,GNDA] [--json]

The nets scored are the ones powerlab_route would route on --nets-from (default: the first
board), so every board is scored on the same joins. Each net's importance comes from the
routing plan (plan.py priority 0..3, from the schematic's netlist), weight = 1 + priority.

Per net, with n pads in g connected groups (KiCad's connectivity, pours included):
  joined = n - g, open = g - 1
  detour = track length / (octilinear minimum spanning tree of its pads, times joined/(n-1))
  earned = JOIN * weight * joined / max(1, detour)     (a straight join earns JOIN * weight)
  lost   = FAIL * weight * open                        (an open join costs what was tried)
Then for the whole board:
  - VIA per via (energy spent changing floors),
  - STYLE x KIND per check_routing finding: a detour weighs 3, an off-angle segment or sharp
    corner 1, a kink 0.5, an off-centre pad entry 0.25,
  - POUR per mm2 of pour cut off from its largest piece (pieces under 1 mm2 not counted),
  - LOOP per mm2 of gate-loop area (gate track to its return, loop_area.py from the router
    bench, when it and the schematic's netlist are there).
bank = earned - lost - vias - style - pour - loop.
New DRC errors are a gate, not a weight: a router result whose run folder has a report.json
with new_drc_errors gets "gated": true, and best-of picks rank by (new DRC errors, -bank):
the fewest new errors first (TestPCB2's runs all leave 1-3 starved thermals, which
powerlab_route's take_out handles, so skipping them all would pick nothing).
Weights can be changed for one run: --w pour=1,loop=0.5,style=0
"""
import json
import math
import os
import sys

MCP = os.path.join(os.environ["LOCALAPPDATA"], "PowerLabKiCadAssistant", "KiCAD-MCP-Server", "python")
sys.path.insert(0, MCP)
import pcbnew  # noqa: E402

# Weights set 2026-11-21 from the user's choice in 8 blind pairs of sf-motion router results,
# whole board and close-ups (calib-map.json, calib2-map.json in the router bench). Without GATE,
# all 8 agree only with vias 6, style 6, loop 3 and margins of 13-35 points; the user's reasons
# ("the gate track wanders left and right") pointed at gate-net detour, and with GATE = 100 all 8
# agree with margins of 45+. Refit with unrouted gate loops counted (LOOP_MISSING): via 2, style 6,
# loop 4, gate 150, pour 0.1, margin 58 on the closest pair. Treat differences under ~50 as a tie.
# Reported, not weighted yet: vias at fine-pitch ICs, stranded priority-3 pins, loop per pair.
JOIN = 10.0     # points for a straight join of weight 1
FAIL = 5.0      # points an open join takes out of the bank, per weight
VIA = 2.0       # points per via
STYLE = 6.0     # scale for the check_routing findings, weighted by kind (KIND)
KIND = {"detour": 3.0, "off_angle": 1.0, "corner": 1.0, "kink": 0.5, "pad_entry": 0.25, "solid_gnd": 1.0}
POUR = 0.1      # points per mm2 of cut-off pour
SLIVER = 1.0    # mm2: pour pieces smaller than this don't count
LOOP = 4.0      # points per mm2 of gate-loop area
LOOP_MISSING = 10.0  # mm2 counted for a gate loop that isn't routed (its open joins already cost FAIL;
                     # the user's 8 choices allow at most ~10, 20+ contradicts them)
GATE = 150.0    # points per unit of excess detour (detour - 1) of each gate net (plan role "gate")
FINE_PITCH = 0.65  # mm: a part with 16+ pads this close is a fine-pitch IC
BENCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sandbox", "router2-bench")

T = pcbnew.ToMM


def _octi(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def mst_length(points):
    """Prim's minimum spanning tree over the points, octilinear distance."""
    if len(points) < 2:
        return 0.0
    best = {i: _octi(points[0], p) for i, p in enumerate(points[1:], 1)}
    total = 0.0
    while best:
        i = min(best, key=best.get)
        total += best.pop(i)
        for j in best:
            best[j] = min(best[j], _octi(points[i], points[j]))
    return total


def scoped_nets(path, pours):
    from commands.powerlab_route import pick_nets
    b = pcbnew.LoadBoard(path)
    nets, _ = pick_nets(b, None, pours)
    return [n for n in nets if not n.startswith("unconnected")]


def weights(path, sch, pours, nets):
    try:
        from commands.powerlab_router2.router import make_plan
        b = pcbnew.LoadBoard(path)
        plan = make_plan(b, path, sch, pours, nets)
        gate = {n for n in nets if "gate" in plan["nets"].get(n, {}).get("roles", ())}
        return {n: 1 + plan["nets"].get(n, {}).get("priority", 1) for n in nets}, plan.get("source"), gate
    except Exception as e:  # no schematic: every net weight 2 (signal)
        return {n: 2 for n in nets}, f"none ({e})", set()


def fine_pitch_parts(b):
    """Footprints with 16+ pads, two of them within FINE_PITCH (centre to centre)."""
    out = []
    for fp in b.GetFootprints():
        ps = list(fp.Pads())
        if len(ps) < 16:
            continue
        xy = [(T(p.GetPosition().x), T(p.GetPosition().y)) for p in ps]
        near = min(math.hypot(a[0] - c[0], a[1] - c[1]) for i, a in enumerate(xy) for c in xy[i + 1:])
        if 0.05 < near <= FINE_PITCH + 1e-6:
            out.append(fp)
    return out


def bank(path, nets, w, loops=None, gate=frozenset()):
    from commands import routing_check
    b = pcbnew.LoadBoard(path)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    conn = b.GetConnectivity()
    pads = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            pads.setdefault(p.GetNetname(), []).append(p)
    length, vias = {}, 0
    for t in b.GetTracks():
        n = t.GetNetname()
        if n not in w:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            vias += 1
        else:
            length[n] = length.get(n, 0.0) + T(t.GetLength())

    earned = lost = 0.0
    per_net = {}
    for n in nets:
        ps = pads.get(n, [])
        if len(ps) < 2:
            continue
        seen, groups = set(), 0
        for p in ps:
            u = p.m_Uuid.AsString()
            if u in seen:
                continue
            groups += 1
            seen.add(u)
            for it in conn.GetConnectedItems(p):
                if it.Type() == pcbnew.PCB_PAD_T:
                    seen.add(it.m_Uuid.AsString())
        joins = len(ps) - 1
        joined, open_ = len(ps) - groups, groups - 1
        ideal = mst_length([(T(p.GetPosition().x), T(p.GetPosition().y)) for p in ps]) * joined / joins
        routed = length.get(n, 0.0)
        detour = routed / ideal if ideal > 0.05 and routed > 0 else 1.0
        e = JOIN * w[n] * joined / max(1.0, detour)
        f = FAIL * w[n] * open_
        earned += e
        lost += f
        per_net[n] = {"weight": w[n], "joined": joined, "open": open_, "detour": round(detour, 2),
                      "points": round(e - f, 1)}

    style = routing_check.check(path, {"nets": nets, "limit": 0})
    counts = style.get("counts") or {}
    findings = sum(n * KIND.get(k, 1.0) for k, n in counts.items())

    cut = 0.0
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.GetNetname():
            continue
        for L in z.GetLayerSet().CuStack():
            fill = z.GetFilledPolysList(L)
            areas = sorted((fill.Outline(i).Area() / 1e12 for i in range(fill.OutlineCount())), reverse=True)
            cut += sum(a for a in areas[1:] if a >= SLIVER)

    drc, rep = None, os.path.join(os.path.dirname(os.path.dirname(path)), "report.json")
    if os.path.basename(os.path.dirname(path)) == "result" and os.path.isfile(rep):
        drc = sum((json.load(open(rep)).get("new_drc_errors") or {}).values())
    loop_mm2, loop_pairs = None, None
    if loops:
        import loop_area
        lm = loop_area.measure(b, loops)
        # a gate loop that isn't routed has no area; count it as a bad loop, or leaving a gate
        # open would make the total smaller
        loop_mm2, loop_pairs = lm.get("area_mm2", 0.0) + LOOP_MISSING * lm.get("unrouted", 0), lm.get("by_pair")
    gate_wander = sum(max(0.0, v["detour"] - 1) for n, v in per_net.items() if n in gate and v["joined"])

    # fine-pitch ICs: vias in the body + 2 mm, vias in the 1 mm in front of the pins, and
    # priority-3 pins (weight 4) left joined to nothing
    fine = fine_pitch_parts(b)
    via_xy = [(T(t.GetPosition().x), T(t.GetPosition().y)) for t in b.GetTracks()
              if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() in w]
    body_vias = lane_vias = stranded = 0
    stranded_pins = []
    for fp in fine:
        bb = fp.GetBoundingBox(False)
        x0, y0, x1, y1 = T(bb.GetLeft()) - 2, T(bb.GetTop()) - 2, T(bb.GetRight()) + 2, T(bb.GetBottom()) + 2
        body_vias += sum(1 for x, y in via_xy if x0 <= x <= x1 and y0 <= y <= y1)
        boxes = []
        for p in fp.Pads():
            pb = p.GetBoundingBox()
            boxes.append((T(pb.GetLeft()) - 1, T(pb.GetTop()) - 1, T(pb.GetRight()) + 1, T(pb.GetBottom()) + 1))
            n = p.GetNetname()
            if w.get(n) == 4 and len(pads.get(n, [])) > 1:
                if not any(it.Type() == pcbnew.PCB_PAD_T and it.m_Uuid.AsString() != p.m_Uuid.AsString()
                           for it in conn.GetConnectedItems(p)):
                    stranded += 1
                    stranded_pins.append(f"{fp.GetReference()}.{p.GetNumber()}")
        lane_vias += sum(1 for x, y in via_xy if any(a <= x <= c and e <= y <= d for a, e, c, d in boxes))

    total = (earned - lost - VIA * vias - STYLE * findings - POUR * cut - LOOP * (loop_mm2 or 0.0)
             - GATE * gate_wander)
    return {
        "board": path.replace("\\", "/"),
        "bank": round(total, 1),
        "earned": round(earned, 1),
        "lost_open": round(lost, 1),
        "vias": vias,
        "style_findings": round(findings, 1),
        "new_drc": drc,
        "gated": bool(drc),
        "style_counts": style.get("counts"),
        "pour_cut_mm2": round(cut, 1),
        "gate_loop_mm2": None if loop_mm2 is None else round(loop_mm2, 1),
        "gate_loop_by_pair": loop_pairs,
        "gate_wander": round(gate_wander, 2),
        "fine_pitch_body_vias": body_vias,
        "fine_pitch_lane_vias": lane_vias,
        "stranded_priority3_pins": stranded,
        "stranded_pins": stranded_pins,
        "joins_open": sum(v["open"] for v in per_net.values()),
        "max_bank": round(sum(JOIN * w[n] * (len(pads.get(n, [])) - 1) for n in nets if len(pads.get(n, [])) > 1), 1),
        "per_net": per_net,
    }


def main(args):
    def opt(name, default=None):
        if name in args:
            i = args.index(name)
            v = args[i + 1]
            del args[i:i + 2]
            return v
        return default
    as_json = "--json" in args
    if as_json:
        args.remove("--json")
    src = opt("--nets-from")
    sch = opt("--schematic")
    for kv in (opt("--w") or "").split(","):
        if kv:
            k, v = kv.split("=")
            globals()[k.strip().upper()] = float(v)
    pours = opt("--pours", "GND").split(",")
    boards = [os.path.abspath(a) for a in args]
    src = os.path.abspath(src or boards[0])
    sch = sch or os.path.splitext(src)[0] + ".kicad_sch"
    nets = scoped_nets(src, pours)
    w, source, gate = weights(src, sch, pours, nets)
    loops = None
    if os.path.isdir(BENCH) and os.path.isfile(sch):
        sys.path.insert(0, BENCH)
        try:
            from commands.powerlab_router2 import plan as P
            nl = P.read_netlist(sch)
            loops = P.gate_loops(nl) if nl else None
        except Exception:
            loops = None
    out = [bank(p, nets, w, loops, gate) for p in boards]
    if as_json:
        print(json.dumps({"weights_from": source, "boards": out}, indent=1))
        return
    print(f"weights from: {source}; {len(nets)} nets")
    print(f"weights: join {JOIN}, fail {FAIL}, via {VIA}, style {STYLE}, pour {POUR}/mm2, loop {LOOP}/mm2, gate {GATE}")
    keys = ("bank", "max_bank", "joins_open", "vias", "style_findings", "pour_cut_mm2", "gate_loop_mm2", "gate_wander",
            "fine_pitch_body_vias", "fine_pitch_lane_vias", "stranded_priority3_pins", "new_drc")
    print("board".ljust(60) + "".join(k.rjust(15) for k in keys))
    for r in out:
        print(r["board"][-60:].ljust(60) + "".join(str(r[k]).rjust(15) for k in keys))


if __name__ == "__main__":
    main(sys.argv[1:])
