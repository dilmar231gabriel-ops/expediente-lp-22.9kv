"""Utilidades comunes de dibujo (DXF R2018 + PDF) con capas, estilos y membrete del modelo Ayaviri–Pucará."""
import sys
from pathlib import Path
import ezdxf, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy, LineweightPolicy
from ezdxf.enums import TextEntityAlignment as TA
sys.path.insert(0, str(Path(__file__).parent))
from params import PROYECTO

# Capas del modelo (perfil–planimetría: DLTCAD; láminas: detalles de armados)
CAPAS = {
    # perfil y planimetría
    "LAuxiliares": 8, "Txt_Planos": 100, "Perfil": 9, "Conductor_Fase": 80, "Cotas": 9, "Soportes_per": 6, "Soportes_pl": 30,
    "Txt_conductores": 140, "Bloque_ret": 12, "Bloques1": 15, "Dist_Seguridad": 6, "Via": 8, "Grilla": 9, "Eje_LP": 1,
    # láminas de detalle
    "DIBUJO": 7, "cotas": 6, "TEXTO": 4, "PLANTILLA": 3, "FeGo": 254, "ACCESORIOS": 133, "POSTE": 3, "MEMBRETE": 7,
    "CUADROS": 2, "CONDUCTOR": 1, "CRUZETAS": 157, "MATERIALES": 140, "HATCH": 8, "EQUIPOS": 30, "AISLADORES": 5, "NUMERACION": 2,
}
INI = PROYECTO.get("iniciales") or "".join(w[0] + "." for w in PROYECTO["proyectista"].split()[-3:])


def nuevo():
    doc = ezdxf.new("R2018", setup=True)
    for n, c in CAPAS.items():
        if n not in doc.layers: doc.layers.add(n, color=c)
    doc.layers.get("LAuxiliares").dxf.linetype = "DASHED"
    if "ARIAL" not in doc.styles: doc.styles.add("ARIAL", font="arial.ttf")
    if "ROMANS" not in doc.styles: doc.styles.add("ROMANS", font="romans.shx")
    doc.header["$INSUNITS"] = 4   # mm
    return doc


def T(msp, txt, x, y, h=2.5, layer="TEXTO", align=TA.BOTTOM_LEFT, rot=0, color=None, style="ARIAL"):
    a = {"layer": layer, "style": style, "rotation": rot}
    if color is not None: a["color"] = color
    t = msp.add_text(str(txt), height=h, dxfattribs=a); t.set_placement((x, y), align=align); return t


def L(msp, pts, layer="DIBUJO", close=False, color=None, lw=None, lt=None):
    a = {"layer": layer}
    if color is not None: a["color"] = color
    if lw: a["lineweight"] = lw
    if lt: a["linetype"] = lt
    return msp.add_lwpolyline(pts, close=close, dxfattribs=a)


def R(msp, x, y, w, h, layer="DIBUJO", color=None, lw=None):
    return L(msp, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer, True, color, lw)


def C(msp, x, y, r, layer="DIBUJO", color=None):
    a = {"layer": layer}
    if color is not None: a["color"] = color
    return msp.add_circle((x, y), r, dxfattribs=a)


def cota(msp, p1, p2, off, txt=None, h=2.0, layer="cotas"):
    """Cota alineada simple (líneas + texto) – compatible con cualquier visor."""
    import math
    (x1, y1), (x2, y2) = p1, p2
    dx, dy = x2 - x1, y2 - y1; Lg = math.hypot(dx, dy) or 1
    nx, ny = -dy / Lg * off, dx / Lg * off
    a, b = (x1 + nx, y1 + ny), (x2 + nx, y2 + ny)
    L(msp, [p1, (a[0] + nx * 0.15, a[1] + ny * 0.15)], layer); L(msp, [p2, (b[0] + nx * 0.15, b[1] + ny * 0.15)], layer)
    L(msp, [a, b], layer)
    for p, s in ((a, 1), (b, -1)):
        ux, uy = dx / Lg * s, dy / Lg * s
        L(msp, [p, (p[0] + ux * 1.6 - uy * 0.5, p[1] + uy * 1.6 + ux * 0.5), (p[0] + ux * 1.6 + uy * 0.5, p[1] + uy * 1.6 - ux * 0.5)], layer, True)
    ang = math.degrees(math.atan2(dy, dx))
    if ang > 90 or ang < -90: ang += 180
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    T(msp, txt, mx + nx / abs(off) * 0.8 if off else mx, my + ny / abs(off) * 0.8 if off else my, h, layer, TA.BOTTOM_CENTER, ang)


