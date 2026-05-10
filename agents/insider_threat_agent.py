"""
Insider Threat Agent — function-based.
Builds behavioral profile from employee data + SOC events.
Agent ID: insider_threat_agent_v1.0.0
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from typing import Dict, List, Optional
from langchain_groq import ChatGroq

from governance.decision_engine import evaluate_insider_risk
from governance.validator import validate_action
import governance.hitl as hitl
import governance.audit_log as audit_log

AGENT_ID = "insider_threat_agent_v1.0.0"

BEHAVIORAL_FLAGS = {
    "resignation_notice":       "Employee has submitted resignation notice",
    "declining_performance":    "Recent performance is declining",
    "excessive_after_hours":    "Abnormal after-hours login frequency (>5/month)",
    "high_sensitive_access":    "Excessive access to sensitive files (>50/month)",
    "policy_violations":        "Recent policy violations on record",
    "data_exfil_detected":      "Large data volume uploaded to external destination",
    "impossible_travel":        "Impossible travel detected in SOC events",
    "privilege_abuse":          "Attempted privilege escalation",
}

RECOMMENDED_ACTIONS = {
    "AUTO_APPROVED":          "No action required. Continue standard monitoring.",
    "MONITOR_ONLY":           "Flag for HR periodic review. Increase access logging.",
    "WAITING_HUMAN_APPROVAL": "Alert security team. Review access logs. Consider HR interview.",
    "CRITICAL_ESCALATION":    "Suspend system access immediately. Notify CISO and HR. Preserve forensics.",
}


def build_behavioral_profile(employee: Dict, soc_events: List[Dict]) -> Dict:
    """Build a risk factors dict from employee data and related SOC events."""
    emp_soc = [e for e in soc_events if e.get("employee_id") == employee.get("id")]
    data_exfil_gb = sum(e.get("data_volume_gb", 0) for e in emp_soc)

    return {
        "after_hours_logins":         employee.get("after_hours_logins_30d", 0),
        "data_exfil_volume_mb":       data_exfil_gb * 1024,
        "resignation_flag":           int(employee.get("resignation_notice", False)),
        "access_sensitive_files_count": employee.get("access_sensitive_files_count_30d", 0),
        "policy_violation_count":     employee.get("policy_violations_12m", 0),
        "performance_declining":      int(employee.get("recent_performance", "") == "declining"),
        "access_anomaly_score":       min(len(emp_soc) * 8, 40),
    }


def _get_triggered_flags(employee: Dict, profile: Dict, soc_events: List[Dict]) -> List[str]:
    flags = []
    emp_soc = [e for e in soc_events if e.get("employee_id") == employee.get("id")]
    if employee.get("resignation_notice"):
        flags.append("resignation_notice")
    if employee.get("recent_performance") == "declining":
        flags.append("declining_performance")
    if profile.get("after_hours_logins", 0) > 5:
        flags.append("excessive_after_hours")
    if profile.get("access_sensitive_files_count", 0) > 50:
        flags.append("high_sensitive_access")
    if profile.get("policy_violation_count", 0) > 0:
        flags.append("policy_violations")
    if profile.get("data_exfil_volume_mb", 0) > 100:
        flags.append("data_exfil_detected")
    if any(e.get("impossible_travel") for e in emp_soc):
        flags.append("impossible_travel")
    if any(e.get("privilege_escalation") for e in emp_soc):
        flags.append("privilege_abuse")
    return flags


def _get_llm_analysis(employee: Dict, profile: Dict, score: float, decision: str, flags: List[str]) -> str:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        return _fallback_analysis(employee, score, decision, flags)
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key, max_retries=1)
        prompt = f"""You are a behavioral intelligence analyst at NORDA Bank.
Analyze this employee's insider threat profile.

Employee: {employee.get('name')} | Role: {employee.get('role')} | Dept: {employee.get('department')}
Tenure: {employee.get('tenure_years')} years | Performance: {employee.get('recent_performance')}
Resignation notice: {employee.get('resignation_notice')}

