"""Volumen VI (Cálculos justificativos – Cap. II), VIII (geología y geotecnia de gabinete + TdR), IX (flujo, cortocircuito y protección),
X (requerimientos mínimos) y XI (anexos: gestión de riesgos, panel fotográfico, cotizaciones, datos pendientes).
Uso: python p14_docs_calculos.py WORK OUTDIR"""
import json, math, cmath, sys
from pathlib import Path
import pandas as pd, openpyxl
sys.path.insert(0, str(Path(__file__).parent))
from params import *
from catalogo import ARM_DESC, MATD, TC, TC_FUENTE
from docgen import *
from comun import cargar, lista, fusibles_txt, png_de_pdf as _png, clima
from xlhelp import libro, hoja, cab, dato, fila, titulo_seccion, nota as xnota, AZ, FB

W = Path(sys.argv[1]); OUT = Path(sys.argv[2])
C = cargar(W); K = C["K"]; E = C["E"]; dem = C["dem"]; DER = C["ders"]
comp = pd.read_csv(W / "comparacion_conductores.csv")
L = C["L"]; el = K["el"]; M = K["met"]; ALT = C["ALT"]; CONC = PROYECTO["concesionaria"]; INI, FINN, E0, EF = C["ini"], C["fin"], C["E0"], C["EF"]
_n = lambda x, d=0: fmt(float(x), d).replace("-", "−")
VMS = float(CLIMA["viento_ms"]); TH6 = HIP["H6 Temp. máxima"]["t"]
# nodos principales: arranque, derivaciones (por progresiva) y llegada
NODOS = [(f"{E0} (arranque, reconectador)", 0.0, None)] + [(f"{x['estructura']} (derivación {x['nombre']})", x["prog"] / 1000, x) for x in DER] + \
        [(f"{EF} (llegada {FINN})", L, None)]
ncruces = len(pd.read_csv(W / "cruces.csv")) if (W / "cruces.csv").exists() else 0
A20 = int(dem.anio.max())
c70 = COND[70]

# =========================================================================================== VOL VI
d = nuevo("VOLUMEN VI – CÁLCULOS JUSTIFICATIVOS")
caratula_volumen(d, "VOLUMEN VI", "CÁLCULOS JUSTIFICATIVOS")
p(d, f"“{NOMBRE}”", bold=True, align="C", size=12); p(d, "CAPÍTULO II: CÁLCULOS JUSTIFICATIVOS", bold=True, align="C", size=12)
h(d, "2.1 Objetivo")
p(d, "Establecer, mediante cálculos, las características eléctricas y mecánicas de la línea primaria en 22,9 kV: nivel de aislamiento, distancias de seguridad, "
     "selección y parámetros del conductor, caída de tensión y pérdidas, pararrayos, coordinación del aislamiento, puesta a tierra, cálculo mecánico de conductores "
     "y estructuras, cimentaciones y retenidas. Las hojas de cálculo editables, con todas sus fórmulas, se presentan como Anexos 1 a 9.")
h(d, "2.2 Normas aplicables")
bullets(d, ["Código Nacional de Electricidad – Suministro 2011.", "R.D. N.° 018-2003-EM/DGE – Bases para el diseño de líneas y redes primarias para electrificación rural.",
            "R.D. N.° 026-2003-EM/DGE – Especificaciones técnicas de suministro de materiales y equipos.", "Norma Técnica de Calidad de los Servicios Eléctricos Rurales (R.D. N.° 016-2008-EM/DGE).",
            "IEC 60071-1/2 (coordinación de aislamiento), IEC 60815 (contaminación), IEC 60099-4/5 (pararrayos), IEEE Std 1410 (desempeño ante descargas)."])
h(d, "2.3 Aspectos de diseño eléctrico")
bullets(d, [f"La tensión de 22,9 kV se toma de la red existente de {CONC} en el punto de diseño de {INI} (por confirmar en la factibilidad).",
            "El porcentaje de caída de tensión no deberá exceder 5,0 %.", "Las pérdidas de potencia no deberán exceder 3,5 % de la máxima demanda.", "Sistema trifásico (3ø)."])
h(d, "2.4 Características generales de la línea")
datos(d, [("Tensión nominal del sistema", "22,9 kV"), ("Tensión máxima del sistema", "25 kV"), ("Configuración", "3ø"), ("Frecuencia", "60 Hz"),
          ("Factor de potencia", "0,90 (atraso)"), ("Potencia de cortocircuito mínima", f"{SIS['Scc_MVA']:.0f} MVA (por confirmar)"),
          ("Nivel isoceráunico", str(SIS["isoceraunico"])), ("Altitud", f"{fmt(el['cota_min'],0)} – {fmt(el['cota_max'],0)} m s.n.m. (diseño {_n(ALT)} m s.n.m.)")])
h(d, "2.5 Trazo de la ruta de línea")
_ruta = (f"La ruta sigue el corredor vial ({TRAZADO.get('nombre_via','vía existente')}), desplazada {_n(TRAZADO.get('desplazamiento_m',0))} m de su eje"
         if TRAZADO.get("ruta_es_via") else "La ruta sigue el eje definido por el proyectista")
p(d, _ruta + ", con los criterios de: evitar zonas urbanas consolidadas, cercanía a vías y caminos para el transporte y montaje, alineamientos largos y mínimo "
     f"número de vértices, y cruce perpendicular de las vías ({ncruces} cruce{'s' if ncruces != 1 else ''}).")
h(d, "2.6 Cálculos eléctricos")
h(d, "2.6.1 Cálculo del aislamiento de la línea y selección de aisladores", 2)
p(d, "Se consideran la contaminación ambiental, las sobretensiones a frecuencia industrial y las sobretensiones atmosféricas (Anexo 1).")
p(d, "A.- Aislamiento necesario por contaminación ambiental", bold=True)
formula(d, "Lfuga = Lf0 · Umax · fch          fch = 1 + 1,25 (h − 1 000) · 10⁻⁴")
tabla(d, ["Altitud", "fch", "Lf0 (mm/kV)", "Umax (kV)", "Lfuga (mm)"], [(f"{_n(ALT)} m s.n.m.", fmt(K["aisl"]["fch"], 4), fmt(LF_MM_KV, 1), _n(SIS["Vmax"]), fmt(K["aisl"]["Lf"], 0))],
      titulo="Aislamiento requerido por contaminación", widths=[3.6, 2.4, 2.8, 2.6, 2.6])
p(d, f"Se adopta {_n(LF_MM_KV)} mm/kV (nivel de contaminación: {CLIMA.get('contaminacion', 'medio')}, IEC 60815) según el ambiente del corredor.", size=10.5)
p(d, "B.- Aislamiento necesario por sobretensión a frecuencia industrial (bajo lluvia)", bold=True)
formula(d, "Vfi = fs · H · (Umax/√3) / [(1 − N·σ) · δ · fl]          log b = log 76 − h/18 336;   δ = 3,92·b/(273 + t)")
p(d, f"Con fs = 1,5; H = 1; N = 3; σ = 2 %; fl = 0,8; b = {fmt(K['aisl']['b'],2)} cm Hg; t = {_n(T_MEDIA)} °C → δ = {fmt(K['aisl']['delta'],4)}; resulta Vfi = {fmt(K['aisl']['Vfi'],1)} kV.")
p(d, "C.- Voltaje crítico de flameo al impulso", bold=True)
formula(d, "Vi = NBI / [(1 − N'·σ') · δ]")
p(d, f"Con NBI = 125 kV, N' = 1,2 y σ' = 3 %: Vi = {fmt(K['aisl']['Vi'],1)} kVp. Para los equipos se requiere NBI·fch = {fmt(K['aisl']['NBIh'],1)} kVp → 170 kV-BIL (clase 38 kV).")
p(d, "D.- Selección de los aisladores", bold=True)
tabla(d, ["Característica", "Unid.", "Calculado", "Porcelana PIN 56-4", "Polimérico susp. 36 kV"],
      [("Lf", "mm", fmt(K["aisl"]["Lf"], 0), "685", "≥ 720"), ("Vfi", "kV", fmt(K["aisl"]["Vfi"], 1), "95", "≥ 100"), ("Vi", "kVp", fmt(K["aisl"]["Vi"], 1), "225", "≥ 250")],
      titulo="Selección de los aisladores", widths=[3.2, 1.6, 2.6, 3.8, 4.2])
