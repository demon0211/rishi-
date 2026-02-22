from docx import Document
import os
from docx.enum.text import WD_ALIGN_PARAGRAPH

file_path = "uploads/CKD_ML_Prediction_Enhanced_Paper_111.docx"
if os.path.exists(file_path):
    doc = Document(file_path)
    alignments = []
    for p in doc.paragraphs:
        if p.text.strip():
            align = p.alignment
            # If explicit alignment is None, it inherits from style
            if align is None:
                align = p.style.paragraph_format.alignment
            alignments.append(str(align))
    
    from collections import Counter
    print(f"Alignment counts: {Counter(alignments)}")
else:
    print("File not found.")
