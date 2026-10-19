# Estructura del expediente generado

```
salida/<proyecto>/
├── EXPEDIENTE_<NOMBRE_CORTO>/
│   ├── 00 INFORME DE GENERACION Y VERIFICACION.docx / .pdf
│   ├── CARATULA Y SEPARADORES/            carátula, índice y separadores de los 11 volúmenes
│   └── Expediente Tecnico/
│       ├── VOL. I FICHA TECNICA/
│       ├── VOL. II RESUMEN EJECUTIVO/
│       ├── VOL. III MEMORIA DESCRIPTIVA/
│       ├── VOL. IV ESPECIFICACIONES TECNICAS/          suministro (ETS-LP-01…13) y montaje
│       ├── VOL. V METRADO Y PRESUPUESTO/               PRESUPUESTO <nombre>.xlsx (+pdf) y CRONOGRAMA (MS Project XML).xml
│       ├── VOL. VI CALCULOS JUSTIFICATIVOS/            Cap. II (docx/pdf) + ANEXOS/ (Anexo 1…9 .xlsx) + ANEXOS/PDF/
│       ├── VOL. VII PLANOS Y LAMINAS DE DETALLE/
│       │   ├── PLANOS/DXF (AutoCAD)/                   LP-01 ubicación, LP-02 planta, PP-01…PP-nn perfil, LP-03 unifilar, LP-04 cruce
│       │   ├── PLANOS/DXF compatible (R2010 simple)/
│       │   ├── PLANOS/PDF/
│       │   ├── LAMINAS DE DETALLE/ (DXF, DXF compatible, PDF)   LD-LP-01…14 armados, retenida, PAT, cimentación
│       │   ├── COORDENADAS Y PLANO GEORREFERENCIADO/   LP-00 (DXF en coordenadas UTM reales), Excel y CSV para estación total
│       │   └── GIS (Google Earth)/                     KML, KMZ, GeoJSON, CSV
│       ├── VOL. VIII ESTUDIO DE GEOLOGIA Y GEOTECNIA/
│       ├── VOL. IX ANALISIS DE FLUJO DEL SISTEMA/      informe + VOL. IX CORTOCIRCUITO.xlsx
│       ├── VOL. X REQUERIMIENTO MINIMO - EJECUTOR Y SUPERVISOR/
│       └── VOL. XI ANEXOS/                             riesgos (docx + formatos F-1…F-3 xlsx), cuadro de cotizaciones, datos pendientes
├── ZIPS/                                  un ZIP por volumen + EXPEDIENTE_…_COMPLETO.zip
└── trabajo/                               intermedios (CSV, JSON, logs de cada paso) – útil para revisar y depurar
```

## Volumen V – hojas del libro de presupuesto

RESUMEN OBRA · GG (gastos generales desagregados) · GS (supervisión) · CCL (coordinación y liquidación) · CRONOG_VALORIZ ·
SUMINISTRO LP · MONTAJE LP · TRANSPORTE LP · APU · FP (fórmula polinómica) · PLANILLA (metrado por estructura) · BP (base de precios) ·
inventario físico por estructura. Todo enlazado con fórmulas: cambiar un precio en BP actualiza el presupuesto completo.

## Archivos intermedios útiles (`trabajo/`)

| Archivo | Contenido |
|---|---|
| `trazado_rectificado.geojson` | eje final y derivaciones (abrir en Google Earth / QGIS) |
| `perfil_troncal.csv` | progresiva, cota DEM |
| `cruces.csv`, `edificaciones_cercanas.csv` | cruces detectados y casas cerca del eje |
| `planilla_estructuras.csv` | la planilla completa (coordenadas, armado, poste, cargas, retenidas, PAT, observaciones) |
| `demanda.csv` | proyección de demanda por carga y año |
| `comparacion_conductores.csv` | ΔV, pérdidas y costo de cada sección AAAC |
| `datos_clave.json` | resultados que usan los documentos + verificaciones |
| `logs/NN_*.log` | salida de cada paso (para diagnosticar errores) |
