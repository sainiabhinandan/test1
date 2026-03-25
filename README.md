# Document Classification & Extraction API

Prototype REST API built with Django + DRF for automatic document classification and key-field extraction using an LLM.

## Stack

- Python 3.13 (compatible with Python >= 3.10)
- Django 6 + Django REST Framework
- SQLite
- PDF extraction: `pdfplumber` (+ `PyMuPDF` for OCR fallback on scanned PDFs)
- OCR: `EasyOCR`
- LLM backends (strategy pattern):
  - Remote: Anthropic
  - Local: Ollama

## Project Structure

- `documents/extraction.py`: text extraction (PDF/image + OCR)
- `documents/llm/base.py`: backend interface
- `documents/llm/remote.py`: Anthropic backend
- `documents/llm/local.py`: Ollama backend
- `documents/llm/factory.py`: env-based backend selection
- `documents/confidence.py`: confidence heuristic
- `documents/views.py`: classify/detail/list endpoints
- `documents/models.py`: persisted classification result
- `documents/tests.py`: API tests

## Why these extraction libraries

- `pdfplumber`: reliable and simple for text-based PDFs, good layout-aware extraction for business docs.
- `PyMuPDF` + `EasyOCR`: scanned PDFs/images often contain no embedded text; pages are rasterized and then OCR is applied.
- `EasyOCR`: fast setup (no external OCR binary required), supports multilingual OCR (Italian + English).

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Environment Configuration

Create a `.env` file in project root:

```env
# LLM selection: remote | local
LLM_BACKEND=remote

# Remote backend (Anthropic)
ANTHROPIC_API_KEY=your_key_here

# Local backend (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Switch backend by changing only:

```env
LLM_BACKEND=local
```

## Sample .env that can be used for ollama just copy
```env

DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-here
LLM_BACKEND=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
EOF
```

## Supported Categories

- `identity_document`
- `employment_contract`
- `payslip`
- `invoice`
- `tax_form`
- `other`

## Extracted Fields (examples)

- `identity_document`: `full_name`, `date_of_birth`, `document_number`, `expiry_date`, `nationality`
- `payslip`: `employee_name`, `employer`, `period`, `gross_salary`, `net_salary`
- `invoice`: `issuer`, `recipient`, `total_amount`, `date`, `invoice_number`

## Confidence Heuristic

Implemented in `documents/confidence.py`.

Rules:

1. Expected field count per category (default: 5 for main categories).
2. Compute filled ratio = non-empty extracted fields / expected fields.
3. If raw text length < 100 chars -> `low`.
4. Else:
   - ratio >= 0.8 -> `high`
   - ratio >= 0.5 -> `medium`
   - otherwise -> `low`

## API Endpoints

### 1) Classify documents

`POST /api/documents/classify/`

- Multipart key: `files`
- Max 3 files per request
- Allowed formats: PDF, JPEG, PNG
- Max size: 5 MB per file

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/documents/classify/ \
  -F "files=@sample/payslip.png" \
  -F "files=@sample/invoice.pdf"
```

Example response:

```json
{
  "results": [
    {
    "id": "1",
    "filename": "payslip.png",
    "category": "payslip",
    "confidence": "high",
    "extracted_fields": {
        "employee_name": "Mario Rossi",
        "employer": "Arletti Partners SRL",
        "period": "Marzo 2026",
        "gross_salary": "1.250,00",
        "net_salary": "1.250,00"
    },
    "raw_text_preview": "BUSTA\nPAGA\n(DUMMY )\nPeriodo\ndi riferimento\nMarzo\n2026\nData pagamento:\n25/03/2026\nDatore di\nlavoro\nArletti\nPartners\nSRL\nDipendente\nMario\nRossi\nRetribuzione lorda\n1.250,00\nDettaglio competenze\nStipendio\nbase:\n1.250,00\nIrattenute\nContributi previdenziali:\nIRPEF\nIotale trattenute\nNetto\nin busta\n1.250,00",
    "model_used": "llama3.2",
    "processing_time_ms": 6926,
    "created_at": "2026-03-25T15:22:07.861087Z" 
    }
  ]
}
```

### 2) Retrieve one result

`GET /api/documents/{id}/`

```bash
curl http://127.0.0.1:8000/api/documents/1/
```

### 3) List and filter

`GET /api/documents/?category=payslip&confidence=high`

```bash
curl "http://127.0.0.1:8000/api/documents/?category=payslip&confidence=high"
```

Example response:

```json
{
  "count": 3,
  "results": [
    {{
    "count": 3,
    "results": [
        {
            "id": "1",
            "filename": "payslip.png",
            "category": "payslip",
            "confidence": "high",
            "created_at": "2026-03-25T15:22:07.861087Z"
        },
    }
  ]
}
```

## Data Persistence

Classification output is stored in SQLite model `ClassifiedDocument` with:

- file name
- predicted category
- extracted fields (JSON)
- confidence
- text preview
- model identifier
- processing time
- created timestamp

## Tests

Run test suite:

```bash
python manage.py test
```

Covered scenarios:

- single file happy path
- multiple files happy path
- invalid file format
- oversized file
- unreachable LLM (mocked)
- retrieve existing result
- non-existent ID
- filtering by category

## Security & Operational Notes

- File format and size are validated before processing.
- LLM and OCR/PDF operations can be expensive; local LLM request timeout is set to 30 seconds.
- API keys are loaded from `.env` and never hardcoded in application logic.
- `.gitignore` excludes `.env`, SQLite DB files, caches, and uploads.

## Git History Note (Security Fix)

During development, an `.env` file containing an API key was accidentally committed.

To address this:

- The sensitive file was removed from the repository.
- Git history was rewritten to ensure the API key was no longer present.
- A force push was performed once to apply this fix.

After this correction:

- No further force pushes were used.
- Development continued following the required Git workflow (feature branches, PRs, atomic commits).

This action was taken solely for security reasons to prevent exposing credentials.

## Small code snippets

### Backend strategy selection

```python
from documents.llm.factory import get_llm_backend

llm = get_llm_backend()  # returns RemoteLLM or LocalLLM based on LLM_BACKEND
result = llm.classify(raw_text)
```

### Confidence scoring

```python
from documents.confidence import compute_confidence

confidence = compute_confidence(category, extracted_fields, raw_text)
```

## Use of AI

AI usage was kept minimal and focused on drafting help only.

- Tools used:
  - GitHub Copilot: small template suggestions while writing repetitive code blocks.
  - Prompt assistant usage: understanding prompt structure and refining wording for clearer JSON output.

- What AI was used for:
  - Template scaffolding (starter structure ).
  - Prompt understanding and phrasing improvements.
  - for writing the tests

- What was done manually:
  - Architecture decisions.
  - Final implementation logic.
  - Error handling decisions.
  - debugging.

## Known limitations / next improvements


- Add async processing (submit + poll) and Docker Compose for one-command startup.
