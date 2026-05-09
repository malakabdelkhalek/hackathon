"""
AML Monitor Agent — scans transactions, assigns risk scores 0.0–1.0.
Agent ID: aml_monitor_v1.0.0
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
from rag.retriever import retrieve
import governance.audit_log as audit_log
import governance.hitl as hitl
from governance.validator import validate_action

AGENT_ID = "aml_monitor_v1.0.0"
HIGH_RISK_COUNTRIES = {"Malta", "Cyprus", "UAE", "BVI", "British Virgin Islands"}
VAGUE_MEMOS = {"consulting", "invoice", "payment", "services"}


class AMLMonitorState(TypedDict):
    transaction: Dict
    client: Dict
    risk_score: float
    flag: str
    reasoning: str
    rag_context: str
    injection_detected: bool
    injection_detail: str
    requires_human: bool
    decision_id: Optional[str]
    blocked: bool
    block_reason: str
    pipeline_status: str


def calculate_risk_score(transaction: Dict, client: Dict) -> float:
    score = 0.0
    amount = transaction.get("amount", 0)
    destination = transaction.get("country_destination", "")
    memo = transaction.get("memo", "").lower().strip()
    pep = client.get("pep_status", False)
    risk_tier = client.get("risk_tier", "LOW")

    if 9000 < amount < 10000:
        score += 0.40
    if amount >= 10000:
        score += 0.4
    if destination in HIGH_RISK_COUNTRIES:
        score += 0.2
    if pep:
        score += 0.3
    if risk_tier == "HIGH":
        score += 0.2
    elif risk_tier == "MEDIUM":
        score += 0.1
    if memo in VAGUE_MEMOS:
        score += 0.1

    return min(score, 1.0)


def node_sanitize(state: AMLMonitorState) -> AMLMonitorState:
    memo = state["transaction"].get("memo", "")
    try:
        sanitize(memo, "transaction.memo")
        state["injection_detected"] = False
        state["injection_detail"] = ""
    except PromptInjectionDetected as e:
        state["injection_detected"] = True
        state["injection_detail"] = str(e)
        state["risk_score"] = 1.0
        state["flag"] = "INJECTION_DETECTED"
        state["reasoning"] = (
            "SECURITY ALERT: Prompt injection attempt detected in transaction memo field. "
            "Input has been rejected without LLM processing. "
            f"Detail: {str(e)}"
        )
    return state


def node_calculate(state: AMLMonitorState) -> AMLMonitorState:
    if state.get("injection_detected"):
        return state
    score = calculate_risk_score(state["transaction"], state["client"])
    state["risk_score"] = score
    return state


def node_llm_reasoning(state: AMLMonitorState) -> AMLMonitorState:
    if state.get("injection_detected"):
        return state
    if state["risk_score"] <= 0.4:
        state["reasoning"] = (
            f"Transaction assessed as low risk (score: {state['risk_score']:.2f}). "
            "No suspicious indicators detected."
        )
        state["flag"] = "CLEAN"
        return state

    query = (
        f"{state['transaction'].get('amount', 0)} EUR transfer to "
        f"{state['transaction'].get('country_destination', 'unknown')} "
        f"memo: {state['transaction'].get('memo', '')}"
    )
    rag_context = retrieve(query, domain="AML", n_results=2)
    state["rag_context"] = rag_context

    prompt = f"""You are an AML compliance officer at NORDA Bank.
Analyze this transaction and explain in 2-3 sentences why it is or is not suspicious.
Be specific about which indicators triggered concern. Speak like a professional compliance officer.

Transaction: {state['transaction']}
Client Profile: {state['client']}
Calculated Risk Score: {state['risk_score']:.2f}
Retrieved AML Regulations: {rag_context}

