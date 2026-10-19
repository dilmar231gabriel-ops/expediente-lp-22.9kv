# Expediente técnico de Línea Primaria 22,9 kV – plantilla automatizada

Genera **el expediente técnico completo** de una línea primaria trifásica de 22,9 kV para electrificación rural en el Perú
(RD 018/024/026/029-2003-EM/DGE y CNE-Suministro 2011) a partir de **un solo archivo de configuración** (`proyecto.yaml`)
y de los datos geográficos del lugar (modelo de elevación + ruta).

Cambia el lugar → cambias `proyecto.yaml` → ejecutas un comando → obtienes los 11 volúmenes.

```
python generar.py proyectos/mi-proyecto/proyecto.yaml
```

| Sale | Formato |
|---|---|
| Carátula, Vol. I Ficha técnica, II Resumen ejecutivo, III Memoria descriptiva | Word + PDF |
| Vol. IV Especificaciones técnicas de suministro (ETS-LP-01…13) y de montaje | Word + PDF |
| Vol. V Metrado, APU, presupuesto, GG, supervisión, cronogramas, fórmula polinómica, inventario por estructura | Excel con fórmulas vivas + PDF + MS Project XML |
| Vol. VI Cálculos justificativos + Anexos 1–9 (aislamiento, pararrayos, PAT, CMC, cimentación, CME, retenidas, caída de tensión, planilla) | Word + 9 Excel con fórmulas + PDF |
| Vol. VII Planos: ubicación, planta-poligonal, perfil y planimetría (todas las hojas), unifilar, cruce, 14 láminas de armados, coordenadas de postes, KML/KMZ | DXF (AutoCAD) + DXF compatible R2010 + PDF + Excel + Google Earth |
| Vol. VIII Geología/geotecnia de gabinete + TdR del EMS · Vol. IX Flujo, cortocircuito y protecciones · Vol. X Requerimientos ejecutor/supervisor · Vol. XI Riesgos, panel fotográfico, cotizaciones, datos pendientes | Word + Excel + PDF |
| Informe de verificación cruzada (17 comprobaciones CONFORME / NO CONFORME) y ZIP por volumen y completo | Word + PDF + ZIP |

> **Importante.** Es una herramienta de ingeniería de gabinete. Los datos que solo se obtienen en campo (topografía, mecánica de suelos,
> resistividad, factibilidad de la concesionaria, cotizaciones) se marcan como **SUPUESTO / PENDIENTE** y se listan en el Vol. XI.
> El expediente debe ser revisado, completado y firmado por un ingeniero colegiado y habilitado. La plantilla no agrega número de CIP, firma ni sello.

---

## 1. Instalación (una vez)

1. **Python 3.10+** → <https://www.python.org/downloads/> (en Windows marque *Add Python to PATH*).
2. **LibreOffice** (gratuito) → <https://www.libreoffice.org>. Se usa para recalcular los Excel y convertir a PDF.
   Si no queda en el PATH, defina la variable `SOFFICE` con la ruta de `soffice.exe`.
3. En la carpeta del repositorio:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows   (Linux/macOS: source .venv/bin/activate)
   pip install -r requirements.txt
   ```

## 2. Probar con el ejemplo incluido

```bash
python generar.py proyectos/chacachaca-cuturapi-yunguyo/proyecto.yaml
```
Tarda 2–4 minutos. El resultado queda en `salida/chacachaca-cuturapi-yunguyo/` (carpeta `EXPEDIENTE_…` y carpeta `ZIPS`).

Hay un segundo ejemplo (`proyectos/ejemplo-eje-libre-2-derivaciones/`, **datos ficticios**) que demuestra un eje dibujado libremente
y dos derivaciones.

## 3. Hacer la línea en OTRO lugar

```bash
python herramientas/nuevo_proyecto.py urcos-cusipata --inicio "Urcos" -71.6234 -13.6861 --fin "Cusipata" -71.5003 -13.9082
#   → edite proyectos/urcos-cusipata/proyecto.yaml (campos "<<< COMPLETAR")
python herramientas/preparar_datos.py proyectos/urcos-cusipata/proyecto.yaml --ruta     # DEM + OSM + ruta (requiere internet)
python generar.py proyectos/urcos-cusipata/proyecto.yaml --hasta 3                      # revise trazado y estructuras
python generar.py proyectos/urcos-cusipata/proyecto.yaml                                # expediente completo
```
Guía detallada, con lo que hay que buscar en SENAMHI, INEI, CNE y la concesionaria: **[docs/GUIA_NUEVO_PROYECTO.md](docs/GUIA_NUEVO_PROYECTO.md)**.

## 4. Estructura del repositorio

```
generar.py                      ← único comando: ejecuta los 15 pasos
plantilla/proyecto.yaml         ← configuración comentada para un proyecto nuevo
proyectos/<proyecto>/           ← un proyecto = proyecto.yaml + carpeta datos/
src/                            ← motor de cálculo y generadores (no se toca para un proyecto nuevo)
   params.py                       lee el YAML; constantes de norma (conductores AAAC, hipótesis)
   catalogo.py                     materiales, listas por armado, precios de referencia
   p01_trazado … p15_paquete       los 15 pasos (ver docs/METODOLOGIA_Y_RAZONAMIENTO.md)
