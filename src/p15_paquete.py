"""PASO 15 – Ensambla el expediente en 11 volúmenes, convierte a PDF (LibreOffice), genera el cronograma MS Project (XML),
el informe de generación y verificación, y los ZIP por volumen y completo. Uso: python p15_paquete.py WORK DESTINO"""
import json, re, shutil, sys, unicodedata, zipfile, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from params import *
from docgen import *
from comun import cargar, lista
import oficina
from dxf_compatible import convertir

W = Path(sys.argv[1]); DST = Path(sys.argv[2])
def slug(t):
    t = re.sub(r"[–—\s/,;:]+", "_", t); t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_").upper()
NOMBRE_RAIZ = "EXPEDIENTE_" + slug(PROYECTO["nombre_corto"])
C = cargar(W)
R = DST / NOMBRE_RAIZ
if R.exists(): shutil.rmtree(R)
ET = R / "Expediente Tecnico"
V = {k: ET / k for k in ["VOL. I FICHA TECNICA", "VOL. II RESUMEN EJECUTIVO", "VOL. III MEMORIA DESCRIPTIVA", "VOL. IV ESPECIFICACIONES TECNICAS",
                         "VOL. V METRADO Y PRESUPUESTO", "VOL. VI CALCULOS JUSTIFICATIVOS", "VOL. VII PLANOS Y LAMINAS DE DETALLE",
                         "VOL. VIII ESTUDIO DE GEOLOGIA Y GEOTECNIA", "VOL. IX ANALISIS DE FLUJO DEL SISTEMA", "VOL. X REQUERIMIENTO MINIMO - EJECUTOR Y SUPERVISOR",
                         "VOL. XI ANEXOS"]}
for p_ in V.values(): p_.mkdir(parents=True, exist_ok=True)
CAR = R / "CARATULA Y SEPARADORES"; CAR.mkdir(parents=True)
D2 = W / "docs2"
def cp(src, dst): dst.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst / Path(src).name)
cp(D2 / "00 CARATULA Y SEPARADORES.docx", CAR)
mapa = {"VOL. I FICHA TECNICA.docx": "VOL. I FICHA TECNICA", "VOL. II RESUMEN EJECUTIVO.docx": "VOL. II RESUMEN EJECUTIVO",
        "VOL. III MEMORIA DESCRIPTIVA.docx": "VOL. III MEMORIA DESCRIPTIVA", "VOL. IV ESPECIFICACIONES TECNICAS DE SUMINISTRO.docx": "VOL. IV ESPECIFICACIONES TECNICAS",
        "VOL. IV ESPECIFICACIONES TECNICAS DE MONTAJE.docx": "VOL. IV ESPECIFICACIONES TECNICAS", "VOL. VI CALCULOS JUSTIFICATIVOS.docx": "VOL. VI CALCULOS JUSTIFICATIVOS",
        "VOL. VIII ESTUDIO DE GEOLOGIA Y GEOTECNIA.docx": "VOL. VIII ESTUDIO DE GEOLOGIA Y GEOTECNIA",
        "VOL. IX ANALISIS DE FLUJO Y COORDINACION DE PROTECCIONES.docx": "VOL. IX ANALISIS DE FLUJO DEL SISTEMA", "VOL. IX CORTOCIRCUITO.xlsx": "VOL. IX ANALISIS DE FLUJO DEL SISTEMA",
        "VOL. X REQUERIMIENTO MINIMO EJECUTOR.docx": "VOL. X REQUERIMIENTO MINIMO - EJECUTOR Y SUPERVISOR", "VOL. X REQUERIMIENTO MINIMO SUPERVISOR.docx": "VOL. X REQUERIMIENTO MINIMO - EJECUTOR Y SUPERVISOR",
        "VOL. XI ANEXOS.docx": "VOL. XI ANEXOS", "VOL. XI FORMATOS GESTION DE RIESGOS.xlsx": "VOL. XI ANEXOS", "VOL. XI CUADRO COMPARATIVO DE COTIZACIONES.xlsx": "VOL. XI ANEXOS"}
