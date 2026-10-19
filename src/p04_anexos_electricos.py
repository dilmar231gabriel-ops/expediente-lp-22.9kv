"""Anexos 1, 2, 3 y 8 de los Cálculos Justificativos (formato del modelo Ayaviri–Pucará), con fórmulas vivas.
Uso: python p04_anexos_electricos.py WORK OUTDIR"""
import json, math, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from params import *
from xlhelp import *

W = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
R = json.load(open(W / "resultados.json"))
el = R["electrico"] if isinstance(R["electrico"], dict) else eval(R["electrico"])
ALT = math.ceil(el["cota_max"] / 100) * 100          # altitud de diseño (m s.n.m.), cota máxima redondeada
T_AMB = T_MEDIA

# =====================================================================================  ANEXO 1
wb = libro()
ws = hoja(wb, "SEL_AISL_22,9KV", [44, 12, 13, 13, 13, 13, 13, 28])
r = cab(ws, "ANEXO 1: SELECCIÓN DEL NIVEL DE AISLAMIENTO Y DE AISLADORES PARA LÍNEAS PRIMARIAS EN 22,9 kV")
titulo_seccion(ws, r, "CONDICIONES DE OPERACIÓN DEL SISTEMA ELÉCTRICO"); r += 1
fila(ws, r, ["Descripción", "Símbolo", "Valor", "Unidad", "Fuente / observación"], font=FB, fill=AZ); ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=8); r += 1
def d(desc, sim, val, uni, fte, fmt=None, entrada=True):
    global r
    ref = dato(ws, r, desc, sim, val, uni, fte, fmt=fmt, entrada=entrada)
    ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=8); r += 1
    return ref
