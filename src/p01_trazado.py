"""PASO 1 – Trazado (eje de la línea).
Entrada: ruta (GeoJSON o KML con una LineString) indicada en proyecto.yaml → trazado.archivo_ruta.
 - Si la ruta es una vía (ruta_es_via: true) se desplaza 'desplazamiento_m' al lado indicado para quedar fuera de la franja
   de la carretera (RD 018-2003-EM/DGE 3.7: ≥ 25 m de carreteras importantes).
 - Se simplifica (Douglas-Peucker), se eliminan quiebres en "U" y se fusionan vértices casi colineales.
 - El primer y último vértice se fijan en los puntos de inicio y fin; cada derivación se conecta al punto más cercano.
Salida: WORK/trazado_meta.json y WORK/trazado_rectificado.geojson
Uso: python p01_trazado.py WORK"""
import json, math, sys, re
from pathlib import Path
from shapely.geometry import shape, LineString, Point, mapping
from shapely.ops import transform, nearest_points, linemerge
from pyproj import Transformer
sys.path.insert(0, str(Path(__file__).parent))
from params import *

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG}", always_xy=True).transform
to_ll = Transformer.from_crs(f"EPSG:{EPSG}", "EPSG:4326", always_xy=True).transform


def leer_ruta(path):
    """Lee la primera LineString (o la unión de varias) de un GeoJSON o KML."""
    path = Path(path); txt = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".kml":
        lines = []
        for blk in re.findall(r"<LineString>.*?<coordinates>(.*?)</coordinates>", txt, re.S):
            pts = [tuple(map(float, c.split(",")[:2])) for c in blk.split() if c.strip()]
            if len(pts) > 1: lines.append(LineString(pts))
    else:
        gj = json.loads(txt); feats = gj["features"] if "features" in gj else [gj]
        lines = []
        for f in feats:
            g = shape(f["geometry"] if "geometry" in f else f)
            if g.geom_type == "LineString": lines.append(g)
            elif g.geom_type == "MultiLineString": lines += list(g.geoms)
    if not lines: sys.exit(f"ERROR: {path} no contiene ninguna LineString")
    g = linemerge(lines) if len(lines) > 1 else lines[0]
    if g.geom_type != "LineString": g = max(g.geoms, key=lambda x: x.length)
    return transform(to_utm, g)


def angles(c):
    o = []
    for i in range(1, len(c) - 1):
        a1 = math.atan2(c[i][1] - c[i - 1][1], c[i][0] - c[i - 1][0]); a2 = math.atan2(c[i + 1][1] - c[i][1], c[i + 1][0] - c[i][0])
        o.append(abs(math.degrees((a2 - a1 + math.pi) % (2 * math.pi) - math.pi)))
    return o


T = TRAZADO
road = leer_ruta(ruta(T["archivo_ruta"]))
P0 = Point(to_utm(INICIO["lon"], INICIO["lat"])); PF = Point(to_utm(FIN["lon"], FIN["lat"]))
if Point(road.coords[0]).distance(P0) > Point(road.coords[-1]).distance(P0):
    road = LineString(road.coords[::-1])                 # orientar la ruta inicio → fin
OFF = float(T.get("desplazamiento_m", 0)); TOL = float(T.get("tolerancia_simplificacion_m", 15))
SIDE = -1 if str(T.get("lado", "derecha")).lower().startswith("d") else 1
o = road.offset_curve(SIDE * OFF, join_style=1) if OFF > 0 else road
if o.geom_type != "LineString":
    o = max(o.geoms, key=lambda g: g.length)
c = list(o.simplify(TOL).coords)
if Point(c[0]).distance(P0) > Point(c[-1]).distance(P0):
    c = c[::-1]
c = [P0.coords[0]] + c[1:-1] + [PF.coords[0]]
AMAX = float(T.get("angulo_max_quiebre_deg", 60)); AFUS = float(T.get("angulo_fusion_deg", 2)); DMIN = float(T.get("dist_min_via_m", 25))
while True:                                             # quiebres en U
    a = angles(c)
    if not a or max(a) <= AMAX: break
    c.pop(a.index(max(a)) + 1)
changed = True
while changed:                                          # fusión de vértices casi colineales
    changed = False
    a = angles(c)
    for i in sorted(range(len(a)), key=lambda k: a[k]):
        if a[i] >= AFUS: break
        cand = c[:i + 1] + c[i + 2:]
        seg = LineString(cand[max(0, i - 1):i + 3])
        lejos = (not T.get("ruta_es_via", False)) or min(road.distance(seg.interpolate(s)) for s in range(0, max(1, int(seg.length)), 10)) >= DMIN
        if lejos or i < 2 or i > len(c) - 4:
            c = cand; changed = True; break
troncal = LineString(c)
derivs = []
for d in DERIVS:
    PI = Point(to_utm(d["lon"], d["lat"]))
    np_ = nearest_points(troncal, PI)[0]
    derivs.append({"id": d["id"], "nombre": d["nombre"], "prog": troncal.project(np_), "coords": [np_.coords[0], PI.coords[0]],
                   "longitud_m": np_.distance(PI)})
derivs.sort(key=lambda x: x["prog"])
a = angles(c)
print(f"troncal {troncal.length:.1f} m, {len(c)} vértices, ángulo máx {max(a) if a else 0:.1f}°")
for d in derivs: print(f"derivación {d['nombre']}: {d['longitud_m']:.1f} m desde la progresiva {d['prog']:.1f} m")


def feat(line, props):
    return {"type": "Feature", "geometry": mapping(transform(to_ll, line)), "properties": props}
fc = {"type": "FeatureCollection", "features": [feat(troncal, {"nombre": f"Troncal {PROYECTO['nombre_corto']}", "tipo": "TRONCAL", "longitud_m": round(troncal.length, 2)})] +
      [feat(LineString(d["coords"]), {"nombre": f"Derivación {d['nombre']}", "tipo": "DERIVACION", "longitud_m": round(d["longitud_m"], 2)}) for d in derivs]}
(OUT / "trazado_rectificado.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
json.dump({"metodo": f"desplazamiento {OFF} m, Douglas-Peucker {TOL} m, sin quiebres > {AMAX}°", "troncal_m": troncal.length,
           "road_m": road.length, "vertices": c, "angulos": a, "derivaciones": derivs,
           "ruta_es_via": bool(T.get("ruta_es_via", False)), "road": list(road.coords)}, open(OUT / "trazado_meta.json", "w"))
