"""Anexos 4 (CMC), 5 (cimentaciones), 6 (CME + verificación por estructura), 7 (retenidas) y 9 (planilla),
con fórmulas vivas y formato del modelo. Uso: python p05_anexos_mecanicos.py WORK OUTDIR"""
import json, math, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from params import *
from xlhelp import *
from catalogo import cable_ret

W = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
R = json.load(open(W / "resultados.json"))
E = pd.read_csv(W / "planilla_estructuras.csv")
CHK = pd.read_csv(W / "verificacion_vanos.csv")
G = 9.80665
c70 = COND[70]
HIPS = [("H1 EDS inicial", "Esfuerzo cada día inicial"), ("H2 EDS final", "Esfuerzo cada día final (referencia)"),
        ("H3 Temp. mínima", "Mínima temperatura"), ("H4 Viento máximo", "Máxima velocidad de viento"),
        ("H5 Hielo", "Máxima carga de hielo"), ("H5b Hielo + viento", "Hielo + viento reducido"),
        ("H6 Temp. máxima", "Máxima temperatura (flecha máxima, incluye CREEP)")]
PESO_POSTE = {"12/300": 1000, "12/400": 1150, "13/400": 1350}   # kg – SUPUESTO catálogo típico; verificar con fabricante


def cbrt(x): return f"(SIGN({x})*ABS({x})^(1/3))"


def sigma_formula(A, B):
    q = f"(2*{A}^3/27-{B})"; dl = f"({q}^2/4-{A}^6/729)"
    return (f"=IF({dl}>=0,{cbrt(f'(-{q}/2+SQRT({dl}))')}+{cbrt(f'(-{q}/2-SQRT({dl}))')},"
            f"2*ABS({A})/3*COS(ACOS(-27*{q}/(2*ABS({A})^3))/3))-{A}/3")


def cmc_sheet(wb, nombre, vanos, titulo):
    """Hoja de cálculo mecánico del conductor (ecuación de cambio de estado, RD 018 4.5) con fórmulas."""
    ws = hoja(wb, nombre, [9] + [10.5] * 40, apaisado=True)
    r = cab(ws, titulo, "CONDUCTOR AAAC 70 mm² – ECUACIÓN DE CAMBIO DE ESTADO: σ2²·[σ2 + A] = B", ncol=36)
    titulo_seccion(ws, r, "CARACTERÍSTICAS DEL CONDUCTOR Y PARÁMETROS DE CÁLCULO", ncol=12); r += 1
    ref = {}
    datos = [("S", "Sección real (19 hilos de 2,10 mm)", "=19*PI()*(2.1/2)^2", "mm²", "RD 018 / ASTM B399"),
             ("D", "Diámetro exterior", c70["D"], "mm", "RD 018 Cuadro 4.2"),
             ("m", "Masa unitaria", c70["kg_m"], "kg/m", "RD 018"),
             ("wc", "Peso unitario  wc = m·g", f"=__m*{G}", "N/m", ""),
             ("sr", "Esfuerzo de rotura", SIGMA_R, "N/mm²", "RD 018"),
             ("Ef", "Módulo de elasticidad final", E_FINAL, "N/mm²", "RD 018"),
             ("al", "Coeficiente de dilatación lineal", ALFA, "1/°C", "RD 018"),
             ("edsf", "EDS final", EDS_FINAL, "p.u. UTS", "RD 018 4.3 (sin amortiguadores)"),
             ("edsi", "EDS inicial", EDS_INI, "p.u. UTS", "RD 018 4.3"),
             ("sref", "Esfuerzo de referencia (H2)  σref = EDSf·σr", "=__edsf*__sr", "N/mm²", ""),
             ("tref", "Temperatura de referencia (H2)", T_MEDIA, "°C", "SENAMHI (media anual)"),
             ("Tr", "Tiro de rotura  Tr = σr·S", "=__sr*__S", "N", ""),
             ("smax", "Esfuerzo máximo admisible (60 % UTS)", "=0.6*__sr", "N/mm²", "RD 018 4.3"),
             ("K", "Constante de presión de viento (> 3000 m s.n.m.)", K_VIENTO, "–", "CNE-S 2011, Regla 250.C"),
             ("rh", "Densidad del hielo", RHO_HIELO, "kg/m³", "CNE-S 2011")]
    for k, (key, desc, val, uni, fte) in enumerate(datos):
        rr = r + k
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=4)
        put(ws, f"A{rr}", desc); put(ws, f"E{rr}", key, al=CEN)
        for cc in "BCD": ws[f"{cc}{rr}"].border = BOX
        ref[key] = f"$F${rr}"
        put(ws, f"F{rr}", val, font=FBL if not str(val).startswith("=") else F, fill=AM if not str(val).startswith("=") else None,
            fmt="0.0000" if key in ("S", "wc", "edsf", "edsi") else ("0.000000" if key == "al" else "0.00"))
        put(ws, f"G{rr}", uni); ws.merge_cells(start_row=rr, start_column=8, end_row=rr, end_column=12); put(ws, f"H{rr}", fte)
    for k in range(len(datos)):
        c = ws[f"F{r+k}"]
        if isinstance(c.value, str):
            for key, rf in ref.items(): c.value = c.value.replace(f"__{key}", rf)
    r += len(datos) + 1
    titulo_seccion(ws, r, "HIPÓTESIS DE CÁLCULO (RD 018-2003-EM/DGE 4.4 y CNE-S 2011 Área 1)", ncol=12); r += 1
    fila(ws, r, ["Hip.", "Descripción", None, None, "t (°C)", "V (m/s)", "e (mm)", "pv (Pa)", "wh (N/m)", "wv (N/m)", "w (N/m)", "wr/wc"], font=FB, fill=AZ)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4); r += 1
    hrow = {}
    for k, (h, desc) in enumerate(HIPS):
        x = HIP[h]; rr = r + k; hrow[h] = rr
        fila(ws, rr, [h.split()[0], desc, None, None, x["t"], x["V"], x["hielo"],
                      f"={ref['K']}*F{rr}^2",
                      f"={ref['rh']}*{G}*PI()*((({ref['D']}+2*G{rr})/1000)^2-({ref['D']}/1000)^2)/4",
                      f"=H{rr}*({ref['D']}+2*G{rr})/1000",
                      f"=SQRT(({ref['wc']}+I{rr})^2+J{rr}^2)", f"=K{rr}/{ref['wc']}"],
             fmts=[None, None, None, None, "0.0", "0.0", "0.0", "0.0", "0.000", "0.000", "0.000", "0.000"])
        ws.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=4)
        for cc in "EFG": ws[f"{cc}{rr}"].fill = AM; ws[f"{cc}{rr}"].font = FBL
    r += len(HIPS) + 1
    # tabla principal
    titulo_seccion(ws, r, "RESULTADOS POR VANO: σ (N/mm²), tiro horizontal TH (N), tiro en el apoyo TA (N), flecha f (m), % UTS", ncol=36); r += 1
    c0 = 2; cols = {}
    hdr1 = ["Vano"]; hdr2 = ["d (m)"]
    for h, _ in HIPS:
        cols[h] = c0 + len(hdr1) - 1
        hdr1 += [h.split()[0] + " " + " ".join(h.split()[1:]), None, None, None, None]; hdr2 += ["σ", "TH", "TA", "f", "%UTS"]
    hdr1 += ["TH máx (H3,H4,H5,H5b)", "% UTS máx", "≤ 60 %"]; hdr2 += ["N", "%", ""]
    fila(ws, r, hdr1, font=FB, fill=AZ); fila(ws, r + 1, hdr2, font=FB, fill=AZ)
    for h in cols:
        ws.merge_cells(start_row=r, start_column=cols[h], end_row=r, end_column=cols[h] + 4)
    naux = len(hdr1) + 2               # columnas auxiliares A,B (a la derecha)
    aux = {}
    k = 0
    for h, _ in HIPS:
        if h in ("H1 EDS inicial", "H2 EDS final"): continue
        aux[h] = naux + 2 * k; k += 1
        ws.cell(r, aux[h]).value = f"A ({h.split()[0]})"; ws.cell(r, aux[h] + 1).value = f"B ({h.split()[0]})"
        ws.cell(r, aux[h]).font = FI; ws.cell(r, aux[h] + 1).font = FI
    r += 2; r0 = r
    wref = {h: f"$K${hrow[h]}" for h in hrow}; tref = {h: f"$E${hrow[h]}" for h in hrow}
    for d in vanos:
        ws.cell(r, 1).value = d; ws.cell(r, 1).border = BOX; ws.cell(r, 1).alignment = CEN; ws.cell(r, 1).font = FB
        for h, _ in HIPS:
            c = cols[h]; sC = CL(c)
            if h == "H1 EDS inicial":
                fs = f"={ref['edsi']}*{ref['sr']}"
            elif h == "H2 EDS final":
                fs = f"={ref['sref']}"
            else:
                A, B = CL(aux[h]), CL(aux[h] + 1)
                ws[f"{A}{r}"] = (f"={ref['Ef']}*{wref['H2 EDS final']}^2*$A{r}^2/(24*{ref['S']}^2*{ref['sref']}^2)-{ref['sref']}"
                                 f"+{ref['al']}*{ref['Ef']}*({tref[h]}-{ref['tref']})")
                ws[f"{B}{r}"] = f"={ref['Ef']}*{wref[h]}^2*$A{r}^2/(24*{ref['S']}^2)"
                ws[f"{A}{r}"].font = FI; ws[f"{B}{r}"].font = FI
                fs = sigma_formula(f"{A}{r}", f"{B}{r}")
            vals = [fs, f"={sC}{r}*{ref['S']}", f"={CL(c+1)}{r}+{wref[h]}*{CL(c+3)}{r}",
                    f"={wref[h]}*$A{r}^2/(8*{CL(c+1)}{r})", f"={CL(c+2)}{r}/{ref['S']}/{ref['sr']}"]
            fila(ws, r, vals, col0=c, fmts=["0.00", "0", "0", "0.00", "0.0%"])
        cm = c0 + 35
        th = ",".join(f"{CL(cols[h]+1)}{r}" for h in ("H3 Temp. mínima", "H4 Viento máximo", "H5 Hielo", "H5b Hielo + viento"))
        pc = ",".join(f"{CL(cols[h]+4)}{r}" for h, _ in HIPS)
        fila(ws, r, [f"=MAX({th})", f"=MAX({pc})", f'=IF({CL(cm+1)}{r}<=0.6,"OK","EXCEDE")'], col0=cm, fmts=["0", "0.0%", None])
        r += 1
    ws.freeze_panes = ws.cell(r0, 2)
    info = {"r0": r0, "r1": r - 1, "Tcol": CL(c0 + 35), "ref": ref, "cols": cols, "hrow": hrow}
    return ws, info


