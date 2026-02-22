from pypdf import PdfReader
import sys

pdf_path = "backend/outputs/formatted_CKD_ML_Prediction_Enhanced_Paper_111.pdf"

try:
    reader = PdfReader(pdf_path)
    print(f"Pages: {len(reader.pages)}")
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f"--- Page {i+1} ({len(text)} chars) ---")
        if len(text) > 0:
            print(text[:300] + "...")
except Exception as e:
    print(f"Error: {e}")