Vn = d("Tensión nominal del sistema entre fases", "Vn", SIS["Vn"], "kV", "RD 018-2003-EM/DGE, 6.1")
Um = d("Tensión máxima del sistema entre fases", "Um", SIS["Vmax"], "kV", "RD 018-2003-EM/DGE, 6.1")
H = d("Altitud de diseño (cota máxima del trazado redondeada)", "h", ALT, "m s.n.m.", f"Perfil DEM: cota máx. {el['cota_max']:.1f} m")
TA = d("Temperatura ambiente media", "t", T_AMB, "°C", CLIMA.get("estacion", "SENAMHI"))
LF0 = d("Línea de fuga específica mínima (contaminación media, clase II)", "Lf0", LF_MM_KV, "mm/kV", "IEC 60815 (proyecto.yaml → diseno.linea_fuga_mm_kV)")
FS_ = d("Factor de sobretensión a frecuencia industrial", "fs", 1.5, "p.u.", "Modelo / RD 018")
HUM = d("Factor por humedad", "H", 1.0, "–", "Modelo")
NN = d("Número de desviaciones estándar (frecuencia industrial)", "N", 3, "–", "Modelo")
SG = d("Desviación estándar (frecuencia industrial)", "σ", 0.02, "p.u.", "Modelo", fmt="0.0%")
FL = d("Factor por lluvia", "fl", 0.8, "–", "Modelo")
NBI0 = d("Nivel básico de aislamiento normalizado a nivel del mar (Um = 25 kV)", "NBI", 125, "kVp", "IEC 60071-1, Tabla 2 / RD 018")
N2 = d("Número de desviaciones estándar (impulso)", "N'", 1.2, "–", "Modelo (Anexo 2)")
SG2 = d("Desviación estándar (impulso)", "σ'", 0.03, "p.u.", "Modelo (Anexo 2)", fmt="0.0%")
r += 1
titulo_seccion(ws, r, "1. FACTORES DE CORRECCIÓN POR ALTITUD"); r += 1
FCH = d("Factor de corrección por altitud  fch = 1 + 1,25·(h − 1000)·10⁻⁴", "fch", f"=1+1.25*({H}-1000)/10000", "–", "RD 018-2003-EM/DGE", fmt="0.0000", entrada=False)
LB = d("Presión barométrica  log b = log 76 − h/18 336", "b", f"=10^(LOG10(76)-{H}/18336)", "cm Hg", "Ecuación de Halley", fmt="0.00", entrada=False)
DEL = d("Densidad relativa del aire  δ = 3,92·b / (273 + t)", "δ", f"=3.92*{LB}/(273+{TA})", "–", "IEC 60060-1", fmt="0.0000", entrada=False)
r += 1
titulo_seccion(ws, r, "2. CRITERIOS PARA LA SELECCIÓN DE AISLADORES"); r += 1
titulo_seccion(ws, r, "A) Aislamiento necesario por contaminación ambiental:  Lf = Lf0 · Um · fch", fill=None); r += 1
LFR = d("Longitud de línea de fuga fase–tierra requerida", "Lf", f"={LF0}*{Um}*{FCH}", "mm", "", fmt="0.0", entrada=False)
titulo_seccion(ws, r, "B) Aislamiento necesario por sobretensión a frecuencia industrial (lluvia):  Vfi = fs·H·(Um/√3) / [(1 − N·σ)·δ·fl]", fill=None); r += 1
VFI = d("Tensión de sostenimiento a frecuencia industrial bajo lluvia requerida", "Vfi", f"={FS_}*{HUM}*({Um}/SQRT(3))/((1-{NN}*{SG})*{DEL}*{FL})", "kV", "", fmt="0.0", entrada=False)
titulo_seccion(ws, r, "C) Aislamiento necesario por sobretensiones atmosféricas:  Vi = NBI / [(1 − N'·σ')·δ]", fill=None); r += 1
VI = d("Tensión crítica de flameo al impulso requerida", "Vi", f"={NBI0}/((1-{N2}*{SG2})*{DEL})", "kVp", "", fmt="0.0", entrada=False)
NBIA = d("Nivel básico de aislamiento requerido para equipos a la altitud de diseño (NBI·fch)", "NBIh", f"={NBI0}*{FCH}", "kVp", "Se adopta equipo de 170 kV-BIL (clase 38 kV)", fmt="0.0", entrada=False)
VFC = d("Tensión de sostenimiento a frecuencia industrial requerida para equipos (50 kV·fch)", "Vfc", f"=50*{FCH}", "kV", "Se adopta equipo de 70 kV (clase 38 kV)", fmt="0.0", entrada=False)
r += 1
titulo_seccion(ws, r, "3. CUADRO COMPARATIVO DE AISLADORES (valores de catálogo en hoja DAT_AISL_BIL)"); r += 1
fila(ws, r, ["Característica", "Unid.", "Calculado", "PIN 56-3", "PIN 56-4", "PIN 56-5", "Polimérico susp. 36 kV", "Selección"], font=FB, fill=AZ); r += 1
rows_cmp = [("Longitud de línea de fuga (Lf)", "mm", LFR, 5), ("Flameo bajo lluvia a frecuencia industrial (Vfi)", "kV", VFI, 7), ("Tensión crítica de flameo al impulso (Vi)", "kVp", VI, 8)]
for desc, u, ref, frow in rows_cmp:
    vals = [desc, u, f"={ref}"] + [f"=DAT_AISL_BIL!{c}{frow}" for c in "DEFG"]
    vals.append(f'=IF(AND(E{r}>=C{r},G{r}>=C{r}),"CUMPLE 56-4 y polimérico","REVISAR")')
    fila(ws, r, vals, fmts=[None, None, "0.0", "0", "0", "0", "0", None]); r += 1
r += 1
nota(ws, r, "Conclusión: se seleccionan aisladores de porcelana tipo PIN clase ANSI 56-4 para armados de suspensión y ángulo "
     "(PS1-3, PA1-3) y aisladores poliméricos de suspensión de 36 kV (línea de fuga ≥ 720 mm, BIL ≥ 170 kV) para armados de "
     "anclaje, ángulo fuerte, derivación y terminal (PA2-3, PR3-3, DT-3, PSER-3, PTH-3). Los equipos (seccionadores, reconectador) "
     "serán de clase 38 kV con NBI 170 kV y línea de fuga ≥ Lf calculada.", h=55)
