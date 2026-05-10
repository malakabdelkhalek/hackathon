"""
Adaptive Decision Engine — risk-based auto-approve / monitor / escalate logic.
Single source of truth for all risk thresholds across every NORDA agent.
"""
from datetime import datetime, timezone
from typing import Dict

# 0–100 risk scale thresholds
THRESHOLDS = {
    "AUTO_APPROVED":          (0,  30),
    "MONITOR_ONLY":           (30, 70),
    "WAITING_HUMAN_APPROVAL": (70, 90),
    "CRITICAL_ESCALATION":    (90, 101),
}

COLOR_MAP = {
    "AUTO_APPROVED":          "green",
    "MONITOR_ONLY":           "blue",
    "WAITING_HUMAN_APPROVAL": "orange",
    "CRITICAL_ESCALATION":    "red",
}

RISK_LEVEL_MAP = {
    "AUTO_APPROVED":          "LOW",
    "MONITOR_ONLY":           "MEDIUM",
    "WAITING_HUMAN_APPROVAL": "HIGH",
    "CRITICAL_ESCALATION":    "CRITICAL",
}


def score_to_decision(risk_score: float, confidence_score: float = 75.0) -> Dict:
    """Convert a 0–100 risk score to a structured adaptive decision."""
    risk_score = max(0.0, min(100.0, float(risk_score)))

    if risk_score < 30:
        decision = "AUTO_APPROVED"
        requires_human = False
        escalate = False
        desc = "Risk within acceptable bounds. Automatically approved and logged."
    elif risk_score < 70:
        decision = "MONITOR_ONLY"
        requires_human = False
        escalate = False
        desc = "Moderate risk detected. Flagged for periodic review — no immediate action."
    elif risk_score < 90:
        decision = "WAITING_HUMAN_APPROVAL"
        requires_human = True
        escalate = False
        desc = "High risk. Compliance officer review required before action."
    else:
        decision = "CRITICAL_ESCALATION"
        requires_human = True
        escalate = True
        desc = "Critical risk. Immediate escalation to senior compliance/admin required."

    # Override: high risk + low AI confidence → force human review
    if risk_score >= 70 and confidence_score < 55 and not requires_human:
        decision = "WAITING_HUMAN_APPROVAL"
        requires_human = True
        desc += " [Override: low confidence triggers human review.]"

    return {
        "decision":          decision,
        "risk_score":        round(risk_score, 2),
        "risk_level":        RISK_LEVEL_MAP[decision],
        "requires_human":    requires_human,
        "escalate":          escalate,
        "color_code":        COLOR_MAP[decision],
        "description":       desc,
        "decided_at":        datetime.now(timezone.utc).isoformat(),
    }


def _weighted_score(factors: Dict, weights: Dict) -> float:
    """Generic weighted sum, clamped to [0, 100]."""
    score = 0.0
    for key, weight in weights.items():
        val = factors.get(key, 0)
        score += float(val) * float(weight)
    return max(0.0, min(100.0, score))


# ── Domain-specific evaluators ──────────────────────────────────────────────

def evaluate_transaction_risk(factors: Dict) -> Dict:
    """
    AML transaction risk factors (0–100 scale).
    factors keys (all optional):
      amount_eur, is_high_risk_country, is_pep, risk_tier_high,
      is_structuring, has_vague_memo, velocity_count,
      is_sanctioned_entity, cross_border, unusual_hours
    """
    weights = {
        "is_sanctioned_entity": 60,
        "is_structuring":       40,
        "is_pep":               30,
        "is_high_risk_country": 20,
        "risk_tier_high":       20,
        "cross_border":         10,
        "has_vague_memo":       8,
        "unusual_hours":        7,
        "velocity_count":       5,   # per tx above threshold
    }
    # amount bonus: +10 if ≥10k, +5 if 9k–10k
    f = dict(factors)
    amt = f.get("amount_eur", 0)
    if amt >= 10000:
        f["is_structuring"] = max(f.get("is_structuring", 0), 0.5)
    elif 9000 < amt < 10000:
        f["is_structuring"] = max(f.get("is_structuring", 0), 0.3)

    raw_score = _weighted_score(f, weights)
    result = score_to_decision(raw_score)
    result["raw_factors"] = {k: f.get(k, 0) for k in weights}
    result["composite_score"] = raw_score
    return result


