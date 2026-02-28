import sys
sys.path.append(r"c:\Users\gokul\OneDrive\Desktop\rishi 2\backend")
from nlp_processor import NLPProcessor
import re

nlp = NLPProcessor()

block = """
line 1: 1st Given Name Surname line 2: dept. name of organization (of Affiliation)

line 3: name of organization (of Affiliation)

line 4: City, Country

line 5: email address or ORCID
"""

authors = nlp._extract_authors_from_block(block)
print(f"Authors extracted: {len(authors)}")
for a in authors:
    print(a)
    
print("-" * 20)
print("Regex test:")
chunks = re.split(r'\n{2,}', block.strip())
for chunk in chunks:
    print(f"CHUNK: {chunk}")
    cleaned_chunk = re.sub(r'(?i)line\s*\d+\s*:\s*(?:\d*(?:st|nd|rd|th)\s*)?', '', chunk)
    print(f"CLEANED: {cleaned_chunk}")
