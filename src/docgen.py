"""Generador de documentos con la presentación del expediente modelo Ayaviri–Pucará:
A4, márgenes 3,0 / 2,0 / 2,8 / 2,0 cm; Times New Roman 12 justificado; títulos Arial negrita numerados;
encabezado con el nombre del proyecto y pie con el nombre del volumen; carátulas y separadores con marco redondeado."""
import math
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from params import PROYECTO

NOMBRE = PROYECTO["nombre"]
UBIC_TXT = PROYECTO["ubicacion"].upper()
PROY = PROYECTO["proyectista"]
FECHA_CAR = PROYECTO["ciudad_fecha"]
AZUL = RGBColor(0x1F, 0x4E, 0x79)
GRIS = RGBColor(0x59, 0x59, 0x59)


def fmt(x, d=2):
    if x is None or (isinstance(x, float) and math.isnan(x)): return "–"
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", " ")


def _field(run, code):
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = code
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t"); t.text = "1"
    f3 = OxmlElement("w:fldChar"); f3.set(qn("w:fldCharType"), "end")
    for e in (f1, it, f2, t, f3): run._r.append(e)


def _border(par, side="bottom", sz=8, color="1F4E79"):
    pPr = par._p.get_or_add_pPr(); bdr = OxmlElement("w:pBdr")
    b = OxmlElement(f"w:{side}"); b.set(qn("w:val"), "single"); b.set(qn("w:sz"), str(sz)); b.set(qn("w:space"), "1"); b.set(qn("w:color"), color)
    bdr.append(b); pPr.append(bdr)


def _shade(cell, color):
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(sh)


def _font(style, name, size=None, bold=None):
    style.font.name = name
    rpr = style.element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
    if rf is None: rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"): rf.set(qn(a), name)
    if size: style.font.size = Pt(size)
    if bold is not None: style.font.bold = bold


def _margins(s, land=False):
    if land:
        s.orientation = WD_ORIENT.LANDSCAPE; s.page_width, s.page_height = Cm(29.7), Cm(21.0)
        s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(2.0), Cm(1.5), Cm(2.6), Cm(1.8)
    else:
        s.orientation = WD_ORIENT.PORTRAIT; s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(3.0), Cm(2.0), Cm(2.8), Cm(2.0)
    s.header_distance = Cm(0.8); s.footer_distance = Cm(0.8)


def _header_footer(s, volumen):
    s.header.is_linked_to_previous = False; s.footer.is_linked_to_previous = False
    hp = s.header.paragraphs[0]; hp.text = ""
    r = hp.add_run("EXPEDIENTE TÉCNICO  |  "); r.font.size = Pt(7); r.font.color.rgb = GRIS; r.font.name = "Arial"
    r = hp.add_run(NOMBRE); r.bold = True; r.font.size = Pt(7.5); r.font.name = "Arial"; r.font.color.rgb = AZUL
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT; _border(hp, "bottom", 6)
    fp = s.footer.paragraphs[0]; fp.text = ""; _border(fp, "top", 6)
    r = fp.add_run(volumen.upper()); r.bold = True; r.font.size = Pt(7.5); r.font.name = "Arial"
    r = fp.add_run("\t\tPág. "); r.font.size = Pt(7.5); r.font.name = "Arial"
    r2 = fp.add_run(); r2.font.size = Pt(7.5); _field(r2, "PAGE")
    fp.paragraph_format.tab_stops.add_tab_stop(Cm(16.0), alignment=2)


def nuevo(volumen):
    d = Document()
    st = d.styles["Normal"]; _font(st, "Times New Roman", 12)
    pf = st.paragraph_format; pf.space_before = Pt(4); pf.space_after = Pt(6); pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.line_spacing = 1.0; pf.left_indent = Cm(0.7)
    for lvl, size in ((1, 12), (2, 11), (3, 11)):
        h = d.styles[f"Heading {lvl}"]; _font(h, "Arial", size, True); h.font.color.rgb = RGBColor(0, 0, 0); h.font.italic = False
        h.paragraph_format.space_before = Pt(12 if lvl == 1 else 8); h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.left_indent = Cm(0 if lvl == 1 else 0.35 if lvl == 2 else 0.7); h.paragraph_format.keep_with_next = True
    for nm in ("List Bullet", "List Number"):
        _font(d.styles[nm], "Times New Roman", 12)
    s = d.sections[0]; _margins(s); _header_footer(s, volumen)
    d._volumen = volumen
    return d


def salto(d): d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def h(d, txt, lvl=1):
    return d.add_heading(txt.upper() if lvl == 1 else txt, level=lvl)


def p(d, txt, bold=False, italic=False, size=None, align="J", indent=None, color=None):
    par = d.add_paragraph(); r = par.add_run(txt); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    par.alignment = {"J": WD_ALIGN_PARAGRAPH.JUSTIFY, "C": WD_ALIGN_PARAGRAPH.CENTER, "L": WD_ALIGN_PARAGRAPH.LEFT, "R": WD_ALIGN_PARAGRAPH.RIGHT}[align]
    if indent is not None: par.paragraph_format.left_indent = Cm(indent)
    return par


def pr(d, partes, align="J"):
    """párrafo con partes (texto, negrita)."""
    par = d.add_paragraph()
    for t, b in partes: r = par.add_run(t); r.bold = b
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if align == "J" else WD_ALIGN_PARAGRAPH.LEFT
    return par


