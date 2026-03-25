import pdfplumber
import easyocr
import fitz  # PyMuPDF
import numpy as np
from pathlib import Path

# Initialize OCR reader (Italian + English)
reader = easyocr.Reader(['it', 'en'])


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from text-based PDFs using pdfplumber."""
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text.append(content)
    return "\n".join(text)


def extract_text_from_image_array(img_array) -> str:
    """Extract text from image array using EasyOCR."""
    results = reader.readtext(img_array, detail=0)
    return "\n".join(results)


def extract_text_with_ocr_from_pdf(file_path: str) -> str:
    """Convert PDF pages to images using PyMuPDF and run OCR."""
    doc = fitz.open(file_path)
    ocr_text = []

    for page in doc:
        pix = page.get_pixmap()

        # Convert pixmap to numpy array
        img = np.frombuffer(pix.samples, dtype=np.uint8)
        img = img.reshape(pix.height, pix.width, pix.n)

        # Run OCR
        text = extract_text_from_image_array(img)
        if text:
            ocr_text.append(text)

    return "\n".join(ocr_text)


def extract_text(file_path: str) -> str:
    """
    Hybrid extraction pipeline:
    - Extract text using pdfplumber
    - Always run OCR using EasyOCR (via PyMuPDF)
    
    """

    suffix = Path(file_path).suffix.lower()

    # PDF handling
    if suffix == ".pdf":
        pdf_text = extract_text_from_pdf(file_path)

        try:
            ocr_text = extract_text_with_ocr_from_pdf(file_path)
        except Exception as e:
            print(f"OCR error: {e}")
            ocr_text = ""

        # If strong PDF text → prioritize it but include OCR for completeness
        if len(pdf_text.strip()) > 50:
            return pdf_text + "\n" + ocr_text

        # If weak/empty PDF text → rely on OCR
        return ocr_text

    # Image handling
    elif suffix in (".jpg", ".jpeg", ".png"):
        import cv2
        img = cv2.imread(file_path)
        return extract_text_from_image_array(img)

    raise ValueError(f"Unsupported format: {suffix}")