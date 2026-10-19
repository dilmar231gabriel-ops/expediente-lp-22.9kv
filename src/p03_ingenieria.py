"""Motor de cálculo: demanda, selección de conductor, cálculo mecánico (cambio de estado),
plantillado sobre el perfil, asignación de armados, postes, retenidas y puestas a tierra."""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
from shapely.geometry import LineString, Point
from pyproj import Transformer
sys.path.insert(0, str(Path(__file__).parent))
from params import *

W = Path(sys.argv[1])
G = 9.80665
to_ll = Transformer.from_crs(f"EPSG:{EPSG}", "EPSG:4326", always_xy=True)
meta = json.load(open(W / "trazado_meta.json"))
troncal = LineString(meta["vertices"])
L_km = troncal.length / 1000
DER = meta.get("derivaciones", [])                      # derivaciones: [{id, nombre, prog}]
PROG = {"FIN": None, **{d["id"]: d["prog"] for d in DER}}
deriv_progs = [d["prog"] for d in DER]
perfil = pd.read_csv(W / "perfil_troncal.csv")
PX, PZ = perfil.progresiva_m.to_numpy(), perfil.cota_m.to_numpy()
cruces = pd.read_csv(W / "cruces.csv")
cr_prog = cruces[cruces.tramo == "TRONCAL"].progresiva_m.to_numpy()
R = {}

# ------------------------------------------------------------------ 1. DEMANDA
M = MERCADO; anios = list(range(PROYECTO["anio_base"], PROYECTO["anio_base"] + PROYECTO["horizonte"] + 1))
filas = []
for c in M["cargas"]:
    viv2017 = c["pob2017"] / M["hab_viv"]
    for k, a in enumerate(anios):
        viv = viv2017 * (1 + M["tasa_viv"]) ** (a - 2017)
        ab = viv * M["coef_elec"]
        cu = M["cu_kwh_mes"] * (1 + M["tasa_cu"]) ** k
        e_dom = ab * cu * 12 / 1000                                     # MWh
        e_otros = e_dom * (M["pct_comercial"] + M["pct_general"] + M["pct_productivo"] + M["pct_ap"])
        e_tot = (e_dom + e_otros) * (1 + M["perd_dist"])
        md = e_tot * 1000 / (8760 * M["fc"])                            # kW
        filas.append({"carga": c["nombre"], "punto": c["punto"], "anio": a, "k": k, "viviendas": viv, "abonados": ab,
                      "cu_kwh_mes": cu, "E_dom_MWh": e_dom, "E_otros_MWh": e_otros, "E_total_MWh": e_tot, "MD_kW": md})
dem = pd.DataFrame(filas)
dem.to_csv(W / "demanda.csv", index=False)
md_tot = dem.groupby("anio").MD_kW.sum()
P20 = dem[dem.anio == anios[-1]].groupby("punto").MD_kW.sum().to_dict()
R["demanda"] = {"MD_anio0_kW": md_tot.iloc[0], "MD_anio20_kW": md_tot.iloc[-1], "P20": P20,
                "E20_MWh": dem[dem.anio == anios[-1]].E_total_MWh.sum()}

# ------------------------------------------------------------------ 2. ELÉCTRICOS
V = SIS["Vn"]; cos = SIS["cos"]; tg = math.tan(math.acos(cos))
FC_alt = 1 + 1.25 * (perfil.cota_m.max() - 1000) * 1e-4                 # RD 018 8.2
PROG["FIN"] = troncal.length
def puntos_carga(Pdict): return [(PROG[k], v) for k, v in Pdict.items()]
cargas_pts = puntos_carga(P20)
def tramos_flujo(cpts):
    pts = sorted(cpts); out = []; prev = 0.0
    for i, (s, p) in enumerate(pts):
        P = sum(pp for _, pp in pts[i:]); out.append(((s - prev) / 1000, P)); prev = s
    return out
