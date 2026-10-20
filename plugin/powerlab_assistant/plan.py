"""The block plan (powerlab-placement): where each functional block goes, before any part
is placed. Claude writes it as block-plan.json in the project; the panel shows it as a card
the user can explore. Clicking a block selects its parts in KiCad (through the same
`kicad:` locate as review links), and KiCad's cross-probing shows them in the schematic.

Everything is in board millimetres, KiCad's coordinates (y down). Angles are degrees
clockwise from +x, as they look on the board. Shapes:
    {"circle": {"center": [x, y], "diameter": d}}
    {"ring": {"center": [x, y], "inner": d1, "outer": d2}}          (diameters)
    {"sector": {"center": [x, y], "r": [r0, r1], "angle": [a0, a1]}}  (radii)
    {"rect": {"center": [x, y], "size": [w, h], "angle": a}}
    {"polygon": [[x, y], ...]}

The file:
    {"title": "...", "outline": <shape>, "cutouts": [<shape>], "holes": [<circle>],
     "keepouts": [{"name": "...", "sides": ["top", "bottom"], <shape>}],
     "blocks": [{"id": "legA", "name": "Leg A", "detail": "Q1 · R8 · C26", "side": "top",
                 "kind": "power", "refs": ["Q1", "R8"], <shape>}],
     "links": [{"from": "u3", "to": "legA", "label": "16 mm", "kind": "gate"}],
     "notes": ["...", ...]}
"""

import html
import json
import math
import os
import re

FILE_NAME = "block-plan.json"
KINDS = {  # block kind -> colour on the dark board
    "power": "#ff5d5d", "gate": "#ffb020", "driver": "#ffb020", "control": "#4f9bff",
    "mcu": "#4f9bff", "supply": "#34d17a", "converter": "#34d17a", "comms": "#b18cff",
    "sensor": "#2fd6c3", "analog": "#2fd6c3", "connector": "#a3b1c6", "fixed": "#a3b1c6",
    "debug": "#7f8ea3", "other": "#c9d3e0",
    "text": "#efe6c4", "logo": "#f2c86b",  # silkscreen: board text and logos, placed last (§3.6)
}
LINK_KINDS = {"gate": ("#ffd166", 0.7, ""), "power": ("#ff7a7a", 0.9, ""),
              "signal": ("#c9d3e0", 0.35, "1.4 1"), "analog": ("#5ee3d3", 0.4, "1.4 1")}
SIDES = ("top", "bottom")
REF = re.compile(r"^[A-Za-z0-9_+.\-]{1,40}$")
MAX_SHAPES = 400
MAX_POINTS = 4000  # of one polygon: board outlines read from Edge.Cuts can be long


def is_plan(path):
    # Either separator: the panel's paths are Windows paths, the auto-fix runner is Linux.
    return re.split(r"[\\/]", path or "")[-1].lower() == FILE_NAME


def _num(v, default=0.0):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    return f if math.isfinite(f) else default


def _pt(v):
    if isinstance(v, (list, tuple)) and len(v) >= 2:
        return _num(v[0]), _num(v[1])
    return 0.0, 0.0


def _polar(c, r, a):
    t = math.radians(a)
    return c[0] + r * math.cos(t), c[1] + r * math.sin(t)