# =====================================================================================  ANEXO 4
wb = libro()
ws, info4 = cmc_sheet(wb, "CMC_AAAC-70", list(range(10, 401, 10)), "ANEXO 4: CÁLCULO MECÁNICO DE CONDUCTORES")
# Tabla de templado
wt = hoja(wb, "TABLA DE TEMPLADO", [10] + [11] * 8, apaisado=True)
r = cab(wt, "TABLA DE TEMPLADO – CONDUCTOR AAAC 70 mm² (flechas de tendido con compensación de CREEP: t − 10 °C)", ncol=9)
nota(wt, r, "Flecha de tendido f (m) y tiro horizontal (N) en función del vano regulador y de la temperatura del conductor al momento del "
     "tendido. Se calcula desde el estado de referencia H2 (EDS final 15 % a la temperatura media) con peso propio; la temperatura de "
     "cálculo se reduce 10 °C para compensar el asentamiento (CREEP) – RD 018 4.4.", ncol=9, h=40); r += 2
temps = list(range(-5, 31, 5)); vt = list(range(60, 301, 20))
ref = info4["ref"]; S_ = f"'CMC_AAAC-70'!{ref['S']}"; sref = f"'CMC_AAAC-70'!{ref['sref']}"; Ef = f"'CMC_AAAC-70'!{ref['Ef']}"
al = f"'CMC_AAAC-70'!{ref['al']}"; wc_ = f"'CMC_AAAC-70'!{ref['wc']}"; tr_ = f"'CMC_AAAC-70'!{ref['tref']}"
blocks = {}
for bi, (tit, kind) in enumerate([("FLECHA DE TENDIDO f (m)", "f"), ("TIRO HORIZONTAL DE TENDIDO (N)", "T"), ("aux A", "A"), ("aux B", "B"), ("aux σ", "s")]):
    titulo_seccion(wt, r, tit if kind in ("f", "T") else f"Cálculo auxiliar: {tit[4:]}", ncol=9, fill=AZ2 if kind in ("f", "T") else None); r += 1
    fila(wt, r, ["Vano (m)"] + [f"{t} °C" for t in temps], font=FB, fill=AZ if kind in ("f", "T") else None); r += 1
    blocks[kind] = r
    for d in vt:
        wt.cell(r, 1).value = d; wt.cell(r, 1).border = BOX; wt.cell(r, 1).alignment = CEN
        r += 1
    r += 1
for i, d in enumerate(vt):
    for j, t in enumerate(temps):
        col = CL(2 + j)
        rA, rB, rS, rF, rT = (blocks[k] + i for k in ("A", "B", "s", "f", "T"))
        wt[f"{col}{rA}"] = f"={Ef}*{wc_}^2*$A{rA}^2/(24*{S_}^2*{sref}^2)-{sref}+{al}*{Ef}*(({t}-10)-{tr_})"
        wt[f"{col}{rB}"] = f"={Ef}*{wc_}^2*$A{rB}^2/(24*{S_}^2)"
        wt[f"{col}{rS}"] = sigma_formula(f"{col}{rA}", f"{col}{rB}")
        wt[f"{col}{rF}"] = f"={wc_}*$A{rF}^2/(8*{col}{rS}*{S_})"; wt[f"{col}{rF}"].number_format = "0.00"
        wt[f"{col}{rT}"] = f"={col}{rS}*{S_}"; wt[f"{col}{rT}"].number_format = "0"
        for rr in (rF, rT): wt[f"{col}{rr}"].border = BOX; wt[f"{col}{rr}"].alignment = CEN; wt[f"{col}{rr}"].font = F
        for rr in (rA, rB, rS): wt[f"{col}{rr}"].font = FI; wt[f"{col}{rr}"].number_format = "0.000"
