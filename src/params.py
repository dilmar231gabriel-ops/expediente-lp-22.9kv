"""Carga el archivo de configuración del proyecto (proyecto.yaml) y expone los parámetros de diseño.
El archivo se indica con la variable de entorno LP_CONFIG (la define generar.py).
Las constantes de normas (conductores, hipótesis, etc.) que no cambian entre proyectos están aquí; todo lo propio del
lugar viene del YAML."""
import os
from pathlib import Path
import yaml

_CFG_PATH = Path(os.environ.get("LP_CONFIG", Path(__file__).resolve().parents[1] / "proyectos/chacachaca-cuturapi-yunguyo/proyecto.yaml"))
CFG = yaml.safe_load(open(_CFG_PATH, encoding="utf-8"))
CFG_DIR = _CFG_PATH.parent


def ruta(rel):
    """Ruta absoluta de un archivo indicado en el YAML (relativa a la carpeta del YAML)."""
    if not rel: return None
    p = Path(rel)
    return p if p.is_absolute() else (CFG_DIR / p)


_p = CFG["proyecto"]
PROYECTO = {"nombre": _p["nombre"], "nombre_corto": _p["nombre_corto"], "ubicacion": _p["ubicacion"], "fecha": _p["fecha"],
            "entidad": _p.get("entidad", "Por definir"), "proyectista": _p["proyectista"], "anio_base": int(_p["anio_base"]),
            "horizonte": int(_p["horizonte"]), "departamento": _p["departamento"], "provincias": _p["provincias"],
            "distritos": _p["distritos"], "concesionaria": _p.get("concesionaria", "la empresa concesionaria"),
            "iniciales": _p.get("iniciales", ""), "ciudad_fecha": _p.get("ciudad_fecha_caratula", _p["fecha"]).upper(),
            "plazo_dias": int(_p.get("plazo_dias", 120))}
EPSG = int(CFG.get("epsg_utm", 32719))
ZONA_UTM = f"{EPSG - 32700} S" if EPSG > 32700 else f"{EPSG - 32600} N"

# ---------------------------------------------------------------- puntos de la línea
_pt = CFG["puntos"]
INICIO = _pt["inicio"]; FIN = _pt["fin"]
DERIVS = _pt.get("derivaciones") or []           # lista de dicts {id, nombre, lon, lat}
NOMBRE_PUNTO = {"FIN": FIN["nombre"], **{d["id"]: d["nombre"] for d in DERIVS}}
TRAZADO = CFG["trazado"]
assert float(TRAZADO.get("angulo_max_quiebre_deg", 60)) <= 60, \
    "angulo_max_quiebre_deg debe ser ≤ 60°: el kit de armados llega hasta PA2-3 (30°–60°); para ángulos mayores agregue un vértice intermedio"
DATOS = {k: ruta(v) for k, v in CFG.get("datos", {}).items()}

# ---------------------------------------------------------------- sistema eléctrico (RD 018-2003-EM/DGE)
_s = CFG["sistema"]
SIS = {"Vn": float(_s["Vn"]), "Vmax": float(_s["Vmax"]), "f": int(_s.get("f", 60)), "cos": float(_s.get("cos", 0.9)), "fases": 3,
       "Scc_MVA": float(_s["Scc_MVA"]), "t_falla": float(_s.get("t_falla", 0.2)), "m": 0.0, "n": 0.85, "J_cc": 91.0,
       "dV_max_pct": float(_s.get("dV_max_pct", 5.0)), "reserva_dV": float(_s.get("reserva_dV", 0.85)),
       "XR": float(_s.get("XR_fuente", 5.0)), "isoceraunico": int(_s.get("nivel_isoceraunico", 30))}

# ---------------------------------------------------------------- estudio de mercado
_m = CFG["mercado"]
MERCADO = {k: v for k, v in _m.items()}
for c in MERCADO["cargas"]:
    assert c["punto"] == "FIN" or c["punto"] in NOMBRE_PUNTO, f"La carga {c['nombre']} usa un punto inexistente: {c['punto']}"

