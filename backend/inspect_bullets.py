from docx import Document
import os

file_path = "uploads/CKD_ML_Prediction_Enhanced_Paper_111.docx"
if os.path.exists(file_path):
    doc = Document(file_path)
    for i, p in enumerate(doc.paragraphs[:50]): # Check first 50 paragraphs
        xml = p._element.xml
        # Look for numbering properties
        has_num = 'w:numPr' in xml
        print(f"P{i}: Style='{p.style.name}', Num={has_num}, Text='{p.text[:50]}...'")
        if has_num or i < 5: # Show XML for first few or any with numbering
             pass # print(xml) # Uncomment if needed, but it's large
else:
    print("File not found.")