p(d, "Se seleccionan aisladores de porcelana tipo PIN clase ANSI 56-4 para los armados de suspensión y ángulo hasta 30°, y aisladores poliméricos de suspensión de "
     "36 kV para los armados de anclaje, ángulo fuerte, retención/suspensión, derivación y terminales (Anexo 1).")
h(d, "2.6.2 Distancias mínimas de seguridad", 2)
bullets(d, ["Entre conductores del mismo circuito en los apoyos: horizontal 0,70 m; vertical 1,00 m (diseño: 2,00 m y 1,40 m).",
            "Entre conductores y elementos puestos a tierra: 0,25 m.",
            f"Horizontal entre conductores a mitad de vano: D = 0,0076·U·Fc + 0,65·√f; máximo requerido {fmt(K['plan']['Dh_max'],2)} m < 2,00 m disponible.",
            "Vertical entre conductores a mitad de vano: 0,70 m (vanos ≤ 100 m), 1,00 m (101–350 m); disponible 1,40 m.",
            "Al terreno: 6,0 m en zonas con circulación de maquinaria agrícola y caminos; 7,0 m en cruces de carreteras; 5,0 m en zonas peatonales.",
            "A edificaciones: 2,5 m radial a paredes y estructuras no accesibles; 2,5 m horizontal a partes accesibles; a árboles 2,5 m vertical y 0,5 m radial."])
p(d, f"Las distancias al terreno se verificaron vano por vano con la flecha a máxima temperatura (H6) y un margen de 0,30 m por la precisión del DEM: los {len(E)-1} vanos cumplen (Anexo 9, hoja DISTANCIAS).")
h(d, "2.6.3 Selección del conductor", 2)
tabla(d, ["Sección (mm²)", "R40 (Ω/km)", "X (Ω/km)", "ΔV año 20 (%)", "PJ (kW)", "Costo total (S/)", "Cumple"],
      [(int(r.seccion_mm2), fmt(r.R40, 3), fmt(r.X, 3), fmt(r.dV20_pct, 2), fmt(r.PJ20_kW, 1), fmt(r.Costo_total_S, 0),
        "Seleccionado" if r.seleccion else ("Sí" if r.cumple_reserva and r.cumple_Icc and r.cumple_I else "No")) for r in comp.itertuples()],
      titulo="Comparación técnico-económica de secciones AAAC", widths=[2.0, 2.0, 2.0, 2.4, 2.0, 3.0, 2.2])
_opt = el.get("seccion_optima")
p(d, f"Se exige ΔV ≤ {_n(SIS['reserva_dV']*100)} % del límite (reserva por la incertidumbre del estudio de mercado), capacidad de corriente y cortocircuito; entre las "
     "que cumplen, el óptimo económico es la de menor costo total (inversión en conductor + valor presente de pérdidas a 20 años, tasa 8 %). "
     + (f"Resultado: AAAC {SECCION} mm²." if _opt == SECCION else
        f"El óptimo económico resulta {_opt} mm²; se adopta AAAC {SECCION} mm² por estandarización del kit de materiales (troncal), que también cumple todos los criterios."
        if el.get("kit_cumple", True) else f"ATENCIÓN: la sección del kit ({SECCION} mm²) NO cumple; ver Vol. VI 2.9 y reemplazar el kit."))
datos(d, [("Sección nominal / real", "70 / 65,8 mm²"), ("Diámetro exterior", "10,5 mm"), ("Masa", "0,181 kg/m"), ("Esfuerzo de rotura", "295,8 N/mm² (19,46 kN)"),
          ("Resistencia eléctrica a 20 °C", "0,507 Ω/km")])
h(d, "2.6.4 Parámetros de la línea primaria", 2)
formula(d, "R40 = R20 · [1 + α (40 − 20)]          XL = 2πf [0,5 + 4,6 log(DMG/re)] · 10⁻⁴ Ω/km")
formula(d, "DMG = (Y · D' · D')^(1/3)          D' = √[(Y/2)² + h²]")
p(d, f"Con Y = 2,00 m (separación entre fases inferiores), h = 1,40 m, re = 0,758·D/2 = 3,98 mm: DMG = {fmt(K['elec']['DMG'],0)} mm, "
     f"R40 = {fmt(K['elec']['r1'],4)} Ω/km y XL = {fmt(K['elec']['X1'],4)} Ω/km.")
h(d, "2.6.5 Cálculo del conductor por capacidad de corriente, caída de tensión y pérdidas de potencia", 2)
formula(d, "ΔV% = K · P · L          K = (r1 + X1 · tg φ) / (10 · VL²)")
formula(d, "PJ = P² · r1 · L / (1 000 · VL² · cos² φ)  [kW]          EJ = 8 760 · PJ · FP  [kWh];   FP = 0,15·Fc + 0,85·Fc²")
tabla(d, ["Tramo", "L (km)", "P (kW)", "ΔV acum. (%)", "PJ (kW)"],
      [(f"{a[0].split(' ')[0]} – {b[0].split(' ')[0]}" + (f" ({b[2]['nombre']})" if b[2] else f" ({FINN})"), fmt(nd["L_tramo_km"], 3), fmt(nd["P_kW"], 1), fmt(nd["dV_pct"], 3), "–")
       for a, b, nd in zip(NODOS[:-1], NODOS[1:], el["nodos"])] +
      [("Total línea", fmt(L, 3), fmt(K["dem"]["MD_anio20_kW"], 1), fmt(K["elec"]["dV"], 3), fmt(K["elec"]["PJ"], 2))],
      titulo=f"Caída de tensión y pérdidas – año {A20}", widths=[6.4, 2.0, 2.4, 2.6, 2.2], bold_last=True)
p(d, f"Corriente máxima al año {A20}: {fmt(comp[comp.seleccion].I20_A.iloc[0],1)} A < 255 A de capacidad del AAAC 70 mm². Pérdidas: {fmt(K['elec']['PJ']/K['dem']['MD_anio20_kW']*100,2)} % "
     f"de la máxima demanda; energía perdida {fmt(K['elec']['PE'],1)} MWh/año (Anexo 8).")
h(d, "2.6.6 Selección de pararrayos", 2)
datos(d, [("Tensión nominal del sistema (Vn)", "22,9 kV"), ("Factor de mayor variación de tensión (Ft)", "1,05 p.u."), ("Factor de falla a tierra (Ce)", "1,4 (neutro efectivamente a tierra)"),
          ("Duración de la falla", "10 s"), ("Altitud de instalación", f"{_n(ALT)} m s.n.m."), ("Nivel de aislamiento de equipos", "170 kVp (125 kVp efectivos a la altitud)")])
formula(d, "MCOV ≥ Ft · Vn / √3          TOVsistema = Ce · Umax / √3          TOVpararrayo = T · MCOV")
_pr21 = (f"El pararrayo de 21 kV (MCOV 17 kV) cumple MCOV y TOV, pero su línea de fuga (660 mm) es menor que la requerida ({fmt(K['aisl']['Lf'],0)} mm); se selecciona el de 24 kV"
         if K["aisl"]["Lf"] > 660 else "Se adopta el pararrayo de 24 kV del kit de materiales (margen adicional de TOV y línea de fuga)")
p(d, f"MCOV requerido = {fmt(K['pr']['MCOVr'],2)} kV. {_pr21}: MCOV = {fmt(K['pr']['MCOV'],1)} kV; TOVpr = 1,3 × {fmt(K['pr']['MCOV'],1)} = {fmt(K['pr']['TOVp'],2)} kV ≥ "
     f"TOVsist = {fmt(K['pr']['TOVs'],2)} kV: {'CUMPLE' if K['pr']['TOVp'] >= K['pr']['TOVs'] else 'NO CUMPLE'}. Línea de fuga {fmt(K['pr']['Lfp'],0)} mm: "
     f"{'CUMPLE' if K['pr']['Lfp'] >= K['aisl']['Lf'] else 'NO CUMPLE'} (Anexo 2).")
