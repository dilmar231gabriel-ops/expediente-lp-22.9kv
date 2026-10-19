"""Carátula y separadores, Volumen I (Ficha técnica), Volumen II (Resumen ejecutivo) y Volumen III (Memoria descriptiva).
Uso: python p12_docs_generales.py WORK OUTDIR"""
import json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from params import *
from catalogo import ARM_DESC, MATD, TC, TC_FUENTE
from docgen import *
from comun import cargar, dias_txt, lista, clima, fusibles_txt, png_de_pdf

W = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
C = cargar(W); K = C["K"]; E = C["E"]; dem = C["dem"]; L = C["L"]; DER = C["ders"]
INI, FINN, E0, EF, ALT = C["ini"], C["fin"], C["E0"], C["EF"], C["ALT"]
PLAZO = dias_txt(PROYECTO["plazo_dias"]); CONC = PROYECTO["concesionaria"]; ZU = f"UTM WGS 84, zona {ZONA_UTM}"
CLI_FUENTE = CLIMA.get("estacion", "SENAMHI (estación por definir)")
M = K["met"]; P = K["pres"]; el = K["el"]
nA = M["armados"]; nP = M["postes"]
A0, A20 = int(dem.anio.min()), int(dem.anio.max())
VOLS = [("VOLUMEN I", "FICHA TÉCNICA"), ("VOLUMEN II", "RESUMEN EJECUTIVO"), ("VOLUMEN III", "MEMORIA DESCRIPTIVA"),
        ("VOLUMEN IV", "ESPECIFICACIONES TÉCNICAS DE SUMINISTRO DE MATERIALES\nESPECIFICACIONES TÉCNICAS DE MONTAJE ELECTROMECÁNICO"),
        ("VOLUMEN V", "METRADO Y PRESUPUESTO"), ("VOLUMEN VI", "CÁLCULOS JUSTIFICATIVOS"), ("VOLUMEN VII", "PLANOS Y LÁMINAS DE DETALLE"),
        ("VOLUMEN VIII", "ESTUDIO DE GEOLOGÍA Y GEOTECNIA, DISEÑO DE CIMENTACIONES"), ("VOLUMEN IX", "ANÁLISIS DE FLUJO DEL SISTEMA Y COORDINACIÓN DE PROTECCIONES"),
        ("VOLUMEN X", "REQUERIMIENTO MÍNIMO – EJECUTOR Y SUPERVISOR DE OBRA"), ("VOLUMEN XI", "ANEXOS")]
SEPAR = {"VOLUMEN IV": ["ESPECIFICACIONES TÉCNICAS DE SUMINISTRO DE MATERIALES", "ESPECIFICACIONES TÉCNICAS DE MONTAJE ELECTROMECÁNICO"],
         "VOLUMEN V": ["SUMINISTRO DE EQUIPOS Y MATERIALES", "MONTAJE ELECTROMECÁNICO", "TRANSPORTE DE MATERIALES", "DESAGREGADO DE GASTOS GENERALES Y UTILIDAD",
                       "ANÁLISIS DE PRECIOS UNITARIOS", "CRONOGRAMA DE EJECUCIÓN DE OBRA (DIAGRAMA GANTT)", "CRONOGRAMA DE SUMINISTRO VALORIZADO",
                       "CALENDARIO VALORIZADO DE OBRA", "FÓRMULA POLINÓMICA DE REAJUSTE", "INVENTARIO FÍSICO POR ESTRUCTURA"],
         "VOLUMEN VI": ["CAPÍTULO II: CÁLCULOS JUSTIFICATIVOS", "ANEXOS 1 AL 9 (hojas de cálculo editables)"],
         "VOLUMEN VII": ["PLANO DE UBICACIÓN", "PLANO DE PLANTA – POLIGONAL", "PLANOS DE PERFIL Y PLANIMETRÍA", "DIAGRAMA UNIFILAR",
                         "DETALLE DE CRUCE Y DISTANCIAS DE SEGURIDAD", "LÁMINAS DE DETALLE (ARMADOS, RETENIDAS, PUESTA A TIERRA, CIMENTACIÓN)"],
         "VOLUMEN VIII": ["INFORME GEOLÓGICO – GEOTÉCNICO DE GABINETE", "TÉRMINOS DE REFERENCIA DEL ESTUDIO DE MECÁNICA DE SUELOS", "DISEÑO DE CIMENTACIONES"],
         "VOLUMEN IX": ["FLUJO DE CARGA", "CORTOCIRCUITO", "COORDINACIÓN DE PROTECCIONES"],
         "VOLUMEN X": ["REQUERIMIENTO MÍNIMO DEL EJECUTOR DE OBRA", "REQUERIMIENTO MÍNIMO DEL SUPERVISOR DE OBRA"],
         "VOLUMEN XI": ["INFORME DE GESTIÓN DE RIESGOS EN LA PLANIFICACIÓN DE LA EJECUCIÓN DE OBRA", "PANEL FOTOGRÁFICO (formato)",
                        "COTIZACIONES DE MATERIALES (cuadro comparativo – pendiente)", "DATOS DE CAMPO Y DOCUMENTOS EXTERNOS PENDIENTES"]}

