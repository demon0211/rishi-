import sys
sys.path.append(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\backend")
from nlp_processor import NLPProcessor
import json

nlp = NLPProcessor()
raw_text = nlp.extract_text_from_file(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\backend\uploads\CKD_ML_Prediction_Enhanced_Paper_111.docx")
doc_data = nlp.process_text(raw_text)

print(f"Number of authors found: {len(doc_data.authors)}")
for i, a in enumerate(doc_data.authors):
    print(f"Author {i+1}:")
    print(f"  Name: {a.name}")
    print(f"  Role: {a.role}")
    print(f"  Dept: {a.department}")
    print(f"  Inst: {a.institution}")
    print(f"  Univ: {a.university}")
    print(f"  Addr: {a.address}")
    print(f"  Pin : {a.pincode}")
    print(f"  Mail: {a.email}")
    print("-" * 20)
