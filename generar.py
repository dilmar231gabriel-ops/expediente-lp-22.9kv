#!/usr/bin/env python3
"""Genera el expediente técnico completo de una línea primaria 22,9 kV a partir de un archivo proyecto.yaml.

Uso:
    python generar.py proyectos/<mi-proyecto>/proyecto.yaml            # todo el expediente
    python generar.py proyectos/<mi-proyecto>/proyecto.yaml --hasta 3  # solo pasos 1 a 3 (trazado, perfil, ingeniería)
    python generar.py proyectos/<mi-proyecto>/proyecto.yaml --desde 6  # rehace del paso 6 en adelante

Salida: salida/<mi-proyecto>/  (carpeta 'trabajo' con intermedios y carpeta EXPEDIENTE con los 11 volúmenes + ZIP)
Requisitos: Python 3.10+, paquetes de requirements.txt y LibreOffice (para recalcular Excel y convertir a PDF)."""
import argparse, os, subprocess, sys, time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SRC = RAIZ / "src"
PASOS = [  # (n, script, descripción, argumentos: W = carpeta de trabajo, O = carpeta de salida)
    (1, "p01_trazado.py", "Trazado del eje de la línea", ["{W}"]),
    (2, "p02_perfil.py", "Perfil del terreno y cruces", ["{W}"]),
    (3, "p03_ingenieria.py", "Demanda, conductor, cálculo mecánico, plantillado, estructuras", ["{W}"]),
    (4, "p04_anexos_electricos.py", "Anexos 1, 2, 3 y 8 (aislamiento, pararrayos, PAT, caída de tensión)", ["{W}", "{W}/anexos"]),
    (5, "p05_anexos_mecanicos.py", "Anexos 4, 5, 6, 7 y 9 (CMC, cimentación, CME, retenidas, planilla)", ["{W}", "{W}/anexos"]),
    (6, "p06_presupuesto.py", "Metrado, APU, presupuesto, cronogramas y fórmula polinómica", ["{W}", "{W}/presup/PRESUPUESTO.xlsx"]),
    (7, "p07_laminas.py", "Láminas de detalle (armados, retenidas, PAT, cimentación)", ["{W}/planos2/laminas"]),
    (8, "p08_planos.py", "Planos de ubicación, planta, perfil, unifilar y cruce", ["{W}", "{W}/planos2/generales"]),
    (9, "p09_gis.py", "KML / KMZ / GeoJSON para Google Earth", ["{W}", "{W}/gis2"]),
    (10, "p10_georeferenciado.py", "Plano georreferenciado y coordenadas de postes", ["{W}", "{W}/georef2"]),
    (11, "p11_verificacion.py", "Verificación cruzada de coherencia", ["{W}"]),
    (12, "p12_docs_generales.py", "Carátula y Volúmenes I, II y III", ["{W}", "{W}/docs2"]),
    (13, "p13_docs_especificaciones.py", "Volumen IV (especificaciones técnicas)", ["{W}", "{W}/docs2"]),
    (14, "p14_docs_calculos.py", "Volúmenes VI, VIII, IX, X y XI", ["{W}", "{W}/docs2"]),
    (15, "p15_paquete.py", "Ensamblado del expediente, PDF y ZIP", ["{W}", "{O}"]),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", help="ruta del archivo proyecto.yaml")
    ap.add_argument("--desde", type=int, default=1); ap.add_argument("--hasta", type=int, default=15)
    ap.add_argument("--salida", default=None, help="carpeta de salida (por defecto salida/<nombre de la carpeta del proyecto>)")
    a = ap.parse_args()
    cfg = Path(a.config).resolve()
    if not cfg.exists(): sys.exit(f"No existe {cfg}")
    out = Path(a.salida).resolve() if a.salida else RAIZ / "salida" / cfg.parent.name
    W = out / "trabajo"; W.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy(); env["LP_CONFIG"] = str(cfg); env["PYTHONIOENCODING"] = "utf-8"
    sys.path.insert(0, str(SRC)); os.environ["LP_CONFIG"] = str(cfg)
    import oficina
    (W / "presup").mkdir(exist_ok=True)
    for n, script, desc, plantilla_args in PASOS:
        if not (a.desde <= n <= a.hasta): continue
        args = [x.replace("{W}", str(W)).replace("{O}", str(out)) for x in plantilla_args]
        t = time.time(); print(f"[{n:2d}/15] {desc} ...", flush=True)
        r = subprocess.run([sys.executable, "-W", "ignore", str(SRC / script)] + args, env=env, cwd=str(SRC),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        (W / "logs").mkdir(exist_ok=True); (W / "logs" / f"{n:02d}_{script}.log").write_text(r.stdout, encoding="utf-8")
        if r.returncode != 0:
            print(r.stdout[-3000:]); sys.exit(f"ERROR en el paso {n} ({script}). Revise {W / 'logs'}")
        # recálculo de libros Excel generados en el paso
        libros = []
        if n in (4, 5): libros = sorted((W / "anexos").glob("*.xlsx"))
        if n == 6: libros = [W / "presup" / "PRESUPUESTO.xlsx"]
        if n == 14: libros = sorted((W / "docs2").glob("*.xlsx"))
        for xl in libros:
            oficina.recalcular(xl); ne, donde = oficina.errores_excel(xl)
            if ne: sys.exit(f"ERROR: {xl.name} tiene {ne} celdas con error: {donde}")
        if n == 11:
            print("        " + "\n        ".join(l for l in r.stdout.splitlines() if l.startswith("[")))
        print(f"        listo en {time.time() - t:.0f} s", flush=True)
    print(f"\nExpediente en: {out}")


if __name__ == "__main__":
    main()
