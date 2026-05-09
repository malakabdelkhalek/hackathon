"""
Human-in-the-Loop (HITL) queue manager.
All high-risk agent decisions queue here before execution.
Satisfies EU AI Act Article 14: mandatory human oversight.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

_queue: List[Dict] = []


def add_decision(
    domain: str,
    agent_id: str,
    recommendation: str,
    risk_score: float,
    reasoning: str,
    transaction_id: Optional[str] = None,
    client_id: Optional[str] = None,
) -> str:
    decision_id = str(uuid.uuid4())
    decision = {
        "decision_id": decision_id,
        "domain": domain,
        "agent_id": agent_id,
        "transaction_id": transaction_id,
        "client_id": client_id,
        "recommendation": recommendation,
        "risk_score": risk_score,
        "reasoning": reasoning,
        "status": "PENDING",
        "operator_modification": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _queue.append(decision)
    return decision_id


def _find(decision_id: str) -> Optional[Dict]:
    for d in _queue:
        if d["decision_id"] == decision_id:
            return d
    return None


def get_pending() -> List[Dict]:
    return [d for d in _queue if d["status"] == "PENDING"]


def approve(decision_id: str) -> bool:
    d = _find(decision_id)
    if d:
        d["status"] = "APPROVED"
        d["resolved_at"] = datetime.now(timezone.utc).isoformat()
        return True
    return False


def reject(decision_id: str) -> bool:
    d = _find(decision_id)
    if d:
        d["status"] = "REJECTED"
        d["resolved_at"] = datetime.now(timezone.utc).isoformat()
        return True
    return False


def suspend(decision_id: str) -> bool:
    d = _find(decision_id)
    if d:
        d["status"] = "SUSPENDED"
        d["resolved_at"] = datetime.now(timezone.utc).isoformat()
        return True
    return False


def modify_and_approve(decision_id: str, modification: str) -> bool:
    d = _find(decision_id)
    if d:
        d["status"] = "MODIFIED"
        d["operator_modification"] = modification
        d["resolved_at"] = datetime.now(timezone.utc).isoformat()
        return True
    return False


def get_all() -> List[Dict]:
    return list(_queue)