p(d, "Conclusión: pararrayos de óxido metálico, tensión nominal 24 kV, MCOV 19,5 kV, 10 kA, clase 1.", bold=True)
h(d, "2.6.7 Coordinación de aislamiento", 2)
formula(d, "MP1 = (TSIACF/NPFO − 1)·100      MP2 = (TSNIA/NPIA − 1)·100      MP3 = (TSNIM/NPIM − 1)·100")
p(d, f"Con TSNIA = 170/fch = {fmt(K['pr']['BILh'],1)} kVp, TSIACF = 1,15·TSNIA, TSNIM = 0,83·TSNIA; NPFO = {fmt(K['pr']['NPFO'],1)} kVp, NPIA = {fmt(K['pr']['NPIA'],1)} kVp y "
     f"NPIM = {fmt(K['pr']['NPIM'],1)} kVp (catálogo):")
tabla(d, ["Ur (kV)", "MP1 (%)", "MP2 (%)", "MP3 (%)", "Mínimos ANSI C62.22"], [("24", fmt(K["pr"]["MP1"], 1), fmt(K["pr"]["MP2"], 1), fmt(K["pr"]["MP3"], 1), "20 / 20 / 15")],
      titulo="Márgenes de seguridad de la coordinación del aislamiento", widths=[2.4, 2.6, 2.6, 2.6, 4.4])
h(d, "2.6.8 Puesta a tierra", 2)
formula(d, "PAT-1:  R1 = 0,366 · (ρ/L) · log(4L/d)          PAT-2:  R2 = (R1/2) · [1 + ρ/(2π · s · R1)]")
tabla(d, ["Configuración", "Sin tratamiento (Ω)", "Con cemento conductivo (Ω)", "Uso"],
      [("PAT-1 (1 varilla)", fmt(K["pat"]["R1"], 1), fmt(K["pat"]["R1t"], 1), "Una de cada tres estructuras y adyacentes a equipos"),
       ("PAT-2 (2 varillas, s = 5 m)", fmt(K["pat"]["R2"], 1), fmt(K["pat"]["R2t"], 1), "Estructuras con equipos (≤ 25 Ω)")],
      titulo=f"Resistencia de puesta a tierra (ρ = {_n(PAT['rho'])} Ω·m supuesto, L = 2,40 m, d = 16 mm)", widths=[3.8, 3.0, 3.6, 5.2])
p(d, "La resistividad real se medirá en campo (método Wenner); el Anexo 3 contiene la tabla de sensibilidad para definir el número de varillas según la ρ medida.")
h(d, "2.7 Cálculos mecánicos")
h(d, "2.7.1 Cálculos mecánicos del conductor", 2)
p(d, "Determinan los esfuerzos horizontales y en los apoyos, las flechas, los parámetros de la catenaria, la plantilla de flecha máxima y los vanos peso y viento.")
tabla(d, ["Descripción", "AAAC 70 mm²"], [("Sección real (mm²)", "65,8"), ("Número de hilos", "19"), ("Diámetro exterior (mm)", "10,5"), ("Peso unitario (N/m)", fmt(K['mec']['w_c_N_m'], 4)),
                                         ("Carga de rotura (N)", "19 466"), ("Módulo de elasticidad final (N/mm²)", "60 760"), ("Coeficiente de dilatación (1/°C)", "23 × 10⁻⁶"),
                                         ("EDS inicial / final", "18 % / 15 % UTS"), ("Esfuerzo máximo admisible", "60 % UTS = 177,5 N/mm²")],
      titulo="Características de los conductores utilizados", widths=[8.0, 4.0])
formula(d, "Wv = Pv · (D + 2e);   Wh = ρh · g · π[(D + 2e)² − D²]/4;   Wr = √[(Wc + Wh)² + Wv²];   Pv = K · V²  (K = " + fmt(K_VIENTO, 3) + ")")
formula(d, "σ2² · [σ2 − σ1 + α E (t2 − t1) + E Wr1² d² / (24 S² σ1²)] = E Wr2² d² / (24 S²)")
formula(d, "f = Wr · d² / (8 · S · σ)          Plantilla:  y = x² / (2p),  p = S·σ/Wr")
rows = []
for dd in ("100", "150", "200"):
    c = K["cmc"][dd]
    for hh in ("H1", "H2", "H3", "H4", "H5", "H5b", "H6"):
        if hh in c: rows.append((dd, hh, fmt(c[hh]["s"], 2), fmt(c[hh]["T"], 0), fmt(c[hh]["f"], 2), fmt(c[hh]["pct"] * 100, 1)))
tabla(d, ["Vano (m)", "Hipótesis", "σ (N/mm²)", "TH (N)", "Flecha (m)", "% UTS (apoyo)"], rows, titulo="Resultados del cálculo mecánico (extracto del Anexo 4)",
      widths=[2.0, 2.4, 2.6, 2.6, 2.4, 2.6], size=8.5)
p(d, f"En ninguna hipótesis ni vano (10 a 400 m) el tiro en el apoyo supera el 60 % UTS (máximo {fmt(K['cmc_maxpct']*100,1)} %). La tabla de templado (flechas de tendido "
     "por vano y temperatura, con compensación de CREEP de 10 °C) se encuentra en el Anexo 4.")
import matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
(W / "prev").mkdir(exist_ok=True)
def png_de_pdf(pdf, nombre, dpi=110): return _png(pdf, W / "prev" / f"{nombre}.png", dpi)
pv = pd.read_csv(W / "parametros_vano.csv"); mec = pd.read_csv(W / "calculo_mecanico_conductor.csv")
fig, ax = plt.subplots(figsize=(7, 3.4))
for hh, lab in (("H6 Temp. máxima", f"Flecha a {_n(TH6)} °C (H6)"), ("H4 Viento máximo", "Flecha con viento máximo (H4)"), ("H2 EDS final", "Flecha EDS final (H2)")):
    g = mec[mec.hipotesis == hh]; ax.plot(g.vano_m, g.flecha_m, marker="o", ms=3, label=lab)
ax.set_xlabel("Vano (m)"); ax.set_ylabel("Flecha (m)"); ax.grid(alpha=.3); ax.legend(fontsize=8); fig.tight_layout()
fig.savefig(W / "prev" / "flechas.png", dpi=150); plt.close(fig)
imagen(d, W / "prev" / "flechas.png", 14.5, "Figura 2.1: Flechas del conductor AAAC 70 mm² por vano e hipótesis (Anexo 4)")
h(d, "2.7.2 Cálculo mecánico de soportes", 2)
datos(d, [("Velocidad / presión del viento", f"{_n(VMS,1)} m/s / {fmt(K_VIENTO*VMS**2,1)} Pa"), ("Vanos de la línea", f"{fmt(K['plan']['vano_min'],1)} a {fmt(K['plan']['vano_max'],1)} m"),
          ("Postes", "CAC 12/300, 12/400, 13/400 daN"), ("Empotramiento", "he = L/10 + 0,60 m"), ("Punto de aplicación de la fuerza", "0,15 m bajo la punta"),
          ("Factores de seguridad", "postes 2; retenidas 2; crucetas 1,5 / 2; PIN 2; polimérico 2,5")])
formula(d, "MVC = Pv·Dc·VV·Σh·cos(α/2);   MTC = 2·T·Σh·sen(α/2) (anclaje/terminal: T·Σh);   MVP = Pv·hl²·(Dm + 2Do)/600")
formula(d, "MCW = bc·(Wc·VP + Wa + Wh);   MRN = MVC + MTC + MVP + MCW;   QN = MRN/(hl − 0,15)")
grp = E.groupby("armado").agg(n=("N", "count"), vv=("vano_viento_m", "max"), qn=("QN_daN", "max"), qr=("QN_con_ret_daN", "max"), ret=("n_retenidas", "sum")).reset_index()
tabla(d, ["Armado", "Cant.", "VV máx (m)", "QN sin ret. máx (daN)", "QN con ret. máx (daN)", "Retenidas"],
      [(r.armado, r.n, fmt(r.vv, 1), fmt(r.qn, 1), fmt(r.qr, 1), int(r.ret)) for r in grp.itertuples()],
      titulo="Resumen de la verificación por estructura (Anexo 6, hoja VERIF_ESTRUCTURAS)", widths=[2.2, 1.6, 2.4, 3.2, 3.2, 2.2])
