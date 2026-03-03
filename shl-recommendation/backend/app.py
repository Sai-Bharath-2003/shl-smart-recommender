"""
SHL Assessment Recommendation API
FastAPI backend with /health and /recommend endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import logging

from recommender import get_engine, CATALOG_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="Intelligent recommendation system for SHL assessments",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    query: str

class AssessmentResponse(BaseModel):
    url: str
    name: str
    adaptive_support: str
    description: str
    duration: int
    remote_support: str
    test_type: List[str]

class RecommendResponse(BaseModel):
    recommended_assessments: List[AssessmentResponse]

# ---------------------------------------------------------------------------
# Global engine (initialized on startup)
# ---------------------------------------------------------------------------

engine = None

@app.on_event("startup")
async def startup_event():
    global engine
    api_key = os.environ.get("GEMINI_API_KEY", "")
    catalog_path = os.environ.get("CATALOG_PATH", CATALOG_PATH)
    
    logger.info("Initializing recommendation engine...")
    try:
        engine = get_engine(catalog_path=catalog_path, api_key=api_key)
        logger.info("Engine initialized successfully")
    except Exception as e:
        logger.error(f"Engine initialization failed: {e}")
        # Don't crash - engine will be None and we'll handle in endpoint


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    """
    Get assessment recommendations for a job description or natural language query.
    
    - Accepts text queries, job descriptions, or URLs containing JDs
    - Returns 5-10 most relevant SHL assessments
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if engine is None:
        raise HTTPException(status_code=503, detail="Recommendation engine not initialized")
    
    try:
        recommendations = engine.recommend(
            query=request.query.strip(),
            n=10,
            use_llm_rerank=True
        )
        
        # Ensure we have at least 1, at most 10
        recommendations = recommendations[:10]
        if not recommendations:
            raise HTTPException(status_code=404, detail="No recommendations found")
        
        return RecommendResponse(
            recommended_assessments=[
                AssessmentResponse(
                    url=r.get('url', ''),
                    name=r.get('name', ''),
                    adaptive_support=r.get('adaptive_support', 'No'),
                    description=r.get('description', ''),
                    duration=r.get('duration', 0) or 0,
                    remote_support=r.get('remote_support', 'Yes'),
                    test_type=r.get('test_type', [])
                )
                for r in recommendations
            ]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"status": "online", "engine": "SHL Recommendation System"}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
