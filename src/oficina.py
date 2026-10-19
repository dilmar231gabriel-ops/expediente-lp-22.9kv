"""Puente con LibreOffice (gratuito) para: recalcular libros Excel y convertir Word/Excel a PDF.
Funciona en Windows, macOS y Linux. Si LibreOffice no está en el PATH, defina la variable de entorno
SOFFICE con la ruta completa del ejecutable (p. ej. C:\\Program Files\\LibreOffice\\program\\soffice.exe)."""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path

CANDIDATOS = [r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
              "/Applications/LibreOffice.app/Contents/MacOS/soffice", "/usr/bin/soffice", "/usr/local/bin/soffice", "/opt/libreoffice/program/soffice"]


def soffice():
    exe = os.environ.get("SOFFICE") or shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        exe = next((c for c in CANDIDATOS if Path(c).exists()), None)
    if not exe:
        sys.exit("ERROR: no se encontró LibreOffice. Instálelo (https://www.libreoffice.org) o defina la variable SOFFICE.")
    return exe


def _run(args, timeout=1800):
    with tempfile.TemporaryDirectory(prefix="lo_perfil_") as prof:
        env = os.environ.copy(); env.setdefault("SAL_USE_VCLPLUGIN", "svp")
        cmd = [soffice(), f"-env:UserInstallation={Path(prof).as_uri()}", "--headless", "--norestore"] + [str(a) for a in args]
        return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, env=env)


def a_pdf(archivos, carpeta_salida):
    """Convierte .docx/.xlsx a PDF en la carpeta indicada."""
    archivos = [Path(a) for a in archivos]
    if archivos:
        _run(["--convert-to", "pdf", "--outdir", carpeta_salida] + archivos)


def recalcular(xlsx):
    """Abre el libro en LibreOffice, calcula todas las fórmulas y lo guarda (los valores quedan en caché
    para que Python y cualquier visor los lean). Devuelve el número de celdas con error (#VALUE!, #REF!, …)."""
    xlsx = Path(xlsx)
    with tempfile.TemporaryDirectory(prefix="lo_recalc_") as tmp:
        _run(["--convert-to", "xlsx:Calc MS Excel 2007 XML", "--outdir", tmp, xlsx])
        out = Path(tmp) / xlsx.name
        if not out.exists():
            raise RuntimeError(f"LibreOffice no pudo recalcular {xlsx.name}")
        # se conservan formatos y fórmulas del original: solo se copian los valores calculados
        import openpyxl
        calc = openpyxl.load_workbook(out, data_only=True)
        orig = openpyxl.load_workbook(xlsx)
        errores = 0
        for ws in orig.worksheets:
            wc = calc[ws.title]
            for row in ws.iter_rows():
                for c in row:
                    v = wc.cell(c.row, c.column).value
                    if isinstance(v, str) and v.startswith("#") and v.rstrip("!?0/").upper() in ("#VALUE", "#REF", "#NAME", "#DIV", "#N/A", "#NUM", "#NULL"):
                        errores += 1
        shutil.copy2(out, xlsx)      # el archivo recalculado (fórmulas + valores) reemplaza al original
    return errores


def errores_excel(xlsx):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, data_only=True); n = 0; donde = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value[:1] == "#" and any(c.value.startswith(e) for e in ("#VALUE", "#REF", "#NAME", "#DIV", "#N/A", "#NUM", "#NULL")):
                    n += 1; donde.append(f"{ws.title}!{c.coordinate}")
    return n, donde[:10]