p(d, f"Las {len(E)} estructuras cumplen con el poste asignado (12/300 daN en suspensión; 12/400 o 13/400 daN en ángulo, anclaje y equipos), con las retenidas indicadas. "
     "Además, el Anexo 6 contiene para cada armado la tabla de prestaciones en función del vano (verificación del poste, deflexión ≤ 2,5 %, pandeo, cruceta y aisladores).")
p(d, f"Arrancamiento: en {int(((E.vano_peso_m < 0) & E.armado.isin(['TS-3'])).sum())} estructuras ubicadas en depresiones el vano peso a temperatura mínima resulta negativo; "
     "en ellas se emplea el armado TS-3 (retención/suspensión con cadenas de anclaje) en lugar de aisladores PIN.")
h(d, "2.7.3 Elección de la estructura soporte", 2)
tabla(d, ["N.°", "Descripción", "Tipo"], [(f"{i+1:03d}", ARM_DESC[a], a) for i, a in enumerate(K["met"]["armados"])] +
      [("", "Retenida inclinada", "RI"), ("", "Puesta a tierra con una varilla", "PAT-1"), ("", "Puesta a tierra con dos varillas", "PAT-2"), ("", "Cimentación de concreto ciclópeo", "CM")],
      titulo="Relación de armados utilizados", widths=[1.4, 11.6, 2.6])
lam = sorted((W / "planos2/laminas").glob("LD-LP-01_*.pdf"))[0]
imagen(d, png_de_pdf(lam, "lam01"), 10.5, "Figura 2.2: Armado PS1-3 con lista de materiales (lámina LD-LP-01, Vol. VII)")
h(d, "2.7.4 Cimentaciones", 2)
p(d, "Método de Sulzberger (distribución de reacciones en la base y a 2/3 de la profundidad):")
formula(d, "F − R1 + R2 = 0;   F·(H + 2h/3) − R1·(h/3) − R2·(2h/9) = 0   ⇒   R1 = F·(9H + 8h)/(5h);   R2 = R1 − F")
formula(d, "σ1 = 1,5·R1/(De·h) ≤ Cp;   σ2 = 3·R2/(De·h) ≤ Cp;   σv = Wt/A ≤ qa")
cm = K["cim"]
tabla(d, ["Poste", "h (m)", "De (m)", "R1 (N)", "R2 (N)", "σ1 (daN/cm²)", "σ2 (daN/cm²)", "σv (daN/cm²)"],
      [(p_, h_, de, fmt(cm["R1"][i], 0), fmt(cm["R2"][i], 0), fmt(cm["s1"][i], 3), fmt(cm["s2"][i], 3), fmt(cm["sv"][i], 3))
       for i, (p_, h_, de) in enumerate([("12/300", "1,80", "0,80"), ("12/400", "1,80", "0,80"), ("13/400", "1,90", "0,90")])],
      titulo="Resultados de la verificación de cimentaciones (Cp = 2,1 daN/cm²; qa = 1,0 daN/cm² – supuestos)", widths=[1.8, 1.4, 1.4, 1.9, 1.9, 2.4, 2.4, 2.4], size=8.5)
p(d, "Todas las presiones resultan menores que las admisibles supuestas. Estos valores deberán confirmarse con el estudio de mecánica de suelos (Vol. VIII).")
lam = sorted((W / "planos2/laminas").glob("LD-LP-11_*.pdf"))[0]
imagen(d, png_de_pdf(lam, "lam11"), 9.5, "Figura 2.3: Cimentación de postes (lámina LD-LP-11)")
h(d, "2.7.5 Cálculo de retenidas", 2)
datos(d, [("Material", "Acero grado Siemens-Martin, 7 hilos, 10 mm"), ("Carga de rotura", "30,92 kN"), ("Coeficiente de seguridad", "2"), ("Ángulo con el poste", "37°")])
formula(d, "Tret = MTC / [(Σh/3) · sen φ];   n = ⌈Tret / (Tr/FS)⌉;   anclaje y ángulo > 60°: n = 2·⌈3T/(sen φ · Tr/FS)⌉")
p(d, f"Tiro máximo de trabajo por retenida: {fmt(K['ret']['Tw'],0)} N → FS del cable = {fmt(K['ret']['FSc'],2)} ≥ 2.", bold=False)
p(d, "Bloque de anclaje", bold=True)
formula(d, "Fres = Wt·cos φ + Pb·cos φ + μ·½·Ka·γ·g·Hb²·(2D + 2f);   Ka = tg²(45° − θ/2)")
p(d, f"Con Hb = 2,00 m, D = f = 0,80 m, γ = 1 500 kg/m³, θ = 23°, μ = 0,5: Fres = {fmt(K['ret']['Fres'],0)} N; FS = {fmt(K['ret']['FSb'],2)} ≥ 2 (Anexo 7), con excavación de "
     "0,80 × 0,80 × 2,00 m.")
h(d, "2.8 Anexos")
bullets(d, ["Anexo 1: Selección del nivel de aislamiento y de aisladores para líneas primarias 22,9 kV.", "Anexo 2: Estudio de coordinación de aislamiento – selección de pararrayos.",
            "Anexo 3: Cálculo de resistencia de puesta a tierra.", "Anexo 4: Cálculo mecánico del conductor AAAC 70 mm² y tabla de templado.", "Anexo 5: Cimentación de estructuras.",
            "Anexo 6: Cálculo mecánico de estructuras, retenidas y crucetas (prestaciones por armado y verificación estructura por estructura).",
            "Anexo 7: Cálculo de retenidas y bloque de anclaje.", "Anexo 8: Parámetros eléctricos, caída de tensión y pérdidas.",
            "Anexo 9: Planilla de estructuras y verificación de distancias de seguridad por vano."])
h(d, "2.9 Verificación de coherencia entre documentos")
tabla(d, ["Verificación", "Resultado", "Detalle"], [(c["verificacion"], c["resultado"], c["detalle"]) for c in K["chk"]], widths=[7.2, 2.4, 6.0], size=8)
proyectista(d)
d.save(OUT / "VOL. VI CALCULOS JUSTIFICATIVOS.docx")

# =========================================================================================== VOL IX (ECP)
V = SIS["Vn"]; Scc = SIS["Scc_MVA"]; XR = SIS["XR"]
Zs1 = V ** 2 / Scc; Rs = Zs1 / math.sqrt(1 + XR ** 2); Xs = Rs * XR
z1 = complex(c70["R20"], K["elec"]["X1"])
De = 658.5 * math.sqrt(PAT["rho"] / SIS["f"]); gmr = 0.758 * c70["D"] / 2 / 1000; Ds3 = (gmr * (K["elec"]["DMG"] / 1000) ** 2) ** (1 / 3)
z0 = complex(c70["R20"] + 3 * 0.0592, 3 * 0.1736 * math.log10(De / Ds3))
nodos = [(nm, l) for nm, l, _ in NODOS]
cc = []
for nm, l in nodos:
    Z1 = complex(Rs, Xs) + l * z1; Z0 = complex(Rs, Xs) + l * z0
    I3 = V * 1000 / (math.sqrt(3) * abs(Z1)); I2 = I3 * math.sqrt(3) / 2
    I1 = 3 * V * 1000 / math.sqrt(3) / abs(2 * Z1 + Z0); I1r = 3 * V * 1000 / math.sqrt(3) / abs(2 * Z1 + Z0 + 3 * 40)
    cc.append((nm, l, I3, I2, I1, I1r))