herramientas/                   ← nuevo_proyecto, preparar_datos, conversores DXF (R12, AutoLISP)
docs/                           ← metodología, normas, guía, estructura del expediente, FAQ, GitHub
.github/workflows/              ← (opcional) genera el expediente en GitHub Actions
```

## 5. Los 15 pasos

| # | Paso | Resultado principal |
|---|---|---|
| 1 | Trazado | eje rectificado (desplazamiento de la vía, simplificación, sin quiebres > 60°), derivaciones |
| 2 | Perfil | perfil del terreno sobre el DEM, cruces con vías y ríos, edificaciones cercanas |
| 3 | Ingeniería | demanda a 20 años, selección del conductor, cambio de estado, plantillado, armados, postes, retenidas, PAT |
| 4–5 | Anexos 1–9 | hojas Excel con fórmulas (aislamiento, pararrayos, PAT, CMC, cimentación, CME, retenidas, ΔV, planilla) |
| 6 | Presupuesto | metrado desde la planilla, APU, GG, utilidad, IGV, supervisión, cronogramas, fórmula polinómica |
| 7–10 | Planos | láminas de armados, planos generales, KML, plano georreferenciado y coordenadas |
| 11 | Verificación | 17 comprobaciones cruzadas Excel ↔ motor ↔ planilla ↔ presupuesto |
| 12–14 | Documentos | volúmenes en Word |
| 15 | Paquete | estructura de carpetas, PDF, MS Project XML, ZIP |

`--desde N` / `--hasta N` rehacen solo una parte (por ejemplo, después de cambiar precios: `--desde 6`).

## 6. Qué se puede y qué no se puede cambiar sin tocar código

Se cambia en `proyecto.yaml`: nombres, ubicación, coordenadas, ruta, derivaciones (0, 1 o varias), cargas, clima y zona de carga CNE,
distancias, vanos, postes, resistividad, línea de fuga, Scc, plazo, tipo de cambio, precios (`precios:`), textos de la memoria.

Es fijo (el "kit de materiales"): conductor **AAAC 70 mm²**, aisladores PIN ANSI 56-4 y poliméricos 36 kV, equipos 38 kV 170 kV-BIL,
pararrayos 24 kV, armados PS1-3, PA1-3, PA2-3, TS-3, PR3-3, DT-3, PSER-3, PTH-3. Si el lugar exige algo fuera del kit
(p. ej. altitud de diseño mayor de unos 3 950 m s.n.m. con 20 mm/kV, donde el PIN 56-4 de 685 mm ya no alcanza la línea de fuga, o contaminación fuerte), la verificación del paso 11 lo marca **NO CONFORME** y hay que ampliar
`src/catalogo.py`. Ver [docs/METODOLOGIA_Y_RAZONAMIENTO.md](docs/METODOLOGIA_Y_RAZONAMIENTO.md) §8.

## 7. Documentación

- [Guía para un proyecto nuevo](docs/GUIA_NUEVO_PROYECTO.md)
- [Metodología y razonamiento](docs/METODOLOGIA_Y_RAZONAMIENTO.md)
- [Normas y criterios](docs/NORMAS_Y_CRITERIOS.md)
- [Estructura del expediente](docs/ESTRUCTURA_DEL_EXPEDIENTE.md)
- [Datos de campo pendientes](docs/DATOS_DE_CAMPO_PENDIENTES.md)
- [Preguntas frecuentes (AutoCAD, LibreOffice, precios…)](docs/PREGUNTAS_FRECUENTES.md)
- [Cómo subir este repositorio a GitHub](docs/COMO_SUBIR_A_GITHUB.md)

## 8. Créditos

Proyectista del ejemplo incluido: Ingeniero Dilmar Humberto Ccora.
Datos abiertos: Copernicus DEM GLO-30 (ESA), OpenStreetMap (ODbL), INEI, SENAMHI, BCRP.