Risk indicators: {', '.join(flags) if flags else 'none detected'}
After-hours logins (30d): {profile.get('after_hours_logins', 0)}
Sensitive file accesses (30d): {profile.get('access_sensitive_files_count', 0)}
Data exfiltration volume: {profile.get('data_exfil_volume_mb', 0):.0f} MB
Policy violations (12m): {profile.get('policy_violation_count', 0)}

Risk Score: {score:.0f}/100 | Decision: {decision}

Write a 3-sentence assessment: (1) threat profile summary, (2) concerning behavioral patterns, (3) recommended action."""
        return llm.invoke(prompt).content
    except Exception:
        return _fallback_analysis(employee, score, decision, flags)


def _fallback_analysis(employee: Dict, score: float, decision: str, flags: List[str]) -> str:
    flag_labels = [BEHAVIORAL_FLAGS.get(f, f) for f in flags[:3]]
    flag_str = "; ".join(flag_labels) if flag_labels else "no critical flags"
    return (
        f"Behavioral analysis for **{employee.get('name')}** ({employee.get('role')}, "
        f"{employee.get('department')}) — risk score {score:.0f}/100 ({decision}). "
        f"Key behavioral flags: {flag_str}. "
        f"Recommended action: {RECOMMENDED_ACTIONS.get(decision, 'Monitor.')}"
    )


def run_insider_threat_agent(employee: Dict, related_soc_events: List[Dict]) -> Dict:
    """Analyze insider threat risk for an employee."""
    employee_id   = employee.get("id", "EMP-unknown")
    employee_name = employee.get("name", "Unknown")

    profile       = build_behavioral_profile(employee, related_soc_events)
    engine_result = evaluate_insider_risk(profile)
    score         = engine_result["composite_score"]
    decision      = engine_result["decision"]
    flags         = _get_triggered_flags(employee, profile, related_soc_events)

    input_snapshot = {
        "employee_id":   employee_id,
        "employee_name": employee_name,
        "department":    employee.get("department", ""),
        "flags":         ",".join(flags),
    }

    validation = validate_action(
        agent_id=AGENT_ID,
        action="analyze_insider_behavior",
        input_data=input_snapshot,
        risk_score=score / 100,
        pipeline_status="ACTIVE",
    )

    blocked, block_reason = False, ""
    if not validation["approved"]:
        blocked = True
        block_reason = validation["reason"]

    analysis    = _get_llm_analysis(employee, profile, score, decision, flags)
    decision_id: Optional[str] = None

    if not blocked and engine_result["requires_human"]:
        decision_id = hitl.add_decision(
            agent_id=AGENT_ID,
            domain="INSIDER",
            transaction_id=employee_id,
            client_id=employee_id,
            recommendation=f"INSIDER THREAT — {employee_name}: {decision}",
            risk_score=score / 100,
            reasoning=analysis,
        )

    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="INSIDER",
        action="analyze_insider_behavior",
        input_snapshot=input_snapshot,
        output_snapshot={
            "risk_score": score,
            "decision":   decision,
            "flags":      flags,
            "blocked":    blocked,
            "analysis":   analysis[:300],
        },
        risk_score=score / 100,
        decision="BLOCKED" if blocked else decision,
        requires_human=engine_result["requires_human"],
    )

    return {
        "employee_id":        employee_id,
        "employee_name":      employee_name,
        "risk_score":         round(score, 1),
        "risk_level":         engine_result["risk_level"],
        "decision":           decision,
        "behavioral_flags":   flags,
        "requires_human":     engine_result["requires_human"],
        "analysis":           analysis,
        "decision_id":        decision_id,
        "blocked":            blocked,
        "block_reason":       block_reason,
        "agent_id":           AGENT_ID,
        "recommended_action": RECOMMENDED_ACTIONS.get(decision, "Monitor."),
        "profile":            profile,
    }