Imax = K["dem"]["MD_anio20_kW"] / (math.sqrt(3) * V * 0.9)
Iph = float(math.ceil(2 * Imax / 10) * 10); Ign = float(max(5, round(0.25 * Iph)))
d = nuevo("VOLUMEN IX – ANÁLISIS DE FLUJO DEL SISTEMA")
caratula_volumen(d, "VOLUMEN IX", "ANÁLISIS DE FLUJO DEL SISTEMA Y COORDINACIÓN DE PROTECCIONES")
p(d, "ESTUDIO DE FLUJO DE CARGA, CORTOCIRCUITO Y COORDINACIÓN DE PROTECCIONES", bold=True, align="C")
nota(d, f"Estudio preliminar con datos de diseño: la potencia de cortocircuito, la relación X/R y la impedancia homopolar en el punto de diseño, así como los ajustes "
        f"de las protecciones aguas arriba, deben ser proporcionados por {CONC.rstrip('.')}. El estudio definitivo se ejecuta en obra (partida 1.02) con el modelo del "
        "sistema eléctrico de la concesionaria (DIgSILENT u otro).")
h(d, "1. Objetivo y alcances")
p(d, "Calcular el flujo de carga con la incorporación de la línea, las corrientes de cortocircuito en los puntos principales y los ajustes preliminares del reconectador "
     "y la selección de fusibles, verificando la coordinación entre dispositivos.")
h(d, "2. Descripción del proyecto")
h(d, "2.1 Características eléctricas de las instalaciones", 2)
datos(d, [("Tensión", "22,9 kV, 3ø, 60 Hz"), ("Longitud", f"{fmt(L,3)} km, AAAC {SECCION} mm²")] +
        [(f"Derivación {x['nombre']}", f"{x['estructura']}, progresiva {fmt(x['prog']/1000,3)} km") for x in DER] +
        [("Protección en el arranque", "Reconectador 38 kV, 630 A, 12,5 kA"), ("Seccionamiento", f"Cut-out 38 kV con fusibles K ({fusibles_txt(C)})")])
h(d, "2.2 Parámetros eléctricos de la línea", 2)
tabla(d, ["Parámetro", "Valor", "Fuente"], [("R1 a 20 °C", f"{fmt(c70['R20'],3)} Ω/km", "RD 018"), ("X1", f"{fmt(K['elec']['X1'],4)} Ω/km", "Anexo 8"),
                                            ("R0", f"{fmt(z0.real,3)} Ω/km", f"Carson (ρ = {_n(PAT['rho'])} Ω·m)"), ("X0", f"{fmt(z0.imag,3)} Ω/km", f"Carson: De = {fmt(De,0)} m; Ds = {fmt(Ds3,3)} m")],
      widths=[4.0, 4.0, 7.6])
h(d, "2.3 Demanda", 2)
_pts = [(x["id"], x["nombre"]) for x in DER] + [("FIN", FINN)]
tabla(d, ["Año"] + [f"MD {nm} (kW)" for _, nm in _pts] + ["MD total (kW)"],
      [(a, *[fmt(g[g.punto == pid].MD_kW.sum(), 1) for pid, _ in _pts], fmt(g.MD_kW.sum(), 1)) for a, g in dem.groupby("anio") if (a - dem.anio.min()) % 5 == 0],
      widths=[2.0] + [11.6 / (len(_pts) + 1)] * (len(_pts) + 1))
h(d, "3. Información utilizada")
bullets(d, [f"Potencia de cortocircuito trifásica en el punto de diseño: {Scc:.0f} MVA – SUPUESTO (confirmar con {CONC}).", f"Relación X/R de la fuente: {XR:g} – SUPUESTO.",
            "Impedancia homopolar de la fuente igual a la de secuencia positiva (transformador de potencia con neutro sólido) – SUPUESTO.",
            "Herramienta: hoja de cálculo propia (archivo Excel adjunto, con fórmulas) – método de componentes simétricas."])
h(d, "4. Flujo de carga")
tabla(d, ["Nodo", "Tensión año 0 (p.u.)", f"Tensión año {A20} (p.u.)", f"Carga año {A20} (kW)"],
      [(E0, "1,000", "1,000", fmt(K['dem']['MD_anio20_kW'], 0))] +
      [(b[0].split(" ")[0], fmt(1 - nd["dV_pct"] / 100 * K['dem']['MD_anio0_kW'] / K['dem']['MD_anio20_kW'], 4), fmt(1 - nd["dV_pct"] / 100, 4),
        fmt(b[2]["P20"] if b[2] else C["Pfin"], 0)) for b, nd in zip(NODOS[1:], el["nodos"])],
      titulo="Perfil de tensiones (tensión en el arranque = 1,00 p.u.)", widths=[3.0, 4.0, 4.0, 4.0])
p(d, f"Las tensiones se mantienen dentro de ±5 % (NTCSER). La corriente máxima al año {A20} es {fmt(Imax,1)} A y las pérdidas {fmt(K['elec']['PJ'],1)} kW.")
h(d, "5. Cortocircuito")
tabla(d, ["Nodo", "Dist. (km)", "Icc 3ø (A)", "Icc 2ø (A)", "Icc 1ø (A)", "Icc 1ø Rf = 40 Ω (A)"],
      [(nm, fmt(l, 3), fmt(i3, 0), fmt(i2, 0), fmt(i1, 0), fmt(i1r, 0)) for nm, l, i3, i2, i1, i1r in cc], widths=[5.0, 1.8, 2.0, 2.0, 2.0, 2.8])
p(d, f"La sección mínima por cortocircuito ({fmt(el['S_min_cc'],1)} mm² para 0,2 s) es menor que {SECCION} mm². El reconectador (12,5 kA) y los cut-out (≥ 8 kA) superan la corriente "
     f"máxima de falla ({fmt(cc[0][2],0)} A).")
h(d, "6. Coordinación del sistema de protecciones")
h(d, "6.1 Dispositivos a coordinarse", 2)
bullets(d, [f"Protección de la red de {CONC} aguas arriba (dato pendiente).", f"Reconectador en {E0} (funciones 50/51, 50N/51N, 51SEF, 79).",
            "Fusibles tipo K en " + lista([f"la derivación a {x['nombre']} ({x['fus']} K)" for x in DER] + [f"la llegada a {FINN} ({C['fus_fin']} K)"]) + "."])
h(d, "6.2 Ajustes de sobrecorriente de fases del reconectador", 2)
p(d, f"Corriente de arranque Ip = 2 × Imax = 2 × {fmt(Imax,1)} ≈ {Iph:.0f} A; se verifica Icc 2ø mínima en el extremo ({fmt(cc[-1][3],0)} A) ≥ 2·Ip = {2*Iph:.0f} A: {'CUMPLE' if cc[-1][3] >= 2 * Iph else 'NO CUMPLE – revisar ajustes'}.")
tabla(d, ["Función", "Ajuste", "Curva", "Observación"], [("51 – fase, operación rápida", f"{Iph:.0f} A", "IEC NI, TMS 0,05", "Ahorro de fusibles (fuse saving)"),
                                                       ("51 – fase, operación lenta", f"{Iph:.0f} A", "IEC VI, TMS 0,20", "Coordina por encima de los fusibles " + lista(sorted({f"{k} K" for k in [C['fus_fin']] + [x['fus'] for x in DER]}, key=lambda z: -int(z.split()[0])))),
                                                       ("50 – fase instantánea", "1 200 A", "–", "Solo primer disparo"), ("79 – recierre", "2 rápidas + 2 lentas", "–", "Tiempos muertos 2 s – 10 s – 15 s")],
      titulo="Resumen de ajustes de fases (preliminar)", widths=[4.6, 2.8, 3.2, 5.0])
h(d, "6.3 Ajustes de sobrecorriente de tierra del reconectador", 2)
p(d, f"Ign = {Ign:.0f} A (≈ 25 % de Ip); se verifica Icc 1ø con Rf = 40 Ω en el extremo ({fmt(cc[-1][5],0)} A) ≥ 1,5·Ign: {'CUMPLE' if cc[-1][5] >= 1.5 * Ign else 'NO CUMPLE'}. Tierra sensible (51SEF): 5 A, 5 s.")
tabla(d, ["Función", "Ajuste", "Curva"], [("51N – tierra", f"{Ign:.0f} A", "IEC NI, TMS 0,10"), ("51SEF – tierra sensible", "5 A", "Tiempo definido 5 s")],
      titulo="Resumen de ajustes de tierra (preliminar)", widths=[6.0, 4.0, 5.6])