# ============================================================================ CARÁTULA Y SEPARADORES
d = nuevo("CARÁTULA Y CONTENIDO")
caratula_volumen(d, "ESTUDIO DEFINITIVO", "EXPEDIENTE TÉCNICO")
p(d, "ESTUDIO DEFINITIVO DEL PROYECTO:", bold=True, align="C", size=13)
p(d, f"“{NOMBRE}”", bold=True, align="C", size=13, color=AZUL)
d.add_paragraph()
tabla(d, ["VOLUMEN", "CONTENIDO"], [(v, t.replace("\n", " / ")) for v, t in VOLS], widths=[3.6, 12.0], size=10, titulo="CONTENIDO")
p(d, FECHA_CAR, bold=True, align="C", size=12)
for v, t in VOLS:
    caratula_volumen(d, v, t.replace("\n", " / "), SEPAR.get(v))
d.save(OUT / "00 CARATULA Y SEPARADORES.docx")

# ============================================================================ VOLUMEN I – FICHA TÉCNICA
d = nuevo("VOLUMEN I – FICHA TÉCNICA")
caratula_volumen(d, "VOLUMEN I", "FICHA TÉCNICA")
p(d, "FICHA TÉCNICA", bold=True, align="C", size=14)
h(d, "1. Nombre del proyecto")
p(d, f"“{NOMBRE}”", bold=True)
h(d, "2. Etapa del proyecto")
p(d, "Elaboración del estudio definitivo (expediente técnico de obra).", bold=True)
h(d, "3. Ubicación del proyecto")
datos(d, [("Departamento", PROYECTO["departamento"]), ("Provincias", PROYECTO["provincias"]), ("Distritos", PROYECTO["distritos"]),
          ("Altitud", f"{fmt(el['cota_min'],0)} a {fmt(el['cota_max'],0)} m s.n.m."), ("Coordenadas del punto de inicio", f"E {fmt(E.este.iloc[0])} – N {fmt(E.norte.iloc[0])} ({ZU})"),
          ("Coordenadas del punto final", f"E {fmt(E.este.iloc[-1])} – N {fmt(E.norte.iloc[-1])} ({ZU})")])
h(d, "4. Documento de factibilidad de suministro y fijación del punto de diseño")
datos(d, [("Empresa concesionaria", CONC), ("Factibilidad de suministro y punto de diseño", f"PENDIENTE – a gestionar por la Entidad ante {CONC} (ver Vol. XI)"),
          ("Punto de diseño adoptado en el estudio", f"Red existente en 22,9 kV en {INI} ({E0}), a confirmar")])
h(d, "5. Objetivo del proyecto")
p(d, f"Dotar de una línea primaria trifásica en 22,9 kV entre {INI} y {FINN}{C['txt_der']}, con capacidad para "
     f"atender la máxima demanda proyectada de {fmt(K['dem']['MD_anio20_kW'],0)} kW al año {A20}, con caída de tensión inferior al 5 % y conforme a las normas DGE de "
     "electrificación rural y al Código Nacional de Electricidad – Suministro 2011.")
h(d, "6. Alcances del proyecto")
p(d, f"El proyecto comprende el suministro, transporte, montaje electromecánico, pruebas y puesta en servicio de {fmt(L,3)} km de línea primaria trifásica "
     f"en 22,9 kV con conductor de aleación de aluminio AAAC de 70 mm², desde la estructura de arranque con reconectador ({E0}, {INI}) hasta la "
     f"estructura terminal {EF} ({FINN})"
     + ("" if not DER else ", incluyendo " + lista([f"la estructura de derivación y seccionamiento hacia {x['nombre']} ({x['estructura']}, progresiva {fmt(x['prog'],2)} m)" for x in DER]))
     + ". "
     "No forman parte del alcance las redes primarias y secundarias de las localidades ni las subestaciones de distribución.")