# ----- hoja de datos de aisladores
w2 = hoja(wb, "DAT_AISL_BIL", [40, 12, 12, 12, 12, 12, 16])
rr = cab(w2, "CARACTERÍSTICAS DE LOS AISLADORES (valores de catálogo – ANSI C29.6 / especificación técnica)", ncol=7)
fila(w2, rr, ["Característica", "Unid.", "", "PIN 56-3", "PIN 56-4", "PIN 56-5", "Polimérico 36 kV (mín. EETT)"], font=FB, fill=AZ)
w2.cell(rr, 3).value = None
data = [("Línea de fuga", "mm", 533, 685, 760, 720), ("Flameo en seco a frec. industrial", "kV", 125, 140, 150, 150),
        ("Flameo bajo lluvia a frec. industrial", "kV", 80, 95, 100, 100), ("Flameo crítico al impulso positivo", "kVp", 200, 225, 255, 250),
        ("Flameo crítico al impulso negativo", "kVp", 265, 310, 340, 250), ("Resistencia mecánica en voladizo", "kN", 13.3, 13.3, 13.3, None),
        ("Carga mecánica especificada (SML)", "kN", None, None, None, 70)]
for k, (a, u, x, y, z, p) in enumerate(data):
    fila(w2, rr + 1 + k, [a, u, None, x, y, z, p])
# las referencias del cuadro comparativo usan filas 6..9 => reubicar a filas fijas
nota(w2, rr + 9, "Fuente: valores típicos de catálogo para porcelana clase ANSI C29.6 56-x; para el aislador polimérico se indican los "
     "mínimos exigidos en las Especificaciones Técnicas de Suministro (Vol. IV). El postor acreditará los valores con protocolos de prueba.", ncol=7, h=40)
assert rr == 4
wb.save(OUT / "Anexo 1 SELECCION DE AISLADORES.xlsx")

