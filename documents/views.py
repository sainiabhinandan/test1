from django.shortcuts import render

# Create your views here.
import os, time
from pathlib import Path
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django_filters.rest_framework import DjangoFilterBackend
from .models import ClassifiedDocument
from .serializers import DocumentResultSerializer
from .extraction import extract_text
from .llm.factory import get_llm_backend
from .confidence import compute_confidence

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

class ClassifyDocumentView(APIView):
    def post(self, request):
        files = request.FILES.getlist("files")
        if not files:
            return Response({"error": "No files uploaded."}, status=400)
        if len(files) > 3:
            return Response({"error": "Max 3 files per request."}, status=400)

        results = []
        llm = get_llm_backend()

        for f in files:
            ext = Path(f.name).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                return Response({"error": f"{f.name}: unsupported format."}, status=400)
            if f.size > MAX_SIZE_BYTES:
                return Response({"error": f"{f.name}: exceeds 5MB limit."}, status=400)

            path = default_storage.save(f"uploads/{f.name}", f)
            abs_path = default_storage.path(path)

            start = time.time()
            raw_text = extract_text(abs_path)

            try:
                llm_result = llm.classify(raw_text)
            except Exception as e:
                return Response({"error": f"LLM error: {str(e)}"}, status=503)

            ms = int((time.time() - start) * 1000)
            category = llm_result.get("category", "other")
            fields = llm_result.get("extracted_fields", {})
            confidence = compute_confidence(category, fields, raw_text)

            doc = ClassifiedDocument.objects.create(
                filename=f.name,
                category=category,
                confidence=confidence,
                extracted_fields=fields,
                raw_text_preview=raw_text[:300],
                model_used="claude-sonnet-4-20250514" if os.getenv("LLM_BACKEND") == "remote" else os.getenv("OLLAMA_MODEL"),
                processing_time_ms=ms,
            )
            results.append(DocumentResultSerializer(doc).data)

        return Response({"results": results}, status=201)


class DocumentDetailView(generics.RetrieveAPIView):
    queryset = ClassifiedDocument.objects.all()
    serializer_class = DocumentResultSerializer


# class DocumentListView(generics.ListAPIView):
#     serializer_class = DocumentResultSerializer

#     def get_queryset(self):
#         qs = ClassifiedDocument.objects.all()
#         cat = self.request.query_params.get("category")
#         conf = self.request.query_params.get("confidence")
#         if cat:
#             qs = qs.filter(category=cat)
#         if conf:
#             qs = qs.filter(confidence=conf)
#         return qs

# chage it to return count and results in the same format as detail view, but with pagination support

class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentResultSerializer

    def get_queryset(self):
        qs = ClassifiedDocument.objects.all()
        cat = self.request.query_params.get("category")
        conf = self.request.query_params.get("confidence")
        if cat:
            qs = qs.filter(category=cat)
        if conf:
            qs = qs.filter(confidence=conf)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "results": serializer.data
        })