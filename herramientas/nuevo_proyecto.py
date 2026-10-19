#!/usr/bin/env python3
"""Crea la carpeta de un proyecto nuevo a partir de la plantilla.

Uso:
    python herramientas/nuevo_proyecto.py mi-proyecto
    python herramientas/nuevo_proyecto.py mi-proyecto --inicio "Urcos" -71.6234 -13.6861 --fin "Cusipata" -71.5003 -13.9082 --epsg 32719

Crea:  proyectos/mi-proyecto/proyecto.yaml   (copia comentada de plantilla/proyecto.yaml)
       proyectos/mi-proyecto/datos/          (aquí van dem.tif, osm_corredor.geojson y la ruta)"""
import argparse, re, shutil, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", help="nombre corto sin espacios, p. ej. urcos-cusipata")
    ap.add_argument("--inicio", nargs=3, metavar=("NOMBRE", "LON", "LAT"))
    ap.add_argument("--fin", nargs=3, metavar=("NOMBRE", "LON", "LAT"))
    ap.add_argument("--epsg", type=int, help="32717, 32718 o 32719 (zona UTM sur)")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", a.carpeta):
        sys.exit("Use solo letras, números, guiones y guiones bajos en el nombre de la carpeta.")
    dst = RAIZ / "proyectos" / a.carpeta
    if dst.exists(): sys.exit(f"Ya existe {dst}")
    (dst / "datos").mkdir(parents=True)
    txt = (RAIZ / "plantilla" / "proyecto.yaml").read_text(encoding="utf-8")
    for clave, val in (("inicio", a.inicio), ("fin", a.fin)):
        if val:
            nombre, lon, lat = val[0], float(val[1]), float(val[2])
            txt = re.sub(rf'(  {clave}:\s*\{{nombre: )"[^"]*",\s*lon: [-\d.]+,\s*lat: [-\d.]+',
                         lambda m: f'{m.group(1)}"{nombre}", lon: {lon:.7f}, lat: {lat:.7f}', txt, count=1)
    if a.epsg:
        txt = re.sub(r"epsg_utm: \d+", f"epsg_utm: {a.epsg}", txt, count=1)
    elif a.inicio:
        lon = float(a.inicio[1]); zona = int((lon + 180) // 6) + 1
        txt = re.sub(r"epsg_utm: \d+", f"epsg_utm: {32700 + zona}", txt, count=1)
    (dst / "proyecto.yaml").write_text(txt, encoding="utf-8")
    print(f"Creado {dst}\n")
    print("Siguientes pasos:")
    print(f"  1. Complete los campos '<<< COMPLETAR' de {dst / 'proyecto.yaml'}")
    print(f"  2. python herramientas/preparar_datos.py {dst.relative_to(RAIZ) / 'proyecto.yaml'} --ruta     (DEM, OSM y ruta)")
    print(f"     o coloque a mano en {dst.relative_to(RAIZ) / 'datos'}: dem.tif, osm_corredor.geojson y la ruta (KML/GeoJSON)")
    print(f"  3. python generar.py {dst.relative_to(RAIZ) / 'proyecto.yaml'} --hasta 3      (revise trazado y estructuras)")
    print(f"  4. python generar.py {dst.relative_to(RAIZ) / 'proyecto.yaml'}                (expediente completo)")


if __name__ == "__main__":
    main()