# =====================================================================================  ANEXO 2
wb = libro()
ws = hoja(wb, "Seleccion Pararrayos", [46, 10, 12, 12, 12, 12, 12, 26])
r = cab(ws, "ANEXO 2: ESTUDIO DE COORDINACIÓN DE AISLAMIENTO – SELECCIÓN DE PARARRAYOS")
titulo_seccion(ws, r, "DATOS DEL SISTEMA"); r += 1
fila(ws, r, ["Descripción", "Símbolo", "Valor", "Unidad", "Fuente / observación"], font=FB, fill=AZ); ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=8); r += 1
Vn = d("Tensión nominal del sistema", "Vn", SIS["Vn"], "kV", "RD 018-2003-EM/DGE")
Um = d("Tensión máxima del sistema", "Um", SIS["Vmax"], "kV", "RD 018-2003-EM/DGE")
FT_ = d("Factor de mayor variación de tensión", "Ft", 1.05, "p.u.", "Modelo")
CE = d("Factor de falla a tierra (sistema con neutro efectivamente puesto a tierra)", "Ce", 1.4, "p.u.", f"IEC 60099-5; confirmar con {PROYECTO['concesionaria']}")
TT = d("Capacidad TOV del pararrayo para 10 s (TOV = T·MCOV)", "T", 1.3, "p.u.", "Curva TOV de catálogo (10 s)")
H = d("Altitud de diseño", "h", ALT, "m s.n.m.", "")
FCH = d("Factor de corrección por altitud", "fch", f"=1+1.25*({H}-1000)/10000", "–", "RD 018", fmt="0.0000", entrada=False)
BIL = d("NBI de los equipos protegidos (cut-out / reconectador, clase 38 kV)", "BIL", 170, "kVp", "Anexo 1")
BILh = d("NBI efectivo de los equipos a la altitud de instalación (BIL/fch)", "BILh", f"={BIL}/{FCH}", "kVp", "Aislamiento externo corregido", fmt="0.0", entrada=False)
UR = d("Tensión nominal del pararrayo seleccionado", "Ur", 24, "kV", "Elegir de la tabla CATALOGO (hoja)")
LFR2 = d("Línea de fuga específica (Anexo 1)", "Lf0", LF_MM_KV, "mm/kV", "Anexo 1")
r += 1
titulo_seccion(ws, r, "a) Máxima tensión de operación continua requerida:  MCOV ≥ Ft·Vn/√3"); r += 1
MCOVr = d("MCOV requerido", "MCOVr", f"={FT_}*{Vn}/SQRT(3)", "kV", "", fmt="0.00", entrada=False)
MCOV = d("MCOV del pararrayo seleccionado (catálogo)", "MCOV", f"=VLOOKUP({UR},CATALOGO!$A$6:$O$20,2,0)", "kV", "", fmt="0.00", entrada=False)
d("Verificación MCOV ≥ MCOVr", "", f'=IF({MCOV}>={MCOVr},"CUMPLE","NO CUMPLE")', "", "", entrada=False)
titulo_seccion(ws, r, "b) Verificación de sobretensión temporal (falla fase–tierra, 10 s):  TOVpr = T·MCOV  ≥  TOVsist = Ce·Um/√3"); r += 1
TOVS = d("TOV del sistema", "TOVs", f"={CE}*{Um}/SQRT(3)", "kV", "", fmt="0.00", entrada=False)
TOVP = d("TOV del pararrayo", "TOVp", f"={TT}*{MCOV}", "kV", "", fmt="0.00", entrada=False)
d("Verificación TOVp ≥ TOVs", "", f'=IF({TOVP}>={TOVS},"CUMPLE","NO CUMPLE")', "", "", entrada=False)
titulo_seccion(ws, r, "c) Niveles de protección del pararrayo (10 kA, catálogo)"); r += 1
NPFO = d("Nivel de protección para frente de onda (0,5 μs, 10 kA)", "NPFO", f"=VLOOKUP({UR},CATALOGO!$A$6:$O$20,4,0)", "kVp", "", fmt="0.0", entrada=False)
NPIA = d("Nivel de protección al impulso atmosférico (8/20 μs, 10 kA)", "NPIA", f"=VLOOKUP({UR},CATALOGO!$A$6:$O$20,8,0)", "kVp", "", fmt="0.0", entrada=False)
NPIM = d("Nivel de protección al impulso de maniobra (500 A)", "NPIM", f"=VLOOKUP({UR},CATALOGO!$A$6:$O$20,11,0)", "kVp", "", fmt="0.0", entrada=False)
titulo_seccion(ws, r, "d) Márgenes de protección (ANSI C62.22: MP1 ≥ 20 %, MP2 ≥ 20 %, MP3 ≥ 15 %)"); r += 1
TSIACF = d("Tensión soportable de impulso de onda cortada del equipo  TSIACF = 1,15·BILh", "TSIACF", f"=1.15*{BILh}", "kVp", "", fmt="0.0", entrada=False)
TSNIM = d("Tensión soportable al impulso de maniobra del equipo  TSNIM = 0,83·BILh", "TSNIM", f"=0.83*{BILh}", "kVp", "", fmt="0.0", entrada=False)
MP1 = d("MP1 = (TSIACF/NPFO − 1)·100", "MP1", f"=({TSIACF}/{NPFO}-1)*100", "%", "", fmt="0.0", entrada=False)
MP2 = d("MP2 = (BILh/NPIA − 1)·100", "MP2", f"=({BILh}/{NPIA}-1)*100", "%", "", fmt="0.0", entrada=False)
MP3 = d("MP3 = (TSNIM/NPIM − 1)·100", "MP3", f"=({TSNIM}/{NPIM}-1)*100", "%", "", fmt="0.0", entrada=False)
d("Verificación de márgenes", "", f'=IF(AND({MP1}>=20,{MP2}>=20,{MP3}>=15),"CUMPLE","NO CUMPLE")', "", "", entrada=False)
titulo_seccion(ws, r, "e) Verificación por línea de fuga:  Lf = Lf0·Um·fch"); r += 1
LFC = d("Línea de fuga requerida", "Lf", f"={LFR2}*{Um}*{FCH}", "mm", "", fmt="0.0", entrada=False)
LFP = d("Línea de fuga del pararrayo seleccionado", "Lfp", f"=VLOOKUP({UR},CATALOGO!$A$6:$O$20,13,0)", "mm", "", fmt="0", entrada=False)
d("Verificación Lfp ≥ Lf", "", f'=IF({LFP}>={LFC},"CUMPLE","NO CUMPLE")', "", "", entrada=False)
r += 1
titulo_seccion(ws, r, "RESUMEN DE LA COORDINACIÓN DEL AISLAMIENTO"); r += 1
fila(ws, r, ["Pararrayo seleccionado", "Ur (kV)", "MCOV (kV)", "MP1 (%)", "MP2 (%)", "MP3 (%)", "Lf (mm)", "Resultado"], font=FB, fill=AZ); r += 1
fila(ws, r, [f'="Óxido metálico, "&{UR}&" kV, 10 kA, clase 1"', f"={UR}", f"={MCOV}", f"={MP1}", f"={MP2}", f"={MP3}", f"={LFP}",
             f'=IF(AND({MCOV}>={MCOVr},{TOVP}>={TOVS},{MP1}>=20,{MP2}>=20,{MP3}>=15,{LFP}>={LFC}),"SELECCIÓN CONFORME","CORREGIR")'],
     fmts=[None, "0", "0.0", "0.0", "0.0", "0.0", "0", None]); r += 2
