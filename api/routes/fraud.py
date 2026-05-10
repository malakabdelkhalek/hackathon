"""
/api/fraud — Fraud Detection endpoints.
"""
import json, os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import require_permission
from agents.fraud_agent import run_fraud_agent

router = APIRouter()
_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_fraud_events():
    with open(os.path.join(_DATA, "fraud_events.json")) as f:
        return json.load(f)


class FraudScanRequest(BaseModel):
    event: dict


class FraudScanResult(BaseModel):
    event_id: str
    client_id: str
    fraud_type: str
    risk_score: float
    risk_level: str
    decision: str
    requires_human: bool
    analysis: str
    decision_id: Optional[str]
    blocked: bool
    block_reason: str
    agent_id: str
    scanned_by: str


@router.get("/events")
def get_fraud_events(claims: dict = Depends(require_permission("fraud"))):
    try:
        return _load_fraud_events()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan", response_model=FraudScanResult)
def scan_fraud_event(req: FraudScanRequest, claims: dict = Depends(require_permission("fraud"))):
    try:
        result = run_fraud_agent(req.event)
        return FraudScanResult(**result, scanned_by=claims["sub"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-all")
def scan_all_fraud_events(claims: dict = Depends(require_permission("fraud"))):
    try:
        events = _load_fraud_events()
        results = [run_fraud_agent(e) for e in events]
        critical = sum(1 for r in results if r["decision"] == "CRITICAL_ESCALATION")
        waiting  = sum(1 for r in results if r["decision"] == "WAITING_HUMAN_APPROVAL")
        return {
            "total":     len(results),
            "critical":  critical,
            "waiting":   waiting,
            "results":   results,
            "scanned_by": claims["sub"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