flujo = tramos_flujo(cargas_pts)
Icc = SIS["Scc_MVA"] / (math.sqrt(3) * V)                               # kA
Im = Icc * math.sqrt((SIS["m"] + SIS["n"]) * SIS["t_falla"])
S_min_cc = Im * 1000 / SIS["J_cc"]
PRECIO_COND = {25: 4.10, 35: 5.20, 50: 7.00, 70: 9.50, 95: 12.80}      # S/ por m – estimado (ver Anexo cotizaciones)
MONTAJE_COND = 1.60          # S/ por m-fase (ACU tendido y flechado) – ver presupuesto
P_ENERGIA = 0.25; TASA = 0.08                                            # S/ kWh SUPUESTO; TSD MEF 8 %
FCg = M["fc"]; FP = 0.15 * FCg + 0.85 * FCg ** 2                         # RD 018 7.0
AMP = {25: 135, 35: 170, 50: 210, 70: 255, 95: 320}                    # A, catálogo referencial (Alfanar)
def x_geo(c):
    """Reactancia por geometría del armado (RD 018 6.2): X = 2πf[0,5 + 4,6 log(DMG/re)]·10⁻⁴ Ω/km."""
    re_ = 0.758 * c["D"] / 2
    Dp = math.hypot(ARM["sep_h"] / 2, ARM["d_inf"] - ARM["d_sup"])
    dmg = (ARM["sep_h"] * Dp * Dp) ** (1 / 3) * 1000
    return 2 * math.pi * SIS["f"] * (0.5 + 4.6 * math.log10(dmg / re_)) * 1e-4
for c_ in COND.values():
    c_["X"] = x_geo(c_); c_["R40"] = c_["R20"] * (1 + 0.0036 * 20)
comp = []
for s, c in COND.items():
    dv = sum(c["K1"] * P * Lk for Lk, P in flujo) * 100 / 100            # K1 en %/(kW·km): RD 018 6.2.2 (x10^-4 ya incluido)
    dv = sum((c["R40"] + c["X"] * tg) / (10 * V ** 2) * P * Lk for Lk, P in flujo)
    I20 = sum(p for _, p in cargas_pts) / (math.sqrt(3) * V * cos)
    # pérdidas por año (kW) con demanda creciente
    vp_perd = 0; pj20 = 0
    for k, a in enumerate(anios):
        Pk = dem[dem.anio == a].groupby("punto").MD_kW.sum().to_dict()
        fl = tramos_flujo(puntos_carga(Pk))
        pj = sum(P ** 2 * c["R40"] * Lk / (1000 * V ** 2 * cos ** 2) for Lk, P in fl)
        ej = 8760 * pj * FP
        if k > 0: vp_perd += ej * P_ENERGIA / (1 + TASA) ** k
        if k == len(anios) - 1: pj20 = pj
    inv = 3 * troncal.length * 1.02 * (PRECIO_COND[s] + MONTAJE_COND)
    comp.append({"seccion_mm2": s, "R40": c["R40"], "X": c["X"], "I20_A": I20, "Iadm_A": AMP[s], "dV20_pct": dv,
                 "PJ20_kW": pj20, "PJ20_pct": 100 * pj20 / sum(p for _, p in cargas_pts),
                 "VP_perdidas_S": vp_perd, "Inversion_cond_S": inv, "Costo_total_S": inv + vp_perd,
                 "cumple_dV": dv <= SIS["dV_max_pct"], "cumple_Icc": s >= S_min_cc, "cumple_I": I20 <= AMP[s]})
