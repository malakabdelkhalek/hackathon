"""
SOC (Security Operations Center) Agent — function-based.
Detects: brute force, impossible travel, data exfiltration, privilege abuse.
Agent ID: soc_agent_v1.0.0
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from typing import Dict, Optional
from langchain_groq import ChatGroq

from governance.decision_engine import evaluate_soc_risk
from governance.validator import validate_action
import governance.hitl as hitl
import governance.audit_log as audit_log

AGENT_ID = "soc_agent_v1.0.0"

THREAT_CLASSES = {
    "brute_force":            "CREDENTIAL_ATTACK",
    "credential_stuffing":    "CREDENTIAL_ATTACK",
    "data_exfiltration":      "DATA_EXFILTRATION",
    "impossible_travel":      "IMPOSSIBLE_TRAVEL",
    "privilege_escalation":   "PRIVILEGE_ABUSE",
    "insider_access_anomaly": "INSIDER_THREAT",
}

RECOMMENDED_ACTIONS = {
    "CREDENTIAL_ATTACK":  "Block source IP, reset credentials, enable MFA review",
    "DATA_EXFILTRATION":  "Suspend employee access, preserve forensic evidence, notify DPO",
    "IMPOSSIBLE_TRAVEL":  "Suspend session, verify employee identity via secondary channel",
    "PRIVILEGE_ABUSE":    "Revoke elevated access, review permission grants, audit trail",
    "INSIDER_THREAT":     "Alert security team, increase monitoring, schedule HR interview",
}


def _build_factors(event: Dict) -> Dict:
    return {
        "impossible_travel":    int(event.get("impossible_travel", False)),
        "failed_logins_count":  event.get("failed_logins_count", 0),
        "off_hours_access":     int(event.get("off_hours_access", False)),
        "data_volume_gb":       event.get("data_volume_gb", 0),
        "privilege_escalation": int(event.get("privilege_escalation", False)),
        "new_ip_country":       int(event.get("new_ip_country", False)),
        "mfa_bypass_attempt":   int(event.get("mfa_bypass_attempt", False)),
    }


def _classify_threat(event: Dict) -> str:
    return THREAT_CLASSES.get(event.get("type", ""), "ANOMALOUS_ACCESS")


def _get_llm_analysis(event: Dict, score: float, decision: str, threat_class: str) -> str:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        return _fallback_analysis(event, score, decision, threat_class)
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key, max_retries=1)
        prompt = f"""You are a SOC analyst at NORDA Bank.
Analyze this security event and provide a concise 3-sentence assessment.

Event: {event.get('type','unknown')} | Employee: {event.get('employee_id')} | Threat Class: {threat_class}
Description: {event.get('description','')}
Source IP: {event.get('source_ip')} | Country: {event.get('source_country')}
Risk Score: {score:.0f}/100 | Decision: {decision}
Data volume: {event.get('data_volume_gb',0)} GB | Failed logins: {event.get('failed_logins_count',0)}

Write: (1) nature of the threat, (2) why it is suspicious, (3) immediate recommended action."""
        return llm.invoke(prompt).content
    except Exception:
        return _fallback_analysis(event, score, decision, threat_class)


def _fallback_analysis(event: Dict, score: float, decision: str, threat_class: str) -> str:
    recommended = RECOMMENDED_ACTIONS.get(threat_class, "Investigate and monitor.")
    return (
        f"**{threat_class.replace('_',' ')}** detected for employee {event.get('employee_id')} "
        f"from {event.get('source_country','unknown')} — risk score {score:.0f}/100 ({decision}). "
        f"{event.get('description', 'Suspicious activity detected.')} "
        f"Recommended action: {recommended}."
    )


def run_soc_agent(event: Dict) -> Dict:
    """Analyze a SOC security event through the full governance pipeline."""
    event_id    = event.get("id", "SOC-unknown")
    employee_id = event.get("employee_id", "unknown")

    factors       = _build_factors(event)
    engine_result = evaluate_soc_risk(factors)
    score         = engine_result["composite_score"]
    decision      = engine_result["decision"]
    threat_class  = _classify_threat(event)

    input_snapshot = {
        "event_id":    event_id,
        "employee_id": employee_id,
        "type":        event.get("type", ""),
        "source_ip":   event.get("source_ip", ""),
    }

    validation = validate_action(
        agent_id=AGENT_ID,
        action="analyze_soc_event",
        input_data=input_snapshot,
        risk_score=score / 100,
        pipeline_status="ACTIVE",
    )

    blocked, block_reason = False, ""
    if not validation["approved"]:
        blocked = True
        block_reason = validation["reason"]

    analysis    = _get_llm_analysis(event, score, decision, threat_class)
    decision_id: Optional[str] = None

    if not blocked and engine_result["requires_human"]:
        decision_id = hitl.add_decision(
            agent_id=AGENT_ID,
            domain="SOC",
            transaction_id=event_id,
            client_id=employee_id,
            recommendation=f"SOC ALERT — {threat_class}: {event.get('type','').replace('_',' ').title()}",
            risk_score=score / 100,
            reasoning=analysis,
        )

    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="SOC",
        action="analyze_soc_event",
        input_snapshot=input_snapshot,
        output_snapshot={
            "risk_score":   score,
            "decision":     decision,
            "threat_class": threat_class,
            "blocked":      blocked,
            "analysis":     analysis[:300],
        },
        risk_score=score / 100,
        decision="BLOCKED" if blocked else decision,
        requires_human=engine_result["requires_human"],
    )

    return {
        "event_id":           event_id,
        "employee_id":        employee_id,
        "threat_type":        event.get("type", ""),
        "threat_class":       threat_class,
        "risk_score":         round(score, 1),
        "risk_level":         engine_result["risk_level"],
        "decision":           decision,
        "requires_human":     engine_result["requires_human"],
        "analysis":           analysis,
        "decision_id":        decision_id,
        "blocked":            blocked,
        "block_reason":       block_reason,
        "agent_id":           AGENT_ID,
        "recommended_action": RECOMMENDED_ACTIONS.get(threat_class, "Investigate."),
        "raw_factors":        engine_result.get("raw_factors", {}),
    }