wb.save(OUT / "Anexo 4 CMC.xlsx")

# =====================================================================================  ANEXO 6 (CME)
wb = libro()
wd = hoja(wb, "DATOS", [48, 10, 12, 10, 34])
r = cab(wd, "ANEXO 6: CÁLCULO MECÁNICO DE ESTRUCTURAS, RETENIDAS Y CRUCETAS – DATOS GENERALES", ncol=5)
fila(wd, r, ["Descripción", "Símbolo", "Valor", "Unidad", "Fuente / observación"], font=FB, fill=AZ); r += 1
D6 = {}
def dd(key, desc, sim, val, uni, fte, fmt=None, entrada=True):
    global r
    D6[key] = "DATOS!" + dato(wd, r, desc, sim, val, uni, fte, fmt=fmt, entrada=entrada); r += 1
dd("pv", "Presión de viento sobre conductor y poste (H4: 29 m/s, K = 0,455)", "pv", f"={K_VIENTO}*29^2", "Pa", "CNE-S 2011 Regla 250.C", fmt="0.00", entrada=False)
dd("Dc", "Diámetro del conductor", "Dc", c70["D"] / 1000, "m", "")
dd("wc", "Peso unitario del conductor", "wc", f"={c70['kg_m']}*{G}", "N/m", "", fmt="0.0000", entrada=False)
dd("wa", "Peso de aisladores y ferretería por estructura", "Wa", W_AISL, "N", "SUPUESTO")
dd("wh", "Carga de montaje (operario con herramientas)", "Wh", W_HOMBRE, "N", "RD 018 5.6")
dd("dsup", "Posición de la fase superior respecto a la cabeza del poste (− = encima)", "d1", ARM["d_sup"], "m", "Armados LD-LP")
dd("dinf", "Posición de las fases inferiores bajo la cabeza del poste", "d2", ARM["d_inf"], "m", "Armados LD-LP")
dd("bc", "Brazo de excentricidad de cargas verticales", "bc", 1.0, "m", "Media cruceta")
dd("dp", "Distancia del punto de aplicación de la fuerza bajo la punta", "dp", 0.15, "m", "RD 018 5.3")
dd("rot", "Carga de rotura del cable de retenida (A°G° SM 10 mm)", "Tr", RET["rotura_N"], "N", "ASTM A475")
dd("fsr", "Factor de seguridad del cable de retenida", "FSr", RET["FS"], "–", "RD 018")
dd("ang", "Ángulo de la retenida con el eje del poste", "φ", RET["angulo_deg"], "°", "Láminas LD-LP")
dd("Ec", "Módulo de elasticidad del concreto", "Ec", 18584, "N/mm²", "Modelo (189 503 kg/cm²)")
dd("pin", "Resistencia en voladizo del aislador PIN 56-4", "Rv", 13300, "N", "ANSI C29.6")
dd("sml", "Carga mecánica especificada del aislador polimérico 36 kV", "SML", 70000, "N", "EETT")
dd("crT", "Cruceta FºGº: carga de rotura transversal (en el eje de la cruceta)", "T", 12000, "N", "EETT (expediente de referencia: 1 200 kg)")
dd("crF", "Cruceta FºGº: carga de rotura longitudinal", "F", 6000, "N", "EETT (expediente de referencia: 600 kg)")
dd("crV", "Cruceta FºGº: carga de rotura vertical por fase", "V", 3000, "N", "EETT (expediente de referencia: 300 kg)")
r += 1
titulo_seccion(wd, r, "POSTES DE CONCRETO ARMADO CENTRIFUGADO", ncol=5); r += 1
fila(wd, r, ["Poste", "L (m)", "Q trabajo (daN)", "Do (cm)", "Db (cm)"], font=FB, fill=AZ)
wd.cell(r, 6).value = "Peso (kg)"; wd.cell(r, 6).font = FB; wd.cell(r, 6).fill = AZ; wd.cell(r, 6).border = BOX
wd.column_dimensions["F"].width = 10; r += 1
P0 = r
for p, x in POSTES.items():
    fila(wd, r, [p, x["L"], x["Q"], x["Do"], x["Db"], PESO_POSTE[p]]); r += 1
PT = f"DATOS!$A${P0}:$F${r-1}"
nota(wd, r + 1, "Pesos de poste: valores típicos de catálogo (SUPUESTO) – el fabricante adjudicado los confirmará. Q: carga de trabajo "
     "a 0,15 m de la punta con factor de seguridad 2 (RD 018 5.2).", ncol=5, h=30)
wsC, infoC = cmc_sheet(wb, "CMC", list(range(20, 401, 5)), "CÁLCULO MECÁNICO DEL CONDUCTOR (tabla de tiros para las estructuras)")
TC_ = f"CMC!${infoC['Tcol']}${infoC['r0']}:${infoC['Tcol']}${infoC['r1']}"; DC_ = f"CMC!$A${infoC['r0']}:$A${infoC['r1']}"
def tinterp(dref):
    m = f"MATCH({dref},{DC_},1)"
    return f"(INDEX({TC_},{m})+({dref}-INDEX({DC_},{m}))*(INDEX({TC_},{m}+1)-INDEX({TC_},{m}))/5)"
SINR = f"SIN(RADIANS({D6['ang']}))"; CAP = f"({D6['rot']}/{D6['fsr']})"

# --- hojas de prestaciones por armado
ARMS = [("PS1-3", "12/300", 5, "susp"), ("PA1-3", "12/400", 30, "ang"), ("PA2-3", "12/400", 60, "ang_t"), ("TS-3", "12/400", 5, "ang_t"),
        ("PR3-3", "12/400", 0, "anc"), ("DT-3", "12/400", 0, "susp_t"), ("PSER-3", "12/400", 0, "term"), ("PTH-3", "12/400", 0, "term")]