h(d, "6.4 Selección de fusibles", 2)
tabla(d, ["Ubicación", f"I carga año {A20} (A)", "Fusible", "Criterio"],
      [(f"Derivación {x['nombre']} ({x['estructura']})", fmt(x["I20"], 1), f"{x['fus']} K", "≥ 1,5 × I carga; coordina con el reconectador") for x in DER] +
      [(f"Llegada {FINN} ({EF})", fmt(C["Ifin"], 1), f"{C['fus_fin']} K", "≥ 1,5 × I carga; MMT > curva rápida del reconectador"),
       (f"Seccionamiento del reconectador ({E0})", fmt(Imax, 1), f"{C['fus_arr']} K", "Respaldo y aislamiento para mantenimiento")], widths=[5.0, 3.0, 2.0, 5.6])
h(d, "7. Conclusiones")
bullets(d, ["La línea opera dentro de los límites de tensión y pérdidas al año 20.", "Las capacidades de interrupción de los equipos superan las corrientes de falla calculadas.",
            f"Los ajustes son preliminares: se validarán con los datos de {CONC} en el estudio de coordinación de la obra (partida 1.02)."])
proyectista(d)
d.save(OUT / "VOL. IX ANALISIS DE FLUJO Y COORDINACION DE PROTECCIONES.docx")
# libro Excel del cortocircuito (fórmulas)
wb = libro(); ws = hoja(wb, "CORTOCIRCUITO", [44, 10, 14, 12, 30])
r = cab(ws, "VOLUMEN IX – CÁLCULO DE CORTOCIRCUITO (componentes simétricas)", ncol=5)
def dd(desc, sim, val, uni, fte, fmt_=None, entrada=True):
    global r
    ref = dato(ws, r, desc, sim, val, uni, fte, fmt=fmt_, entrada=entrada); r += 1; return ref
V_ = dd("Tensión nominal", "V", V, "kV", ""); S_ = dd("Potencia de cortocircuito en el punto de diseño", "Scc", Scc, "MVA", f"SUPUESTO – confirmar con {CONC}")
XR_ = dd("Relación X/R de la fuente", "X/R", XR, "–", "SUPUESTO"); Zs = dd("Impedancia de la fuente |Zs| = V²/Scc", "Zs", f"={V_}^2/{S_}", "Ω", "", "0.0000", False)
Rs_ = dd("Rs = Zs/√(1+(X/R)²)", "Rs", f"={Zs}/SQRT(1+{XR_}^2)", "Ω", "", "0.0000", False); Xs_ = dd("Xs = Rs·X/R", "Xs", f"={Rs_}*{XR_}", "Ω", "", "0.0000", False)
r1 = dd("R1 de la línea", "r1", c70["R20"], "Ω/km", "RD 018"); x1 = dd("X1 de la línea", "x1", round(K["elec"]["X1"], 5), "Ω/km", "Anexo 8")
rho = dd("Resistividad del terreno", "ρ", PAT["rho"], "Ω·m", "SUPUESTO"); Dee = dd("Profundidad equivalente De = 658,5·√(ρ/f)", "De", f"=658.5*SQRT({rho}/{SIS['f']})", "m", "", "0.0", False)
Dsr = dd("Radio medio geométrico del grupo Ds = (GMR·DMG²)^(1/3)", "Ds", round(Ds3, 5), "m", "Anexo 8", "0.00000", False)
r0 = dd("R0 = r1 + 3·0,0592", "r0", f"={r1}+3*0.0592", "Ω/km", "Carson", "0.0000", False); x0 = dd("X0 = 3·0,1736·log(De/Ds)", "x0", f"=3*0.1736*LOG10({Dee}/{Dsr})", "Ω/km", "Carson", "0.0000", False)
RF = dd("Resistencia de falla (mínima corriente)", "Rf", 40, "Ω", "Criterio")
r += 1
fila(ws, r, ["Nodo", "L (km)", "Icc 3ø (A)", "Icc 1ø (A)", "Icc 1ø con Rf (A)"], font=FB, fill=AZ); r += 1
for nm, l in nodos:
    Z1 = f"COMPLEX({Rs_}+B{r}*{r1},{Xs_}+B{r}*{x1})"; Z0 = f"COMPLEX({Rs_}+B{r}*{r0},{Xs_}+B{r}*{x0})"
    fila(ws, r, [nm, round(l, 3), f"={V_}*1000/(SQRT(3)*IMABS({Z1}))", f"=3*{V_}*1000/SQRT(3)/IMABS(IMSUM(IMPRODUCT(2,{Z1}),{Z0}))",
                 f"=3*{V_}*1000/SQRT(3)/IMABS(IMSUM(IMPRODUCT(2,{Z1}),{Z0},COMPLEX(3*{RF},0)))"], fmts=[None, "0.000", "0", "0", "0"]); r += 1
wb.save(OUT / "VOL. IX CORTOCIRCUITO.xlsx")

# =========================================================================================== VOL VIII
d = nuevo("VOLUMEN VIII – GEOLOGÍA Y GEOTECNIA")
caratula_volumen(d, "VOLUMEN VIII", "ESTUDIO DE GEOLOGÍA Y GEOTECNIA, DISEÑO DE CIMENTACIONES")
nota(d, "Este volumen contiene la evaluación de gabinete y los términos de referencia del estudio de mecánica de suelos. No se han ejecutado calicatas ni ensayos de "
        "laboratorio; por ello no se reportan resultados de campo. Los parámetros de suelo empleados en el diseño (Anexo 5 y 7 del Vol. VI) son supuestos que deben "
        "confirmarse antes de la ejecución.")
h(d, "1. Memoria descriptiva")
h(d, "1.1 Ubicación y objetivos", 2)
p(d, f"Corredor de {fmt(L,1)} km entre {INI} y {FINN}, en {txt('region_natural').lower()} ({fmt(el['cota_min'],0)} – {fmt(el['cota_max'],0)} m s.n.m.). "
     "Objetivos: caracterizar de forma preliminar los suelos de fundación, identificar peligros geológicos y definir los estudios de campo necesarios.")
h(d, "2. Evaluación de gabinete")
bullets(d, [("Geomorfología y suelos esperados: ", txt("geologia") + " El perfil del trazado se presenta en el Vol. VII (planos PP)."),
            ("Peligros: ", txt("peligros", "inundación o anegamiento en depresiones, erosión, heladas y sismicidad; la zonificación sísmica se verificará con la Norma E.030.")),
            ("Cartografía de referencia: ", f"carta geológica nacional del INGEMMET ({txt('cuadrangulo_ingemmet', 'cuadrángulo correspondiente al área del proyecto')}) a consultar por el especialista.")])
h(d, "3. Términos de referencia del estudio de mecánica de suelos (EMS)")
tabla(d, ["Actividad", "Alcance mínimo"], [("Calicatas", f"1 por cada 1,0 km de línea y 1 en cada estructura especial (ángulo > 30°, anclaje, TS-3, equipos): ≈ {math.ceil(L) + int(E.armado.isin(['PA2-3','PR3-3','TS-3','PSER-3','DT-3','PTH-3']).sum())} calicatas de 2,5 m"),
                                          ("Ensayos estándar", "Granulometría, límites de Atterberg, humedad natural, clasificación SUCS (por calicata)"),
                                          ("Ensayos especiales", "Densidad natural, corte directo o triaxial UU (≥ 6 muestras), contenido de sulfatos, cloruros y sales solubles"),
                                          ("Nivel freático", "Registro en cada calicata y época del año"),
                                          ("Resistividad del terreno", "Método Wenner (a = 1, 2, 4 m) en cada estructura con equipos y cada 1 km"),
                                          ("Entregables", "Perfiles estratigráficos, capacidad portante y lateral admisibles, ángulo de fricción, recomendación de cimentación y de concreto (tipo de cemento)")],
      widths=[4.2, 11.4])
