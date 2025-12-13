# PII Redaction System – Technical Documentation (One-Pager)

## Overview
High-performance, German-language-focused PII detection & redaction pipeline combining:
- Strict regex + mathematical validation (Luhn, IBAN Mod-97)
- Contextual age extraction with TF-IDF
- spaCy `de_core_news_lg` for NER
- Conflict resolution to avoid overlaps/false positives

Average processing time: **< 100 ms per sentence on CPU**

Core logic: `pii.py` → `UnifiedPIIPipeline`

---

## Quick Usage

```python
from pii import UnifiedPIIPipeline

pipeline = UnifiedPIIPipeline()
results = pipeline.process_batch(["Text mit Max Mustermann und IBAN DE89370400440532013000"])
```

Output per text includes `has_pii`, `anonymized_text`, and sorted `detections` list with type, token, original text, positions, confidence, and metadata.

### Supported PII Types
- Person: `PERSON`
- Address: `LOCATION:ADDRESS`
- Contact: `CONTACT:EMAIL`, `CONTACT:PHONE`, `CONTACT:URL`
- Financial: `FINANCIAL:IBAN`, `FINANCIAL:CARD`
- IDs: Tax ID, SSN, driver license, etc.
- Age: `AGE:CHILD/TEEN/ADULT/SENIOR`
- Medical: Medication, condition, procedure

---

## Production Integration (Recommended)

Use the provided FastAPI application in **`app.py`**:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Main Endpoint
`POST /api/v1/anonymize`

**Request**:
```json
{
  "text": "Hallo, ich bin Max Mustermann aus Musterstraße 12.",
  "language": "de"
}
```

**Response**:
```json
{
  "has_pii": true,
  "anonymized_text": "Hallo, ich bin [PII:PERSON_ID_a1b2c3d4] aus [PII:LOCATION:ADDRESS_ID_e5f6g7h8].",
  "detections": [ ... ],
  "processing_time_ms": 87.3
}
```

Health check: `GET /health`

The pipeline is loaded once at startup for maximum performance.

---

## Dependencies

```txt
spacy>=3.0
de-core-news-lg @ https://github.com/explosion/spacy-models/releases/download/de_core_news_lg-3.7.0/de_core_news_lg-3.7.0-py3-none-any.whl
scikit-learn
numpy
fastapi
uvicorn
pydantic
```

Install with:
```bash
pip install spacy scikit-learn numpy fastapi uvicorn pydantic
python -m spacy download de_core_news_lg
```

---

## Notes for Maintainers
- Strict validation reduces false positives (invalid IBANs/cards ignored)
- City names preserved; only full addresses masked
- Deterministic MD5 tokens (same value → same token)
- Index occupation prevents overlapping detections
- Adjust thresholds/blocklists in `UnifiedPIIPipeline.__init__()` if needed

The old `main.py` Streamlit demo can be ignored. Use `app.py` for production.
