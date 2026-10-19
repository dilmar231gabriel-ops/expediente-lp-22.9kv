"""Genera un programa AutoLISP que dibuja el plano dentro de AutoCAD con entmake (sin abrir archivos DXF)."""
import sys, math, ezdxf
src, dst, cmd, titulo = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
doc = ezdxf.readfile(src); msp = doc.modelspace()
def s(t):
    out = []
    for ch in t:
        if ch == '"': out.append('\\"')
        elif ch == "\\": out.append("\\\\")
        elif ord(ch) < 128: out.append(ch)
        else: out.append("\\\\U+%04X" % ord(ch))
    return '"' + "".join(out) + '"'
f = lambda v: ("%.4f" % v)
lay = {}
for ly in doc.layers: lay[ly.dxf.name] = abs(ly.color) or 7
L = [f";; {titulo}",
     ";; Uso: APPLOAD (o arrastrar este archivo a AutoCAD) y luego escribir el comando " + cmd.upper(),
     "(defun lp-capa (n c) (if (not (tblsearch \"LAYER\" n)) (entmake (list '(0 . \"LAYER\") '(100 . \"AcDbSymbolTableRecord\") '(100 . \"AcDbLayerTableRecord\") (cons 2 n) '(70 . 0) (cons 62 c) '(6 . \"Continuous\")))))",
     "(defun lp-l (c x1 y1 x2 y2) (entmake (list '(0 . \"LINE\") (cons 8 c) (list 10 x1 y1 0.0) (list 11 x2 y2 0.0))))",
     "(defun lp-c (c x y r) (entmake (list '(0 . \"CIRCLE\") (cons 8 c) (list 10 x y 0.0) (cons 40 r))))",
     "(defun lp-a (c x y r a1 a2) (entmake (list '(0 . \"ARC\") (cons 8 c) (list 10 x y 0.0) (cons 40 r) (cons 50 a1) (cons 51 a2))))",
     "(defun lp-p (c cerr pts) (entmake (append (list '(0 . \"LWPOLYLINE\") '(100 . \"AcDbEntity\") (cons 8 c) '(100 . \"AcDbPolyline\") (cons 90 (length pts)) (cons 70 cerr)) (mapcar '(lambda (p) (cons 10 p)) pts))))",
     "(defun lp-t (c x y h r txt ha va ax ay) (entmake (list '(0 . \"TEXT\") (cons 8 c) (list 10 x y 0.0) (cons 40 h) (cons 1 txt) (cons 50 r) '(7 . \"Standard\") (cons 72 ha) (cons 73 va) (list 11 ax ay 0.0))))",
     f"(defun c:{cmd} ( / oe)",
     "  (setq oe (getvar \"CMDECHO\")) (setvar \"CMDECHO\" 0)"]
for n, c in lay.items(): L.append(f"  (lp-capa {s(n)} {c})")
cnt = 0
for e in msp:
    t = e.dxftype(); c = s(e.dxf.layer)
    if t == "LINE":
        a, b = e.dxf.start, e.dxf.end; L.append(f"  (lp-l {c} {f(a.x)} {f(a.y)} {f(b.x)} {f(b.y)})")
    elif t == "CIRCLE":
        p = e.dxf.center; L.append(f"  (lp-c {c} {f(p.x)} {f(p.y)} {f(e.dxf.radius)})")
    elif t == "ARC":
        p = e.dxf.center; L.append(f"  (lp-a {c} {f(p.x)} {f(p.y)} {f(e.dxf.radius)} {f(math.radians(e.dxf.start_angle))} {f(math.radians(e.dxf.end_angle))})")
    elif t == "POLYLINE":
        pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        if len(pts) < 2: continue
        L.append(f"  (lp-p {c} {1 if e.is_closed else 0} (list " + " ".join(f"(list {f(x)} {f(y)})" for x, y in pts) + "))")
    elif t == "TEXT":
        txt = e.dxf.text.strip()
        if not txt: continue
        ins = e.dxf.insert; ha = e.dxf.get("halign", 0); va = e.dxf.get("valign", 0)
        ap = e.dxf.get("align_point", ins) if (ha or va) else ins
        L.append(f"  (lp-t {c} {f(ins.x)} {f(ins.y)} {f(e.dxf.height)} {f(math.radians(e.dxf.get('rotation', 0)))} {s(txt)} {ha} {va} {f(ap.x)} {f(ap.y)})")
    elif t == "POINT":
        p = e.dxf.location; L.append(f"  (entmake (list '(0 . \"POINT\") (cons 8 {c}) (list 10 {f(p.x)} {f(p.y)} 0.0)))")
    else: continue
    cnt += 1
L += ["  (setvar \"CMDECHO\" oe)", "  (command \"_.ZOOM\" \"_E\")",
      f"  (princ \"\\n{titulo}: {cnt} objetos dibujados. Guarde el dibujo como DWG.\")", "  (princ))",
      f"(princ \"\\nCargado. Escriba {cmd.upper()} para dibujar el plano.\")", "(princ)"]
open(dst, "w", encoding="ascii").write("\n".join(L) + "\n")
print(dst, cnt, "objetos")
