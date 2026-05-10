"""
IT Risk Monitor Agent — function-based.
Analyses system health data and produces DORA-aligned risk assessment.
Agent ID: it_monitor_agent_v1.0.0
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from typing import Dict, List
from langchain_groq import ChatGroq
import governance.audit_log as audit_log
import governance.hitl as hitl

AGENT_ID = "it_monitor_agent_v1.0.0"

STATUS_SCORES = {
    "operational": 10,
    "degraded":    55,
    "incident":    90,
}

DORA_THRESHOLDS = {
    "max_latency_ms":   500,
    "max_error_rate":   1.0,
    "max_cpu":          85,
    "max_memory":       85,
    "min_uptime_pct":   99.5,
}

RECOMMENDED_ACTIONS = {
    "incident":    "Activate incident response protocol. Notify CISO. Escalate to CTO. Consider failover.",
    "degraded":    "Investigate root cause. Alert on-call team. Prepare rollback plan. Monitor closely.",
    "operational": "No immediate action required. Continue standard monitoring.",
}


def compute_system_risk(system: Dict) -> Dict:
    status   = system.get("status", "operational")
    cpu      = system.get("cpu", 0)
    memory   = system.get("memory", 0)
    latency  = system.get("latency_ms", 0)
    error_r  = system.get("error_rate", 0)
    uptime   = system.get("uptime_pct", 100)

    base_score = STATUS_SCORES.get(status, 10)
    violations = []

    if latency > DORA_THRESHOLDS["max_latency_ms"]:
        base_score = min(base_score + 15, 100)
        violations.append(f"Latency {latency}ms exceeds {DORA_THRESHOLDS['max_latency_ms']}ms threshold")
    if error_r > DORA_THRESHOLDS["max_error_rate"]:
        base_score = min(base_score + 20, 100)
        violations.append(f"Error rate {error_r}% exceeds {DORA_THRESHOLDS['max_error_rate']}% threshold")
    if cpu > DORA_THRESHOLDS["max_cpu"]:
        base_score = min(base_score + 10, 100)
        violations.append(f"CPU {cpu}% exceeds {DORA_THRESHOLDS['max_cpu']}% threshold")
    if memory > DORA_THRESHOLDS["max_memory"]:
        base_score = min(base_score + 10, 100)
        violations.append(f"Memory {memory}% exceeds {DORA_THRESHOLDS['max_memory']}% threshold")
    if uptime < DORA_THRESHOLDS["min_uptime_pct"]:
        base_score = min(base_score + 15, 100)
        violations.append(f"Uptime {uptime}% below {DORA_THRESHOLDS['min_uptime_pct']}% requirement")

    risk_level = "CRITICAL" if base_score >= 80 else "HIGH" if base_score >= 60 else "MEDIUM" if base_score >= 30 else "LOW"
    requires_human = base_score >= 70 or status in ("incident", "degraded")

    return {
        "system":           system.get("system"),
        "status":           status,
        "risk_score":       base_score,
        "risk_level":       risk_level,
        "requires_human":   requires_human,
        "dora_violations":  violations,
        "recommended_action": RECOMMENDED_ACTIONS.get(status, "Monitor."),
        "criticality":      system.get("criticality", "MEDIUM"),
        "dora_tier":        system.get("dora_tier", 2),
    }


def _get_llm_analysis(systems: List[Dict], results: List[Dict]) -> str:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        return _fallback_analysis(results)
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key, max_retries=1)
        system_summary = "\n".join(
            f"- {r['system']}: status={r['status']}, risk={r['risk_score']}/100, "
            f"cpu={s.get('cpu')}%, mem={s.get('memory')}%, latency={s.get('latency_ms')}ms, "
            f"error_rate={s.get('error_rate')}%, uptime={s.get('uptime_pct')}%"
            for r, s in zip(results, systems)
        )
        violations = "\n".join(
            f"- {r['system']}: {', '.join(r['dora_violations'])}"
            for r in results if r["dora_violations"]
        ) or "None"
        prompt = f"""You are a DORA (Digital Operational Resilience Act) compliance expert at NORDA Bank.

Analyse these IT system health metrics and provide a structured assessment.

SYSTEM STATUS:
{system_summary}

DORA VIOLATIONS DETECTED:
{violations}

Provide a 4-part response:
1. RISK SUMMARY: Which systems pose immediate risk and why (2-3 sentences)
2. PREDICTED TIME TO FAILURE: For degraded/incident systems, estimate time to failure if current trend continues
3. IMMEDIATE ACTIONS: Prioritised list of actions for the IT team (numbered)
4. DORA COMPLIANCE: Assessment of compliance with DORA Art.11 (ICT continuity), Art.17 (incident management), and DORA RTS on ICT risk

Be specific, technical, and actionable. Format with clear section headers."""
        return llm.invoke(prompt).content
    except Exception:
        return _fallback_analysis(results)


def _fallback_analysis(results: List[Dict]) -> str:
    incidents  = [r for r in results if r["status"] == "incident"]
    degraded   = [r for r in results if r["status"] == "degraded"]
    all_violations = [v for r in results for v in r["dora_violations"]]

    parts = []
    if incidents:
        parts.append(f"**CRITICAL INCIDENTS**: {', '.join(r['system'] for r in incidents)} require immediate response.")
    if degraded:
        parts.append(f"**DEGRADED SYSTEMS**: {', '.join(r['system'] for r in degraded)} need urgent investigation.")
    if all_violations:
        parts.append(f"**DORA VIOLATIONS**: {len(all_violations)} threshold breaches detected across monitored systems.")
    if not parts:
        parts.append("All systems within operational parameters. Continue standard DORA monitoring.")

    return " ".join(parts)


def run_it_monitor_agent(systems: List[Dict]) -> Dict:
    """Analyse all IT systems and return aggregate risk report."""
    results = [compute_system_risk(s) for s in systems]

    critical  = [r for r in results if r["status"] == "incident"]
    degraded  = [r for r in results if r["status"] == "degraded"]
    max_score = max((r["risk_score"] for r in results), default=0)
    avg_score = sum(r["risk_score"] for r in results) / len(results) if results else 0

    requires_human = any(r["requires_human"] for r in results)
    analysis = _get_llm_analysis(systems, results)

    decision_id = None
    if requires_human and (critical or degraded):
        affected = ", ".join(r["system"] for r in critical + degraded)
        decision_id = hitl.add_decision(
            agent_id=AGENT_ID,
            domain="IT",
            transaction_id=f"IT-MONITOR-{len(critical)}C-{len(degraded)}D",
            client_id="IT_INFRASTRUCTURE",
            recommendation=f"IT RISK ALERT — {affected}: Immediate review required",
            risk_score=max_score / 100,
            reasoning=analysis,
        )

    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="IT",
        action="monitor_it_systems",
        input_snapshot={"systems_checked": len(systems), "incidents": len(critical), "degraded": len(degraded)},
        output_snapshot={"max_risk_score": max_score, "avg_risk_score": round(avg_score, 1),
                         "requires_human": requires_human},
        risk_score=max_score / 100,
        decision="CRITICAL_ESCALATION" if critical else "WAITING_HUMAN_APPROVAL" if degraded else "MONITOR_ONLY",
        requires_human=requires_human,
    )

    return {
        "systems_analyzed": len(results),
        "incident_count":   len(critical),
        "degraded_count":   len(degraded),
        "max_risk_score":   round(max_score, 1),
        "avg_risk_score":   round(avg_score, 1),
        "requires_human":   requires_human,
        "decision_id":      decision_id,
        "analysis":         analysis,
        "system_results":   results,
        "agent_id":         AGENT_ID,
    }
