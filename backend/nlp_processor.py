import re
import os
import zipfile
from dataclasses import dataclass, field
from typing import List, Dict
from pypdf import PdfReader
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


@dataclass
class AuthorInfo:
    name: str = ""
    role: str = ""
    department: str = ""
    institution: str = ""
    university: str = ""
    address: str = ""
    pincode: str = ""
    email: str = ""
    location: str = ""
    # Springer/Metadata support
    aff_ids: List[int] = field(default_factory=list)
    is_corresponding: bool = False
    equal_contrib: bool = False


@dataclass
class SectionData:
    heading: str = ""
    body: str = ""
    figures: List[dict] = field(default_factory=list) # [{'path': ..., 'caption': ...}]
    tables: List[dict] = field(default_factory=list)  # [{'data': ..., 'caption': ...}]
    equations: List[dict] = field(default_factory=list) # [{'text': ..., 'num': ...}]


@dataclass
class DocumentData:
    title: str = ""
    authors: List[AuthorInfo] = field(default_factory=list)
    affiliations: Dict[int, str] = field(default_factory=dict) # {1: "Dept, Org..."}
    keywords: List[str] = field(default_factory=list)
    sections: List[SectionData] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


class NLPProcessor:
    # Regex for standard IEEE Roman numeral section headings
    SECTION_PATTERN = re.compile(
        r'^\s*((?:I{1,3}V?|VI{0,3}|VII|VIII|IX|X|\d+)\.\s+[A-Z][A-Z\s,]+|REFERENCES|BIBLIOGRAPHY)', 
        re.MULTILINE | re.IGNORECASE
    )

    # Matches reference entries like [1] Author, Title...
    REFERENCE_ENTRY_PATTERN = re.compile(
        r'(\[\d+\])',
        re.MULTILINE
    )

    EMAIL_PATTERN = re.compile(
        r'[\w.\-+]+@[\w.\-]+\.[a-zA-Z]{2,}'
    )

    def __init__(self):
        self.last_parsed_affiliations = {}
        self.image_map = {}

    def extract_text_from_file(self, file_path: str) -> str:
        """Extracts raw text from PDF, DOCX, TXT, or MD."""
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf':
                reader = PdfReader(file_path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            elif ext == '.docx':
                doc = Document(file_path)
                content = []
                # Map rId to target media filename
                rels = doc.part.rels
                
                for element in doc.element.body:
                    if element.tag.endswith('p'):
                        p = Paragraph(element, doc)
                        text = p.text.strip()
                        
                        # Preserve Bullet Points/Numbering
                        is_bullet = 'w:numPr' in element.xml
                        if is_bullet:
                            text = f"[BULLET] {text}"
                        
                        # Find all rId references in this paragraph's XML
                        rids = re.findall(r'r:embed="([^"]+)"|r:id="([^"]+)"', element.xml)
                        for rid_pair in rids:
                            rid = rid_pair[0] or rid_pair[1]
                            if rid in rels:
                                target = rels[rid].target_ref
                                if 'media/' in target:
                                    img_name = os.path.basename(target)
                                    content.append(f"![Figure](IMG:{img_name})")
                        
                        if text:
                            content.append(text)
                        
                    elif element.tag.endswith('tbl'):
                        table = Table(element, doc)
                        content.append("\n[TABLE_START]")
                        for row in table.rows:
                            row_text = [cell.text.strip() for cell in row.cells]
                            content.append(" | ".join(row_text))
                        content.append("[TABLE_END]\n")
                return "\n".join(content)
            elif ext in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            print(f"[NLPProcessor] Error extracting text: {e}")
            return ""

    def extract_images_from_file(self, file_path: str, output_dir: str) -> List[str]:
        """Extracts embedded images from PDF or DOCX."""
        images = []
        ext = os.path.splitext(file_path)[1].lower()
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        try:
            if ext == '.docx':
                with zipfile.ZipFile(file_path, 'r') as z:
                    for f in z.namelist():
                        if f.startswith('word/media/'):
                            img_name = os.path.basename(f)
                            if not img_name:
                                continue
                            out_path = os.path.join(output_dir, f"{base_name}_{img_name}")
                            with open(out_path, 'wb') as img_out:
                                img_out.write(z.read(f))
                            images.append(out_path)
            elif ext == '.pdf':
                reader = PdfReader(file_path)
                for pg_num, page in enumerate(reader.pages):
                    for count, img_obj in enumerate(page.images):
                        out_path = os.path.join(output_dir, f"{base_name}_p{pg_num}_{count}_{img_obj.name}")
                        with open(out_path, 'wb') as fp:
                            fp.write(img_obj.data)
                        images.append(out_path)
        except Exception as e:
            print(f"[NLPProcessor] Image extraction warning: {e}")

        return images

    def process_text(self, text: str, images: List[str] = None) -> DocumentData:
        """
        Main entry point. Parses raw text into a structured DocumentData object.
        """
        text = self._normalize_text(text)
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # Pre-clean any docx placeholders that leak into multiple lines
        text = re.sub(r'(?i)line\s*\d+\s*:\s*(?:\d*(?:st|nd|rd|th)\s*)?', '', text)

        doc = DocumentData()
        # Build lookup dict for images: {filename: full_path}
        self.image_map = {}
        if images:
            for path in images:
                fname = os.path.basename(path)
                self.image_map[fname] = path
                # Also map the short name (e.g. image1.png)
                # Files are usually named "{base_name}_{img_name}"
                if '_' in fname:
                    # Match the last part after underscores
                    # e.g. "My_Paper_image1.png" -> split from right
                    parts = fname.rsplit('_', 1)
                    if len(parts) > 1:
                        self.image_map[parts[1]] = path

        if self._is_markdown(text):
            self._parse_markdown(text, doc)
        else:
            self._parse_plain_ieee(text, doc)

        # Springer/Affiliation mapping
        if self.last_parsed_affiliations:
            doc.affiliations = self.last_parsed_affiliations

        if not doc.sections:
            doc.sections.append(SectionData(heading="Content", body=text.strip()))

        return doc

    # ─────────────────────────────────────────────────────────────────────────
    # MARKDOWN PARSER
    # ─────────────────────────────────────────────────────────────────────────

    def _is_markdown(self, text: str) -> bool:
        return bool(re.search(r'^#+\s+', text, re.MULTILINE))

    def _parse_markdown(self, text: str, doc: DocumentData):
        """Parse markdown-formatted research paper text."""
        lines = text.split('\n')
        i = 0

        # Title: first # heading
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('# ') and not line.startswith('## '):
                doc.title = line.lstrip('#').strip()
                i += 1
                break
            i += 1

        # Author block: lines after title with **Author:** / **Affiliation:** / **Email:**
        author = AuthorInfo()
        has_author_meta = False
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('## ') or line.startswith('---'):
                break
            au = re.match(r'\*\*Author[s]?\*\*:?\s*(.*)', line, re.IGNORECASE)
            af = re.match(r'\*\*Affiliation[s]?\*\*:?\s*(.*)', line, re.IGNORECASE)
            em = self.EMAIL_PATTERN.search(line)
            if au:
                author.name = au.group(1).strip()
                has_author_meta = True
            elif af:
                author.institution = af.group(1).strip()
                has_author_meta = True
            elif em:
                author.email = em.group(0)
                has_author_meta = True
            i += 1

        if has_author_meta:
            doc.authors.append(author)

        # Now parse ## headings as sections
        current_heading = ""
        current_body_lines = []
        current_figures = []
        current_tables = []
        current_equations = []

        def flush_section():
            nonlocal current_heading, current_body_lines, current_figures, current_tables, current_equations
            body = "\n".join(current_body_lines).strip()
            if not body and not current_heading:
                return
            heading_upper = current_heading.upper()

            if 'ABSTRACT' in heading_upper:
                new_sec = SectionData(heading="Abstract")
                self._extract_media(body, new_sec)
                # Detect inline Keywords within Abstract body
                if '**KEYWORDS:**' in new_sec.body.upper() or 'KEYWORDS:' in new_sec.body.upper():
                    kw_match = re.search(r'(?i)\*\*Keywords:\*\*\s*(.*)|(?i)Keywords:\s*(.*)', new_sec.body)
                    if kw_match:
                        kw_text = (kw_match.group(1) or kw_match.group(2)).strip()
                        doc.keywords = [k.strip().rstrip('.') for k in re.split(r'[,;]', kw_text) if k.strip()]
                        new_sec.body = new_sec.body[:kw_match.start()].strip()
                doc.sections.insert(0, new_sec)
            elif 'KEYWORD' in heading_upper:
                kw_text = body.replace('**', '').strip()
                doc.keywords = [k.strip().rstrip('.') for k in re.split(r'[,;]', kw_text) if k.strip()]
            # Stricter check for References section to avoid matching "LITERATURE REFERENCE" etc.
            elif re.search(r'\b(REFERENCES|BIBLIOGRAPHY)\b', heading_upper):
                doc.references = self._parse_references(body)
            else:
                if current_heading:
                    doc.sections.append(SectionData(
                        heading=current_heading, 
                        body=body,
                        figures=list(current_figures),
                        tables=list(current_tables),
                        equations=list(current_equations)
                    ))
            
            current_heading = ""
            current_body_lines = []
            current_figures = []
            current_tables = []
            current_equations = []

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith('## '):
                flush_section()
                raw_heading = stripped.lstrip('#').strip()
                current_heading = self._normalize_section_heading(raw_heading)
            elif stripped.startswith('### '):
                # Subsection — append as part of current body with its heading preserved
                current_body_lines.append('\n' + stripped.lstrip('#').strip())
            else:
                # Detect Figures (Markdown Image or DOCX Placeholder syntax)
                fig_match = re.search(r'!\[(.*?)\]\((.*?)\)', stripped)
                if fig_match:
                    caption = fig_match.group(1)
                    path = fig_match.group(2)
                    
                    # Resolve DOCX placeholder
                    if path.startswith('DOCX_IMG_'):
                        try:
                            idx = int(path.replace('DOCX_IMG_', '')) - 1
                            if idx < len(self.extracted_images):
                                path = self.extracted_images[idx]
                        except: pass
                    
                    current_figures.append({'caption': caption, 'path': path})
                    i += 1
                    continue

                # Detect [TABLE_START] blocks from DOCX
                if '[TABLE_START]' in stripped:
                    i += 1
                    table_rows = []
                    while i < len(lines) and '[TABLE_END]' not in lines[i]:
                        row_cells = [c.strip() for c in lines[i].split('|')]
                        if any(row_cells):
                            table_rows.append(row_cells)
                        i += 1
                    current_tables.append({'caption': 'Table', 'data': table_rows})
                    i += 1
                    continue

                # Detect Equations ($$ math $$ block)
                if stripped.startswith('$$'):
                    eq_content = stripped.strip('$').strip()
                    if not (stripped.endswith('$$') and len(stripped) > 4):
                        # Multi-line math block
                        eq_lines = [eq_content]
                        i += 1
                        while i < len(lines) and not lines[i].strip().endswith('$$'):
                            eq_lines.append(lines[i].strip())
                            i += 1
                        if i < len(lines):
                            eq_lines.append(lines[i].strip().rstrip('$').strip())
                        eq_content = " ".join(eq_lines)
                    
                    current_equations.append({
                        'text': eq_content,
                        'num': len(current_equations) + 1
                    })
                    i += 1
                    continue

                # Strip inline markdown for clean body text
                clean = re.sub(r'\*\*(.+?)\*\*', r'\1', stripped)
                clean = re.sub(r'\*(.+?)\*', r'\1', clean)
                clean = re.sub(r'`(.+?)`', r'\1', clean)
                
                # Filter out horizontal rules
                if re.match(r'^-{3,}$', clean) or re.match(r'^\*{3,}$', clean):
                    i += 1
                    continue
                
                if clean:
                    current_body_lines.append(clean)
            i += 1

        flush_section()

    # ─────────────────────────────────────────────────────────────────────────
    # PLAIN IEEE TEXT PARSER
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_plain_ieee(self, text: str, doc: DocumentData):
        """
        Parse plain-text IEEE-structured documents (e.g., extracted from PDF).
        Strategy: find block boundaries by pattern matching.
        """
        lines = text.split('\n')

        # ── Title: lines before any known section marker, typically first few non-empty lines ──
        title_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Stop at Abstract or first Roman heading
            if re.match(r'(?i)^(abstract|keywords?|index\s+terms)', line) or self.SECTION_PATTERN.match(line):
                break
            
            # IEEE/Springer authors/affiliations stop title if found
            if any(kw in line.lower() for kw in ['department', 'dept.', 'university', 'college', 'institute', 'india', 'chennai', 'email', 'e-mail']):
                break
            
            # Stop if line looks like Springer authors (Numbers/symbols after names)
            if re.search(r'[A-Z][a-z]+.*?\d+[*†]?', line):
                break

            if line:
                title_lines.append(line)
            i += 1

        doc.title = ' '.join(title_lines[:5]).strip()  # Allow up to 5 lines for long titles

        # ── Author block: lines between title end and Abstract ──
        author_block_text = []
        j = i
        while j < len(lines):
            line = lines[j].strip()
            if re.match(r'(?i)^abstract', line):
                break
            author_block_text.append(line)
            j += 1
        doc.authors = self._extract_authors_from_block('\n'.join(author_block_text))
        i = j

        # ── Abstract ──
        abstract_lines = []
        if i < len(lines) and re.match(r'(?i)^abstract', lines[i].strip()):
            i += 1  # skip 'Abstract' heading line
            while i < len(lines):
                line = lines[i].strip()
                if re.match(r'(?i)^(keywords?|index\s+terms)', line) or self.SECTION_PATTERN.match(line):
                    break
                abstract_lines.append(line)
                i += 1
        
        abstract_raw = ' '.join(l for l in abstract_lines if l).strip()
        if abstract_raw:
            new_sec = SectionData(heading="Abstract")
            self._extract_media(abstract_raw, new_sec)
            doc.sections.insert(0, new_sec)

        # ── Keywords ──
        if i < len(lines) and re.match(r'(?i)^(keywords?|index\s+terms)', lines[i].strip()):
            kw_line = lines[i].strip()
            # Remove leading "Keywords:" label
            kw_content = re.sub(r'(?i)^(keywords?|index\s+terms)\s*[:\-—]?\s*', '', kw_line)
            i += 1
            # Collect continuation lines (until next section)
            while i < len(lines):
                l = lines[i].strip()
                if self.SECTION_PATTERN.match(l) or not l:
                    break
                kw_content += ' ' + l
                i += 1
            doc.keywords = [k.strip().rstrip('.') for k in re.split(r'[,;]', kw_content) if k.strip()]

        # ── Sections ──
        remaining_text = '\n'.join(lines[i:])
        self._extract_sections(remaining_text, doc)

    # ─────────────────────────────────────────────────────────────────────────
    # SHARED HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_sections(self, text: str, doc: DocumentData):
        """Split text by Roman numeral section headings, extract References separately."""
        # Find all section starts
        matches = list(self.SECTION_PATTERN.finditer(text))

        if not matches:
            # No IEEE headings found — dump as Content
            doc.sections.append(SectionData(heading="Content", body=text.strip()))
            return

        # ── Handle text BEFORE the first detected section ──
        prefix_text = text[:matches[0].start()].strip()
        if prefix_text:
            doc.sections.append(SectionData(heading="Content", body=prefix_text))

        for idx, match in enumerate(matches):
            heading_raw = match.group(0).strip()
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = text[start:end].strip()

            heading_upper = heading_raw.upper()

            if re.search(r'\b(REFERENCES|BIBLIOGRAPHY)\b', heading_upper):
                doc.references = self._parse_references(body)
            else:
                new_sec = SectionData(heading=heading_raw)
                self._extract_media(body, new_sec)
                
                heading_upper = heading_raw.upper()
                new_sec.heading = self._normalize_section_heading(heading_raw)
                doc.sections.append(new_sec)

    def _extract_media(self, body: str, section: SectionData):
        """Helper to extract figures, tables, and equations into placeholders within the body."""
        # Normalize characters early to avoid regex issues
        body = self._normalize_text(body)
        
        figures = []
        tables = []
        equations = []

        # 1. Figures: ![caption](path)
        def fig_repl(m):
            cap, path = m.groups()
            final_path = path
            if path.startswith('IMG:'):
                img_name = path[4:]
                final_path = self.image_map.get(img_name, path)
            figures.append({'caption': cap, 'path': final_path})
            return f"[[FIG:{len(figures)-1}]]"

        body = re.sub(r'!\[(.*?)\]\((.*?)\)', fig_repl, body)

        # 2. Tables: [TABLE_START] ... [TABLE_END]
        def tbl_repl(m):
            block = m.group(1)
            rows = [r.split(' | ') for r in block.strip().split('\n') if r.strip()]
            if rows:
                tables.append({'caption': f"Table {len(tables)+1}", 'data': rows})
                return f"[[TBL:{len(tables)-1}]]"
            return ""

        body = re.sub(r'\[TABLE_START\](.*?)\[TABLE_END\]', tbl_repl, body, flags=re.DOTALL)

        # 3. Equations: $$ ... $$
        def eq_repl(m):
            eq_text = m.group(1).strip()
            if eq_text:
                equations.append({'text': eq_text, 'num': len(equations)+1})
                return f"[[EQ:{len(equations)-1}]]"
            return ""

        body = re.sub(r'\$\$(.*?)\$\$', eq_repl, body, flags=re.DOTALL)

        section.body = body.strip()
        section.figures = figures
        section.tables = tables
        section.equations = equations

    def _normalize_section_heading(self, heading: str) -> str:
        """
        Ensure IEEE section headings have proper Roman numeral prefix if missing.
        E.g. 'INTRODUCTION' → kept as-is; 'I. Introduction' → 'I. INTRODUCTION'
        Also normalizes markdown ## II. headings.
        """
        heading = heading.strip()
        # If already has Roman numeral prefix
        m = re.match(r'^(I{1,3}V?|VI{0,3}|VII|VIII|IX|X)\.\s+(.*)', heading, re.IGNORECASE)
        if m:
            numeral = m.group(1).upper()
            title_part = m.group(2).strip().upper()
            return f"{numeral}. {title_part}"
        return heading.upper()

    def _normalize_text(self, text: str) -> str:
        """Replace specialized characters (smart quotes, special dashes) with safe ASCII equivalents."""
        if not text:
            return ""
        
        # Mapping of common specialized characters to ASCII
        # These are often the cause of "missing letters/words" in PDF renderers
        replacements = {
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...', # Ellipsis
            '\u00a0': ' ',   # Non-breaking space
            '\ufb01': 'fi',  # Ligature fi
            '\ufb02': 'fl',  # Ligature fl
            '\ufb03': 'ffi', # Ligature ffi
            '\ufb04': 'ffl', # Ligature ffl
            '\u00f9': 'u',   # u with accent (often used in 'specifically')
            '\u2192': '->',  # Right arrow
            '\u2264': '<=',  # Less than or equal
            '\u2265': '>=',  # Greater than or equal
            '\u00b1': '+/-', # Plus-minus
            '\u221e': 'infinity',
            '\u2248': '~',   # Approximately
            '\u22c5': '*',   # Dot operator
            '\u00d7': 'x',   # Multiplication sign
            '\u2022': '*',   # Bullet
            '\u2713': 'check', 
            '\u2113': 'l',   # Cursive l
            '\u03bc': 'micro', # Greek mu
            '\u2206': 'delta', # Delta
            '\u03c0': 'pi',    # Pi
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
            
        # Also handle any byte-order markers or zero-width spaces
        text = text.replace('\ufeff', '').replace('\u200b', '')
        
        # Remove other extreme non-ascii that might cause reportlab to crash
        # but keep common western accents if possible (though Times-Roman might struggle)
        # For now, let's just stick to the mapping.
        
        return text

    def _extract_authors_from_block(self, block: str) -> List[AuthorInfo]:
        """
        Attempts to parse author block text into AuthorInfo objects.
        Supports both IEEE (line-by-line) and Springer (superscript numbering) styles.
        """
        authors = []
        if not block.strip():
            return authors

        # DETECT SPRINGER STYLE (numbers/symbols following names in the first non-empty line)
        non_empty_lines = [l.strip() for l in block.split('\n') if l.strip()]
        if non_empty_lines:
            first_line = non_empty_lines[0]
            if re.search(r'[A-Z][a-z]+.*?\d+[*†]?', first_line):
                return self._extract_authors_springer(block)

        # DEFAULT IEEE STYLE
        # Clean block of multiple newlines to standardize before chunking
        
        # 1. Clean up default placeholder templates (line 1:, etc.) completely across the block
        cleaned_block = re.sub(r'(?i)line\s*\d+\s*:\s*(?:\d*(?:st|nd|rd|th)\s*)?', '', block)
        
        # 2. Extract Lines and group them into Author blocks based on Email terminating sequences
        # In Docx parsing, each single text segment usually breaks into a new paragraph, removing double-newlines.
        chunks = []
        current_chunk = []
        
        lines = [l.strip() for l in cleaned_block.split('\n') if l.strip()]
        for line in lines:
            if "given name surname" in line.lower() or "name of organization" in line.lower() or "city, country" in line.lower() or "email address or orcid" in line.lower():
                continue # Skip dummy data completely
            
            current_chunk.append(line)
            
            # Predict end of an Author's block based on common terminal fields
            if self.EMAIL_PATTERN.search(line) or "email address" in line.lower() or "orcid" in line.lower() or "country" in line.lower():
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                
        # Append leftovers if any
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        for chunk in chunks:
            lines = [l.strip() for l in chunk.split('\n') if l.strip()]
            if not lines:
                continue

            a = AuthorInfo()
            
            # Assume first line is name if it's not a known label
            labels = ['address:', 'pin code:', 'pincode:', 'mail id:', 'email:', 'dept', 'department', 
                      'university', 'college', 'professor', 'scholar', 'institution', 'institute', 'organization']
            
            if lines:
                first_line = lines[0]
                # If first line contains generic placeholder text, ignore it
                if "given name surname" in first_line.lower():
                    lines = lines[1:]
                    if lines:
                        a.name = lines[0]
                        lines = lines[1:]
                elif not any(kw in first_line.lower() for kw in labels):
                    a.name = first_line
                    lines = lines[1:]

            for line in lines:
                lower_line = line.lower()
                
                # Email ID
                if self.EMAIL_PATTERN.search(line) or 'mail id:' in lower_line or 'email:' in lower_line:
                    email_match = self.EMAIL_PATTERN.search(line)
                    if email_match:
                        a.email = email_match.group(0)
                    elif ':' in line:
                        a.email = line.split(':', 1)[1].strip()
                
                # Author Role
                elif any(kw in lower_line for kw in ['professor', 'scholar', 'dean', 'lecturer', 'student', 'fellow', 'associate']):
                    a.role = line
                
                # Department
                elif any(kw in lower_line for kw in ['department', 'dept.']):
                    a.department = line
                
                # University
                elif any(kw in lower_line for kw in ['university', 'simats', 'univ.']):
                    a.university = line
                
                # Institution
                elif any(kw in lower_line for kw in ['college', 'institute', 'institution', 'technology', 'saveetha']):
                    if not a.university or 'university' not in lower_line:
                        a.institution = line
                
                # Address
                elif 'address:' in lower_line:
                    a.address = line.split(':', 1)[1].strip()
                elif not a.address and any(kw in lower_line for kw in ['saveetha nagar', 'thandalam', 'chennai']):
                    a.address = line
                
                # Pin Code
                elif any(kw in lower_line for kw in ['pin code:', 'pincode:']):
                    a.pincode = re.sub(r'(?i)pincode:|pin code:', '', line).strip()
                
                # Catch-all for other details
                elif not a.name:
                    a.name = line
                elif not a.address and any(kw in lower_line for kw in ['india', 'usa', 'uk']):
                    a.address = line

            if a.name or a.email or a.institution:
                authors.append(a)

        return authors

    def _extract_authors_springer(self, block: str) -> List[AuthorInfo]:
        """Specific parser for Springer 'Author1,2* and Author2,3†' followed by numbered affiliations."""
        authors = []
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        if not lines: return authors

        # 1. Distinguish between Author line(s) and Affiliation lines
        # Usually authors are in the first 1-2 lines.
        author_metadata_lines = []
        aff_lines = []
        email_lines = []
        
        for line in lines:
            lower_line = line.lower()
            if re.match(r'^\d+\s+', line):
                aff_lines.append(line)
            elif 'email(s):' in lower_line or 'e-mail(s):' in lower_line or 'contributing authors' in lower_line:
                email_lines.append(line)
            elif 'contributed equally' in lower_line:
                pass
            else:
                # Potential author name line
                if re.search(r'[A-Z][a-z]+', line):
                    author_metadata_lines.append(line)

        # Process Author Names
        for aline in author_metadata_lines:
            # Better split for Springer: comma followed by space, or " and "
            raw_authors = re.split(r',\s+| and ', aline)
            for ra in raw_authors:
                ra = ra.strip()
                if not ra: continue
                
                a = AuthorInfo()
                # Extract name and superscripts - match any name-like part followed by digits/symbols
                # Correcting regex: (name part) (trailing metadata)
                match = re.search(r'^(.*?)([\d, *†]+)$', ra)
                if match:
                    a.name = match.group(1).strip()
                    meta = match.group(2)
                    a.aff_ids = [int(n) for n in re.findall(r'\d+', meta)]
                    a.is_corresponding = '*' in meta
                    a.equal_contrib = '†' in meta
                else:
                    a.name = ra
                
                if a.name and len(a.name) > 1:
                    authors.append(a)

        # 2. Parse Affiliations
        aff_dict = {}
        for line in aff_lines:
            aff_match = re.match(r'^(\d+)\s+(.*)', line)
            if aff_match:
                idx = int(aff_match.group(1))
                aff_dict[idx] = aff_match.group(2).strip()

        # 3. Parse Emails
        for line in email_lines:
            lower_line = line.lower()
            email_part = line.split(':', 1)[1] if ':' in line else line
            found_emails = self.EMAIL_PATTERN.findall(email_part)
            
            if 'corresponding author(s)' in lower_line or 'e-mail(s):' in lower_line:
                corr_authors = [au for au in authors if au.is_corresponding]
                if not corr_authors and authors:
                    # Fallback if no * was used, assign to first author
                    corr_authors = [authors[0]]
                
                for i, email in enumerate(found_emails):
                    if i < len(corr_authors):
                        corr_authors[i].email = email
            elif 'contributing authors' in lower_line:
                other_authors = [au for au in authors if not au.is_corresponding]
                for i, email in enumerate(found_emails):
                    if i < len(other_authors):
                        other_authors[i].email = email

        self.last_parsed_affiliations = aff_dict
        return authors

    def _parse_references(self, text: str) -> List[str]:
        """
        Split reference text into individual reference strings.
        Handles [1], [2] style numbering.
        """
        refs = []
        # Split by reference markers
        parts = self.REFERENCE_ENTRY_PATTERN.split(text)

        i = 1  # Skip the first empty part before first [n]
        while i < len(parts) - 1:
            marker = parts[i]        # e.g. "[1]"
            content = parts[i + 1].strip()  # text after the marker
            refs.append(f"{marker} {content}")
            i += 2

        # Fallback: if no markers found, split by newline
        if not refs:
            refs = [l.strip() for l in text.split('\n') if l.strip()]

        return refs
