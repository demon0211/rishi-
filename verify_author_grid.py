import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from nlp_processor import DocumentData, AuthorInfo, SectionData
from formatter import PDFGenerator, WordGenerator

def test_author_layouts():
    output_dir = os.path.join(os.getcwd(), 'outputs', 'verification')
    os.makedirs(output_dir, exist_ok=True)
    
    # Base document data
    doc_data = DocumentData(
        title="Dynamic IEEE Document Formatting Verification",
        authors=[], # To be filled
        keywords=["IEEE", "ReportLab", "Python", "Automation", "Academic Writing"],
        sections=[
            SectionData(heading="Abstract", body="This paper presents a dynamic layout engine for IEEE standard conference papers. We verify the placement of Title, Authors, Abstract and Index Terms. The engine handles various author counts and ensures visual symmetry."),
            SectionData(heading="Introduction", body="The introduction section follows the abstract. In IEEE format, the abstract and index terms are usually in the single-column area before the two-column body begins."),
            SectionData(heading="Methodology", body="We use ReportLab for PDF generation and python-docx for Word documents. The grid logic is centralized in a layout manager."),
        ],
        references=["[1] J. Doe, 'Testing Document Layouts,' IEEE Trans., 2026.", "[2] A. Expert, 'Small Caps and Grids,' Journal of Formatting, 2025."]
    )

    # Test cases: 1 to 6 authors
    for count in range(1, 7):
        authors = []
        for i in range(1, count + 1):
            authors.append(AuthorInfo(
                name=f"Author Number {i}",
                role="Senior Researcher",
                institution="Saveetha School of Engineering",
                university="SIMATS University",
                address="Chennai, India",
                email=f"author{i}@saveetha.com"
            ))
        
        doc_data.authors = authors
        
        # PDF
        pdf_gen = PDFGenerator(output_dir)
        pdf_path = pdf_gen.generate_pdf(doc_data, f"ieee_authors_{count}.pdf")
        
        # Word
        word_gen = WordGenerator(output_dir)
        word_path = word_gen.generate_docx(doc_data, f"ieee_authors_{count}.docx")
        
        print(f"Generated test results for {count} authors: PDF & DOCX")

    # Stress test: Long affiliation
    long_author = AuthorInfo(
        name="Long Affiliation Author",
        institution="Department of Advanced Bio-Inspired Neuromorphic Computing Research and Development Division, Institute of Extreme Technology and Innovation Management, Global Research Hub",
        email="long@research.org"
    )
    doc_data.authors = [long_author]
    pdf_gen.generate_pdf(doc_data, "ieee_authors_long_aff.pdf")
    print("Generated stress test PDF with long affiliation.")

if __name__ == "__main__":
    test_author_layouts()