comp = pd.DataFrame(comp)
RESERVA_DV = SIS["reserva_dV"]   # se exige reserva sobre el límite de caída de tensión (incertidumbre del estudio de mercado)
comp["cumple_reserva"] = comp.dV20_pct <= RESERVA_DV * SIS["dV_max_pct"]
ok = comp[comp.cumple_reserva & comp.cumple_Icc & comp.cumple_I]
# Óptimo económico entre las secciones que cumplen; la sección ADOPTADA es la del kit de materiales (diseno.conductor_mm2, 70 mm²),
# porque metrados, precios, láminas y anexos están armados para ella. Si el kit no cumple, el paso 11 lo marca NO CONFORME.
SEC_OPT = int(ok.sort_values("Costo_total_S").iloc[0].seccion_mm2) if len(ok) else None
SEC = SECCION
comp["optimo"] = comp.seccion_mm2 == (SEC_OPT or -1)
comp["seleccion"] = comp.seccion_mm2 == SEC
comp.to_csv(W / "comparacion_conductores.csv", index=False)
R["electrico"] = {"FC_alt": FC_alt, "Icc_kA": Icc, "Im_kA": Im, "S_min_cc": S_min_cc, "seccion": SEC, "seccion_optima": SEC_OPT,
                  "kit_cumple": bool(comp[comp.seleccion].iloc[0][["cumple_reserva", "cumple_Icc", "cumple_I"]].all()), "FP": FP,
                  "flujo": flujo, "cota_max": float(perfil.cota_m.max()), "cota_min": float(perfil.cota_m.min())}
# perfil de tensión año 20 con la sección elegida
cS = COND[SEC]; kS = (cS["R40"] + cS["X"] * tg) / (10 * V ** 2)
nodos = []; acc = 0.0
for (Lk, P), (s_, _) in zip(flujo, sorted(cargas_pts)):
    acc += kS * P * Lk
    pid = [k for k, v in PROG.items() if abs(v - s_) < 1e-6][0]
    nodos.append({"punto": pid, "nombre": NOMBRE_PUNTO[pid], "prog_m": s_, "L_tramo_km": Lk, "P_kW": P, "dV_pct": acc})
R["electrico"]["nodos"] = nodos
R["electrico"]["dV_cut_pct"] = nodos[0]["dV_pct"] if DER else acc
R["electrico"]["dV_fin_pct"] = float(comp[comp.seleccion].dV20_pct.iloc[0])

# ------------------------------------------------------------------ 3. MECÁNICA DEL CONDUCTOR
c = COND[SEC]
S = c["n"] * math.pi * (c["dw"] / 2) ** 2                               # mm² real
D = c["D"] / 1000; wc = c["kg_m"] * G
sr = SIGMA_R
def carga(h):
    e = h["hielo"] / 1000
    wh = RHO_HIELO * G * math.pi * ((D + 2 * e) ** 2 - D ** 2) / 4
    pv = K_VIENTO * h["V"] ** 2
    fv = pv * (D + 2 * e)
    return math.hypot(wc + wh, fv), pv, wh, fv
def cambio_estado(s1, w1, t1, w2, t2, d):
    """σ2 (N/mm²) por la ecuación de cambio de estado (RD 018 4.5.1)."""
    A = d ** 2 * E_FINAL * (w1 / S) ** 2 / (24 * s1 ** 2) - s1 + ALFA * E_FINAL * (t2 - t1)
    B = d ** 2 * E_FINAL * (w2 / S) ** 2 / 24
    r = np.roots([1.0, A, 0.0, -B])                  # σ³ + A·σ² − B = 0: única raíz real positiva
    s2 = max(x.real for x in r if abs(x.imag) < 1e-7 and x.real > 0)
    return s2
hip = {k: dict(v, w=carga(v)[0], pv=carga(v)[1]) for k, v in HIP.items()}
ref = "H2 EDS final"; s_ref = EDS_FINAL * sr
def estados(d):
    out = {}
    for k, h in hip.items():
        if k == "H1 EDS inicial":
            out[k] = EDS_INI * sr; continue
        out[k] = cambio_estado(s_ref, hip[ref]["w"], hip[ref]["t"], h["w"], h["t"], d)
    return out
vanos_tab = list(range(50, 351, 25))
mec = []
for d in vanos_tab:
    st = estados(d)
    for k, s2 in st.items():
        w = hip[k]["w"]; H = s2 * S; f = w * d ** 2 / (8 * H); Tmax = H + w * f   # tiro en apoyo (aprox. RD 018 4.5.2)
        mec.append({"vano_m": d, "hipotesis": k, "t_C": hip[k]["t"], "w_N_m": w, "sigma_N_mm2": s2, "pct_UTS": 100 * s2 / sr,
                    "T_horizontal_N": H, "T_apoyo_N": Tmax, "flecha_m": f, "parametro_m": H / w,
                    "cumple_60pct": Tmax / S <= SIGMA_MAX * sr})
