EXPECTED_FIELDS = {
    "identity_document": 5,
    "employment_contract": 5,
    "payslip": 5,
    "invoice": 5,
    "tax_form": 5,
    "other": 0,
}

def compute_confidence(category: str, extracted_fields: dict, raw_text: str) -> str:
    """
    Heuristic: score based on (a) ratio of non-null fields extracted vs expected,
    and (b) minimum raw text length (very short text = low confidence).
    """
    expected = EXPECTED_FIELDS.get(category, 0)
    if expected == 0:
        return "low"
    filled = sum(1 for v in extracted_fields.values() if v)
    ratio = filled / expected
    if len(raw_text) < 100:
        return "low"
    if ratio >= 0.8:
        return "high"
    if ratio >= 0.5:
        return "medium"
    return "low"