"""Reescribe un DXF a DXF R12 (AC1009) con solo entidades básicas: LINE, POLYLINE, CIRCLE, ARC, TEXT.
Máxima compatibilidad con cualquier versión de AutoCAD."""
import sys, math, ezdxf
from ezdxf.enums import TextEntityAlignment as TA
src, dst = sys.argv[1], sys.argv[2]
a = ezdxf.readfile(src); b = ezdxf.new("R12", setup=True)
for ly in a.layers:
    n = ly.dxf.name
    if n not in b.layers: b.layers.add(n, color=abs(ly.color) or 7)
mb = b.modelspace()
def lay(e):
    l = e.dxf.get("layer", "0"); return l if l in b.layers else "0"
def att(e):
    d = {"layer": lay(e)}
    c = e.dxf.get("color", 256)
    if c not in (0, 256): d["color"] = c
    return d
H = {0: "LEFT", 1: "CENTER", 2: "RIGHT", 3: "ALIGNED", 4: "MIDDLE", 5: "FIT"}
def text(e, txt, ins, h, rot, halign=0, valign=0, align_pt=None):
    t = mb.add_text(txt.replace("\n", " "), dxfattribs={**att(e), "height": h, "rotation": rot, "style": "STANDARD"})
    t.dxf.insert = ins
    if halign or valign:
        t.dxf.halign = min(halign, 2) if halign not in (3, 5) else 0; t.dxf.valign = valign
        t.dxf.align_point = align_pt if align_pt is not None else ins
n = 0
def put(e):
    global n
    t = e.dxftype()
    if t == "LINE": mb.add_line(e.dxf.start, e.dxf.end, dxfattribs=att(e))
    elif t == "CIRCLE": mb.add_circle(e.dxf.center, e.dxf.radius, dxfattribs=att(e))
    elif t == "ARC": mb.add_arc(e.dxf.center, e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle, dxfattribs=att(e))
    elif t == "LWPOLYLINE":
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(pts) >= 2: mb.add_polyline2d(pts, close=e.closed, dxfattribs=att(e))
    elif t == "POLYLINE":
        pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if len(pts) >= 2: mb.add_polyline2d(pts, close=e.is_closed, dxfattribs=att(e))
    elif t in ("TEXT", "ATTRIB"):
        text(e, e.dxf.text, e.dxf.insert, e.dxf.height, e.dxf.get("rotation", 0), e.dxf.get("halign", 0), e.dxf.get("valign", 0), e.dxf.get("align_point", None))
    elif t == "MTEXT":
        text(e, e.plain_text(), e.dxf.insert, e.dxf.char_height, e.dxf.get("rotation", 0))
    elif t == "INSERT":
        for v in e.virtual_entities(): put(v)
        for at in e.attribs: put(at)
        return
    elif t == "POINT": mb.add_point(e.dxf.location, dxfattribs=att(e))
    else: return
    n += 1
for e in a.modelspace(): put(e)
b.saveas(dst)
c = ezdxf.readfile(dst)
print(dst, c.dxfversion, len(c.modelspace()), "entidades; errores auditoría:", len(c.audit().errors))