def _f(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")


class Shape:
    """A plan shape: its SVG path, the points that bound it, where its label goes and
    how much room the label has."""

    def __init__(self, spec):
        self.d, self.points, self.anchor, self.room, self.angle = "", [], (0.0, 0.0), (10.0, 10.0), 0.0
        self.outline = []  # the boundary as a closed polygon, for gaps between blocks
        if "circle" in spec:
            c = spec["circle"] or {}
            o, r = _pt(c.get("center")), _num(c.get("diameter")) / 2
            self._circle(o, r)
        elif "ring" in spec:
            c = spec["ring"] or {}
            o = _pt(c.get("center"))
            r0, r1 = _num(c.get("inner")) / 2, _num(c.get("outer")) / 2
            self._circle(o, r1)
            self.d += " " + _circle_path(o, r0)
            self.room = (r1 - r0, r1 - r0)
        elif "sector" in spec:
            self._sector(spec["sector"] or {})
        elif "rect" in spec:
            c = spec["rect"] or {}
            o, (w, h), a = _pt(c.get("center")), _pt(c.get("size")), _num(c.get("angle"))
            t = math.radians(a)
            corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
            self.points = [(o[0] + x * math.cos(t) - y * math.sin(t),
                            o[1] + x * math.sin(t) + y * math.cos(t)) for x, y in corners]
            self.d = _poly_path(self.points)
            self.anchor, self.room, self.angle = o, (w, h), _upright(a)
            self.outline = list(self.points)
        elif "polygon" in spec:
            pts = [_pt(p) for p in (spec["polygon"] or [])[:MAX_POINTS]]
            if len(pts) >= 3:
                self.points = pts
                self.outline = list(pts)
                self.d = _poly_path(pts)
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                self.anchor = (sum(xs) / len(xs), sum(ys) / len(ys))
                self.room = (max(xs) - min(xs), max(ys) - min(ys))

    def _circle(self, o, r):
        self.d = _circle_path(o, r)
        self.points = [(o[0] - r, o[1] - r), (o[0] + r, o[1] + r)]
        self.anchor, self.room = o, (r * 1.4, r * 1.4)
        self.outline = [_polar(o, r, i * 7.5) for i in range(48)]

    def _sector(self, c):
        o = _pt(c.get("center"))
        r0, r1 = _pt(c.get("r"))
        a0, a1 = _pt(c.get("angle"))
        if a1 < a0:
            a1 += 360
        large = 1 if a1 - a0 > 180 else 0
        p0, p1 = _polar(o, r1, a0), _polar(o, r1, a1)
        q1, q0 = _polar(o, r0, a1), _polar(o, r0, a0)
        self.d = (f"M{_f(p0[0])} {_f(p0[1])} A{_f(r1)} {_f(r1)} 0 {large} 1 {_f(p1[0])} {_f(p1[1])} "
                  f"L{_f(q1[0])} {_f(q1[1])} A{_f(r0)} {_f(r0)} 0 {large} 0 {_f(q0[0])} {_f(q0[1])} Z")
        steps = max(2, int((a1 - a0) / 10) + 1)
        self.points = [_polar(o, r, a0 + (a1 - a0) * i / steps) for r in (r0, r1) for i in range(steps + 1)]
        n = max(2, int((a1 - a0) / 2) + 1)
        self.outline = ([_polar(o, r1, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
                        + [_polar(o, r0, a1 - (a1 - a0) * i / n) for i in range(n + 1)])
        mid = (a0 + a1) / 2
        self.anchor = _polar(o, (r0 + r1) / 2, mid)
        arc = (r0 + r1) / 2 * math.radians(a1 - a0)
        self.angle = _upright(mid + 90)  # labels run along the arc
        self.room = (arc, r1 - r0)


def _densify(poly, step=0.5):
    """The closed polygon's boundary as points at most `step` mm apart."""
    out = []
    for i, (x0, y0) in enumerate(poly):
        x1, y1 = poly[(i + 1) % len(poly)]
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        out += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    return out


def _inside(p, poly):
    x, y, hit = p[0], p[1], False
    for i, (x0, y0) in enumerate(poly):
        x1, y1 = poly[i - 1]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            hit = not hit
    return hit


def gap(a, b):
    """The edge-to-edge distance between two shapes in mm: 0 when they touch or overlap."""
    if not a.outline or not b.outline:
        return None
    pa, pb = _densify(a.outline), _densify(b.outline)
    if any(_inside(p, b.outline) for p in pa[::4]) or any(_inside(p, a.outline) for p in pb[::4]):
        return 0.0
    return min(math.hypot(x0 - x1, y0 - y1) for x0, y0 in pa for x1, y1 in pb)


def _upright(a):
    """A text angle that never reads upside down."""
    a %= 360
    return a - 180 if 90 < a < 270 else a


def _circle_path(o, r):
    return (f"M{_f(o[0] - r)} {_f(o[1])} a{_f(r)} {_f(r)} 0 1 0 {_f(2 * r)} 0 "
            f"a{_f(r)} {_f(r)} 0 1 0 {_f(-2 * r)} 0 Z")


def _poly_path(pts):
    return "M" + " L".join(f"{_f(x)} {_f(y)}" for x, y in pts) + " Z"


def _shape_of(item):
    for key in ("circle", "ring", "sector", "rect", "polygon"):
        if key in item:
            return Shape({key: item[key]})
    return None


def _label(shape, name, detail, cls, silk=False):
    """Name and detail lines, level and sized to the room round the block's centre.
    A silkscreen block (board text) shows its words at about the height they print."""
    xs, ys = [p[0] for p in shape.points], [p[1] for p in shape.points]
    w = min(shape.room[0], shape.room[1], max(xs) - min(xs)) if shape.angle else shape.room[0]
    w = max(w, 0.7 * (max(xs) - min(xs)))
    h = max(ys) - min(ys) if shape.angle else shape.room[1]
    size = max(1.1, min(2.8, w / max(3.0, 0.6 * len(name)), h * 0.3))
    if silk:
        size, detail = max(0.9, min(3.0, h * 0.62, w / max(1.0, 0.58 * len(name)))), ""
    x, y = shape.anchor
    out = [f'<g class="{cls}">']
    small = size * 0.58
    fits = detail and h > size * 2.2 and w > 0.55 * small * len(detail)
    dy = -size * 0.28 if fits else size * 0.35
    out.append(f'<text x="{_f(x)}" y="{_f(y + dy)}" font-size="{_f(size)}" class="nm">'
               f"{html.escape(name)}</text>")
    if fits:
        out.append(f'<text x="{_f(x)}" y="{_f(y + dy + size * 1.05)}" font-size="{_f(small)}" '
                   f'class="dt">{html.escape(detail)}</text>')
    out.append("</g>")
    return "".join(out)


def _loc(refs, shape):
    """What a click selects in KiCad: the block's parts, or for a block without parts
    (board text, which has no reference) what lies at its centre."""
    if refs:
        return "refs=" + ",".join(refs)
    return f"at={_f(shape.anchor[0])},{_f(shape.anchor[1])}" if shape else ""


def _blocks(data):
    return [b for b in (data.get("blocks") or [])[:MAX_SHAPES] if isinstance(b, dict)]


def block_id(b, i):
    return str(b.get("id") or b.get("name") or i)


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("the block plan is not a JSON object")
    return data


def svg(data):
    """The plan as an SVG drawing; every text is escaped."""
    outline = _shape_of(data.get("outline") or {})
    shapes = [(b, _shape_of(b)) for b in _blocks(data)]
    pts = list(outline.points if outline else [])
    for _b, s in shapes:
        if s:
            pts += s.points
    if not pts:
        pts = [(0, 0), (100, 100)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.04 + 1
    x0, y0 = min(xs) - pad, min(ys) - pad
    w, h = max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad
    grid = 5.0 if max(w, h) < 200 else 10.0
    o = [f'<svg class="plan-svg" viewBox="{_f(x0)} {_f(y0)} {_f(w)} {_f(h)}" '
         f'xmlns="http://www.w3.org/2000/svg" role="img">',
         "<defs>",
         f'<pattern id="pg" width="{_f(grid)}" height="{_f(grid)}" patternUnits="userSpaceOnUse">'
         f'<path d="M{_f(grid)} 0 L0 0 0 {_f(grid)}" fill="none" class="grid"/></pattern>']
    for kind, colour in sorted(set(KINDS.items())):
        o.append(f'<pattern id="h-{kind}" width="1.6" height="1.6" patternUnits="userSpaceOnUse" '
                 f'patternTransform="rotate(45)"><rect width="1.6" height="1.6" fill="{colour}" '
                 f'fill-opacity=".10"/><line x1="0" y1="0" x2="0" y2="1.6" stroke="{colour}" '
                 f'stroke-width=".5" stroke-opacity=".55"/></pattern>')
    o.append('<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
             '<feGaussianBlur stdDeviation="0.9" result="b"/><feMerge><feMergeNode in="b"/>'
             '<feMergeNode in="SourceGraphic"/></feMerge></filter>')
    if outline:
        o.append(f'<clipPath id="pc"><path d="{outline.d}"/></clipPath>')
    o.append("</defs>")
    if outline:
        cut = " ".join(s.d for s in (_shape_of(c) for c in data.get("cutouts") or [] if isinstance(c, dict)) if s)
        o.append(f'<path d="{outline.d} {cut}" fill-rule="evenodd" class="board"/>')
        o.append(f'<rect x="{_f(x0)}" y="{_f(y0)}" width="{_f(w)}" height="{_f(h)}" '
                 f'fill="url(#pg)" clip-path="url(#pc)"/>')
        if cut:
            o.append(f'<path d="{cut}" class="cut"/>')
        o.append(f'<path d="{outline.d}" class="edge"/>')
    for k in (data.get("keepouts") or [])[:MAX_SHAPES]:
        s = _shape_of(k) if isinstance(k, dict) else None
        if not s:
            continue
        sides = [x for x in (k.get("sides") or SIDES) if x in SIDES] or list(SIDES)
        title = str(k.get("name") or "Keep-out")
        o.append(f'<path d="{s.d}" fill-rule="evenodd" class="keepout" data-sides="{" ".join(sides)}">'
                 f"<title>{html.escape(title)}</title></path>")
    for c in (data.get("holes") or [])[:MAX_SHAPES]:
        s = _shape_of(c) if isinstance(c, dict) else None
        if s:
            o.append(f'<path d="{s.d}" class="hole"/>')
    anchors, by_id = {}, {}
    for i, (b, s) in enumerate(shapes):
        if not s:
            continue
        bid = block_id(b, i)
        anchors[bid], by_id[bid] = s.anchor, s
    pills = []
    for n, ln in enumerate((data.get("links") or [])[:MAX_SHAPES]):
        if not isinstance(ln, dict):
            continue
        a, z = ln.get("from"), ln.get("to")
        p = anchors.get(a) if isinstance(a, str) else _pt(a)
        q = anchors.get(z) if isinstance(z, str) else _pt(z)
        if not p or not q:
            continue
        colour, width, dash = LINK_KINDS.get(ln.get("kind"), LINK_KINDS["signal"])
        dash = f' stroke-dasharray="{dash}"' if dash else ""
        ends = (f'data-i="{n}" data-from="{html.escape(str(a), True)}" data-to="{html.escape(str(z), True)}"'
                if isinstance(a, str) and isinstance(z, str) else f'data-i="{n}"')
        o.append(f'<line class="link" {ends} x1="{_f(p[0])}" y1="{_f(p[1])}" x2="{_f(q[0])}" '
                 f'y2="{_f(q[1])}" stroke="{colour}" stroke-width="{width}" stroke-linecap="round"{dash}/>')
        label = str(ln.get("label") or "")
        g = gap(by_id[a], by_id[z]) if a in by_id and z in by_id else None
        tip = f"<title>{html.escape(label)}{' · ' if label else ''}gap {g:.1f} mm</title>" if g is not None else ""
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        fs = 1.45
        bw = 0.56 * fs * len(label) + 1.4
        pills.append(f'<g class="pill-g{"" if label else " empty"}" {ends} data-label="{html.escape(label, True)}">'
                     f'{tip}<rect x="{_f(mx - bw / 2)}" y="{_f(my - fs * 0.78)}" '
                     f'width="{_f(bw)}" height="{_f(fs * 1.56)}" rx="{_f(fs * 0.78)}" class="pill" '
                     f'stroke="{colour}"/><text x="{_f(mx)}" y="{_f(my + fs * 0.36)}" '
                     f'font-size="{_f(fs)}" fill="{colour}" class="pt">{html.escape(label)}</text></g>')
    # Bottom-side blocks first, so the top side is drawn over them.
    order = sorted(range(len(shapes)), key=lambda i: shapes[i][0].get("side") != "bottom")
    for i in order:
        b, s = shapes[i]
        if not s:
            continue
        kind = b.get("kind") if b.get("kind") in KINDS else "other"
        colour = KINDS[kind]
        side = "bottom" if b.get("side") == "bottom" else "top"
        bid = block_id(b, i)
        fill = f"url(#h-{kind})" if side == "bottom" else colour
        dash = ' stroke-dasharray="1.6 1"' if side == "bottom" else ""
        refs = [r for r in (str(x) for x in b.get("refs") or []) if REF.match(r)]
        loc = f' data-loc="{_loc(refs, s)}"'
        name, detail = str(b.get("name") or bid), str(b.get("detail") or "")
        # How a drag moves it: a ring sector turns round its centre and moves in or out
        # along its radius; any other shape moves in x and y.
        if "sector" in b:
            c = _pt((b["sector"] or {}).get("center"))
            drag = f' data-drag="sector" data-cx="{_f(c[0])}" data-cy="{_f(c[1])}"'
        else:
            drag = ' data-drag="move"'
        if "rect" in b or "polygon" in b:
            drag += ' data-turn="1"'  # can be turned in 90° steps
        pts = _densify(s.outline, 1.0) if s.outline else []
        pts = pts[::max(1, len(pts) // 160 + 1)]
        drag += f' data-pts="{" ".join(f"{_f(x)},{_f(y)}" for x, y in pts)}"'
        o.append(f'<g class="blk {side}" data-id="{html.escape(bid, True)}" data-side="{side}" data-kind="{kind}"{loc}{drag} '
                 f'data-ax="{_f(s.anchor[0])}" data-ay="{_f(s.anchor[1])}" '
                 f'style="--c:{colour}" tabindex="0">'
                 f"<title>{html.escape(name)}{(' — ' + html.escape(detail)) if detail else ''}"
                 f"{' · click to select its parts in KiCad' if refs else ''} · drag to move it</title>"
                 f'<path d="{s.d}" class="base"/>'
                 f'<path d="{s.d}" fill="{fill}" stroke="{colour}"{dash} class="body"/>'
                 + _label(s, name, detail, "lbl", kind in ("text", "logo")) + "</g>")
    o += pills
    o.append("</svg>")
    return "".join(o)


# --- The board's own outline -------------------------------------------------------------
# "outline": "board" (or {"board": "<file>.kicad_pcb"}) draws the board's Edge.Cuts exactly:
# any shape, with arcs, notches and cutouts. It's read from the saved file's text, not with
# pcbnew.LoadBoard, which inside KiCad's process can switch KiCad's open project.

_EDGE_CACHE = {}
_NUM = r"(-?[\d.]+)"


def _items(text, head):
    """The balanced `(head ...)` expressions in a .kicad_pcb text."""
    i = text.find(head)
    while i != -1:
        depth, j = 0, i
        while j < len(text):
            c = text[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            elif c == '"':
                j = text.find('"', j + 1)
                while j != -1 and text[j - 1] == "\\":
                    j = text.find('"', j + 1)
                if j == -1:
                    return
            j += 1
        yield text[i:j + 1]
        i = text.find(head, j)


def _arc_points(a, m, b):
    """Points along the arc through a, m and b (KiCad's start, mid, end)."""
    ax, ay = a
    bx, by = m
    cx, cy = b
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [a, b]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    t0, tm, t1 = (math.atan2(y - uy, x - ux) for x, y in (a, m, b))
    sweep = (t1 - t0) % (2 * math.pi)
    if (tm - t0) % (2 * math.pi) > sweep:  # the mid point says it runs the other way
        sweep -= 2 * math.pi
    n = max(2, int(abs(sweep) / math.radians(3)) + 1)
    return [(ux + r * math.cos(t0 + sweep * k / n), uy + r * math.sin(t0 + sweep * k / n)) for k in range(n + 1)]


def _area(loop):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(loop, loop[1:] + loop[:1]))) / 2


def edge_cuts(pcb_path):
    """The closed loops on Edge.Cuts of a saved board, largest first (the outline, then
    cutouts), each a list of points in mm. Cached until the file changes."""
    key = (os.path.abspath(pcb_path), os.path.getmtime(pcb_path))
    if key in _EDGE_CACHE:
        return _EDGE_CACHE[key]
    with open(pcb_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    loops, pieces = [], []
    for head in ("(gr_line", "(gr_arc", "(gr_circle", "(gr_rect", "(gr_poly", "(gr_curve"):
        for item in _items(text, head):
            if '(layer "Edge.Cuts")' not in item:
                continue
            pt = {k: (float(x), float(y)) for k, x, y in re.findall(r"\((start|mid|end|center) " + _NUM + " " + _NUM + r"\)", item)}
            xy = [(float(x), float(y)) for x, y in re.findall(r"\(xy " + _NUM + " " + _NUM + r"\)", item)]
            if head == "(gr_line" and "start" in pt and "end" in pt:
                pieces.append([pt["start"], pt["end"]])
            elif head == "(gr_arc" and {"start", "mid", "end"} <= pt.keys():
                pieces.append(_arc_points(pt["start"], pt["mid"], pt["end"]))
            elif head == "(gr_circle" and "center" in pt and "end" in pt:
                (x, y), (ex, ey) = pt["center"], pt["end"]
                r = math.hypot(ex - x, ey - y)
                loops.append([(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(0, 360, 2)])
            elif head == "(gr_rect" and "start" in pt and "end" in pt:
                (x0, y0), (x1, y1) = pt["start"], pt["end"]
                loops.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
            elif head == "(gr_poly" and len(xy) >= 3:
                loops.append(xy)
            elif head == "(gr_curve" and len(xy) == 4:  # a cubic Bezier: start, two controls, end
                (x0, y0), (x1, y1), (x2, y2), (x3, y3) = xy
                pieces.append([((1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3 * x3,
                                (1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3 * y3)
                               for t in (k / 16 for k in range(17))])
    close = lambda a, b: abs(a[0] - b[0]) < 0.01 and abs(a[1] - b[1]) < 0.01  # noqa: E731
    while pieces:  # chain lines, arcs and curves end to end into closed loops
        loop = list(pieces.pop())
        grown = True
        while grown and not close(loop[0], loop[-1]):
            grown = False
            for i, piece in enumerate(pieces):
                if close(piece[0], loop[-1]):
                    loop += piece[1:]
                elif close(piece[-1], loop[-1]):
                    loop += piece[-2::-1]
                else:
                    continue
                pieces.pop(i)
                grown = True
                break
        if close(loop[0], loop[-1]) and len(loop) > 3:
            loops.append(loop[:-1])
    loops.sort(key=_area, reverse=True)
    _EDGE_CACHE.clear()
    _EDGE_CACHE[key] = loops
    return loops


def _board_file(data, plan_path):
    """The board a plan means: its "board" file, or the one .kicad_pcb in the project
    (the folder that holds the placement folder)."""
    outline = data.get("outline")
    project = os.path.dirname(os.path.dirname(os.path.abspath(plan_path)))
    named = data.get("board") or (outline.get("board") if isinstance(outline, dict) else None)
    if isinstance(named, str) and named.lower().endswith(".kicad_pcb"):
        path = named if os.path.isabs(named) else os.path.join(project, named)
        return path if os.path.isfile(path) else None
    boards = [f for f in os.listdir(project) if f.lower().endswith(".kicad_pcb")] if os.path.isdir(project) else []
    return os.path.join(project, boards[0]) if len(boards) == 1 else None


def with_board_outline(data, plan_path):
    """The plan with "outline": "board" replaced by the board's Edge.Cuts (outline and
    cutouts). Plans that draw their own outline come back as they are."""
    outline = data.get("outline")
    if not (outline == "board" or (isinstance(outline, dict) and "board" in outline)):
        return data
    pcb = _board_file(data, plan_path)
    loops = edge_cuts(pcb) if pcb else []
    if not loops:
        raise ValueError("the board outline can't be read: no closed outline on Edge.Cuts"
                         + ("" if pcb else " (no .kicad_pcb found next to the plan)"))
    data = dict(data)
    data["outline"] = {"polygon": [[round(x, 3), round(y, 3)] for x, y in loops[0]]}
    data["cutouts"] = list(data.get("cutouts") or []) + [
        {"polygon": [[round(x, 3), round(y, 3)] for x, y in loop]} for loop in loops[1:]]
    return data


def card(path):
    """What the panel shows for a plan: title, the drawing, the block list and the notes."""
    try:
        data = with_board_outline(load(path), path)
    except (OSError, ValueError) as e:
        return {"path": path, "title": "Block plan", "error": f"The block plan can't be read: {e}",
                "svg": "", "blocks": [], "notes": []}
    blocks = []
    shapes = {block_id(b, i): _shape_of(b) for i, b in enumerate(_blocks(data))}
    for i, b in enumerate(_blocks(data)):
        kind = b.get("kind") if b.get("kind") in KINDS else "other"
        refs = [r for r in (str(x) for x in b.get("refs") or []) if REF.match(r)]
        blocks.append({"id": block_id(b, i), "name": str(b.get("name") or ""),
                       "detail": str(b.get("detail") or ""), "kind": kind, "colour": KINDS[kind],
                       "side": "bottom" if b.get("side") == "bottom" else "top",
                       "loc": _loc(refs, shapes.get(block_id(b, i))), "count": len(refs)})
    notes = [str(n) for n in (data.get("notes") or [])[:20]]
    return {"path": path, "title": str(data.get("title") or "Block plan"), "svg": svg(data),
            "blocks": blocks, "notes": notes,
            "links": [{"label": str(ln.get("label") or ""), "from": str(ln.get("from")), "to": str(ln.get("to")),
                       "kind": str(ln.get("kind") or "signal")}
                      for ln in (data.get("links") or [])[:MAX_SHAPES] if isinstance(ln, dict)]}


MAX_MOVE = 500.0  # mm or degrees: anything larger is a broken message, not a drag


def move(path, moves):
    """Apply the user's drags from the card to the plan file, and write it back.

    Each move is {"id", "da", "dr"} for a ring sector (degrees clockwise, mm outward),
    {"id", "dx", "dy"} (mm) for any other shape, or {"id", "side": "top"/"bottom"}.
    Returns one line per move for Claude, e.g. "Leg A: turned 12° clockwise, now 313–335°"."""
    data = load(path)
    blocks = {block_id(b, i): b for i, b in enumerate(_blocks(data))}
    lines, moved = [], set()
    for m in moves if isinstance(moves, list) else []:
        b = blocks.get(str((m or {}).get("id")))
        if b is None:
            continue
        name = str(b.get("name") or b.get("id"))
        moved.add(str(m.get("id")))
        turn = _num(m.get("rot")) if "rot" in m else 0.0
        if turn and abs(turn) <= 360:  # any angle; the card offers 90° and 45° first
            if isinstance(b.get("rect"), dict):
                b["rect"]["angle"] = round((_num(b["rect"].get("angle")) + turn) % 360, 2)
            elif isinstance(b.get("polygon"), list):
                ox, oy = Shape({"polygon": b["polygon"]}).anchor
                t = math.radians(turn)
                b["polygon"] = [[round(ox + (x - ox) * math.cos(t) - (y - oy) * math.sin(t), 2),
                                 round(oy + (x - ox) * math.sin(t) + (y - oy) * math.cos(t), 2)]
                                for x, y in (_pt(q) for q in b["polygon"])]
            else:
                continue
            lines.append(f"{name}: turned {_f(abs(turn))}° {'clockwise' if turn > 0 else 'counter-clockwise'}")
            continue
        if m.get("side") in SIDES:
            b["side"] = m["side"]
            lines.append(f"{name}: to the {m['side']} side")
            continue
        clamp = lambda v: max(-MAX_MOVE, min(MAX_MOVE, _num(v)))  # noqa: E731
        if "sector" in b and isinstance(b["sector"], dict):
            sec = b["sector"]
            da, dr = clamp(m.get("da")), clamp(m.get("dr"))
            a0, a1 = _pt(sec.get("angle"))
            r0, r1 = _pt(sec.get("r"))
            dr = max(dr, -r0)  # never through the centre
            sec["angle"] = [round((a0 + da) % 360, 2), round((a1 + da) % 360, 2)]
            sec["r"] = [round(r0 + dr, 2), round(r1 + dr, 2)]
            parts = []
            if abs(da) >= 0.05:
                parts.append(f"turned {abs(da):.1f}° {'clockwise' if da > 0 else 'counter-clockwise'}")
            if abs(dr) >= 0.05:
                parts.append(f"{abs(dr):.1f} mm {'outward' if dr > 0 else 'inward'}")
            if parts:
                lines.append(f"{name}: {', '.join(parts)}; now {_f(sec['angle'][0])}–{_f(sec['angle'][1])}°, "
                             f"r {_f(sec['r'][0])}–{_f(sec['r'][1])} mm")
            continue
        dx, dy = clamp(m.get("dx")), clamp(m.get("dy"))
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            continue
        shifted = False
        for key in ("rect", "circle", "ring"):
            if isinstance(b.get(key), dict):
                x, y = _pt(b[key].get("center"))
                b[key]["center"] = [round(x + dx, 2), round(y + dy, 2)]
                where = b[key]["center"]
                shifted = True
        if isinstance(b.get("polygon"), list):
            b["polygon"] = [[round(_pt(q)[0] + dx, 2), round(_pt(q)[1] + dy, 2)] for q in b["polygon"]]
            shape = Shape({"polygon": b["polygon"]})
            where = [round(shape.anchor[0], 2), round(shape.anchor[1], 2)]
            shifted = True
        if shifted:
            lines.append(f"{name}: moved {dx:+.1f} mm in x, {dy:+.1f} mm in y; "
                         f"centre now ({_f(where[0])}, {_f(where[1])})")
    relabel(data, moved)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return lines


NUMBER_AT_END = re.compile(r"[\s·:]*[~≈]?\s*\d+(\.\d+)?\s*(mm)?(\s*gap)?\s*$")


def relabel(data, moved):
    """A link of a moved block gets the measured gap instead of Claude's old length,
    e.g. "gate A ~16" -> "gate A · 7.5 mm gap", until Claude measures it again."""
    shapes = {block_id(b, i): _shape_of(b) for i, b in enumerate(_blocks(data))}
    sides = {block_id(b, i): b.get("side") == "bottom" for i, b in enumerate(_blocks(data))}
    for ln in data.get("links") or []:
        if not isinstance(ln, dict) or not ({ln.get("from"), ln.get("to")} & moved):
            continue
        a, z = shapes.get(ln.get("from")), shapes.get(ln.get("to"))
        g = gap(a, z) if a and z else None
        if g is None:
            continue
        base = NUMBER_AT_END.sub("", re.sub(r"\s*·\s*(overlap|stacked|[\d.]+ mm gap)$", "",
                                            str(ln.get("label") or "")))
        # Over each other on the two sides is a stack (a via apart), on one side a collision.
        stacked = sides.get(ln.get("from")) != sides.get(ln.get("to"))
        ln["label"] = (base + " · " if base else "") + (
            ("stacked" if stacked else "overlap") if g == 0 else f"{g:.1f} mm gap")
