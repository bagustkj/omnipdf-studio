import os
import io
import zipfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pypdf import PdfWriter, PdfReader

app = Flask(__name__)
app.secret_key = "omnipdf-secret-key-super-safe"

# Setup Folder Upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


@app.route('/')
def index():
    return render_template('index.html')


# 1. FITUR CONVERT IMAGE TO PDF
@app.route('/convert-image', methods=['POST'])
def convert_image():
    files = request.files.getlist('images')
    if not files or files[0].filename == '':
        flash('Silakan pilih minimal satu gambar!', 'danger')
        return redirect(url_for('index'))

    image_list = []
    for file in files:
        if file and file.filename != '':
            try:
                img = Image.open(file.stream)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                image_list.append(img)
            except Exception:
                continue

    if not image_list:
        flash('Gagal memproses gambar.', 'danger')
        return redirect(url_for('index'))

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'converted_images.pdf')
    image_list[0].save(output_path, save_all=True, append_images=image_list[1:])
    return send_file(output_path, as_attachment=True, download_name='OmniPDF_Images.pdf')


# 2. FITUR TEXT TO PDF
@app.route('/convert-text', methods=['POST'])
def convert_text():
    text_content = request.form.get('text_content', '').strip()
    uploaded_file = request.files.get('text_file')

    if uploaded_file and uploaded_file.filename != '':
        text_content = uploaded_file.read().decode('utf-8', errors='ignore')

    if not text_content:
        flash('Masukkan teks atau unggah file TXT terlebih dahulu!', 'danger')
        return redirect(url_for('index'))

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'converted_text.pdf')
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    custom_style = ParagraphStyle(
        'CustomStyle', parent=styles['Normal'], fontSize=11, leading=16, spaceAfter=10
    )

    story = []
    for p in text_content.split('\n'):
        if p.strip():
            clean_p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(clean_p, custom_style))
        else:
            story.append(Spacer(1, 10))

    doc.build(story)
    return send_file(output_path, as_attachment=True, download_name='OmniPDF_Document.pdf')


# 3. FITUR MERGE PDF
@app.route('/merge-pdf', methods=['POST'])
def merge_pdf():
    files = request.files.getlist('pdf_files')
    if not files or len(files) < 2 or files[0].filename == '':
        flash('Pilih minimal 2 file PDF untuk digabungkan!', 'danger')
        return redirect(url_for('index'))

    merger = PdfWriter()
    count = 0
    for file in files:
        if file and file.filename.lower().endswith('.pdf'):
            merger.append(file)
            count += 1

    if count < 2:
        flash('Minimal harus ada 2 file PDF yang valid!', 'danger')
        return redirect(url_for('index'))

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_output.pdf')
    with open(output_path, 'wb') as f_out:
        merger.write(f_out)
    merger.close()

    return send_file(output_path, as_attachment=True, download_name='OmniPDF_Merged.pdf')


# 4. FITUR SPLIT PDF
@app.route('/split-pdf', methods=['POST'])
def split_pdf():
    file = request.files.get('pdf_file')
    if not file or not file.filename.lower().endswith('.pdf'):
        flash('Pilih file PDF yang valid!', 'danger')
        return redirect(url_for('index'))

    reader = PdfReader(file)
    if len(reader.pages) < 2:
        flash('File PDF minimal harus memiliki 2 halaman untuk dipisah!', 'danger')
        return redirect(url_for('index'))

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            page_buffer = io.BytesIO()
            writer.write(page_buffer)
            page_buffer.seek(0)
            zip_file.writestr(f"Halaman_{i+1}.pdf", page_buffer.getvalue())

    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name='OmniPDF_Split_Pages.zip', mimetype='application/zip')


# 5. FITUR ROTATE PDF
@app.route('/rotate-pdf', methods=['POST'])
def rotate_pdf():
    file = request.files.get('pdf_file')
    angle = request.form.get('angle', '90')

    if not file or not file.filename.lower().endswith('.pdf'):
        flash('Pilih file PDF yang valid!', 'danger')
        return redirect(url_for('index'))

    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(int(angle))
            writer.add_page(page)

        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'rotated.pdf')
        with open(output_path, 'wb') as f_out:
            writer.write(f_out)

        return send_file(output_path, as_attachment=True, download_name='OmniPDF_Rotated.pdf')
    except Exception:
        flash('Gagal memutar file PDF.', 'danger')
        return redirect(url_for('index'))


# Diperlukan untuk Vercel Serverless
app = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
