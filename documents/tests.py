from django.test import TestCase

# Create your tests here.
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import ClassifiedDocument

LLM_MOCK_RESPONSE = {
    "category": "payslip",
    "extracted_fields": {
        "employee_name": "Mario Rossi",
        "employer": "Arletti Partners SRL",
        "period": "Marzo 2026",
        "gross_salary": "2850.00",
        "net_salary": "2015.00",
    }
}

def make_pdf(content=b"%PDF-1.4 fake content payslip"):
    return SimpleUploadedFile("test.pdf", content, content_type="application/pdf")

class ClassifyViewTests(TestCase):

    @patch("documents.views.extract_text", return_value="Busta paga Mario Rossi")
    @patch("documents.views.get_llm_backend")
    def test_happy_path_single(self, mock_llm_factory, mock_extract):
        mock_llm = MagicMock()
        mock_llm.classify.return_value = LLM_MOCK_RESPONSE
        mock_llm_factory.return_value = mock_llm

        r = self.client.post("/api/documents/classify/", {"files": make_pdf()})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["results"][0]["category"], "payslip")

    @patch("documents.views.extract_text", return_value="text")
    @patch("documents.views.get_llm_backend")
    def test_happy_path_multiple(self, mock_llm_factory, mock_extract):
        mock_llm = MagicMock()
        mock_llm.classify.return_value = LLM_MOCK_RESPONSE
        mock_llm_factory.return_value = mock_llm
        files = [make_pdf(), make_pdf(b"%PDF fake2"), make_pdf(b"%PDF fake3")]
        r = self.client.post("/api/documents/classify/", {"files": files})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.json()["results"]), 3)

    def test_invalid_format(self):
        bad = SimpleUploadedFile("doc.exe", b"binary", content_type="application/octet-stream")
        r = self.client.post("/api/documents/classify/", {"files": bad})
        self.assertEqual(r.status_code, 400)

    def test_file_too_large(self):
        big = SimpleUploadedFile("big.pdf", b"x" * (6 * 1024 * 1024), content_type="application/pdf")
        r = self.client.post("/api/documents/classify/", {"files": big})
        self.assertEqual(r.status_code, 400)

    @patch("documents.views.extract_text", return_value="text")
    @patch("documents.views.get_llm_backend")
    def test_llm_unreachable(self, mock_llm_factory, mock_extract):
        mock_llm = MagicMock()
        mock_llm.classify.side_effect = Exception("connection refused")
        mock_llm_factory.return_value = mock_llm
        r = self.client.post("/api/documents/classify/", {"files": make_pdf()})
        self.assertEqual(r.status_code, 503)

    @patch("documents.views.extract_text", return_value="text")
    @patch("documents.views.get_llm_backend")
    def test_retrieve_existing(self, mock_llm_factory, mock_extract):
        mock_llm = MagicMock()
        mock_llm.classify.return_value = LLM_MOCK_RESPONSE
        mock_llm_factory.return_value = mock_llm
        post = self.client.post("/api/documents/classify/", {"files": make_pdf()})
        doc_id = post.json()["results"][0]["id"]
        r = self.client.get(f"/api/documents/{doc_id}/")
        self.assertEqual(r.status_code, 200)

    def test_nonexistent_id(self):
        r = self.client.get("/api/documents/99999/")
        self.assertEqual(r.status_code, 404)

    @patch("documents.views.extract_text", return_value="text")
    @patch("documents.views.get_llm_backend")
    def test_filter_by_category(self, mock_llm_factory, mock_extract):
        mock_llm = MagicMock()
        mock_llm.classify.return_value = LLM_MOCK_RESPONSE
        mock_llm_factory.return_value = mock_llm
        self.client.post("/api/documents/classify/", {"files": make_pdf()})
        r = self.client.get("/api/documents/?category=payslip")
        self.assertEqual(r.status_code, 200)
        for item in r.json()["results"]:
            self.assertEqual(item["category"], "payslip")