Provide your reasoning:"""

    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=os.environ.get("GROQ_API_KEY", ""),
            max_retries=1,
        )
        response = llm.invoke(prompt)
        state["reasoning"] = response.content
    except Exception as e:
        state["reasoning"] = (
            f"LLM unavailable ({str(e)}). Risk score {state['risk_score']:.2f} calculated from "
            f"rule-based indicators: amount={state['transaction'].get('amount')}, "
            f"destination={state['transaction'].get('country_destination')}, "
            f"PEP={state['client'].get('pep_status')}."
        )

    state["flag"] = "SUSPICIOUS" if state["risk_score"] > 0.4 else "CLEAN"
    return state


def node_governance_check(state: AMLMonitorState) -> AMLMonitorState:
    tx_id = state["transaction"].get("id", "unknown")
    input_snapshot = {
        "transaction_id": tx_id,
        "amount": state["transaction"].get("amount"),
        "country_destination": state["transaction"].get("country_destination"),
        "memo": "[SANITIZED]" if state.get("injection_detected") else state["transaction"].get("memo"),
    }

    validation = validate_action(
        agent_id=AGENT_ID,
        action="flag_transaction",
        input_data=input_snapshot,
        risk_score=state["risk_score"],
        pipeline_status=state.get("pipeline_status", "ACTIVE"),
    )

    if not validation["approved"] and not state.get("injection_detected"):
        state["blocked"] = True
        state["block_reason"] = validation["reason"]
        state["flag"] = "BLOCKED"
        return state

    state["blocked"] = False
    state["requires_human"] = validation["requires_human"] or state.get("injection_detected", False)

    if state["requires_human"]:
        decision_id = hitl.add_decision(
            domain="AML",
            agent_id=AGENT_ID,
            recommendation=state["flag"],
            risk_score=state["risk_score"],
            reasoning=state["reasoning"],
            transaction_id=tx_id,
        )
        state["decision_id"] = decision_id

    return state


def node_audit(state: AMLMonitorState) -> AMLMonitorState:
    tx_id = state["transaction"].get("id", "unknown")
    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="AML",
        action="flag_transaction",
        input_snapshot={
            "transaction_id": tx_id,
            "client_id": state["transaction"].get("client_id"),
            "amount": state["transaction"].get("amount"),
            "country_destination": state["transaction"].get("country_destination"),
            "memo": "[INJECTION_BLOCKED]" if state.get("injection_detected") else state["transaction"].get("memo"),
        },
        output_snapshot={
            "risk_score": state["risk_score"],
            "flag": state["flag"],
            "reasoning": state["reasoning"][:500],
            "injection_detected": state.get("injection_detected", False),
        },
        risk_score=state["risk_score"],
        decision=state["flag"],
        requires_human=state.get("requires_human", False),
    )
    return state


def _should_stop_early(state: AMLMonitorState) -> str:
    if state.get("injection_detected"):
        return "governance"
    return "calculate"


def build_monitor_graph():
    graph = StateGraph(AMLMonitorState)
    graph.add_node("sanitize", node_sanitize)
    graph.add_node("calculate", node_calculate)
    graph.add_node("llm_reasoning", node_llm_reasoning)
    graph.add_node("governance", node_governance_check)
    graph.add_node("audit", node_audit)

    graph.set_entry_point("sanitize")
    graph.add_conditional_edges("sanitize", _should_stop_early, {
        "governance": "governance",
        "calculate": "calculate",
    })
    graph.add_edge("calculate", "llm_reasoning")
    graph.add_edge("llm_reasoning", "governance")
    graph.add_edge("governance", "audit")
    graph.add_edge("audit", END)

    return graph.compile()


_monitor_graph = None


def run_aml_monitor(transaction: Dict, client: Dict, pipeline_status: str = "ACTIVE") -> Dict:
    global _monitor_graph
    if _monitor_graph is None:
        _monitor_graph = build_monitor_graph()

    initial_state: AMLMonitorState = {
        "transaction": transaction,
        "client": client,
        "risk_score": 0.0,
        "flag": "CLEAN",
        "reasoning": "",
        "rag_context": "",
        "injection_detected": False,
        "injection_detail": "",
        "requires_human": False,
        "decision_id": None,
        "blocked": False,
        "block_reason": "",
        "pipeline_status": pipeline_status,
    }

    result = _monitor_graph.invoke(initial_state)
    return {
        "transaction_id": transaction.get("id"),
        "client_id": transaction.get("client_id"),
        "risk_score": result["risk_score"],
        "flag": result["flag"],
        "reasoning": result["reasoning"],
        "requires_human": result.get("requires_human", False),
        "decision_id": result.get("decision_id"),
        "injection_detected": result.get("injection_detected", False),
        "injection_detail": result.get("injection_detail", ""),
        "blocked": result.get("blocked", False),
        "block_reason": result.get("block_reason", ""),
    }