for f, v in mapa.items(): cp(D2 / f, V[v])
# Vol V
cp(W / "presup/PRESUPUESTO.xlsx", V["VOL. V METRADO Y PRESUPUESTO"])
XL_PRES = V["VOL. V METRADO Y PRESUPUESTO"] / f"PRESUPUESTO {slug(PROYECTO['nombre_corto']).replace('_', ' ')}.xlsx"
(V["VOL. V METRADO Y PRESUPUESTO"] / "PRESUPUESTO.xlsx").rename(XL_PRES)
# cronograma MS Project (MSPDI)
meta = json.load(open(W / "presup_meta.json"))
PLAZO = PROYECTO["plazo_dias"]
_fi = CFG["proyecto"].get("fecha_inicio_obra")            # AAAA-MM-DD; por defecto, primer lunes de enero del año base
if _fi: ini = dt.date.fromisoformat(str(_fi))
else:
    ini = dt.date(PROYECTO["anio_base"], 1, 1); ini += dt.timedelta(days=(7 - ini.weekday()) % 7)
acts = [("A", "SUMINISTRO Y TRANSPORTE DE MATERIALES A ALMACÉN DE OBRA", 1, max(1, round(PLAZO / 2)))] + [(a[0], a[1], a[2], a[3]) for a in meta["ACT"]]
x = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', '<Project xmlns="http://schemas.microsoft.com/project">',
     f"<Name>Cronograma {PROYECTO['nombre']}</Name>", f"<StartDate>{ini}T08:00:00</StartDate>", "<CalendarUID>1</CalendarUID>",
     "<Calendars><Calendar><UID>1</UID><Name>Calendario 7 días</Name><IsBaseCalendar>1</IsBaseCalendar><WeekDays>"
     + "".join(f"<WeekDay><DayType>{k}</DayType><DayWorking>1</DayWorking><WorkingTimes><WorkingTime><FromTime>08:00:00</FromTime><ToTime>17:00:00</ToTime></WorkingTime></WorkingTimes></WeekDay>" for k in range(1, 8))
     + "</WeekDays></Calendar></Calendars><Tasks>"]
x.append(f"<Task><UID>0</UID><ID>0</ID><Name>{PROYECTO['nombre']}</Name><OutlineLevel>0</OutlineLevel><Summary>1</Summary><Start>{ini}T08:00:00</Start>"
         f"<Finish>{ini + dt.timedelta(days=PLAZO - 1)}T17:00:00</Finish></Task>")
for k, (it, nm, a, b) in enumerate(acts, 1):
    s0 = ini + dt.timedelta(days=a - 1); s1 = ini + dt.timedelta(days=b - 1)
    x.append(f"<Task><UID>{k}</UID><ID>{k}</ID><Name>{it} {nm}</Name><OutlineLevel>1</OutlineLevel><Start>{s0}T08:00:00</Start><Finish>{s1}T17:00:00</Finish>"
             f"<Duration>PT{(b-a+1)*8}H0M0S</Duration><DurationFormat>7</DurationFormat><ManualStart>{s0}T08:00:00</ManualStart><ManualFinish>{s1}T17:00:00</ManualFinish>"
             f"<Manual>1</Manual></Task>")
