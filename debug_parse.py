import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from nlp_processor import NLPProcessor

processor = NLPProcessor()
file_path = "research_paper.md"

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    doc_data = processor.process_text(text)
    
    print(f"Title: {doc_data.title}")
    print(f"Authors: {len(doc_data.authors)}")
    print(f"Abstract: {len(doc_data.abstract)} chars")
    print(f"Keywords: {doc_data.keywords}")
    print(f"Sections: {len(doc_data.sections)}")
    for sec in doc_data.sections:
        print(f"  - {sec.heading} ({len(sec.body)} chars)")
        if sec.equations:
            print(f"    Eqs: {len(sec.equations)}")
        if sec.figures:
            print(f"    Figs: {len(sec.figures)}")
else:
    print(f"File not found: {file_path}")