def evaluate_fraud_risk(factors: Dict) -> Dict:
    """
    Fraud detection factors (0–100 scale).
    factors keys:
      card_present (bool, reduces risk), velocity_1h, geo_mismatch (bool),
      device_fingerprint_new (bool), amount_deviation_pct,
      time_since_last_txn_minutes, is_international (bool)
    """
    weights = {
        "geo_mismatch":           25,
        "device_fingerprint_new": 15,
        "is_international":       10,
        "card_not_present":       10,   # derived below
        "high_velocity":          0,    # derived below
        "large_deviation":        0,    # derived below
        "very_fast_followup":     20,
    }
    f = dict(factors)
    f["card_not_present"]   = 0 if f.get("card_present", False) else 1
    f["high_velocity"]      = min(f.get("velocity_1h", 0) * 8, 30)
    dev = f.get("amount_deviation_pct", 0)
    f["large_deviation"]    = min(max(0, (dev - 50) * 0.05), 15)
    ttl = f.get("time_since_last_txn_minutes", 999)
    f["very_fast_followup"] = 1 if ttl < 5 else 0

    raw_score = _weighted_score(f, weights)
    result = score_to_decision(raw_score)
    result["raw_factors"] = {k: f.get(k, 0) for k in weights}
    result["composite_score"] = raw_score
    return result


def evaluate_soc_risk(factors: Dict) -> Dict:
    """
    SOC/cybersecurity event factors (0–100 scale).
    factors keys:
      impossible_travel (bool), failed_logins_count, off_hours_access (bool),
      data_volume_gb, privilege_escalation (bool),
      new_ip_country (bool), mfa_bypass_attempt (bool)
    """
    weights = {
        "impossible_travel":    35,
        "mfa_bypass_attempt":   40,
        "privilege_escalation": 30,
        "new_ip_country":       15,
        "off_hours_access":     12,
        "brute_force_bonus":    0,   # derived below
        "exfil_bonus":          0,   # derived below
    }
    f = dict(factors)
    failed = f.get("failed_logins_count", 0)
    f["brute_force_bonus"] = min(failed * 1.5, 30) if failed > 5 else 0
    gb = f.get("data_volume_gb", 0)
    f["exfil_bonus"] = min(gb * 3, 30) if gb > 1 else 0

    raw_score = _weighted_score(f, weights)
    result = score_to_decision(raw_score)
    result["raw_factors"] = {k: f.get(k, 0) for k in weights}
    result["composite_score"] = raw_score
    return result


def evaluate_insider_risk(factors: Dict) -> Dict:
    """
    Insider threat factors (0–100 scale).
    factors keys:
      after_hours_logins, data_exfil_volume_mb, resignation_flag (bool),
      access_sensitive_files_count, policy_violation_count,
      performance_declining (bool), access_anomaly_score (0–40)
    """
    weights = {
        "resignation_flag":          30,
        "performance_declining":     10,
        "access_anomaly_score":      1.0,
        "after_hours_bonus":         0,   # derived
        "exfil_bonus":               0,   # derived
        "sensitive_access_bonus":    0,   # derived
        "violation_bonus":           0,   # derived
    }
    f = dict(factors)
    f["after_hours_bonus"]       = min(f.get("after_hours_logins", 0) * 3, 20)
    f["exfil_bonus"]             = min(f.get("data_exfil_volume_mb", 0) * 0.02, 20)
    f["sensitive_access_bonus"]  = min(max(0, f.get("access_sensitive_files_count", 0) - 20) * 0.5, 15)
    f["violation_bonus"]         = min(f.get("policy_violation_count", 0) * 8, 24)

    raw_score = _weighted_score(f, weights)
    result = score_to_decision(raw_score)
    result["raw_factors"] = {k: f.get(k, 0) for k in weights}
    result["composite_score"] = raw_score
    return result
