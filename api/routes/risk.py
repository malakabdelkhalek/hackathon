"""
/api/risk — Risk Management and Decision Engine endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import require_permission
from governance.decision_engine import (
    THRESHOLDS, evaluate_transaction_risk,
    evaluate_fraud_risk, evaluate_soc_risk, evaluate_insider_risk,
)
import governance.audit_log as audit_log
import governance.hitl as hitl

router = APIRouter()


class RiskEvaluateRequest(BaseModel):
    domain: str
    factors: dict


@router.get("/thresholds")
def get_thresholds(claims: dict = Depends(require_permission("risk"))):
    return {
        name: {"min": bounds[0], "max": bounds[1]}
        for name, bounds in THRESHOLDS.items()
    }


@router.post("/evaluate")
def evaluate_risk(req: RiskEvaluateRequest, claims: dict = Depends(require_permission("risk"))):
    evaluators = {
        "transaction": evaluate_transaction_risk,
        "fraud":       evaluate_fraud_risk,
        "soc":         evaluate_soc_risk,
        "insider":     evaluate_insider_risk,
    }
    fn = evaluators.get(req.domain.lower())
    if not fn:
        raise HTTPException(status_code=400, detail=f"Unknown domain '{req.domain}'. Use: {list(evaluators)}")
    try:
        result = fn(req.factors)
        result["domain"] = req.domain
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_risk_summary(claims: dict = Depends(require_permission("risk"))):
    entries  = audit_log.get_all_entries()
    pending  = hitl.get_pending()
    all_hitl = hitl.get_all()

    decision_counts = {
        "AUTO_APPROVED":          0,
        "MONITOR_ONLY":           0,
        "WAITING_HUMAN_APPROVAL": 0,
        "CRITICAL_ESCALATION":    0,
        "other":                  0,
    }
    domain_counts: dict = {}
    scores = []

    for e in entries:
        d = e.get("decision", "other")
        if d in decision_counts:
            decision_counts[d] += 1
        else:
            decision_counts["other"] += 1
        dom = e.get("domain", "UNKNOWN")
        domain_counts[dom] = domain_counts.get(dom, 0) + 1
        rs = e.get("risk_score")
        if rs is not None:
            scores.append(float(rs) * 100)

    return {
        "total_events":            len(entries),
        "pending_approvals":       len(pending),
        "critical_count":          decision_counts["CRITICAL_ESCALATION"],
        "waiting_approval_count":  decision_counts["WAITING_HUMAN_APPROVAL"],
        "monitor_count":           decision_counts["MONITOR_ONLY"],
        "approved_count":          decision_counts["AUTO_APPROVED"],
        "highest_risk_score":      round(max(scores, default=0), 1),
        "average_risk_score":      round(sum(scores) / len(scores), 1) if scores else 0,
        "domains_breakdown":       domain_counts,
        "hitl_total":              len(all_hitl),
    }
