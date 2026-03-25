import pdfplumber
import easyocr
from pathlib import Path

# Why pdfplumber: best at structured PDF tables & layout; pythonic API.
# Why EasyOCR: supports 80+ languages including Italian; no system Tesseract needed.

reader = easyocr.Reader(['it', 'en'])

def extract_text_from_pdf(file_path: str) -> str:
    with pdfplumber.open(file_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def extract_text_from_image(file_path: str) -> str:
    results = reader.readtext(file_path, detail=0)
    return "\n".join(results)

def extract_text(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in (".jpg", ".jpeg", ".png"):
        return extract_text_from_image(file_path)
    raise ValueError(f"Unsupported format: {suffix}")