# ---------------------------------------------------------------- conductores AAAC (RD 018 4.2.2, Cuadros 6.1/6.2)
COND = {
    25: {"n": 7, "dw": 2.1, "D": 6.3, "kg_m": 0.067, "R20": 1.370, "R40": 1.469, "X": 0.47, "K1": 3.231e-4},
    35: {"n": 7, "dw": 2.5, "D": 7.5, "kg_m": 0.094, "R20": 0.966, "R40": 1.036, "X": 0.45, "K1": 2.387e-4},
    50: {"n": 7, "dw": 3.0, "D": 9.0, "kg_m": 0.135, "R20": 0.671, "R40": 0.719, "X": 0.44, "K1": 1.774e-4},
    70: {"n": 19, "dw": 2.1, "D": 10.5, "kg_m": 0.181, "R20": 0.507, "R40": 0.544, "X": 0.43, "K1": 1.431e-4},
    95: {"n": 19, "dw": 2.5, "D": 12.5, "kg_m": 0.250, "R20": 0.358, "R40": 0.384, "X": 0.41, "K1": 1.108e-4},
}
E_FINAL = 60760.0; ALFA = 23e-6; SIGMA_R = 295.8
EDS_FINAL = 0.15; EDS_INI = 0.18; SIGMA_MAX = 0.60

# ---------------------------------------------------------------- clima e hipótesis (RD 018 4.4 + CNE-S 2011)
CLIMA = CFG["clima"]
T_MEDIA = float(CLIMA["t_media"])
HIP = {
    "H1 EDS inicial":     {"t": T_MEDIA, "V": 0.0, "hielo": 0.0},
    "H2 EDS final":       {"t": T_MEDIA, "V": 0.0, "hielo": 0.0},
    "H3 Temp. mínima":    {"t": float(CLIMA["t_min_diseno"]), "V": 0.0, "hielo": 0.0},
    "H4 Viento máximo":   {"t": float(CLIMA.get("t_viento", 5.0)), "V": float(CLIMA["viento_ms"]), "hielo": 0.0},
    "H5 Hielo":           {"t": 0.0, "V": 0.0, "hielo": float(CLIMA.get("hielo_mm", 0.0))},
    "H5b Hielo + viento": {"t": 0.0, "V": float(CLIMA.get("viento_comb_ms", 0.0)), "hielo": float(CLIMA.get("hielo_comb_mm", 0.0))},
    "H6 Temp. máxima":    {"t": float(CLIMA.get("t_max_diseno", 40.0)) + 10.0, "V": 0.0, "hielo": 0.0},
}
K_VIENTO = float(CLIMA.get("K_viento", 0.455)); RHO_HIELO = 913.0

# ---------------------------------------------------------------- diseño de estructuras
_d = CFG["diseno"]
DIST = {"general": float(_d["dist_terreno_m"]), "cruce_via": float(_d["dist_cruce_via_m"]), "margen_dem": float(_d.get("margen_dem_m", 0.3))}
POSTES = {k: {kk: float(vv) for kk, vv in v.items()} for k, v in _d["postes"].items()}
ARM = {k: float(v) for k, v in _d["armado"].items()}
FS_POSTE = 2.0; W_HOMBRE = 1000.0; W_AISL = 60.0
RET = dict(_d["retenida"])
PAT = {k: float(v) if k != "cada_n" else int(v) for k, v in _d["puesta_tierra"].items()}
PLANT = {"vano_max": float(_d["vano_max_m"]), "vano_min": float(_d["vano_min_m"]), "paso": float(_d.get("paso_plantillado_m", 5)),
         "anclaje_cada_m": float(_d.get("anclaje_cada_m", 3000))}
LF_MM_KV = float(_d.get("linea_fuga_mm_kV", 20))
SECCION = int(_d.get("conductor_mm2", 70))      # kit de materiales: AAAC 70 mm² (catálogo, láminas y anexos preparados para esta sección)
assert SECCION == 70, "El kit de materiales está preparado para AAAC 70 mm²; otra sección exige actualizar catalogo.py, p05 y los textos"

# ---------------------------------------------------------------- económico y textos
ECON = CFG.get("economico", {})
TEXTOS = CFG.get("textos", {})


def txt(clave, defecto="(completar en proyecto.yaml → textos)"):
    return " ".join(str(TEXTOS.get(clave, defecto)).split())
