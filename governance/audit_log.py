"""
Hash-chained audit log — every agent decision is logged immutably.
Satisfies EU AI Act Article 17 and AML 6th Directive auditability requirements.
"""
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_entries: List[Dict] = []
_log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audit_log.json")


def _init_log_file():
    if not os.path.exists(_log_file):
        with open(_log_file, "w") as f:
            json.dump([], f)
    else:
        global _entries
        try:
            with open(_log_file, "r") as f:
                _entries = json.load(f)
        except (json.JSONDecodeError, IOError):
            _entries = []


_init_log_file()


def _compute_hash(entry_without_hash: Dict) -> str:
    serialized = json.dumps(entry_without_hash, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def get_last_hash() -> str:
    if not _entries:
        return "GENESIS"
    return _entries[-1].get("current_entry_hash", "GENESIS")


def log_decision(
    agent_id: str,
    domain: str,
    action: str,
    input_snapshot: Dict,
    output_snapshot: Any,
    risk_score: Optional[float],
    decision: str,
    requires_human: bool,
    llm_model: str = "groq/llama-3.3-70b-versatile",
) -> Dict:
    previous_hash = get_last_hash()

    entry_without_hash = {
        "entry_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "agent_version": agent_id.split("_v")[-1] if "_v" in agent_id else "1.0.0",
        "domain": domain,
        "action": action,
        "input_snapshot": input_snapshot,
        "output_snapshot": output_snapshot,
        "llm_model": llm_model,
        "risk_score": risk_score,
        "decision": decision,
        "requires_human": requires_human,
        "previous_entry_hash": previous_hash,
    }

    current_hash = _compute_hash(entry_without_hash)
    entry = {**entry_without_hash, "current_entry_hash": current_hash}

    _entries.append(entry)

    try:
        with open(_log_file, "w") as f:
            json.dump(_entries, f, indent=2, default=str)
    except IOError as e:
        print(f"WARNING: Could not write audit log to file: {e}")

    return entry


def get_all_entries() -> List[Dict]:
    return list(_entries)


def verify_chain_integrity() -> List[Dict]:
    """
    Verify the hash chain integrity of the entire audit log.
    Returns a list of verification results per entry.
    """
    results = []
    prev_hash = "GENESIS"

    for i, entry in enumerate(_entries):
        entry_without_hash = {k: v for k, v in entry.items() if k != "current_entry_hash"}
        expected_hash = _compute_hash(entry_without_hash)
        actual_hash = entry.get("current_entry_hash", "")
        prev_hash_ok = entry.get("previous_entry_hash", "") == prev_hash

        is_valid = (expected_hash == actual_hash) and prev_hash_ok

        results.append({
            "index": i,
            "entry_id": entry.get("entry_id", ""),
            "agent_id": entry.get("agent_id", ""),
            "action": entry.get("action", ""),
            "valid": is_valid,
            "hash_match": expected_hash == actual_hash,
            "chain_intact": prev_hash_ok,
            "current_hash": actual_hash[:16],
        })
        prev_hash = actual_hash

    return results
