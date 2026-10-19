"""Salidas GIS: KML/KMZ, GeoJSON y CSV del trazado rectificado y las estructuras."""
import json, sys, zipfile
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from params import PROYECTO
import re as _re
import unicodedata as _ud
_t = _ud.normalize("NFKD", _re.sub(r"[–—\s/,;:]+", "_", PROYECTO["nombre_corto"])).encode("ascii", "ignore").decode()
BASE_N = "TRAZADO_" + _re.sub(r"[^A-Za-z0-9]+", "_", _t).strip("_")

W = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
for _f in list(OUT.glob("*.km[lz]")) + list(OUT.glob("*.geojson")): _f.unlink()   # limpia salidas anteriores
E = pd.read_csv(W / "planilla_estructuras.csv"); tr = json.load(open(W / "trazado_rectificado.geojson"))
color = {"PS1-3": "ff0000ff", "PA1-3": "ff00a5ff", "PA2-3": "ff00a5ff", "TS-3": "ff00a5ff", "PR3-3": "ff0000ff", "DT-3": "ffff00ff", "PTH-3": "ff00ff00", "PSER-3": "ff00ff00"}
k = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>', f"<name>{escape(PROYECTO['nombre_corto'])}</name>"]
for a, c in color.items():
    k.append(f'<Style id="{a}"><IconStyle><color>{c}</color><scale>0.7</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle></Style>')
k.append('<Style id="eje"><LineStyle><color>ff0000ff</color><width>3</width></LineStyle></Style>')
k.append("<Folder><name>Trazado</name>")
for f in tr["features"]:
    cs = " ".join(f"{x:.7f},{y:.7f},0" for x, y in f["geometry"]["coordinates"])
    k.append(f"<Placemark><name>{escape(f['properties']['nombre'])}</name><styleUrl>#eje</styleUrl><LineString><tessellate>1</tessellate><coordinates>{cs}</coordinates></LineString></Placemark>")
k.append("</Folder><Folder><name>Estructuras</name>")
for r in E.itertuples():
    desc = f"Armado {r.armado} | Poste CAC {r.poste} | Progresiva {r.progresiva_m:.1f} m | Cota {r.cota_m:.1f} m | Retenidas {int(r.n_retenidas)} | PAT {r.puesta_tierra}"
    k.append(f"<Placemark><name>{r.estructura}</name><description>{escape(desc)}</description><styleUrl>#{r.armado}</styleUrl><Point><coordinates>{r.lon:.7f},{r.lat:.7f},0</coordinates></Point></Placemark>")
k.append("</Folder></Document></kml>")
kml = "\n".join(k)
(OUT / f"{BASE_N}.kml").write_text(kml, encoding="utf-8")
with zipfile.ZipFile(OUT / f"{BASE_N}.kmz", "w", zipfile.ZIP_DEFLATED) as z: z.writestr("doc.kml", kml)
fc = {"type": "FeatureCollection", "features": tr["features"] + [
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [r.lon, r.lat]},
     "properties": {"estructura": r.estructura, "armado": r.armado, "poste": r.poste, "progresiva_m": round(r.progresiva_m, 2),
                    "este": round(r.este, 2), "norte": round(r.norte, 2), "cota_m": round(r.cota_m, 2), "retenidas": int(r.n_retenidas), "pat": r.puesta_tierra}}
    for r in E.itertuples()]}
(OUT / f"{BASE_N}.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
E[["estructura", "progresiva_m", "este", "norte", "lat", "lon", "cota_m", "armado", "poste", "n_retenidas", "puesta_tierra"]].to_csv(OUT / "estructuras_utm.csv", index=False)
print("OK GIS")
