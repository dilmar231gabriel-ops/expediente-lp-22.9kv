"""Láminas de detalle A4 (formato del modelo LD-LP-xx): armados con lista de materiales y globos, retenida, puestas a tierra,
cimentación, cruceta y señalización. Uso: python p07_laminas.py OUTDIR"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from params import *
from catalogo import MATD, BOM, RET_RI, PAT_KIT, ARM_DESC, PUENTE_M, cable_ret
from planos_common import *

OUT = Path(sys.argv[1])
LISTA = []


class Dib:
    def __init__(self, msp, cx, ytop, s):
        self.m, self.cx, self.yt, self.s = msp, cx, ytop, s
    def P(self, x, y): return (self.cx + x * self.s, self.yt + y * self.s)
    def line(self, pts, layer="DIBUJO", **k): return L(self.m, [self.P(*p) for p in pts], layer, **k)
    def rect(self, x, y, w, h, layer="DIBUJO", **k): return self.line([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer, close=True, **k)
    # --- elementos
    def poste(self, Lshow=3.2, Dtop=0.16, taper=0.015):
        a, b = Dtop / 2, (Dtop + taper * Lshow) / 2
        self.line([(-a, 0), (a, 0), (b, -Lshow)], "POSTE"); self.line([(-a, 0), (-b, -Lshow)], "POSTE")
        for k in range(3): self.line([(-b - 0.02, -Lshow + 0.05 * k - 0.02), (b + 0.02, -Lshow + 0.05 * k + 0.02)], "POSTE")
    def w(self, y, Dtop=0.16, taper=0.015): return (Dtop + taper * (-y)) / 2
    def cruceta(self, y, half=1.2, layer="CRUZETAS"):
        self.rect(-half, y - 0.032, 2 * half, 0.064, layer)
        self.rect(-self.w(y) - 0.03, y - 0.05, 2 * self.w(y) + 0.06, 0.10, "FeGo")          # abrazadera
    def riostras(self, y, xr=0.70, dy=0.60):
        for sgn in (-1, 1):
            self.line([(sgn * xr, y - 0.032), (sgn * (self.w(y - dy) + 0.02), y - dy)], "FeGo")
        self.rect(-self.w(y - dy) - 0.03, y - dy - 0.04, 2 * self.w(y - dy) + 0.06, 0.08, "FeGo")
    def pin(self, x, ybase, espiga=0.25, h=0.19):
        self.line([(x, ybase), (x, ybase + espiga)], "FeGo")
        y0 = ybase + espiga
        for k, wd in enumerate((0.085, 0.11, 0.13)):
            yy = y0 + h * k / 3
            self.line([(x - wd * 0.6, yy), (x - wd, yy + h / 6), (x + wd, yy + h / 6), (x + wd * 0.6, yy)], "AISLADORES", close=True)
        self.line([(x - 0.05, y0 + h), (x + 0.05, y0 + h)], "AISLADORES")
        return y0 + h            # altura del conductor
    def susp_h(self, x0, y, Lg=0.55, dirx=1):
        """aislador polimérico horizontal (anclaje) desde x0 hacia dirx; devuelve extremo."""
        x1 = x0 + dirx * Lg
        self.line([(x0, y), (x1, y)], "AISLADORES")
        for k in range(6):
            xx = x0 + dirx * (0.08 + k * (Lg - 0.16) / 5)
            self.line([(xx, y - 0.045), (xx, y + 0.045)], "AISLADORES")
        g = x1 + dirx * 0.10
        self.line([(x1, y), (g, y + 0.03), (g, y - 0.03), (x1, y)], "ACCESORIOS")      # grapa pistola
        return g
    def conductor(self, pts): self.line(pts, "CONDUCTOR")
    def cutout(self, x, y):
        self.line([(x, y), (x + 0.12, y + 0.40)], "EQUIPOS"); self.line([(x - 0.04, y + 0.02), (x + 0.04, y - 0.02)], "EQUIPOS")
        self.rect(x - 0.035, y + 0.08, 0.07, 0.24, "EQUIPOS")
    def pararrayo(self, x, y):
        self.rect(x - 0.04, y, 0.08, 0.27, "EQUIPOS")
        for k in range(5): self.line([(x - 0.065, y + 0.04 + 0.05 * k), (x + 0.065, y + 0.04 + 0.05 * k)], "EQUIPOS")
    def reconectador(self, x, y):
        self.rect(x - 0.42, y, 0.84, 0.55, "EQUIPOS")
        for k in (-0.25, 0, 0.25): self.line([(x + k, y + 0.55), (x + k, y + 0.85)], "EQUIPOS")
        T(self.m, "RECONECTADOR", *self.P(x, y + 0.25), 1.6, "EQUIPOS", TA.MIDDLE_CENTER)
    def g(self, n, xm, ym, dx, dy):
        X, Y = self.P(xm, ym); globo(self.m, X + dx, Y + dy, n, X, Y)


def tabla_mat(msp, items, y_top, x0=12, w=188, rh=4.0):
    """Tabla de materiales del modelo: ITEM | DESCRIPCIÓN | UND. | CANT."""
    cols = [x0, x0 + 9, x0 + w - 26, x0 + w - 13, x0 + w]
    y = y_top
    R(msp, x0, y - rh, w, rh, "CUADROS")
    for xx in cols[1:-1]: L(msp, [(xx, y), (xx, y - rh * (len(items) + 1))], "CUADROS")
    for t, xx in zip(["ITEM", "DESCRIPCIÓN", "UND.", "CANT."], cols):
        T(msp, t, xx + 1, y - rh + 1.2, 1.9, "MATERIALES")
    y -= rh
    for k, (desc, und, cant) in enumerate(items, 1):
        R(msp, x0, y - rh, w, rh, "CUADROS")
        T(msp, k, cols[0] + 4.5, y - rh + 1.1, 1.8, "MATERIALES", TA.BOTTOM_CENTER)
        T(msp, desc[:118], cols[1] + 1, y - rh + 1.1, 1.65, "MATERIALES")
        T(msp, und, cols[2] + 6.5, y - rh + 1.1, 1.8, "MATERIALES", TA.BOTTOM_CENTER)
        q = f"{cant:g}".replace(".", ",") if isinstance(cant, (int, float)) else cant
        T(msp, q, cols[3] + 6.5, y - rh + 1.1, 1.8, "MATERIALES", TA.BOTTOM_CENTER)
        y -= rh
    return y


def items_armado(arm, poste):
    it = [(f"Poste de C.A.C. {poste} daN, con perilla", "u", 1)]
    for cod, q in BOM[arm].items():
        m = MATD[cod]; it.append((m[1], m[2], q))
    if arm in PUENTE_M: it.append(("Conductor AAAC 70 mm² para puentes y conexión a equipos", "m", PUENTE_M[arm]))
    return it


def lamina(codigo, titulo, sub, fn, items=None, escala="S/E", notas=()):
    doc = nuevo(); msp = doc.modelspace()
    ytb = membrete_a4(msp, codigo, titulo, sub, escala)
    yt = 284
    ybot = fn(msp)
    if items:
        rh = 4.0 if len(items) <= 18 else 3.3
        T(msp, "LISTA DE MATERIALES", 12, 6 + ytb + rh * (len(items) + 1) + 3, 2.2, "MATERIALES")
        tabla_mat(msp, items, ytb + 4 + rh * (len(items) + 1), rh=rh)
    for k, n in enumerate(notas):
        T(msp, ("NOTAS: " if k == 0 else "            ") + n, 12, 284.5 - 3.3 * k, 1.6, "TEXTO")
    import unicodedata, re
    slug = re.sub(r"[^A-Za-z0-9]+", "_", unicodedata.normalize("NFKD", titulo + (" " + sub if sub else "")).encode("ascii", "ignore").decode()).strip("_")
    nombre = f"{codigo}_{slug}"[:80]
    guardar(doc, OUT, nombre, 210, 297)
    LISTA.append((codigo, titulo, sub, nombre))


# ----------------------------------------------------------------------------------------------- armados
YC = -1.40           # eje de cruceta bajo la cabeza del poste (conductor inferior a 1,10 m)
def ps13(msp, arm="PS1-3", doble=False):
    d = Dib(msp, 105, 256, 40)            # 1:25
    d.poste(3.0)
    T(msp, "VISTA FRONTAL", *d.P(0, -3.25), 2.4, "TEXTO", TA.TOP_CENTER)
    d.cruceta(YC); d.riostras(YC)
    yc_top = d.pin(0, 0.0, espiga=0.12)
    yb = []
    xs = (-1.0, 1.0) if not doble else (-1.08, -0.92, 0.92, 1.08)
    for x in xs: yb.append(d.pin(x, YC + 0.032, espiga=0.10))
    d.conductor([(-0.15, yc_top), (0.15, yc_top)])
    for x in (-1.0, 1.0): d.conductor([(x - 0.18, yb[0]), (x + 0.18, yb[0])])
    cota(msp, d.P(-1.2, YC - 0.05), d.P(1.2, YC - 0.05), -14, "2 400")
    cota(msp, d.P(-1.0, yb[0]), d.P(1.0, yb[0]), 10, "2 000")
    cota(msp, d.P(1.35, yc_top), d.P(1.35, yb[0]), -6, "1 400")
    cota(msp, d.P(-1.35, 0), d.P(-1.35, YC), 6, "1 400")
    n = 2
    d.g(n, -1.2, YC, -10, -14); d.g(n + 1, 0.85, YC - 0.45, 14, -6); d.g(n + 2, -d.w(YC), YC, -16, 6)
    d.g(n + 3, -d.w(YC - 0.6), YC - 0.6, -20, -4); d.g(n + 5, -1.0, yb[0] - 0.1, -6, 14); d.g(n + 7, 0, yc_top - 0.1, -16, 10)
    d.g(1, 0, -2.6, 16, 0)
    if doble:
        dl = Dib(msp, 105, 268, 40)
    return 120


def ps13_doble(msp):
    return ps13(msp, "PA1-3", True)


def tension(msp, arm):
    """PA2-3 / PR3-3 / PTH-3 / DT-3 / PSER-3: vista frontal (transversal) y vista lateral con cadenas de anclaje."""
    d = Dib(msp, 62, 254, 30)          # vista frontal 1:33
    d.poste(3.4); d.cruceta(YC); d.riostras(YC)
    T(msp, "VISTA FRONTAL", *d.P(0, -3.65), 2.2, "TEXTO", TA.TOP_CENTER)
    yb = YC + 0.10
    for x in (-1.0, 1.0):
        d.line([(x, YC + 0.032), (x, yb)], "FeGo"); C(msp, *d.P(x, yb + 0.02), 0.6, "AISLADORES")
    C(msp, *d.P(0, 0.12), 0.6, "AISLADORES"); d.line([(0, 0), (0, 0.10)], "FeGo")
    if arm in ("PA2-3", "PR3-3", "TS-3"):
        d.pin(0, 0.0, espiga=0.12)
    cota(msp, d.P(-1.2, YC - 0.05), d.P(1.2, YC - 0.05), -10, "2 400")
    cota(msp, d.P(1.35, 0.12), d.P(1.35, yb), -6, "1 400")
    v = Dib(msp, 152, 254, 30)          # vista lateral
    v.poste(3.4)
    T(msp, "VISTA LATERAL (EN EL SENTIDO DE LA LÍNEA)", *v.P(0, -3.65), 2.2, "TEXTO", TA.TOP_CENTER)
    for sgn in ((-1, 1) if arm != "PTH-3" else (-1,)):
        v.rect(sgn * 0.11 - 0.032, YC - 0.032, 0.064, 0.064, "CRUZETAS")
        e = v.susp_h(sgn * 0.14, YC + 0.10, dirx=sgn); v.conductor([(e, YC + 0.10), (e + sgn * 0.35, YC + 0.10)])
        e2 = v.susp_h(sgn * 0.10, 0.12, dirx=sgn); v.conductor([(e2, 0.12), (e2 + sgn * 0.35, 0.12)])
    v.rect(-0.14, YC - 0.05, 0.28, 0.10, "FeGo")
    if arm in ("PA2-3", "PR3-3", "TS-3"):
        v.conductor([(-0.75, YC + 0.10), (-0.45, YC + 0.35), (0.45, YC + 0.35), (0.75, YC + 0.10)])
    cota(msp, v.P(-0.14, YC - 0.25), v.P(-0.79, YC - 0.25), 6, "≈ 650")
    # equipos
    if arm in ("PTH-3", "DT-3", "PSER-3"):
        ye = YC - 0.80
        d.cruceta(ye); d.riostras(ye, 0.6, 0.5)
        for x in (-0.9, 0.0, 0.9):
            d.cutout(x - 0.18, ye + 0.05); d.pararrayo(x + 0.22, ye + 0.03)
        T(msp, "Cut-out 38 kV 170 kV-BIL", *d.P(1.3, ye + 0.30), 1.7, "TEXTO")
        T(msp, "y pararrayos 24 kV", *d.P(1.3, ye + 0.15), 1.7, "TEXTO")
        if arm == "DT-3":
            T(msp, "Derivación (PSEC-3P)", *d.P(1.3, ye - 0.05), 1.7, "TEXTO")
    if arm == "PSER-3":
        d.reconectador(0, -3.30)
        d.line([(-0.45, -2.6), (-0.10, -2.6)], "FeGo"); d.line([(0.45, -2.6), (0.10, -2.6)], "FeGo")
    for k, (xm, ym, dx, dy) in enumerate([(0, -3.0, 12, -2), (-1.2, YC, -8, -12), (0.7, YC - 0.4, 14, -8), (-0.08, YC, -14, 8), (0.9, YC + 0.06, 10, 10), (-1.0, YC + 0.12, -12, 12)], 1):
        d.g(k, xm, ym, dx, dy)
    v.g(7, -0.45, YC + 0.10, -6, 10); v.g(8, -0.84, YC + 0.10, -8, -10)
    return 120


def ret_RI(msp):
    d = Dib(msp, 70, 262, 12)            # 1:83
    d.line([(0, 0), (0.12, -11), (0.24, -11), (0.12, 0)], "POSTE")
    d.line([(-3, -9.8), (14, -9.8)], "DIBUJO")
    for k in range(18): d.line([(-3 + k, -9.8), (-2.6 + k, -10.2)], "HATCH")
    ya = -1.4 - 0.4
    xa = 0.15
    xs = xa + (9.8 + ya) * math.tan(math.radians(37))
    d.line([(xa, ya), (xs, -9.8)], "CONDUCTOR")
    d.line([(xs, -9.8), (xs + 2.0 * math.tan(math.radians(37)) * 0.75, -11.6)], "FeGo")
    d.rect(xs + 1.0, -12.0, 0.5, 0.2, "PLANTILLA")
    d.rect(xs + 0.75, -11.8, 0.8, -0.0001, "PLANTILLA")
    R(msp, *d.P(xs + 0.6, -11.8), 0.8 * 12, 2.0 * 12, "PLANTILLA")
    xi = xa + (2.6) * math.tan(math.radians(37))
    d.rect(xi - 0.12, ya - 2.6 - 0.25, 0.24, 0.5, "AISLADORES")
    T(msp, "37°", *d.P(xa + 0.35, ya - 1.2), 2.2, "cotas")
    cota(msp, d.P(-0.4, 0), d.P(-0.4, ya), 4, "1 800")
    cota(msp, d.P(-0.4, ya), d.P(-0.4, -9.8), 4, "≈ 8 000")
    cota(msp, d.P(xa, -10.6), d.P(xs, -10.6), -4, "≈ 6 000")
    for k, (xm, ym, dx, dy) in enumerate([(xa + 2, ya - 2.7, 14, 6), (xi, ya - 2.6, 16, -2), (xs - 1, -8.5, 16, 4), (xs, -9.8, 16, -6),
                                          (xs + 1.2, -11.9, 16, -4), (0.18, ya, -14, 6)], 1):
        d.g(k, xm, ym, dx, dy)
    T(msp, "RETENIDA INCLINADA – ELEVACIÓN", *d.P(5, -13.0), 2.3, "TEXTO", TA.TOP_CENTER)
    T(msp, "Bloque de concreto armado 0,50 × 0,50 × 0,20 m;", 120, 200, 1.9, "TEXTO")
    T(msp, "excavación 0,80 × 0,80 × 2,00 m, relleno compactado", 120, 196, 1.9, "TEXTO")
    T(msp, "en capas de 0,20 m (Anexo 7, Vol. VI).", 120, 192, 1.9, "TEXTO")
    T(msp, "Aislador de tracción a 2,6 m del amarre.", 120, 186, 1.9, "TEXTO")
    T(msp, "Ángulo con el eje del poste: 37°.", 120, 182, 1.9, "TEXTO")
    return 120


def pat(msp, n):
    d = Dib(msp, 38 if n == 2 else 75, 222, 20 if n == 2 else 26)
    d.line([(0, 2.0), (0.1, -1.8), (0.25, -1.8), (0.35, 2.0)], "POSTE")
    d.line([(-1.8, 0), (6.5 if n == 2 else 2.4, 0)], "DIBUJO")
    for k in range(int((8.3 if n == 2 else 4.2) / 0.3)): d.line([(-1.8 + k * 0.3, 0), (-1.65 + k * 0.3, -0.12)], "HATCH")
    d.line([(0.4, 1.9), (0.4, 0.05), (1.2, -0.4)], "CONDUCTOR")
    xs = [1.2] + ([1.2 + 5.0] if n == 2 else [])
    for x in xs:
        d.line([(x - 0.4, -0.05), (x - 0.4, -2.75), (x + 0.4, -2.75), (x + 0.4, -0.05)], "PLANTILLA")
        d.rect(x - 0.2, -0.2, 0.4, 0.2, "PLANTILLA")
        d.line([(x, -0.3), (x, -2.7)], "FeGo")
        d.line([(x - 0.3, -0.3 - 0.0), (x + 0.3, -0.3)], "HATCH")
    if n == 2:
        d.line([(1.2, -0.45), (6.2, -0.45)], "CONDUCTOR")
        cota(msp, d.P(1.2, -3.1), d.P(6.2, -3.1), -4, "5 000")
    cota(msp, d.P(xs[0] + 0.55, -0.3), d.P(xs[0] + 0.55, -2.7), -4, "2 400")
    cota(msp, d.P(xs[0] - 0.4, -2.95), d.P(xs[0] + 0.4, -2.95), -4, "Ø 800")
    for k, (xm, ym, dx, dy) in enumerate([(1.2, -1.5, 16, 0), (0.4, 1.0, 14, 4), (0.2, 1.7, -14, 4), (1.2, -0.3, 16, 10), (1.2, -0.1, -14, 10),
                                          (1.2, -1.0, -16, -4), (0.4, 0.5, 14, -4), (1.0, -2.2, -16, 4)], 1):
        d.g(k, xm, ym, dx, dy)
    T(msp, f"PUESTA A TIERRA TIPO PAT-{n} – ELEVACIÓN", 105, 134, 2.3, "TEXTO", TA.TOP_CENTER)
    return 120


def cimentacion(msp):
    for k, (pst, cx) in enumerate((("12/300 – 12/400", 60), ("13/400", 150))):
        h = 1.8 if k == 0 else 1.9; De = 0.8 if k == 0 else 0.9
        d = Dib(msp, cx, 262, 30)
        d.line([(-1.2, 0), (1.2, 0)], "DIBUJO")
        for j in range(16): d.line([(-1.2 + j * 0.15, 0), (-1.1 + j * 0.15, -0.08)], "HATCH")
        d.line([(-0.16, 1.0), (-0.17, -h)], "POSTE"); d.line([(0.16, 1.0), (0.17, -h)], "POSTE")
        d.rect(-De / 2, -h - 0.1, De, h + 0.1, "PLANTILLA")
        d.rect(-De / 2, -h - 0.1, De, 0.1, "HATCH")
        for j in range(10):
            C(msp, *d.P(-De / 2 + 0.08 + (j % 5) * (De - 0.16) / 4, -0.4 - 0.5 * (j // 5) - 0.2 * (j % 2)), 1.2, "HATCH")
        cota(msp, d.P(-De / 2, -h - 0.35), d.P(De / 2, -h - 0.35), -4, f"Ø {De*1000:.0f}")
        cota(msp, d.P(De / 2 + 0.15, 0), d.P(De / 2 + 0.15, -h), -4, f"{h*1000:.0f}")
        cota(msp, d.P(De / 2 + 0.15, -h), d.P(De / 2 + 0.15, -h - 0.1), -4, "100")
        T(msp, f"POSTE {pst}", *d.P(0, -h - 0.75), 2.2, "TEXTO", TA.TOP_CENTER)
        d.g(1, 0.1, 0.6, 12, 6); d.g(2, -0.3, -0.9, -14, 4); d.g(3, -0.2, -h - 0.05, -14, -6)
    T(msp, "1. Poste de C.A.C.   2. Concreto ciclópeo f'c = 100 kg/cm² + 30 % P.M.   3. Solado f'c = 100 kg/cm², e = 0,10 m", 14, 150, 1.8, "TEXTO")
    return 120


def cruceta_det(msp):
    d = Dib(msp, 105, 250, 70)
    d.rect(-1.2, 0, 2.4, 0.064, "CRUZETAS"); d.rect(-1.2, -0.12, 2.4, 0.064, "CRUZETAS")
    for x in (-1.0, -0.70, -0.05, 0.05, 0.70, 1.0):
        C(msp, *d.P(x, 0.032), 0.7, "CRUZETAS")
    cota(msp, d.P(-1.2, 0.064), d.P(1.2, 0.064), 8, "2 400")
    cota(msp, d.P(-1.2, 0.064), d.P(-1.0, 0.064), 4, "200"); cota(msp, d.P(-1.0, 0.064), d.P(-0.7, 0.064), 4, "300")
    cota(msp, d.P(-0.7, 0.064), d.P(-0.05, 0.064), 4, "650"); cota(msp, d.P(-0.05, 0.064), d.P(0.05, 0.064), 4, "100")
    T(msp, "CRUCETA DE PERFIL ANGULAR FºGº 64 × 64 × 6,4 × 2 400 mm – TIPO I (vista frontal y planta)", 105, 235, 2.0, "TEXTO", TA.TOP_CENTER)
    v = Dib(msp, 105, 205, 70)
    v.rect(-0.5, 0, 1.0, 0.064, "FeGo"); C(msp, *v.P(-0.45, 0.032), 0.7, "FeGo"); C(msp, *v.P(0.45, 0.032), 0.7, "FeGo")
    cota(msp, v.P(-0.5, 0.064), v.P(0.5, 0.064), 6, "1 000")
    T(msp, "RIOSTRA DE PERFIL ANGULAR FºGº 64 × 64 × 6,4 × 1 000 mm", 105, 195, 2.0, "TEXTO", TA.TOP_CENTER)
    s = Dib(msp, 60, 175, 220)
    s.line([(0, 0), (0.064, 0), (0.064, 0.0064), (0.0064, 0.0064), (0.0064, 0.064), (0, 0.064)], "FeGo", close=True)
    T(msp, "SECCIÓN L 64 × 64 × 6,4", 60, 168, 1.9, "TEXTO", TA.TOP_CENTER)
    T(msp, "Agujeros Ø 17,5 mm (pernos 16 mm) y Ø 20,5 mm (espigas);", 100, 185, 1.8, "TEXTO")
    T(msp, "acero ASTM A36, galvanizado en caliente ASTM A123", 100, 181, 1.8, "TEXTO")
    T(msp, "(espesor mínimo de zinc 86 µm).", 100, 177, 1.8, "TEXTO")
    return 120


def senal(msp):
    d = Dib(msp, 105, 250, 60)
    d.rect(-0.6, -0.4, 1.2, 0.4, "NUMERACION")
    T(msp, "E-001", *d.P(0, -0.2), 9, "NUMERACION", TA.MIDDLE_CENTER)
    T(msp, "PLACA DE NUMERACIÓN (pintura esmalte negro sobre fondo amarillo, a 3,0 m del suelo)", 105, 220, 1.9, "TEXTO", TA.TOP_CENTER)
    t = Dib(msp, 105, 205, 60)
    t.line([(-0.35, -0.6), (0.35, -0.6), (0, 0.0)], "NUMERACION", close=True)
    T(msp, "!", *t.P(0, -0.35), 9, "NUMERACION", TA.MIDDLE_CENTER)
    T(msp, "PELIGRO RIESGO ELÉCTRICO (NTP 399.010-1 / R.M. 111-2013-MEM/DM)", 105, 160, 1.9, "TEXTO", TA.TOP_CENTER)
    return 120


A = [("LD-LP-01", "PS1-3", "12/300", lambda m: ps13(m)), ("LD-LP-02", "PA1-3", "12/400", ps13_doble),
     ("LD-LP-03", "PA2-3", "12/400", lambda m: tension(m, "PA2-3")), ("LD-LP-04", "PR3-3", "12/400", lambda m: tension(m, "PR3-3")),
     ("LD-LP-05", "DT-3", "12/400", lambda m: tension(m, "DT-3")), ("LD-LP-06", "PSER-3", "12/400", lambda m: tension(m, "PSER-3")),
     ("LD-LP-07", "PTH-3", "12/400", lambda m: tension(m, "PTH-3")), ("LD-LP-14", "TS-3", "12/400", lambda m: tension(m, "TS-3"))]
TIT = {"PS1-3": "SOPORTE DE SUSPENSIÓN 0°–5°, TRIFÁSICO SIN NEUTRO", "PA1-3": "SOPORTE DE ÁNGULO 5°–30°, TRIFÁSICO SIN NEUTRO",
       "PA2-3": "SOPORTE DE ÁNGULO 30°–60°, TRIFÁSICO SIN NEUTRO", "TS-3": "SOPORTE DE RETENCIÓN/SUSPENSIÓN, TRIFÁSICO SIN NEUTRO", "PR3-3": "SOPORTE DE RETENCIÓN O ANCLAJE, TRIFÁSICO SIN NEUTRO",
       "DT-3": "SOPORTE DE DERIVACIÓN TENSADA CON SECCIONAMIENTO", "PSER-3": "ARMADO CON RECONECTADOR (ARRANQUE)",
       "PTH-3": "SOPORTE TERMINAL HORIZONTAL, TRIFÁSICO SIN NEUTRO"}
for cod, arm, pst, fn in A:
    lamina(cod, TIT[arm], f"TIPO {arm}", fn, items_armado(arm, pst), "1:25" if arm in ("PS1-3", "PA1-3") else "1:30",
           notas=["Cotas en mm. Ferretería de acero galvanizado en caliente (ASTM A153/A123).",
                  "Fase superior a 0,30 m sobre la cabeza; cruceta a 1,40 m bajo la cabeza (conductores inferiores a 1,10 m).",
                  "La numeración de los globos corresponde al orden de la lista de materiales."])
ret_items = [(MATD[c][1], MATD[c][2], q) for c, q in RET_RI.items()] + [("Cable de acero 10 mm Ø, 7 hilos, grado Siemens-Martin (poste 12 m / 13 m)", "m", "14,0 / 15,1")]
lamina("LD-LP-08", "RETENIDA INCLINADA", "TIPO RI", ret_RI, ret_items, "1:80",
       notas=["Tiro máximo de trabajo por retenida 15,15 kN; FS cable ≥ 2,0; FS bloque ≥ 2,0 (Anexo 7).",
              "La retenida se instalará en la bisectriz del ángulo o en la prolongación del alineamiento (anclajes y terminales)."])
for n in (1, 2):
    it = [(MATD[c][1], MATD[c][2], q) for c, q in PAT_KIT[f"PAT-{n}"].items()]
    lamina(f"LD-LP-{8+n:02d}", "PUESTA A TIERRA", f"TIPO PAT-{n}", lambda m, n=n: pat(m, n), it, "1:40",
           notas=["Resistencia máxima en estructuras con equipos: 25 Ω (medir; Anexo 3).",
                  "Relleno con tierra de cultivo cernida + cemento conductivo (1 dosis por varilla)."])
lamina("LD-LP-11", "CIMENTACIÓN DE POSTES", "TIPO CM (CONCRETO CICLÓPEO)", cimentacion, None, "1:35",
       notas=["Dimensiones según Anexo 5 (método de Sulzberger). Capacidad lateral asumida 2,1 daN/cm² – confirmar con EMS.",
              "Volúmenes por poste: 12 m: excav. 0,955 m³, ciclópeo 0,75 m³; 13 m: excav. 1,272 m³, ciclópeo 1,02 m³."])
lamina("LD-LP-12", "PERFILES PARA CRUCETA Y RIOSTRA", "TIPO I", cruceta_det, None, "Indicada",
       notas=["Carga de rotura mínima de la cruceta con riostras: transversal 12 kN, longitudinal 6 kN, vertical 3 kN por fase."])
lamina("LD-LP-13", "SEÑALIZACIÓN Y NUMERACIÓN DE ESTRUCTURAS", "", senal, [(MATD["10.01"][1], "u", 1)], "S/E",
       notas=["La codificación final será coordinada con la empresa concesionaria."])
import json
json.dump(LISTA, open(OUT / "laminas.json", "w"), ensure_ascii=False, indent=1)
print(len(LISTA), "láminas")
