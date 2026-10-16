"""Routing quality report for a board, to compare routers with each other and with hand
routing (docs/powerlab-router-plan.md, milestone 3).

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/route_quality.py <board.kicad_pcb> [<board2> ...] [--class Default]

For the signal nets (net class Default unless --class says otherwise):
- length per layer and the bottom-layer share, vias, segments, vias per connection;
- detour: track length / straight-line (octilinear) length, for two-pad nets;
- diagonals: the share of track length that runs at 45 degrees, and the longest 45 degree
  segment (hand routing runs horizontal and vertical, with diagonals as short corners);
- corners: changes of direction between two joined segments; "sharp" means a turn of more
  than 45 degrees (a 90 degree corner or worse, design rules §3.4);
- pad entries: track ends on a pad that are off its centre, or come in at an angle to the
  pad's axes (§3.4, "enter a pad straight and end at its centre");
- pours (zones refilled): filled area per pour net and layer, and how many pieces it is
  in (fewer, larger pieces = the routing left the pour whole, §3.3);
- unconnected items, from KiCad's connectivity.
"""
import json
import math
import sys
from collections import defaultdict

import pcbnew

T = pcbnew.ToMM


def _key(p):
    return (round(T(p.x), 3), round(T(p.y), 3))


def report(path, netclass="Default"):
    b = pcbnew.LoadBoard(path)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    ns = b.GetDesignSettings().m_NetSettings
    pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
    nets = {p.GetNetname() for p in pads if p.GetNetname()
            and ns.GetEffectiveNetClass(p.GetNetname()).GetName() == netclass}
    tracks = [t for t in b.GetTracks() if t.GetNetname() in nets]
    segs = [t for t in tracks if t.Type() == pcbnew.PCB_TRACE_T]
    vias = [t for t in tracks if t.Type() == pcbnew.PCB_VIA_T]
    length = defaultdict(float)
    diagonal, longest_diagonal = 0.0, 0.0
    for s in segs:
        length[b.GetLayerName(s.GetLayer())] += T(s.GetLength())
        dx, dy = abs(T(s.GetEnd().x - s.GetStart().x)), abs(T(s.GetEnd().y - s.GetStart().y))
        if min(dx, dy) > 0.01 and abs(dx - dy) < 0.02:
            diagonal += T(s.GetLength())
            longest_diagonal = max(longest_diagonal, T(s.GetLength()))
    total = sum(length.values())

    # corners: points where exactly two segments of one net and layer meet, not on a pad
    pad_at = defaultdict(list)
    for p in pads:
        pad_at[_key(p.GetPosition())].append(p)
    ends = defaultdict(list)
    for s in segs:
        for here, there in ((s.GetStart(), s.GetEnd()), (s.GetEnd(), s.GetStart())):
            ends[(s.GetNetname(), s.GetLayer(), _key(here))].append((T(there.x) - T(here.x), T(there.y) - T(here.y)))
    corners = sharp = 0
    for (net, layer, pt), dirs in ends.items():
        if len(dirs) != 2 or pt in pad_at:
            continue
        (ax, ay), (bx, by) = dirs
        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
        if la < 1e-6 or lb < 1e-6:
            continue
        # both point away from the corner: straight through is 180 degrees between them
        between = math.degrees(math.acos(max(-1, min(1, (ax * bx + ay * by) / (la * lb)))))
        turn = 180 - between
        if turn > 1:
            corners += 1
        if turn > 46:
            sharp += 1

    # pad entries
    off_centre = angled = entries = 0
    for s in segs:
        for here, there in ((s.GetStart(), s.GetEnd()), (s.GetEnd(), s.GetStart())):
            for p in pads:
                if p.GetNetname() != s.GetNetname() or not p.IsOnLayer(s.GetLayer()):
                    continue
                if not p.HitTest(here):
                    continue
                if p.HitTest(there):
                    continue  # a segment inside the pad
                entries += 1
                c = p.GetPosition()
                if math.hypot(T(here.x - c.x), T(here.y - c.y)) > 0.01:
                    off_centre += 1
                a = math.degrees(math.atan2(T(there.y - here.y), T(there.x - here.x))) - p.GetOrientation().AsDegrees()
                if min(a % 90, 90 - a % 90) > 1:
                    angled += 1
                break

    # detour on two-pad nets
    detours = []
    for net in nets:
        np_ = [p for p in pads if p.GetNetname() == net]
        if len(np_) != 2:
            continue
        dx = abs(T(np_[0].GetPosition().x - np_[1].GetPosition().x))
        dy = abs(T(np_[0].GetPosition().y - np_[1].GetPosition().y))
        direct = max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        routed = sum(T(s.GetLength()) for s in segs if s.GetNetname() == net)
        if direct > 0.5 and routed > 0:
            detours.append(routed / direct)

    pours = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.GetNetname():
            continue
        for L in z.GetLayerSet().CuStack():
            fill = z.GetFilledPolysList(L)
            areas = sorted((fill.Outline(i).Area() / 1e12 for i in range(fill.OutlineCount())), reverse=True)
            k = f"{z.GetNetname()} {b.GetLayerName(L)}"
            pours[k] = {"area_mm2": round(sum(areas), 1), "pieces": len(areas),
                        "largest_share": round(areas[0] / sum(areas), 3) if areas else 0}

    b.BuildConnectivity()
    connections = sum(max(0, sum(1 for p in pads if p.GetNetname() == n) - 1) for n in nets)
    return {
        "board": path.replace("\\", "/").rsplit("/", 1)[-1],
        "unconnected_items": b.GetConnectivity().GetUnconnectedCount(False),
        "length_mm": round(total, 1),
        "bottom_share": round(length.get("B.Cu", 0) / total, 2) if total else 0,
        "vias": len(vias),
        "vias_per_connection": round(len(vias) / connections, 2) if connections else 0,
        "segments": len(segs),
        "diagonal_share": round(diagonal / total, 2) if total else 0,
        "longest_diagonal_mm": round(longest_diagonal, 2),
        "corners": corners,
        "sharp_corners": sharp,
        "detour_median": round(sorted(detours)[len(detours) // 2], 2) if detours else None,
        "detour_worst": round(max(detours), 2) if detours else None,
        "pad_entries": entries,
        "entries_off_centre": off_centre,
        "entries_at_an_angle": angled,
        "pours": pours,
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    cls = "Default"
    if "--class" in args:
        i = args.index("--class")
        cls = args[i + 1]
        del args[i:i + 2]
    print(json.dumps([report(p, cls) for p in args], indent=1))
