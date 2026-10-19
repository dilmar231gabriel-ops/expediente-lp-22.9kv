# Cómo subir este repositorio a GitHub

## Opción 1 – Desde la web (sin instalar nada)

1. Entre a <https://github.com> → **New repository** → nombre, por ejemplo `expediente-lp-22.9kv` → *Private* o *Public* → **Create repository**
   (no marque "Add a README", el repositorio ya lo trae).
2. En la página del repositorio vacío: **uploading an existing file**.
3. Descomprima el ZIP en su computadora y **arrastre el contenido de la carpeta** `expediente-lp-plantilla` (no la carpeta misma) a la página.
   La web acepta hasta 100 archivos por vez: si se queja, suba primero las carpetas `src`, `docs`, `herramientas`, `plantilla` y los archivos
   sueltos, y después `proyectos`.
   La carpeta oculta `.github` (y el archivo `.gitignore`) a veces no se arrastran desde el explorador: puede crearlos con *Add file → Create new file*
   escribiendo el nombre `.github/workflows/generar-expediente.yml` y pegando el contenido.
4. **Commit changes**.

## Opción 2 – Con Git (recomendado)

```bash
cd expediente-lp-plantilla
git init
git add .
git commit -m "Plantilla de expediente técnico LP 22,9 kV"
git branch -M main
git remote add origin https://github.com/<su-usuario>/expediente-lp-22.9kv.git
git push -u origin main
```
(Instale Git desde <https://git-scm.com>; la primera vez configure `git config --global user.name "…"` y `user.email`.)

## Trabajar después

- Un proyecto nuevo = una carpeta nueva en `proyectos/` → `git add proyectos/mi-proyecto` → `git commit -m "Proyecto X"` → `git push`.
- La carpeta `salida/` no se sube (está en `.gitignore`): el expediente se regenera con `generar.py`. Si quiere guardar un expediente
  entregado, súbalo como *Release* (pestaña *Releases* → adjuntar el ZIP completo).
- **GitHub Actions** (opcional): con el archivo `.github/workflows/generar-expediente.yml`, en la pestaña *Actions* → *Generar expediente* →
  *Run workflow* puede indicar la ruta de un `proyecto.yaml` y GitHub genera el expediente en la nube; el ZIP queda en *Artifacts*.

## Antes de hacerlo público

- Revise que `proyecto.yaml` no contenga datos que la Entidad considere reservados.
- Los DEM y capas OSM son datos abiertos (Copernicus, OpenStreetMap – licencia ODbL, cite la fuente).
- Elija una licencia (pestaña *Add file → Create new file → LICENSE* → *Choose a license template*) si quiere que otros lo reutilicen.