def bullets(d, items, style="List Bullet", size=None):
    for it in items:
        par = d.add_paragraph(style=style); par.paragraph_format.space_after = Pt(2); par.paragraph_format.left_indent = Cm(1.3)
        if isinstance(it, tuple):
            r = par.add_run(it[0]); r.bold = True
            if size: r.font.size = Pt(size)
            r = par.add_run(it[1])
            if size: r.font.size = Pt(size)
        else:
            r = par.add_run(it)
            if size: r.font.size = Pt(size)
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def datos(d, filas, ancho=(6.5, 0.5, 9.0), size=11):
    """Lista 'Descripción : valor' en tabla sin bordes (como en la memoria del modelo)."""
    t = d.add_table(rows=0, cols=3); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for a, b in filas:
        c = t.add_row().cells
        for j, x in enumerate((a, ":", b)):
            c[j].text = ""; r = c[j].paragraphs[0].add_run(str(x)); r.font.size = Pt(size); r.bold = (j == 0)
            c[j].paragraphs[0].paragraph_format.space_after = Pt(1); c[j].paragraphs[0].paragraph_format.space_before = Pt(1)
            c[j].paragraphs[0].paragraph_format.left_indent = Cm(0)
    _widths(t, ancho); d.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def _widths(t, widths):
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = t._tbl.tblGrid.findall(qn("w:gridCol"))
    for j, gc in enumerate(grid):
        if j < len(widths): gc.set(qn("w:w"), str(int(widths[j] * 567)))
    for row in t.rows:
        for j, w in enumerate(widths):
            if j < len(row.cells): row.cells[j].width = Cm(w)


def tabla(d, header, rows, widths=None, size=9, bold_last=False, titulo=None, avail=15.6, header_fill="C5DFF0"):
    if titulo:
        tp = p(d, titulo, bold=True, size=10, align="C"); tp.paragraph_format.keep_with_next = True
    t = d.add_table(rows=1, cols=len(header)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, x in enumerate(header):
        c = t.rows[0].cells[j]; c.text = ""; par = c.paragraphs[0]; r = par.add_run(str(x)); r.bold = True; r.font.size = Pt(size); r.font.name = "Arial"
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER; par.paragraph_format.left_indent = Cm(0); _shade(c, header_fill)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, x in enumerate(row):
            cells[j].text = ""; par = cells[j].paragraphs[0]; r = par.add_run("" if x is None else str(x)); r.font.size = Pt(size); r.font.name = "Arial"
            par.paragraph_format.space_after = Pt(0); par.paragraph_format.space_before = Pt(0); par.paragraph_format.left_indent = Cm(0)
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if bold_last and i == len(rows) - 1: r.bold = True
            if isinstance(x, str) and x and len(x) < 18 and (x[0].isdigit() or x[0] in "-–(+≤≥<>") and any(ch.isdigit() for ch in x):
                par.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j > 0 else WD_ALIGN_PARAGRAPH.CENTER
            elif j > 0 and isinstance(x, str) and len(x) <= 14:
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if not widths:
        lens = [max([len(str(header[j]))] + [min(48, len(str(r[j]))) for r in rows if j < len(r)]) for j in range(len(header))]
        tot = sum(max(4, x) for x in lens); widths = [max(1.0, avail * max(4, x) / tot) for x in lens]
    _widths(t, widths)
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def imagen(d, path, ancho_cm=15, pie=None):
    d.add_picture(str(path), width=Cm(ancho_cm)); d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if pie: p(d, pie, italic=True, size=9, align="C")


def formula(d, txt, nota=None):
    par = d.add_paragraph(); r = par.add_run(txt); r.italic = True; r.font.name = "Cambria Math"; r.font.size = Pt(12)
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if nota: p(d, nota, size=10, align="L")


def apaisado(d):
    s = d.add_section(WD_SECTION.NEW_PAGE); _margins(s, True); _header_footer(s, d._volumen); return s


def vertical(d):
    s = d.add_section(WD_SECTION.NEW_PAGE); _margins(s); _header_footer(s, d._volumen); return s


def caratula_volumen(d, volumen, titulo, contenido=None):
    """Portada del volumen (como el modelo: proyecto, volumen, título, proyectista y fecha, dentro de marco)."""
    t = d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.style = "Table Grid"
    c = t.cell(0, 0); c.text = ""
    def add(txt, size, bold=True, color=None, sp=6):
        par = c.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER; par.paragraph_format.left_indent = Cm(0)
        par.paragraph_format.space_after = Pt(sp); r = par.add_run(txt); r.bold = bold; r.font.size = Pt(size); r.font.name = "Arial"
        if color: r.font.color.rgb = color
    add("", 10, sp=40)
    add("EXPEDIENTE TÉCNICO DEL PROYECTO", 16, color=AZUL, sp=16)
    add(f"“{NOMBRE}”", 15, color=AZUL, sp=10)
    add(UBIC_TXT, 10, bold=False, sp=60)
    add(volumen, 22, sp=8)
    add(titulo, 18, color=AZUL, sp=20)
    if contenido:
        for x in contenido: add(x, 11, bold=False, sp=3)
    add("", 10, sp=90)
    add("PROYECTISTA", 10, bold=False, sp=2)
    add(PROY.upper(), 13, sp=40)
    add(FECHA_CAR, 13, sp=40)
    _widths(t, [16.0])
    salto(d)


def nota(d, txt, color="FFF2CC"):
    t = d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.style = "Table Grid"
    c = t.cell(0, 0); c.text = ""; par = c.paragraphs[0]; par.paragraph_format.left_indent = Cm(0)
    r = par.add_run(txt); r.font.size = Pt(9.5); r.font.name = "Arial"; _shade(c, color); _widths(t, [15.6])
    d.add_paragraph().paragraph_format.space_after = Pt(0)


def proyectista(d):
    d.add_paragraph()
    p(d, "Proyectista:", bold=True, align="R", size=11)
    p(d, PROY, align="R", size=11)