h(d, "7. Descripción técnica del proyecto")
datos(d, [("Sistema", "Trifásico (3ø), 60 Hz, neutro efectivamente puesto a tierra en la fuente"), ("Nivel de tensión", "22,9 kV (tensión máxima 25 kV)"),
          ("Longitud de la línea", f"{fmt(L,3)} km"),
          ("Estructuras", f"Postes de concreto armado centrifugado: 12/300 = {nP.get('12/300',0)} u; 12/400 = {nP.get('12/400',0)} u; 13/400 = {nP.get('13/400',0)} u (total {len(E)})"),
          ("Armados", "; ".join(f"{a} = {n}" for a, n in nA.items())),
          ("Conductor", f"Aleación de aluminio AAAC 70 mm², 19 hilos: {fmt(M['cond_m']/1000,3)} km (3 fases, incluye flecha, puentes y desperdicio)"),
          ("Crucetas", "Perfil angular de FºGº 64 × 64 × 6,4 × 2 400 mm (Tipo I) con riostras 64 × 64 × 6,4 × 1 000 mm"),
          ("Aisladores", f"Porcelana tipo PIN ANSI 56-4 (línea de fuga 685 mm) = {fmt(M['pin'],0)} u; polimérico de suspensión 36 kV (línea de fuga ≥ 720 mm) = {fmt(M['susp'],0)} u"),
          ("Vano promedio / máximo", f"{fmt(K['plan']['vano_medio'],1)} m / {fmt(K['plan']['vano_max'],1)} m"),
          ("Retenidas", f"Inclinadas tipo RI con cable A°G° Siemens-Martin 10 mm: {M['ret']} u"),
          ("Puesta a tierra", f"PAT-1 (una varilla Cu 16 mm × 2,40 m) = {M['pat'].get('PAT-1',0)} u; PAT-2 (dos varillas) = {M['pat'].get('PAT-2',0)} u"),
          ("Equipos de protección y maniobra", f"Reconectador trifásico 38 kV, 170 kV-BIL = 1 u; seccionadores fusibles cut-out 38 kV, 100 A, 170 kV-BIL = {fmt(M['cutout'],0)} u; "
                                               f"pararrayos de óxido metálico 24 kV, 10 kA, clase 1 = {fmt(M['pararrayos'],0)} u"),
          ("Cable de guarda", f"No se requiere (nivel isoceráunico {SIS['isoceraunico']} según RD 018-2003-EM/DGE, Cuadro 6.1; ver Vol. VI)")], ancho=(4.8, 0.4, 10.8), size=10.5)
h(d, "8. Plazo de ejecución")
p(d, f"El plazo de ejecución para el suministro de materiales y el montaje electromecánico es de {PLAZO}.")
h(d, "9. Valor referencial")
datos(d, [("Costo directo", f"S/ {fmt(P['CD'])}"), ("Valor referencial de obra (incluye IGV)", f"S/ {fmt(P['VR'])}"),
          ("Supervisión, coordinación y liquidación (incluye IGV)", f"S/ {fmt(P['SUP']+P['COO']+P['LIQ'])}"), ("Costo total de inversión", f"S/ {fmt(P['TOT'])}"),
          ("Fecha de precios", f"{PROYECTO['fecha']} (precios de suministro con fuente indicada en el Vol. V; deben actualizarse)")])
h(d, "10. Ejecución de obra")
p(d, "Modalidad de ejecución propuesta: contrata, con sistema de contratación a precios unitarios (práctica usual en electrificación rural). La modalidad definitiva será "
     "establecida por la Entidad contratante.")
h(d, "11. Fuente de financiamiento")
p(d, CFG["proyecto"].get("financiamiento", "Por definir por la Entidad contratante."))
h(d, "12. Entidad que licita y administra el contrato")
p(d, f"{PROYECTO['entidad']}. La Entidad contratante coordinará con {CONC} la factibilidad, la supervisión técnica y la recepción de las instalaciones.")
h(d, "13. Proyectista")
p(d, PROY, bold=True)
d.save(OUT / "VOL. I FICHA TECNICA.docx")

# ============================================================================ VOLUMEN II – RESUMEN EJECUTIVO
d = nuevo("VOLUMEN II – RESUMEN EJECUTIVO")
caratula_volumen(d, "VOLUMEN II", "RESUMEN EJECUTIVO")
p(d, "RESUMEN EJECUTIVO", bold=True, align="C", size=14)
h(d, "1. Aspectos generales")
h(d, "1.1 Proyecto", 2); p(d, f"“{NOMBRE}”", bold=True)
h(d, "1.2 Propietario", 2); p(d, f"Entidad contratante: {PROYECTO['entidad']}; empresa concesionaria de la zona: {CONC.rstrip('.')}.")
h(d, "1.3 Ubicación", 2)
datos(d, [("Departamento", PROYECTO["departamento"]), ("Provincias", PROYECTO["provincias"]), ("Distritos", PROYECTO["distritos"]), ("Región natural", txt("region_natural"))])
h(d, "1.4 Antecedentes", 2)
p(d, txt("antecedentes"))
h(d, "1.5 Situación actual", 2)
p(d, txt("situacion_actual") + " La demanda del proyecto se ha estimado con un estudio de mercado basado en el Censo 2017 (INEI).")
h(d, "1.6 Objetivo del proyecto", 2)
p(d, f"Construir una línea primaria trifásica en 22,9 kV de {fmt(L,3)} km, con conductor AAAC 70 mm², que permita atender la máxima demanda proyectada de "
     f"{fmt(K['dem']['MD_anio20_kW'],0)} kW al año {A20} (" + "; ".join([f"{x['nombre']} {fmt(x['P20'],0)} kW" for x in DER] + [f"{FINN} {fmt(C['Pfin'],0)} kW"]) + ") "
     f"con una caída de tensión máxima de {fmt(K['elec']['dV'],2)} % y pérdidas de potencia de {fmt(K['elec']['PJ'],1)} kW.")
h(d, "1.7 Condiciones climatológicas", 2)
p(d, f"Estación de referencia: {CLI_FUENTE}. Temperatura mínima media anual {clima('t_min_media','°C')}, máxima media {clima('t_max_media','°C')} y media "
     f"{clima('t_media','°C')}. Zona de carga {CLIMA.get('zona_carga','(definir)')} del CNE-S 2011: viento de {clima('viento_ms','m/s',1)} a {clima('t_viento','°C',0)} "
     f"y manguito de hielo de {clima('hielo_mm','mm',0)} a 0 °C.")