mec = pd.DataFrame(mec); mec.to_csv(W / "calculo_mecanico_conductor.csv", index=False)
# tabla de templado (flecha de tendido a t = flecha final a t-10 °C, compensación de CREEP RD 018 4.4)
temp = []
for d in range(60, 301, 20):
    row = {"vano_m": d}
    for t in range(-5, 31, 5):
        s2 = cambio_estado(s_ref, hip[ref]["w"], hip[ref]["t"], wc, t - 10, d)
        row[f"f_{t}C_m"] = wc * d ** 2 / (8 * s2 * S); row[f"T_{t}C_N"] = s2 * S
    temp.append(row)
pd.DataFrame(temp).to_csv(W / "tabla_templado.csv", index=False)
# parámetro en H6 por vano (para plantillado) y tiro máximo horizontal por vano
dgrid = np.arange(20, 401, 5)
p6 = np.array([cambio_estado(s_ref, hip[ref]["w"], hip[ref]["t"], hip["H6 Temp. máxima"]["w"], hip["H6 Temp. máxima"]["t"], d) * S / wc for d in dgrid])
Tmax_h = np.array([max(estados(d)[k] for k in ("H3 Temp. mínima", "H4 Viento máximo", "H5 Hielo", "H5b Hielo + viento")) * S for d in dgrid])
pmin = np.array([cambio_estado(s_ref, hip[ref]["w"], hip[ref]["t"], wc, HIP["H3 Temp. mínima"]["t"], d) * S / wc for d in dgrid])
R["mecanico"] = {"S_real_mm2": S, "w_c_N_m": wc, "D_m": D, "hipotesis": {k: {kk: v for kk, v in h.items()} for k, h in hip.items()},
                 "sigma_ref": s_ref, "cumple_60_todos": bool(mec.cumple_60pct.all()),
                 "max_pct_UTS": float(mec.pct_UTS.max())}

# ------------------------------------------------------------------ 4. PLANTILLADO
def zt(s): return float(np.interp(s, PX, PZ))
def req(s):
    base = DIST["general"]
    if len(cr_prog) and np.min(np.abs(cr_prog - s)) <= 20: base = DIST["cruce_via"]
    return base + DIST["margen_dem"]
def h_low(poste): L = POSTES[poste]["L"]; return L - (L / 10 + 0.6) - ARM["d_inf"]
def span_ok(s0, s1, h0, h1):
    d = s1 - s0
    if d <= 0: return True, 99
    p = float(np.interp(d, dgrid, p6))
    ya, yb = zt(s0) + h0, zt(s1) + h1
    xs = np.arange(s0 + 2.0, s1 - 1.0, 2.0)
    if len(xs) == 0: return True, 99
    x = xs - s0
    y = ya + (yb - ya) * x / d - x * (d - x) / (2 * p)
    clr = y - np.array([zt(v) for v in xs]) - np.array([req(v) for v in xs])
    return bool(clr.min() >= 0), float(clr.min())
verts_prog = [troncal.project(Point(v)) for v in meta["vertices"]]
fixed = sorted(set([0.0, troncal.length] + deriv_progs + verts_prog))
fixed = [f for i, f in enumerate(fixed) if i == 0 or f - fixed[i - 1] > 1.0]
poles = [(0.0, "12/400")]
for a, b in zip(fixed[:-1], fixed[1:]):
    s0 = a
    while b - s0 > 1e-6:
        h0 = h_low(poles[-1][1]); placed = False
        for poste in ("12/300", "13/400"):
            hs = h_low(poste)
            best = None
            s1 = min(b, s0 + PLANT["vano_max"])
            while s1 - s0 >= PLANT["vano_min"] or s1 == b:
                if span_ok(s0, s1, h0, hs)[0]:
                    best = s1; break
                if s1 == b and b - s0 < PLANT["vano_min"]: break
                s1 -= PLANT["paso"]
            if best is not None:
                poles.append((best, poste)); s0 = best; placed = True; break
        if not placed:     # vano muy corto forzado
            s1 = min(b, s0 + PLANT["vano_min"]); poles.append((s1, "13/400")); s0 = s1
