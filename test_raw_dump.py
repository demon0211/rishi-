import sys
sys.path.append(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\backend")
from nlp_processor import NLPProcessor
import json

nlp = NLPProcessor()
raw_text = nlp.extract_text_from_file(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\backend\uploads\CKD_ML_Prediction_Enhanced_Paper_111.docx")
doc_data = nlp.process_text(raw_text)

print("Title:")
print(doc_data.title)

print("\nAuthors Block Raw:")
# Need to see what block was actually extracted
lines = raw_text.split('\n')
for i, line in enumerate(lines[:30]):
    print(f"{i}: {repr(line)}")
