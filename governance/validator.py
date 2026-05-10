"""
Governance validator — 6-rule enforcement layer.
Every agent action passes through this before execution.
Implements Zero Trust: no agent is implicitly trusted.
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

from security.sanitizer import sanitize, PromptInjectionDetected
import governance.audit_log as audit_log

KNOWN_AGENTS = [
    "aml_monitor_v1.0.0",
    "aml_investigator_v1.0.0",
    "kyc_collector_v1.0.0",
    "kyc_assessor_v1.0.0",
    "fraud_agent_v1.0.0",
    "soc_agent_v1.0.0",
    "insider_threat_agent_v1.0.0",
    "sentinel_assistant_v1.0.0",
]

AGENT_ACTION_WHITELIST = {
    "aml_monitor_v1.0.0":           ["flag_transaction", "calculate_risk"],
    "aml_investigator_v1.0.0":      ["investigate_case", "generate_report", "recommend_action"],
    "kyc_collector_v1.0.0":         ["collect_data", "check_sanctions", "check_pep"],
    "kyc_assessor_v1.0.0":          ["assess_risk", "assign_tier", "generate_kyc_report"],
    "fraud_agent_v1.0.0":           ["analyze_fraud_event", "score_transaction"],
    "soc_agent_v1.0.0":             ["analyze_soc_event", "classify_threat"],
    "insider_threat_agent_v1.0.0":  ["analyze_insider_behavior", "build_profile"],
    "sentinel_assistant_v1.0.0":    ["ai_assistant_query"],
}

HIGH_RISK_THRESHOLD = 0.75


def validate_action(
    agent_id: str,
    action: str,
    input_data: Dict,
    risk_score: float = 0.0,
    pipeline_status: str = "ACTIVE",
) -> Dict:
    """
    Validate an agent action against all 6 governance rules.
    Returns: {"approved": bool, "reason": str, "requires_human": bool}
    """
    requires_human = False

    # RULE 1 — Agent authentication
    if agent_id not in KNOWN_AGENTS:
        return {
            "approved": False,
            "reason": f"RULE 1 FAILED: Unknown agent '{agent_id}'. Not in authenticated agent registry.",
            "requires_human": False,
        }

    # RULE 2 — Action whitelist
    allowed_actions = AGENT_ACTION_WHITELIST.get(agent_id, [])
    if action not in allowed_actions:
        return {
            "approved": False,
            "reason": f"RULE 2 FAILED: Action '{action}' is not whitelisted for agent '{agent_id}'. Allowed: {allowed_actions}",
            "requires_human": False,
        }

    # RULE 3 — Input sanitization (prompt injection check)
    for field_name, value in input_data.items():
        if isinstance(value, str):
            try:
                sanitize(value, field_name)
            except PromptInjectionDetected as e:
                return {
                    "approved": False,
                    "reason": f"RULE 3 FAILED: {str(e)}",
                    "requires_human": True,
                }

    # RULE 4 — Risk threshold check (sets requires_human, does not block)
    if risk_score > HIGH_RISK_THRESHOLD:
        requires_human = True

    # RULE 5 — Duplicate action check (within last 60 seconds)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=60)
    input_str = json.dumps(input_data, sort_keys=True, default=str)

    for entry in audit_log.get_all_entries():
        if entry.get("agent_id") != agent_id or entry.get("action") != action:
            continue
        try:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)
        except (ValueError, KeyError):
            continue
        if entry_time >= cutoff:
            entry_input_str = json.dumps(
                entry.get("input_snapshot", {}), sort_keys=True, default=str
            )
            if entry_input_str == input_str:
                return {
                    "approved": False,
                    "reason": f"RULE 5 FAILED: Duplicate action '{action}' by '{agent_id}' detected within 60 seconds. Replay attack prevention.",
                    "requires_human": False,
                }

    # RULE 6 — Pipeline suspension check
    if pipeline_status == "SUSPENDED":
        return {
            "approved": False,
            "reason": "RULE 6 FAILED: Pipeline is SUSPENDED. All agent actions are halted by operator.",
            "requires_human": False,
        }

    return {
        "approved": True,
        "reason": "All 6 governance rules passed.",
        "requires_human": requires_human,
    }