# equilibrar vanos entre puntos fijos (mismo número de vanos, distribución uniforme) si cumple
def rebalance(poles):
    """Entre puntos fijos: distribución uniforme con el menor número de vanos que cumpla
    distancias al terreno (primero postes de 12 m, luego 13 m); si no, se mantiene el plantillado progresivo."""
    out = [poles[0]]
    idx = [i for i, (s, _) in enumerate(poles) if any(abs(s - f) < 1e-3 for f in fixed)]
    for i0, i1 in zip(idx[:-1], idx[1:]):
        seg = poles[i0:i1 + 1]; n0 = len(seg) - 1
        a, b = seg[0][0], seg[-1][0]
        COSTO = {"12/300": 1350 + 900, "12/400": 1650 + 900, "13/400": 1950 + 900}   # poste + armado (orden de magnitud)
        cands = [seg]
        for poste in ("12/300", "13/400"):
            for nn in range(max(1, n0 - 1), n0 + 7):
                if (b - a) / nn > PLANT["vano_max"]: continue
                cand = [(a + (b - a) * k / nn, poste) for k in range(nn + 1)]
                cand[0] = seg[0]
                if all(span_ok(cand[k][0], cand[k + 1][0], h_low(cand[k][1]), h_low(cand[k + 1][1]))[0] for k in range(nn)):
                    cands.append(cand); break
        # se prefiere la alternativa de menor costo; a igualdad, la de vanos uniformes
        chosen = min(cands, key=lambda c: (sum(COSTO[x[1]] for x in c[1:]) + (1 if c is seg else 0),))
        out.extend((chosen or seg)[1:])
    return out
poles = rebalance(poles)
# ajuste local: cada estructura no fija se desplaza para maximizar el menor de sus dos vanos
for _ in range(3):
    for k in range(1, len(poles) - 1):
        s, pst = poles[k]
        if any(abs(s - f) < 1e-3 for f in fixed): continue
        sa, pa = poles[k - 1]; sb, pb = poles[k + 1]
        best = (min(s - sa, sb - s), s)
        for x in np.arange(sa + PLANT["vano_min"], sb - PLANT["vano_min"] + 0.1, 2.5):
            m = min(x - sa, sb - x)
            if m <= best[0] or (sb - sa) - m > PLANT["vano_max"]: continue
            if span_ok(sa, x, h_low(pa), h_low(pst))[0] and span_ok(x, sb, h_low(pst), h_low(pb))[0]:
                best = (m, x)
        poles[k] = (best[1], pst)
# ------------------------------------------------------------------ 5. ESTRUCTURAS
def defl(s):
    for v, a in zip(verts_prog[1:-1], meta["angulos"]):
        if abs(v - s) < 1.0: return a
    return 0.0
rows = []
n = len(poles)
for i, (s, poste) in enumerate(poles):
    p = troncal.interpolate(s); lon, lat = to_ll.transform(p.x, p.y)
    rows.append({"N": i + 1, "estructura": f"E-{i+1:03d}", "progresiva_m": s, "este": p.x, "norte": p.y, "lat": lat, "lon": lon,
                 "cota_m": zt(s), "poste": poste, "angulo_deg": defl(s)})
