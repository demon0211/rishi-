import sys
import os
import re

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from nlp_processor import NLPProcessor
from formatter import PDFGenerator, WordGenerator

def test_final():
    p = NLPProcessor()
    text = """TITLE OF THE PAPER
Author One, Author Two

Abstract—This is a test abstract. It should be preserved.

I. INTRODUCTION
This is the first paragraph. It starts with 'T'.
Next line of the same paragraph.

II. BACKGROUND
Another paragraph here.
![fig](IMG:fig1.png)
Inline image followed by text.
"""
    doc_data = p.process_text(text)
    
    with open('debug_output.log', 'w', encoding='utf-8') as f:
        f.write(f"Title: {repr(doc_data.title)}\n")
        f.write(f"Abstract: {repr(doc_data.abstract)}\n")
        for i, sec in enumerate(doc_data.sections):
            f.write(f"Section {i} Heading: {repr(sec.heading)}\n")
            f.write(f"Section {i} Body: {repr(sec.body)}\n")
            f.write(f"Section {i} Figures: {len(sec.figures)}\n")

    print("Diagnostic log written to debug_output.log")

if __name__ == "__main__":
    test_final()
