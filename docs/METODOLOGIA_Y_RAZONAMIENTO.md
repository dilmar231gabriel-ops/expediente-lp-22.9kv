# Metodología y razonamiento

Este documento explica **qué hace cada paso, con qué criterio y por qué**, para que el proyectista pueda defender el expediente
y modificar la plantilla con conocimiento de causa. Las referencias normativas están detalladas en `NORMAS_Y_CRITERIOS.md`.

Principios que guían todo el código:

1. **Una sola fuente de verdad.** Cada número sale de un único cálculo (motor en Python) y se escribe en los Excel como fórmula viva;
   el paso 11 comprueba que el Excel recalculado y el motor coincidan.
2. **Nada inventado.** Lo que no tiene fuente se marca `SUPUESTO` (celdas amarillas en los Excel) y se lista en el Vol. XI.
3. **Trazabilidad.** Cada valor de entrada lleva su fuente (columna *Fuente* en los anexos, comentario en `proyecto.yaml`).
4. **Kit de materiales fijo.** Un conjunto cerrado de armados, aisladores, equipos y conductor, con precios y láminas preparados;
   el cálculo verifica que el kit sirva para el lugar en vez de rediseñar materiales cada vez.

---

## Paso 1 – Trazado (`p01_trazado.py`)

- Lee la ruta (GeoJSON o KML) y la orienta de inicio a fin.
- **Si la ruta es una carretera** (`ruta_es_via: true`) se desplaza `desplazamiento_m` (40 m por defecto) al lado indicado: la RD 018
  pide alejarse de la franja de la vía (≥ 25 m en carreteras importantes) y así los postes no quedan en el derecho de vía.
- Simplificación Douglas-Peucker (`tolerancia_simplificacion_m`): alineamientos largos = menos estructuras de ángulo (más caras).
- Se eliminan quiebres > `angulo_max_quiebre_deg` (60°): el kit llega hasta el armado PA2-3 (30°–60°).
- Se fusionan vértices casi colineales (< 2°) siempre que el nuevo segmento no se acerque a la vía a menos de `dist_min_via_m`.
- Inicio y fin se fijan exactamente en los puntos de `proyecto.yaml`; cada derivación se conecta al punto más cercano de la troncal
  (allí irá una estructura DT-3).

## Paso 2 – Perfil y cruces (`p02_perfil.py`)

- Muestrea el DEM cada pocos metros a lo largo del eje → `perfil_troncal.csv`.
- Con OpenStreetMap detecta cruces con vías y ríos (`cruces.csv`) y edificaciones a menos de la faja de servidumbre (`edificaciones_cercanas.csv`).
- El DEM Copernicus GLO-30 tiene error vertical de ~2–4 m: por eso se suma un margen (`margen_dem_m`) a las distancias al terreno y
  el replanteo topográfico es obligatorio antes de excavar.

## Paso 3 – Motor de ingeniería (`p03_ingenieria.py`)

### 3.1 Demanda (estudio de mercado simplificado)
Por cada carga: viviendas 2017 = población / hab_viv → proyección geométrica con `tasa_viv` → abonados = viviendas × `coef_elec` →
energía doméstica = abonados × consumo unitario (crece con `tasa_cu`) × 12 → + cargas comercial, uso general, productivo y alumbrado
público (porcentajes) → + pérdidas de distribución → máxima demanda = E / (8 760 × factor de carga). Horizonte 20 años.

### 3.2 Selección del conductor
Para AAAC 25, 35, 50, 70 y 95 mm² se calcula ΔV (K·P·L por tramos), corriente, sección mínima por cortocircuito y el costo total
(inversión + valor presente de pérdidas a 20 años). Se exige **ΔV ≤ 85 % del límite de 5 %** (reserva por incertidumbre de la demanda).
Se informa el óptimo económico, pero se **adopta 70 mm² (kit)**; si el kit no cumple, el paso 11 da NO CONFORME.

### 3.3 Cálculo mecánico del conductor
Ecuación de cambio de estado con 7 hipótesis (EDS inicial 18 %, EDS final 15 %, temperatura mínima, viento máximo, hielo, hielo + viento,
temperatura máxima + 10 °C de CREEP). Presión de viento Pv = K·V² con K = 0,613 (≤ 3 000 m) o 0,455 (> 3 000 m). Límite: tiro en el
apoyo ≤ 60 % UTS. Se obtienen parámetros de catenaria para el plantillado (flecha máxima) y para el vano peso (temperatura mínima).

### 3.4 Plantillado automático
- Puntos fijos: inicio, fin, vértices y derivaciones.
- Entre puntos fijos se avanza colocando el poste más lejano posible (≤ vano máximo) que mantenga, en todo el vano, la catenaria de
  flecha máxima por encima de terreno + distancia mínima (6 m general, 7 m en cruces de vía) + margen del DEM. Primero se prueba poste
  de 12 m, luego 13 m.
- Luego se reequilibran los vanos entre puntos fijos (mismo número de vanos, uniformes) eligiendo la alternativa de menor costo, y se
  hace un ajuste local que maximiza el vano menor de cada estructura.

### 3.5 Armados, postes, retenidas y puesta a tierra
| Condición | Armado |
|---|---|
| Primera estructura (punto de diseño) | PSER-3 (reconectador + cut-out + pararrayos) |
| Última estructura | PTH-3 (terminal con cut-out + pararrayos) |
| Derivación | DT-3 (con seccionamiento PSEC-3P) |
| Ángulo 30°–60° | PA2-3 |
| Anclaje cada ~3 km en alineamientos largos | PR3-3 |
| Ángulo 5°–30° | PA1-3 |
| 0°–5° | PS1-3 |
| Vano peso negativo a temperatura mínima (arrancamiento) en PIN | TS-3 (cadenas de anclaje) |

