import os
import io
import zipfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pypdf import PdfWriter, PdfReader

# Gunakan absolute path agar Vercel nemu folder templates
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = "omnipdf-secret-key-super-safe"
