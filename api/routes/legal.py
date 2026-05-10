"""
/api/legal — Legal Document Review endpoints.
"""
import json, os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import require_permission
from agents.legal_reviewer import run_legal_reviewer_agent

router = APIRouter()
_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_documents():
    with open(os.path.join(_DATA, "legal_documents.json")) as f:
        return json.load(f)


class ReviewRequest(BaseModel):
    doc_id: str


@router.get("/documents")
def get_legal_documents(claims: dict = Depends(require_permission("legal"))):
    try:
        return _load_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review")
def review_document(req: ReviewRequest, claims: dict = Depends(require_permission("legal"))):
    try:
        docs = _load_documents()
        doc  = next((d for d in docs if d["id"] == req.doc_id), None)
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document {req.doc_id} not found.")
        result = run_legal_reviewer_agent(doc)
        result["reviewed_by"] = claims["sub"]
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review-all")
def review_all_documents(claims: dict = Depends(require_permission("legal"))):
    try:
        docs    = _load_documents()
        results = [run_legal_reviewer_agent(d) for d in docs]
        high    = sum(1 for r in results if r["risk_level"] == "HIGH")
        return {
            "total":       len(results),
            "high_risk":   high,
            "results":     results,
            "reviewed_by": claims["sub"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
