# Preguntas frecuentes

### AutoCAD no abre el DXF o se cierra al abrirlo
1. Use la carpeta **`DXF compatible (R2010 simple)`**: tiene solo polilíneas, círculos y textos con estilo Standard. Es la versión que
   abre en cualquier AutoCAD (incluido 2027), BricsCAD, ZWCAD, DraftSight y LibreCAD.
2. En AutoCAD, en vez de doble clic: comando `DXFIN` (o *Abrir* → tipo de archivo *DXF*), o `INSERT` / `INSERTAR` el DXF en un dibujo vacío.
3. Convierta a R12: `python herramientas/dxf_a_r12.py ENTRADA.dxf SALIDA_R12.dxf`.
4. Último recurso, sin abrir archivos: genere un programa AutoLISP que dibuja el plano dentro de AutoCAD:
   `python herramientas/dxf_a_autolisp.py ENTRADA.dxf PLANO.lsp DIBUJAR "Título"` → en AutoCAD `APPLOAD` → cargar `PLANO.lsp` → escribir `DIBUJAR`.
5. Para obtener DWG: abra el DXF y use *Guardar como* → `.dwg`.
6. Cualquier DXF se puede convertir a la versión simple con `python src/dxf_compatible.py CARPETA_O_ARCHIVO`.

### "No se encontró LibreOffice"
Instálelo desde <https://www.libreoffice.org>. Si ya está instalado, defina la variable de entorno `SOFFICE`:
- Windows (PowerShell): `$env:SOFFICE="C:\Program Files\LibreOffice\program\soffice.exe"`
- macOS: `export SOFFICE=/Applications/LibreOffice.app/Contents/MacOS/soffice`
Cierre LibreOffice antes de generar (si está abierto puede bloquear la conversión).

### ¿Puedo abrir los Excel en Microsoft Excel?
Sí. Tienen fórmulas vivas; LibreOffice solo se usa para dejarlos recalculados. Las celdas amarillas son los datos de entrada.

### ¿Cómo pongo mis precios?
En `proyecto.yaml`:
```yaml
precios:
  "1.01": 1450.00     # código del catálogo: precio en S/ sin IGV
  "3.01": 4.10
```
Los códigos están en `src/catalogo.py` y en la hoja BP del presupuesto. Luego: `python generar.py ... --desde 6`.

### La verificación sale NO CONFORME
Lea el detalle impreso al final del paso 11 (también en el Vol. VI 2.9):
- *Conductor del kit … NO cumple ΔV*: línea muy larga o cargas grandes → revise la demanda, divida en dos alimentadores o analice 95 mm².
- *Aislamiento / BIL*: altitud de diseño alta → ver `METODOLOGIA_Y_RAZONAMIENTO.md` §8.
- *Distancias al terreno*: perfil muy accidentado → baje `vano_max_m` o permita postes más altos en `diseno.postes`.
- *Metrado*: avise como error (no debería ocurrir).

### Error "ERROR en el paso N"
Abra `salida/<proyecto>/trabajo/logs/NN_*.log`; el final del archivo indica la causa. Errores típicos: el DEM no cubre la ruta,
la ruta no es una LineString, una carga apunta a una derivación que no existe, coordenadas con lon/lat invertidas.

### ¿Las coordenadas van como lon, lat o lat, lon?
En `proyecto.yaml` siempre **lon** (oeste = negativo, p. ej. −71.62) y **lat** (sur = negativo, p. ej. −13.68).

### ¿Cuánto tarda?
Entre 2 y 5 minutos según la longitud de la línea (la mayor parte es la conversión a PDF).

### ¿Sirve para 10 kV, 13,2 kV o monofásico?
No directamente: la plantilla está hecha para 22,9 kV trifásico (armados, equipos, aislamiento). Habría que ampliar el catálogo y los cálculos.
