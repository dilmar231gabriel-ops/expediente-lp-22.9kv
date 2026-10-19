"""Planos generales en el formato del modelo: LP-01 ubicación, LP-02 planta–poligonal, PP-xx perfil y planimetría (estilo DLTCAD,
H 1:2000 / V 1:500), LP-03 diagrama unifilar, LP-04 cruce con vía y distancias de seguridad.
Uso: python p08_planos.py WORK OUTDIR"""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
from shapely.geometry import LineString, Point, shape
from shapely.ops import transform
from pyproj import Transformer
sys.path.insert(0, str(Path(__file__).parent))
from params import *
from planos_common import *

W = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
E = pd.read_csv(W / "planilla_estructuras.csv"); RS = json.load(open(W / "resultados.json"))
meta = json.load(open(W / "trazado_meta.json")); prof = pd.read_csv(W / "perfil_troncal.csv")
par = pd.read_csv(W / "parametros_vano.csv"); cr = pd.read_csv(W / "cruces.csv")
troncal = LineString(meta["vertices"])
to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG}", always_xy=True).transform
road = LineString(meta["road"])
cat = json.loads(Path(DATOS["osm"]).read_text(encoding="utf-8"))["features"] if DATOS.get("osm") and Path(DATOS["osm"]).exists() else []
DERP = RS["plantillado"].get("derivaciones", [])
LISTA = []
PX, PZ = prof.progresiva_m.to_numpy(), prof.cota_m.to_numpy()
zt = lambda s: float(np.interp(s, PX, PZ))
p6 = lambda d: float(np.interp(d, par.vano_m, par.p_H6_m))
def h_low(poste): Lp = POSTES[poste]["L"]; return Lp - (Lp / 10 + 0.6) - ARM["d_inf"]
def h_top(poste): Lp = POSTES[poste]["L"]; return Lp - (Lp / 10 + 0.6)
cr_prog = cr[cr.tramo == "TRONCAL"].progresiva_m.to_numpy()
LOC = ([(f"{INICIO['nombre'].upper()} (punto de diseño – E-001)", (INICIO["lon"], INICIO["lat"]))] +
       [(f"{d['nombre'].upper()} (derivación – {d['estructura']})", next((x["lon"], x["lat"]) for x in DERIVS if x["id"] == d["id"])) for d in DERP] +
       [(f"{FIN['nombre'].upper()} (llegada – {E.estructura.iloc[-1]})", (FIN["lon"], FIN["lat"]))])

def reg(codigo, titulo, nombre, formato):
    LISTA.append((codigo, titulo, nombre, formato))

