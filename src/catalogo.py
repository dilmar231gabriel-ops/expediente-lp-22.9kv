"""Catálogo de suministros, listas de materiales por armado (armados normalizados DGE / concesionarias del sur) y base de precios.
Es común a todos los proyectos. Para un proyecto concreto, los precios se pueden sobrescribir en proyecto.yaml → precios
(código: precio en S/ sin IGV) y el tipo de cambio en proyecto.yaml → economico.

Fuentes de precios (columna FUENTE):
  COT-M  : cotización en US$ (sin IGV) del expediente modelo Ayaviri–Pucará (junio 2022), convertida con el
           tipo de cambio venta SBS/BCRP del 07-10-2026 (TC = 3,453). DEBEN ACTUALIZARSE con cotizaciones vigentes.
  COT-MS : precio en S/ del expediente modelo (2022), sin IGV. Actualizar.
  EST    : estimado del proyectista (no existe ítem equivalente en el modelo). Reemplazar por cotización.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from params import ECON, CFG
TC = float(ECON.get("tipo_cambio", 3.453))            # S/ por US$
TC_FUENTE = ECON.get("tipo_cambio_fuente", "BCRP – tipo de cambio SBS venta")
PRECIOS_PROYECTO = {str(k): float(v) for k, v in (CFG.get("precios") or {}).items()}

# (código, descripción, unidad, precio_USD o None, precio_S/ o None, fuente, grupo FP)
MAT = [
    # 1 POSTES
    ("1.01", "Poste de C.A.C. 12/300/150/330 daN (incluye perilla)", "u", None, 1091.53, "EST", "PC"),
    ("1.02", "Poste de C.A.C. 12/400/160/340 daN (incluye perilla)", "u", None, 1247.46, "EST", "PC"),
    ("1.03", "Poste de C.A.C. 13/400/180/375 daN (incluye perilla)", "u", None, 1355.93, "COT-MS", "PC"),
    # 2 AISLADORES Y ACCESORIOS
    ("2.01", "Aislador de porcelana tipo PIN, clase ANSI 56-4 (línea de fuga 685 mm)", "u", 31.36, None, "COT-M", "AI"),
    ("2.02", "Espiga de AºGº de 609 mm de longitud, para cabeza de poste y aislador ANSI 56-4", "u", 7.28, None, "COT-M", "AI"),
    ("2.03", "Espiga de AºGº para cruceta y aislador ANSI 56-4, de 381 mm de longitud, con accesorios", "u", 9.97, None, "COT-M", "AI"),
    ("2.04", "Aislador polimérico tipo suspensión 36 kV, conexión horquilla-lengüeta (línea de fuga ≥ 720 mm)", "u", 16.24, None, "COT-M", "AI"),
    ("2.05", "Grillete de AºGº tipo lira de 16 mm Ø, con pasador de seguridad", "u", 2.58, None, "COT-M", "AI"),
    # 3 CONDUCTOR
    ("3.01", "Conductor de aleación de aluminio AAAC de 70 mm², 19 hilos", "m", 1.1487, None, "COT-M", "CO"),
    # 4 ACCESORIOS DEL CONDUCTOR
    ("4.01", "Varilla de armar preformada simple para conductor AAAC de 70 mm²", "u", 3.47, None, "COT-M", "CO"),
    ("4.02", "Grapa de anclaje tipo pistola de 3 pernos para conductor AAAC 35–70 mm²", "u", 7.84, None, "COT-M", "CO"),
    ("4.03", "Cinta plana de armar de aluminio", "m", 0.25, None, "COT-M", "CO"),
    ("4.04", "Alambre de amarre de aluminio de 16 mm²", "m", 0.28, None, "COT-M", "CO"),
    ("4.05", "Conector doble vía Al/Al para conductor 35–70 mm², tres pernos", "u", 1.34, None, "COT-M", "CO"),
    ("4.06", "Conector bimetálico Al/Cu para conexión de equipos", "u", None, 19.00, "COT-MS", "CO"),
    ("4.07", "Manguito de empalme a compresión para conductor AAAC 70 mm²", "u", None, 40.00, "EST", "CO"),
    # 5 CONDUCTOR DE COBRE
    ("5.01", "Conductor de cobre recocido cableado de 25 mm², para puesta a tierra", "m", 2.6242, None, "COT-M", "CC"),
    # 6 FERRETERÍA PARA POSTES Y CRUCETAS
    ("6.01", "Cruceta de perfil angular FºGº de 64 x 64 x 2400 mm, E = 6,4 mm, con 02 dados. TIPO I", "u", 45.58, None, "COT-M", "FE"),
    ("6.02", "Riostra de perfil angular FºGº de 64 x 64 x 1000 mm, E = 6,4 mm", "u", 15.03, None, "COT-M", "FE"),
    ("6.03", "Abrazadera tipo CAS simple de 75 mm, E = 6,4 mm, D = 206 mm", "u", 11.42, None, "COT-M", "FE"),
    ("6.04", "Abrazadera tipo CAS doble de 75 mm, E = 6,4 mm, D = 206 mm", "u", 11.87, None, "COT-M", "FE"),
    ("6.05", "Abrazadera partida para cruceta de 75 mm, E = 6,4 mm, D = 196 mm, c/2P/2T/2C/4A/2AP", "u", 7.39, None, "COT-M", "FE"),
    ("6.06", "Perno maquinado de AºGº L = 50 mm, D = 13 mm, c/T/C/2A/AP", "u", 0.39, None, "COT-M", "FE"),
    ("6.07", "Perno de AºGº de 16 mm Ø x 254 mm, con tuerca y contratuerca", "u", 1.57, None, "COT-M", "FE"),
    ("6.08", "Perno de doble armado de AºGº de 16 mm Ø x 508 mm, c/4 tuercas y arandelas", "u", 3.75, None, "COT-M", "FE"),
    ("6.09", "Perno ojo de AºGº de 16 mm Ø x 254 mm, con tuerca y contratuerca", "u", 2.58, None, "COT-M", "FE"),
    ("6.10", "Tuerca ojo de AºGº para perno de 16 mm Ø", "u", 2.07, None, "COT-M", "FE"),
    ("6.11", "Arandela cuadrada plana de AºGº 57 x 57 x 5 mm, agujero 18 mm Ø", "u", 0.30, None, "COT-M", "FE"),
    ("6.12", "Soporte metálico de FºGº para montaje de reconectador en poste, con accesorios", "u", None, 1200.00, "EST", "FE"),
    # 7 RETENIDAS Y ANCLAJES
    ("7.01", "Cable de acero de 10 mm Ø, 7 hilos, grado Siemens-Martin", "m", 0.9744, None, "COT-M", "RA"),
    ("7.02", "Varilla de anclaje de AºGº de 16 mm Ø x 2,40 m, con ojal guardacabo, tuerca y contratuerca", "u", 9.184, None, "COT-M", "RA"),
    ("7.03", "Grapa paralela de doble vía de FºGº de tres pernos", "u", 3.10, None, "COT-M", "RA"),
    ("7.04", "Abrazadera de FºGº 185 mm Ø x 64 mm x 6,4 mm, tipo partida, c/3 pernos 16 mm Ø", "u", 9.1504, None, "COT-M", "RA"),
    ("7.05", "Aislador polimérico de tracción para retenida 36 kV", "u", 16.24, None, "COT-M", "RA"),
    ("7.06", "Arandela de anclaje cuadrada plana de FºGº 102 x 102 x 6,4 mm, agujero 20 mm", "u", 1.1424, None, "COT-M", "RA"),
    ("7.07", "Guardacabo de FºGº de 16 mm para cable de 10 mm", "u", 0.448, None, "COT-M", "RA"),
    ("7.08", "Guardacable de FºGº de 1,80 mm x 2,40 m, incluye accesorios de fijación", "u", 9.968, None, "COT-M", "RA"),
    ("7.09", "Bloque de concreto armado 0,50 x 0,50 x 0,20 m", "u", None, 30.00, "COT-MS", "RA"),
    ("7.10", "Alambre galvanizado de entorche N.° 14 para amarre", "m", 0.0896, None, "COT-M", "RA"),
    # 8 PUESTA A TIERRA
    ("8.01", "Varilla de cobre de 16 mm Ø x 2,40 m, con rosca al final de 100 mm", "u", 76.16, None, "COT-M", "PT"),
    ("8.02", "Plancha doblada de cobre para toma a tierra de espigas y/o pernos", "u", 2.46, None, "COT-M", "PT"),
    ("8.03", "Conector de bronce para electrodo de 16 mm Ø y conductor de cobre de 25 mm²", "u", 1.68, None, "COT-M", "PT"),
    ("8.04", "Conector de cobre tipo perno partido para conductor de cobre de 25 mm²", "u", 1.57, None, "COT-M", "PT"),
    ("8.05", "Caja de registro de concreto para puesta a tierra 0,40 x 0,40 x 0,20 m", "u", None, 38.14, "COT-MS", "PT"),
    ("8.06", "Cemento conductivo (dosis de 25 kg)", "u", 15.68, None, "COT-M", "PT"),
    ("8.07", "Tubo de PVC SAP de 19 mm Ø x 0,50 m, con curva de 90°", "u", 0.90, None, "COT-M", "PT"),
    ("8.08", "Tierra negra de cultivo, cernida", "m3", None, 65.00, "COT-MS", "PT"),
    # 9 EQUIPOS DE PROTECCIÓN Y MANIOBRA
    ("9.01", "Seccionador fusible unipolar tipo expulsión (cut-out) de 38 kV, 100 A, 170 kV-BIL", "u", 104.61, None, "COT-M", "PR"),
    ("9.02", "Fusible tipo expulsión tipo K para derivaciones (calibre según Vol. IX)", "u", 1.46, None, "COT-M", "PR"),
    ("9.03", "Fusible tipo expulsión tipo K para la llegada / estructura terminal (calibre según Vol. IX)", "u", None, 25.00, "EST", "PR"),
    ("9.06", "Fusible tipo expulsión tipo K para el seccionamiento del reconectador (calibre según Vol. IX)", "u", None, 28.00, "EST", "PR"),
    ("9.04", "Pararrayos de óxido metálico 24 kV, 10 kA, clase 1, MCOV 19,5 kV, línea de fuga ≥ 780 mm", "u", 69.10, None, "COT-M", "PR"),
    ("9.05", "Reconectador automático trifásico 38 kV, 170 kV-BIL, 630 A, 12,5 kA, con control electrónico y TT auxiliar", "u", None, 110000.00, "EST", "PR"),
    # 10 SEÑALIZACIÓN
    ("10.01", "Placa de numeración de estructura y señal de riesgo eléctrico (juego)", "u", None, 25.00, "EST", "FE"),
]
GRUPOS = [("1", "POSTES DE CONCRETO ARMADO CENTRIFUGADO"), ("2", "CONJUNTO DE AISLADORES Y ACCESORIOS"),
          ("3", "CONDUCTOR DE ALEACIÓN DE ALUMINIO"), ("4", "ACCESORIOS DEL CONDUCTOR DE ALEACIÓN DE ALUMINIO"),
          ("5", "CONDUCTOR DE COBRE"), ("6", "MATERIAL DE FERRETERÍA PARA POSTES Y CRUCETAS"),
          ("7", "RETENIDAS Y ANCLAJES"), ("8", "MATERIAL PARA PUESTA A TIERRA"),
          ("9", "EQUIPO DE PROTECCIÓN Y MANIOBRA"), ("10", "SEÑALIZACIÓN")]
MATD = {m[0]: m for m in MAT}
def precio(cod):
    if cod in PRECIOS_PROYECTO: return PRECIOS_PROYECTO[cod]
    m = MATD[cod]
    return round(m[3] * TC, 2) if m[3] is not None else m[4]

ARMADOS = ["PS1-3", "PA1-3", "PA2-3", "TS-3", "PR3-3", "DT-3", "PSER-3", "PTH-3"]
ARM_DESC = {
    "PS1-3": "Soporte de suspensión 0°–5°, trifásico sin neutro",
    "PA1-3": "Soporte de ángulo 5°–30°, trifásico sin neutro",
    "PA2-3": "Soporte de ángulo 30°–60°, trifásico sin neutro",
    "TS-3": "Soporte de retención/suspensión (doble anclaje con puente), trifásico sin neutro – zonas de arrancamiento",
    "PR3-3": "Soporte de retención o anclaje, trifásico sin neutro",
    "DT-3": "Soporte de derivación tensada trifásica, con seccionamiento PSEC-3P (cut-out + pararrayos)",
    "PSER-3": "Armado con reconectador, cut-out y pararrayos (arranque, punto de diseño)",
    "PTH-3": "Soporte terminal horizontal trifásico, con cut-out y pararrayos (llegada)",
}
ARM_LAMINA = {"PS1-3": "LD-LP-01", "PA1-3": "LD-LP-02", "PA2-3": "LD-LP-03", "TS-3": "LD-LP-14", "PR3-3": "LD-LP-04",
              "DT-3": "LD-LP-05", "PSER-3": "LD-LP-06", "PTH-3": "LD-LP-07"}
_TENSION = {"6.01": 2, "6.02": 4, "6.04": 1, "6.08": 4, "6.06": 4, "6.11": 16}
BOM = {   # cantidades por armado (sin poste, retenida ni puesta a tierra)
    "PS1-3": {"6.01": 1, "6.02": 2, "6.03": 1, "6.05": 1, "6.06": 2, "6.07": 2, "6.11": 2,
              "2.01": 3, "2.02": 1, "2.03": 2, "4.01": 3, "4.04": 7.2},
    "PA1-3": {**_TENSION, "2.01": 5, "2.02": 1, "2.03": 4, "4.01": 5, "4.04": 12.0},
    "PA2-3": {**_TENSION, "6.10": 6, "6.09": 1, "6.07": 2, "2.04": 6, "2.05": 6, "4.02": 6,
              "2.01": 1, "2.02": 1, "4.04": 2.4, "4.03": 1.0, "4.05": 3},
    "TS-3": {**_TENSION, "6.10": 6, "6.09": 1, "6.07": 2, "2.04": 6, "2.05": 6, "4.02": 6,
             "2.01": 1, "2.02": 1, "4.04": 2.4, "4.03": 1.0, "4.05": 3},
    "PR3-3": {**_TENSION, "6.10": 6, "6.09": 1, "6.07": 2, "2.04": 6, "2.05": 6, "4.02": 6,
              "2.01": 1, "2.02": 1, "4.04": 2.4, "4.03": 1.0, "4.05": 3},
    "DT-3": {**_TENSION, "6.01": 3, "6.02": 5, "6.11": 18, "6.10": 3, "6.09": 1, "6.07": 2,
             "2.01": 3, "2.02": 1, "2.03": 2, "4.01": 3, "4.04": 7.2,
             "2.04": 3, "2.05": 3, "4.02": 3, "4.05": 6, "4.06": 3, "9.01": 3, "9.02": 3, "9.04": 3},
    "PSER-3": {**_TENSION, "6.01": 3, "6.02": 5, "6.12": 1, "6.10": 3, "6.09": 1, "6.07": 2,
               "2.04": 3, "2.05": 3, "4.02": 3, "4.05": 6, "4.06": 6, "9.01": 3, "9.06": 3, "9.04": 3, "9.05": 1},
    "PTH-3": {**_TENSION, "6.01": 3, "6.02": 5, "6.10": 3, "6.09": 1, "6.07": 2,
              "2.04": 3, "2.05": 3, "4.02": 3, "4.05": 3, "4.06": 3, "9.01": 3, "9.03": 3, "9.04": 3},
}
PUENTE_M = {"PA2-3": 6, "TS-3": 6, "PR3-3": 6, "DT-3": 12, "PSER-3": 15, "PTH-3": 9}   # m de AAAC para puentes y bajadas a equipos
COMUN = {"10.01": 1}
RET_RI = {"7.02": 1, "7.03": 2, "7.04": 1, "7.05": 1, "7.06": 1, "7.07": 2, "7.08": 1, "7.09": 1, "7.10": 1.5}
def cable_ret(poste_L):   # m de cable SM por retenida: altura de amarre / cos(37°) + 2 m (amarres)
    import math
    h = poste_L - (poste_L / 10 + 0.6) - 0.6
    return round(h / math.cos(math.radians(37)) + 2.0, 1)
PAT_KIT = {"PAT-1": {"8.01": 1, "5.01": 15, "8.02": 2, "8.03": 1, "8.04": 1, "8.05": 1, "8.06": 1, "8.07": 1, "8.08": 1.3},
           "PAT-2": {"8.01": 2, "5.01": 22, "8.02": 2, "8.03": 2, "8.04": 2, "8.05": 2, "8.06": 2, "8.07": 1, "8.08": 2.6}}
DESPERDICIO_COND = 0.03   # flecha, puentes de vano y desperdicio (modelo ≈ 3,4 %)

# --- Base de precios: mano de obra (S/ por h-h) ---
JORNAL_CAPECO = {"Operario": 89.30, "Oficial": 69.75, "Peón": 62.80}   # jornal básico convenio CAPECO–FTCCP 2025-2026
FACTOR_HH = 2.20                                                       # SUPUESTO: leyes sociales y beneficios sobre jornal básico
MO = {  # descripción: (precio S/ h-h, fuente)
    "Ingeniero especialista en Líneas Primarias": (46.82, "Modelo BP 2022"),
    "Ingeniero residente / supervisor de campo": (37.62, "Modelo BP 2022"),
    "Topógrafo operador de estación total": (25.53, "Modelo BP 2022"),
    "Técnico especialista en dibujo por computadora": (20.50, "Modelo BP 2022"),
    "Especialista en estudios de coordinación y protección": (50.50, "Modelo BP 2022"),
    "Especialista ambiental": (46.82, "Modelo BP 2022"),
    "Arqueólogo": (37.62, "Modelo BP 2022"),
    "Capataz": (29.85, "Modelo BP 2022"),
    "Operario": (round(89.30 * FACTOR_HH / 8, 2), "CAPECO 2025-26 x 2,20 / 8"),
    "Oficial": (round(69.75 * FACTOR_HH / 8, 2), "CAPECO 2025-26 x 2,20 / 8"),
    "Peón": (round(62.80 * FACTOR_HH / 8, 2), "CAPECO 2025-26 x 2,20 / 8"),
}
EQ = {  # descripción: (S/ h-m, fuente)
    "Camión grúa de 6 t": (104.01, "ELSE ACU 2021"), "Camioneta rural 4x4": (80.59, "ELSE ACU 2021"),
    "Camión de 4 t": (85.00, "EST"), "Winche de 3 t": (29.82, "ELSE ACU 2021"), "Freno hidráulico": (22.10, "ELSE ACU 2021"),
    "Caballete porta bobina": (15.30, "ELSE ACU 2021"), "Juego de poleas": (2.35, "ELSE ACU 2021"),
    "Dinamómetro": (5.00, "ELSE ACU 2021"), "Equipo de comunicación (par)": (6.25, "ELSE ACU 2021"),
    "Tirfor de 3 t": (2.89, "ELSE ACU 2021"), "Escalera de tres cuerpos": (3.52, "ELSE ACU 2021"),
    "Estación total y accesorios (incluye GPS)": (26.50, "Modelo BP 2022"), "Telurómetro": (6.25, "ELSE ACU 2021"),
    "Megóhmetro": (6.25, "ELSE ACU 2021"), "Mezcladora de concreto 9 p3": (18.00, "EST"),
    "Compactador vibratorio tipo plancha": (12.00, "EST"), "Equipo de cómputo y plotter": (7.00, "ELSE ACU 2021"),
}
MATMON = {  # materiales de montaje: descripción: (unidad, S/, fuente)
    "Cemento Portland tipo I (bolsa 42,5 kg)": ("bls", 31.00, "EST"), "Hormigón": ("m3", 70.00, "EST"),
    "Piedra mediana": ("m3", 65.00, "EST"), "Agua": ("m3", 8.00, "EST"),
    "Estacas, yeso, pintura y materiales de replanteo": ("glb", 1.00, "EST"),
    "Gigantografía y bastidor de madera para cartel de obra 3,60 x 2,40 m": ("u", 950.00, "EST"),
}
UTILIDAD_PCT = float(ECON.get("utilidad", 0.08)); IGV_PCT = float(ECON.get("igv", 0.18)); TRANSPORTE_PCT = float(ECON.get("transporte_pct", 0.07))
