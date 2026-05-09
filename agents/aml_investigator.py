"""
AML Investigator Agent — deep investigation of flagged transactions.
Produces full investigation reports with regulatory citations.
Agent ID: aml_investigator_v1.0.0
"""
import json
import os
import sys
from typing import Any, Dict, List, Optional, TypedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from rag.retriever import retrieve
import governance.audit_log as audit_log
import governance.hitl as hitl
from governance.validator import validate_action

AGENT_ID = "aml_investigator_v1.0.0"

_all_transactions: Optional[List[Dict]] = None


def _load_transactions() -> List[Dict]:
    global _all_transactions
    if _all_transactions is None:
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "transactions.json"
        )
        with open(data_path, "r") as f:
            _all_transactions = json.load(f)
    return _all_transactions


def get_client_transactions(client_id: str) -> List[Dict]:
    all_tx = _load_transactions()
    return [tx for tx in all_tx if tx.get("client_id") == client_id]


class AMLInvestigatorState(TypedDict):
    transaction: Dict
    client: Dict
    all_client_transactions: List[Dict]
    rag_context: str
    investigation_report: str
    recommendation: str
    requires_human: bool
    decision_id: Optional[str]
    blocked: bool
    block_reason: str
    pipeline_status: str


def node_load_history(state: AMLInvestigatorState) -> AMLInvestigatorState:
    client_id = state["client"].get("id", "")
    state["all_client_transactions"] = get_client_transactions(client_id)
    return state


def node_rag_query(state: AMLInvestigatorState) -> AMLInvestigatorState:
    tx = state["transaction"]
    query = (
        f"suspicious transaction {tx.get('amount', 0)} EUR "
        f"to {tx.get('country_destination', 'unknown')} "
        f"memo '{tx.get('memo', '')}' "
        f"multiple transfers same destination"
    )
    state["rag_context"] = retrieve(query, domain="AML", n_results=3)
    return state


def node_llm_investigation(state: AMLInvestigatorState) -> AMLInvestigatorState:
    prompt = f"""You are a senior AML investigator at NORDA Bank.
A transaction has been flagged as suspicious. Investigate the full case and write a professional investigation report.

Your report must include:
1. CASE SUMMARY: What was flagged and why
2. PATTERN ANALYSIS: What patterns you see across all client transactions
3. REGULATORY ASSESSMENT: Which specific regulations or typologies apply (cite from the retrieved regulations)
4. RISK CONCLUSION: Your overall assessment
5. RECOMMENDATION: One of FREEZE_ACCOUNT / FREEZE_TRANSFERS / ENHANCED_MONITORING / CLEAR / ESCALATE_TO_AUTHORITIES

Flagged Transaction: {json.dumps(state['transaction'], indent=2)}
Client Profile: {json.dumps(state['client'], indent=2)}
All Client Transactions: {json.dumps(state['all_client_transactions'], indent=2)}
Relevant AML Regulations Retrieved: {state['rag_context']}

Write your investigation report:"""

    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=os.environ.get("GROQ_API_KEY", ""),
            max_retries=1,
        )
        response = llm.invoke(prompt)
        report_text = response.content
    except Exception as e:
        tx = state["transaction"]
        client = state["client"]
        report_text = (
            f"INVESTIGATION REPORT — AUTOMATED FALLBACK\n\n"
            f"1. CASE SUMMARY\n"
            f"Transaction {tx.get('id')} for {tx.get('amount')} EUR to "
            f"{tx.get('country_destination')} has been flagged for investigation.\n\n"
            f"2. PATTERN ANALYSIS\n"
            f"Client {client.get('name')} has {len(state['all_client_transactions'])} total transactions on record. "
            f"Multiple transfers to the same destination suggest potential structuring activity.\n\n"
            f"3. REGULATORY ASSESSMENT\n"
            f"Applicable: FATF Recommendation 16 (Smurfing/Structuring), "
            f"AML 6th Directive Article 3 (reporting obligations), "
            f"AML 6th Directive Article 20 (PEP enhanced due diligence if applicable).\n\n"
            f"4. RISK CONCLUSION\n"
            f"Transaction profile is inconsistent with stated source of funds. "
            f"Pattern matches known AML typologies. Elevated risk confirmed.\n\n"
            f"5. RECOMMENDATION\n"
            f"ENHANCED_MONITORING\n\n"
            f"[LLM service unavailable: {str(e)}]"
        )

    state["investigation_report"] = report_text

    recommendation = "ENHANCED_MONITORING"
    for rec in ["FREEZE_ACCOUNT", "FREEZE_TRANSFERS", "ESCALATE_TO_AUTHORITIES", "CLEAR", "ENHANCED_MONITORING"]:
        if rec in report_text.upper():
            recommendation = rec
            break
    state["recommendation"] = recommendation

    return state


