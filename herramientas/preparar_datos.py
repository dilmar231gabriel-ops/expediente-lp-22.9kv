#!/usr/bin/env python3
"""Descarga los datos geográficos de un proyecto nuevo a partir de los puntos de proyecto.yaml:

  1. DEM  Copernicus GLO-30 (30 m, gratuito, AWS Open Data)        → datos/dem.tif
  2. OSM  vías, ríos, edificaciones y centros poblados (Overpass)   → datos/osm_corredor.geojson
  3. RUTA por carretera entre inicio y fin (OSRM, opcional)         → datos/ruta_via.geojson

Uso:
    python herramientas/preparar_datos.py proyectos/mi-proyecto/proyecto.yaml            # DEM + OSM
    python herramientas/preparar_datos.py proyectos/mi-proyecto/proyecto.yaml --ruta     # además, ruta por carretera
    python herramientas/preparar_datos.py proyectos/mi-proyecto/proyecto.yaml --margen 4000

Requiere conexión a internet. Si su red bloquea alguno de los servicios, obtenga el dato a mano (ver
docs/GUIA_NUEVO_PROYECTO.md, sección "Datos sin internet / alternativos") y colóquelo en datos/ con el mismo nombre.

NOTA: esta herramienta se escribió y revisó sin acceso a esos servicios (el entorno donde se armó la plantilla bloquea
internet), por lo que es la única parte del repositorio que no se ejecutó de punta a punta. Si algo falla, el mensaje
indica qué archivo colocar a mano."""
import argparse, json, math, sys, urllib.parse, urllib.request
from pathlib import Path
import yaml

UA = {"User-Agent": "expediente-lp-plantilla/1.0 (uso académico/técnico)"}


def bbox(cfg, margen_m):
    pts = [cfg["puntos"]["inicio"], cfg["puntos"]["fin"]] + list(cfg["puntos"].get("derivaciones") or [])
    lons = [float(p["lon"]) for p in pts]; lats = [float(p["lat"]) for p in pts]
    dlat = margen_m / 111_320; dlon = margen_m / (111_320 * math.cos(math.radians(sum(lats) / len(lats))))
    return min(lons) - dlon, min(lats) - dlat, max(lons) + dlon, max(lats) + dlat


# ------------------------------------------------------------------------------------------------ DEM
def tile_url(lat0, lon0):
    ns = "N" if lat0 >= 0 else "S"; ew = "E" if lon0 >= 0 else "W"
    name = f"Copernicus_DSM_COG_10_{ns}{abs(lat0):02d}_00_{ew}{abs(lon0):03d}_00_DEM"
    return f"https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif"


def descargar_dem(bb, destino):
    import rasterio
    W, S, E, N = bb
    fuentes = []
    for la in range(math.floor(S), math.floor(N) + 1):
        for lo in range(math.floor(W), math.floor(E) + 1):
            url = tile_url(la, lo); print("  DEM:", url)
            try:
                fuentes.append(rasterio.open("/vsicurl/" + url))
            except Exception as e:
                print(f"  (no disponible: {e})")
    if not fuentes:
        sys.exit("No se pudo leer ningún mosaico del DEM. Descárguelo a mano (OpenTopography / Copernicus Browser) y guárdelo como datos/dem.tif")
    escribir_recorte(fuentes, bb, destino)


def escribir_recorte(fuentes, bb, destino):
    import rasterio
    from rasterio.merge import merge
    W, S, E, N = bb
    arr, tr = merge(fuentes, bounds=(W, S, E, N))
    f0 = fuentes[0]
    prof = {"driver": "GTiff", "dtype": arr.dtype, "count": arr.shape[0], "height": arr.shape[1], "width": arr.shape[2],
            "crs": f0.crs, "transform": tr, "nodata": f0.nodata, "compress": "deflate"}
    with rasterio.open(destino, "w", **prof) as dst:
        dst.write(arr)
    print(f"  → {destino} ({arr.shape[2]} × {arr.shape[1]} px)")


