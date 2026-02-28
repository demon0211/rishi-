import sys
import os
sys.path.append(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\backend")
from nlp_processor import NLPProcessor
from formatter import PDFGenerator, WordGenerator

nlp_processor = NLPProcessor()
raw_text = nlp_processor.extract_text_from_file(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\research_paper.md")
doc_data = nlp_processor.process_text(raw_text)

# Ensures at least 3 authors for a nice grid
if len(doc_data.authors) > 0:
    doc_data.authors[0].role = "Research scholar"
    doc_data.authors[0].department = "Dept. of computer science"
    doc_data.authors[0].institution = "Saveetha College of Liberal Arts and Sciences, SIMATS Deemed to be University"
    doc_data.authors[0].address = "Saveetha Nagar, Thandalam, Chennai"
    doc_data.authors[0].pincode = "602105"
    doc_data.authors[0].email = "sowmiyabharanir@gmail.com"

while len(doc_data.authors) < 3:
    import copy
    doc_data.authors.append(copy.deepcopy(doc_data.authors[0]))
    
print("Found authors:", len(doc_data.authors))

pdf_gen = PDFGenerator(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\backend\outputs")
pdf_gen.generate_pdf(doc_data, "test_output.pdf")

word_gen = WordGenerator(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\backend\outputs")
word_gen.generate_docx(doc_data, "test_output.docx")
print("Done")
