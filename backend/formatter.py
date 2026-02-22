"""
IEEE-Standard Document Formatter — Complete Redesign
Produces PDF (via ReportLab BaseDocTemplate + Frames) and DOCX (via python-docx)
outputs that match an IEEE conference paper layout.

DocumentBuilder pattern:
  build_title() → build_authors() → build_abstract() → build_keywords()
  → switch_to_two_column() → build_sections() → build_references()
"""

import os
import textwrap
import html
import re
from typing import List

# ── ReportLab ─────────────────────────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, FrameBreak, NextPageTemplate, HRFlowable,
    KeepTogether
)
from reportlab.platypus.tableofcontents import SimpleIndex
from reportlab.lib import colors

# ── python-docx ───────────────────────────────────────────────────────────
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── Internal ──────────────────────────────────────────────────────────────
from nlp_processor import DocumentData, AuthorInfo


# ═══════════════════════════════════════════════════════════════════════════
# SHARED CONSTANTS (IEEE A4 Specs)
# ═══════════════════════════════════════════════════════════════════════════

CM = 28.346 # ReportLab points per cm
COL_W = 8.25 * CM
COL_GAP = 0.8 * CM
LEFT_MARGIN = 1.9 * CM
RIGHT_MARGIN = 1.9 * CM
TOP_MARGIN = 2.54 * CM
BOTTOM_MARGIN = 2.86 * CM


# ═══════════════════════════════════════════════════════════════════════════
# PDF GENERATOR  (ReportLab BaseDocTemplate)
# ═══════════════════════════════════════════════════════════════════════════