from catalogo import ARM_DESC
VVs = list(range(40, 241, 20))
for arm, poste, ang, kind in ARMS:
    ws = hoja(wb, arm, [52, 10] + [10] * len(VVs), apaisado=True)
    nc = 2 + len(VVs)
    r = cab(ws, f"CÁLCULO MECÁNICO DE ESTRUCTURAS – ARMADO {arm}", ARM_DESC[arm].upper(), ncol=nc)
    titulo_seccion(ws, r, "DATOS DEL ARMADO Y DEL POSTE", ncol=nc); r += 1
    def ln(desc, uni, vals, fmt="0.00", bold=False):
        global r
        fila(ws, r, [desc, uni] + vals, font=FB if bold else F, fmts=[None, None] + [fmt] * len(vals)); r += 1
        return r - 1
    rp = ln("Poste", "", [poste] + [None] * (len(VVs) - 1)); ws.merge_cells(start_row=rp, start_column=3, end_row=rp, end_column=nc)
    ws.cell(rp, 3).fill = AM; ws.cell(rp, 3).font = FBL
    PS = f"$C${rp}"
    rL = ln("Longitud del poste L", "m", [f"=VLOOKUP({PS},{PT},2,0)"]); rQ = ln("Carga de trabajo en la punta Q", "daN", [f"=VLOOKUP({PS},{PT},3,0)"])
    rDo = ln("Diámetro en la punta Do", "cm", [f"=VLOOKUP({PS},{PT},4,0)"]); rDb = ln("Diámetro en la base Db", "cm", [f"=VLOOKUP({PS},{PT},5,0)"])
    rWp = ln("Peso del poste", "N", [f"=VLOOKUP({PS},{PT},6,0)*{G}"], "0")
    rhe = ln("Empotramiento he = L/10 + 0,60", "m", [f"=C{rL}/10+0.6"]); rhl = ln("Altura libre hl = L − he", "m", [f"=C{rL}-C{rhe}"])
    rh1 = ln("Altura de la fase superior h1 = hl − d1", "m", [f"=C{rhl}-{D6['dsup']}"]); rh2 = ln("Altura de las fases inferiores h2 = hl − d2", "m", [f"=C{rhl}-{D6['dinf']}"])
    rSh = ln("Suma de alturas Σh = h1 + 2·h2", "m", [f"=C{rh1}+2*C{rh2}"])
    rDm = ln("Diámetro medio Dm = Do + (Db − Do)·hl/L", "cm", [f"=C{rDo}+(C{rDb}-C{rDo})*C{rhl}/C{rL}"])
    rang = ln("Ángulo de desvío de la línea α (máximo del armado)", "°", [ang]); ws.cell(rang, 3).fill = AM; ws.cell(rang, 3).font = FBL
    for rr in range(rL, rang + 1):
        if rr != rang and rr != rp: ws.merge_cells(start_row=rr, start_column=3, end_row=rr, end_column=4)
    titulo_seccion(ws, r, "I. ANÁLISIS DEL ESFUERZO DE TRABAJO DEL POSTE (hipótesis H4, viento máximo)", ncol=nc); r += 1
    rvv = ln("Vano viento", "m", VVs, "0", True)
    rvp = ln("Vano peso (1,5·vano viento)", "m", [f"=1.5*{CL(3+k)}{rvv}" for k in range(len(VVs))], "0")
    cl = [CL(3 + k) for k in range(len(VVs))]
    rT = ln("Tiro horizontal máximo por conductor (Tabla CMC, vano = vano viento)", "N", ["=" + tinterp(f"{c}{rvv}") for c in cl], "0")
    rMVC = ln("Momento por viento sobre conductores MVC = pv·Dc·VV·Σh·cos(α/2)", "N·m",
              [f"={D6['pv']}*{D6['Dc']}*{c}{rvv}*$C${rSh}*COS(RADIANS($C${rang}/2))" for c in cl], "0")
    if kind in ("anc", "term"):
        rMTC = ln("Momento por tiro de conductores MTC = T·Σh (desequilibrio total)", "N·m", [f"={c}{rT}*$C${rSh}" for c in cl], "0")
    else:
        rMTC = ln("Momento por tiro de conductores MTC = 2·T·Σh·sen(α/2)", "N·m", [f"=2*{c}{rT}*$C${rSh}*SIN(RADIANS($C${rang}/2))" for c in cl], "0")
    rMVP = ln("Momento por viento sobre el poste MVP = pv·hl²·(Dm + 2·Do)/600", "N·m", [f"={D6['pv']}*$C${rhl}^2*($C${rDm}+2*$C${rDo})/600" for c in cl], "0")
    rMCW = ln("Momento por cargas verticales excéntricas MCW = bc·(wc·VP + Wa + Wh)", "N·m", [f"={D6['bc']}*({D6['wc']}*{c}{rvp}+{D6['wa']}+{D6['wh']})" for c in cl], "0")
    rMRN = ln("Momento total en el empotramiento MRN", "N·m", [f"={c}{rMVC}+{c}{rMTC}+{c}{rMVP}+{c}{rMCW}" for c in cl], "0", True)
    rQN = ln("Fuerza equivalente en la punta QN = MRN/(hl − 0,15)", "daN", [f"={c}{rMRN}/($C${rhl}-{D6['dp']})/10" for c in cl], "0.0", True)
    rFS = ln("Factor de utilización QN/Q", "–", [f"={c}{rQN}/$C${rQ}" for c in cl], "0.00")
    ln("1.1 VERIFICACIÓN DEL POSTE SIN RETENIDA", "", [f'=IF({c}{rQN}<=$C${rQ},"OK","Use retenida")' for c in cl], "@", True)
    rI = ln("Momento de inercia I = π·de³·dp/64 (de: diámetro en empotramiento)", "cm⁴",
            [f"=PI()*(($C${rDo}+($C${rDb}-$C${rDo})*$C${rhl}/$C${rL}))^3*$C${rDo}/64" for c in cl], "0")
    rdef = ln("Deflexión en la punta δ = QN·hl³/(3·Ec·I)", "cm", [f"={c}{rQN}*10*($C${rhl}*100)^3/(3*{D6['Ec']}*100*{c}{rI})" for c in cl], "0.00")
    rdp = ln("Deflexión relativa δ/hl", "%", [f"={c}{rdef}/($C${rhl}*100)" for c in cl], "0.00%")
    ln("1.2 VERIFICACIÓN DE LA DEFLEXIÓN MÁXIMA (≤ 2,5 %, sin retenida)", "", [f'=IF({c}{rdp}<=0.025,"OK","Use retenida")' for c in cl], "@", True)
    titulo_seccion(ws, r, "II. RETENIDAS (toman el momento por tiro de conductores; el poste resiste viento y cargas verticales)", ncol=nc); r += 1
    rFh = ln("Fuerza horizontal equivalente a la altura media de conductores Fh = MTC/(Σh/3)", "N", [f"={c}{rMTC}/($C${rSh}/3)" for c in cl], "0")
    rTr = ln("Tiro en las retenidas Tret = Fh / sen φ", "N", [f"={c}{rFh}/{SINR}" for c in cl], "0")
    if kind in ("anc",):
        rn = ln("Número de retenidas (en ambos sentidos)", "u", [f"=2*MAX(1,CEILING(3*{c}{rT}/{SINR}/{CAP},1))" for c in cl], "0", True)
        rTu = ln("Tiro por retenida", "N", [f"=3*{c}{rT}/{SINR}/({c}{rn}/2)" for c in cl], "0")
    elif kind == "susp":
        rn = ln("Número de retenidas (solo si el poste no resiste)", "u", [f"=IF(AND({c}{rQN}>$C${rQ},{c}{rTr}>0),MAX(1,CEILING({c}{rTr}/{CAP},1)),0)" for c in cl], "0", True)
        rTu = ln("Tiro por retenida", "N", [f"=IF({c}{rn}=0,0,{c}{rTr}/{c}{rn})" for c in cl], "0")
    else:
        rn = ln("Número de retenidas", "u", [f"=IF({c}{rTr}>0,MAX(1,CEILING({c}{rTr}/{CAP},1)),0)" for c in cl], "0", True)
        rTu = ln("Tiro por retenida", "N", [f"=IF({c}{rn}=0,0,{c}{rTr}/{c}{rn})" for c in cl], "0")
    rFSr = ln("Factor de seguridad del cable de retenida", "–", [f'=IF({c}{rn}=0,"-",{D6["rot"]}/{c}{rTu})' for c in cl], "0.00")
    ln("VERIFICACIÓN DEL CABLE DE RETENIDA (FS ≥ 2)", "", [f'=IF({c}{rn}=0,"No requiere",IF({c}{rFSr}>={D6["fsr"]},"OK","Aumentar"))' for c in cl], "@", True)
    rQr = ln("Fuerza en la punta con retenida QNr = (MRN − MTC·[n>0])/(hl − 0,15)", "daN", [f"=({c}{rMRN}-IF({c}{rn}>0,{c}{rMTC},0))/($C${rhl}-{D6['dp']})/10" for c in cl], "0.0")
    ln("VERIFICACIÓN DEL POSTE CON RETENIDA", "", [f'=IF({c}{rQr}<=$C${rQ},"OK","Cambiar poste")' for c in cl], "@", True)
    titulo_seccion(ws, r, "III. VERIFICACIÓN AL PANDEO POR CARGAS VERTICALES (FS ≥ 2)", ncol=nc); r += 1
    rPcr = ln("Carga crítica de Euler Pcr = π²·Ec·I/(2·hl)²", "N", [f"=PI()^2*{D6['Ec']}*100*{c}{rI}/((2*$C${rhl}*100)^2)" for c in cl], "0")
    rWv = ln("Carga vertical total Wv = peso poste + 3·wc·VP + Wa + Wh + n·Tret·cos φ", "N",
             [f"=$C${rWp}+3*{D6['wc']}*{c}{rvp}+{D6['wa']}+{D6['wh']}+IF({c}{rn}>0,{c}{rn}*{c}{rTu}*COS(RADIANS({D6['ang']})),0)" for c in cl], "0")
    rFp = ln("Factor de seguridad al pandeo Pcr/Wv", "–", [f"={c}{rPcr}/{c}{rWv}" for c in cl], "0.00")
    ln("VERIFICACIÓN DEL PANDEO", "", [f'=IF({c}{rFp}>=2,"OK","Cambiar clase")' for c in cl], "@", True)
    titulo_seccion(ws, r, "IV. VERIFICACIÓN DE CRUCETA FºGº Y AISLADORES", ncol=nc); r += 1
    if kind in ("anc", "term", "ang_t", "susp_t"):
        rTc = ln("Carga transversal en la cruceta (tiro del conductor en el apoyo)", "N", [f"={c}{rT}*1.05" for c in cl], "0")
        ln("FS transversal de la cruceta (≥ 1,5)", "–", [f"={D6['crT']}/{c}{rTc}" for c in cl], "0.00")
        rins = ln("FS del aislador polimérico de suspensión SML/T (≥ 2,5)", "–", [f"={D6['sml']}/({c}{rT}*1.05)" for c in cl], "0.00")
    else:
        rTc = ln("Carga transversal por fase (resultante de ángulo + viento)", "N",
                 [f"=2*{c}{rT}*SIN(RADIANS($C${rang}/2))+{D6['pv']}*{D6['Dc']}*{c}{rvv}" for c in cl], "0")
        ln("FS transversal de la cruceta (≥ 1,5)", "–", [f"={D6['crT']}/{c}{rTc}" for c in cl], "0.00")
        rins = ln("FS del aislador PIN 56-4 en voladizo (≥ 2)", "–", [f"={D6['pin']}/{c}{rTc}" for c in cl], "0.00")
    rVc = ln("Carga vertical por fase (wc·VP + Wa/3 + Wh)", "N", [f"={D6['wc']}*{c}{rvp}+{D6['wa']}/3+{D6['wh']}" for c in cl], "0")
    ln("FS vertical de la cruceta (≥ 1,0 con carga de montaje)", "–", [f"={D6['crV']}/{c}{rVc}" for c in cl], "0.00")
    rLc = ln("Carga longitudinal por fase (desequilibrio 10 % del tiro)", "N", [f"=0.1*{c}{rT}" for c in cl], "0")
    ln("FS longitudinal de la cruceta (≥ 2)", "–", [f"={D6['crF']}/{c}{rLc}" for c in cl], "0.00")
    r += 1
    nota(ws, r, "Convención: los vanos de la fila 'Vano viento' cubren el rango de vanos de la línea (37 a 220 m). La verificación "
         "estructura por estructura, con los vanos reales del plantillado, está en la hoja VERIF_ESTRUCTURAS.", ncol=nc, h=30)

