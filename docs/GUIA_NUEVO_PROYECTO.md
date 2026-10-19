# Guía: hacer la línea primaria en otro lugar

Esta guía responde a la pregunta *"quiero hacer la línea primaria en otro lugar, ¿qué hago?"*.
El código no se modifica: todo lo propio del lugar va en `proyectos/<mi-proyecto>/proyecto.yaml` y en su carpeta `datos/`.

---

## Paso 0 – Reunir la información de partida

| Dato | Dónde se obtiene | Campo en `proyecto.yaml` |
|---|---|---|
| Punto de inicio (red existente 22,9 kV) y punto final | Google Earth (clic derecho → *¿Qué hay aquí?* o marca de posición → propiedades) en grados decimales | `puntos.inicio`, `puntos.fin` |
| Localidades que se derivan de la troncal | Google Earth | `puntos.derivaciones` (lista; puede estar vacía) |
| Ruta de la línea | (a) carretera: `preparar_datos.py --ruta`; (b) eje dibujado en Google Earth (*Agregar ruta* → guardar como KML) | `trazado.archivo_ruta`, `ruta_es_via` |
| Zona UTM | según la longitud: 17 S (−84° a −78°), 18 S (−78° a −72°), 19 S (−72° a −66°); `nuevo_proyecto.py` la calcula desde el punto de inicio | `epsg_utm` 32717 / 32718 / 32719 |
| Población 2017 por localidad o distrito | INEI – Censo 2017 (REDATAM / *Resultados definitivos* por departamento) | `mercado.cargas[].pob2017` |
| Habitantes por vivienda, tasa de crecimiento | INEI (mismo censo); si no tiene, deje el SUPUESTO marcado | `mercado.hab_viv`, `tasa_viv` |
| Temperaturas | SENAMHI – normales climáticas de la estación más cercana | `clima.t_min_media`, `t_max_media`, `t_media` |
| Zona de carga (viento, hielo) | CNE-Suministro 2011, Regla 250.B y Tabla 250-1.A, según altitud | `clima.zona_carga`, `viento_ms`, `t_viento`, `hielo_mm`, `K_viento` |
| Nivel isoceráunico | RD 018-2003-EM/DGE, Cuadro 6.1 (o mapa isoceráunico) | `sistema.nivel_isoceraunico` |
| Empresa concesionaria | la de la zona (Electro Sur Este, Electro Puno, Electrocentro, Hidrandina, Electronoroeste, Seal, …) | `proyecto.concesionaria` |
| Potencia de cortocircuito en el punto de diseño | factibilidad de suministro de la concesionaria (si no la tiene: SUPUESTO 250 MVA) | `sistema.Scc_MVA` |
| Tipo de cambio | BCRP – tipo de cambio SBS venta del día | `economico.tipo_cambio`, `tipo_cambio_fuente` |
| Textos de la memoria | redacción propia del proyectista | `textos.*` |

Regla de oro: **si un dato no tiene fuente, no se inventa**: se deja el valor típico con el comentario `SUPUESTO` y el expediente lo
lista en el Vol. XI como dato pendiente.

## Paso 1 – Crear la carpeta del proyecto

```bash
python herramientas/nuevo_proyecto.py mi-proyecto --inicio "Nombre inicio" LON LAT --fin "Nombre fin" LON LAT
```
Crea `proyectos/mi-proyecto/proyecto.yaml` (copia comentada de `plantilla/proyecto.yaml`) y la carpeta `datos/`.
Complete todos los campos marcados con `<<< COMPLETAR`.

## Paso 2 – Datos geográficos

### Opción A: automática (requiere internet)
```bash
python herramientas/preparar_datos.py proyectos/mi-proyecto/proyecto.yaml --ruta
```
Descarga a `datos/`:
- `dem.tif` – Copernicus DEM GLO-30 (30 m) recortado al área (+3 km de margen),
- `osm_corredor.geojson` – vías, ríos, edificaciones y centros poblados de OpenStreetMap,
- `ruta_via.geojson` – ruta por carretera entre inicio y fin (OSRM). Con ella use `ruta_es_via: true` y `desplazamiento_m: 40`.

### Opción B: manual (sin internet o si un servicio falla)
- **DEM**: <https://portal.opentopography.org> → *Copernicus GLO-30* → dibujar el área → GeoTIFF → guardar como `datos/dem.tif` (WGS 84).
  También sirve SRTM 30 m. El DEM debe cubrir toda la ruta con margen.
- **Ruta**: en Google Earth Pro, *Agregar → Ruta*, dibuje el eje desde el inicio hasta el fin, clic derecho → *Guardar lugar como…* → KML.
  Ponga el archivo en `datos/` y escriba su nombre en `trazado.archivo_ruta` (`ruta_es_via: false`, `desplazamiento_m: 0`).
- **OSM** (opcional): <https://overpass-turbo.eu> con la consulta del archivo `herramientas/preparar_datos.py` → *Exportar → GeoJSON* →
  `datos/osm_corredor.geojson`. Sin este archivo el expediente se genera igual, pero sin cruces ni edificaciones detectadas.

## Paso 3 – Revisar el trazado y las estructuras antes de todo lo demás

```bash
python generar.py proyectos/mi-proyecto/proyecto.yaml --hasta 3
```
Revise en `salida/mi-proyecto/trabajo/`:
- `trazado_rectificado.geojson` (ábralo en Google Earth / QGIS / geojson.io): ¿el eje evita poblados, lagunas, quebradas?
- `perfil_troncal.csv`, `cruces.csv`, `edificaciones_cercanas.csv`.
- `planilla_estructuras.csv`: número de postes, armados, vanos, retenidas, observaciones.

Si algo no le gusta, corrija la ruta o los parámetros de `trazado:` y repita. Ajustes típicos:
| Problema | Ajuste |
|---|---|
| La línea queda pegada a la carretera | aumente `desplazamiento_m` o cambie `lado` |
| Muchos vértices pequeños | aumente `tolerancia_simplificacion_m` (15 → 30) |
| Vértice en U o ángulo > 60° | `angulo_max_quiebre_deg` (máx. 60) o dibuje un vértice intermedio |
| Pasa sobre casas | edite el KML de la ruta y aléjela |

## Paso 4 – Generar el expediente

```bash
python generar.py proyectos/mi-proyecto/proyecto.yaml
```
Al final del paso 11 se imprimen las 17 verificaciones. **Todas deben salir CONFORME.** Si alguna sale NO CONFORME, el detalle dice
qué falla (por ejemplo, la línea de fuga a gran altitud o la caída de tensión de una línea muy larga). Ver `docs/PREGUNTAS_FRECUENTES.md`.

## Paso 5 – Revisar y completar

1. Lea `00 INFORME DE GENERACION Y VERIFICACION.pdf`.
2. Revise el Vol. XI → *Datos de campo y documentos externos pendientes* y gestione cada uno.
3. Reemplace precios por cotizaciones vigentes en `proyecto.yaml → precios:` y regenere desde el paso 6 (`--desde 6`).
4. Con la topografía de replanteo, sustituya el DEM por un DEM/perfil de campo y regenere desde el paso 2.

## Cambiar datos después

| Cambié… | Regenerar desde |
|---|---|
| Ruta, puntos, derivaciones, DEM | `--desde 1` |
| Cargas, clima, distancias, postes, resistividad | `--desde 3` |
| Precios, tipo de cambio, plazo | `--desde 6` |
| Proyectista, fecha, nombre del proyecto (van en membretes de planos y Excel) | `--desde 4` |
| Solo textos de la memoria (`textos:`) | `--desde 12` |
