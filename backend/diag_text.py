import os
import re
from nlp_processor import NLPProcessor

file_path = "uploads/CKD_ML_Prediction_Enhanced_Paper_111.docx"
p = NLPProcessor()

if os.path.exists(file_path):
    # 1. Test raw extraction for bullets
    text = p.extract_text_from_file(file_path)
    bullet_count = text.count("[BULLET]")
    print(f"Total [BULLET] markers found: {bullet_count}")
    
    # 2. Find specifically 'specifically' and look at surrounding chars
    # The user mentioned missing letters/words.
    # From previous output: "ùspecifically" was seen as "ùspecifically" or similar.
    # Let's look for specific problematic sequences.
    
    pattern = re.compile(r'.{10}specifically.{10}', re.DOTALL)
    matches = pattern.findall(text)
    for m in matches:
        print(f"Context for 'specifically': {repr(m)}")
        for char in m:
            if ord(char) > 127:
                print(f"  Non-ASCII char: {char!r} (hex: {hex(ord(char))})")

    # 3. Test normalization
    norm_text = p._normalize_text(text)
    if "specifically" in norm_text:
        idx = norm_text.find("specifically")
        print(f"Normalized context: {repr(norm_text[idx-5:idx+17])}")
else:
    print("File not found.")