_fch = 1 + 1.25 * (ALT - 1000) / 10000; _lf = LF_MM_KV * SIS["Vmax"] * _fch
if _lf > 660:
    _txt = (f"Nota: el pararrayo de 21 kV (MCOV 17 kV) cumple MCOV, TOV y márgenes, pero su línea de fuga de catálogo (660 mm) es menor que la "
            f"requerida ({_lf:.0f} mm a {ALT} m s.n.m.); por ello se selecciona el de 24 kV (MCOV 19,5 kV, 780 mm). ")
else:
    _txt = (f"Nota: a {ALT} m s.n.m. la línea de fuga requerida es {_lf:.0f} mm; el pararrayo de 21 kV también cumpliría, pero se adopta el de "
            "24 kV (780 mm) por uniformidad del kit de equipos. ")
nota(ws, r, _txt + "Puede cambiarse Ur en la celda amarilla para evaluar otras alternativas.", h=45)
w2 = hoja(wb, "CATALOGO", [10, 10, 12, 11, 9, 9, 9, 9, 9, 9, 10, 10, 11, 11, 11], apaisado=True)
rr = cab(w2, "PARARRAYOS DE ÓXIDO METÁLICO – DATOS DE CATÁLOGO DE REFERENCIA (tipo distribución, 10 kA)", ncol=15)
fila(w2, rr, ["Ur kV", "MCOV kV", "Catálogo", "0,5 μs 10 kA", "1,5 kA", "3 kA", "5 kA", "10 kA", "20 kA", "40 kA", "500 A maniobra",
              "Altura mm", "Línea de fuga mm", "BIL envolvente kVc", "Peso kg"], font=FB, fill=AZ)
cat = [(3, 2.55, 214203, 10.9, 8, 8.7, 9.1, 10.1, 11.6, 13.7, 7.3, 140, 390, 125, 1.9),
       (6, 5.1, 214205, 20.5, 15.2, 16.4, 17.3, 19.1, 21.9, 25.9, 13.8, 140, 390, 125, 1.9),
       (9, 7.65, 214208, 29.1, 21.5, 23.2, 24.5, 27.0, 30.1, 36.6, 19.6, 140, 390, 125, 1.9),
       (10, 8.4, 214209, 32.3, 23.9, 25.7, 27.2, 30.0, 34.4, 40.6, 21.8, 140, 390, 125, 1.9),
       (12, 10.2, 214210, 36.8, 27.3, 29.4, 31.0, 34.3, 39.3, 46.4, 25.0, 140, 390, 125, 2.0),
       (15, 12.7, 214213, 46.0, 34.0, 36.7, 38.7, 42.8, 49.0, 57.9, 31.0, 216, 660, 180, 2.6),
       (18, 15.3, 214215, 56.7, 41.9, 45.2, 47.7, 52.7, 60.4, 71.4, 38.2, 216, 660, 180, 2.6),
       (21, 17.0, 214217, 67.8, 48.0, 51.3, 53.4, 60.0, 68.2, 80.2, 43.8, 216, 660, 180, 2.8),
       (24, 19.5, 214220, 73.6, 54.6, 58.7, 62.0, 68.5, 78.6, 92.8, 50.0, 274, 780, 210, 3.4),
       (27, 22.0, 214222, 82.9, 61.4, 66.1, 69.8, 77.1, 88.4, 104.4, 55.9, 437, 1320, 250, 4.4),
       (30, 24.4, 214224, 91.9, 68.1, 73.3, 77.4, 85.5, 98.1, 115.8, 62.0, 437, 1320, 250, 4.4),
       (36, 29.0, 214230, 114.0, 84.4, 90.8, 95.9, 106.0, 121.6, 143.5, 76.9, 437, 1320, 250, 4.9)]
