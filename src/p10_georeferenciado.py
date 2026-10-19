"""Plano georreferenciado (UTM WGS84 del proyecto, 1 unidad = 1 m) con cada estructura como bloque con atributos,
más el cuadro de coordenadas en Excel y CSV para estación total / GPS."""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd, ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import shape, LineString
from shapely.ops import transform
from pyproj import Transformer
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
sys.path.insert(0, str(Path(__file__).parent))
from params import *

W = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
E = pd.read_csv(W / "planilla_estructuras.csv"); meta = json.load(open(W / "trazado_meta.json"))
to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{EPSG}", always_xy=True).transform
_m = json.load(open(W / "trazado_meta.json")); road = LineString(_m["road"])

doc = ezdxf.new("R2018", setup=True)
doc.header["$INSUNITS"] = 6          # metros
doc.header["$MEASUREMENT"] = 1
doc.styles.add("EXP", font="arial.ttf")
LAY = {"LP_EJE": 1, "LP_ESTRUCTURAS": 5, "LP_ESTRUCT_ESPECIALES": 6, "LP_ROTULOS": 7, "LP_RETENIDAS": 3, "LP_PAT": 30,
       "LP_VERTICES": 2, "VIA_OSM": 8, "CUADRICULA_UTM": 9, "CUADRO_COORDENADAS": 7, "LOCALIDADES": 4}
for n, c in LAY.items(): doc.layers.add(n, color=c)
doc.layers.get("LP_EJE").dxf.lineweight = 50

# bloque de estructura con atributos (extraíbles con DATAEXTRACTION / ATTEXT)
blk = doc.blocks.new("ESTRUCTURA_LP")
blk.add_circle((0, 0), 1.5); blk.add_line((-2.2, 0), (2.2, 0)); blk.add_line((0, -2.2), (0, 2.2))
blk2 = doc.blocks.new("ESTRUCTURA_ESPECIAL_LP")
blk2.add_lwpolyline([(-2, -2), (2, -2), (2, 2), (-2, 2)], close=True); blk2.add_circle((0, 0), 1.2)
for b in (blk, blk2):
    for i, tag in enumerate(["NUMERO", "ARMADO", "POSTE", "PROGRESIVA", "ESTE", "NORTE", "COTA", "RETENIDAS", "PAT"]):
        b.add_attdef(tag, (3, -3 - i * 2.5), dxfattribs={"height": 1.8, "style": "EXP", "flags": 1 if i > 0 else 0})  # solo NUMERO visible
msp = doc.modelspace()

