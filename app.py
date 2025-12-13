import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from pii import UnifiedPIIPipeline

# --- CONFIGURATION ---
app = FastAPI(
    title="PII Redaction API",
    description="High-performance PII detection and anonymization API for German text.",
    version="1.0.0"
)

# --- GLOBAL STATE (Resource Loading) ---
# We load the pipeline once at the module level (or ideally in a lifespan event)
# to keep the API fast (avoiding reloading models per request).
try:
    pipeline = UnifiedPIIPipeline()
    print("✅ UnifiedPIIPipeline loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load UnifiedPIIPipeline: {e}")
    pipeline = None

# --- DATA MODELS (Pydantic) ---

class AnonymizeRequest(BaseModel):
    text: str = Field(..., description="The input text to anonymize.")
    language: str = Field(default="de", description="Language code (e.g., 'de').")

class DetectionMetadata(BaseModel):
    country: Optional[str] = None
    region: Optional[str] = None
    number_type: Optional[str] = None
    # Allow extra fields for flexibility
    class Config:
        extra = "allow" 

class Detection(BaseModel):
    type: str
    token: str
    text: str
    start: int
    end: int
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

class AnonymizeResponse(BaseModel):
    has_pii: bool
    detections: List[Detection]
    anonymized_text: str
    processing_time_ms: float

# --- ENDPOINTS ---

@app.post("/api/v1/anonymize", response_model=AnonymizeResponse)
async def anonymize_text(request: AnonymizeRequest):
    """
    Anonymizes PII in the provided text.
    Target response time: <300ms.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="PII Pipeline not initialized.")

    start_time = time.perf_counter()

    try:
        # The pipeline logic replicates the Streamlit 'mask_pii_logic'
        # processing a batch of 1 for this endpoint.
        results = pipeline.process_batch([request.text])
        
        # Extract the single result
        data = results[0]
        
        # Calculate precise processing time including API overhead
        end_time = time.perf_counter()
        total_time_ms = round((end_time - start_time) * 1000, 2)

        # Map the pipeline dictionary output to our Pydantic response model
        # ensuring it matches the API contract strictly.
        response_data = AnonymizeResponse(
            has_pii=data.get("has_pii", False),
            detections=data.get("detections", []),
            anonymized_text=data.get("anonymized_text", ""),
            processing_time_ms=total_time_ms
        )
        
        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

# --- HEALTH CHECK ---
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": pipeline is not None}

if __name__ == "__main__":
    import uvicorn
    # Run with: uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)