h(d, "1.8 Topografía y altitud", 2)
p(d, f"Relieve del corredor entre {fmt(el['cota_min'],0)} y {fmt(el['cota_max'],0)} m s.n.m. El perfil de diseño se obtuvo del modelo digital de elevación "
     "Copernicus GLO-30; las cotas deberán confirmarse con el levantamiento topográfico de replanteo.")
h(d, "1.9 Vías de acceso", 2)
p(d, txt("vias_acceso"))
h(d, "2. Descripción del proyecto")
h(d, "2.1 Línea primaria", 2)
tabla(d, ["Característica", "Descripción"], [
    ("Tensión nominal / máxima", "22,9 kV / 25 kV, 60 Hz, trifásico"), ("Longitud", f"{fmt(L,3)} km"),
    ("Punto de inicio", f"{E0} – {INI} (armado PSER-3 con reconectador)")] +
    [("Derivación", f"{x['estructura']} – progresiva {fmt(x['prog'],2)} m, derivación a {x['nombre']} (armado DT-3 con seccionamiento PSEC-3P)") for x in DER] + [
    ("Punto final", f"{EF} – {FINN} (armado terminal PTH-3 con seccionamiento)"),
    ("Conductor", "AAAC 70 mm², 19 hilos; EDS inicial 18 %, final 15 %"), ("Estructuras", f"{len(E)} postes de CAC (12/300, 12/400 y 13/400)"),
    ("Vano medio / máximo / mínimo", f"{fmt(K['plan']['vano_medio'],1)} / {fmt(K['plan']['vano_max'],1)} / {fmt(K['plan']['vano_min'],1)} m")], widths=[5.5, 10.1])
h(d, "2.2 Postes y crucetas", 2)
tabla(d, ["Poste", "Cantidad"], [(f"CAC {k}", v) for k, v in nP.items()] + [("Total", len(E))], widths=[6, 3], bold_last=True)
p(d, "Crucetas de perfil angular FºGº 64 × 64 × 6,4 × 2 400 mm con riostras, según los armados normalizados de la concesionaria (láminas LD-LP del Vol. VII).")
h(d, "2.3 Armados", 2)
tabla(d, ["Armado", "Descripción", "Cant."], [(a, ARM_DESC[a], n) for a, n in nA.items()], widths=[2.2, 11.2, 2.2])
h(d, "2.4 Conductor", 2)
p(d, f"Conductor de aleación de aluminio AAAC de 70 mm²: {fmt(M['cond_m'],0)} m (tres fases, incluye flecha, puentes y 3 % de desperdicio).")
h(d, "2.5 Aisladores", 2)
p(d, f"Aisladores de porcelana tipo PIN clase ANSI 56-4 ({fmt(M['pin'],0)} u) para suspensión y ángulos hasta 30°, y aisladores poliméricos de suspensión de 36 kV "
     f"({fmt(M['susp'],0)} u) para anclajes, ángulos mayores, zonas de arrancamiento y estructuras con equipos.")
h(d, "2.6 Retenidas y anclajes", 2)
p(d, f"{M['ret']} retenidas inclinadas tipo RI con cable de acero grado Siemens-Martin de 10 mm, varilla de anclaje de 16 mm × 2,40 m y bloque de concreto armado "
     "de 0,50 × 0,50 × 0,20 m.")
h(d, "2.7 Puesta a tierra", 2)
p(d, f"PAT-1 (una varilla de cobre de 16 mm × 2,40 m) en {M['pat'].get('PAT-1',0)} estructuras (una de cada tres y las adyacentes a equipos) y PAT-2 (dos varillas) en "
     f"{M['pat'].get('PAT-2',0)} estructuras con equipos, con resistencia máxima de 25 Ω.")
h(d, "2.8 Equipos de protección y maniobra", 2)
p(d, "Reconectador automático trifásico de 38 kV, 170 kV-BIL en el arranque; seccionadores fusibles cut-out de 38 kV, 100 A, 170 kV-BIL y pararrayos de óxido metálico de "
     f"24 kV, 10 kA en " + lista(["el arranque"] + [f"la derivación a {x['nombre']}" for x in DER] + [f"la llegada a {FINN}"]) + ".")
h(d, "3. Presupuesto")
tabla(d, ["Ítem", "Descripción", "S/"], [("A", "Suministro de materiales", fmt(P["SU"])), ("B", "Montaje electromecánico", fmt(P["MO"])), ("C", "Transporte de materiales", fmt(P["TR"])),
                                         ("D", "Costo directo", fmt(P["CD"])), ("E", f"Gastos generales directos ({fmt(P['pGGD']*100,2)} %)", fmt(P["GGD"])),
                                         ("F", f"Gastos generales indirectos ({fmt(P['pGGI']*100,2)} %)", fmt(P["GGI"])), ("G", f"Utilidad ({fmt(ECON.get('utilidad',0.08)*100,0)} %)", fmt(P["UT"])),
                                         ("H", "Sub total", fmt(P["ST"])), ("I", f"IGV ({fmt(ECON.get('igv',0.18)*100,0)} %)", fmt(P["IGV"])), ("J", "Valor referencial de obra", fmt(P["VR"])),
                                         ("K", "Supervisión de obra", fmt(P["SUP"])), ("L", "Coordinación de obra", fmt(P["COO"])), ("M", "Liquidación financiera", fmt(P["LIQ"])),
                                         ("O", "Costo total de inversión", fmt(P["TOT"]))], widths=[1.4, 10.0, 4.2], bold_last=True)
