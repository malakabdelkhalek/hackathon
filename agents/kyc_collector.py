"""
KYC Collector Agent — structures onboarding data, checks PEP and sanctions.
Agent ID: kyc_collector_v1.0.0
"""
import os
import sys
from typing import Any, Dict, Optional, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from security.sanitizer import sanitize, PromptInjectionDetected
import governance.audit_log as audit_log
from governance.validator import validate_action

AGENT_ID = "kyc_collector_v1.0.0"

SANCTIONED_NAMES = ["Ivan Petrov", "Ahmed Al-Qaeda", "Shell Corp BVI"]
SANCTIONED_COUNTRIES = ["North Korea", "Iran", "Syria", "Belarus"]
PEP_HIGH_RISK_NATIONALITIES = ["Russian", "Chinese", "Iranian", "North Korean"]


def check_sanctions(name: str, nationality: str) -> Dict:
    name_lower = name.lower()
    sanctioned_flag = any(s.lower() in name_lower for s in SANCTIONED_NAMES)
    country_sanctioned = nationality in SANCTIONED_COUNTRIES

    if sanctioned_flag:
        return {
            "sanctioned": True,
            "reason": f"Name '{name}' matches OFAC/EU sanctions list.",
        }
    if country_sanctioned:
        return {
            "sanctioned": True,
            "reason": f"Nationality '{nationality}' is a sanctioned country under EU regulations.",
        }
    return {"sanctioned": False, "reason": "No sanctions match found."}


def check_pep(name: str, nationality: str, pep_declared: bool) -> Dict:
    pep_by_nationality = nationality in PEP_HIGH_RISK_NATIONALITIES
    pep_confirmed = pep_declared or pep_by_nationality

    return {
        "pep_confirmed": pep_confirmed,
        "pep_declared": pep_declared,
        "pep_by_nationality_flag": pep_by_nationality,
        "enhanced_dd_required": pep_confirmed,
        "reason": (
            "PEP status confirmed by self-declaration."
            if pep_declared
            else f"Enhanced due diligence required: nationality '{nationality}' is on PEP-risk list."
            if pep_by_nationality
            else "No PEP indicators detected."
        ),
    }


class KYCCollectorState(TypedDict):
    form_data: Dict
    structured_data: Dict
    sanctions_result: Dict
    pep_result: Dict
    llm_summary: str
    injection_detected: bool
    injection_detail: str
    rejected: bool
    reject_reason: str
    pipeline_status: str


def node_sanitize(state: KYCCollectorState) -> KYCCollectorState:
    form = state["form_data"]
    string_fields = ["name", "nationality", "country_of_residence",
                     "account_type", "source_of_funds", "business_description"]
    for field in string_fields:
        value = form.get(field, "")
        if isinstance(value, str):
            try:
                sanitize(value, f"form.{field}")
            except PromptInjectionDetected as e:
                state["injection_detected"] = True
                state["injection_detail"] = str(e)
                state["rejected"] = True
                state["reject_reason"] = f"PROMPT INJECTION BLOCKED: {str(e)}"
                return state
    state["injection_detected"] = False
    return state


def node_structure_data(state: KYCCollectorState) -> KYCCollectorState:
    if state.get("rejected"):
        return state
    form = state["form_data"]
    state["structured_data"] = {
        "name": form.get("name", "").strip(),
        "nationality": form.get("nationality", ""),
        "country_of_residence": form.get("country_of_residence", ""),
        "account_type": form.get("account_type", "retail"),
        "source_of_funds": form.get("source_of_funds", "salary"),
        "pep_declared": bool(form.get("pep_declared", False)),
        "business_description": form.get("business_description", ""),
    }
    return state


def node_sanctions_check(state: KYCCollectorState) -> KYCCollectorState:
    if state.get("rejected"):
        return state
    d = state["structured_data"]
    result = check_sanctions(d["name"], d["nationality"])
    state["sanctions_result"] = result
    if result["sanctioned"]:
        state["rejected"] = True
        state["reject_reason"] = (
            f"AUTOMATIC REJECTION: Client matches sanctions list. {result['reason']} "
            f"Mandatory report to authorities required under AML 6th Directive Article 7."
        )
    return state


def node_pep_check(state: KYCCollectorState) -> KYCCollectorState:
    if state.get("rejected"):
        return state
    d = state["structured_data"]
    result = check_pep(d["name"], d["nationality"], d["pep_declared"])
    state["pep_result"] = result
    return state