# --- verificación estructura por estructura
wv = hoja(wb, "VERIF_ESTRUCTURAS", [5, 8, 8, 7, 9, 6, 7, 7, 7, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 8, 8, 9, 8, 8, 9, 7, 8, 5, 7, 8, 8, 6, 6, 7, 8, 11, 8], apaisado=True)
r = cab(wv, "VERIFICACIÓN MECÁNICA ESTRUCTURA POR ESTRUCTURA (vanos reales del plantillado) – COHERENCIA CON LA PLANILLA",
        "Fórmulas idénticas a las de las hojas de armados; columnas AH–AJ comparan con la Planilla de Estructuras (Anexo 9)", ncol=37)
hdr = ["N.°", "Estruc.", "Armado", "Poste", "Progr. (m)", "α (°)", "VV (m)", "VP (m)", "dmax (m)", "L", "Q daN", "Do", "Db", "he", "hl", "h1", "h2",
       "Σh", "Dm", "T (N)", "MVC", "MTC", "MVP", "MCW", "MRN", "QN daN", "Tret (N)", "n ret", "QNr daN", "Poste", "T/ret (N)", "FS cable", "Cable",
       "n ret planilla", "QNr planilla", "Coherencia", "Arranque PIN"]
fila(wv, r, hdr, font=FB, fill=AZ); wv.row_dimensions[r].height = 30; r += 1
v0 = r
for x in E.itertuples():
    rr = r
    L = f"VLOOKUP(D{rr},{PT},"
    vals = [x.N, x.estructura, x.armado, x.poste, round(x.progresiva_m, 2), round(x.angulo_deg, 3), round(x.vano_viento_m, 3),
            round(x.vano_peso_m, 3), round(x.vano_max_adyacente_m, 3),
            f"={L}2,0)", f"={L}3,0)", f"={L}4,0)", f"={L}5,0)", f"=J{rr}/10+0.6", f"=J{rr}-N{rr}",
            f"=O{rr}-{D6['dsup']}", f"=O{rr}-{D6['dinf']}", f"=P{rr}+2*Q{rr}", f"=L{rr}+(M{rr}-L{rr})*O{rr}/J{rr}",
            "=" + tinterp(f"I{rr}"),
            f"={D6['pv']}*G{rr}*{D6['Dc']}*R{rr}*COS(RADIANS(F{rr}/2))",
            f'=IF(OR(C{rr}="PSER-3",C{rr}="PTH-3",C{rr}="PR3-3"),T{rr}*R{rr},2*T{rr}*R{rr}*SIN(RADIANS(F{rr}/2)))',
            f"={D6['pv']}*O{rr}^2*(S{rr}+2*L{rr})/600", f"={D6['bc']}*({D6['wc']}*H{rr}+{D6['wa']}+{D6['wh']})",
            f"=U{rr}+V{rr}+W{rr}+X{rr}", f"=Y{rr}/(O{rr}-{D6['dp']})/10",
            f"=IF(V{rr}>0,V{rr}/(R{rr}/3)/{SINR},0)",
            (f'=IF(C{rr}="PS1-3",IF(AND(Z{rr}>K{rr},AA{rr}>0),MAX(1,CEILING(AA{rr}/{CAP},1)),0),'
             f'IF(OR(C{rr}="PR3-3",C{rr}="PA3-3"),2*MAX(1,CEILING(3*T{rr}/{SINR}/{CAP},1)),'
             f'IF(AA{rr}>0,MAX(1,CEILING(AA{rr}/{CAP},1)),0)))'),
            f"=(Y{rr}-IF(AB{rr}>0,V{rr},0))/(O{rr}-{D6['dp']})/10", f'=IF(AC{rr}<=K{rr},"OK","NO")',
            f'=IF(AB{rr}=0,0,IF(OR(C{rr}="PR3-3",C{rr}="PA3-3"),3*T{rr}/{SINR}/(AB{rr}/2),AA{rr}/AB{rr}))',
            f'=IF(AB{rr}=0,"-",{D6["rot"]}/AE{rr})', f'=IF(AB{rr}=0,"-",IF(AF{rr}>={D6["fsr"]},"OK","NO"))',
            int(x.n_retenidas), round(x.QN_con_ret_daN, 2),
            f'=IF(AND(AB{rr}=AH{rr},ABS(AC{rr}-AI{rr})<0.5,AD{rr}="OK",AK{rr}="OK"),"COHERENTE","REVISAR")',
            f'=IF(AND(H{rr}<0,OR(C{rr}="PS1-3",C{rr}="PA1-3")),"NO","OK")']
    fila(wv, rr, vals, fmts=[None, None, None, None, "0.0", "0.0", "0.0", "0.0", "0.0", "0", "0", "0", "0", "0.00", "0.00", "0.00", "0.00",
                             "0.00", "0.0", "0", "0", "0", "0", "0", "0", "0.0", "0", "0", "0.0", None, "0", "0.00", None, "0", "0.0", None, None])
    r += 1
