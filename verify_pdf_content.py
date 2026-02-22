from pypdf import PdfReader
import sys

pdf_path = "backend/outputs/formatted_research_paper.pdf"

try:
    reader = PdfReader(pdf_path)
    print(f"Pages: {len(reader.pages)}")
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f"--- Page {i+1} ({len(text)} chars) ---")
        print(text[:200] + "...")
except Exception as e:
    print(f"Error: {e}")
