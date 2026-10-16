"""Draw a board's copper without pours, to look at routing: pads grey, F.Cu tracks red,
B.Cu tracks blue, vias yellow (2-layer boards).

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/render_copper.py <board.kicad_pcb> <out.png> [px per mm] [x0 y0 x1 y1] [nets to highlight, comma separated]
"""
import sys
import pcbnew
from PIL import Image, ImageDraw
T = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]
s = float(sys.argv[3]) if len(sys.argv) > 3 else 30
eb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = (map(float, sys.argv[4:8]) if len(sys.argv) > 7 else (T(eb.GetLeft()), T(eb.GetTop()), T(eb.GetRight()), T(eb.GetBottom())))
hl = set(sys.argv[8].split(",")) if len(sys.argv) > 8 else None
W, H = int((x1 - x0) * s), int((y1 - y0) * s)
im = Image.new("RGB", (W, H), (20, 22, 30)); d = ImageDraw.Draw(im, "RGBA")
P = lambda x, y: ((x - x0) * s, (y - y0) * s)
def poly(sp, fill):
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i); pts = [P(T(o.CPoint(k).x), T(o.CPoint(k).y)) for k in range(o.PointCount())]
        if len(pts) >= 3: d.polygon(pts, fill=fill)
for dw in b.GetDrawings():
    if dw.GetLayer() == pcbnew.Edge_Cuts and dw.GetShape() == pcbnew.SHAPE_T_SEGMENT:
        d.line([P(T(dw.GetStart().x), T(dw.GetStart().y)), P(T(dw.GetEnd().x), T(dw.GetEnd().y))], fill=(230, 200, 60), width=2)
for fp in b.GetFootprints():
    for p in fp.Pads():
        for L, col in ((pcbnew.B_Cu, (90, 90, 110, 255)), (pcbnew.F_Cu, (150, 150, 160, 255))):
            if p.IsOnLayer(L):
                sp = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(sp, L, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE); poly(sp, col)
for L, col in ((pcbnew.B_Cu, (70, 120, 255, 200)), (pcbnew.F_Cu, (235, 60, 60, 220))):
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == L:
            c = col if (hl is None or t.GetNetname() in hl) else (col[0] // 3, col[1] // 3, col[2] // 3, 160)
            w = max(1, int(T(t.GetWidth()) * s))
            a, e = P(T(t.GetStart().x), T(t.GetStart().y)), P(T(t.GetEnd().x), T(t.GetEnd().y))
            d.line([a, e], fill=c, width=w)
            r = w / 2; d.ellipse([a[0]-r, a[1]-r, a[0]+r, a[1]+r], fill=c); d.ellipse([e[0]-r, e[1]-r, e[0]+r, e[1]+r], fill=c)
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = P(T(t.GetPosition().x), T(t.GetPosition().y)); r = T(t.GetWidth(pcbnew.F_Cu)) * s / 2; rd = T(t.GetDrillValue()) * s / 2
        d.ellipse([x-r, y-r, x+r, y+r], fill=(230, 200, 60)); d.ellipse([x-rd, y-rd, x+rd, y+rd], fill=(20, 22, 30))
im.save(out); print(out, W, H)