def node_llm_summary(state: KYCCollectorState) -> KYCCollectorState:
    if state.get("rejected"):
        return state

    prompt = f"""You are a KYC compliance officer at NORDA Bank.
Review this client onboarding data and provide a structured summary of the key compliance-relevant facts.
Highlight any concerns you observe.

Client Data: {state['structured_data']}
PEP Check Result: {state['pep_result']}
Sanctions Check Result: {state['sanctions_result']}

Provide a 3-4 sentence professional summary:"""

    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=os.environ.get("GROQ_API_KEY", ""),
            max_retries=1,
        )
        response = llm.invoke(prompt)
        state["llm_summary"] = response.content
    except Exception as e:
        d = state["structured_data"]
        pep = state["pep_result"]
        state["llm_summary"] = (
            f"Client {d.get('name')} ({d.get('nationality')}) applying for {d.get('account_type')} account. "
            f"Source of funds declared as {d.get('source_of_funds')}. "
            f"PEP status: {'confirmed' if pep.get('pep_confirmed') else 'not detected'}. "
            f"Sanctions check: clear. [LLM unavailable: {str(e)}]"
        )
    return state


def node_governance_check(state: KYCCollectorState) -> KYCCollectorState:
    if state.get("rejected"):
        return state
    d = state.get("structured_data", {})
    input_snapshot = {
        "name": d.get("name"),
        "nationality": d.get("nationality"),
        "account_type": d.get("account_type"),
        "source_of_funds": d.get("source_of_funds"),
    }
    validation = validate_action(
        agent_id=AGENT_ID,
        action="collect_data",
        input_data=input_snapshot,
        risk_score=0.5 if state["pep_result"].get("pep_confirmed") else 0.2,
        pipeline_status=state.get("pipeline_status", "ACTIVE"),
    )
    if not validation["approved"]:
        state["rejected"] = True
        state["reject_reason"] = validation["reason"]
    return state


def node_audit(state: KYCCollectorState) -> KYCCollectorState:
    d = state.get("structured_data", state["form_data"])
    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="KYC",
        action="collect_data",
        input_snapshot={
            "name": d.get("name"),
            "nationality": d.get("nationality"),
            "account_type": d.get("account_type"),
        },
        output_snapshot={
            "pep_confirmed": state.get("pep_result", {}).get("pep_confirmed", False),
            "sanctioned": state.get("sanctions_result", {}).get("sanctioned", False),
            "rejected": state.get("rejected", False),
            "summary_preview": state.get("llm_summary", "")[:300],
        },
        risk_score=0.8 if state.get("sanctions_result", {}).get("sanctioned") else
                   0.5 if state.get("pep_result", {}).get("pep_confirmed") else 0.2,
        decision="REJECTED" if state.get("rejected") else "COLLECTED",
        requires_human=state.get("pep_result", {}).get("pep_confirmed", False),
    )
    return state


def build_collector_graph():
    graph = StateGraph(KYCCollectorState)
    graph.add_node("sanitize", node_sanitize)
    graph.add_node("structure_data", node_structure_data)
    graph.add_node("sanctions_check", node_sanctions_check)
    graph.add_node("pep_check", node_pep_check)
    graph.add_node("summarize", node_llm_summary)
    graph.add_node("governance", node_governance_check)
    graph.add_node("audit", node_audit)

    graph.set_entry_point("sanitize")
    graph.add_edge("sanitize", "structure_data")
    graph.add_edge("structure_data", "sanctions_check")
    graph.add_edge("sanctions_check", "pep_check")
    graph.add_edge("pep_check", "summarize")
    graph.add_edge("summarize", "governance")
    graph.add_edge("governance", "audit")
    graph.add_edge("audit", END)

    return graph.compile()


_collector_graph = None


def run_kyc_collector(form_data: Dict, pipeline_status: str = "ACTIVE") -> Dict:
    global _collector_graph
    if _collector_graph is None:
        _collector_graph = build_collector_graph()

    initial_state: KYCCollectorState = {
        "form_data": form_data,
        "structured_data": {},
        "sanctions_result": {"sanctioned": False, "reason": ""},
        "pep_result": {"pep_confirmed": False, "enhanced_dd_required": False},
        "llm_summary": "",
        "injection_detected": False,
        "injection_detail": "",
        "rejected": False,
        "reject_reason": "",
        "pipeline_status": pipeline_status,
    }

    result = _collector_graph.invoke(initial_state)
    return {
        "structured_data": result.get("structured_data", {}),
        "sanctions_result": result.get("sanctions_result", {}),
        "pep_result": result.get("pep_result", {}),
        "llm_summary": result.get("llm_summary", ""),
        "injection_detected": result.get("injection_detected", False),
        "rejected": result.get("rejected", False),
        "reject_reason": result.get("reject_reason", ""),
    }