p(d, f"Precios a {PROYECTO['fecha'].lower()}, tipo de cambio S/ {fmt(TC,3)} por US$ ({TC_FUENTE}). Los precios de suministro provienen del catálogo de precios de referencia del repositorio (src/catalogo.py, ajustable en proyecto.yaml → precios) "
     "convertidas al tipo de cambio vigente y de estimados del proyectista; deben actualizarse con un mínimo de tres cotizaciones antes de la convocatoria.", size=10)
h(d, "4. Ejecución de obra por contrato")
p(d, "La obra se ejecutará por contrata, bajo el sistema de precios unitarios propuesto; la Entidad definirá la modalidad final.")
h(d, "5. Fuente de financiamiento")
p(d, CFG["proyecto"].get("financiamiento", "Por definir por la Entidad contratante."))
h(d, "6. Plazo de ejecución")
p(d, PLAZO[0].upper() + PLAZO[1:] + ".")
proyectista(d)
d.save(OUT / "VOL. II RESUMEN EJECUTIVO.docx")

# ============================================================================ VOLUMEN III – MEMORIA DESCRIPTIVA
d = nuevo("VOLUMEN III – MEMORIA DESCRIPTIVA")
caratula_volumen(d, "VOLUMEN III", "MEMORIA DESCRIPTIVA")
p(d, f"“{NOMBRE}”", bold=True, align="C", size=12)
p(d, "MEMORIA DESCRIPTIVA", bold=True, align="C", size=13); p(d, "LÍNEA PRIMARIA", bold=True, align="C", size=12)
h(d, "1. Aspectos generales")
h(d, "1.1 Antecedentes del proyecto", 2)
p(d, txt("antecedentes"))
p(d, "El presente expediente desarrolla el proyecto al nivel de estudio definitivo, siguiendo la organización en once volúmenes, los formatos y los "
     "procedimientos de cálculo de un expediente técnico de línea primaria de electrificación rural (RD 018-2003-EM/DGE), adaptados a las condiciones propias "
     f"del corredor {INI} – {FINN}.")
h(d, "1.2 Objetivo del proyecto", 2)
p(d, f"El objetivo es dotar de una línea primaria trifásica en 22,9 kV con capacidad para la máxima demanda proyectada al año {A20} "
     f"({fmt(K['dem']['MD_anio20_kW'],0)} kW), con una caída de tensión máxima de {fmt(K['elec']['dV'],2)} % (límite 5 %) y cumpliendo las distancias de "
     "seguridad del CNE-S 2011 y las normas DGE de electrificación rural.")
bullets(d, ["Se requiere el suministro, transporte, montaje electromecánico, pruebas y puesta en servicio de la línea primaria.",
            "Se requiere que, previo al montaje, el contratista efectúe el replanteo topográfico y la ingeniería de detalle (verificación del plantillado con cotas de campo)."])
h(d, "1.3 Fuente de información", 2)
bullets(d, CFG.get("fuentes_informacion") or ["Trazado de gabinete sobre la ruta indicada, capas OpenStreetMap del corredor y modelo digital de elevación Copernicus GLO-30.",
            "Instituto Nacional de Estadística e Informática – Censo 2017 (población por distrito).",
            f"Datos climáticos: {CLI_FUENTE}.",
            "Normas DGE (RD 018, 024, 026 y 029-2003-EM/DGE) y Código Nacional de Electricidad – Suministro 2011.",
            f"Tipo de cambio: {TC_FUENTE}.",
            "Convenio CAPECO – FTCCP 2025-2026 (jornales de construcción civil)."])
h(d, "1.4 Descripción del área del proyecto", 2)
h(d, "1.4.1 Ubicación", 3)
tabla(d, ["Punto", "Descripción", "Este (m)", "Norte (m)", "Cota (m s.n.m.)"],
      [(E0, f"Inicio – {INI}", fmt(E.este.iloc[0]), fmt(E.norte.iloc[0]), fmt(E.cota_m.iloc[0], 1))] +
      [(x["estructura"], f"Derivación a {x['nombre']}", *(lambda r_: (fmt(r_.este), fmt(r_.norte), fmt(r_.cota_m, 1)))(E[E.estructura == x["estructura"]].iloc[0])) for x in DER] +
      [(EF, f"Final – {FINN}", fmt(E.este.iloc[-1]), fmt(E.norte.iloc[-1]), fmt(E.cota_m.iloc[-1], 1))], widths=[1.6, 5.4, 3.0, 3.2, 2.4])
