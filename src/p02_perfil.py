"""PASO 2 – Perfil del terreno sobre el eje (DEM cada 10 m, interpolación bilineal, filtro de mediana) y cruces con vías y
cursos de agua (OpenStreetMap). Uso: python p02_perfil.py WORK"""
import json, sys, math
from pathlib import Path
import numpy as np, pandas as pd, rasterio
from scipy.signal import medfilt
from shapely.geometry import shape, LineString, Point
from shapely.ops import transform
from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).parent))
from params import *
W = Path(sys.argv[1])
to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG}", always_xy=True).transform
to_ll = Transformer.from_crs(f"EPSG:{EPSG}", "EPSG:4326", always_xy=True).transform
meta = json.load(open(W / "trazado_meta.json"))
if not DATOS.get("dem") or not Path(DATOS["dem"]).exists():
    sys.exit("ERROR: falta el modelo digital de elevación (datos → dem en proyecto.yaml). Use herramientas/preparar_datos.py")
dem = rasterio.open(DATOS["dem"])
road = LineString(meta["road"]) if meta.get("ruta_es_via") else None
cat = json.loads(Path(DATOS["osm"]).read_text(encoding="utf-8")) if DATOS.get("osm") and Path(DATOS["osm"]).exists() else {"features": []}
hw = []
for f in cat["features"]:
    p = f["properties"]
    if p.get("highway") and f["geometry"]["type"] == "LineString":
        hw.append((p.get("highway"), p.get("name") or "s/n", transform(to_utm, shape(f["geometry"]))))
wat = [(f["properties"].get("waterway"), f["properties"].get("name") or "s/n", transform(to_utm, shape(f["geometry"])))
       for f in cat["features"] if f["properties"].get("waterway")]
blds = [transform(to_utm, shape(f["geometry"])) for f in cat["features"] if f["properties"].get("building")]

ARR = dem.read(1).astype(float); INV = ~dem.transform
def bilinear(ll):
    """Interpolación bilineal del DEM (evita el escalonado del muestreo por vecino más cercano)."""
    out = []
    for lon, lat in ll:
        c, r = INV * (lon, lat); c -= 0.5; r -= 0.5
        c0, r0 = int(np.floor(c)), int(np.floor(r)); fc, fr = c - c0, r - r0
        q = ARR[r0:r0 + 2, c0:c0 + 2]
        out.append(q[0, 0] * (1 - fc) * (1 - fr) + q[0, 1] * fc * (1 - fr) + q[1, 0] * (1 - fc) * fr + q[1, 1] * fc * fr)
    return np.array(out)

def perfil(line, step=10.0):
    n = int(line.length // step)
    prog = np.append(np.arange(0, n + 1) * step, line.length)
    pts = [line.interpolate(s) for s in prog]
    ll = [to_ll(p.x, p.y) for p in pts]
    z = bilinear(ll)
    zf = medfilt(z, 9)                       # mediana de 90 m: elimina picos de edificaciones/cortes
    art = np.abs(z - zf) > 3.0
    return pd.DataFrame({"progresiva_m": prog, "este": [p.x for p in pts], "norte": [p.y for p in pts],
                         "cota_dem_m": z, "cota_m": zf, "artefacto": art})

def cruces(line, nombre):
    out = []
    feats = [("VIA", k, n, g) for k, n, g in hw] + ([("VIA", "carretera principal", TRAZADO.get("nombre_via", "Vía principal"), road)] if road else []) + \
            [("AGUA", k, n, g) for k, n, g in wat]
    for tipo, clase, nom, g in feats:
        inter = line.intersection(g)
        if inter.is_empty:
            continue
        geoms = getattr(inter, "geoms", [inter])
        for p in geoms:
            if p.geom_type != "Point":
                continue
            out.append({"tramo": nombre, "tipo": tipo, "clase": clase, "nombre": nom,
                        "progresiva_m": round(line.project(p), 1), "este": round(p.x, 2), "norte": round(p.y, 2)})
    df = pd.DataFrame(out).drop_duplicates(subset=["progresiva_m"]) if out else pd.DataFrame(out)
    return df

troncal = LineString(meta["vertices"])
pt = perfil(troncal)
pt.to_csv(W / "perfil_troncal.csv", index=False)
cr = cruces(troncal, "TRONCAL")
if len(cr):
    cr = cr.sort_values(["tramo", "progresiva_m"]).reset_index(drop=True)
    cr.insert(0, "cruce_id", [f"CR-{i+1:02d}" for i in range(len(cr))])
if not len(cr): cr = pd.DataFrame(columns=["cruce_id", "tramo", "tipo", "clase", "nombre", "progresiva_m", "este", "norte"])
cr.to_csv(W / "cruces.csv", index=False)
if road is not None:
    pt["dist_via_m"] = [road.distance(Point(x, y)) for x, y in zip(pt.este, pt.norte)]
    pt.to_csv(W / "perfil_troncal.csv", index=False)
near_b = [(round(troncal.project(b.centroid)), round(b.distance(troncal), 1)) for b in blds if b.distance(troncal) < 15]
pd.DataFrame(near_b, columns=["progresiva_m", "distancia_m"]).to_csv(W / "edificaciones_cercanas.csv", index=False)
print("cota troncal", pt.cota_m.min().round(1), pt.cota_m.max().round(1), "artefactos:", int(pt.artefacto.sum()))
print("cruces:\n", cr.to_string() if len(cr) else "ninguno")
print("edificaciones <15 m:", near_b)
