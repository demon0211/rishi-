from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from nlp_processor import NLPProcessor
from formatter import PDFGenerator, WordGenerator
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
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    output_format = request.form.get('format', 'pdf').lower()

    if file:
        filename   = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        # 1. Extract raw text
        try:
            raw_text = nlp_processor.extract_text_from_file(input_path)
        except Exception as e:
            return jsonify({'error': f"Failed to read file: {str(e)}"}), 400

        if not raw_text:
            return jsonify({'error': 'Text extraction failed. File may be empty or unsupported.'}), 400

        # 2. Extract embedded images (best-effort)
        images = []
        try:
            images = nlp_processor.extract_images_from_file(input_path, IMAGES_FOLDER)
        except Exception as e:
            print(f"[app] Image extraction warning: {e}")

        # 3. Parse text into structured DocumentData
        doc_data = nlp_processor.process_text(raw_text, images=images)

        # 4. Generate output document
        base_name = os.path.splitext(filename)[0]

        if output_format == 'docx':
            output_filename = f"formatted_{base_name}.docx"
            output_path     = word_generator.generate_docx(doc_data, output_filename)
        else:
            output_filename = f"formatted_{base_name}.pdf"
            output_path     = pdf_generator.generate_pdf(doc_data, output_filename)

        return jsonify({
            'message':        'Processing complete',
            'download_url':   f'/download/{output_filename}',
            'title_detected': doc_data.title[:80] if doc_data.title else '(none)',
            'sections_found': [s.heading for s in doc_data.sections],
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
    app.run(debug=True, port=5000)
