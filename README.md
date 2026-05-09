# SENTINEL — Autonomous AI Compliance System
## HACK'N'BIZ 2026 | NORDA Bank Challenge

SENTINEL is an autonomous AI compliance operating system built for NORDA Bank, processing AML transaction monitoring and KYC client onboarding through a network of four specialized AI agents governed by a zero-trust validation layer, hash-chained audit trail, and mandatory human-in-the-loop controls. Every agent decision is validated, logged immutably, and exposed to a real-time operator dashboard where compliance officers can approve, reject, suspend, or modify any action — satisfying the EU AI Act Article 14 requirement for meaningful human oversight.

## Architecture

```
[Operator Dashboard — Streamlit]
         │
         ▼
[Governance Layer]
├── Validator (6-rule enforcement, Zero Trust)
├── Audit Log (SHA-256 hash-chained, tamper-evident)
└── HITL Queue (human approval for high-risk decisions)
         │
    ┌────┴────┐
    ▼         ▼
[AML Domain]  [KYC Domain]
├── AML Monitor    ├── KYC Collector
└── AML Investigator└── KYC Assessor
         │
    ┌────┴────┐
    ▼         ▼
[Tool Layer]
├── ChromaDB RAG (FATF, AML 6th Directive, KYC Policy, EU AI Act)
├── Prompt Injection Sanitizer
└── JSON Mock Data (10 transactions, 6 clients)
```

## Domains Covered

- **AML Transaction Monitoring** — real-time risk scoring, smurfing detection, PEP transaction alerts, investigation reports with regulatory citations
- **KYC Client Onboarding** — sanctions screening, PEP verification, risk tier assignment (LOW/MEDIUM/HIGH), policy-referenced assessments

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI Agents | LangGraph 0.2.28 | Stateful agent workflow orchestration |
| LLM | Gemini 2.0 Flash (langchain-google-genai) | Reasoning, report generation |
| Dashboard | Streamlit 1.39.0 | Operator control interface |
| Vector DB | ChromaDB 0.5.15 | RAG for compliance regulations |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Free local embeddings |
| API Layer | FastAPI 0.115.0 + uvicorn | REST API (JWT authenticated) |
| Auth | python-jose[cryptography] | JWT token validation |
| Validation | Pydantic 2.9.2 | Data schemas |
| Security | Custom sanitizer | Prompt injection detection |

## Installation

### Prerequisites
- Python 3.11+
- Git

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/sentinel-aml
cd sentinel-aml
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
SECRET_KEY=sentinel_secret_jwt_key_2026
```

Get your free Gemini API key at: https://aistudio.google.com/app/apikey

### Run

```bash
python main.py
```

This will:
1. Check your API key
2. Automatically run RAG setup (first time only — loads compliance documents into ChromaDB)
3. Launch the Streamlit dashboard at http://localhost:8501

## Security Features

| Feature | Implementation |
|---------|---------------|
| **Prompt Injection Protection** | `security/sanitizer.py` — 12 pattern blocklist, case-insensitive matching, raises `PromptInjectionDetected` exception before any LLM call |
| **Hash-Chained Audit Log** | `governance/audit_log.py` — SHA-256 chain, each entry includes previous hash, `verify_chain_integrity()` detects any tampering |
| **Human-in-the-Loop (HITL)** | `governance/hitl.py` — all risk_score > 0.75 decisions queue for operator Approve/Reject/Suspend/Modify |
| **Agent Isolation** | Agents never import each other — all inter-agent communication via governance layer only |
| **Zero Trust** | `governance/validator.py` — every action validated against 6 rules: agent auth, action whitelist, input sanitization, risk threshold, duplicate detection, pipeline status |
| **No Plain-text Secrets** | All secrets via `.env` + `python-dotenv`, `.env` in `.gitignore` |

## STRIDE Threat Model

| Threat | Vector | Mitigation |
|--------|--------|-----------|
| **Spoofing** | Rogue agent pretending to be AML Monitor | Agent ID whitelist in validator (Rule 1) |
| **Tampering** | Modifying audit log entries post-hoc | SHA-256 hash chain — tampering breaks verification |
| **Repudiation** | Denying a decision was made | Immutable audit log with exact input/output snapshots |
| **Information Disclosure** | Leaking client data via LLM prompt | Input sanitization before LLM, no raw PII in logs |
| **Denial of Service** | Flooding agents with duplicate requests | Duplicate action detection within 60s window (Rule 5) |
| **Elevation of Privilege** | Prompt injection to bypass compliance rules | Sanitizer blocks injection before governance check (Rule 3) |

## Hackathon Requirements Coverage

| Requirement | Implementation |
|------------|---------------|
| FR1: 2+ specialized AI agents | 4 agents: AML Monitor, AML Investigator, KYC Collector, KYC Assessor |
| FR2: Governance layer | `governance/` — validator, audit log, HITL queue |
| FR3: Human operator dashboard | `dashboard/app.py` — 3 tabs, full control panel |
| Security: Component authentication | `validator.py` Rule 1: agent ID whitelist |
| Security: No plain-text secrets | `.env` + `python-dotenv` + `.gitignore` |
| Security: Signed chained logs | SHA-256 hash-chained `audit_log.py` |
| Security: Prompt injection protection | `security/sanitizer.py` — 12 patterns |
| Security: Agent isolation | No cross-agent imports, governance-only communication |
| Security: Zero Trust | All 6 validator rules on every action |
| Auditability: Reproducible decisions | Input snapshot + agent version + LLM model logged per entry |
| Explainability: Non-technical rationale | LLM generates plain-language reasoning per decision |
| Human Control: Suspend/Cancel/Modify | HITL panel: Approve / Reject / Suspend / Modify & Approve |

## Demo Scenarios

1. **Smurfing Detection** — Run AML scan: TX-002/003/004 (Karim Benali, Malta) score >0.7, investigator cites FATF Rec 16
2. **Prompt Injection Blocked** — TX-006 memo triggers red alert, score=1.0, goes to HITL, LLM never called
3. **KYC HIGH RISK PEP** — Submit Viktor Petrov form (Russian, offshore_company, PEP=true) → HIGH tier, human approval required
4. **Audit Chain Verification** — Audit Log tab → "Verify Chain Integrity" → all green checkmarks

## Team

**HACK'N'BIZ 2026** — Fortum Junior Entreprise × NORDA Bank Challenge