p(d, f"Coordenadas {ZU}.", italic=True, size=10)
imagen(d, png_de_pdf(W / "planos2/generales/LP-01_PLANO_DE_UBICACION.pdf", W / "prev" / "lp01.png"), 15.5, "Figura 1: Plano de ubicación (LP-01, Vol. VII)")
h(d, "1.4.2 Condiciones climatológicas", 3)
ZC = f"CNE-S 2011, {CLIMA.get('zona_carga','zona de carga por definir')}"
tabla(d, ["Parámetro", "Valor", "Fuente"], [("Temperatura mínima media anual", clima("t_min_media", "°C"), CLI_FUENTE),
                                            ("Temperatura máxima media anual", clima("t_max_media", "°C"), CLI_FUENTE),
                                            ("Temperatura media (EDS)", clima("t_media", "°C"), CLI_FUENTE), ("Temperatura mínima de diseño", clima("t_min_diseno", "°C"), "Criterio del proyectista"),
                                            ("Velocidad de viento de diseño", f"{clima('viento_ms','m/s')} ({fmt(float(CLIMA['viento_ms'])*3.6,0)} km/h) a {clima('t_viento','°C',0)}", ZC),
                                            ("Manguito de hielo", f"{clima('hielo_mm','mm',0)} a 0 °C; {clima('hielo_comb_mm','mm',0)} + {clima('viento_comb_ms','m/s')}", ZC),
                                            ("Nivel isoceráunico", f"{SIS['isoceraunico']} días de tormenta/año", "RD 018-2003-EM/DGE, Cuadro 6.1")], widths=[5.8, 4.6, 5.2])
h(d, "1.4.3 Topografía – altitud del área del proyecto", 3)
p(d, f"El trazado discurre por terreno llano a ondulado entre las cotas {fmt(el['cota_min'],1)} y {fmt(el['cota_max'],1)} m s.n.m. (altitud de diseño {fmt(ALT,0)} m s.n.m.).")
h(d, "1.4.4 Vías de acceso", 3)
p(d, txt("vias_acceso") + (f" La línea se ubica a unos {fmt(float(TRAZADO.get('desplazamiento_m',0)),0)} m del eje de la vía, lo que facilita el transporte de postes con camión grúa."
                               if TRAZADO.get("ruta_es_via") else ""))
h(d, "1.4.5 Actividad económica y social", 3)
p(d, txt("actividad_economica"))
h(d, "1.5 Localidades beneficiadas", 2)
tabla(d, ["Carga", "Población 2017 (INEI)", f"MD {A0} (kW)", f"MD {A20} (kW)"],
      [(r.carga, fmt(float(C["pob"][r.carga]), 0) if C["pob"].get(r.carga) else "–", fmt(dem[(dem.carga == r.carga) & (dem.anio == A0)].MD_kW.iloc[0], 1), fmt(dem[(dem.carga == r.carga) & (dem.anio == A20)].MD_kW.iloc[0], 1))
       for r in dem[dem.anio == A0].itertuples()], widths=[7.0, 3.2, 2.7, 2.7])
h(d, "2. Alcance del estudio")
p(d, f"El estudio comprende la línea primaria troncal de {fmt(L,3)} km" + ("" if not DER else " y " + lista([f"la estructura de derivación hacia {x['nombre']}" for x in DER])) + ", con su equipamiento de protección, "
     "seccionamiento y puesta a tierra. No incluye las redes primarias y secundarias de las localidades, las subestaciones de distribución, la gestión de "
     "servidumbre ni los estudios de campo (topografía de replanteo, mecánica de suelos, resistividad del terreno, CIRA/Plan de Monitoreo Arqueológico, "
     "instrumento de gestión ambiental), que se listan como pendientes en el Volumen XI.")
h(d, "3. Descripción del proyecto")
h(d, "3.1 Normas aplicables", 2)
bullets(d, ["Ley de Concesiones Eléctricas, D.L. N.° 25844, y su reglamento.", "Ley General de Electrificación Rural, Ley N.° 28749, y su reglamento (D.S. N.° 025-2007-EM).",
            "Código Nacional de Electricidad – Suministro 2011 (R.M. N.° 214-2011-MEM/DM).",
            "R.D. N.° 018-2003-EM/DGE: Bases para el diseño de líneas y redes primarias para electrificación rural.",
            "R.D. N.° 024-2003-EM/DGE: Especificaciones técnicas de soportes normalizados para líneas y redes primarias.",
            "R.D. N.° 026-2003-EM/DGE: Especificaciones técnicas para el suministro de materiales y equipos de líneas y redes primarias.",
            "R.D. N.° 029-2003-EM/DGE: Especificaciones técnicas de montaje de líneas y redes primarias.",
            "Norma Técnica de Calidad de los Servicios Eléctricos Rurales (R.D. N.° 016-2008-EM/DGE).",
            "Reglamento de Seguridad y Salud en el Trabajo con Electricidad (R.M. N.° 111-2013-MEM/DM)."])