xy = E[["este", "norte"]].to_numpy(); n = len(E)
def unit(v): l = np.hypot(*v); return v / l if l else v
for i, r in E.iterrows():
    p = xy[i]
    u_prev = unit(xy[i - 1] - p) if i > 0 else None
    u_next = unit(xy[i + 1] - p) if i < n - 1 else None
    d_line = unit((u_next if u_next is not None else -u_prev)) if (u_next is not None or u_prev is not None) else np.array([1, 0])
    ang_line = math.degrees(math.atan2(d_line[1], d_line[0]))
    especial = r.armado != "PS1-3"
    ref = msp.add_blockref("ESTRUCTURA_ESPECIAL_LP" if especial else "ESTRUCTURA_LP", p,
                           dxfattribs={"layer": "LP_ESTRUCT_ESPECIALES" if especial else "LP_ESTRUCTURAS"})
    ref.add_auto_attribs({"NUMERO": r.estructura, "ARMADO": r.armado, "POSTE": f"CAC {r.poste}", "PROGRESIVA": f"{r.progresiva_m:.2f}",
                          "ESTE": f"{r.este:.3f}", "NORTE": f"{r.norte:.3f}", "COTA": f"{r.cota_m:.2f}",
                          "RETENIDAS": str(int(r.n_retenidas)), "PAT": r.puesta_tierra})
    # rótulo perpendicular a la línea
    nrm = np.array([-d_line[1], d_line[0]]); rot = ang_line + 90
    if rot > 90: rot -= 180
    if rot < -90: rot += 180
    lp = p + nrm * 6
    t = msp.add_text(f"{r.estructura}  {r.armado}  CAC {r.poste}", height=3.0, dxfattribs={"layer": "LP_ROTULOS", "style": "EXP", "rotation": rot})
    t.set_placement(tuple(lp), align=TA.MIDDLE_LEFT if np.dot(nrm, [math.cos(math.radians(rot)), math.sin(math.radians(rot))]) >= 0 else TA.MIDDLE_RIGHT)
    # retenidas (dirección según tipo de estructura)
    dirs = []
    k = int(r.n_retenidas)
    if k:
        if i == 0 or i == n - 1:
            dirs = [-(u_next if u_next is not None else u_prev)] * k
        elif r.armado == "PR3-3":
            dirs = [-u_prev] * (k // 2) + [-u_next] * (k - k // 2)
        else:
            b = -(u_prev + u_next); dirs = [unit(b) if np.hypot(*b) > 1e-6 else nrm] * k
    for j, dv in enumerate(dirs):
        off = (j - (len(dirs) - 1) / 2) * 0.6
        a = math.atan2(dv[1], dv[0]) + math.radians(off * 4)
        end = p + 8.0 * np.array([math.cos(a), math.sin(a)])
        msp.add_line(tuple(p), tuple(end), dxfattribs={"layer": "LP_RETENIDAS"})
        msp.add_circle(tuple(end), 0.6, dxfattribs={"layer": "LP_RETENIDAS"})
    if r.puesta_tierra != "-":
        g = p - nrm * 4
        msp.add_text(r.puesta_tierra, height=2.0, dxfattribs={"layer": "LP_PAT", "style": "EXP", "rotation": rot}).set_placement(tuple(g), align=TA.MIDDLE_CENTER)

msp.add_lwpolyline(xy.tolist(), dxfattribs={"layer": "LP_EJE"})
msp.add_lwpolyline(list(road.coords), dxfattribs={"layer": "VIA_OSM"})
for i, v in enumerate(meta["vertices"]):
    msp.add_circle(v, 4, dxfattribs={"layer": "LP_VERTICES"})
    msp.add_text(f"V{i:02d}", height=4, dxfattribs={"layer": "LP_VERTICES", "style": "EXP"}).set_placement((v[0] + 5, v[1] + 5))
for nm, (lon, lat) in [(p["nombre"].upper(), (p["lon"], p["lat"])) for p in [INICIO] + DERIVS + [FIN]]:
    x, y = to_utm(lon, lat); msp.add_text(nm, height=15, dxfattribs={"layer": "LOCALIDADES", "style": "EXP"}).set_placement((x + 20, y - 40))
# cuadrícula UTM cada 1 km
x0, y0 = xy.min(0) - 500; x1, y1 = xy.max(0) + 500
for gx in range(int(x0 // 1000) * 1000, int(x1) + 1001, 1000):
    msp.add_line((gx, y0), (gx, y1), dxfattribs={"layer": "CUADRICULA_UTM"})
    msp.add_text(f"E {gx}", height=12, dxfattribs={"layer": "CUADRICULA_UTM", "style": "EXP", "rotation": 90}).set_placement((gx - 4, y0 + 20))
for gy in range(int(y0 // 1000) * 1000, int(y1) + 1001, 1000):
    msp.add_line((x0, gy), (x1, gy), dxfattribs={"layer": "CUADRICULA_UTM"})
    msp.add_text(f"N {gy}", height=12, dxfattribs={"layer": "CUADRICULA_UTM", "style": "EXP"}).set_placement((x0 + 20, gy + 4))
# cuadro de coordenadas en el plano (al sureste del trazado)
cx, cy = xy[:, 0].min() + 9000, xy[:, 1].min() + 200
th, rh = 6.0, 10.0; cols = [0, 70, 140, 270, 400, 470, 540]
hdrs = ["ESTRUCT.", "ARMADO", "ESTE (m)", "NORTE (m)", "COTA (m)", "POSTE", "RET/PAT"]
per = 40
msp.add_text(f"CUADRO DE COORDENADAS DE ESTRUCTURAS – UTM WGS84 ZONA {ZONA_UTM.replace(' ', '')}", height=12, dxfattribs={"layer": "CUADRO_COORDENADAS", "style": "EXP"}).set_placement((cx, cy + 40))
for blkn in range(math.ceil(n / per)):
    bx = cx + blkn * 640
    for j, h in enumerate(hdrs):
        msp.add_text(h, height=th, dxfattribs={"layer": "CUADRO_COORDENADAS", "style": "EXP"}).set_placement((bx + cols[j], cy + 15))
    msp.add_line((bx, cy + 10), (bx + 620, cy + 10), dxfattribs={"layer": "CUADRO_COORDENADAS"})
    for k, (_, r) in enumerate(E.iloc[blkn * per:(blkn + 1) * per].iterrows()):
        yy = cy - k * rh
        vals = [r.estructura, r.armado, f"{r.este:.3f}", f"{r.norte:.3f}", f"{r.cota_m:.2f}", r.poste, f"{int(r.n_retenidas)}/{r.puesta_tierra}"]
        for j, v in enumerate(vals):
            msp.add_text(v, height=th, dxfattribs={"layer": "CUADRO_COORDENADAS", "style": "EXP"}).set_placement((bx + cols[j], yy))
doc.set_modelspace_vport(height=(y1 - y0) * 1.1, center=((x0 + x1) / 2, (y0 + y1) / 2))
dxf = OUT / "LP-00_PLANO_GEORREFERENCIADO_ESTRUCTURAS_UTM.dxf"
doc.saveas(dxf)

# ---------------- Excel y CSV de coordenadas
def gms(v, pos, neg):
    s = pos if v >= 0 else neg; v = abs(v); g = int(v); m = int((v - g) * 60); sec = ((v - g) * 60 - m) * 60
    return f"{g}°{m:02d}'{sec:05.2f}\" {s}"
wb = Workbook(); ws = wb.active; ws.title = "COORDENADAS"
F = Font(name="Arial", size=9); thin = Side(style="thin", color="A6A6A6"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
ws["A1"] = "COORDENADAS DE ESTRUCTURAS – LP 22,9 kV CHACACHACA – CUTURAPI – YUNGUYO"; ws["A1"].font = Font(name="Arial", size=12, bold=True)
ws["A2"] = f"Datum WGS84 – Proyección UTM zona {ZONA_UTM} (EPSG:{EPSG}). Cotas: DEM Copernicus GLO-30 (validar con topografía de campo)."; ws["A2"].font = Font(name="Arial", size=8, italic=True)
hd = ["N.°", "Estructura", "Progresiva (m)", "Este (m)", "Norte (m)", "Cota (m s.n.m.)", "Latitud (°)", "Longitud (°)", "Latitud (GMS)", "Longitud (GMS)",
      "Vano adelante (m)", "Ángulo (°)", "Armado", "Poste CAC", "Retenidas", "Puesta a tierra"]
for j, h in enumerate(hd, 1):
    c = ws.cell(4, j, h); c.font = Font(name="Arial", size=9, bold=True); c.fill = PatternFill("solid", fgColor="D9E1F2"); c.border = BOX
    c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
for i, r in E.iterrows():
    vals = [int(r.N), r.estructura, round(r.progresiva_m, 2), round(r.este, 3), round(r.norte, 3), round(r.cota_m, 2), round(r.lat, 7), round(r.lon, 7),
            gms(r.lat, "N", "S"), gms(r.lon, "E", "O"), None if pd.isna(r.vano_adelante_m) else round(r.vano_adelante_m, 2), round(r.angulo_deg, 2),
            r.armado, r.poste, int(r.n_retenidas), r.puesta_tierra]
    for j, v in enumerate(vals, 1):
        c = ws.cell(5 + i, j, v); c.font = F; c.border = BOX
        if j in (3, 4, 5, 11): c.number_format = "#,##0.000" if j in (4, 5) else "#,##0.00"
for col, w in zip("ABCDEFGHIJKLMNOP", [5, 10, 12, 14, 15, 11, 12, 12, 17, 17, 11, 9, 9, 9, 9, 10]): ws.column_dimensions[col].width = w
ws.freeze_panes = "C5"
wb.save(OUT / "Coordenadas_Estructuras_UTM.xlsx")
# CSV formato PENZD (punto, norte, este, cota, descripción) para estación total / Civil 3D
with open(OUT / "Coordenadas_PENZD_estacion_total.csv", "w", encoding="utf-8") as f:
    for r in E.itertuples():
        f.write(f"{r.N},{r.norte:.3f},{r.este:.3f},{r.cota_m:.2f},{r.estructura}_{r.armado}\n")
print("OK", dxf, n)
