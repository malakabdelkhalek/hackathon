"""
/api/hitl — Human-in-the-Loop decision control.
All routes require a valid JWT. Suspend/pipeline routes require admin.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from api.auth import verify_token
import governance.hitl as hitl

router = APIRouter()


class DecisionOut(BaseModel):
    decision_id: str
    domain: str
    agent_id: str
    transaction_id: Optional[str]
    client_id: Optional[str]
    recommendation: str
    risk_score: float
    reasoning: str
    status: str
    operator_modification: Optional[str]
    created_at: str


class ModifyRequest(BaseModel):
    modification: str


@router.get("/pending", response_model=List[DecisionOut])
def get_pending(claims: dict = Depends(verify_token)):
    return hitl.get_pending()


@router.get("/all", response_model=List[DecisionOut])
def get_all(claims: dict = Depends(verify_token)):
    return hitl.get_all()


@router.post("/{decision_id}/approve")
def approve(decision_id: str, claims: dict = Depends(verify_token)):
    if not hitl.approve(decision_id):
        raise HTTPException(status_code=404, detail="Decision not found.")
    return {"decision_id": decision_id, "status": "APPROVED", "by": claims["sub"]}


@router.post("/{decision_id}/reject")
def reject(decision_id: str, claims: dict = Depends(verify_token)):
    if not hitl.reject(decision_id):
        raise HTTPException(status_code=404, detail="Decision not found.")
    return {"decision_id": decision_id, "status": "REJECTED", "by": claims["sub"]}


@router.post("/{decision_id}/suspend")
def suspend(decision_id: str, claims: dict = Depends(verify_token)):
    if not hitl.suspend(decision_id):
        raise HTTPException(status_code=404, detail="Decision not found.")
    return {"decision_id": decision_id, "status": "SUSPENDED", "by": claims["sub"]}


@router.post("/{decision_id}/modify")
def modify(decision_id: str, req: ModifyRequest, claims: dict = Depends(verify_token)):
    if not hitl.modify_and_approve(decision_id, req.modification):
        raise HTTPException(status_code=404, detail="Decision not found.")
    return {
        "decision_id": decision_id,
        "status": "MODIFIED",
        "modification": req.modification,
        "by": claims["sub"],
    }