h(d, "3.2 Ruta de línea", 2)
if TRAZADO.get("ruta_es_via"):
    _r = (f"La ruta se definió en gabinete sobre el corredor vial ({TRAZADO.get('nombre_via','vía existente')}): el eje de la vía se desplazó "
          f"{fmt(float(TRAZADO.get('desplazamiento_m',0)),0)} m hacia el lado {'derecho' if str(TRAZADO.get('lado','derecha')).lower().startswith('d') else 'izquierdo'} y se simplificó para obtener alineamientos largos, ")
else:
    _r = "La ruta se definió en gabinete sobre el eje propuesto por el proyectista y se simplificó para obtener alineamientos largos, "
p(d, _r + f"eliminando quiebres mayores de {fmt(float(TRAZADO.get('angulo_max_quiebre_deg',60)),0)}°. Los criterios fueron: cercanía a vías para facilitar el "
     "transporte y el mantenimiento, evitar zonas urbanas consolidadas, minimizar cruces de vías y respetar la faja de servidumbre de 11 m (5,5 m a cada lado del eje).")
vt = json.load(open(W / "trazado_meta.json"))
p(d, f"La poligonal resultante tiene {len(vt['angulos'])+2} vértices (cuadro en el plano LP-02); el ángulo de desvío máximo es {fmt(max(vt['angulos']),1)}°.")
h(d, "3.3 Características del equipamiento", 2)
h(d, "3.3.1 Postes", 3)
p(d, "Postes de concreto armado centrifugado (CAC) de 12 m (300 y 400 daN) y 13 m (400 daN), seleccionados por estructura en el plantillado y la verificación "
     "mecánica (Anexo 6). El empotramiento es L/10 + 0,60 m, con cimentación de concreto ciclópeo y solado (Anexo 5).")
h(d, "3.3.2 Conductores", 3)
p(d, "Conductor de aleación de aluminio AAAC de 70 mm² (19 hilos de 2,10 mm, diámetro 10,5 mm, masa 0,181 kg/m, esfuerzo de rotura 295,8 N/mm²), seleccionado "
     "por caída de tensión con 15 % de reserva, capacidad de corriente, cortocircuito y costo total (inversión + pérdidas) frente a las secciones de 25 a 95 mm².")
h(d, "3.3.3 Aisladores", 3)
p(d, f"Porcelana tipo PIN clase ANSI 56-4 (línea de fuga 685 mm) y polimérico de suspensión de 36 kV (línea de fuga ≥ 720 mm), seleccionados para una línea de fuga "
     f"requerida de {fmt(K['aisl']['Lf'],0)} mm ({fmt(LF_MM_KV,0)} mm/kV × {fmt(SIS['Vmax'],0)} kV × factor de altitud {fmt(K['aisl']['fch'],4)}), según el Anexo 1.")
h(d, "3.3.4 Retenidas y anclajes", 3)
p(d, "Retenidas inclinadas a 37° del eje del poste, con cable de acero galvanizado grado Siemens-Martin de 10 mm (7 hilos, rotura 30,92 kN), aislador polimérico de "
     "tracción, varilla de anclaje de 16 mm × 2,40 m y bloque de concreto armado de 0,50 × 0,50 × 0,20 m en excavación de 0,80 × 0,80 × 2,00 m (Anexo 7).")
h(d, "3.3.5 Puesta a tierra", 3)
p(d, f"PAT-1 y PAT-2 con varilla de cobre de 16 mm × 2,40 m, conductor de cobre de 25 mm² y cemento conductivo. Con resistividad supuesta de {fmt(PAT['rho'],0)} Ω·m: "
     f"R(PAT-1) = {fmt(K['pat']['R1'],1)} Ω sin tratamiento y {fmt(K['pat']['R1t'],1)} Ω con tratamiento; R(PAT-2) = {fmt(K['pat']['R2t'],1)} Ω con tratamiento (≤ 25 Ω).")
h(d, "3.3.6 Material de ferretería", 3)
p(d, "Toda la ferretería será de acero forjado o fundido galvanizado en caliente (ASTM A153/A123): crucetas, riostras, abrazaderas, pernos, espigas, tuercas y arandelas.")
h(d, "3.3.7 Equipo de protección", 3)
p(d, f"Reconectador trifásico de 38 kV, 170 kV-BIL, 630 A, 12,5 kA en el arranque ({E0}); seccionadores fusibles cut-out de 38 kV, 100 A, 170 kV-BIL con fusibles tipo K "
     f"({fusibles_txt(C)}); pararrayos de óxido metálico de 24 kV, 10 kA, clase 1 (Anexo 2 y Vol. IX).")
h(d, "4. Criterios de diseño eléctrico")
h(d, "4.1 Regulación de tensión", 2)
p(d, f"Caída de tensión máxima admisible {fmt(SIS['dV_max_pct'],0)} % (RD 018). Resultado al año {A20}: " + lista([f"{fmt(x['dV'],2)} % en la derivación a {x['nombre']}" for x in DER] + [f"{fmt(C['dV_fin'],2)} % en {FINN}"]) + "; "
     f"pérdidas de potencia {fmt(K['elec']['PJ'],1)} kW y de energía {fmt(K['elec']['PE'],1)} MWh/año (Anexo 8).")
