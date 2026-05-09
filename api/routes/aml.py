"""
/api/aml — AML Monitor and Investigator endpoints.
All routes require a valid JWT (operator or admin).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import verify_token
from agents.aml_monitor import run_aml_monitor
from agents.aml_investigator import run_aml_investigator

router = APIRouter()


class ScanRequest(BaseModel):
    transaction: dict
    client: dict
    pipeline_status: str = "ACTIVE"


class InvestigateRequest(BaseModel):
    transaction: dict
    client: dict
    pipeline_status: str = "ACTIVE"


class ScanResult(BaseModel):
    transaction_id: str
    client_id: str
    risk_score: float
    flag: str
    reasoning: str
    requires_human: bool
    decision_id: Optional[str]
    injection_detected: bool
    injection_detail: str
    blocked: bool
    block_reason: str
    scanned_by: str


class InvestigateResult(BaseModel):
    transaction_id: str
    client_id: str
    investigation_report: str
    recommendation: str
    requires_human: bool
    decision_id: Optional[str]
    blocked: bool
    block_reason: str
    investigated_by: str


@router.post("/scan", response_model=ScanResult)
def scan_transaction(req: ScanRequest, claims: dict = Depends(verify_token)):
    """Run AML Monitor agent on a single transaction."""
    try:
        result = run_aml_monitor(req.transaction, req.client, req.pipeline_status)
        result["scanned_by"] = claims["sub"]
        return ScanResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investigate", response_model=InvestigateResult)
def investigate_transaction(req: InvestigateRequest, claims: dict = Depends(verify_token)):
    """Run AML Investigator agent on a flagged transaction."""
    try:
        result = run_aml_investigator(req.transaction, req.client, req.pipeline_status)
        result["investigated_by"] = claims["sub"]
        return InvestigateResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