def globo(msp, x, y, n, tx, ty, r=2.6):
    """Globo de numeración de material con línea de llamada (como en las láminas del modelo)."""
    import math
    d = math.hypot(tx - x, ty - y) or 1
    L(msp, [(tx, ty), (x - (x - tx) / d * r, y - (y - ty) / d * r)], "TEXTO")
    C(msp, x, y, r, "TEXTO"); T(msp, n, x, y, 2.2, "TEXTO", TA.MIDDLE_CENTER)
    msp.add_circle((tx, ty), 0.45, dxfattribs={"layer": "TEXTO"})


CFG = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK,
                    lineweight_policy=LineweightPolicy.RELATIVE, lineweight_scaling=0.7)


def guardar(doc, out_dir, nombre, W, H, dpi_png=None):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    doc.saveas(out_dir / f"{nombre}.dxf")
    fig = plt.figure(figsize=(W / 25.4, H / 25.4)); ax = fig.add_axes([0, 0, 1, 1])
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=CFG).draw_layout(doc.modelspace(), finalize=False)
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(out_dir / f"{nombre}.pdf")
    if dpi_png: fig.savefig(out_dir / f"{nombre}.png", dpi=dpi_png)
    plt.close(fig)


UBIC = {"DEPARTAMENTO": PROYECTO["departamento"].upper(), "PROVINCIA": PROYECTO["provincias"].upper(), "DISTRITO": PROYECTO["distritos"].upper()}


def membrete_a4(msp, codigo, titulo, sub="", escala="S/E"):
    """Lámina A4 vertical (210 x 297 mm) con el membrete tipo del modelo (marco, franja de proyecto y cuadro de firmas)."""
    R(msp, 0, 0, 210, 297, "MEMBRETE"); R(msp, 10, 8, 192, 281, "MEMBRETE", lw=50)
    y0 = 8; h = 30
    R(msp, 10, y0, 192, h, "MEMBRETE")
    L(msp, [(10, y0 + 10), (202, y0 + 10)], "MEMBRETE"); L(msp, [(10, y0 + 20), (202, y0 + 20)], "MEMBRETE")
    for x in (52, 160): L(msp, [(x, y0), (x, y0 + h)], "MEMBRETE")
    T(msp, "DISEÑO :", 12, y0 + 23, 1.8, "MEMBRETE"); T(msp, INI, 30, y0 + 23, 1.8, "MEMBRETE")
    T(msp, "REVISÓ :", 12, y0 + 13, 1.8, "MEMBRETE"); T(msp, "—", 30, y0 + 13, 1.8, "MEMBRETE")
    T(msp, "FECHA :", 12, y0 + 3, 1.8, "MEMBRETE"); T(msp, PROYECTO["fecha"].upper(), 26, y0 + 3, 1.8, "MEMBRETE")
    T(msp, "PROYECTISTA:", 54, y0 + 26, 1.5, "MEMBRETE"); T(msp, PROYECTO["proyectista"].upper(), 106, y0 + 22.5, 2.0, "MEMBRETE", TA.BOTTOM_CENTER)
    T(msp, PROYECTO["nombre"], 106, y0 + 13.2, 1.75, "MEMBRETE", TA.BOTTOM_CENTER)
    T(msp, titulo, 106, y0 + 5.0, 2.2, "MEMBRETE", TA.BOTTOM_CENTER)
    if sub: T(msp, sub, 106, y0 + 1.6, 2.0, "MEMBRETE", TA.BOTTOM_CENTER)
    T(msp, "ESCALA :", 162, y0 + 23, 1.8, "MEMBRETE"); T(msp, escala, 178, y0 + 23, 1.8, "MEMBRETE")
    T(msp, "LÁMINA N.°", 162, y0 + 14, 1.8, "MEMBRETE"); T(msp, codigo, 181, y0 + 3, 3.5, "MEMBRETE", TA.BOTTOM_CENTER)
    return y0 + h