h(d, "4. Parámetros de diseño de cimentaciones adoptados (a validar)")
tabla(d, ["Parámetro", "Valor adoptado", "Uso"], [("Capacidad lateral admisible del terreno compactado", "2,1 daN/cm²", "Anexo 5 – Sulzberger"),
                                                 ("Capacidad portante admisible", "1,0 daN/cm²", "Anexo 5 – presión vertical"), ("Peso unitario del relleno", "1 500 kg/m³", "Anexo 7 – bloque de anclaje"),
                                                 ("Ángulo de fricción interna", "23°", "Anexo 7"), ("Coeficiente de fricción", "0,5", "Anexo 7")], widths=[6.6, 3.4, 5.6])
h(d, "5. Diseño de cimentaciones")
_cm = K["cim"]
p(d, "Postes empotrados L/10 + 0,60 m con solado de 0,10 m y relleno de concreto ciclópeo f'c = 100 kg/cm² + 30 % de piedra mediana (lámina LD-LP-11); retenidas con "
     f"bloque de anclaje en excavación de 0,80 × 0,80 × 2,00 m (lámina LD-LP-08). Volúmenes por poste: 12 m – excavación {fmt(_cm['ve'][0],3)} m³, concreto {fmt(_cm['vc'][0],2)} m³; "
     f"13 m – {fmt(_cm['ve'][2],3)} m³ y {fmt(_cm['vc'][2],2)} m³.")
h(d, "6. Conclusiones y recomendaciones")
bullets(d, ["Ejecutar el EMS antes del inicio de obra y ajustar el diámetro de cimentación si la capacidad lateral medida es menor que 1,0 daN/cm².",
            "En suelos con nivel freático alto, usar cemento tipo MS o V según la agresividad medida y drenaje perimetral.", "Medir la resistividad para definir el número de varillas de PAT."])
proyectista(d)
d.save(OUT / "VOL. VIII ESTUDIO DE GEOLOGIA Y GEOTECNIA.docx")

# =========================================================================================== VOL X
for quien, tit in (("EJECUTOR", "REQUERIMIENTO MÍNIMO DEL EJECUTOR DE OBRA"), ("SUPERVISOR", "REQUERIMIENTO MÍNIMO DEL SUPERVISOR DE OBRA")):
    d = nuevo(f"VOLUMEN X – {tit}")
    caratula_volumen(d, "VOLUMEN X", tit)
    nota(d, "Requerimientos propuestos con base en expedientes similares de electrificación rural; la Entidad los ajustará a las bases estándar vigentes del OSCE y a la Ley de Contrataciones del Estado.")
    h(d, "1. Requerimientos mínimos")
    if quien == "EJECUTOR":
        h(d, "1.1 Del ejecutor de obra", 2)
        p(d, "Persona natural o jurídica inscrita en el Registro Nacional de Proveedores como ejecutor de obras, con especialidad en obras electromecánicas, y con capacidad máxima de "
             "contratación no menor al valor referencial.")
        h(d, "1.2 Experiencia en la especialidad", 2)
        p(d, f"Monto facturado acumulado equivalente a una (1) vez el valor referencial (S/ {fmt(K['pres']['VR'])}) en la ejecución de obras similares durante los diez años anteriores. "
             "Obras similares: construcción, mejoramiento o ampliación de líneas primarias o redes primarias en media tensión (10 a 33 kV).")
        h(d, "1.3 Personal profesional clave", 2)
        tabla(d, ["Cargo", "Profesión", "Experiencia mínima"], [("Ingeniero residente de obra", "Ingeniero electricista o mecánico electricista, colegiado y habilitado",
                                                                  "36 meses como residente, supervisor o inspector en obras similares"),
                                                                 ("Especialista en seguridad y salud en el trabajo", "Ingeniero colegiado y habilitado",
                                                                  "24 meses como responsable de seguridad en obras de construcción o electromecánicas")], widths=[4.4, 5.4, 5.8])
        h(d, "1.4 Otro personal", 2)
        bullets(d, ["Técnico electricista capataz (24 meses en montaje de líneas).", "Topógrafo (12 meses en replanteo de líneas)."])
        h(d, "1.5 Equipamiento estratégico", 2)
        tabla(d, ["Equipo", "Cantidad"], [("Camión grúa de 6 t (mínimo)", 1), ("Camioneta 4x4", 2), ("Winche de tendido 3 t y freno hidráulico", "1 juego"), ("Juego de poleas de tendido", 20),
                                          ("Dinamómetro", 1), ("Estación total con GPS", 1), ("Telurómetro", 1), ("Megóhmetro 5 kV", 1), ("Equipos de comunicación portátiles", 4),
                                          ("Mezcladora de concreto 9 p³", 1)], widths=[11.0, 4.0])
    else:
        h(d, "1.1 Del supervisor de obra", 2)
        p(d, "Persona natural o jurídica inscrita en el RNP como consultor de obras en la especialidad de obras electromecánicas, categoría acorde al valor referencial.")
        h(d, "1.2 Experiencia en la especialidad", 2)
        p(d, "Monto facturado acumulado equivalente a una (1) vez el valor referencial de la supervisión en supervisión de obras similares (líneas y redes primarias).")
        h(d, "1.3 Personal profesional clave", 2)
        tabla(d, ["Cargo", "Profesión", "Experiencia mínima"], [("Supervisor de obra (jefe de supervisión)", "Ingeniero electricista o mecánico electricista, colegiado y habilitado",
                                                                  "36 meses como supervisor, inspector o residente en obras similares")], widths=[4.4, 5.4, 5.8])
        h(d, "1.4 Equipamiento", 2)
        bullets(d, ["Camioneta 4x4 doble cabina.", "Equipo de cómputo con software CAD y de oficina.", "GPS navegador y cámara fotográfica.", "Telurómetro y megóhmetro (verificación de pruebas)."])
    proyectista(d)
    d.save(OUT / f"VOL. X REQUERIMIENTO MINIMO {quien}.docx")

# =========================================================================================== VOL XI
RIESGOS = [("R-01", f"Demora en la factibilidad de suministro y fijación del punto de diseño por {CONC}", "Externo", 0.5, 0.8, "Evitar", "Entidad",
            "Gestionar la factibilidad antes de la convocatoria"),
           ("R-02", "Diferencias entre las cotas del DEM y la topografía real (reubicación de estructuras)", "Técnico", 0.5, 0.4, "Mitigar", "Contratista",
            "Replanteo e ingeniería de detalle (partida 1.01) antes de excavar"),
           ("R-03", "Oposición de propietarios / falta de autorizaciones de paso en la faja de servidumbre", "Social", 0.5, 0.8, "Mitigar", "Entidad",
            "Talleres informativos y gestión temprana de servidumbre"),
           ("R-04", "Hallazgos arqueológicos durante las excavaciones", "Externo", 0.3, 0.8, "Mitigar", "Entidad / contratista", "Plan de Monitoreo Arqueológico y CIRA"),
           ("R-05", "Incremento de precios de materiales importados (aluminio, equipos)", "Económico", 0.5, 0.4, "Transferir", "Contratista", "Fórmula polinómica de reajuste"),
           ("R-06", "Suelos con nivel freático alto o baja capacidad portante", "Técnico", 0.3, 0.4, "Mitigar", "Contratista", "EMS previo; cimentación especial"),
           ("R-07", txt("riesgo_climatico", "Lluvias intensas en la temporada de lluvias que paralicen trabajos"), "Climático", 0.5, 0.2, "Aceptar", "Contratista", "Programar excavaciones en época seca"),
           ("R-08", "Accidentes por trabajos en altura y cercanía a redes energizadas", "Seguridad", 0.3, 0.8, "Mitigar", "Contratista", "Plan SST, ATS, permisos de trabajo y bloqueos"),
           ("R-09", "Demora en la entrega del reconectador (importado)", "Logístico", 0.5, 0.4, "Mitigar", "Contratista", "Orden de compra en el primer mes")]