E = pd.DataFrame(rows)
E["vano_atras_m"] = E.progresiva_m.diff()
E["vano_adelante_m"] = -E.progresiva_m.diff(-1)
E["vano_viento_m"] = E[["vano_atras_m", "vano_adelante_m"]].fillna(0).sum(axis=1) / 2
# vano peso con desnivel (parábola, hipótesis de temperatura mínima para verificar arranque)
def xi_left(d, h, p): return d / 2 - p * h / d     # distancia del vértice al apoyo izquierdo
hc = [r.cota_m + h_low(r.poste) for r in E.itertuples()]
vp = []
for i in range(n):
    left = right = 0.0
    if i > 0:
        d = E.vano_atras_m[i]; p = float(np.interp(d, dgrid, pmin)); h = hc[i] - hc[i - 1]
        left = d - xi_left(d, h, p)                    # tramo del vano atrás que carga sobre i
    if i < n - 1:
        d = E.vano_adelante_m[i]; p = float(np.interp(d, dgrid, pmin)); h = hc[i + 1] - hc[i]
        right = xi_left(d, h, p)
    vp.append(left + right)
E["vano_peso_m"] = vp
# anclajes intermedios cada ~3 km en alineamientos largos
last = 0.0; anc = set()
for i, r in E.iterrows():
    if r.angulo_deg > 30 or i in (0, n - 1) or any(abs(r.progresiva_m - p) < 1 for p in deriv_progs): last = r.progresiva_m; continue
    if r.progresiva_m - last >= PLANT["anclaje_cada_m"]:
        anc.add(i); last = r.progresiva_m
def tipo(i, r):
    if i == 0: return "PSER-3"
    if i == n - 1: return "PTH-3"
    if any(abs(r.progresiva_m - p) < 1 for p in deriv_progs): return "DT-3"
    a = r.angulo_deg
    if a > 60: return "PA3-3"
    if i in anc: return "PR3-3"
    if a > 30: return "PA2-3"
    if a > 5: return "PA1-3"
    return "PS1-3"
E["armado"] = [tipo(i, r) for i, r in E.iterrows()]
# arrancamiento: vano peso negativo a temperatura mínima en armados con aisladores PIN → armado de anclaje (aisladores de suspensión)
E["arranque"] = (E.vano_peso_m < 0) & E.armado.isin(["PS1-3", "PA1-3"])
E.loc[E.arranque, "armado"] = "TS-3"
# cargas (RD 018 5.3) – hipótesis H4 viento máximo
pv4 = hip["H4 Viento máximo"]["pv"]
def tmax_h(d): return float(np.interp(d, dgrid, Tmax_h))
CAP_RET = RET["rotura_N"] / RET["FS"]; SIN_R = math.sin(math.radians(RET["angulo_deg"]))
def cargas(r, poste):
    P = POSTES[poste]; L = P["L"]; he = L / 10 + 0.6; hl = L - he
    hs = [hl - ARM["d_sup"], hl - ARM["d_inf"], hl - ARM["d_inf"]]
    Dm = P["Do"] + (P["Db"] - P["Do"]) * hl / L
    a = math.radians(r.angulo_deg)
    dmax = max(v for v in (r.vano_atras_m, r.vano_adelante_m) if not pd.isna(v))
    T = tmax_h(dmax)                                       # tiro horizontal máximo por conductor (vano mayor adyacente)
    MVC = pv4 * r.vano_viento_m * D * sum(hs) * math.cos(a / 2)
    MVP = pv4 * hl ** 2 * (Dm + 2 * P["Do"]) / 600
    MCW = 1.0 * (wc * r.vano_peso_m + W_AISL + W_HOMBRE)
    if r.armado in ("PSER-3", "PTH-3", "PR3-3"):
        MTC = T * sum(hs)                                  # terminal / anclaje: tiro total de un lado (RD 018 5.3)
    else:
        MTC = 2 * T * sum(hs) * math.sin(a / 2)
    MRN = MVC + MTC + MCW + MVP
    return dict(hl=hl, he=he, hs=hs, T=T, dmax=dmax, MVC=MVC, MTC=MTC, MCW=MCW, MVP=MVP, MRN=MRN, QN=MRN / (hl - 0.15))
