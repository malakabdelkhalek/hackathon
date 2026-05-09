"""
KYC Assessor Agent — assigns risk tier and writes formal KYC assessment.
Agent ID: kyc_assessor_v1.0.0
"""
import json
import os
import sys
from typing import Any, Dict, Optional, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from rag.retriever import retrieve
import governance.audit_log as audit_log
import governance.hitl as hitl
from governance.validator import validate_action

AGENT_ID = "kyc_assessor_v1.0.0"

HIGH_RISK_NATIONALITIES = {"Russian", "Iranian", "North Korean", "Chinese"}
HIGH_RISK_SOURCES = {"offshore_company", "unknown"}
MEDIUM_RISK_SOURCES = {"business", "investment_portfolio"}
MEDIUM_RISK_ACCOUNT_TYPES = {"corporate"}
NON_EU_NATIONALITIES = {
    "Russian", "Chinese", "Iranian", "North Korean", "Algerian",
    "Emirati", "Saudi", "Nigerian", "Pakistani", "Afghan",
}


class KYCAssessorState(TypedDict):
    collector_output: Dict
    client_profile: Dict
    rag_context: str
    risk_tier: str
    llm_assessment: str
    decision: str
    requires_human: bool
    decision_id: Optional[str]
    blocked: bool
    block_reason: str
    pipeline_status: str


def calculate_risk_tier(profile: Dict, pep_result: Dict, sanctions_result: Dict) -> str:
    if sanctions_result.get("sanctioned"):
        return "REJECTED"

    nationality = profile.get("nationality", "")
    source_of_funds = profile.get("source_of_funds", "")
    account_type = profile.get("account_type", "retail")
    pep_confirmed = pep_result.get("pep_confirmed", False)

    if pep_confirmed:
        return "HIGH"
    if source_of_funds in HIGH_RISK_SOURCES:
        return "HIGH"
    if nationality in HIGH_RISK_NATIONALITIES:
        return "HIGH"

    if nationality in NON_EU_NATIONALITIES:
        return "MEDIUM"
    if source_of_funds in MEDIUM_RISK_SOURCES:
        return "MEDIUM"
    if account_type in MEDIUM_RISK_ACCOUNT_TYPES:
        return "MEDIUM"

    return "LOW"


def node_rag_query(state: KYCAssessorState) -> KYCAssessorState:
    profile = state["client_profile"]
    query = (
        f"KYC risk assessment {profile.get('nationality', '')} national "
        f"source of funds {profile.get('source_of_funds', '')} "
        f"account type {profile.get('account_type', '')} "
        f"PEP status {state['collector_output'].get('pep_result', {}).get('pep_confirmed', False)}"
    )
    state["rag_context"] = retrieve(query, domain="KYC", n_results=3)
    return state


def node_calculate_tier(state: KYCAssessorState) -> KYCAssessorState:
    pep_result = state["collector_output"].get("pep_result", {})
    sanctions_result = state["collector_output"].get("sanctions_result", {})
    tier = calculate_risk_tier(state["client_profile"], pep_result, sanctions_result)
    state["risk_tier"] = tier

    if tier == "REJECTED":
        state["decision"] = "REJECT"
        state["llm_assessment"] = (
            "AUTOMATIC REJECTION — Client matches active sanctions list. "
            "Onboarding is prohibited. Mandatory regulatory report filed."
        )
    return state


def node_llm_assessment(state: KYCAssessorState) -> KYCAssessorState:
    if state.get("decision") == "REJECT":
        return state

    prompt = f"""You are a senior KYC compliance officer at NORDA Bank.
Based on the client profile and retrieved NORDA KYC policy, write a formal risk assessment.

Your assessment must include:
1. RISK TIER ASSIGNED: {state['risk_tier']}
2. KEY RISK FACTORS: List the specific factors that determined this tier
3. POLICY REFERENCE: Cite the specific NORDA policy sections that apply
4. REQUIRED ACTIONS: What must happen before this client can be onboarded
5. DECISION: APPROVE / APPROVE_WITH_CONDITIONS / REJECT / ESCALATE

Client Profile: {json.dumps(state['client_profile'], indent=2)}
PEP Result: {json.dumps(state['collector_output'].get('pep_result', {}), indent=2)}
Sanctions Result: {json.dumps(state['collector_output'].get('sanctions_result', {}), indent=2)}
Calculated Risk Tier: {state['risk_tier']}
Retrieved KYC Policy: {state['rag_context']}

Write your formal risk assessment:"""

    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=os.environ.get("GROQ_API_KEY", ""),
            max_retries=1,
        )
        response = llm.invoke(prompt)
        assessment_text = response.content
    except Exception as e:
        profile = state["client_profile"]
        tier = state["risk_tier"]
        pep = state["collector_output"].get("pep_result", {})
        assessment_text = (
            f"FORMAL KYC RISK ASSESSMENT — AUTOMATED FALLBACK\n\n"
            f"1. RISK TIER ASSIGNED: {tier}\n\n"
            f"2. KEY RISK FACTORS:\n"
            f"- Nationality: {profile.get('nationality', 'N/A')}\n"
            f"- Source of Funds: {profile.get('source_of_funds', 'N/A')}\n"
            f"- Account Type: {profile.get('account_type', 'N/A')}\n"
            f"- PEP Status: {'Confirmed' if pep.get('pep_confirmed') else 'Not detected'}\n\n"
            f"3. POLICY REFERENCE:\n"
            f"NORDA KYC Policy v2.3 — {tier} RISK tier definitions and escalation rules apply.\n"
            f"AML 6th Directive Article 20: PEP enhanced due diligence required.\n\n"
            f"4. REQUIRED ACTIONS:\n"
            f"{'Senior officer sign-off + enhanced background check required.' if tier == 'HIGH' else 'Enhanced due diligence within 5 business days.' if tier == 'MEDIUM' else 'Standard ID and proof of address required.'}\n\n"
            f"5. DECISION: {'ESCALATE' if tier == 'HIGH' else 'APPROVE_WITH_CONDITIONS' if tier == 'MEDIUM' else 'APPROVE'}\n\n"
            f"[LLM unavailable: {str(e)}]"
        )

    state["llm_assessment"] = assessment_text

    decision = "APPROVE"
    for dec in ["REJECT", "ESCALATE", "APPROVE_WITH_CONDITIONS", "APPROVE"]:
        if dec in assessment_text.upper():
            decision = dec
            break
    state["decision"] = decision

    return state


