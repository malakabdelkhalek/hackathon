"""
/api/kyc — KYC Collector + Assessor pipeline endpoint.
All routes require a valid JWT.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import verify_token
from agents.kyc_collector import run_kyc_collector
from agents.kyc_assessor import run_kyc_assessor

router = APIRouter()


class KYCRequest(BaseModel):
    name: str
    nationality: str
    country_of_residence: str
    account_type: str
    source_of_funds: str
    pep_declared: bool = False
    business_description: str = ""
    pipeline_status: str = "ACTIVE"


class KYCResult(BaseModel):
    structured_data: dict
    sanctions_result: dict
    pep_result: dict
    llm_summary: str
    risk_tier: str
    llm_assessment: str
    decision: str
    requires_human: bool
    decision_id: Optional[str]
    injection_detected: bool
    rejected: bool
    reject_reason: str
    assessed_by: str


@router.post("/assess", response_model=KYCResult)
def assess_client(req: KYCRequest, claims: dict = Depends(verify_token)):
    """Run the full KYC pipeline: Collector → Assessor."""
    try:
        form_data = req.model_dump(exclude={"pipeline_status"})
        collector = run_kyc_collector(form_data, req.pipeline_status)

        if collector.get("rejected") or collector.get("injection_detected"):
            return KYCResult(
                structured_data=collector.get("structured_data", {}),
                sanctions_result=collector.get("sanctions_result", {}),
                pep_result=collector.get("pep_result", {}),
                llm_summary=collector.get("llm_summary", ""),
                risk_tier="REJECTED",
                llm_assessment=collector.get("reject_reason", "Rejected at collection stage."),
                decision="REJECT",
                requires_human=False,
                decision_id=None,
                injection_detected=collector.get("injection_detected", False),
                rejected=True,
                reject_reason=collector.get("reject_reason", ""),
                assessed_by=claims["sub"],
            )

        assessor = run_kyc_assessor(collector, req.pipeline_status)
        return KYCResult(
            structured_data=collector.get("structured_data", {}),
            sanctions_result=collector.get("sanctions_result", {}),
            pep_result=collector.get("pep_result", {}),
            llm_summary=collector.get("llm_summary", ""),
            risk_tier=assessor["risk_tier"],
            llm_assessment=assessor["llm_assessment"],
            decision=assessor["decision"],
            requires_human=assessor["requires_human"],
            decision_id=assessor.get("decision_id"),
            injection_detected=False,
            rejected=False,
            reject_reason="",
            assessed_by=claims["sub"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