def membrete_grande(msp, W, H, codigo, titulo, escala_h, escala_v=None, hoja=""):
    """Membrete para planos A1/A3 (cuadro inferior derecho, campos del modelo: DIS., DIB., REV., APR., ubicación, escala, versión)."""
    m = 10
    R(msp, 0, 0, W, H, "MEMBRETE"); R(msp, m, m, W - 2 * m, H - 2 * m, "MEMBRETE", lw=50)
    w, h = 300, 48; x0, y0 = W - m - w, m
    R(msp, x0, y0, w, h, "MEMBRETE")
    L(msp, [(x0, y0 + 24), (x0 + 135, y0 + 24)], "MEMBRETE"); L(msp, [(x0 + 135, y0), (x0 + 135, y0 + h)], "MEMBRETE")
    L(msp, [(x0 + 190, y0), (x0 + 190, y0 + h)], "MEMBRETE")
    for k in (12, 24, 36): L(msp, [(x0 + 135, y0 + k), (x0 + 190, y0 + k)], "MEMBRETE")
    L(msp, [(x0 + 190, y0 + 24), (x0 + w, y0 + 24)], "MEMBRETE"); L(msp, [(x0 + 245, y0), (x0 + 245, y0 + 24)], "MEMBRETE")
    T(msp, "PROYECTISTA:", x0 + 2, y0 + 43, 1.8, "MEMBRETE")
    T(msp, PROYECTO["proyectista"].upper(), x0 + 67, y0 + 34, 3.0, "MEMBRETE", TA.BOTTOM_CENTER)
    T(msp, "PROYECTO:", x0 + 2, y0 + 19.5, 1.8, "MEMBRETE")
    T(msp, PROYECTO["nombre"], x0 + 67, y0 + 13.5, 2.2, "MEMBRETE", TA.BOTTOM_CENTER)
    T(msp, titulo, x0 + 67, y0 + 4, 2.8, "MEMBRETE", TA.BOTTOM_CENTER)
    for k, (a, b) in enumerate([("DIS. :", INI), ("DIB. :", "—"), ("REV. :", "—"), ("APR. :", "—")]):
        yy = y0 + 39 - 12 * k
        T(msp, a, x0 + 138, yy, 2.0, "MEMBRETE"); T(msp, b, x0 + 160, yy, 2.0, "MEMBRETE")
    for k, (a, b) in enumerate(list(UBIC.items()) + [("FECHA", PROYECTO["fecha"].upper())]):
        T(msp, f"{a}", x0 + 193, y0 + 41 - 5.2 * k, 1.8, "MEMBRETE"); T(msp, f": {b}", x0 + 217, y0 + 41 - 5.2 * k, 1.8, "MEMBRETE")
    T(msp, "ESCALA :", x0 + 193, y0 + 18, 2.0, "MEMBRETE")
    T(msp, f"H : {escala_h}" if escala_v else escala_h, x0 + 200, y0 + 11, 2.2, "MEMBRETE")
    if escala_v: T(msp, f"V : {escala_v}", x0 + 200, y0 + 4, 2.2, "MEMBRETE")
    T(msp, "VERSIÓN: 01", x0 + 248, y0 + 18, 2.0, "MEMBRETE")
    T(msp, "LÁMINA:", x0 + 248, y0 + 11, 2.0, "MEMBRETE"); T(msp, codigo, x0 + 272, y0 + 3, 4.2, "MEMBRETE", TA.BOTTOM_CENTER)
    if hoja: T(msp, hoja, x0 + 248, y0 + 3, 1.6, "MEMBRETE")
    return x0, y0, w, h