for k, row in enumerate(cat):
    fila(w2, rr + 1 + k, list(row))
nota(w2, rr + 1 + len(cat) + 1, "Fuente: tabla de catálogo de fabricante (pararrayo polimérico de distribución, servicio pesado) incluida en el "
     "Anexo 2 del expediente de referencia LP Ayaviri–Pucará. Tensiones residuales en kV cresta. El postor acreditará valores equivalentes o mejores.", ncol=15, h=30)
wb.save(OUT / "Anexo 2 Aislamiento y Pararrayos.xlsx")

# =====================================================================================  ANEXO 3
wb = libro()
ws = hoja(wb, "CAL.P.TIERRA", [46, 10, 12, 12, 12, 12, 12, 22])
r = cab(ws, "ANEXO 3: CÁLCULO DE LA RESISTENCIA DE PUESTA A TIERRA")
titulo_seccion(ws, r, "DATOS"); r += 1
fila(ws, r, ["Descripción", "Símbolo", "Valor", "Unidad", "Fuente / observación"], font=FB, fill=AZ); ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=8); r += 1
RHO = d("Resistividad aparente del terreno (a medir en campo)", "ρ", PAT["rho"], "Ω·m", "SUPUESTO – suelo limo-arcilloso circunlacustre")
LV = d("Longitud de la varilla (electrodo vertical)", "L", PAT["L"], "m", "RD 018 / EETT")
DV = d("Diámetro de la varilla", "d", PAT["d"], "m", "Varilla de cobre 16 mm Ø")
SV = d("Separación entre varillas (PAT-2)", "s", 5.0, "m", "≥ 2·L")
KT = d("Factor de reducción de resistividad por tratamiento (cemento conductivo)", "Kt", 0.6, "–", "Modelo: tierra de cultivo + sal + carbón + bentonita")
RMAX = d("Resistencia máxima en estructuras con equipos de protección y seccionamiento", "Rmax", PAT["R_equipo_max"], "Ω", "RD 018-2003-EM/DGE")
r += 1
titulo_seccion(ws, r, "a) Electrodo vertical al nivel del terreno:  R1 = 0,366·(ρ/L)·log₁₀(4L/d)   (fórmula del expediente de referencia)"); r += 1
R1 = d("PAT-1, una varilla, sin tratamiento", "R1", f"=0.366*{RHO}/{LV}*LOG10(4*{LV}/{DV})", "Ω", "Estructuras de alineamiento (cada 3 estructuras)", fmt="0.00", entrada=False)
R1T = d("PAT-1, una varilla, con tratamiento (ρ·Kt)", "R1t", f"=0.366*{RHO}*{KT}/{LV}*LOG10(4*{LV}/{DV})", "Ω", "", fmt="0.00", entrada=False)
titulo_seccion(ws, r, "b) Dos varillas en paralelo separadas s:  R2 = (R1/2)·[1 + ρ/(2π·s·R1)]"); r += 1
R2 = d("PAT-2, dos varillas, sin tratamiento", "R2", f"={R1}/2*(1+{RHO}/(2*PI()*{SV}*{R1}))", "Ω", "Estructuras con equipos (PSER-3, DT-3, PTH-3)", fmt="0.00", entrada=False)
R2T = d("PAT-2, dos varillas, con tratamiento", "R2t", f"={R1T}/2*(1+{RHO}*{KT}/(2*PI()*{SV}*{R1T}))", "Ω", "", fmt="0.00", entrada=False)
d("Verificación PAT-2 con tratamiento ≤ Rmax", "", f'=IF({R2T}<={RMAX},"CUMPLE","AGREGAR VARILLAS / CONTRAPESO")', "", "", entrada=False)
r += 1
titulo_seccion(ws, r, "c) Sensibilidad de la resistencia a la resistividad medida (a completar con mediciones de campo)"); r += 1
fila(ws, r, ["ρ medida (Ω·m)", "R1 (Ω)", "R1t (Ω)", "R2 (Ω)", "R2t (Ω)", "PAT-2 cumple", "Varillas req. (≤ Rmax)", ""], font=FB, fill=AZ); r += 1
for rho in (50, 100, 150, 200, 300, 400):
    a = f"A{r}"
    fila(ws, r, [rho, f"=0.366*{a}/{LV}*LOG10(4*{LV}/{DV})", f"=B{r}*{KT}", f"=B{r}/2*(1+{a}/(2*PI()*{SV}*B{r}))",
                 f"=C{r}/2*(1+{a}*{KT}/(2*PI()*{SV}*C{r}))", f'=IF(E{r}<={RMAX},"SÍ","NO")',
                 f"=IF(C{r}<={RMAX},1,IF(E{r}<={RMAX},2,IF(C{r}/3*1.25<={RMAX},3,\"4 o contrapeso\")))", ""],
         fmts=[None, "0.0", "0.0", "0.0", "0.0", None, None, None]); r += 1