v1 = r - 1
fila(wv, r + 1, ["", "Resumen", None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                 None, None, None, None, f"=MAX(Z{v0}:Z{v1})", None, f"=SUM(AB{v0}:AB{v1})", f"=MAX(AC{v0}:AC{v1})",
                 f'=COUNTIF(AD{v0}:AD{v1},"OK")', None, None, None, f"=SUM(AH{v0}:AH{v1})", None,
                 f'=COUNTIF(AJ{v0}:AJ{v1},"COHERENTE")&" de "&COUNTA(B{v0}:B{v1})'], font=FB)
wv.freeze_panes = wv.cell(v0, 5)
wb.save(OUT / "Anexo 6 CME_CMR_ALUMINIO_AAAC.xlsx")
json.dump({"v0": v0, "v1": v1}, open(W / "verif_rows.json", "w"))

# =====================================================================================  ANEXO 5 (cimentaciones)
wb = libro()
ws = hoja(wb, "RESUMEN", [30, 12, 12, 12, 12, 12, 12, 12, 12, 12])
r = cab(ws, "ANEXO 5: CÁLCULO DE CIMENTACIÓN DE POSTES – MÉTODO DE SULZBERGER", ncol=10)
nota(ws, r, "Equilibrio: F − R1 + R2 = 0;  F·(H + 2h/3) − R1·(h/3) − R2·(2h/9) = 0  ⇒  R1 = F·(9H + 8h)/(5h);  R2 = R1 − F. "
     "Presiones laterales: σ1 = 1,5·R1/(De·h); σ2 = 3·R2/(De·h). Se compara con la capacidad admisible lateral del terreno compactado "
     "(SUPUESTO 2,1 daN/cm², igual al expediente de referencia, a confirmar con el Estudio de Mecánica de Suelos).", ncol=10, h=55); r += 2
fila(ws, r, ["Descripción", "Unid."] + list(POSTES.keys()), font=FB, fill=AZ); r += 1
rs = {}
def lr(key, desc, uni, vals, fmt="0.00", entrada=False):
    global r
    fila(ws, r, [desc, uni] + vals, fmts=[None, None] + [fmt] * 3)
    if entrada:
        for k in range(3): ws.cell(r, 3 + k).fill = AM; ws.cell(r, 3 + k).font = FBL
    rs[key] = r; r += 1
cols = ["C", "D", "E"]
lr("L", "Longitud del poste L", "m", [x["L"] for x in POSTES.values()], entrada=True)
lr("Q", "Carga de trabajo Cw", "daN", [x["Q"] for x in POSTES.values()], "0", entrada=True)
lr("Db", "Diámetro en la base D", "cm", [x["Db"] for x in POSTES.values()], "0.0", entrada=True)
lr("Do", "Diámetro en la punta d", "cm", [x["Do"] for x in POSTES.values()], "0.0", entrada=True)
lr("Wp", "Peso del poste Wp", "N", [PESO_POSTE[p] * G for p in POSTES], "0", entrada=True)
lr("De", "Diámetro de la cimentación (excavación rellena con concreto ciclópeo) De", "cm", [80, 80, 90], "0", entrada=True)
lr("hs", "Espesor del solado", "m", [0.10, 0.10, 0.10], entrada=True)
lr("Cp", "Capacidad admisible lateral del terreno compactado", "daN/cm²", [2.1, 2.1, 2.1], entrada=True)
lr("qa", "Capacidad portante admisible (fondo de cimentación)", "daN/cm²", [1.0, 1.0, 1.0], entrada=True)
lr("h", "Profundidad de empotramiento h = L/10 + 0,60", "m", [f"={c}{rs['L']}/10+0.6" for c in cols])
lr("H", "Altura útil H = L − h", "m", [f"={c}{rs['L']}-{c}{rs['h']}" for c in cols])
lr("F", "Fuerza horizontal de trabajo F = 10·Cw", "N", [f"=10*{c}{rs['Q']}" for c in cols], "0")
lr("R1", "R1 = F·(9H + 8h)/(5h)", "N", [f"={c}{rs['F']}/(5*{c}{rs['h']})*(9*{c}{rs['H']}+8*{c}{rs['h']})" for c in cols], "0")
lr("R2", "R2 = R1 − F", "N", [f"={c}{rs['R1']}-{c}{rs['F']}" for c in cols], "0")
lr("s1", "σ1 = 1,5·R1/(De·h)", "daN/cm²", [f"=1.5*{c}{rs['R1']}/({c}{rs['De']}*{c}{rs['h']}*100)/10" for c in cols], "0.000")
lr("s2", "σ2 = 3·R2/(De·h)", "daN/cm²", [f"=3*{c}{rs['R2']}/({c}{rs['De']}*{c}{rs['h']}*100)/10" for c in cols], "0.000")
lr("v1", "Verificación σ1, σ2 ≤ Cp", "", [f'=IF(AND({c}{rs["s1"]}<={c}{rs["Cp"]},{c}{rs["s2"]}<={c}{rs["Cp"]}),"OK","AMPLIAR De")' for c in cols], "@")
lr("Wt", "Carga vertical: poste + conductores (3 × 220 m) + armado + 2 retenidas al 100 % (cos φ)", "N",
   [f"={c}{rs['Wp']}+3*1.775*220+600+1000+2*{RET['rotura_N']}/{RET['FS']}*COS(RADIANS({RET['angulo_deg']}))" for c in cols], "0")