def node_governance_check(state: KYCAssessorState) -> KYCAssessorState:
    if state.get("decision") == "REJECT":
        state["requires_human"] = False
        return state

    risk_score_map = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.9, "REJECTED": 1.0}
    risk_score = risk_score_map.get(state["risk_tier"], 0.5)

    input_snapshot = {
        "name": state["client_profile"].get("name"),
        "nationality": state["client_profile"].get("nationality"),
        "risk_tier": state["risk_tier"],
        "decision": state["decision"],
    }

    validation = validate_action(
        agent_id=AGENT_ID,
        action="generate_kyc_report",
        input_data=input_snapshot,
        risk_score=risk_score,
        pipeline_status=state.get("pipeline_status", "ACTIVE"),
    )

    if not validation["approved"]:
        state["blocked"] = True
        state["block_reason"] = validation["reason"]
        return state

    state["blocked"] = False
    state["requires_human"] = (
        state["risk_tier"] == "HIGH" or
        state["decision"] in {"REJECT", "ESCALATE"} or
        validation["requires_human"]
    )
    return state


def node_hitl_queue(state: KYCAssessorState) -> KYCAssessorState:
    if state.get("blocked") or not state.get("requires_human"):
        return state

    decision_id = hitl.add_decision(
        domain="KYC",
        agent_id=AGENT_ID,
        recommendation=state["decision"],
        risk_score={"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.9}.get(state["risk_tier"], 0.5),
        reasoning=state["llm_assessment"][:1000],
        client_id=state["client_profile"].get("name"),
    )
    state["decision_id"] = decision_id
    return state


def node_audit(state: KYCAssessorState) -> KYCAssessorState:
    risk_score_map = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.9, "REJECTED": 1.0}
    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="KYC",
        action="generate_kyc_report",
        input_snapshot={
            "name": state["client_profile"].get("name"),
            "nationality": state["client_profile"].get("nationality"),
            "account_type": state["client_profile"].get("account_type"),
            "source_of_funds": state["client_profile"].get("source_of_funds"),
        },
        output_snapshot={
            "risk_tier": state["risk_tier"],
            "decision": state["decision"],
            "assessment_preview": state["llm_assessment"][:500],
            "requires_human": state.get("requires_human", False),
        },
        risk_score=risk_score_map.get(state["risk_tier"], 0.5),
        decision=state["decision"],
        requires_human=state.get("requires_human", False),
    )
    return state


def build_assessor_graph():
    graph = StateGraph(KYCAssessorState)
    graph.add_node("rag_query", node_rag_query)
    graph.add_node("calculate_tier", node_calculate_tier)
    graph.add_node("assess", node_llm_assessment)
    graph.add_node("governance", node_governance_check)
    graph.add_node("hitl_queue", node_hitl_queue)
    graph.add_node("audit", node_audit)

    graph.set_entry_point("rag_query")
    graph.add_edge("rag_query", "calculate_tier")
    graph.add_edge("calculate_tier", "assess")
    graph.add_edge("assess", "governance")
    graph.add_edge("governance", "hitl_queue")
    graph.add_edge("hitl_queue", "audit")
    graph.add_edge("audit", END)

    return graph.compile()


_assessor_graph = None


def run_kyc_assessor(collector_output: Dict, pipeline_status: str = "ACTIVE") -> Dict:
    global _assessor_graph
    if _assessor_graph is None:
        _assessor_graph = build_assessor_graph()

    client_profile = collector_output.get("structured_data", {})

    initial_state: KYCAssessorState = {
        "collector_output": collector_output,
        "client_profile": client_profile,
        "rag_context": "",
        "risk_tier": "LOW",
        "llm_assessment": "",
        "decision": "APPROVE",
        "requires_human": False,
        "decision_id": None,
        "blocked": False,
        "block_reason": "",
        "pipeline_status": pipeline_status,
    }

    result = _assessor_graph.invoke(initial_state)
    return {
        "client_profile": result["client_profile"],
        "risk_tier": result["risk_tier"],
        "llm_assessment": result["llm_assessment"],
        "decision": result["decision"],
        "requires_human": result.get("requires_human", False),
        "decision_id": result.get("decision_id"),
        "blocked": result.get("blocked", False),
        "block_reason": result.get("block_reason", ""),
    }
