"""
Fraud Detection Agent — function-based (no LangGraph).
Covers: card fraud, account takeover, wire fraud, synthetic identity, mule accounts.
Agent ID: fraud_agent_v1.0.0
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Optional
from langchain_groq import ChatGroq

from governance.decision_engine import evaluate_fraud_risk
from governance.validator import validate_action
import governance.hitl as hitl
import governance.audit_log as audit_log

AGENT_ID = "fraud_agent_v1.0.0"

FRAUD_TYPE_LABELS = {
    "card_not_present":   "Card Not Present Fraud",
    "account_takeover":   "Account Takeover",
    "wire_fraud":         "Wire Fraud",
    "synthetic_identity": "Synthetic Identity",
    "phishing_mule":      "Phishing / Money Mule",
    "first_party_fraud":  "First-Party Fraud",
}


def _build_factors(event: Dict) -> Dict:
    return {
        "card_present":              event.get("card_present", False),
        "velocity_1h":               event.get("velocity_1h", 0),
        "geo_mismatch":              int(event.get("geo_mismatch", False)),
        "device_fingerprint_new":    int(event.get("device_fingerprint_new", False)),
        "amount_deviation_pct":      event.get("amount_deviation_pct", 0),
        "time_since_last_txn_minutes": event.get("time_since_last_txn_minutes", 999),
        "is_international":          int(event.get("is_international", False)),
    }


def _get_llm_analysis(event: Dict, score: float, decision: str) -> str:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        return _fallback_analysis(event, score, decision)
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key, max_retries=1)
        prompt = f"""You are a fraud detection analyst at NORDA Bank.
Analyze this fraud event and provide a concise 3-sentence assessment.

Event: {event.get('type','unknown')} | Client: {event.get('client_id')} | Amount: €{event.get('amount',0):,.2f}
Description: {event.get('description','')}
Risk Score: {score:.0f}/100 | Decision: {decision}
Geo mismatch: {event.get('geo_mismatch')} | New device: {event.get('device_fingerprint_new')} | Velocity (1h): {event.get('velocity_1h',0)}

Write: (1) why this is suspicious, (2) key risk indicators, (3) recommended action. Be specific."""
        return llm.invoke(prompt).content
    except Exception as e:
        return _fallback_analysis(event, score, decision)


def _fallback_analysis(event: Dict, score: float, decision: str) -> str:
    fraud_type = FRAUD_TYPE_LABELS.get(event.get("type", ""), event.get("type", "Unknown"))
    flags = []
    if event.get("geo_mismatch"):
        flags.append("geographic mismatch")
    if event.get("device_fingerprint_new"):
        flags.append("unrecognized device")
    if event.get("velocity_1h", 0) > 2:
        flags.append(f"high velocity ({event['velocity_1h']} tx/hour)")
    if event.get("amount_deviation_pct", 0) > 100:
        flags.append(f"amount {event['amount_deviation_pct']}% above baseline")
    if event.get("time_since_last_txn_minutes", 999) < 5:
        flags.append("transaction < 5 minutes after previous")
    flag_str = ", ".join(flags) if flags else "anomalous pattern"
    return (
        f"**{fraud_type}** detected on client {event.get('client_id')} — "
        f"risk score {score:.0f}/100 ({decision}). "
        f"Key indicators: {flag_str}. "
        f"Transaction of €{event.get('amount',0):,.2f} to {event.get('merchant_country','unknown')}. "
        f"Recommended: {'Block and escalate for investigation.' if score >= 70 else 'Monitor account activity closely.'}"
    )


def run_fraud_agent(event: Dict) -> Dict:
    """Analyze a fraud event through the full governance pipeline."""
    event_id  = event.get("id", "FRD-unknown")
    client_id = event.get("client_id", "unknown")

    factors = _build_factors(event)
    engine_result = evaluate_fraud_risk(factors)
    score    = engine_result["composite_score"]
    decision = engine_result["decision"]

    input_snapshot = {
        "event_id":  event_id,
        "client_id": client_id,
        "type":      event.get("type", ""),
        "amount":    event.get("amount", 0),
    }

    validation = validate_action(
        agent_id=AGENT_ID,
        action="analyze_fraud_event",
        input_data=input_snapshot,
        risk_score=score / 100,
        pipeline_status="ACTIVE",
    )

    blocked, block_reason = False, ""
    if not validation["approved"]:
        blocked = True
        block_reason = validation["reason"]

    analysis  = _get_llm_analysis(event, score, decision)
    decision_id: Optional[str] = None

    if not blocked and engine_result["requires_human"]:
        decision_id = hitl.add_decision(
            agent_id=AGENT_ID,
            domain="FRAUD",
            transaction_id=event_id,
            client_id=client_id,
            recommendation=f"FRAUD ALERT — {FRAUD_TYPE_LABELS.get(event.get('type',''), event.get('type',''))}",
            risk_score=score / 100,
            reasoning=analysis,
        )

    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="FRAUD",
        action="analyze_fraud_event",
        input_snapshot=input_snapshot,
        output_snapshot={
            "risk_score":   score,
            "decision":     decision,
            "blocked":      blocked,
            "analysis":     analysis[:300],
        },
        risk_score=score / 100,
        decision="BLOCKED" if blocked else decision,
        requires_human=engine_result["requires_human"],
    )

    return {
        "event_id":       event_id,
        "client_id":      client_id,
        "fraud_type":     event.get("type", ""),
        "risk_score":     round(score, 1),
        "risk_level":     engine_result["risk_level"],
        "decision":       decision,
        "requires_human": engine_result["requires_human"],
        "analysis":       analysis,
        "decision_id":    decision_id,
        "blocked":        blocked,
        "block_reason":   block_reason,
        "agent_id":       AGENT_ID,
        "raw_factors":    engine_result.get("raw_factors", {}),
    }