class PDFGenerator:
    """
    Generates IEEE-formatted PDF documents using ReportLab BaseDocTemplate
    with proper single-column and dual-column PageTemplate objects.
    """

    PAGE_W, PAGE_H = A4
    LEFT   = LEFT_MARGIN
    RIGHT  = RIGHT_MARGIN
    TOP    = TOP_MARGIN
    BOTTOM = BOTTOM_MARGIN

    def __init__(self, output_folder: str):
        self.output_folder = output_folder
        self.styles = self._build_styles()

    # ─── Style Sheet ──────────────────────────────────────────────────────

    def _build_styles(self) -> dict:
        s = {}

        s['title'] = ParagraphStyle(
            'IEEE_Title',
            fontName='Times-Roman',
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        s['author_name'] = ParagraphStyle(
            'IEEE_AuthorName',
            fontName='Times-Roman',
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        s['author_detail'] = ParagraphStyle(
            'IEEE_AuthorDetail',
            fontName='Times-Italic',
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        s['author_email'] = ParagraphStyle(
            'IEEE_AuthorEmail',
            fontName='Times-Roman',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        s['abstract_heading'] = ParagraphStyle(
            'IEEE_AbstractHeading',
            fontName='Times-BoldItalic',
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY,
            spaceBefore=10,
            spaceAfter=0,
        )
        s['abstract_body'] = ParagraphStyle(
            'IEEE_AbstractBody',
            fontName='Times-BoldItalic',
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY,
            firstLineIndent=0,
        )
        s['keywords_label'] = ParagraphStyle(
            'IEEE_KeywordsLabel',
            fontName='Times-Italic',
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY,
            spaceBefore=6,
        )
        s['keywords_body'] = ParagraphStyle(
            'IEEE_KeywordsBody',
            fontName='Times-Italic',
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY,
        )
        s['section_heading'] = ParagraphStyle(
            'IEEE_SectionHeading',
            fontName='Times-Roman',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            spaceBefore=12,
            spaceAfter=6,
            textTransform='uppercase', # We'll handle Small Caps via manual font switching if needed or just Uppercase
        )
        s['subsection_heading'] = ParagraphStyle(
            'IEEE_SubsectionHeading',
            fontName='Times-Italic',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            spaceBefore=9,
            spaceAfter=3,
        )
        s['body'] = ParagraphStyle(
            'IEEE_Body',
            fontName='Times-Roman',
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY,
            firstLineIndent=0.422 * CM,
            spaceBefore=0,
            spaceAfter=0,
        )
        s['reference'] = ParagraphStyle(
            'IEEE_Reference',
            fontName='Times-Roman',
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            leftIndent=14,
            firstLineIndent=-14,
            spaceAfter=3,
        )
        s['figure_caption'] = ParagraphStyle(
            'IEEE_FigureCaption',
            fontName='Times-Roman',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            spaceBefore=6,
            spaceAfter=6,
            textTransform='uppercase', # Scopus/IEEE Small Caps for Fig. X.
        )
        s['table_caption'] = ParagraphStyle(
            'IEEE_TableCaption',
            fontName='Times-Roman',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            spaceBefore=6,
            spaceAfter=6,
            textTransform='uppercase',
        )
        s['list_item'] = ParagraphStyle(
            'IEEE_ListItem',
            fontName='Times-Roman',
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY,
            leftIndent=0.844 * CM, # 0.422 * 2
            firstLineIndent=-0.422 * CM,
            spaceBefore=0,
            spaceAfter=0,
        )
        return s

    # ─── Page Layout ──────────────────────────────────────────────────────

    def _build_doc(self, filepath: str) -> BaseDocTemplate:
        doc = BaseDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=self.LEFT,
            rightMargin=self.RIGHT,
            topMargin=self.TOP,
            bottomMargin=self.BOTTOM,
        )

        usable_w = self.PAGE_W - self.LEFT - self.RIGHT
        usable_h = self.PAGE_H - self.TOP - self.BOTTOM

        # ── Single-column template ──
        frame_1col = Frame(
            self.LEFT, self.BOTTOM,
            usable_w, usable_h,
            id='single',
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        tmpl_1col = PageTemplate(id='OneCol', frames=[frame_1col])

        # ── Two-column template ──
        # IEEE Specs: Column Width = 8.25 cm, Inter Column Space = 0.8 cm
        col_w = COL_W
        col_gap = COL_GAP
        
        frame_left = Frame(
            self.LEFT, self.BOTTOM,
            col_w, usable_h,
            id='left',
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        frame_right = Frame(
            self.LEFT + col_w + col_gap, self.BOTTOM,
            col_w, usable_h,
            id='right',
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        tmpl_2col = PageTemplate(id='TwoCol', frames=[frame_left, frame_right])

        doc.addPageTemplates([tmpl_1col, tmpl_2col])
        return doc

    # ─── Builder Methods ──────────────────────────────────────────────────

    def _build_title(self, story: list, data: DocumentData):
        if data.title:
            # IEEE Title: Capitalize Nouns, Pronouns, Verbs, Adjectives, Adverbs
            ignore_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with'}
            words = data.title.split()
            formatted_words = []
            for i, word in enumerate(words):
                clean_word = word.lower()
                if clean_word not in ignore_words or i == 0 or i == len(words) - 1:
                    formatted_words.append(word.capitalize())
                else:
                    formatted_words.append(clean_word)
            title_text = html.escape(" ".join(formatted_words))
            
            story.append(Spacer(1, 1.0 * inch - self.TOP))
            story.append(Paragraph(title_text, self.styles['title']))
            story.append(Spacer(1, 12))

    def _build_authors(self, story: list, data: DocumentData):
        if not data.authors:
            return

        from reportlab.platypus import Table, TableStyle
        author_cells = []
        for author in data.authors:
            lines = []
            if author.name:
                lines.append(Paragraph(html.escape(author.name), self.styles['author_name']))
            if author.institution or author.department or author.location:
                # Group affiliation details
                aff = []
                if author.department: aff.append(author.department)
                if author.institution: aff.append(author.institution)
                if author.location: aff.append(author.location)
                lines.append(Paragraph(html.escape(", ".join(aff)), self.styles['author_detail']))
            if author.email:
                lines.append(Paragraph(html.escape(author.email), self.styles['author_email']))
            author_cells.append(lines)

        # Arrange in grid: 2-3 columns
        num_authors = len(author_cells)
        cols_per_row = 3 if num_authors >= 3 else 2
        col_w = (self.PAGE_W - self.LEFT - self.RIGHT) / cols_per_row

        for i in range(0, len(author_cells), cols_per_row):
            row_cells = author_cells[i:i + cols_per_row]
            while len(row_cells) < cols_per_row:
                row_cells.append([Paragraph("", self.styles['author_detail'])])

            tbl = Table([[cell for cell in row_cells]], colWidths=[col_w] * cols_per_row)
            tbl.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(tbl)

        story.append(Spacer(1, 24))

    def _build_abstract(self, story: list, data: DocumentData):
        if data.abstract:
            # Single paragraph, starts with "Abstract—"
            esc_abstract = html.escape(data.abstract)
            text = f"<i><b>Abstract—</b>{esc_abstract}</i>"
            story.append(Paragraph(text, self.styles['abstract_body']))
            story.append(Spacer(1, 10))

    def _build_keywords(self, story: list, data: DocumentData):
        if data.keywords:
            # Sort alphabetically, only first keyword capitalized
            keywords = sorted([k.strip() for k in data.keywords])
            if keywords:
                keywords[0] = keywords[0].capitalize()
                for i in range(1, len(keywords)):
                    keywords[i] = keywords[i].lower()
                
                kw_text = f"<i>Index Terms—</i>{html.escape(', '.join(keywords))}"
                story.append(Paragraph(kw_text, self.styles['keywords_body']))
                story.append(Spacer(1, 12))

    def _switch_to_two_column(self, story: list):
        """Trigger 2-column layout. Uses FrameBreak to start flowing into left column."""
        story.append(NextPageTemplate('TwoCol'))
        story.append(FrameBreak())

    def _build_sections(self, story: list, data: DocumentData):
        for sec in data.sections:
            # IEEE Primary Heading: Small Caps (simulated with upper() and 10pt)
            story.append(Paragraph(html.escape(sec.heading.upper()), self.styles['section_heading']))

            if sec.body:
                paragraphs = sec.body.split('\n')
                for para_text in paragraphs:
                    stripped = para_text.strip()
                    if not stripped:
                        continue
                    # Normalize before matching
                    stripped = self.styles['body'].fontName # dummy access to style
                    # We'll use doc_data which is already normalized by NLPProcessor, 
                    # but double-check if needed. For now, focus on marker padding.

                    if re.match(r'^([A-Z]\.|[0-9]+\.[0-9]+)\s+\S', stripped):
                        story.append(Paragraph(html.escape(stripped), self.styles['subsection_heading']))
                    elif stripped.startswith('[BULLET]'):
                        # Handle Bullet: Replace marker with a bullet character
                        content = stripped[8:].strip()
                        story.append(Paragraph(f"• {html.escape(content)}", self.styles['list_item']))
                    else:
                        story.append(Paragraph(html.escape(stripped), self.styles['body']))

            # Add Figures, Tables, Equations for this section
            for fig in getattr(sec, 'figures', []):
                self._add_figure(story, fig['path'], fig['caption'])
            for tbl in getattr(sec, 'tables', []):
                self._add_table(story, tbl['data'], tbl['caption'])
            for eq in getattr(sec, 'equations', []):
                self._add_equation(story, eq['text'], eq['num'])

            story.append(Spacer(1, 6))

    def _build_references(self, story: list, data: DocumentData):
        if not data.references:
            return

        story.append(Paragraph("REFERENCES", self.styles['section_heading']))
        for i, ref in enumerate(data.references):
            # Ensure sequence [1]
            ref_text = ref.strip()
            if not ref_text.startswith('['):
                ref_text = f"[{i+1}] {ref_text}"
            story.append(Paragraph(html.escape(ref_text), self.styles['reference']))

    def _add_figure(self, story: list, img_path: str, caption: str):
        from reportlab.platypus import Image
        if not os.path.exists(img_path):
            return
        img = Image(img_path)
        # Scale to max column width
        if img.drawWidth > COL_W:
            ratio = COL_W / img.drawWidth
            img.drawWidth = COL_W
            img.drawHeight *= ratio
        story.append(img)
        story.append(Paragraph(html.escape(caption), self.styles['figure_caption']))

    def _add_table(self, story: list, table_data: list, caption: str):
        from reportlab.platypus import Table, TableStyle
        story.append(Paragraph(html.escape(caption), self.styles['table_caption']))
        # Escape table cells
        esc_data = [[html.escape(str(cell)) for cell in row] for row in table_data]
        tbl = Table(esc_data)
        tbl.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONT', (0, 1), (-1, -1), 'Times-Roman'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(tbl)

    def _add_equation(self, story: list, eq_text: str, num: int):
        from reportlab.platypus import Table, TableStyle
        # IEEE Equation: Centered equation with right-aligned number (n)
        # Use a table with 3 columns: empty, content, number
        data = [['', Paragraph(f"<i>{html.escape(eq_text)}</i>", self.styles['body']), f"({num})"]]
        tbl = Table(data, colWidths=[20, COL_W - 60, 40])
        tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ]))
        story.append(Spacer(1, 6))
        story.append(tbl)
        story.append(Spacer(1, 6))

    # ─── Main Entry Point ─────────────────────────────────────────────────

    def generate_pdf(self, data: DocumentData, filename: str) -> str:
        """
        Builds and saves an IEEE-formatted PDF. Returns the output file path.
        """
        import re
        filepath = os.path.join(self.output_folder, filename)
        doc = self._build_doc(filepath)

        story = []

        # ── Single-column block: Title, Authors, Abstract, Keywords ──
        self._build_title(story, data)
        self._build_authors(story, data)

        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=6))

        self._build_abstract(story, data)
        self._build_keywords(story, data)

        # ── Switch to 2-column ──
        self._switch_to_two_column(story)

        # ── Two-column block: Sections, References ──
        self._build_sections(story, data)
        self._build_references(story, data)

        # Explicitly remove any default page numbers (BaseDocTemplate doesn't add them by default)
        # but we can ensure it by not defining any onPage handlers.
        
        doc.build(story)
        return filepath


# ═══════════════════════════════════════════════════════════════════════════
# DOCX GENERATOR  (python-docx)
# ═══════════════════════════════════════════════════════════════════════════

class WordGenerator:
    """
    Generates IEEE-formatted DOCX documents using python-docx.
    Uses a continuous section break with XML-level w:cols="2" for two-column layout.
    """

    def __init__(self, output_folder: str):
        self.output_folder = output_folder

    # ─── Paragraph Helpers ────────────────────────────────────────────────

    def _add_paragraph(self, doc: Document, text: str,
                       bold=False, italic=False, font_size=10,
                       alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                       space_before=0, space_after=0,
                       first_line_indent=0, left_indent=0) -> None:
        p = doc.add_paragraph()
        p.alignment = alignment
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after  = Pt(space_after)
        if first_line_indent:
            p.paragraph_format.first_line_indent = Pt(first_line_indent)
        if left_indent:
            p.paragraph_format.left_indent = Pt(left_indent)

        run = p.add_run(text)
        run.bold   = bold
        run.italic = italic
        run.font.name = 'Times New Roman'
        run.font.size = Pt(font_size)
        return p

    def _add_section_heading(self, doc: Document, text: str) -> None:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after  = Pt(6)
        run = p.add_run(text.upper())
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        run.font.small_caps = True

    def _add_subsection_heading(self, doc: Document, text: str) -> None:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(9)
        p.paragraph_format.space_after  = Pt(3)
        run = p.add_run(text)
        run.italic = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)

    # ─── Column Switch ────────────────────────────────────────────────────

    def _switch_to_two_column(self, doc: Document) -> None:
        """
        Inserts a continuous section break and sets the new section to 2 columns
        via direct XML manipulation (w:cols w:num="2" w:space="720").
        """
        new_section = doc.add_section(WD_SECTION.CONTINUOUS)
        sect_pr = new_section._sectPr

        # Remove any existing w:cols elements
        for existing in sect_pr.findall(qn('w:cols')):
            sect_pr.remove(existing)

        cols = OxmlElement('w:cols')
        cols.set(qn('w:num'), '2')
        cols.set(qn('w:space'), '454')   # ~0.8cm in twentieths of a point (0.8 / 2.54 * 72 * 20 = 453.5)
        cols.set(qn('w:equalWidth'), '1')
        sect_pr.append(cols)

    # ─── Builder Methods ──────────────────────────────────────────────────

    def _build_title(self, doc: Document, data: DocumentData) -> None:
        if not data.title:
            return
            
        # IEEE Title Capitalization logic
        ignore_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with'}
        words = data.title.split()
        formatted_words = []
        for i, word in enumerate(words):
            clean_word = word.lower()
            if clean_word not in ignore_words or i == 0 or i == len(words) - 1:
                formatted_words.append(word.capitalize())
            else:
                formatted_words.append(clean_word)
        title_text = " ".join(formatted_words)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(72) # 1 inch offset from top (approx)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(title_text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(24)

    def _build_authors(self, doc: Document, data: DocumentData) -> None:
        if not data.authors:
            return

        # Use a table for the author grid (2-3 columns)
        num_authors = len(data.authors)
        cols = 3 if num_authors >= 3 else 2
        table = doc.add_table(rows=0, cols=cols)
        table.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        row_cells = None
        for i, author in enumerate(data.authors):
            if i % cols == 0:
                row_cells = table.add_row().cells
            
            cell = row_cells[i % cols]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Name
            run = p.add_run(author.name)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
            
            # Affiliation
            aff_details = []
            if author.department: aff_details.append(author.department)
            if author.institution: aff_details.append(author.institution)
            if author.location: aff_details.append(author.location)
            
            if aff_details:
                p = cell.add_paragraph(", ".join(aff_details))
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.runs[0]
                run.italic = True
                run.font.name = 'Times New Roman'
                run.font.size = Pt(12)
            
            if author.email:
                p = cell.add_paragraph(author.email)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.runs[0]
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10)

        doc.add_paragraph().paragraph_format.space_after = Pt(12)

        # Horizontal rule equivalent: a border paragraph
        doc.add_paragraph()  # small gap

    def _build_abstract(self, doc: Document, data: DocumentData) -> None:
        if not data.abstract:
            return

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after  = Pt(0)
        
        run = p.add_run("Abstract—")
        run.bold = True
        run.italic = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10)
        
        run_body = p.add_run(data.abstract)
        run_body.bold = True
        run_body.italic = True
        run_body.font.name = 'Times New Roman'
        run_body.font.size = Pt(10)

    def _build_keywords(self, doc: Document, data: DocumentData) -> None:
        if not data.keywords:
            return

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after  = Pt(12)

        # Alphabetically ordered, only first capitalized
        keywords = sorted([k.strip() for k in data.keywords])
        if keywords:
            keywords[0] = keywords[0].capitalize()
            for i in range(1, len(keywords)):
                keywords[i] = keywords[i].lower()

        run_label = p.add_run("Index Terms—")
        run_label.italic = True
        run_label.font.name = 'Times New Roman'
        run_label.font.size = Pt(10)

        run_body = p.add_run(", ".join(keywords))
        run_body.italic = True
        run_body.font.name = 'Times New Roman'
        run_body.font.size = Pt(10)

    def _build_sections(self, doc: Document, data: DocumentData) -> None:
        import re as _re
        for sec in data.sections:
            self._add_section_heading(doc, sec.heading)

            if sec.body:
                for para_text in sec.body.split('\n'):
                    stripped = para_text.strip()
                    if not stripped:
                        continue
                    if re.match(r'^([A-Z]\.|[0-9]+\.[0-9]+)\s+\S', stripped):
                        self._add_subsection_heading(doc, stripped)
                    elif stripped.startswith('[BULLET]'):
                        content = stripped[8:].strip()
                        # Use high-level add_paragraph with style if it exists, or manual indent
                        try:
                            p = doc.add_paragraph(content, style='List Bullet')
                        except:
                            # Fallback to manual bullet
                            self._add_paragraph(doc, f"• {content}", font_size=10,
                                               alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                                               left_indent=Pt(12))
                    else:
                        self._add_paragraph(doc, stripped, font_size=10,
                                            alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                                            space_after=0, first_line_indent=Pt(0.422 * 28.346))

            # Add Figures, Tables, Equations for this section
            for fig in getattr(sec, 'figures', []):
                self._add_figure(doc, fig['path'], fig['caption'])
            for tbl in getattr(sec, 'tables', []):
                self._add_table(doc, tbl['data'], tbl['caption'])
            for eq in getattr(sec, 'equations', []):
                self._add_equation(doc, eq['text'], eq['num'])

    def _build_references(self, doc: Document, data: DocumentData) -> None:
        if not data.references:
            return

        self._add_section_heading(doc, "References")

        for i, ref in enumerate(data.references):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.left_indent   = Pt(14)
            p.paragraph_format.first_line_indent = Pt(-14)
            p.paragraph_format.space_after   = Pt(2)
            
            ref_text = ref.strip()
            if not ref_text.startswith('['):
                ref_text = f"[{i+1}] {ref_text}"
            
            run = p.add_run(ref_text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(9)

    def _add_figure(self, doc: Document, img_path: str, caption: str):
        from docx.shared import Cm
        if not os.path.exists(img_path):
            return
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(img_path, width=Cm(8.25))
        
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(6)
        cap.paragraph_format.space_after = Pt(6)
        run_cap = cap.add_run(caption.upper())
        run_cap.font.name = 'Times New Roman'
        run_cap.font.size = Pt(10)
        run_cap.font.small_caps = True

    def _add_table(self, doc: Document, table_data: list, caption: str):
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_before = Pt(6)
        cap.paragraph_format.space_after = Pt(6)
        run_cap = cap.add_run(caption.upper())
        run_cap.font.name = 'Times New Roman'
        run_cap.font.size = Pt(10)
        run_cap.font.small_caps = True

        table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
        table.style = 'Table Grid'
        for i, row in enumerate(table_data):
            for j, val in enumerate(row):
                table.cell(i, j).text = str(val)

    def _add_equation(self, doc: Document, eq_text: str, num: int):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(eq_text)
        run.italic = True
        tab_run = p.add_run('\t')
        num_run = p.add_run(f"({num})")
        # Ensure right alignment for number via tab stops (would need section width)
        # For now, just adding them.

    # ─── Main Entry Point ─────────────────────────────────────────────────

    def generate_docx(self, data: DocumentData, filename: str) -> str:
        """
        Builds and saves an IEEE-formatted DOCX. Returns the output file path.
        """
        filepath = os.path.join(self.output_folder, filename)
        doc = Document()

        # ── Global default font ──
        doc.styles['Normal'].font.name = 'Times New Roman'
        doc.styles['Normal'].font.size = Pt(10)

        # ── Page margins (IEEE A4) ──
        for section in doc.sections:
            section.top_margin    = Cm(2.54)
            section.bottom_margin = Cm(2.86)
            section.left_margin   = Cm(1.9)
            section.right_margin  = Cm(1.9)
            section.header_distance = Pt(0)
            section.footer_distance = Pt(0)

        # ── Single-column block ──
        self._build_title(doc, data)
        self._build_authors(doc, data)
        self._build_abstract(doc, data)
        self._build_keywords(doc, data)

        # ── Switch to two columns ──
        self._switch_to_two_column(doc)

        # ── Two-column block ──
        self._build_sections(doc, data)
        self._build_references(doc, data)

        doc.save(filepath)
        return filepath


# ═══════════════════════════════════════════════════════════════════════════
# LEGACY SHIM  (keeps backward compatibility with app.py dict-based calls)
# ═══════════════════════════════════════════════════════════════════════════
# If old code passes a plain dict instead of DocumentData, wrap it.

def _dict_to_doc_data(sections_dict: dict) -> DocumentData:
    """Convert legacy flat dict (section_name → body) to DocumentData."""
    from nlp_processor import DocumentData, SectionData, AuthorInfo
    doc = DocumentData()
    doc.title = "Research Paper Output"
    for name, body in sections_dict.items():
        n_upper = name.upper()
        if 'ABSTRACT' in n_upper:
            doc.abstract = body
        elif 'KEYWORD' in n_upper:
            doc.keywords = [k.strip() for k in body.split(',') if k.strip()]
        elif 'REFERENCE' in n_upper:
            doc.references = [r.strip() for r in body.split('\n') if r.strip()]
        else:
            doc.sections.append(SectionData(heading=name, body=body))
    return doc


import re  # needed in _build_sections bodies at module level
