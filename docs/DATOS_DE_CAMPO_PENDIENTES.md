# Datos de campo y documentos externos que la plantilla NO puede generar

La plantilla produce ingeniería de gabinete. Los siguientes datos se obtienen fuera de ella; mientras no se tengan, el expediente usa
valores **SUPUESTOS** claramente marcados (celdas amarillas, columna *Fuente*) y los lista en el Vol. XI (Anexo XI-4).

| Dato / documento | Quién lo da | Dónde impacta | Cómo se incorpora |
|---|---|---|---|
| Factibilidad de suministro y fijación del punto de diseño | Concesionaria | punto de inicio, Scc, X/R, Z0, ajustes aguas arriba | `puntos.inicio`, `sistema.Scc_MVA`, `XR_fuente` → `--desde 1` |
| Levantamiento topográfico (poligonal y perfil) | Topógrafo | plantillado, cotas, planos | reemplazar `datos/dem.tif` por un DEM de campo o ajustar la ruta → `--desde 1` |
| Estudio de mecánica de suelos (EMS) | Especialista geotécnico | cimentación (Cp, qa), retenidas (γ, θ), tipo de cemento | celdas amarillas de los Anexos 5 y 7 |
| Resistividad del terreno (Wenner) | Contratista / especialista | número de varillas PAT | `diseno.puesta_tierra.rho` → `--desde 3` |
| CIRA o Plan de Monitoreo Arqueológico | Ministerio de Cultura | requisito previo a excavar | trámite |
| Instrumento de gestión ambiental (DIA/FTA) | Autoridad ambiental competente | certificación ambiental | trámite |
| Autorizaciones de paso / servidumbre | Entidad / propietarios | faja de 11 m | trámite |
| Cotizaciones vigentes (mínimo 3 por ítem) | Proveedores | presupuesto | `precios:` en `proyecto.yaml` → `--desde 6` |
| Catálogos de postes y equipos del fabricante | Fabricantes | verificación de pandeo, cimentación, protecciones | `diseno.postes`, Anexos |
| Registros SAIFI/SAIDI y demanda real | Concesionaria | antecedentes, validación del mercado | `textos.situacion_actual`, `mercado` |
| Población y tasas actualizadas | INEI | demanda | `mercado.cargas` |
| Panel fotográfico de campo | Entidad / contratista | Vol. XI | insertar en el Word |
| Diseño de las redes de cada derivación | Proyecto complementario | tiro sobre la estructura DT-3 | Anexo 6 |
| Número de colegiatura, firma y sello | Proyectista | todas las láminas y documentos | a mano; la plantilla no los agrega |
