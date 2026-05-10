"""
HTTP client for the SENTINEL FastAPI backend.
Stores the JWT token and injects it as Bearer on every request.
"""
import os
import requests
from typing import Optional

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
TIMEOUT = 120


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


def _raise(response: requests.Response):
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise APIError(response.status_code, detail)


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth ──────────────────────────────────────────────────────────────────────

def login(username: str, password: str) -> dict:
    """
    POST /auth/token — returns token dict with access_token, role, operator.
    Raises APIError on bad credentials.
    """
    r = requests.post(
        f"{API_BASE}/auth/token",
        data={"username": username, "password": password},
        timeout=10,
    )
    _raise(r)
    return r.json()


def health() -> bool:
    """Return True if the API is reachable."""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.ok
    except Exception:
        return False


# ── AML ───────────────────────────────────────────────────────────────────────

def scan_transaction(token: str, transaction: dict, client: dict, pipeline_status: str = "ACTIVE") -> dict:
    r = requests.post(
        f"{API_BASE}/api/aml/scan",
        json={"transaction": transaction, "client": client, "pipeline_status": pipeline_status},
        headers=_h(token),
        timeout=TIMEOUT,
    )
    _raise(r)
    return r.json()


def investigate_transaction(token: str, transaction: dict, client: dict, pipeline_status: str = "ACTIVE") -> dict:
    r = requests.post(
        f"{API_BASE}/api/aml/investigate",
        json={"transaction": transaction, "client": client, "pipeline_status": pipeline_status},
        headers=_h(token),
        timeout=TIMEOUT,
    )
    _raise(r)
    return r.json()


# ── KYC ───────────────────────────────────────────────────────────────────────

def assess_client(token: str, form_data: dict, pipeline_status: str = "ACTIVE") -> dict:
    r = requests.post(
        f"{API_BASE}/api/kyc/assess",
        json={**form_data, "pipeline_status": pipeline_status},
        headers=_h(token),
        timeout=TIMEOUT,
    )
    _raise(r)
    return r.json()


# ── HITL ──────────────────────────────────────────────────────────────────────

def get_pending(token: str) -> list:
    r = requests.get(f"{API_BASE}/api/hitl/pending", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def approve(token: str, decision_id: str) -> dict:
    r = requests.post(f"{API_BASE}/api/hitl/{decision_id}/approve", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def reject(token: str, decision_id: str) -> dict:
    r = requests.post(f"{API_BASE}/api/hitl/{decision_id}/reject", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def suspend_decision(token: str, decision_id: str) -> dict:
    r = requests.post(f"{API_BASE}/api/hitl/{decision_id}/suspend", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def modify_and_approve(token: str, decision_id: str, modification: str) -> dict:
    r = requests.post(
        f"{API_BASE}/api/hitl/{decision_id}/modify",
        json={"modification": modification},
        headers=_h(token),
        timeout=10,
    )
    _raise(r)
    return r.json()


# ── Audit ─────────────────────────────────────────────────────────────────────

def get_audit_log(token: str) -> list:
    r = requests.get(f"{API_BASE}/api/audit/log", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def verify_chain(token: str) -> list:
    r = requests.get(f"{API_BASE}/api/audit/verify", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


# ── Fraud ─────────────────────────────────────────────────────────────────────

def get_fraud_events(token: str) -> list:
    r = requests.get(f"{API_BASE}/api/fraud/events", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def scan_fraud_event(token: str, event: dict) -> dict:
    r = requests.post(f"{API_BASE}/api/fraud/scan", json={"event": event},
                      headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


def scan_all_fraud(token: str) -> dict:
    r = requests.post(f"{API_BASE}/api/fraud/scan-all", headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


# ── SOC ───────────────────────────────────────────────────────────────────────

def get_soc_events(token: str) -> list:
    r = requests.get(f"{API_BASE}/api/soc/events", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def get_employees(token: str) -> list:
    r = requests.get(f"{API_BASE}/api/soc/employees", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def analyze_soc_event(token: str, event: dict) -> dict:
    r = requests.post(f"{API_BASE}/api/soc/analyze", json={"event": event},
                      headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


def analyze_all_soc(token: str) -> dict:
    r = requests.post(f"{API_BASE}/api/soc/analyze-all", headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


def analyze_insider(token: str, employee_id: str) -> dict:
    r = requests.post(f"{API_BASE}/api/soc/insider-threat/{employee_id}",
                      headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


def analyze_all_insider(token: str) -> dict:
    r = requests.post(f"{API_BASE}/api/soc/insider-threat-all", headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


# ── Risk ──────────────────────────────────────────────────────────────────────

def get_risk_summary(token: str) -> dict:
    r = requests.get(f"{API_BASE}/api/risk/summary", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def get_risk_thresholds(token: str) -> dict:
    r = requests.get(f"{API_BASE}/api/risk/thresholds", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def evaluate_risk(token: str, domain: str, factors: dict) -> dict:
    r = requests.post(f"{API_BASE}/api/risk/evaluate",
                      json={"domain": domain, "factors": factors},
                      headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


def get_it_systems(token: str) -> list:
    r = requests.get(f"{API_BASE}/api/it/systems", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def monitor_it_systems(token: str) -> dict:
    r = requests.post(f"{API_BASE}/api/it/monitor", headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


def get_legal_documents(token: str) -> list:
    r = requests.get(f"{API_BASE}/api/legal/documents", headers=_h(token), timeout=10)
    _raise(r)
    return r.json()


def review_legal_document(token: str, doc_id: str) -> dict:
    r = requests.post(f"{API_BASE}/api/legal/review", json={"doc_id": doc_id},
                      headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


def review_all_legal_documents(token: str) -> dict:
    r = requests.post(f"{API_BASE}/api/legal/review-all", headers=_h(token), timeout=TIMEOUT)
    _raise(r)
    return r.json()


def send_chat(token: str, messages: list, tutorial: bool = False) -> str:
    r = requests.post(
        f"{API_BASE}/api/chat/message",
        json={"messages": messages, "tutorial": tutorial},
        headers=_h(token),
        timeout=40,
    )
    _raise(r)
    return r.json()["reply"]