d = nuevo("VOLUMEN XI – ANEXOS")
caratula_volumen(d, "VOLUMEN XI", "ANEXOS", SEPAR_XI := ["Gestión de riesgos", "Panel fotográfico", "Cotizaciones", "Datos pendientes"])
h(d, "Anexo XI-1: Informe de gestión de riesgos en la planificación de la ejecución de obra")
p(d, "Se aplica la Directiva de gestión de riesgos en la planificación de la ejecución de obras (OSCE): identificación, análisis cualitativo (probabilidad × impacto), "
     "respuesta y asignación. Los formatos editables F-1, F-2 y F-3 se adjuntan en Excel.")
tabla(d, ["Código", "Riesgo", "Tipo", "P", "I", "P×I", "Respuesta", "Responsable"],
      [(c, ds, t, f"{pp:.1f}", f"{ii:.1f}", f"{pp*ii:.2f}", rsp, rs) for c, ds, t, pp, ii, rsp, rs, _ in RIESGOS], widths=[1.4, 6.0, 1.8, 0.9, 0.9, 1.1, 1.7, 2.0], size=8)
p(d, "Escalas: probabilidad 0,1 (muy baja) – 0,9 (muy alta); impacto 0,05 – 0,80. Prioridad alta si P×I ≥ 0,18; moderada 0,05 – 0,18; baja < 0,05.", size=10)
h(d, "Anexo XI-2: Panel fotográfico")
_fotos = [f"{E0} – punto de diseño"] + [f"{x['estructura']} – derivación {x['nombre']}" for x in DER] + \
         [f"{c} – cruce de vía" for c in (pd.read_csv(W / "cruces.csv").cruce_id.tolist() if ncruces else [])[:3]] + [f"{EF} – llegada {FINN}"]
nota(d, "PENDIENTE: no se dispone de registro fotográfico de campo del trazado. El contratista o la Entidad completará el panel con fotografías georreferenciadas de: "
        + lista(_fotos) + " y estructuras de ángulo, siguiendo el formato adjunto.")
tabla(d, ["N.°", "Ubicación (estructura / progresiva)", "Coordenadas UTM", "Descripción", "Fecha"], [(i, e, "", "", "") for i, e in enumerate(_fotos, 1)],
      widths=[1.0, 5.0, 3.6, 4.4, 1.6])
h(d, "Anexo XI-3: Cotizaciones de materiales")
nota(d, f"PENDIENTE: el presupuesto usa los precios de referencia del catálogo del repositorio convertidos al tipo de cambio indicado ({TC_FUENTE}) y estimados del proyectista. "
        "Se adjunta el cuadro comparativo en Excel para registrar como mínimo tres cotizaciones vigentes por ítem principal.")
h(d, "Anexo XI-4: Datos de campo y documentos externos pendientes")
PEND = [("Factibilidad de suministro y fijación del punto de diseño", CONC, "Confirmar punto de conexión, Scc, X/R, Z0 y ajustes aguas arriba (Vol. IX)"),
        ("Levantamiento topográfico de la poligonal y perfil", "Contratista / Entidad", "Las cotas actuales provienen del DEM Copernicus GLO-30"),
        ("Estudio de mecánica de suelos", "Especialista geotécnico", "Valida Cp, qa, γ, θ y agresividad (Vol. VIII)"),
        ("Medición de resistividad del terreno", "Contratista", "Define varillas por PAT (Anexo 3)"),
        ("CIRA o Plan de Monitoreo Arqueológico aprobado", "Ministerio de Cultura", "Requisito previo a excavaciones"),
        ("Instrumento de gestión ambiental (DIA/FTA) aprobado", "Autoridad ambiental competente", "Requisito de certificación ambiental"),
        ("Autorizaciones de paso y servidumbre", "Entidad / propietarios", "Faja de 11 m"),
        ("Cotizaciones vigentes (mínimo tres por ítem)", "Proveedores", "Actualizar BP del Vol. V"),
        ("Pesos y catálogos de postes del fabricante", "Fabricante", "Verificación de pandeo y cimentación"),
        ("Registros de calidad de suministro (SAIFI/SAIDI) y demanda real", CONC, "Antecedentes y validación del estudio de mercado"),
        ("Panel fotográfico de campo", "Entidad / contratista", "Anexo XI-2"),
] + [(f"Diseño de la red primaria de {x['nombre']} (derivación)", "Proyecto complementario", f"Define el tiro de la derivación sobre la estructura {x['estructura']}") for x in DER] + [
        ("Habilidad profesional del proyectista", "Proyectista", "No se ha consignado número de colegiatura, firma ni sello: deben ser incorporados por el proyectista")]
tabla(d, ["Dato / documento", "Responsable", "Uso / observación"], PEND, widths=[6.0, 3.6, 6.0], size=8.5)
proyectista(d)
d.save(OUT / "VOL. XI ANEXOS.docx")
# formatos de riesgos y cotizaciones (Excel)
wb = libro(); ws = hoja(wb, "F-1 IDENTIFICACION", [8, 50, 12, 9, 9, 10, 12, 16, 40], apaisado=True)
r = cab(ws, "FORMATO F-1: IDENTIFICACIÓN Y ANÁLISIS CUALITATIVO DE RIESGOS", ncol=9)
fila(ws, r, ["Código", "Descripción del riesgo", "Tipo", "Probabilidad", "Impacto", "P × I", "Prioridad", "Respuesta / responsable", "Acción"], font=FB, fill=AZ); r += 1
for c, ds, t, pp, ii, rsp, rs, acc in RIESGOS:
    fila(ws, r, [c, ds, t, pp, ii, f"=D{r}*E{r}", f'=IF(F{r}>=0.18,"ALTA",IF(F{r}>=0.05,"MODERADA","BAJA"))', f"{rsp} – {rs}", acc]); r += 1
ws2 = hoja(wb, "F-2 MATRIZ P-I", [14] + [12] * 5)
r = cab(ws2, "FORMATO F-2: MATRIZ DE PROBABILIDAD E IMPACTO", ncol=6)
hr = r; fila(ws2, r, ["P \\ I", 0.05, 0.10, 0.20, 0.40, 0.80], font=FB, fill=AZ); r += 1
for pp in (0.9, 0.7, 0.5, 0.3, 0.1):
    fila(ws2, r, [pp] + [f"=$A{r}*{CLx}${hr}" for CLx in "BCDEF"], fmts=[None] + ["0.000"] * 5); r += 1
ws3 = hoja(wb, "F-3 ASIGNACION", [8, 50, 22, 40])
r = cab(ws3, "FORMATO F-3: ASIGNACIÓN DE RIESGOS", ncol=4)
fila(ws3, r, ["Código", "Riesgo", "Asignado a", "Respuesta"], font=FB, fill=AZ); r += 1
for c, ds, t, pp, ii, rsp, rs, acc in RIESGOS:
    fila(ws3, r, [c, ds, rs, f"{rsp}: {acc}"]); r += 1
wb.save(OUT / "VOL. XI FORMATOS GESTION DE RIESGOS.xlsx")
wb = libro(); ws = hoja(wb, "COTIZACIONES", [8, 60, 7, 14, 14, 14, 14, 14], apaisado=True)
r = cab(ws, "CUADRO COMPARATIVO DE COTIZACIONES (precios sin IGV, puestos en almacén de obra)", ncol=8)
fila(ws, r, ["Código", "Descripción", "Und.", "Precio BP (S/)", "Cotización 1", "Cotización 2", "Cotización 3", "Promedio / adoptado"], font=FB, fill=AZ); r += 1
for m in MATD.values():
    pbp = round(m[3] * TC, 2) if m[3] is not None else m[4]
    fila(ws, r, [m[0], m[1], m[2], pbp, None, None, None, f'=IF(COUNT(E{r}:G{r})>0,AVERAGE(E{r}:G{r}),D{r})'], fmts=[None, None, None, "#,##0.00", "#,##0.00", "#,##0.00", "#,##0.00", "#,##0.00"]); r += 1
wb.save(OUT / "VOL. XI CUADRO COMPARATIVO DE COTIZACIONES.xlsx")
print("ok p14", [(c[0], round(c[2]), round(c[4]), round(c[5])) for c in cc])
