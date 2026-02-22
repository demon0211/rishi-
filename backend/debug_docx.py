import os
from nlp_processor import NLPProcessor

file_path = "uploads/CKD_ML_Prediction_Enhanced_Paper_111.docx"
processor = NLPProcessor()

if os.path.exists(file_path):
    print(f"File found: {file_path}")
    raw_text = processor.extract_text_from_file(file_path)
    os.makedirs("uploads/test_images", exist_ok=True)
    images = processor.extract_images_from_file(file_path, "uploads/test_images")
    print(f"Raw text length: {len(raw_text)}")
    print("--- First 5000 chars ---")
    print(raw_text[:5000])
    print("--- Last 500 chars ---")
    print(raw_text[-500:])
    
    # Parse
    doc_data = processor.process_text(raw_text, images=images)
    print("\n--- Processed Data ---")
    print(f"Title: {doc_data.title}")
    print(f"Authors: {len(doc_data.authors)}")
    print(f"Abstract: {len(doc_data.abstract)} chars")
    print(f"Keywords: {doc_data.keywords}")
    print(f"Sections: {len(doc_data.sections)}")
    for sec in doc_data.sections:
        print(f"  - {sec.heading} ({len(sec.body)} chars)")
        if sec.figures:
            print(f"    Figs: {len(sec.figures)}")
            for fig in sec.figures:
                print(f"      - {fig['caption']}: {fig['path']}")
        if sec.tables:
            print(f"    Tables: {len(sec.tables)}")
        if sec.equations:
            print(f"    Eqs: {len(sec.equations)}")
    print(f"References: {len(doc_data.references)}")
    if doc_data.references:
        print(f"  - First reference: {doc_data.references[0]}")
else:
    print(f"File not found: {file_path}")