# ============================================================================ LP-01 UBICACIÓN (A3)
doc = nuevo(); msp = doc.modelspace(); Wp, Hp = 420, 297
membrete_grande(msp, Wp, Hp, "LP-01", "PLANO DE UBICACIÓN", "1:75 000")
minx, miny, maxx, maxy = troncal.bounds
sc = 1 / 75.0
ox, oy = 30 - (minx - 1500) * sc, 75 - (miny - 1500) * sc
tr = lambda x, y: (ox + x * sc, oy + y * sc)
for gx in range(int(minx // 2000) * 2000, int(maxx) + 4001, 2000):
    X = tr(gx, 0)[0]
    if 12 < X < 408: L(msp, [(X, 62), (X, 285)], "Grilla"); T(msp, f"{gx:,}".replace(",", " "), X + 0.6, 63, 1.6, "Grilla", rot=90)
for gy in range(int(miny // 2000) * 2000, int(maxy) + 4001, 2000):
    Y = tr(0, gy)[1]
    if 62 < Y < 285: L(msp, [(12, Y), (408, Y)], "Grilla"); T(msp, f"{gy:,}".replace(",", " "), 13, Y + 0.6, 1.6, "Grilla")
for f in cat:
    g = transform(to_utm, shape(f["geometry"])); p = f["properties"]
    if g.geom_type == "LineString" and p.get("highway"):
        L(msp, [tr(*c) for c in g.coords], "Via")
    elif g.geom_type == "LineString" and p.get("waterway"):
        L(msp, [tr(*c) for c in g.coords], "LAuxiliares", color=5)
L(msp, [tr(*p) for p in troncal.coords], "Eje_LP", lw=70)
for nm, (lon, lat) in LOC:
    X, Y = tr(*to_utm(lon, lat)); C(msp, X, Y, 1.8, "Txt_Planos", 1); T(msp, nm, X + 2.5, Y + 2.5, 2.4, "Txt_Planos")
for f in cat:
    if f["geometry"]["type"] == "Point" and f["properties"].get("name"):
        X, Y = tr(*to_utm(*f["geometry"]["coordinates"]))
        if 15 < X < 405 and 65 < Y < 280: C(msp, X, Y, 0.8, "Txt_Planos"); T(msp, f["properties"]["name"], X + 1.5, Y - 3, 1.9, "Txt_Planos")
L(msp, [(392, 255), (397, 272), (402, 255), (397, 259)], "Txt_Planos", True); T(msp, "N", 395.4, 274, 4, "Txt_Planos")
L(msp, [(30, 68), (30 + 5000 * sc, 68)], "Txt_Planos", lw=50); T(msp, "0", 29, 70, 2, "Txt_Planos"); T(msp, "5 km", 30 + 5000 * sc - 5, 70, 2, "Txt_Planos")
R(msp, 14, 200, 112, 82, "CUADROS")
T(msp, "UBICACIÓN POLÍTICA", 16, 276, 2.6, "Txt_Planos")
for k, t in enumerate(["País: Perú", f"Departamento: {PROYECTO['departamento']}", f"Provincias: {PROYECTO['provincias']}", f"Distritos: {PROYECTO['distritos']}",
                       "Región natural: Altiplano (circunlacustre)", f"Altitud: {RS['electrico']['cota_min']:.0f} – {RS['electrico']['cota_max']:.0f} m s.n.m.",
                       f"Sistema de coordenadas: UTM WGS 84, zona {ZONA_UTM}", f"Longitud de la línea: {troncal.length/1000:,.3f} km".replace(".", ","),
                       f"Estructuras: {len(E)}   Conductor: AAAC 70 mm²", "Tensión: 22,9 kV trifásico (3ø), 60 Hz"]):
    T(msp, t, 17, 270 - 6.6 * k, 2.1, "Txt_Planos")
T(msp, "LEYENDA", 255, 112, 2.4, "Txt_Planos")
L(msp, [(255, 106), (270, 106)], "Eje_LP", lw=70); T(msp, "Línea primaria 22,9 kV proyectada", 272, 105, 2.0, "Txt_Planos")
L(msp, [(255, 100), (270, 100)], "Via"); T(msp, "Vías (OpenStreetMap)", 272, 99, 2.0, "Txt_Planos")
L(msp, [(255, 94), (270, 94)], "LAuxiliares", color=5); T(msp, "Cursos de agua (OpenStreetMap)", 272, 93, 2.0, "Txt_Planos")
nombre = "LP-01_PLANO_DE_UBICACION"; guardar(doc, OUT, nombre, Wp, Hp); reg("LP-01", "PLANO DE UBICACIÓN", nombre, "A3")

# ============================================================================ LP-02 PLANTA – POLIGONAL (A1)
doc = nuevo(); msp = doc.modelspace(); Wp, Hp = 841, 594
membrete_grande(msp, Wp, Hp, "LP-02", "PLANO DE PLANTA – POLIGONAL Y UBICACIÓN DE ESTRUCTURAS", "1:25 000")
sc = 1 / 25.0
ox, oy = 25 - (minx - 300) * sc, 200 - (miny - 300) * sc
tr = lambda x, y: (ox + x * sc, oy + y * sc)
for gx in range(int(minx // 1000) * 1000, int(maxx) + 1001, 1000):
    X = tr(gx, 0)[0]
    if 15 < X < 826: L(msp, [(X, 195), (X, 580)], "Grilla"); T(msp, f"E {gx:,}".replace(",", " "), X + 0.8, 196, 2.0, "Grilla", rot=90)
for gy in range(int(miny // 1000) * 1000, int(maxy) + 1001, 1000):
    Y = tr(0, gy)[1]
    if 195 < Y < 580: L(msp, [(15, Y), (826, Y)], "Grilla"); T(msp, f"N {gy:,}".replace(",", " "), 16, Y + 0.8, 2.0, "Grilla")
for f in cat:
    g = transform(to_utm, shape(f["geometry"])); p = f["properties"]
    if g.geom_type == "LineString":
        L(msp, [tr(*c) for c in g.coords], "Via" if p.get("highway") else "LAuxiliares", color=None if p.get("highway") else 5)
    elif g.geom_type == "Polygon":
        L(msp, [tr(*c) for c in g.exterior.coords], "LAuxiliares", True, color=3)
L(msp, [tr(*p) for p in troncal.coords], "Eje_LP", lw=50)
for r in E.itertuples():
    X, Y = tr(r.este, r.norte)
    if r.armado == "PS1-3":
        C(msp, X, Y, 0.9, "Soportes_pl")
    else:
        R(msp, X - 1.3, Y - 1.3, 2.6, 2.6, "Soportes_pl", color=1)
    lab = f"{r.N}" if r.armado == "PS1-3" else f"{r.N} {r.armado}"
    T(msp, lab, X + 1.4, Y + 1.0, 1.6 if r.armado == "PS1-3" else 2.0, "Txt_Planos", rot=55)
for i, (x, y) in enumerate(meta["vertices"]):
    X, Y = tr(x, y); T(msp, f"V{i:02d}", X - 3, Y - 4.5, 2.0, "Bloques1", color=1)
for nm, (lon, lat) in LOC:
    X, Y = tr(*to_utm(lon, lat)); T(msp, nm, X + 3, Y - 9, 3.0, "Txt_Planos")
# cuadro de vértices (poligonal)
x0, y0 = 20, 182
T(msp, f"CUADRO DE COORDENADAS DE LA POLIGONAL (UTM WGS 84 – {ZONA_UTM})", x0, y0, 2.8, "Txt_Planos")
hdr = ["VÉRTICE", "PROGRESIVA (m)", "ESTE (m)", "NORTE (m)", "ÁNGULO", "ESTRUCTURA"]
cw = [16, 26, 28, 30, 18, 20]
vprog = [troncal.project(Point(v)) for v in meta["vertices"]]
angs = [0] + meta["angulos"] + [0]
rows = []
for i, ((x, y), s, a) in enumerate(zip(meta["vertices"], vprog, angs)):
    est = E.iloc[(E.progresiva_m - s).abs().argmin()].estructura
    rows.append([f"V{i:02d}", f"{s:,.2f}", f"{x:,.2f}", f"{y:,.2f}", f"{a:.2f}°", est])
half = math.ceil(len(rows) / 2)
for blk in range(2):
    bx = x0 + blk * 150; by = y0 - 5
    xx = bx
    for wdt, h in zip(cw, hdr):
        R(msp, xx, by - 5, wdt, 5, "CUADROS"); T(msp, h, xx + wdt / 2, by - 3.6, 1.8, "Txt_Planos", TA.BOTTOM_CENTER); xx += wdt
    for k, row in enumerate(rows[blk * half:(blk + 1) * half]):
        xx = bx; yy = by - 5 - 4.4 * (k + 1)
        for wdt, v in zip(cw, row):
            R(msp, xx, yy, wdt, 4.4, "CUADROS"); T(msp, v.replace(",", " "), xx + wdt / 2, yy + 1.2, 1.7, "Txt_Planos", TA.BOTTOM_CENTER); xx += wdt
# leyenda y resumen
lx, ly = 330, 182
T(msp, "LEYENDA", lx, ly, 2.8, "Txt_Planos")
L(msp, [(lx, ly - 8), (lx + 18, ly - 8)], "Eje_LP", lw=50); T(msp, "Línea primaria 22,9 kV – 3ø – AAAC 70 mm²", lx + 21, ly - 9, 2.0, "Txt_Planos")
C(msp, lx + 9, ly - 15, 0.9, "Soportes_pl"); T(msp, "Estructura de suspensión PS1-3 (número)", lx + 21, ly - 16, 2.0, "Txt_Planos")
R(msp, lx + 7.7, ly - 23.3, 2.6, 2.6, "Soportes_pl", color=1); T(msp, "Estructura especial (ángulo, anclaje, equipos)", lx + 21, ly - 23, 2.0, "Txt_Planos")
L(msp, [(lx, ly - 29), (lx + 18, ly - 29)], "Via"); T(msp, "Vías y caminos (OpenStreetMap)", lx + 21, ly - 30, 2.0, "Txt_Planos")
L(msp, [(lx, ly - 36), (lx + 18, ly - 36)], "LAuxiliares", color=5); T(msp, "Cursos de agua / áreas (OpenStreetMap)", lx + 21, ly - 37, 2.0, "Txt_Planos")
T(msp, "RESUMEN DE ESTRUCTURAS", lx, ly - 50, 2.6, "Txt_Planos")
for k, (a, n) in enumerate(E.armado.value_counts().items()):
    T(msp, f"{a:7s}: {n:4d}", lx, ly - 57 - 4.5 * k, 2.1, "Txt_Planos")
for k, (a, n) in enumerate(E.poste.value_counts().items()):
    T(msp, f"Poste {a}: {n}", lx + 60, ly - 57 - 4.5 * k, 2.1, "Txt_Planos")
T(msp, f"Retenidas RI: {int(E.n_retenidas.sum())}   PAT-1: {(E.puesta_tierra=='PAT-1').sum()}   PAT-2: {(E.puesta_tierra=='PAT-2').sum()}", lx + 60, ly - 75, 2.1, "Txt_Planos")
L(msp, [(806, 540), (812, 560), (818, 540), (812, 545)], "Txt_Planos", True); T(msp, "N", 810, 562, 5, "Txt_Planos")
nombre = "LP-02_PLANTA_POLIGONAL"; guardar(doc, OUT, nombre, Wp, Hp); reg("LP-02", "PLANO DE PLANTA – POLIGONAL Y UBICACIÓN DE ESTRUCTURAS", nombre, "A1")

# ============================================================================ PP-xx PERFIL Y PLANIMETRÍA (A1, H 1:2000, V 1:500)
EH, EV = 0.5, 2.0          # mm por m
X0 = 92                    # inicio del dibujo
LONG = 1480.0              # m por hoja (aprox.)
cortes = [0]
while E.progresiva_m.iloc[cortes[-1]] + LONG < E.progresiva_m.iloc[-1]:
    tgt = E.progresiva_m.iloc[cortes[-1]] + LONG
    j = int(E.index[E.progresiva_m <= tgt].max())
    cortes.append(j)
cortes.append(len(E) - 1)
ROWS = ["NRO ESTRUCTURA", "TIPO ARMADO", "POSTE/SOPORTE", "VANO HORIZONTAL (m)", "VANO PESO (m)", "VANO VIENTO (m)", "ACUMULADA (m)",
        "P. CATENARIA H6 (m)", "EDS INICIAL (%TR)", "EDS FINAL (%TR)", "TIPO RETENIDAS", "TIPO PAT", "CONDUCTOR DE FASE"]
rhh = 4.6
def side_angle(i):
    """lado del giro en el vértice (Izq./Der.) a partir de la poligonal."""
    if i <= 0 or i >= len(E) - 1 or E.angulo_deg[i] == 0: return ""
    a, b, c = (E.este[i - 1], E.norte[i - 1]), (E.este[i], E.norte[i]), (E.este[i + 1], E.norte[i + 1])
    cz = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
    return ("Izq." if cz > 0 else "Der.") + f" {E.angulo_deg[i]:.1f}°"
def offset_signed(geom_pts, s0, s1):
    """proyecta una polilínea a coordenadas (progresiva, desplazamiento lateral) respecto al eje."""
    out = []
    for x, y in geom_pts:
        s = troncal.project(Point(x, y))
        if s0 - 20 <= s <= s1 + 20:
            p = troncal.interpolate(s); q = troncal.interpolate(min(s + 1, troncal.length))
            tx, ty = q.x - p.x, q.y - p.y; nrm = math.hypot(tx, ty) or 1
            d = ((x - p.x) * (-ty) + (y - p.y) * tx) / nrm
            out.append((s, d))
        else:
            out.append(None)
    return out
nh = len(cortes) - 1
for k in range(nh):
    i0, i1 = cortes[k], cortes[k + 1]
    s0, s1 = E.progresiva_m[i0], E.progresiva_m[i1]
    doc = nuevo(); msp = doc.modelspace(); Wp, Hp = 841, 594
    cod = f"PP-{k+1:02d}"
    membrete_grande(msp, Wp, Hp, cod, f"PERFIL Y PLANIMETRÍA – PROGRESIVA {s0/1000:.3f} A {s1/1000:.3f} km".replace(".", ","), "1:2 000", "1:500",
                    hoja=f"Hoja {k+1} de {nh}")
    X = lambda s: X0 + (s - s0) * EH
    seg = (PX >= s0 - 1) & (PX <= s1 + 1)
    zmin = math.floor((PZ[seg].min() - 4) / 10) * 10
    ztop = PZ[seg].max() + 14
    YB = max(205, 0.5 * (205 + 505) - 0.5 * (ztop - zmin) * EV)
    Y = lambda z: YB + (z - zmin) * EV
    # --- tabla superior
    ytab = 575
    for j, lab in enumerate(ROWS):
        yy = ytab - rhh * (j + 1)
        L(msp, [(20, yy), (X(s1) + 12, yy)], "LAuxiliares", lt="CONTINUOUS", color=8)
        T(msp, lab, 22, yy + 1.2, 2.0, "Txt_Planos")
    L(msp, [(20, ytab), (X(s1) + 12, ytab)], "LAuxiliares", lt="CONTINUOUS", color=8)
    R(msp, 20, ytab - rhh * len(ROWS), X(s1) + 12 - 20, rhh * len(ROWS), "CUADROS")
    L(msp, [(X0 - 10, ytab), (X0 - 10, ytab - rhh * len(ROWS))], "CUADROS")
    rowy = lambda j: ytab - rhh * (j + 1) + 1.2
    for i in range(i0, i1 + 1):
        r = E.iloc[i]; x = X(r.progresiva_m)
        L(msp, [(x, ytab), (x, ytab - rhh * len(ROWS))], "LAuxiliares", lt="CONTINUOUS", color=9)
        vals = {0: r.N, 1: r.armado, 2: f"CAC {r.poste}", 4: f"{r.vano_peso_m:.2f}", 5: f"{r.vano_viento_m:.2f}", 6: f"{r.progresiva_m:.2f}",
                10: (f"RI x{int(r.n_retenidas)}" if r.n_retenidas else "-"), 11: r.puesta_tierra}
        for j, v in vals.items():
            T(msp, str(v).replace(".", ","), x, rowy(j), 1.8, "Txt_Planos", TA.BOTTOM_CENTER)
        if i < i1:
            d = E.vano_adelante_m[i]; xm = X(r.progresiva_m + d / 2)
            for j, v in {3: f"{d:.2f}", 7: f"{p6(d):.2f}", 8: "18,00%", 9: "15,00%", 12: "AAAC-70"}.items():
                T(msp, v.replace(".", ","), xm, rowy(j), 1.8, "Txt_Planos", TA.BOTTOM_CENTER)
    # --- perfil
    pts = [(X(s), Y(z)) for s, z in zip(PX[seg], PZ[seg])]
    L(msp, pts, "Perfil")
    zmax = max(PZ[seg].max() + 16, zmin + 40)
    for z in range(int(zmin), int(zmax) + 1, 10):
        L(msp, [(X0 - 6, Y(z)), (X0 - 2, Y(z))], "Cotas"); T(msp, f"{z:.1f}".replace(".", ","), X0 - 7, Y(z), 2.0, "Cotas", TA.MIDDLE_RIGHT)
    L(msp, [(X0 - 2, Y(zmin)), (X0 - 2, Y(int(zmax)))], "Cotas")
    # distancia de seguridad (terreno + 6/7 m)
    sp = np.arange(s0, s1, 5.0)
    req = [DIST["cruce_via"] if (len(cr_prog) and np.min(np.abs(cr_prog - s)) <= 20) else DIST["general"] for s in sp]
    L(msp, [(X(s), Y(zt(s) + q)) for s, q in zip(sp, req)], "LAuxiliares", color=8)
    # postes, conductor y flechas
    for i in range(i0, i1 + 1):
        r = E.iloc[i]; x = X(r.progresiva_m); zg = zt(r.progresiva_m)
        L(msp, [(x, Y(zg)), (x, Y(zg + h_top(r.poste)))], "Soportes_per", lw=35)
        L(msp, [(x - 1.2, Y(zg + h_low(r.poste))), (x + 1.2, Y(zg + h_low(r.poste)))], "Soportes_per")
        T(msp, f"{r.estructura}", x, Y(zg + h_top(r.poste)) + 2, 1.8, "Txt_Planos", TA.BOTTOM_CENTER, rot=90)
        if i < i1:
            q = E.iloc[i + 1]; d = q.progresiva_m - r.progresiva_m; p = p6(d)
            ya, yb = zg + h_low(r.poste), zt(q.progresiva_m) + h_low(q.poste)
            xs = np.linspace(0, d, 25)
            zz = ya + (yb - ya) * xs / d - xs * (d - xs) / (2 * p)
            L(msp, [(X(r.progresiva_m + a), Y(b)) for a, b in zip(xs, zz)], "Conductor_Fase")
            f = d * d / (8 * p); xm = r.progresiva_m + d / 2
            T(msp, f"{f:.2f}".replace(".", ","), X(xm), Y((ya + yb) / 2) + 2.0, 1.8, "Conductor_Fase", TA.BOTTOM_CENTER)
    # --- bandas inferiores
    yb0 = 196
    bands = [("VANO (m)", 0), ("PROGRESIVA DEL TERRENO (m)", 1), ("COTA DEL TERRENO (m s.n.m.)", 2)]
    for lab, j in bands:
        yy = yb0 - 9 * (j + 1)
        R(msp, 20, yy, X(s1) + 12 - 20, 9, "CUADROS"); T(msp, lab, 22, yy + 3.2, 2.0, "Txt_Planos")
    for i in range(i0, i1):
        r = E.iloc[i]; d = E.vano_adelante_m[i]; xm = X(r.progresiva_m + d / 2)
        T(msp, f"{d:.2f}".replace(".", ","), xm, yb0 - 9 + 3.0, 2.0, "Txt_conductores", TA.BOTTOM_CENTER)
    for s in np.arange(math.ceil(s0 / 50) * 50, s1, 50):
        T(msp, f"{s:.0f}", X(s), yb0 - 18 + 1.0, 1.6, "Txt_Planos", TA.BOTTOM_CENTER, rot=90)
        T(msp, f"{zt(s):.1f}".replace(".", ","), X(s), yb0 - 27 + 1.0, 1.6, "Txt_Planos", TA.BOTTOM_CENTER, rot=90)
    # --- planimetría (eje rectificado con desplazamientos laterales)
    yp = 120
    T(msp, "PLANIMETRÍA", 22, yp + 30, 2.4, "Txt_Planos")
    L(msp, [(X(s0), yp), (X(s1), yp)], "Eje_LP", lw=35)
    lines_pl = [(road, True)] + [(transform(to_utm, shape(f["geometry"])), bool(f["properties"].get("highway"))) for f in cat if f["geometry"]["type"] == "LineString"]
    for g, esvia in lines_pl:
        if g.distance(troncal) > 120: continue
        dens = [g.interpolate(t).coords[0] for t in np.arange(0, g.length, 8.0)] + [g.coords[-1]]
        o = offset_signed(dens, s0, s1)
        f = {"properties": {"highway": esvia}}
        segp = []
        for v in o:
            if v and abs(v[1]) < 70 and s0 <= v[0] <= s1:
                segp.append((X(v[0]), yp + v[1] * EH))
            else:
                if len(segp) > 1: L(msp, segp, "Via" if f["properties"].get("highway") else "LAuxiliares")
                segp = []
        if len(segp) > 1: L(msp, segp, "Via" if f["properties"].get("highway") else "LAuxiliares")
    for i in range(i0, i1 + 1):
        r = E.iloc[i]; x = X(r.progresiva_m)
        C(msp, x, yp, 1.0, "Soportes_pl")
        if r.n_retenidas:
            L(msp, [(x, yp), (x, yp - 6)], "Bloque_ret"); L(msp, [(x - 1, yp - 6), (x + 1, yp - 6)], "Bloque_ret")
        sa = side_angle(i)
        if sa: T(msp, sa, x + 1.5, yp + 6, 1.8, "Bloques1", rot=30)
    for km in range(int(math.ceil(s0 / 1000)), int(s1 // 1000) + 1):
        x = X(km * 1000); L(msp, [(x, yp - 4), (x, yp + 4)], "Bloques1"); T(msp, f"Km {km},0", x, yp - 9, 2.6, "Bloques1", TA.BOTTOM_CENTER)
    for c in cr[cr.tramo == "TRONCAL"].itertuples():
        if s0 <= c.progresiva_m <= s1:
            T(msp, f"{c.cruce_id} – cruce {c.nombre}", X(c.progresiva_m) + 1.5, yp - 16, 1.8, "Bloques1")
    # leyenda
    T(msp, "Conductor: AAAC 70 mm², flecha a máxima temperatura (50 °C con CREEP). Línea discontinua: distancia mínima al terreno (6,0 m; 7,0 m en cruces).",
      22, 66, 1.8, "Txt_Planos")
    T(msp, "Cotas de terreno: DEM Copernicus GLO-30 interpolado (margen 0,30 m). Deben verificarse con el levantamiento topográfico de replanteo.",
      22, 62, 1.8, "Txt_Planos")
    nombre = f"{cod}_PERFIL_Y_PLANIMETRIA"
    guardar(doc, OUT, nombre, Wp, Hp)
    reg(cod, f"PERFIL Y PLANIMETRÍA – E-{i0+1:03d} a E-{i1+1:03d} (km {s0/1000:.3f} – {s1/1000:.3f})".replace(".", ","), nombre, "A1")

# ============================================================================ LP-03 DIAGRAMA UNIFILAR (A3)
doc = nuevo(); msp = doc.modelspace(); Wp, Hp = 420, 297
membrete_grande(msp, Wp, Hp, "LP-03", "DIAGRAMA UNIFILAR DE LA LÍNEA PRIMARIA 22,9 kV", "S/E")
y = 190
L(msp, [(30, y), (390, y)], "DIBUJO", lw=70)
T(msp, f"RED EXISTENTE 22,9 kV – {PROYECTO['concesionaria'].upper()}", 20, y + 22, 2.4, "TEXTO")
T(msp, "(alimentador y SET de origen por confirmar en la factibilidad)", 20, y + 17, 1.9, "TEXTO")
L(msp, [(30, y + 14), (30, y)], "DIBUJO", lw=50)
def disp(x, txt):
    R(msp, x - 6, y - 4, 12, 8, "EQUIPOS"); T(msp, txt, x, y + 6, 1.9, "TEXTO", TA.BOTTOM_CENTER)
def cutout(x, yy=None):
    yy = y if yy is None else yy
    L(msp, [(x - 3, yy), (x + 3, yy + 3)], "EQUIPOS"); C(msp, x - 3, yy, 0.7, "EQUIPOS"); C(msp, x + 3, yy, 0.7, "EQUIPOS")
def ppr(x):
    L(msp, [(x, y), (x, y - 10)], "EQUIPOS"); R(msp, x - 2, y - 18, 4, 8, "EQUIPOS"); L(msp, [(x, y - 18), (x, y - 22)], "EQUIPOS")
    for k in range(3): L(msp, [(x - 3 + k, y - 22 - k), (x + 3 - k, y - 22 - k)], "EQUIPOS")
cutout(45); T(msp, "3 cut-out 38 kV", 45, y + 6, 1.9, "TEXTO", TA.BOTTOM_CENTER); ppr(52)
disp(70, "RECONECTADOR 38 kV, 170 kV-BIL"); T(msp, "E-001 (PSER-3)", 70, y - 10, 2.0, "TEXTO", TA.TOP_CENTER)
T(msp, f"Punto de diseño: {INICIO['nombre']}", 70, y - 15, 1.8, "TEXTO", TA.TOP_CENTER)
Ltot = RS["plantillado"]["L_troncal_m"]
xpos = lambda s_: 80 + s_ / Ltot * 270
prev_x, prev_s = 70, 0.0
for d in DERP:
    xc = xpos(d["prog"])
    T(msp, f"3ø AAAC 70 mm² – {(d['prog']-prev_s)/1000:.3f} km".replace(".", ","), (prev_x + xc) / 2, y + 2, 1.8, "TEXTO", TA.BOTTOM_CENTER)
    L(msp, [(xc, y), (xc, y - 45)], "DIBUJO", lw=50); cutout(xc, y - 20)
    T(msp, "PSEC-3P", xc + 5, y - 20, 1.7, "TEXTO")
    T(msp, f"{d['estructura']} (DT-3) – {d['nombre'].upper()}", xc, y + 6, 1.8, "TEXTO", TA.BOTTOM_CENTER)
    T(msp, "Red primaria (fuera del alcance)", xc + 2, y - 50, 1.7, "TEXTO")
    prev_x, prev_s = xc, d["prog"]
T(msp, f"3ø AAAC 70 mm² – {(Ltot-prev_s)/1000:.3f} km".replace(".", ","), (prev_x + 360) / 2, y + 2, 1.8, "TEXTO", TA.BOTTOM_CENTER)
cutout(362); ppr(368); T(msp, f"{E.estructura.iloc[-1]} (PTH-3) – 3 cut-out + 3 pararrayos", 362, y + 6, 2.0, "TEXTO", TA.BOTTOM_CENTER)
T(msp, f"Llegada a {FIN['nombre'].upper()} (punto de interconexión por confirmar)", 290, y - 30, 1.9, "TEXTO")
dem = RS["demanda"]
_cargas = "; ".join(f"{NOMBRE_PUNTO[k]} {v:.0f} kW" for k, v in dem["P20"].items())
for k, t in enumerate(["DATOS DEL SISTEMA", "Tensión nominal 22,9 kV; tensión máxima 25 kV; 60 Hz; 3ø, neutro efectivamente puesto a tierra en la fuente",
                       f"Máxima demanda año {PROYECTO['horizonte']}: {dem['MD_anio20_kW']:.0f} kW ({_cargas})".replace(".", ","),
                       f"Caída de tensión máxima: {RS['electrico']['dV_fin_pct']:.2f} % (año {PROYECTO['horizonte']})".replace(".", ","),
                       f"Potencia de cortocircuito de diseño: {SIS['Scc_MVA']:.0f} MVA (por confirmar con {PROYECTO['concesionaria']})",
                       f"Nivel de aislamiento de equipos: 170 kV-BIL (altitud de diseño {math.ceil(RS['electrico']['cota_max']/100)*100:,} m s.n.m.)".replace(",", " ")]):
    T(msp, t, 25, 120 - 7 * k, 2.4 if k == 0 else 2.0, "TEXTO")
nombre = "LP-03_DIAGRAMA_UNIFILAR"; guardar(doc, OUT, nombre, Wp, Hp); reg("LP-03", "DIAGRAMA UNIFILAR DE LA LÍNEA PRIMARIA 22,9 kV", nombre, "A3")

# ============================================================================ LP-04 CRUCE DE VÍA Y DISTANCIAS DE SEGURIDAD (A3)
doc = nuevo(); msp = doc.modelspace(); Wp, Hp = 420, 297
membrete_grande(msp, Wp, Hp, "LP-04", "DETALLE DE CRUCE DE VÍA Y DISTANCIAS MÍNIMAS DE SEGURIDAD", "1:200")
s = 5.0          # mm por m (1:200)
bx, by = 40, 80
L(msp, [(bx, by), (bx + 330, by)], "Perfil")
R(msp, bx + 120, by - 1.5, 7.2 * s, 1.5, "Via")
T(msp, f"CALZADA ({TRAZADO.get('nombre_via', 'vía')})", bx + 120 + 3.6 * s, by - 6, 2.0, "TEXTO", TA.TOP_CENTER)
for xp in (bx + 40, bx + 290):
    L(msp, [(xp, by), (xp, by + 10.2 * s)], "Soportes_per", lw=50)
    T(msp, "Poste CAC 12/400 – armado PR3-3 / PA2-3", xp, by + 10.2 * s + 3, 1.9, "TEXTO", TA.BOTTOM_CENTER)
xs = np.linspace(0, 250, 40); ya = yb = 9.1
zz = ya - xs * (250 - xs) / (2 * 1100)
L(msp, [(bx + 40 + a * s * 250 / 250 * 1.0, by + z * s) for a, z in zip(xs, zz)], "Conductor_Fase")
xm = bx + 120 + 3.6 * s; zm = 9.1 - 125 * 125 / (2 * 1100)
L(msp, [(xm, by), (xm, by + zm * s)], "cotas"); T(msp, f"≥ 7,0 m (RD 018 3.7: cruce de vías)", xm + 2, by + zm * s / 2, 2.2, "cotas")
L(msp, [(bx + 10, by + 6 * s), (bx + 110, by + 6 * s)], "LAuxiliares"); T(msp, "6,0 m: terreno con circulación de vehículos y maquinaria agrícola", bx + 10, by + 6 * s + 1.5, 1.9, "cotas")
T(msp, "Vano de cruce sin empalmes; estructuras de anclaje a ambos lados; flecha verificada a 50 °C (H6).", 40, 70, 2.0, "TEXTO")
_crt = cr[cr.tipo == "VIA"] if len(cr) else cr
T(msp, ("Cruces de vía identificados en el perfil: " + ", ".join(f"{c.cruce_id} km {c.progresiva_m/1000:.3f}" for c in _crt.itertuples())[:180]) if len(_crt) else "No se identificaron cruces de vía en el trazado (verificar en campo).", 40, 65, 2.0, "TEXTO")
tx, ty = 230, 280
T(msp, "DISTANCIAS MÍNIMAS DE SEGURIDAD (RD 018-2003-EM/DGE y CNE-S 2011)", tx - 190, ty - 8, 2.4, "TEXTO")
filas = [("Al terreno en zonas de circulación de maquinaria agrícola y caminos", "6,0 m"), ("En cruce de carreteras y calles", "7,0 m"),
         ("Lugares accesibles solo a peatones", "5,0 m"), ("Entre conductores en el apoyo: horizontal / vertical", "0,70 / 1,00 m"),
         ("Horizontal entre fases a medio vano: 0,0076·U·Fc + 0,65·√f", f"≤ {RS['plantillado']['Dh_max']:.2f} m (disp.: 2,00 m)".replace(".", ",")),
         ("Radial a edificaciones (paredes, ventanas, balcones)", "2,50 m"), ("A árboles: vertical / radial", "2,50 / 0,50 m")]
for k, (a, b) in enumerate(filas):
    R(msp, tx - 190, ty - 16 - 6 * k, 140, 6, "CUADROS"); R(msp, tx - 50, ty - 16 - 6 * k, 40, 6, "CUADROS")
    T(msp, a, tx - 188, ty - 14 - 6 * k, 1.9, "TEXTO"); T(msp, b, tx - 30, ty - 14 - 6 * k, 1.9, "TEXTO", TA.BOTTOM_CENTER)
nombre = "LP-04_CRUCE_Y_DISTANCIAS_DE_SEGURIDAD"; guardar(doc, OUT, nombre, Wp, Hp); reg("LP-04", "DETALLE DE CRUCE DE VÍA Y DISTANCIAS MÍNIMAS DE SEGURIDAD", nombre, "A3")
json.dump(LISTA, open(OUT / "planos.json", "w"), ensure_ascii=False, indent=1)
print(len(LISTA), "planos")