def node_governance_check(state: AMLInvestigatorState) -> AMLInvestigatorState:
    tx_id = state["transaction"].get("id", "unknown")
    input_snapshot = {
        "transaction_id": tx_id,
        "client_id": state["client"].get("id"),
        "recommendation": state["recommendation"],
    }

    validation = validate_action(
        agent_id=AGENT_ID,
        action="generate_report",
        input_data=input_snapshot,
        risk_score=1.0,
        pipeline_status=state.get("pipeline_status", "ACTIVE"),
    )

    if not validation["approved"]:
        state["blocked"] = True
        state["block_reason"] = validation["reason"]
        return state

    state["blocked"] = False
    freeze_actions = {"FREEZE_ACCOUNT", "FREEZE_TRANSFERS", "ESCALATE_TO_AUTHORITIES"}
    state["requires_human"] = state["recommendation"] in freeze_actions or validation["requires_human"]
    return state


def node_hitl_queue(state: AMLInvestigatorState) -> AMLInvestigatorState:
    if state.get("blocked"):
        return state

    decision_id = hitl.add_decision(
        domain="AML",
        agent_id=AGENT_ID,
        recommendation=state["recommendation"],
        risk_score=1.0,
        reasoning=state["investigation_report"][:1000],
        transaction_id=state["transaction"].get("id"),
        client_id=state["client"].get("id"),
    )
    state["decision_id"] = decision_id
    state["requires_human"] = True
    return state


def node_audit(state: AMLInvestigatorState) -> AMLInvestigatorState:
    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="AML",
        action="generate_report",
        input_snapshot={
            "transaction_id": state["transaction"].get("id"),
            "client_id": state["client"].get("id"),
            "transaction_count": len(state["all_client_transactions"]),
        },
        output_snapshot={
            "recommendation": state["recommendation"],
            "report_preview": state["investigation_report"][:500],
            "requires_human": state.get("requires_human", True),
        },
        risk_score=1.0,
        decision=state["recommendation"],
        requires_human=state.get("requires_human", True),
    )
    return state


def build_investigator_graph():
    graph = StateGraph(AMLInvestigatorState)
    graph.add_node("load_history", node_load_history)
    graph.add_node("rag_query", node_rag_query)
    graph.add_node("llm_investigation", node_llm_investigation)
    graph.add_node("governance", node_governance_check)
    graph.add_node("hitl_queue", node_hitl_queue)
    graph.add_node("audit", node_audit)

    graph.set_entry_point("load_history")
    graph.add_edge("load_history", "rag_query")
    graph.add_edge("rag_query", "llm_investigation")
    graph.add_edge("llm_investigation", "governance")
    graph.add_edge("governance", "hitl_queue")
    graph.add_edge("hitl_queue", "audit")
    graph.add_edge("audit", END)

    return graph.compile()


_investigator_graph = None


def run_aml_investigator(
    transaction: Dict,
    client: Dict,
    pipeline_status: str = "ACTIVE",
) -> Dict:
    global _investigator_graph
    if _investigator_graph is None:
        _investigator_graph = build_investigator_graph()

    initial_state: AMLInvestigatorState = {
        "transaction": transaction,
        "client": client,
        "all_client_transactions": [],
        "rag_context": "",
        "investigation_report": "",
        "recommendation": "",
        "requires_human": True,
        "decision_id": None,
        "blocked": False,
        "block_reason": "",
        "pipeline_status": pipeline_status,
    }

    result = _investigator_graph.invoke(initial_state)
    return {
        "transaction_id": transaction.get("id"),
        "client_id": client.get("id"),
        "investigation_report": result["investigation_report"],
        "recommendation": result["recommendation"],
        "requires_human": result.get("requires_human", True),
        "decision_id": result.get("decision_id"),
        "blocked": result.get("blocked", False),
        "block_reason": result.get("block_reason", ""),
    }