lr("A3", "Área de apoyo sobre el solado (π·De²/4)", "cm²", [f"=PI()*{c}{rs['De']}^2/4" for c in cols], "0")
lr("sv", "Presión vertical Wt/A3", "daN/cm²", [f"={c}{rs['Wt']}/{c}{rs['A3']}/10" for c in cols], "0.000")
lr("v2", "Verificación presión vertical ≤ qa", "", [f'=IF({c}{rs["sv"]}<={c}{rs["qa"]},"OK","AMPLIAR SOLADO")' for c in cols], "@")
r += 1
titulo_seccion(ws, r, "DIMENSIONES DE EXCAVACIÓN Y CIMENTACIÓN (para metrados)", ncol=10); r += 1
lr("pe", "Profundidad de excavación = h + solado", "m", [f"={c}{rs['h']}+{c}{rs['hs']}" for c in cols])
lr("ve", "Volumen de excavación π·De²/4·pe", "m³", [f"=PI()*({c}{rs['De']}/100)^2/4*{c}{rs['pe']}" for c in cols], "0.000")
lr("vs", "Volumen de solado π·De²/4·hs", "m³", [f"=PI()*({c}{rs['De']}/100)^2/4*{c}{rs['hs']}" for c in cols], "0.000")
lr("dE", "Diámetro del poste en el nivel del terreno", "cm", [f"={c}{rs['Db']}-({c}{rs['Db']}-{c}{rs['Do']})*{c}{rs['h']}/{c}{rs['L']}" for c in cols], "0.0")
lr("vp", "Volumen del poste enterrado (tronco de cono)", "m³", [f"=PI()*{c}{rs['h']}/12*(({c}{rs['Db']}/100)^2+({c}{rs['Db']}/100)*({c}{rs['dE']}/100)+({c}{rs['dE']}/100)^2)" for c in cols], "0.000")
lr("vc", "Volumen de concreto ciclópeo (excav. − solado − poste)", "m³", [f"={c}{rs['ve']}-{c}{rs['vs']}-{c}{rs['vp']}" for c in cols], "0.000")
lr("ee", "Volumen de material excedente a eliminar (esponjamiento 1,25)", "m³", [f"=1.25*{c}{rs['vp']}" for c in cols], "0.000")
r += 1
nota(ws, r, "Concreto ciclópeo f'c = 100 kg/cm² + 30 % de piedra mediana; solado de concreto f'c = 100 kg/cm² de 0,10 m. "
     "En terrenos con nivel freático alto o baja capacidad portante (bofedales, ribera lacustre) el EMS definirá cimentación especial.", ncol=10, h=30)
wb.save(OUT / "Anexo 5 Calculo Cimentacion.xlsx")
json.dump(rs, open(W / "cim_rows.json", "w"))

# =====================================================================================  ANEXO 7 (retenidas)
wb = libro()
ws = hoja(wb, "RI", [56, 12, 14, 12, 30])
r = cab(ws, "ANEXO 7: CÁLCULO MECÁNICO DE RETENIDAS Y DEL BLOQUE DE ANCLAJE – RETENIDA INCLINADA (RI)", ncol=5)
fila(ws, r, ["Descripción", "Símbolo", "Valor", "Unidad", "Fuente / observación"], font=FB, fill=AZ); r += 1
def d7(desc, sim, val, uni, fte, fmt=None, entrada=True):
    global r
    ref = dato(ws, r, desc, sim, val, uni, fte, fmt=fmt, entrada=entrada); r += 1; return ref
Tmax = float(pd.Series([x.T_retenida_N / x.n_retenidas if x.armado not in ("PR3-3", "PA3-3") else
                        3 * x.T_cond_N / math.sin(math.radians(37)) / (x.n_retenidas / 2)
                        for x in E.itertuples() if x.n_retenidas > 0]).max())
TT = d7("Tiro máximo de trabajo por retenida (máximo de la hoja VERIF_ESTRUCTURAS del Anexo 6)", "Tw", round(Tmax, 1), "N", "Anexo 6", "0.0")
TR = d7("Carga de rotura del cable A°G° grado Siemens-Martin 10 mm, 7 hilos", "Tr", RET["rotura_N"], "N", "ASTM A475")
FSC = d7("Factor de seguridad del cable", "FS", f"={TR}/{TT}", "–", "≥ 2 (RD 018)", "0.00", False)
d7("Verificación del cable", "", f'=IF({FSC}>=2,"CUMPLE","NO CUMPLE")', "", "", entrada=False)
AV = d7("Sección de la varilla de anclaje 16 mm Ø", "Av", "=PI()*16^2/4", "mm²", "", "0.0", False)
FY = d7("Esfuerzo de fluencia del acero de la varilla", "fy", 250, "N/mm²", "ASTM A36 – SUPUESTO")
FSV = d7("Factor de seguridad de la varilla a la rotura del cable  Av·fy/Tr", "FSv", f"={AV}*{FY}/{TR}", "–", "≥ 1,0", "0.00", False)
r += 1
titulo_seccion(ws, r, "BLOQUE DE ANCLAJE – FUERZAS QUE SE OPONEN A LA TRACCIÓN (método del expediente de referencia)", ncol=5); r += 1
PHI = d7("Ángulo del cable de retenida con la vertical", "φ", RET["angulo_deg"], "°", "Lámina LD-LP-08")
HB = d7("Profundidad de excavación", "Hb", 2.0, "m", "Modelo")
DD = d7("Largo de la excavación (en el plano de la retenida)", "D", 0.80, "m", "Ampliado respecto al expediente de referencia (0,70 m) para FS ≥ 2")
FF = d7("Ancho de la excavación (transversal)", "f", 0.80, "m", "Ampliado respecto al expediente de referencia (0,70 m)")
LB = d7("Bloque de concreto armado: largo × ancho × alto", "Vb", "=0.5*0.5*0.2", "m³", "0,50 × 0,50 × 0,20 m", "0.000", False)
GR = d7("Densidad del relleno compactado", "γ", 1500, "kg/m³", "Modelo (terreno arcilloso compactado)")
GC = d7("Densidad del concreto armado", "γc", 2400, "kg/m³", "")
TH = d7("Ángulo de fricción interna del suelo", "θ", 23, "°", "Modelo – a confirmar con EMS")
MU = d7("Coeficiente de fricción relleno – terreno natural", "μ", 0.5, "–", "Morales, Diseño en concreto armado (expediente de referencia)")
KA = d7("Coeficiente de empuje activo Ka = tg²(45° − θ/2)", "Ka", f"=TAN(RADIANS(45-{TH}/2))^2", "–", "", "0.0000", False)
WT = d7("Peso del relleno compactado Wt = γ·g·(D·f·Hb − Vb)", "Wt", f"={GR}*{G}*({DD}*{FF}*{HB}-{LB})", "N", "", "0", False)
WTC = d7("Componente de Wt en la dirección del cable  Wt·cos φ", "Wt'", f"={WT}*COS(RADIANS({PHI}))", "N", "", "0", False)
PB = d7("Peso del bloque Pb·cos φ", "Pb'", f"={GC}*{G}*{LB}*COS(RADIANS({PHI}))", "N", "", "0", False)
FR = d7("Rozamiento en las 4 caras  Fr = μ·½·Ka·γ·g·Hb²·(2D + 2f)", "ΣFr", f"={MU}*0.5*{KA}*{GR}*{G}*{HB}^2*(2*{DD}+2*{FF})", "N", "", "0", False)
FT = d7("Fuerza resistente total", "Fres", f"={WTC}+{PB}+{FR}", "N", "", "0", False)
FSB = d7("Factor de seguridad del bloque Fres/Tw", "FSb", f"={FT}/{TT}", "–", "≥ 2", "0.00", False)
d7("Verificación del bloque de anclaje", "", f'=IF({FSB}>=2,"CUMPLE","AMPLIAR EXCAVACIÓN")', "", "", entrada=False)
r += 1
titulo_seccion(ws, r, "EXCAVACIÓN DE RETENIDA (para metrados)", ncol=5); r += 1
VE = d7("Volumen de excavación por retenida D·f·Hb", "Ve", f"={DD}*{FF}*{HB}", "m³", "", "0.000", False)
VR = d7("Volumen de relleno compactado por retenida Ve − Vb", "Vr", f"={VE}-{LB}", "m³", "", "0.000", False)
r += 1
titulo_seccion(ws, r, "LONGITUD DE CABLE POR RETENIDA (para metrados)", ncol=5); r += 1
for p in POSTES:
    d7(f"Poste {p}: altura de amarre/cos φ + 2,0 m de amarres", "Lc", cable_ret(POSTES[p]["L"]), "m", "Catálogo de materiales", "0.0", False)
