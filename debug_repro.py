import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from nlp_processor import NLPProcessor
from formatter import PDFGenerator, WordGenerator

def test_reproduction():
    p = NLPProcessor()
    text = "I. INTRODUCTION\nThis is a test paragraph.\nIt has multiple sentences.\n\nII. NEXT SECTION\nAnother paragraph here."
    doc_data = p.process_text(text)
    
    print(f"Title: {repr(doc_data.title)}")
    for i, sec in enumerate(doc_data.sections):
        print(f"Section {i} Heading: {repr(sec.heading)}")
        print(f"Section {i} Body: {repr(sec.body)}")
        
    # Test normalization specifically
    test_str = " specifically"
    normalized = p._normalize_text(test_str)
    print(f"Normalization test: {repr(test_str)} -> {repr(normalized)}")

if __name__ == "__main__":
    test_reproduction()
