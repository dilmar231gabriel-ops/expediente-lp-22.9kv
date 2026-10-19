"""Convierte un DXF a una versión "simple" R2010 que abre en cualquier AutoCAD (incluido 2027), BricsCAD, ZWCAD o LibreCAD.
Se queda solo con entidades básicas: LWPOLYLINE, CIRCLE y TEXT (estilo Standard, caracteres del juego Windows-1252).
Los bloques se descomponen, las líneas y arcos pasan a polilíneas y el MTEXT a líneas de TEXT.

Uso: python dxf_compatible.py ENTRADA.dxf [SALIDA.dxf]       (sin SALIDA escribe ENTRADA_COMPATIBLE.dxf)
     python dxf_compatible.py CARPETA                        (convierte todos los .dxf de la carpeta)"""
import sys
from pathlib import Path
import ezdxf
from ezdxf import path as zpath

REEMPLAZOS = {"Δ": "Delta ", "σ": "s", "≤": "<=", "≥": ">=", "√": "raiz ", "π": "pi", "α": "alfa", "φ": "fi", "→": "->", "×": "x", "·": ".", "−": "-",
              "≈": "~", "′": "'", "″": '"', "Ω": "ohm", "μ": "u", "“": '"', "”": '"', "‘": "'", "’": "'", "…": "...", "⁻": "-", "¹": "1", "²": "2", "³": "3"}


def _txt(s):
    s = "".join(REEMPLAZOS.get(ch, ch) for ch in str(s))
    return s.encode("cp1252", "replace").decode("cp1252").replace("?", "?")


def convertir(src, dst=None):
    src = Path(src); dst = Path(dst) if dst else src.with_name(src.stem + "_COMPATIBLE.dxf")
    old = ezdxf.readfile(src)
    new = ezdxf.new("R2010"); new.header["$DWGCODEPAGE"] = "ANSI_1252"; new.header["$INSUNITS"] = old.header.get("$INSUNITS", 6)
    msp = new.modelspace()
    for ly in old.layers:
        n = ly.dxf.name
        if n not in new.layers:
            new.layers.add(n, color=abs(ly.dxf.get("color", 7)) or 7)

    def color_de(e):
        c = e.dxf.get("color", 256)
        return c if c not in (0,) else 256

    def emitir(e, n=0):
        t = e.dxftype(); at = {"layer": e.dxf.get("layer", "0"), "color": color_de(e)}
        try:
            if t == "INSERT":
                if n < 8:
                    for v in e.virtual_entities(): emitir(v, n + 1)
            elif t == "LINE":
                msp.add_lwpolyline([e.dxf.start[:2], e.dxf.end[:2]], dxfattribs=at)
            elif t == "LWPOLYLINE":
                pts = [p[:2] for p in e.get_points("xy")]
                if len(pts) > 1:
                    if any(b for *_, b in e.get_points("xyb") if b):
                        pts = [v[:2] for v in zpath.make_path(e).flattening(0.05)]
                    msp.add_lwpolyline(pts, close=e.closed, dxfattribs={**at, "const_width": e.dxf.get("const_width", 0)})
            elif t in ("POLYLINE", "ARC", "ELLIPSE", "SPLINE"):
                pts = [v[:2] for v in zpath.make_path(e).flattening(0.05)]
                if len(pts) > 1: msp.add_lwpolyline(pts, dxfattribs=at)
            elif t == "CIRCLE":
                msp.add_circle((e.dxf.center.x, e.dxf.center.y), e.dxf.radius, dxfattribs=at)
            elif t in ("TEXT", "ATTRIB"):
                txt = _txt(e.dxf.text)
                if txt.strip():
                    x = msp.add_text(txt, height=e.dxf.get("height", 2.5), rotation=e.dxf.get("rotation", 0), dxfattribs={**at, "style": "Standard"})
                    x.dxf.insert = e.dxf.insert; x.dxf.halign = e.dxf.get("halign", 0); x.dxf.valign = e.dxf.get("valign", 0)
                    if e.dxf.hasattr("align_point"): x.dxf.align_point = e.dxf.align_point
            elif t == "MTEXT":
                h = e.dxf.get("char_height", 2.5); ins = e.dxf.insert; rot = e.dxf.get("rotation", 0)
                for i, linea in enumerate(e.plain_text().splitlines()):
                    if linea.strip():
                        msp.add_text(_txt(linea), height=h, rotation=rot, dxfattribs={**at, "style": "Standard", "insert": (ins[0], ins[1] - 1.5 * h * (i + 1))})
            elif t == "HATCH":
                for bp in e.paths:
                    try:
                        pts = [v[:2] for v in zpath.from_hatch_boundary_path(bp).flattening(0.05)]
                        if len(pts) > 2: msp.add_lwpolyline(pts, close=True, dxfattribs=at)
                    except Exception:
                        pass
            elif t == "POINT":
                msp.add_circle((e.dxf.location.x, e.dxf.location.y), 0.2, dxfattribs=at)
        except Exception:
            pass

    for e in old.modelspace(): emitir(e)
    new.saveas(dst)          # R2007+ : el archivo se escribe en UTF-8 (norma DXF)
    return dst


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    p = Path(sys.argv[1])
    if p.is_dir():
        for f in sorted(p.glob("*.dxf")):
            if not f.stem.endswith("_COMPATIBLE"): print(convertir(f))
    else:
        print(convertir(p, sys.argv[2] if len(sys.argv) > 2 else None))