r += 1
nota(ws, r, "Notas: (1) La resistividad es un dato de campo pendiente: el contratista medirá ρ (método Wenner) en cada estructura con "
     "equipos y en muestras representativas del trazado, y ajustará el número de varillas según la tabla c). (2) Coeficiente para 3 varillas "
     "≈ R1t/3·1,25 (interferencia mutua). (3) Las estructuras sin equipos llevan PAT-1 cada 3 estructuras, según la Planilla de Estructuras.", h=55)
wb.save(OUT / "Anexo 3 CALCULO PUESTA A TIERRA.xlsx")

# =====================================================================================  ANEXO 8  (caída de tensión)
dem = pd.read_csv(W / "demanda.csv")
wb = libro()
ws = hoja(wb, "PARAMETROS", [44, 12, 13, 13, 13, 13, 13, 26])
r = cab(ws, "ANEXO 8: PARÁMETROS ELÉCTRICOS, CAÍDA DE TENSIÓN Y PÉRDIDAS DE POTENCIA Y ENERGÍA")
titulo_seccion(ws, r, "PARÁMETROS DEL CONDUCTOR AAAC 70 mm² Y DE LA LÍNEA"); r += 1
fila(ws, r, ["Descripción", "Símbolo", "Valor", "Unidad", "Fuente / observación"], font=FB, fill=AZ); ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=8); r += 1
c70 = COND[70]
V = d("Tensión nominal", "VL", SIS["Vn"], "kV", "")
COS = d("Factor de potencia", "cos φ", SIS["cos"], "–", "RD 018")
R20 = d("Resistencia eléctrica a 20 °C", "R20", c70["R20"], "Ω/km", "RD 018-2003, Cuadro 6.1")
ALF = d("Coeficiente térmico de resistencia", "α", 0.0036, "1/°C", "AAAC (expediente de referencia)")
TOP = d("Temperatura de operación del conductor", "t", 40, "°C", "RD 018")
RT = d("Resistencia a la temperatura de operación  R = R20·[1 + α(t − 20)]", "r1", f"={R20}*(1+{ALF}*({TOP}-20))", "Ω/km", "", fmt="0.0000", entrada=False)
DIA = d("Diámetro exterior del conductor", "D", c70["D"], "mm", "")
RE = d("Radio medio geométrico  RMG = 0,7788·D/2 (aprox. 19 hilos: 0,758·D/2)", "re", f"=0.758*{DIA}/2", "mm", "", fmt="0.00", entrada=False)
DAB = d("Distancia entre fases inferiores (cruceta)", "Y", ARM["sep_h"], "m", "Armado PS1-3")
DV_ = d("Distancia vertical fase superior – cruceta", "h", ARM["d_inf"] - ARM["d_sup"], "m", "Armado PS1-3", fmt="0.00")
DD = d("Distancia fase superior a fases inferiores  D = √[(Y/2)² + h²]", "D'", f"=SQRT(({DAB}/2)^2+{DV_}^2)", "m", "", fmt="0.000", entrada=False)
DMG = d("Distancia media geométrica  DMG = (Y·D'·D')^(1/3)", "DMG", f"=({DAB}*{DD}*{DD})^(1/3)*1000", "mm", "", fmt="0.0", entrada=False)
XL = d("Reactancia inductiva  XL = 2πf·[0,5 + 4,6·log(DMG/re)]·10⁻⁴", "X1", f"=2*PI()*{SIS['f']}*(0.5+4.6*LOG10({DMG}/{RE}))*0.0001", "Ω/km", "RD 018 6.2", fmt="0.0000", entrada=False)
K1 = d("Factor de caída de tensión  K = (r1 + X1·tg φ)/(10·VL²)", "K", f"=({RT}+{XL}*TAN(ACOS({COS})))/(10*{V}^2)", "%/(kW·km)", "", fmt="0.000000", entrada=False)
FCg = d("Factor de carga", "Fc", MERCADO["fc"], "–", "Estudio de mercado (Memoria)")
FPd = d("Factor de pérdidas  FP = 0,15·Fc + 0,85·Fc²", "FP", f"=0.15*{FCg}+0.85*{FCg}^2", "–", "RD 018 7.0", fmt="0.0000", entrada=False)
r += 1
titulo_seccion(ws, r, "CAÍDA DE TENSIÓN Y PÉRDIDAS POR TRAMO – AÑO 20 (máxima demanda proyectada)"); r += 1
fila(ws, r, ["Tramo", "L (km)", "P (kW)", "ΔV tramo (%)", "ΔV acum. (%)", "PJ (kW)", "PE (MWh/año)", "Verificación ΔV ≤ 5 %"], font=FB, fill=AZ); r += 1
nodos = R["electrico"]["nodos"]; t1 = r
ini = f"{INICIO['nombre']} (E-001)"
for k, nd in enumerate(nodos):
    desde = ini if k == 0 else f"Derivación {nodos[k-1]['nombre']}"
    hasta = f"{'Derivación ' if nd['punto'] != 'FIN' else ''}{nd['nombre']}"
    acum = f"=D{r}" if k == 0 else f"=E{r-1}+D{r}"
    fila(ws, r, [f"{desde} – {hasta}", round(nd["L_tramo_km"], 3), round(nd["P_kW"], 2),
                 f"={K1}*C{r}*B{r}", acum, f"=C{r}^2*{RT}*B{r}/(1000*{V}^2*{COS}^2)", f"=8760*F{r}*{FPd}/1000",
                 f'=IF(E{r}<={SIS["dV_max_pct"]},"CUMPLE","NO CUMPLE")'], fmts=[None, "0.000", "0.0", "0.000", "0.000", "0.00", "0.0", None]); r += 1
