"""Contexto común para los documentos (pasos 12 a 15): datos del proyecto ya calculados, textos derivados de la
configuración y utilidades (número en letras, listas en castellano, selección de fusibles, imagen de un PDF)."""
import json, math
from pathlib import Path
import pandas as pd
from params import *

FUS_K = [6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 65, 80, 100, 140, 200]   # fusibles tipo K normalizados (ANSI C37.43)
FUS_MIN_DERIV = 10                                                       # mínimo práctico en derivaciones


def letras(n):
    """Número entero (0–999 999) en letras, p. ej. 120 → 'ciento veinte'."""
    U = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte".split()
    V = {2: "veinti", 3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
    C = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos"}
    n = int(n)
    if n <= 20: return U[n]
    if n < 30: return {22: "veintidós", 23: "veintitrés", 26: "veintiséis"}.get(n, "veinti" + U[n - 20])
    if n < 100: return V[n // 10] + ("" if n % 10 == 0 else " y " + U[n % 10])
    if n == 100: return "cien"
    if n < 1000: return C[n // 100] + ("" if n % 100 == 0 else " " + letras(n % 100))
    m, r = divmod(n, 1000)
    return ("mil" if m == 1 else letras(m) + " mil") + ("" if r == 0 else " " + letras(r))


def dias_txt(n):
    return f"{letras(n)} ({n}) días calendario"


def lista(items, y="y"):
    items = [str(i) for i in items if str(i)]
    if not items: return ""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + f" {y} " + items[-1]


def fusible_k(I, minimo=0):
    """Menor fusible K con corriente nominal ≥ 1,5 × I de carga (y ≥ mínimo)."""
    obj = max(1.5 * I, minimo)
    return next((k for k in FUS_K if k >= obj), FUS_K[-1])


def png_de_pdf(pdf, png, dpi=120):
    """Primera página de un PDF → PNG (PyMuPDF; no requiere programas externos)."""
    import pymupdf
    png = Path(png); png.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf)); doc[0].get_pixmap(dpi=dpi).save(str(png)); doc.close()
    return str(png)


def cargar(W):
    """Devuelve un diccionario con todo lo que necesitan los documentos."""
    W = Path(W)
    K = json.load(open(W / "datos_clave.json")); E = pd.read_csv(W / "planilla_estructuras.csv")
    dem = pd.read_csv(W / "demanda.csv")
    V = SIS["Vn"]; cos = SIS["cos"]
    I = lambda kw: kw / (math.sqrt(3) * V * cos)
    nod = {n["punto"]: n for n in K["el"]["nodos"]}
    ders = []
    for d in K["plan"]["derivaciones"]:
        P = K["dem"]["P20"].get(d["id"], 0.0)
        ders.append({**d, "P20": P, "I20": I(P), "dV": nod.get(d["id"], {}).get("dV_pct", float("nan")),
                     "fus": fusible_k(I(P), FUS_MIN_DERIV)})
    Pfin = K["dem"]["P20"].get("FIN", 0.0)
    fus_fin = fusible_k(I(Pfin), FUS_MIN_DERIV)
    Ptot = K["dem"]["MD_anio20_kW"]
    aguas_abajo = max([fus_fin] + [d["fus"] for d in ders])
    fus_arr = max(fusible_k(I(Ptot)), next((k for k in FUS_K if k > aguas_abajo), FUS_K[-1]))   # coordina con los de aguas abajo
    E0, EF = E.estructura.iloc[0], E.estructura.iloc[-1]
    n_der = len(ders)
    if n_der == 0: txt_der = ""
    elif n_der == 1: txt_der = f" con derivación para {ders[0]['nombre']}"
    else: txt_der = f" con derivaciones para {lista([d['nombre'] for d in ders])}"
    pob = {c["nombre"]: c.get("pob2017") for c in MERCADO["cargas"]}
    return {"K": K, "E": E, "dem": dem, "L": K["plan"]["L_troncal_m"] / 1000, "ders": ders, "Pfin": Pfin, "Ifin": I(Pfin),
            "Ptot": Ptot, "Itot": I(Ptot), "fus_fin": fus_fin, "fus_arr": fus_arr, "E0": E0, "EF": EF,
            "dV_fin": nod.get("FIN", {}).get("dV_pct", K["elec"]["dV"]), "ALT": K["aisl"]["h"], "txt_der": txt_der,
            "ini": INICIO["nombre"], "fin": FIN["nombre"], "pob": pob, "I": I, "meta": json.load(open(W / "trazado_meta.json"))}


def clima(clave, unidad="", dec=1, defecto="(dato pendiente)"):
    v = CLIMA.get(clave)
    if v is None: return defecto
    s = f"{float(v):,.{dec}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−") + (f" {unidad}" if unidad else "")


def fusibles_txt(C):
    partes = [f"{C['fus_arr']} A en el arranque"] + [f"{d['fus']} A en la derivación a {d['nombre']}" for d in C["ders"]] + [f"{C['fus_fin']} A en la llegada a {C['fin']}"]
    return lista(partes)
