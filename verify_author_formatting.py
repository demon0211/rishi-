import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from nlp_processor import NLPProcessor, DocumentData, AuthorInfo
from formatter import PDFGenerator, WordGenerator

def test_author_formatting():
    # Data transcribed from the image
    text = """
Causal-M3: Disentangling Clinical Intent from Physiological State via Missing-Not-At-Random Causal Representation Learning for Robust CKD Risk Stratification

R. Sowmiya Bharani
Research scholar
Dept. of computer science
Saveetha College of Liberal Arts and Sciences, SIMATS Deemed to be University
Address: Saveetha Nagar, Thandalam, Chennai
Pin code: 602105
Mail ID: sowmiyabharanir@gmail.com

Prof. Dr. Jayakarthik Ramachandran
Assistant Dean - Faculty
Dept. of Computer Science
Saveetha College of Liberal Arts and Sciences, SIMATS Deemed to be University
Address: Saveetha Nagar, Thandalam, Chennai
Pin code: 602105
Mail ID: jayakarthickr.sclas@saveetha.com

S. Sathyakala
Research scholar
Dept. of Computer Science
Saveetha College of Liberal Arts and Sciences, SIMATS Deemed to be University
Address: Saveetha Nagar, Thandalam, Chennai
Pin code: 602105
Mail ID: drponmurugan25@gmail.com

Dr. S. Rukmani Devi
Associate Professor
Department of Computer Science
Saveetha College of Liberal Arts and Sciences, SIMATS Deemed to be University
Address: Saveetha Nagar, Thandalam, Chennai
Pincode: 602105
Mail ID: rukmanibaveshnambi@gmail.com

M. Rajasekar
Associate Professor
Department of computer science
Saveetha college of Liberal Arts and Sciences,
Saveetha Institute of Medical and Technical Sciences, Chennai, India
Mail ID: sekarca07@gmail.com

T. Mahitha
Research Scholar
Dept. of Computer Science
Saveetha College of Liberal Arts and Sciences, SIMATS Deemed to be University
Mail ID: mahithavaradhu@gmail.com
"""
    
    nlp = NLPProcessor()
    doc_data = nlp.process_text(text)
    
    output_dir = os.path.join(os.getcwd(), 'outputs')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    pdf_gen = PDFGenerator(output_dir)
    pdf_path = pdf_gen.generate_pdf(doc_data, "test_author_formatting.pdf")
    print(f"PDF generated: {pdf_path}")
    
    word_gen = WordGenerator(output_dir)
    docx_path = word_gen.generate_docx(doc_data, "test_author_formatting.docx")
    print(f"DOCX generated: {docx_path}")

if __name__ == "__main__":
    test_author_formatting()