def n_ret(arm, c, Q):
    Tret = (c["MTC"] / (sum(c["hs"]) / 3)) / SIN_R if c["MTC"] > 0 else 0.0
    if arm == "PS1-3":
        n = max(1, math.ceil(Tret / CAP_RET)) if c["QN"] > Q * 10 and Tret > 0 else 0
    elif arm in ("PA1-3", "PA2-3", "TS-3", "DT-3", "PSER-3", "PTH-3"):
        n = max(1, math.ceil(Tret / CAP_RET)) if Tret > 0 else 0
    elif arm == "PR3-3":
        n = 2 * max(1, math.ceil(3 * c["T"] / SIN_R / CAP_RET))      # anclaje: retenidas en ambos sentidos
    elif arm == "PA3-3":
        n = 2 * max(1, math.ceil(3 * c["T"] / SIN_R / CAP_RET))
    else:
        n = 0
    return n, Tret
res = []
for i, r in E.iterrows():
    poste = r.poste
    if r.armado != "PS1-3" and poste == "12/300": poste = "12/400"
    c = cargas(r, poste)
    if r.armado == "PS1-3" and c["QN"] > POSTES[poste]["Q"] * 10 and poste == "12/300":
        poste = "12/400"; c = cargas(r, poste)
    nret, Tret = n_ret(r.armado, c, POSTES[poste]["Q"])
    QN_res = (c["MRN"] - (c["MTC"] if nret else 0)) / (c["hl"] - 0.15)
    res.append({"poste": poste, "hl_m": c["hl"], "empotramiento_m": c["he"], "vano_max_adyacente_m": c["dmax"], "T_cond_N": c["T"],
                "MVC_Nm": c["MVC"], "MTC_Nm": c["MTC"], "MCW_Nm": c["MCW"], "MVP_Nm": c["MVP"], "MRN_Nm": c["MRN"],
                "QN_daN": c["QN"] / 10, "QN_con_ret_daN": QN_res / 10, "Qadm_daN": POSTES[poste]["Q"],
                "T_retenida_N": Tret, "n_retenidas": nret})
E = pd.concat([E.drop(columns=["poste"]), pd.DataFrame(res)], axis=1)
E["cumple_poste"] = E.QN_con_ret_daN <= E.Qadm_daN
# tipo de retenida
def tipo_ret(r):
    if r.n_retenidas == 0: return "-"
    return "RI"
E["tipo_retenida"] = E.apply(tipo_ret, axis=1)
# puestas a tierra (RD 018 10.2: cada 3 estructuras; equipos con R <= 25 Ω; 2 estructuras contiguas a equipos)
equip = set(E.index[E.armado.isin(["PSER-3", "DT-3", "PTH-3"])])
pat = []
for i in range(n):
    if i in equip: pat.append("PAT-2")
    elif any(abs(i - j) == 1 for j in equip) or i % PAT["cada_n"] == 0: pat.append("PAT-1")
    else: pat.append("-")
E["puesta_tierra"] = pat
def deriv_de(r):
    return min(DER, key=lambda d: abs(d["prog"] - r.progresiva_m))["nombre"] if DER else ""
def equipo(r):
    if r.armado == "PSER-3": return "Reconectador 38 kV 170 kV-BIL + 3 cut-out 38 kV + 3 pararrayos 24 kV"
    if r.armado == "DT-3": return f"Seccionamiento PSEC-3P: 3 cut-out 38 kV 170 kV-BIL + 3 pararrayos 24 kV (derivación {deriv_de(r)})"
    if r.armado == "PTH-3": return f"3 cut-out 38 kV 170 kV-BIL + 3 pararrayos 24 kV (llegada {FIN['nombre']})"
    return "-"
E["equipamiento"] = E.apply(equipo, axis=1)
def obs(r):
    o = []
    if len(cr_prog) and np.min(np.abs(cr_prog - r.progresiva_m)) <= 60: o.append("Próxima a cruce de vía")
    if r.angulo_deg > 0: o.append(f"Vértice ({r.angulo_deg:.1f}°)")
    if r.armado == "DT-3": o.append(f"Punto de derivación a {deriv_de(r)}")
    if r.arranque: o.append("Arrancamiento a temperatura mínima: armado TS-3 con cadenas de anclaje")
    return "; ".join(o)
