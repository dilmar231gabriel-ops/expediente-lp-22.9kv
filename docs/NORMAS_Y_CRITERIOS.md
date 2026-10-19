# Normas y criterios de diseño

## Marco normativo

| Norma | Uso en la plantilla |
|---|---|
| Ley de Concesiones Eléctricas (D.L. 25844) y reglamento | marco general |
| Ley General de Electrificación Rural (Ley 28749) y reglamento (D.S. 025-2007-EM) | marco de proyectos rurales |
| **Código Nacional de Electricidad – Suministro 2011** (R.M. 214-2011-MEM/DM) | zonas de carga (viento, hielo, temperatura), distancias de seguridad, faja de servidumbre, factores de sobrecarga |
| **R.D. 018-2003-EM/DGE** – Bases para el diseño de líneas y redes primarias | caída de tensión, aislamiento por altitud, conductores AAAC, hipótesis, cálculo mecánico, nivel isoceráunico |
| R.D. 024-2003-EM/DGE – Soportes normalizados | armados y estructuras |
| R.D. 026-2003-EM/DGE – Suministro de materiales y equipos | especificaciones técnicas (Vol. IV) |
| R.D. 029-2003-EM/DGE – Montaje de líneas y redes primarias | especificaciones de montaje (Vol. IV) |
| R.D. 016-2008-EM/DGE – NTCSER | tolerancia de tensión ±5 % (Vol. IX) |
| R.M. 111-2013-MEM/DM – RESESATE | seguridad en el trabajo |
| IEC 60815 | línea de fuga por nivel de contaminación |
| IEC 60071-1/2 | coordinación de aislamiento |
| IEC 60099-4/5, ANSI C62.22 | pararrayos y márgenes de protección |
| ANSI C29 / C37.43 | aisladores; fusibles tipo K |
| NTP 339.027 | postes de concreto armado centrifugado |
| Norma E.030 | zonificación sísmica (geotecnia) |

## Valores de diseño por defecto (se cambian en `proyecto.yaml`)

| Parámetro | Valor | Fuente / criterio |
|---|---|---|
| Tensión nominal / máxima | 22,9 / 25 kV, 3ø, 60 Hz | RD 018 |
| Caída de tensión máxima | 5 %; se diseña con ≤ 85 % del límite | RD 018; reserva del proyectista |
| Pérdidas | ≤ 3,5 % de la MD | criterio usual en electrificación rural |
| Factor de potencia | 0,90 | RD 018 |
| Potencia de cortocircuito | 250 MVA (SUPUESTO) | confirmar con la concesionaria |
| Conductor | AAAC 70 mm², 19 hilos, E = 60 760 N/mm², α = 23·10⁻⁶ /°C, σr = 295,8 N/mm² | RD 018 Cuadro de conductores |
| EDS inicial / final | 18 % / 15 % UTS | RD 018 |
| Tiro máximo | 60 % UTS | RD 018 / CNE-S |
| CREEP | +10 °C en la hipótesis de flecha máxima | práctica usual |
| Zona de carga | Área 0: 26 m/s, 10 °C · Área 1: 29 m/s, 5 °C, hielo 6 mm · Área 2: 31,5 m/s | CNE-S 2011 (verificar en la Tabla 250-1.A) |
| K de presión de viento | 0,613 (≤ 3 000 m) / 0,455 (> 3 000 m) | CNE-S 250.C |
| Distancia al terreno | 6,0 m (general), 7,0 m (cruce de carreteras) + 0,30 m margen DEM | CNE-S Tabla 232-1 |
| Faja de servidumbre 22,9 kV | 11 m (5,5 m a cada lado) | CNE-S Tabla 219 |
| Línea de fuga | 20 mm/kV (contaminación media) | IEC 60815 |
| Corrección por altitud | fch = 1 + 1,25(h − 1 000)·10⁻⁴ | RD 018 |
| Postes | CAC 12/300, 12/400, 13/400 daN; empotramiento L/10 + 0,60 m | RD 024; práctica |
| FS postes / retenidas / crucetas | 2 / 2 / 1,5–2 | RD 018 |
| Retenida | cable A°G° Siemens-Martin 10 mm, 30,92 kN, 37° | RD 026 |
| Bloque de anclaje | 0,50 × 0,50 × 0,20 m en excavación 0,80 × 0,80 × 2,00 m | cálculo Anexo 7 (FS ≥ 2) |
| Puesta a tierra | varilla Cu 16 mm × 2,40 m; ρ = 100 Ω·m (SUPUESTO); R ≤ 25 Ω en equipos | RD 018 |
| Vano máximo / mínimo | 220 m / 15 m | criterio de plantillado |
| Anclaje intermedio | cada ~3 km en alineamientos rectos | práctica |
| Fusibles tipo K | ≥ 1,5 × I de carga; mínimo 10 K en derivaciones; el del arranque uno mayor que el mayor aguas abajo | criterio de coordinación |
| Reconectador | 38 kV, 170 kV-BIL, 630 A, 12,5 kA; 51 fase = 2·Imax; 51N ≈ 25 % | criterio preliminar (Vol. IX) |
| Utilidad / IGV | 8 % / 18 % | proyecto.yaml |

> Revise siempre los valores con la versión vigente de cada norma: la plantilla los toma de las versiones citadas.
