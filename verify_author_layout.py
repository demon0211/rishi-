import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from nlp_processor import NLPProcessor

def test_author_extraction():
    nlp = NLPProcessor()
    
    sample_text = """
    A Modern Approach to Deep Learning in Healthcare
    
    John Doe
    Research Scholar
    Dept. of Computer Science
    Saveetha College of Liberal Arts and Sciences
    SIMATS Deemed to be University
    Address: Saveetha Nagar, Thandalam, Chennai
    Pin code: 602105
    Email: john.doe@example.com
    
    Jane Smith
    Assistant Professor
    Dept. of Information Technology
    Saveetha Engineering College
    Anna University
    Address: Thandalam, Chennai
    Pin code: 602105
    Email: jane.smith@example.com
    
    ABSTRACT
    This paper discusses...
    """
    
    doc = nlp.process_text(sample_text)
    
    print(f"Title: {doc.title}")
    print(f"Number of authors: {len(doc.authors)}")
    
    for i, a in enumerate(doc.authors):
        print(f"\nAuthor {i+1}:")
        print(f"  Name: {a.name}")
        print(f"  Role: {a.role}")
        print(f"  Dept: {a.department}")
        print(f"  Inst: {a.institution}")
        print(f"  Univ: {a.university}")
        print(f"  Addr: {a.address}")
        print(f"  Pin:  {a.pincode}")
        print(f"  Email: {a.email}")

if __name__ == "__main__":
    test_author_extraction()