E["observaciones"] = E.apply(obs, axis=1)
E.to_csv(W / "planilla_estructuras.csv", index=False)
# resistencia de PAT
rho = PAT["rho"]; Lr = PAT["L"]; dr = PAT["d"]
KT = 0.6; SV = 5.0
R1 = 0.366 * rho / Lr * math.log10(4 * Lr / dr)                 # fórmula del modelo (Anexo 3)
R1t = R1 * KT
R2 = R1 / 2 * (1 + rho / (2 * math.pi * SV * R1))
R2t = R1t / 2 * (1 + rho * KT / (2 * math.pi * SV * R1t))
R["pat"] = {"R1": R1, "R1t": R1t, "R2": R2, "R2t": R2t}
# resumen
vanos = E.vano_adelante_m.dropna()
R["plantillado"] = {"n_estructuras": int(n), "vano_medio": float(vanos.mean()), "vano_max": float(vanos.max()),
                    "vano_min": float(vanos.min()), "tipos": E.armado.value_counts().to_dict(),
                    "postes": E.poste.value_counts().to_dict(), "retenidas": int(E.n_retenidas.sum()),
                    "pat": E.puesta_tierra.value_counts().to_dict(), "todos_cumplen_poste": bool(E.cumple_poste.all()),
                    "L_troncal_m": troncal.length, "prog_cut": (deriv_progs[0] if deriv_progs else None),
                    "derivaciones": [{**d, "estructura": E.iloc[(E.progresiva_m - d["prog"]).abs().argmin()].estructura} for d in DER]}
# verificación de distancias para cada vano
chk = []
for i in range(n - 1):
    ok_, cmin = span_ok(E.progresiva_m[i], E.progresiva_m[i + 1], h_low(E.poste[i]), h_low(E.poste[i + 1]))
    d = E.progresiva_m[i + 1] - E.progresiva_m[i]
    f6 = d ** 2 / (8 * float(np.interp(d, dgrid, p6)))
    Dh = 0.0076 * V * FC_alt + 0.65 * math.sqrt(f6)                    # RD 018 3.3
    chk.append({"vano": f"{E.estructura[i]}–{E.estructura[i+1]}", "d_m": d, "flecha_H6_m": f6, "holgura_min_m": cmin,
                "cumple_terreno": ok_, "D_horizontal_req_m": Dh, "cumple_sep_fases": Dh <= ARM["sep_h"]})
chk = pd.DataFrame(chk); chk.to_csv(W / "verificacion_vanos.csv", index=False)
R["plantillado"]["cumple_terreno"] = bool(chk.cumple_terreno.all())
R["plantillado"]["cumple_sep"] = bool(chk.cumple_sep_fases.all())
R["plantillado"]["Dh_max"] = float(chk.D_horizontal_req_m.max())
pd.DataFrame({"vano_m": dgrid, "p_H6_m": p6, "p_Hmin_m": pmin, "Tmax_h_N": Tmax_h}).to_csv(W / "parametros_vano.csv", index=False)
json.dump(R, open(W / "resultados.json", "w"), indent=1, default=float)
print(json.dumps({k: R[k] for k in ("demanda", "plantillado")}, indent=1, default=float))
print(comp.round(3).to_string())
print("Icc", round(Icc, 2), "Im", round(Im, 2), "Smin", round(S_min_cc, 1), "FCalt", round(FC_alt, 4), "PAT", {k: round(v, 1) for k, v in R["pat"].items()})
print("mec max %UTS", round(R["mecanico"]["max_pct_UTS"], 1), "cumple60", R["mecanico"]["cumple_60_todos"])
print(E[E.armado != "PS1-3"][["estructura", "progresiva_m", "angulo_deg", "armado", "poste", "QN_daN", "QN_con_ret_daN", "T_retenida_N", "n_retenidas"]].round(1).to_string())
print(E[E.armado == "PS1-3"][["QN_daN"]].describe().round(1).T)