h(d, "4.2 Nivel de aislamiento requerido", 2)
p(d, f"Altitud de diseño {fmt(ALT,0)} m s.n.m., factor de corrección {fmt(K['aisl']['fch'],4)}, densidad relativa del aire {fmt(K['aisl']['delta'],4)}. Nivel básico requerido para equipos "
     f"{fmt(K['aisl']['NBIh'],1)} kVp → se adopta 170 kV-BIL (clase 38 kV). Para la línea: Vfi = {fmt(K['aisl']['Vfi'],1)} kV y Vi = {fmt(K['aisl']['Vi'],1)} kVp (Anexo 1).")
h(d, "4.3 Sistema de protección", 2)
p(d, "Reconectador con funciones de sobrecorriente de fase y tierra y recierre en el arranque, seccionadores fusibles en la derivación y la llegada, y pararrayos en "
     "cada punto de seccionamiento. Los ajustes preliminares están en el Vol. IX y serán confirmados con el estudio de coordinación de la obra (partida 1.02).")
h(d, "4.4 Nivel de cortocircuito", 2)
p(d, f"Potencia de cortocircuito de diseño en el punto de diseño: {SIS['Scc_MVA']:.0f} MVA (valor a confirmar con {CONC}). "
     f"La sección mínima por cortocircuito resulta {fmt(el['S_min_cc'],1)} mm² < 70 mm².")
h(d, "4.5 Sistema de puesta a tierra", 2)
p(d, "Puesta a tierra en una de cada tres estructuras y en las adyacentes a equipos (PAT-1), y PAT-2 en las estructuras con equipos con resistencia ≤ 25 Ω. "
     "La resistividad del terreno debe medirse en campo (Anexo 3, tabla de sensibilidad).")
clima_t = lambda t: (fmt(t, 0) + " °C").replace("-", "−")
h(d, "5. Criterios de diseño mecánico")
h(d, "5.1 Cálculo mecánico de conductores", 2)
tabla(d, ["Hipótesis", "Temperatura", "Viento", "Hielo", "Condición"],
      [(k.split(" ",1)[0] + " " + k.split(" ",1)[1], clima_t(v["t"]), (fmt(v["V"],1).replace(",0","") + " m/s") if v["V"] else "0", (fmt(v["hielo"],0) + " mm") if v["hielo"] else "0",
        {"H1": f"{fmt(EDS_INI*100,0)} % UTS", "H2": f"{fmt(EDS_FINAL*100,0)} % UTS (referencia)", "H6": f"Flecha máxima ({clima('t_max_diseno','°C',0)} + 10 °C CREEP)"}.get(k.split()[0], f"≤ {fmt(SIGMA_MAX*100,0)} % UTS"))
       for k, v in HIP.items()], widths=[3.6, 2.4, 2.2, 2.0, 5.4])
p(d, f"El tiro máximo resulta {fmt(K['cmc_maxpct']*100,1)} % del tiro de rotura (Anexo 4).")
h(d, "5.2 Cálculo mecánico de estructuras", 2)
p(d, "Factores de seguridad: postes 2 (carga de trabajo en la punta), cable de retenida 2, crucetas 1,5 (transversal) y 2 (longitudinal y vertical), aisladores PIN 2 "
     f"y poliméricos 2,5. Las {len(E)} estructuras se verificaron una a una con los vanos reales (Anexo 6, hoja VERIF_ESTRUCTURAS: {K['cme']['coherentes']} de {len(E)} conformes).")
h(d, "5.3 Características de las estructuras", 2)
tabla(d, ["Armado", "Descripción", "Lámina"], [(a, ARM_DESC[a], {"PS1-3": "LD-LP-01", "PA1-3": "LD-LP-02", "PA2-3": "LD-LP-03", "TS-3": "LD-LP-14", "PR3-3": "LD-LP-04",
                                                                    "DT-3": "LD-LP-05", "PSER-3": "LD-LP-06", "PTH-3": "LD-LP-07"}[a]) for a in nA],
      widths=[2.2, 11.0, 2.4])
h(d, "6. Servidumbre")
p(d, "Faja de servidumbre de 11 m (5,5 m a cada lado del eje) para líneas de 22,9 kV (CNE-S 2011, Tabla 219). La identificación de propietarios y la gestión de "
     "autorizaciones de paso corresponden a la Entidad y están fuera del alcance de este estudio.")
h(d, "7. Financiamiento")
p(d, CFG["proyecto"].get("financiamiento", "Por definir por la Entidad contratante."))
h(d, "8. Plazo de ejecución")
p(d, PLAZO[0].upper() + PLAZO[1:] + " (cronograma en el Vol. V).")
h(d, "9. Planos y láminas de detalle")
pl = json.load(open(W / "planos2/generales/planos.json")); la = json.load(open(W / "planos2/laminas/laminas.json"))
tabla(d, ["Código", "Descripción", "Formato"], [(c, t, f) for c, t, n, f in pl] + [(c, f"{t} – {s}".strip(" –"), "A4") for c, t, s, n in la], widths=[2.4, 11.4, 1.8], size=8.5)
proyectista(d)
d.save(OUT / "VOL. III MEMORIA DESCRIPTIVA.docx")
print("ok p12")
