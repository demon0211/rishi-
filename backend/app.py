from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from nlp_processor import NLPProcessor, SectionData
from formatter import PDFGenerator, WordGenerator, SpringerPDFGenerator, SpringerWordGenerator
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Absolute paths relative to this script
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

nlp_processor  = NLPProcessor()
pdf_generator  = PDFGenerator(OUTPUT_FOLDER)
word_generator = WordGenerator(OUTPUT_FOLDER)


@app.route('/process', methods=['POST'])
def process_document():
    output_format = request.form.get('format', 'pdf').lower()
    
    # Custom styling parameters
    try:
        style_config = {
            'titleSize': int(request.form.get('titleSize', 24)),
            'sectionSize': int(request.form.get('sectionSize', 10)),
            'subheadingSize': int(request.form.get('subheadingSize', 10)),
            'bodySize': int(request.form.get('bodySize', 10)),
            'lineSpacing': float(request.form.get('lineSpacing', 1.0)),
            'fontFamily': request.form.get('fontFamily', 'Times New Roman')
        }
    except (ValueError, TypeError):
        # Fallback to defaults if parsing fails
        style_config = {}

    # Template selection (default to ieee)
    template = request.form.get('template', 'ieee').lower()

    # Initialize generators based on template
    if template == 'springer':
        pdf_gen = SpringerPDFGenerator(OUTPUT_FOLDER, style_config)
        word_gen = SpringerWordGenerator(OUTPUT_FOLDER, style_config)
        # Mandatory sections for Springer
        mandatory_headings = [
            "Introduction", "Methods", "Results", "Discussion", "Conclusion",
            "Acknowledgements", "Declarations", "Funding", "Conflict of Interest",
            "Ethics Approval", "Consent to Participate", "Data Availability",
            "Code Availability", "Author Contributions", "Appendix"
        ]
    else:
        pdf_gen = PDFGenerator(OUTPUT_FOLDER, style_config)
        word_gen = WordGenerator(OUTPUT_FOLDER, style_config)
        mandatory_headings = []

    raw_text = None
    filename = "pasted_text"
    
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        try:
            raw_text = nlp_processor.extract_text_from_file(input_path)
        except Exception as e:
            return jsonify({'error': f"Failed to read file: {str(e)}"}), 400
    elif 'text' in request.form and request.form['text'].strip():
        raw_text = request.form['text']
        filename = "pasted_text.txt"
    else:
        return jsonify({'error': 'No file or text provided'}), 400

    if not raw_text:
        return jsonify({'error': 'No content to process'}), 400

    # 2. Extract embedded images (best-effort)
    images = []
    try:
        if 'input_path' in locals():
            images = nlp_processor.extract_images_from_file(input_path, IMAGES_FOLDER)
    except Exception as e:
        print(f"[app] Image extraction warning: {e}")

    # 3. Parse text into structured DocumentData
    import json
    doc_data = None
    try:
        # Check if the user uploaded a JSON string instead of a raw text/docx file
        parsed_json = json.loads(raw_text)
        if isinstance(parsed_json, dict) and 'title' in parsed_json and 'authors' in parsed_json:
            # Manually build DocumentData
            from nlp_processor import DocumentData, AuthorInfo
            doc_data = DocumentData(title=parsed_json.get('title', ''))
            
            for a_json in parsed_json.get('authors', []):
                author = AuthorInfo(
                    name=a_json.get('name', ''),
                    email=a_json.get('email', ''),
                    institution=a_json.get('institution', ''),
                    department=a_json.get('department', ''),
                    role=a_json.get('role', a_json.get('designation', '')), # map designation to role
                    address=a_json.get('address', ''),
                    pincode=a_json.get('pincode', ''),
                    university=a_json.get('university', '')
                )
                doc_data.authors.append(author)
                
            # If the user also included sections we could parse them here
            sections = parsed_json.get('sections', [])
            for s in sections:
                from nlp_processor import SectionData
                s_obj = SectionData(
                    heading=s.get('heading', ''),
                    body=s.get('body', '')
                )
                doc_data.sections.append(s_obj)
    except Exception:
        pass
        
    if doc_data is None:
        doc_data = nlp_processor.process_text(raw_text, images=images)

    # 4. Mandatory Section Post-processing (Springer Only)
    if template == 'springer':
        # Ensure Abstract is always present (usually it is, but just in case)
        if not any("ABSTRACT" in s.heading.upper() for s in doc_data.sections):
            doc_data.sections.insert(0, SectionData(heading="Abstract", body="Not Applicable"))
        
        # Check other mandatory sections
        for h in mandatory_headings:
            if not any(h.upper() in s.heading.upper() for s in doc_data.sections):
                doc_data.sections.append(SectionData(heading=h, body="Not Applicable"))
        
        # Ensure References is handled (likely already in doc_data.references)

    # 5. Generate output document
    base_name = os.path.splitext(filename)[0]

    if output_format == 'docx':
        output_filename = f"formatted_{base_name}.docx"
        output_path     = word_gen.generate_docx(doc_data, output_filename)
    else:
        output_filename = f"formatted_{base_name}.pdf"
        output_path     = pdf_gen.generate_pdf(doc_data, output_filename)

    # Prepare sections list for UI
    sections_for_ui = []
    if doc_data.title:
        sections_for_ui.append("TITLE")
    if doc_data.authors:
        sections_for_ui.append("AUTHORS")
    
    # Filter out redundant ABSTRACT heading and add other sections
    other_sections = [s.heading for s in doc_data.sections if s.heading.upper() != "ABSTRACT"]
    sections_for_ui.extend(other_sections)
    
    # Ensure Abstract is in the list if it was processed
    if any(s.heading.upper() == "ABSTRACT" for s in doc_data.sections):
        idx = 2 if ("TITLE" in sections_for_ui and "AUTHORS" in sections_for_ui) else (1 if ("TITLE" in sections_for_ui or "AUTHORS" in sections_for_ui) else 0)
        sections_for_ui.insert(idx, "ABSTRACT")

    return jsonify({
        'message':        'Processing complete',
        'download_url':   f'/download/{output_filename}',
        'title_detected': doc_data.title[:80] if doc_data.title else '(none)',
        'sections_found': sections_for_ui,
        'authors_found':  len(doc_data.authors),
        'images_found':   len(images),
    })


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    filename  = secure_filename(filename)
    file_path = os.path.join(OUTPUT_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
