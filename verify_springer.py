import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from nlp_processor import NLPProcessor, DocumentData, AuthorInfo
from formatter import SpringerPDFGenerator, SpringerWordGenerator

def test_springer_full_spec():
    text = """
The Impact of AI on Modern Research Paper Formatting

First Author1,2*, Second Author2,3† and Third Author1,2†
1 Department of Computer Science, Saveetha School of Engineering, Chennai, 602105, Tamil Nadu, India
2 Saveetha Institute of Medical and Technical Sciences (SIMATS), Chennai, India
3 Department of Electronics, College of Engineering, Chennai, India

*Corresponding author(s). E-mail(s): first@email.com
Contributing authors: second@email.com; third@email.com

Abstract
This paper explores the automated formatting of academic research papers using AI. The focus is on the Springer template.

Keywords: Artificial Intelligence, Research Paper, Formatting, Springer, Automation

Introduction
Introduction content goes here.
"""
    
    nlp = NLPProcessor()
    doc_data = nlp.process_text(text)
    
    # Check if extraction worked
    print(f"Extracted {len(doc_data.authors)} authors")
    for a in doc_data.authors:
        print(f"Author: {a.name}, Email: {a.email}, Corr: {a.is_corresponding}, Equal: {a.equal_contrib}")

    output_dir = os.path.join(os.getcwd(), 'outputs')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Test PDF
    pdf_gen = SpringerPDFGenerator(output_dir)
    pdf_path = pdf_gen.generate_pdf(doc_data, "test_springer_full_spec.pdf")
    print(f"Springer Full Spec PDF generated: {pdf_path}")
    
    # Test Word
    word_gen = SpringerWordGenerator(output_dir)
    docx_path = word_gen.generate_docx(doc_data, "test_springer_full_spec.docx")
    print(f"Springer Full Spec DOCX generated: {docx_path}")

if __name__ == "__main__":
    test_springer_full_spec()