fila(ws, r, ["TOTAL", f"=SUM(B{t1}:B{r-1})", f"=C{t1}", "", f"=E{r-1}", f"=SUM(F{t1}:F{r-1})", f"=SUM(G{t1}:G{r-1})",
             f'="Pérdidas: "&TEXT(F{r}/C{r}*100,"0.00")&" % de la MD"'], font=FB, fmts=[None, "0.000", "0.0", None, "0.000", "0.00", "0.0", None]); r += 2
nota(ws, r, f"Notas: la caída de tensión se calcula desde el punto de diseño ({INICIO['nombre']}, E-001); la tensión en dicho punto y la "
     f"potencia de cortocircuito deben ser confirmadas por {PROYECTO['concesionaria']} en el documento de factibilidad y fijación del punto de diseño "
     "(pendiente). Demanda año 20 según estudio de mercado (hoja DEMANDA).", h=45)
w2 = hoja(wb, "DEMANDA", [10, 34, 12, 12, 12, 12, 12, 12])
rr = cab(w2, "PROYECCIÓN DE LA MÁXIMA DEMANDA (Estudio de mercado – Memoria Descriptiva)", ncol=8)
fila(w2, rr, ["Año", "Carga", "Viviendas", "Abonados", "CU kWh/mes", "E total MWh", "MD kW", ""], font=FB, fill=AZ); rr += 1
for x in dem.itertuples():
    fila(w2, rr, [x.anio, x.carga, round(x.viviendas, 0), round(x.abonados, 0), round(x.cu_kwh_mes, 2), round(x.E_total_MWh, 1), round(x.MD_kW, 1), ""]); rr += 1
wb.save(OUT / "Anexo 8 CAIDA DE TENSION Y PERDIDAS.xlsx")
print("ok anexos 1,2,3,8 – ALT", ALT)
