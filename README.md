# PII Redaction System – Technical Documentation (One-Pager)

## Overview
This repository contains a **high-performance, German-language-focused PII (Personally Identifiable Information) detection & redaction pipeline** combining:
- Strict regex patterns + mathematical validation (Luhn, IBAN Mod-97)
- Contextual age extraction with TF-IDF similarity
- spaCy `de_core_news_lg` for NER (persons, locations, medical entities)
- Conflict resolution & index occupation to prevent overlapping/false positives

Average processing time: **< 100 ms per sentence on CPU**

The core logic lives in `pii.py` → class `UnifiedPIIPipeline`.  
The `main.py` file is only a Streamlit demo (can be ignored).

---

## Core Component: `UnifiedPIIPipeline`

```python
from pii import UnifiedPIIPipeline

pipeline = UnifiedPIIPipeline()        # Loads spaCy model once (de_core_news_lg)
results = pipeline.process_batch(["Your text here", "Another sentence..."])
```

### Input
`process_batch(text_list: List[str])` – accepts a list of strings (batch processing supported).

### Output (per input string)
```json
{
  "has_pii": bool,
  "anonymized_text": str,                       // text with [PII:...] tokens
  "detections": [                               // sorted by start position
    {
      "type": "PERSON" | "LOCATION:ADDRESS" | "CONTACT:EMAIL" | "FINANCIAL:IBAN" | ...,
      "token": "[PII:PERSON_ID_a1b2c3d4]",      // unique deterministic mask
      "text": "Max Mustermann",                 // original value
      "start": 12,
      "end": 26,
      "confidence": 0.95,
      "metadata": {...}                         // optional (e.g. calculated_age)
    }
  ],
  "processing_time_ms": 87
}
```

### Supported PII Types
| Category           | Types                                      | Validation |
|-------------------|--------------------------------------------|------------|
| Person            | `PERSON`                                   | spaCy + blocklists |
| Location          | `LOCATION:ADDRESS`                         | Custom ruler + number check |
| Contact           | `CONTACT:EMAIL`, `CONTACT:PHONE`, `CONTACT:URL` | Strict validators |
| Financial         | `FINANCIAL:IBAN`, `FINANCIAL:CARD`         | Mod-97 & Luhn |
| IDs               | `PII:ID:TAX`, `PII:ID:SSN`, `PII:ID:DRIVERLICENSE`, etc. | Length + format |
| Age               | `AGE:CHILD`, `AGE:TEEN`, `AGE:ADULT`, `AGE:SENIOR` | Contextual TF-IDF |
| Medical           | `MED:MEDICATION`, `MED:CONDITION`, `MED:PROCEDURE` | Ruler + dependency patterns |

---

## Integration into FastAPI (Recommended Way)

```python
# fastapi_app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from pii import UnifiedPIIPipeline
import logging

app = FastAPI(title="PII Redaction API")
pipeline = UnifiedPIIPipeline()   # loaded once at startup

class RedactRequest(BaseModel):
    texts: List[str]

class RedactResponseItem(BaseModel):
    has_pii: bool
    anonymized_text: str
    detections: List[dict]
    processing_time_ms: int

@app.post("/redact", response_model=List[RedactResponseItem])
async def redact_pii(request: RedactRequest):
    if not request.texts:
        raise HTTPException(400, "Empty texts list")
    try:
        results = pipeline.process_batch(request.texts)
        return results
    except Exception as e:
        logging.error(f"Redaction failed: {e}")
        raise HTTPException(500, "Internal processing error")
```

**Endpoint**: `POST /redact`  
**Request body**:
```json
{
  "texts": ["Hallo, ich bin Max Mustermann...", "Meine IBAN ist DE89370400440532013000"]
}
```

Returns the full result structure (same as shown above).

---

## Dependencies (requirements.txt)

```txt
spacy>=3.0
de-core-news-lg @ https://github.com/explosion/spacy-models/releases/download/de_core_news_lg-3.7.0/de_core_news_lg-3.7.0-py3-none-any.whl
scikit-learn
numpy
```

Install with:
```bash
pip install spacy scikit-learn numpy
python -m spacy download de_core_news_lg
```

---

## Key Design Decisions (for the maintainer)

- **Strict validation** → invalid/fake IBANs or credit cards are ignored (reduces false positives)
- **City names preserved**, only specific addresses (street + number) are masked
- Deterministic token generation via MD5 → same value → same token across requests
- Index occupation system prevents overlapping detections
- All heavy models loaded once at initialization

Feel free to adjust thresholds in `FastAgeExtractor(threshold=0.60)` or extend blocklists in `UnifiedPIIPipeline.__init__()`.

You now have everything needed to plug this into any FastAPI (or other) service. The Streamlit demo can be discarded.
