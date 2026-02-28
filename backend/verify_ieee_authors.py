import os
from nlp_processor import DocumentData, AuthorInfo
from formatter import PDFGenerator, WordGenerator

def test_ieee_authors():
    OUTPUT_FOLDER = os.path.dirname(os.path.abspath(__file__))
    data = DocumentData(
        title="Sample IEEE Paper",
        authors=[
            AuthorInfo(name="Alice Smith", role="Professor", department="Computer Science", institution="MIT", email="alice@mit.edu"),
            AuthorInfo(name="Bob Jones", role="Researcher", department="Physics", institution="Stanford", email="bob@stanford.edu"),
            AuthorInfo(name="Charlie Brown", role="Student", department="Mathematics", institution="Harvard", email="charlie@harvard.edu"),
            AuthorInfo(name="David White", role="Engineer", department="Engineering", institution="Berkeley", email="david@berkeley.edu")
        ],
        sections=[],
        references=[]
    )
    
    style_config = {}
    
    pdf_gen = PDFGenerator(OUTPUT_FOLDER, style_config)
    pdf_path = pdf_gen.generate_pdf(data, "test_ieee_authors.pdf")
    print(f"PDF generated: {pdf_path}")
    
    word_gen = WordGenerator(OUTPUT_FOLDER, style_config)
    word_path = word_gen.generate_docx(data, "test_ieee_authors.docx")
    print(f"Word generated: {word_path}")

if __name__ == "__main__":
    test_ieee_authors()