Cargas por estructura (RD 018 / CNE-S, hipótesis de viento máximo): MVC (viento sobre conductores), MTC (tiro por ángulo o anclaje),
MVP (viento sobre el poste), MCW (cargas verticales excéntricas) → QN en la punta. Se elige el poste (12/300, 12/400, 13/400 daN) con
FS = 2; si no alcanza, se agregan retenidas (cable SM 10 mm, FS 2, 37°). PAT: una de cada tres estructuras + adyacentes a equipos (PAT-1),
estructuras con equipos PAT-2 (≤ 25 Ω).

## Pasos 4 y 5 – Anexos de cálculo (Excel con fórmulas)

| Anexo | Contenido | Criterio principal |
|---|---|---|
| 1 | Aislamiento por contaminación, frecuencia industrial e impulso | Lf = Lf0·Umax·fch; fch = 1 + 1,25(h − 1 000)·10⁻⁴ |
| 2 | Pararrayos y coordinación de aislamiento | MCOV, TOV, márgenes MP1–MP3 (ANSI C62.22) |
| 3 | Puesta a tierra | R = 0,366·(ρ/L)·log(4L/d); sensibilidad a ρ |
| 4 | Cálculo mecánico del conductor + tabla de templado | ≤ 60 % UTS |
| 5 | Cimentación (Sulzberger) | σ ≤ capacidad lateral; presión vertical ≤ qa |
| 6 | Estructuras, crucetas y retenidas, por armado y estructura por estructura | FS poste 2; cruceta 1,5/2 |
| 7 | Retenidas y bloque de anclaje | FS cable ≥ 2, FS bloque ≥ 2 |
| 8 | Parámetros eléctricos, ΔV y pérdidas | ΔV ≤ 5 % |
| 9 | Planilla de estructuras y distancias por vano | distancias al terreno y entre fases |

Las celdas amarillas son datos de entrada (editables); el resto son fórmulas. LibreOffice recalcula cada libro y se aborta si hay #¡VALOR!, #REF!, etc.

## Paso 6 – Presupuesto

Metrado **desde la planilla** (cada estructura suma su lista de materiales por armado, retenidas, PAT y conductor por vano); APU de montaje
con jornales CAPECO y rendimientos; transporte como % del suministro; gastos generales desagregados (fijos y variables ligados al plazo),
utilidad, IGV, supervisión, coordinación y liquidación; cronograma Gantt escalado al plazo; calendario valorizado; fórmula polinómica.
Precios: catálogo de referencia (`src/catalogo.py`, columna FUENTE) o los que ponga en `proyecto.yaml → precios:`.

## Pasos 7 a 10 – Planos

DXF (AutoCAD) con capas y membrete, y PDF de cada plano: ubicación, planta-poligonal con cuadro de coordenadas, perfil y planimetría por
hojas (tabla de estructuras bajo el perfil), unifilar con fusibles y equipos, cruce, 14 láminas A4 de armados con lista de materiales;
KML/KMZ para Google Earth y plano georreferenciado con coordenadas UTM de cada poste. El paso 15 añade una versión "DXF compatible"
(solo polilíneas, círculos y textos, R2010) por si alguna versión de AutoCAD no abre la completa.

## Paso 11 – Verificación cruzada (17 comprobaciones)

Excel ↔ motor (ΔV, CMC), conductor del kit, verificación estructura por estructura, retenidas, cimentación, aislamiento, BIL de equipos,
pararrayos, PAT, 60 % UTS, distancias al terreno, arrancamiento, metrado ↔ planilla, resumen del presupuesto, calendario valorizado y
fórmula polinómica. Resultado en el Vol. VI (2.9) y en el informe de generación.

## Pasos 12 a 15 – Documentos y paquete

Los textos de los volúmenes se arman con los resultados (`datos_clave.json`) y la configuración: nombres de puntos, derivaciones,
estructuras, fusibles (seleccionados como el menor tipo K ≥ 1,5 × I de carga, mínimo 10 K en derivaciones; el del arranque, uno mayor
que el mayor aguas abajo), clima, plazo, concesionaria, textos propios. Luego se ensambla la estructura de 11 volúmenes, se convierten
a PDF y se comprimen.

## 8. Límites del kit y cómo ampliarlo

| Límite | Por qué | Qué hacer si se supera |
|---|---|---|
| Altitud de diseño ≲ 3 950 m s.n.m. (con 20 mm/kV) | PIN ANSI 56-4 tiene 685 mm de línea de fuga | Bajar a 16 mm/kV si el ambiente es limpio (justificar) o agregar un aislador PIN 56-5 / polimérico tipo pin al catálogo |
| NBI requerido ≤ 170 kV-BIL (+1 %) | equipos de 38 kV | equipos de 200 kV-BIL (catálogo) |
| Ángulos ≤ 60° | no hay armado PA3-3 en el kit | dos vértices o agregar PA3-3 (catálogo, BOM, lámina) |
| Conductor 70 mm² | catálogo, láminas y Anexo 4 preparados | cambiar `COND`, precios 3.01/4.xx y textos |
| ΔV ≤ 4,25 % con 70 mm² | líneas muy largas o cargas grandes | analizar 95 mm² o regulador de tensión (fuera del kit) |
| Sin cable de guarda | nivel isoceráunico típico ≤ 30–40 | si es alto, agregar cable de guarda (catálogo y armados) |

Para ampliar el kit: `src/catalogo.py` (material, precio, lista por armado `BOM`, descripción `ARM_DESC`), `src/p07_laminas.py` (lámina),
`src/p03_ingenieria.py` (regla de asignación). Ejecute los dos ejemplos para comprobar que todo siga CONFORME.