x.append("</Tasks></Project>")
(V["VOL. V METRADO Y PRESUPUESTO"] / "CRONOGRAMA (MS Project XML).xml").write_text("\n".join(x), encoding="utf-8")
# Vol VI anexos
AN = V["VOL. VI CALCULOS JUSTIFICATIVOS"] / "ANEXOS"
for f in sorted((W / "anexos").glob("*.xlsx")): cp(f, AN)
# Vol VII planos
P7 = V["VOL. VII PLANOS Y LAMINAS DE DETALLE"]
for sub, src in (("PLANOS", W / "planos2/generales"), ("LAMINAS DE DETALLE", W / "planos2/laminas")):
    for f in sorted(src.glob("*.dxf")):
        cp(f, P7 / sub / "DXF (AutoCAD)")
        # versión simple R2010 (solo polilíneas, círculos y textos) por si alguna versión de AutoCAD no abre la completa
        (P7 / sub / "DXF compatible (R2010 simple)").mkdir(parents=True, exist_ok=True)
        convertir(f, P7 / sub / "DXF compatible (R2010 simple)" / f.name)
    for f in sorted(src.glob("*.pdf")): cp(f, P7 / sub / "PDF")
for f in (W / "georef2").glob("*"): cp(f, P7 / "COORDENADAS Y PLANO GEORREFERENCIADO")
for f in (W / "gis2").glob("*"): cp(f, P7 / "GIS (Google Earth)")

# PDF de documentos y libros
def soffice(files, outdir): oficina.a_pdf(files, outdir)
for folder in [CAR] + list(V.values()):
    docs = sorted(folder.glob("*.docx"))
    if docs: soffice(docs, folder)
soffice([XL_PRES], V["VOL. V METRADO Y PRESUPUESTO"])
(AN / "PDF").mkdir(exist_ok=True); soffice(sorted(AN.glob("*.xlsx")), AN / "PDF")
soffice([V["VOL. IX ANALISIS DE FLUJO DEL SISTEMA"] / "VOL. IX CORTOCIRCUITO.xlsx"], V["VOL. IX ANALISIS DE FLUJO DEL SISTEMA"])

# informe de adaptación y verificación
K = json.load(open(W / "datos_clave.json"))
d = nuevo("INFORME DE GENERACIÓN Y VERIFICACIÓN")
p(d, "INFORME DE GENERACIÓN DEL EXPEDIENTE Y VERIFICACIÓN DE COHERENCIA", bold=True, align="C", size=13)
p(d, f"“{PROYECTO['nombre']}”", bold=True, align="C", size=11)
p(d, f"Generado automáticamente el {dt.date.today():%d/%m/%Y} a partir de proyecto.yaml con la plantilla de expediente técnico de líneas primarias 22,9 kV.", italic=True, size=10)
h(d, "1. Contenido del expediente")
tabla(d, ["Volumen", "Contenido", "Archivos"], [
    ("Carátula y separadores", "Carátula, contenido y separadores de los 11 volúmenes", "docx/pdf"),
    ("Vol. I", "Ficha técnica", "docx/pdf"), ("Vol. II", "Resumen ejecutivo", "docx/pdf"),
    ("Vol. III", "Memoria descriptiva", "docx/pdf"), ("Vol. IV", "ETS-LP-01 a 13 y especificaciones de montaje por partida", "2 docx/pdf"),
    ("Vol. V", "Presupuesto (RESUMEN OBRA, GG, GS, CCL, CRONOG_VALORIZ, SUMINISTRO LP, MONTAJE LP, TRANSPORTE LP, APU, FP, PLANILLA, BP…) y cronograma MS Project",
     "xlsx con fórmulas, pdf, xml"),
    ("Vol. VI", "Cálculos justificativos (Cap. II, 2.1–2.9) y Anexos 1–9 en Excel con fórmulas", "docx/pdf + 9 xlsx + pdf"),
    ("Vol. VII", "Ubicación, planta-poligonal, hojas de perfil y planimetría, unifilar, cruce, láminas A4 de armados, coordenadas y GIS", "DXF + PDF + KML/CSV"),
    ("Vol. VIII", "Informe de gabinete, TdR del EMS y diseño de cimentaciones (sin datos de campo)", "docx/pdf"),
    ("Vol. IX", "Flujo, cortocircuito y protección preliminares (hoja de cálculo propia)", "docx/pdf + xlsx"),
    ("Vol. X", "Requerimientos mínimos del ejecutor y del supervisor", "2 docx/pdf"), ("Vol. XI", "Riesgos, panel fotográfico (formato), cotizaciones (cuadro), datos pendientes", "docx/pdf + 2 xlsx")],
    widths=[3.0, 9.0, 3.6], size=8.5)