wb.save(OUT / "Anexo 7 Calculo Mecanico de Retenidas.xlsx")

# =====================================================================================  ANEXO 9 (planilla + distancias)
wb = libro()
ws = hoja(wb, "PLANILLA", [5, 8, 9, 11, 12, 8, 7, 7, 7, 7, 8, 8, 7, 7, 8, 30, 26], apaisado=True)
r = cab(ws, f"ANEXO 9: PLANILLA DE ESTRUCTURAS – LÍNEA PRIMARIA 22,9 kV (coordenadas UTM WGS 84, zona {ZONA_UTM})", ncol=17)
fila(ws, r, ["N.°", "Estruc.", "Progresiva (m)", "Este (m)", "Norte (m)", "Cota (m)", "Ángulo (°)", "Vano adel. (m)", "Vano viento (m)",
             "Vano peso (m)", "Armado", "Poste", "Retenida", "N.° ret.", "PAT", "Equipamiento", "Observaciones"], font=FB, fill=AZ)
ws.row_dimensions[r].height = 30; r += 1
for x in E.itertuples():
    fila(ws, r, [x.N, x.estructura, round(x.progresiva_m, 2), round(x.este, 2), round(x.norte, 2), round(x.cota_m, 2), round(x.angulo_deg, 2),
                 None if pd.isna(x.vano_adelante_m) else round(x.vano_adelante_m, 2), round(x.vano_viento_m, 2), round(x.vano_peso_m, 2),
                 x.armado, x.poste, x.tipo_retenida, int(x.n_retenidas), x.puesta_tierra, x.equipamiento if x.equipamiento != "-" else "",
                 x.observaciones if isinstance(x.observaciones, str) else ""],
         fmts=[None, None, "0.00", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00"]); r += 1
p1 = r - 1
r += 1
titulo_seccion(ws, r, "RESUMEN", ncol=17); r += 1
for lab, f in [("Estructuras", f"=COUNTA(B5:B{p1})"), ("Longitud (m)", f"=MAX(C5:C{p1})"), ("Vano medio (m)", f"=AVERAGE(H5:H{p1})"),
               ("Vano máximo (m)", f"=MAX(H5:H{p1})"), ("Vano mínimo (m)", f"=MIN(H5:H{p1})"), ("Retenidas", f"=SUM(N5:N{p1})")]:
    fila(ws, r, [None, lab, None, f], fmts=[None, None, None, "0.00"]); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3); r += 1
for a in sorted(E.armado.unique()):
    fila(ws, r, [None, f"Armado {a}", None, f'=COUNTIF(K5:K{p1},"{a}")']); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3); r += 1
for p in POSTES:
    fila(ws, r, [None, f"Poste {p}", None, f'=COUNTIF(L5:L{p1},"{p}")']); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3); r += 1
for p in ("PAT-1", "PAT-2"):
    fila(ws, r, [None, f"Puesta a tierra {p}", None, f'=COUNTIF(O5:O{p1},"{p}")']); ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3); r += 1
ws.freeze_panes = "C5"
w2 = hoja(wb, "DISTANCIAS", [18, 10, 12, 12, 12, 14, 14, 14], apaisado=False)
r = cab(w2, "VERIFICACIÓN DE DISTANCIAS DE SEGURIDAD POR VANO (RD 018 3.3 y 3.7)", ncol=8)
fila(w2, r, ["Vano", "d (m)", "Flecha H6 (m)", "Holgura mín. al terreno (m)", "Cumple terreno", "D horiz. req. (m)", "Separación (m)", "Cumple separación"], font=FB, fill=AZ)
w2.row_dimensions[r].height = 30; r += 1
c0 = r
for x in CHK.itertuples():
    fila(w2, r, [x.vano, round(x.d_m, 2), round(x.flecha_H6_m, 3), round(x.holgura_min_m, 3), f'=IF(D{r}>=0,"SÍ","NO")',
                 f"=0.0076*22.9*(1+1.25*({R['electrico']['cota_max']:.3f}-1000)/10000)+0.65*SQRT(C{r})",
                 ARM["sep_h"], f'=IF(F{r}<=G{r},"SÍ","NO")'], fmts=[None, "0.00", "0.000", "0.000", None, "0.000", "0.00", None]); r += 1
nota(w2, r + 1, "Holgura = distancia vertical del conductor más bajo a la flecha máxima (H6, 50 °C) sobre el perfil, menos la distancia mínima "
     "exigida (6,0 m general; 7,0 m en cruces de vías) y menos 0,30 m de margen por la precisión del modelo digital de elevación. "
     "D horizontal: 0,0076·U·Fc + 0,65·√f (RD 018 3.3).", ncol=8, h=45)
wb.save(OUT / "Anexo 9 PLANILLA DE ESTRUCTURAS.xlsx")
print("ok anexos 4,5,6,7,9")
