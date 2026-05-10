"""
Legal Review Agent — function-based.
Analyses legal documents for regulatory compliance risks.
Agent ID: legal_reviewer_agent_v1.0.0
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from typing import Dict, List
from langchain_groq import ChatGroq
import governance.audit_log as audit_log
import governance.hitl as hitl

AGENT_ID = "legal_reviewer_agent_v1.0.0"

RISK_SCORES = {"LOW": 20, "MEDIUM": 55, "HIGH": 82}

REGULATORY_FRAMEWORK = {
    "loan_agreement": ["Basel IV / CRR III", "IFRS 9", "EBA Loan Origination Guidelines"],
    "dpa":            ["GDPR Art.28", "GDPR Art.44-49", "EDPB SCCs Guidelines"],
    "compliance_doc": ["MiFID II Art.25", "ESMA Suitability Guidelines", "PRIIPs"],
    "ict_contract":   ["DORA Art.28-30", "DORA RTS on ICT Risk", "EBA Outsourcing Guidelines"],
    "internal_policy":["Basel IV Output Floor", "CRR III", "EBA Internal Governance"],
}


def _get_llm_analysis(document: Dict) -> str:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        return _fallback_analysis(document)
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_key, max_retries=1)
        frameworks = ", ".join(REGULATORY_FRAMEWORK.get(document.get("type",""), ["General banking law"]))
        prompt = f"""You are a senior legal counsel at NORDA Bank specialising in financial regulation.

Review this legal document and provide a structured risk assessment.

DOCUMENT DETAILS:
Title: {document.get('title')}
Type: {document.get('type')}
Counterparty: {document.get('counterparty')}
Jurisdiction: {document.get('jurisdiction')}
Risk Level: {document.get('risk_level')}
Pages: {document.get('pages')}
Date: {document.get('date')}
Regulatory tags: {', '.join(document.get('regulatory_tags', []))}

CONTENT SUMMARY:
{document.get('content_summary')}

APPLICABLE FRAMEWORKS: {frameworks}

Provide a 5-part analysis:
1. KEY LEGAL RISKS: Top 3 legal risks in this document (be specific, cite clauses if mentioned)
2. REGULATORY COMPLIANCE ISSUES: Non-compliance or gaps vs {frameworks}
3. CLAUSES REQUIRING LAWYER REVIEW: Specific provisions that need senior legal sign-off
4. RISK RATING: Confirm or revise the {document.get('risk_level')} rating with justification
5. RECOMMENDED ACTIONS: Numbered list of next steps (negotiation points, amendments needed, approvals required)

Be precise and actionable. This is for a compliance officer making decisions."""
        return llm.invoke(prompt).content
    except Exception:
        return _fallback_analysis(document)


def _fallback_analysis(document: Dict) -> str:
    risk = document.get("risk_level", "MEDIUM")
    dtype = document.get("type", "document").replace("_", " ").title()
    tags = ", ".join(document.get("regulatory_tags", []))
    actions = {
        "HIGH":   "Escalate to General Counsel. Do not execute without senior legal sign-off. Request external counsel review.",
        "MEDIUM": "Review open clauses with legal team. Obtain compliance sign-off before execution.",
        "LOW":    "Standard review process. Compliance officer approval sufficient.",
    }.get(risk, "Review required.")
    return (
        f"**{dtype} — {risk} Risk** | Counterparty: {document.get('counterparty')} | "
        f"Jurisdiction: {document.get('jurisdiction')}\n\n"
        f"Regulatory frameworks: {tags}\n\n"
        f"**Recommended action:** {actions}"
    )


def run_legal_reviewer_agent(document: Dict) -> Dict:
    """Analyse a legal document for regulatory compliance and risk."""
    doc_id    = document.get("id", "DOC-unknown")
    risk_str  = document.get("risk_level", "MEDIUM")
    risk_score = RISK_SCORES.get(risk_str, 55)
    requires_human = risk_str == "HIGH" or document.get("status") == "requires_negotiation"

    analysis  = _get_llm_analysis(document)

    decision_id = None
    if requires_human:
        decision_id = hitl.add_decision(
            agent_id=AGENT_ID,
            domain="LEGAL",
            transaction_id=doc_id,
            client_id=document.get("counterparty", "Unknown"),
            recommendation=f"LEGAL REVIEW — {document.get('title')}: {risk_str} risk, requires legal sign-off",
            risk_score=risk_score / 100,
            reasoning=analysis,
        )

    audit_log.log_decision(
        agent_id=AGENT_ID,
        domain="LEGAL",
        action="review_legal_document",
        input_snapshot={"doc_id": doc_id, "type": document.get("type"), "risk_level": risk_str,
                        "counterparty": document.get("counterparty")},
        output_snapshot={"risk_score": risk_score, "requires_human": requires_human,
                         "analysis_preview": analysis[:300]},
        risk_score=risk_score / 100,
        decision="CRITICAL_ESCALATION" if risk_str == "HIGH" else "WAITING_HUMAN_APPROVAL" if requires_human else "MONITOR_ONLY",
        requires_human=requires_human,
    )

    return {
        "doc_id":         doc_id,
        "title":          document.get("title"),
        "type":           document.get("type"),
        "risk_level":     risk_str,
        "risk_score":     risk_score,
        "requires_human": requires_human,
        "decision_id":    decision_id,
        "analysis":       analysis,
        "agent_id":       AGENT_ID,
        "frameworks":     REGULATORY_FRAMEWORK.get(document.get("type",""), []),
        "status":         document.get("status"),
    }