h(d, "2. Decisiones de diseño")
_E = C["E"]; _nts = int((_E.armado == "TS-3").sum())
bullets(d, ["Armados normalizados (crucetas FºGº Tipo I, PIN ANSI 56-4, poliméricos 36 kV) con la nomenclatura PS1-3, PA1-3, PA2-3, TS-3, PR3-3, DT-3, PSER-3 y PTH-3.",
            f"Equipos de clase 38 kV, 170 kV-BIL (altitud de diseño {fmt(C['ALT'],0)} m s.n.m.); pararrayos de 24 kV.",
            f"Conductor AAAC {SECCION} mm² (kit de materiales); óptimo económico calculado: {C['K']['el'].get('seccion_optima')} mm².",
            (f"Estructuras TS-3 en {_nts} ubicaciones con arrancamiento a temperatura mínima detectado por el cálculo del vano peso." if _nts else
             "No se detectó arrancamiento en estructuras de suspensión."),
            "Bloque de anclaje de retenidas en excavación de 0,80 × 0,80 × 2,00 m (FS ≥ 2).",
            "Postes de 12 m (y 13 m donde lo exige el plantillado), verificados vano por vano.",
            f"Cable de guarda: {'sí' if CFG['diseno'].get('cable_guarda') else 'no'} (nivel isoceráunico {SIS['isoceraunico']})."])
h(d, "3. Verificación de coherencia")
tabla(d, ["Verificación", "Resultado", "Detalle"], [(c["verificacion"], c["resultado"], c["detalle"]) for c in K["chk"]], widths=[7.0, 2.4, 6.2], size=8)
h(d, "4. Datos de campo y documentos externos pendientes")
p(d, "Se listan en el Vol. XI (Anexo XI-4). Ningún dato de campo ha sido inventado: los valores supuestos están identificados como tales en cada hoja de cálculo "
     "(celdas amarillas con texto azul) y en la columna de fuente.")
h(d, "5. Formatos de entrega")
bullets(d, ["Documentos: Word (.docx) editable y PDF.", "Cálculos, metrados y presupuesto: Excel (.xlsx) con fórmulas vivas, recalculados sin errores.",
            "Planos: DXF (se abren y editan en AutoCAD, BricsCAD, ZWCAD, DraftSight o LibreCAD) y PDF. Para obtener DWG: abrir el DXF en AutoCAD y GUARDAR COMO .dwg."])
p(d, f"Proyectista: {PROYECTO['proyectista']}", bold=True, align="R")
d.save(R / "00 INFORME DE GENERACION Y VERIFICACION.docx"); soffice([R / "00 INFORME DE GENERACION Y VERIFICACION.docx"], R)

# ZIP por volumen y completo
ZD = DST / "ZIPS"
if ZD.exists(): shutil.rmtree(ZD)
ZD.mkdir()
def zipdir(src, zf, base):
    for f in sorted(src.rglob("*")):
        if f.is_file(): zf.write(f, f.relative_to(base))
for nm, folder in [("00_CARATULA_Y_SEPARADORES", CAR)] + [(k.replace(". ", "_").replace(" ", "_").replace("-", ""), v) for k, v in V.items()]:
    with zipfile.ZipFile(ZD / f"{nm}.zip", "w", zipfile.ZIP_DEFLATED) as zf: zipdir(folder, zf, R)
with zipfile.ZipFile(ZD / f"{NOMBRE_RAIZ}_COMPLETO.zip", "w", zipfile.ZIP_DEFLATED) as zf: zipdir(R, zf, DST)
print("ok paquete", sum(1 for _ in R.rglob("*") if _.is_file()), "archivos")