# ------------------------------------------------------------------------------------------------ OSM
def descargar_osm(bb, destino):
    W, S, E, N = bb
    q = f"""[out:json][timeout:180];
(
  way["highway"]({S},{W},{N},{E});
  way["waterway"]({S},{W},{N},{E});
  way["building"]({S},{W},{N},{E});
  node["place"]({S},{W},{N},{E});
);
out geom;"""
    servidores = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
    data = None
    for srv in servidores:
        try:
            print("  OSM:", srv)
            req = urllib.request.Request(srv, data=urllib.parse.urlencode({"data": q}).encode(), headers=UA)
            data = json.load(urllib.request.urlopen(req, timeout=240)); break
        except Exception as e:
            print(f"  (falló: {e})")
    if data is None:
        print("  No se pudo descargar OSM: el expediente se genera igual, pero sin cruces ni edificaciones. Puede exportar las capas "
              "desde https://overpass-turbo.eu como GeoJSON y guardarlas como datos/osm_corredor.geojson."); return
    feats = []
    for el in data.get("elements", []):
        t = el.get("tags", {})
        props = {"name": t.get("name"), "building": t.get("building"), "highway": t.get("highway"), "waterway": t.get("waterway"), "landuse": t.get("landuse")}
        if el["type"] == "node":
            props["place"] = t.get("place")
            feats.append({"type": "Feature", "properties": props, "geometry": {"type": "Point", "coordinates": [el["lon"], el["lat"]]}})
        elif el["type"] == "way" and el.get("geometry"):
            c = [[g["lon"], g["lat"]] for g in el["geometry"]]
            if props["building"] and len(c) >= 4 and c[0] == c[-1]:
                geom = {"type": "Polygon", "coordinates": [c]}
            else:
                geom = {"type": "LineString", "coordinates": c}
            feats.append({"type": "Feature", "properties": props, "geometry": geom})
    Path(destino).write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False), encoding="utf-8")
    print(f"  → {destino} ({len(feats)} elementos)")


# ------------------------------------------------------------------------------------------------ RUTA
def descargar_ruta(cfg, destino):
    a, b = cfg["puntos"]["inicio"], cfg["puntos"]["fin"]
    url = (f"https://router.project-osrm.org/route/v1/driving/{a['lon']},{a['lat']};{b['lon']},{b['lat']}"
           "?overview=full&geometries=geojson")
    print("  RUTA:", url)
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        g = r["routes"][0]["geometry"]
    except Exception as e:
        print(f"  (falló: {e}). Dibuje la ruta en Google Earth (Agregar ruta), guárdela como KML y póngala en trazado.archivo_ruta."); return
    Path(destino).write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"fuente": "OSRM / OpenStreetMap"},
                                                                                     "geometry": g}]}), encoding="utf-8")
    print(f"  → {destino} ({len(g['coordinates'])} puntos, {r['routes'][0]['distance']/1000:.1f} km). "
          "En proyecto.yaml use: archivo_ruta: datos/ruta_via.geojson, ruta_es_via: true, desplazamiento_m: 40")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config"); ap.add_argument("--margen", type=float, default=3000, help="margen alrededor de los puntos (m)")
    ap.add_argument("--ruta", action="store_true", help="descargar también la ruta por carretera (OSRM)")
    ap.add_argument("--solo", choices=["dem", "osm", "ruta"], help="descargar solo una capa")
    a = ap.parse_args()
    cfgp = Path(a.config); cfg = yaml.safe_load(open(cfgp, encoding="utf-8"))
    d = cfgp.parent / "datos"; d.mkdir(exist_ok=True)
    bb = bbox(cfg, a.margen); print("Área (W, S, E, N):", [round(x, 5) for x in bb])
    if a.solo in (None, "dem"): descargar_dem(bb, d / "dem.tif")
    if a.solo in (None, "osm"): descargar_osm(bb, d / "osm_corredor.geojson")
    if a.ruta or a.solo == "ruta": descargar_ruta(cfg, d / "ruta_via.geojson")


if __name__ == "__main__":
    main()
