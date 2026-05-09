"""
SENTINEL Operator Dashboard — Bloomberg-terminal-style enterprise UI.
All agent calls are JWT-authenticated via FastAPI. Role-based access control enforced.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="SENTINEL — NORDA Bank",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Bloomberg terminal meets modern fintech
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer { visibility: hidden; }
.stApp { background: #060d1a; color: #c8d8e8; }
.stApp > header { background: transparent; }
.block-container { padding: 1.5rem 2rem; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #060d1a 100%) !important;
    border-right: 1px solid rgba(0,212,170,0.12);
}
[data-testid="stSidebar"] * { color: #c8d8e8 !important; }
[data-testid="stSidebar"] .stRadio label {
    padding: 8px 12px; border-radius: 8px; cursor: pointer;
    transition: all 0.15s; border: 1px solid transparent;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(0,212,170,0.06); border-color: rgba(0,212,170,0.15);
}

/* ── Cards ── */
.s-card {
    background: rgba(10,22,40,0.8);
    border: 1px solid rgba(0,212,170,0.12);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 14px;
    backdrop-filter: blur(10px);
    transition: border-color 0.2s;
}
.s-card:hover { border-color: rgba(0,212,170,0.25); }

/* ── Section headers ── */
.s-header {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #00d4aa;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(0,212,170,0.15);
}

/* ── Risk badges ── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    font-family: 'JetBrains Mono', monospace;
}
.badge-high    { background: rgba(255,68,68,0.15);  color:#ff6666; border:1px solid rgba(255,68,68,0.3); }
.badge-medium  { background: rgba(255,153,0,0.15);  color:#ffaa33; border:1px solid rgba(255,153,0,0.3); }
.badge-low     { background: rgba(0,170,85,0.15);   color:#00cc66; border:1px solid rgba(0,170,85,0.3); }
.badge-clean   { background: rgba(0,170,85,0.1);    color:#00cc66; border:1px solid rgba(0,170,85,0.2); }
.badge-suspicious { background: rgba(255,153,0,0.1); color:#ffaa33; border:1px solid rgba(255,153,0,0.2); }
.badge-blocked { background: rgba(255,68,68,0.1);   color:#ff6666; border:1px solid rgba(255,68,68,0.2); }

/* ── INJECTION ALERT ── */
.inject-alert {
    background: linear-gradient(135deg, rgba(80,0,0,0.6), rgba(40,0,0,0.4));
    border: 1px solid rgba(255,68,68,0.5);
    border-left: 4px solid #ff4444;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 10px 0;
    animation: alertPulse 2s ease-in-out infinite;
}
@keyframes alertPulse { 0%,100%{border-left-color:#ff4444} 50%{border-left-color:#ff8888} }
.inject-alert .alert-title { color:#ff6666; font-weight:700; font-size:14px; margin-bottom:6px; }
.inject-alert .alert-body  { color:#cc8888; font-size:13px; }

/* ── HITL panel ── */
.hitl-panel {
    background: rgba(0,212,170,0.04);
    border: 1px solid rgba(0,212,170,0.2);
    border-radius: 12px;
    padding: 18px;
    margin-top: 14px;
}

/* ── Hash display ── */
.hash-mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #00d4aa;
    background: rgba(0,212,170,0.06);
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid rgba(0,212,170,0.15);
}

/* ── JWT box ── */
.jwt-display {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #00d4aa;
    background: rgba(0,10,20,0.6);
    border: 1px solid rgba(0,212,170,0.2);
    border-radius: 8px;
    padding: 10px;
    word-break: break-all;
    line-height: 1.6;
}

/* ── Role badge ── */
.role-admin   { color:#ff9900; font-weight:700; }
.role-co      { color:#00d4aa; font-weight:700; }
.role-analyst { color:#7799bb; font-weight:700; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: rgba(10,22,40,0.7);
    border: 1px solid rgba(0,212,170,0.1);
    border-radius: 12px;
    padding: 16px !important;
}
[data-testid="metric-container"] label { color: #5a7a9a !important; font-size: 11px !important; letter-spacing: 0.1em; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #00d4aa !important; font-family: 'JetBrains Mono', monospace !important; }

/* ── Buttons ── */
.stButton > button {
    background: rgba(0,212,170,0.08) !important;
    border: 1px solid rgba(0,212,170,0.25) !important;
    color: #00d4aa !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(0,212,170,0.15) !important;
    border-color: #00d4aa !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(0,212,170,0.15) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(0,212,170,0.25), rgba(0,150,255,0.15)) !important;
    border-color: #00d4aa !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid rgba(0,212,170,0.1) !important; border-radius: 10px !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(10,22,40,0.6) !important;
    border: 1px solid rgba(0,212,170,0.1) !important;
    border-radius: 8px !important;
    color: #8899aa !important;
}

/* ── Status dot ── */
.live-dot { display:inline-block; width:8px; height:8px; background:#00d4aa; border-radius:50%; margin-right:6px; animation:blink 2s infinite; }
@keyframes blink { 0%,100%{opacity:1;box-shadow:0 0 4px #00d4aa} 50%{opacity:0.3;box-shadow:none} }

/* ── Chat ── */
.chat-bubble-user {
    background: rgba(0,150,255,0.1);
    border: 1px solid rgba(0,150,255,0.2);
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #d0e8ff;
    font-size: 14px;
    margin-left: 40px;
}
.chat-bubble-bot {
    background: rgba(0,212,170,0.06);
    border: 1px solid rgba(0,212,170,0.15);
    border-radius: 12px 12px 12px 4px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #c8d8e8;
    font-size: 14px;
    margin-right: 40px;
}
.chat-label { font-size: 10px; color: #4a6a8a; margin-bottom: 4px; letter-spacing: 0.1em; }

/* ── Scrollable chat area ── */
.chat-area {
    max-height: 420px;
    overflow-y: auto;
    padding: 8px;
    scrollbar-width: thin;
    scrollbar-color: rgba(0,212,170,0.3) transparent;
}

/* ── Page title ── */
.page-title {
    font-size: 22px;
    font-weight: 700;
    color: #e0f0ff;
    margin-bottom: 4px;
}
.page-sub {
    font-size: 12px;
    color: #4a6a8a;
    margin-bottom: 24px;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════
@st.cache_data
def load_transactions():
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "transactions.json")
    return json.load(open(p))

@st.cache_data
def load_clients():
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "clients.json")
    return json.load(open(p))

TRANSACTIONS = load_transactions()
CLIENTS = load_clients()
CLIENT_MAP = {c["id"]: c for c in CLIENTS}

from dashboard.api_client import (
    login, health, scan_transaction, investigate_transaction, assess_client,
    get_pending, approve, reject, suspend_decision, modify_and_approve,
    get_audit_log, verify_chain, APIError,
)
from dashboard.api_client import API_BASE
import requests as _requests

def chat_api(token: str, messages: list, tutorial: bool = False) -> str:
    try:
        r = _requests.post(
            f"{API_BASE}/api/chat/message",
            json={"messages": messages, "tutorial": tutorial},
            headers={"Authorization": f"Bearer {token}"},
            timeout=40,
        )
        if not r.ok:
            return f"❌ Chat error: {r.json().get('detail', r.text)}"
        return r.json()["reply"]
    except Exception as e:
        return f"❌ AI Assistant unavailable: {e}"


# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
_defaults = {
    "jwt_token": None, "operator_name": None, "operator_role": None,
    "scan_results": {}, "investigation_results": {}, "kyc_result": None,
    "pipeline_status": "ACTIVE", "chat_history": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auto-login from URL token (set by index.html) ──────────────────
if not st.session_state.jwt_token:
    params = st.query_params
    if "token" in params:
        raw = params["token"]
        try:
            from api.auth import verify_token_data
            claims = verify_token_data(raw)
            st.session_state.jwt_token = raw
            st.session_state.operator_name = claims.get("full_name", claims["sub"])
            st.session_state.operator_role = claims.get("role", "analyst")
            st.query_params.clear()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════
# LOGIN GATE (fallback if not auto-logged via URL token)
# ══════════════════════════════════════════════════════════════════════
def show_login():
    st.markdown("""
    <div style='text-align:center;padding:60px 0 30px'>
      <div style='font-size:11px;letter-spacing:.3em;color:#3a5a7a;text-transform:uppercase;margin-bottom:10px'>🏦 NORDA Bank</div>
      <div style='font-size:44px;font-weight:900;color:#00d4aa;letter-spacing:.15em;text-shadow:0 0 40px rgba(0,212,170,0.4)'>SENTINEL</div>
      <div style='color:#4a6a8a;font-size:13px;margin-top:6px'>Autonomous AI Compliance System</div>
    </div>
    """, unsafe_allow_html=True)

    col, mid, col2 = st.columns([1, 1.2, 1])
    with mid:
        if not health():
            st.error("⚠️ API server unreachable — run `python main.py` first.")
            return

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="operator")
            password = st.text_input("Password", type="password", placeholder="••••••••••")
            robot = st.checkbox("✅ I am not a robot")
            submitted = st.form_submit_button("🔐 Authenticate", use_container_width=True, type="primary")

        if submitted:
            if not robot:
                st.error("Please confirm you are not a robot.")
            elif not username or not password:
                st.error("Enter username and password.")
            else:
                with st.spinner("Authenticating…"):
                    try:
                        data = login(username, password)
                        st.session_state.jwt_token = data["access_token"]
                        st.session_state.operator_name = data["operator"]
                        st.session_state.operator_role = data["role"]
                        st.rerun()
                    except APIError as e:
                        st.error(f"Authentication failed: {e.detail}")
                    except Exception as e:
                        st.error(f"Cannot reach API: {e}")

        st.markdown("""
        <div style='background:rgba(0,212,170,0.04);border:1px solid rgba(0,212,170,0.1);border-radius:10px;padding:14px;margin-top:16px;font-size:12px;color:#4a6a8a'>
        <b style='color:#5a8a7a'>Demo credentials</b><br><br>
        <code style='color:#8ab'>operator</code> / <code style='color:#8ab'>sentinel2026</code> — Compliance Officer<br>
        <code style='color:#8ab'>analyst</code> / <code style='color:#8ab'>analyst2026</code> — Risk Analyst (read-only)<br>
        <code style='color:#8ab'>admin</code> / <code style='color:#8ab'>norda_admin_2026</code> — Admin
        </div>
        """, unsafe_allow_html=True)


if not st.session_state.jwt_token:
    show_login()
    st.stop()

TOKEN = st.session_state.jwt_token
ROLE  = st.session_state.operator_role or "analyst"
CAN_APPROVE = ROLE in ("admin", "compliance_officer")


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding:8px 0 4px'>
      <div style='font-size:10px;color:#3a5a7a;letter-spacing:.25em;text-transform:uppercase'>🏦 NORDA Bank</div>
      <div style='font-size:26px;font-weight:900;color:#00d4aa;letter-spacing:.12em'>SENTINEL</div>
      <div style='font-size:10px;color:#3a5a7a;margin-top:2px'>AI Compliance System v1.0</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    nav = st.radio("", ["🔍 AML Monitor", "📋 KYC Review", "🔐 Audit Log", "💬 AI Assistant"],
                   label_visibility="collapsed")
    st.divider()

    # System status
    try:
        pending_count = len(get_pending(TOKEN))
    except Exception:
        pending_count = 0

    st.markdown(f'<span class="live-dot"></span>**OPERATIONAL**', unsafe_allow_html=True)
    if pending_count:
        st.warning(f"⚠️ {pending_count} pending")
    else:
        st.success("✅ Queue clear")

    # Pipeline toggle
    if st.session_state.pipeline_status == "ACTIVE":
        if st.button("⏸ Suspend Pipeline", use_container_width=True):
            st.session_state.pipeline_status = "SUSPENDED"
            st.rerun()
    else:
        if st.button("▶ Resume Pipeline", use_container_width=True):
            st.session_state.pipeline_status = "ACTIVE"
            st.rerun()

    pip_color = "#00d4aa" if st.session_state.pipeline_status == "ACTIVE" else "#ff4444"
    st.markdown(f"<div style='font-size:11px;color:{pip_color};font-weight:600;margin-top:4px'>● {st.session_state.pipeline_status}</div>",
                unsafe_allow_html=True)

    st.divider()

    # User info
    role_class = {"admin": "role-admin", "compliance_officer": "role-co", "analyst": "role-analyst"}.get(ROLE, "role-analyst")
    role_label = {"admin": "Admin", "compliance_officer": "Compliance Officer", "analyst": "Risk Analyst"}.get(ROLE, ROLE)
    st.markdown(f"""
    <div style='font-size:13px;font-weight:600;color:#c8d8e8'>👤 {st.session_state.operator_name}</div>
    <div class='{role_class}' style='font-size:11px;margin-top:2px'>{role_label}</div>
    """, unsafe_allow_html=True)

    with st.expander("🔑 Active JWT"):
        st.markdown(f'<div class="jwt-display">{TOKEN[:60]}…</div>', unsafe_allow_html=True)
        st.caption("Sent as `Authorization: Bearer` on every API call")

    if st.button("🚪 Logout", use_container_width=True):
        for k in _defaults:
            st.session_state[k] = _defaults[k]
        st.rerun()

    st.divider()
    st.caption("HACK'N'BIZ 2026\nFortum Junior Entreprise")


# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════
def score_badge(score: float) -> str:
    if score >= 0.75:
        return f'<span class="badge badge-high">⬆ {score:.2f} HIGH</span>'
    if score >= 0.4:
        return f'<span class="badge badge-medium">◆ {score:.2f} MED</span>'
    return f'<span class="badge badge-low">✓ {score:.2f} LOW</span>'

def flag_badge(flag: str) -> str:
    c = {"SUSPICIOUS": "badge-suspicious", "INJECTION_DETECTED": "badge-blocked",
         "BLOCKED": "badge-blocked", "CLEAN": "badge-clean"}.get(flag, "badge-low")
    return f'<span class="badge {c}">{flag}</span>'

def tier_badge(tier: str) -> str:
    c = {"HIGH": "badge-high", "MEDIUM": "badge-medium", "LOW": "badge-low",
         "REJECTED": "badge-blocked"}.get(tier, "badge-low")
    return f'<span class="badge {c} " style="font-size:16px;padding:6px 20px">{tier}</span>'

def hitl_panel(decision_id: str, prefix: str):
    if not CAN_APPROVE:
        st.markdown("""<div style='background:rgba(255,153,0,0.06);border:1px solid rgba(255,153,0,0.2);border-radius:8px;padding:12px;font-size:12px;color:#aa7733'>
        ⚠️ Your role (<b>analyst</b>) cannot approve or reject decisions. Requires Compliance Officer or Admin.
        </div>""", unsafe_allow_html=True)
        return
    st.markdown('<div class="hitl-panel">', unsafe_allow_html=True)
    st.markdown("**🔐 Human Decision Required**")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✅ Approve", key=f"{prefix}_ap_{decision_id}"):
            try: approve(TOKEN, decision_id); st.success("Approved.")
            except APIError as e: st.error(e.detail)
    with c2:
        if st.button("❌ Reject", key=f"{prefix}_rj_{decision_id}"):
            try: reject(TOKEN, decision_id); st.error("Rejected.")
            except APIError as e: st.error(e.detail)
    with c3:
        if st.button("⏸ Suspend", key=f"{prefix}_su_{decision_id}"):
            try: suspend_decision(TOKEN, decision_id); st.warning("Suspended.")
            except APIError as e: st.error(e.detail)
    mod = st.text_input("Modify & Approve:", key=f"{prefix}_mod_{decision_id}",
                        placeholder="Enter operator modification…")
    if st.button("✏️ Modify & Approve", key=f"{prefix}_ma_{decision_id}"):
        if mod:
            try: modify_and_approve(TOKEN, decision_id, mod); st.success(f"Modified: {mod}")
            except APIError as e: st.error(e.detail)
        else:
            st.warning("Enter a modification first.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# ── SECTION 1: AML MONITOR ──────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
if nav == "🔍 AML Monitor":
    st.markdown('<div class="page-title">🔍 AML Transaction Monitor</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Real-time risk scoring · Smurfing detection · Injection protection</div>', unsafe_allow_html=True)

    if st.session_state.pipeline_status == "SUSPENDED":
        st.error("🔴 **PIPELINE SUSPENDED** — All agent actions are halted by operator command.")

    col_left, col_right = st.columns([6, 4], gap="large")

    with col_left:
        st.markdown('<div class="s-header">Transaction Feed</div>', unsafe_allow_html=True)

        rows = []
        for tx in TRANSACTIONS:
            cl = CLIENT_MAP.get(tx["client_id"], {})
            r = st.session_state.scan_results.get(tx["id"])
            rows.append({
                "TX ID": tx["id"],
                "Client": cl.get("name", tx["client_id"]),
                "Amount": f"€{tx['amount']:,.0f}",
                "Destination": tx["country_destination"],
                "Memo": tx["memo"][:38] + ("…" if len(tx["memo"]) > 38 else ""),
                "Risk": f"{r['risk_score']:.2f}" if r else "—",
                "Flag": r["flag"] if r else "—",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True,
                     column_config={"Risk": st.column_config.NumberColumn(format="%.2f"),
                                    "Amount": st.column_config.TextColumn()})

        if st.button("🚀 Run AML Scan on All Transactions", type="primary", use_container_width=True):
            prog = st.progress(0, text="Initializing AML scan…")
            ph = st.empty()
            for i, tx in enumerate(TRANSACTIONS):
                cl = CLIENT_MAP.get(tx["client_id"], {})
                ph.markdown(f'<div style="font-size:13px;color:#5a8a7a">⟳ Scanning <b>{tx["id"]}</b> — {cl.get("name","")} ({tx["amount"]} EUR → {tx["country_destination"]})</div>', unsafe_allow_html=True)
                try:
                    result = scan_transaction(TOKEN, tx, cl, st.session_state.pipeline_status)
                    st.session_state.scan_results[tx["id"]] = result
                except APIError as e:
                    if e.status_code == 401:
                        st.error("Session expired."); st.session_state.jwt_token = None; st.rerun()
                prog.progress((i + 1) / len(TRANSACTIONS), text=f"Scanned {i+1}/{len(TRANSACTIONS)}")
                time.sleep(0.05)
            ph.success(f"✅ Scan complete — {len(TRANSACTIONS)} transactions processed.")

    with col_right:
        st.markdown('<div class="s-header">Flagged Cases</div>', unsafe_allow_html=True)

        if not st.session_state.scan_results:
            st.markdown("""<div class="s-card" style="text-align:center;color:#3a5a7a;padding:32px">
            Run a scan to see flagged transactions</div>""", unsafe_allow_html=True)
        else:
            flagged = sorted(
                [r for r in st.session_state.scan_results.values()
                 if r.get("risk_score", 0) > 0.4 or r.get("injection_detected")],
                key=lambda x: x.get("risk_score", 0), reverse=True,
            )
            if not flagged:
                st.success("✅ No suspicious transactions detected.")

            for result in flagged:
                tx_id = result["transaction_id"]
                tx = next((t for t in TRANSACTIONS if t["id"] == tx_id), {})
                cl = CLIENT_MAP.get(result["client_id"], {})
                score = result.get("risk_score", 0)

                if result.get("injection_detected"):
                    st.markdown(f"""<div class="inject-alert">
                    <div class="alert-title">🚨 PROMPT INJECTION BLOCKED</div>
                    <div class="alert-body">
                    <b>{tx_id}</b> — {cl.get("name","Unknown")}<br>
                    Pattern: <code>ignore previous instructions</code><br>
                    SENTINEL rejected this input before LLM processing.<br>
                    Risk Score: <b>1.00</b> → Queued for human review.
                    </div></div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="s-card">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                      <div><b style="color:#e0f0ff">{tx_id}</b> <span style="color:#4a6a8a;font-size:12px">— {cl.get("name","")}</span></div>
                      {score_badge(score)}
                    </div>
                    <div style="margin-top:8px">{flag_badge(result.get("flag",""))}</div>
                    </div>""", unsafe_allow_html=True)

                with st.expander(f"🔎 Reasoning — {tx_id}"):
                    st.markdown(f'<div style="color:#8899aa;font-size:13px;line-height:1.6">{result.get("reasoning","—")}</div>', unsafe_allow_html=True)
                    if result.get("requires_human"):
                        st.info("⚠️ Queued for human review (HITL)")

                if not result.get("injection_detected"):
                    if st.button(f"🔬 Investigate {tx_id}", key=f"inv_{tx_id}"):
                        with st.status(f"Investigating {tx_id}…", expanded=True) as s:
                            st.write("Loading client transaction history…")
                            time.sleep(0.3)
                            st.write("Querying AML regulation database (ChromaDB)…")
                            time.sleep(0.3)
                            st.write("Running Investigator Agent (Groq/Llama-3.3-70b)…")
                            try:
                                inv = investigate_transaction(TOKEN, tx, cl, st.session_state.pipeline_status)
                                st.session_state.investigation_results[tx_id] = inv
                                s.update(label="Investigation complete", state="complete")
                            except APIError as e:
                                s.update(label="Investigation failed", state="error")
                                st.error(e.detail)

                if tx_id in st.session_state.investigation_results:
                    inv = st.session_state.investigation_results[tx_id]
                    with st.expander("📄 Investigation Report", expanded=True):
                        rec = inv.get("recommendation", "UNKNOWN")
                        rec_color = {"FREEZE_ACCOUNT":"#ff4444","FREEZE_TRANSFERS":"#ff6600",
                                     "ESCALATE_TO_AUTHORITIES":"#ff0000",
                                     "ENHANCED_MONITORING":"#ff9900","CLEAR":"#00cc66"}.get(rec,"#888")
                        st.markdown(f"**Recommendation:** <span style='color:{rec_color};font-weight:700;font-size:15px'>{rec}</span>",
                                    unsafe_allow_html=True)
                        st.text_area("", value=inv.get("investigation_report",""), height=220,
                                     key=f"rep_{tx_id}", disabled=True, label_visibility="collapsed")
                        if inv.get("requires_human") and inv.get("decision_id"):
                            hitl_panel(inv["decision_id"], f"aml_{tx_id}")

                st.divider()


# ══════════════════════════════════════════════════════════════════════
# ── SECTION 2: KYC REVIEW ───────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
elif nav == "📋 KYC Review":
    st.markdown('<div class="page-title">📋 KYC Client Onboarding</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Sanctions screening · PEP verification · Risk tier assignment</div>', unsafe_allow_html=True)

    if st.session_state.pipeline_status == "SUSPENDED":
        st.error("🔴 **PIPELINE SUSPENDED**")

    NATIONALITIES = ["French","German","British","Spanish","Italian","Belgian","Dutch","Swedish",
                     "Polish","Romanian","Algerian","Moroccan","Tunisian","Russian","Chinese",
                     "Iranian","North Korean","Emirati","Saudi","Nigerian","Pakistani","American","Other"]

    col_form, col_res = st.columns([5, 5], gap="large")

    with col_form:
        st.markdown('<div class="s-header">Onboarding Form</div>', unsafe_allow_html=True)
        with st.form("kyc_form"):
            name   = st.text_input("Full Name", placeholder="e.g. Viktor Petrov")
            nat    = st.selectbox("Nationality", NATIONALITIES)
            res    = st.text_input("Country of Residence", placeholder="e.g. France")
            acc    = st.selectbox("Account Type", ["retail","corporate","private_banking"])
            sof    = st.selectbox("Source of Funds", ["salary","business","investment_portfolio","offshore_company","other"])
            pep    = st.checkbox("Politically Exposed Person (PEP)")
            biz    = st.text_area("Business Description", placeholder="Corporate/private banking only…") if acc != "retail" else ""
            submit = st.form_submit_button("🚀 Run KYC Assessment", type="primary", use_container_width=True)

        if submit:
            st.session_state.kyc_result = None
            form = {"name":name,"nationality":nat,"country_of_residence":res,
                    "account_type":acc,"source_of_funds":sof,"pep_declared":pep,"business_description":biz}
            with st.status("Running KYC Pipeline…", expanded=True) as s:
                st.write("⟳ Step 1 — Sanitizing & structuring data…"); time.sleep(0.4)
                st.write("⟳ Step 2 — Sanctions screening…"); time.sleep(0.4)
                st.write("⟳ Step 3 — PEP verification…"); time.sleep(0.3)
                st.write("⟳ Step 4 — Risk tier assessment (Groq/Llama)…")
                try:
                    result = assess_client(TOKEN, form, st.session_state.pipeline_status)
                    st.session_state.kyc_result = result
                    s.update(label="KYC Assessment Complete ✓", state="complete")
                except APIError as e:
                    s.update(label="Assessment Failed", state="error")
                    if e.status_code == 401:
                        st.session_state.jwt_token = None; st.rerun()
                    st.error(e.detail)

    with col_res:
        st.markdown('<div class="s-header">Assessment Results</div>', unsafe_allow_html=True)
        r = st.session_state.kyc_result

        if r is None:
            st.markdown('<div class="s-card" style="text-align:center;color:#3a5a7a;padding:32px">Submit the form to run the pipeline</div>', unsafe_allow_html=True)
        elif r.get("injection_detected"):
            st.markdown('<div class="inject-alert"><div class="alert-title">🚨 INJECTION BLOCKED</div><div class="alert-body">Malicious input detected in form data.</div></div>', unsafe_allow_html=True)
        elif r.get("rejected"):
            st.error(f"🚫 **ONBOARDING REJECTED**\n\n{r.get('reject_reason','')}")
        else:
            sanctions = r.get("sanctions_result", {})
            pep_r     = r.get("pep_result", {})

            st.markdown(f"{'🚫' if sanctions.get('sanctioned') else '✅'} **Sanctions** — {sanctions.get('reason','N/A')}")
            st.markdown(f"{'⚠️' if pep_r.get('pep_confirmed') else '✅'} **PEP** — {pep_r.get('reason','N/A')}")

            if r.get("llm_summary"):
                with st.expander("Collector Agent Summary"):
                    st.markdown(f'<div style="color:#8899aa;font-size:13px;line-height:1.6">{r["llm_summary"]}</div>', unsafe_allow_html=True)

            st.divider()
            tier = r.get("risk_tier","LOW")
            st.markdown(f'<div style="text-align:center;padding:20px 0">{tier_badge(tier)}</div>', unsafe_allow_html=True)

            dec = r.get("decision","APPROVE")
            dec_color = "#ff4444" if dec in ("REJECT","ESCALATE") else "#ff9900" if dec == "APPROVE_WITH_CONDITIONS" else "#00cc66"
            st.markdown(f"**Decision:** <span style='color:{dec_color};font-weight:700'>{dec}</span>", unsafe_allow_html=True)

            with st.expander("📄 Full Risk Assessment", expanded=True):
                st.text_area("", value=r.get("llm_assessment",""), height=260,
                             disabled=True, key="kyc_txt", label_visibility="collapsed")

            if r.get("requires_human") and r.get("decision_id"):
                hitl_panel(r["decision_id"], "kyc")


# ══════════════════════════════════════════════════════════════════════
# ── SECTION 3: AUDIT LOG ────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
elif nav == "🔐 Audit Log":
    st.markdown('<div class="page-title">🔐 Immutable Audit Log</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">SHA-256 hash-chained · Every decision traceable · Tamper-evident</div>', unsafe_allow_html=True)

    try:
        entries = get_audit_log(TOKEN)
    except APIError as e:
        st.error(f"Failed to load audit log: {e.detail}"); entries = []

    approved = sum(1 for e in entries if e.get("decision") in ("CLEAN","COLLECTED","APPROVE","AUTO_APPROVE","RESPONDED"))
    rejected = sum(1 for e in entries if e.get("decision") in ("REJECTED","REJECT","BLOCKED","INJECTION_DETECTED"))
    try:
        pending = len(get_pending(TOKEN))
    except Exception:
        pending = 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Entries",    len(entries))
    c2.metric("Approved / Clear", approved)
    c3.metric("Rejected / Blocked", rejected)
    c4.metric("Pending HITL",    pending)

    st.divider()

    if st.button("🔗 Verify Chain Integrity", type="primary"):
        with st.spinner("Verifying SHA-256 hash chain…"):
            try:
                chain = verify_chain(TOKEN)
                all_ok = all(r["valid"] for r in chain)
                if all_ok:
                    st.success(f"✅ All {len(chain)} entries verified — chain is intact.")
                else:
                    st.error(f"❌ TAMPERED — {sum(1 for r in chain if not r['valid'])} entries failed!")
                for r in chain:
                    icon = "✅" if r["valid"] else "❌"
                    st.markdown(f'{icon} **#{r["index"]+1}** `{r["entry_id"][:16]}` · `{r["agent_id"]}` · `{r["action"]}` · <span class="hash-mono">{r["current_hash"]}</span>', unsafe_allow_html=True)
            except APIError as e:
                st.error(e.detail)

    st.divider()
    st.markdown('<div class="s-header">Decision History</div>', unsafe_allow_html=True)

    if not entries:
        st.markdown('<div class="s-card" style="text-align:center;color:#3a5a7a;padding:32px">No audit entries yet — run an AML scan or KYC assessment.</div>', unsafe_allow_html=True)
    else:
        for entry in reversed(entries):
            dom = entry.get("domain","?")
            dom_color = {"AML":"#0066ff","KYC":"#9900cc","CHAT":"#00aa66"}.get(dom,"#446688")
            decision = entry.get("decision","?")
            dec_color = "#ff6666" if decision in ("REJECTED","REJECT","BLOCKED","INJECTION_DETECTED") else \
                        "#ffaa33" if decision in ("SUSPICIOUS","ESCALATE","ENHANCED_MONITORING") else "#44cc88"

            with st.expander(f"[{entry.get('timestamp','')[:19]}]  {entry.get('agent_id','')}  —  {entry.get('action','')}"):
                cc1, cc2, cc3 = st.columns(3)
                cc1.markdown(f"**Entry** `{entry.get('entry_id','')[:14]}…`")
                cc1.markdown(f"<span style='background:{dom_color};color:#fff;padding:2px 8px;border-radius:10px;font-size:10px'>{dom}</span>", unsafe_allow_html=True)
                cc2.markdown(f"**Agent** `{entry.get('agent_id','')}`")
                cc2.markdown(f"**Model** `{entry.get('llm_model','N/A')}`")
                cc3.markdown(f"**Decision** <span style='color:{dec_color};font-weight:700'>{decision}</span>", unsafe_allow_html=True)
                cc3.markdown(f"**Score** `{entry.get('risk_score','—')}`")
                cc3.markdown(f"**HITL** {'Yes' if entry.get('requires_human') else 'No'}")

                ph, ch = entry.get("previous_entry_hash","GENESIS"), entry.get("current_entry_hash","")
                h1, h2 = st.columns(2)
                h1.markdown(f"Prev hash: <span class='hash-mono'>{ph[:16] if ph!='GENESIS' else 'GENESIS'}</span>", unsafe_allow_html=True)
                h2.markdown(f"Curr hash: <span class='hash-mono'>{ch[:16]}</span>", unsafe_allow_html=True)

                with st.expander("Input / Output snapshots"):
                    st.json({"input": entry.get("input_snapshot",{}), "output": entry.get("output_snapshot",{})})


# ══════════════════════════════════════════════════════════════════════
# ── SECTION 4: AI ASSISTANT ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════
elif nav == "💬 AI Assistant":
    st.markdown('<div class="page-title">💬 SENTINEL AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Powered by Grok (xAI) · Banking compliance expert · Context-aware</div>', unsafe_allow_html=True)

    col_chat, col_info = st.columns([6, 3], gap="large")

    with col_chat:
        # Chat history display
        st.markdown('<div class="s-header">Conversation</div>', unsafe_allow_html=True)

        chat_html = '<div class="chat-area">'
        if not st.session_state.chat_history:
            chat_html += """<div style="text-align:center;padding:40px;color:#3a5a7a">
            <div style="font-size:32px;margin-bottom:12px">🤖</div>
            <div style="font-size:14px">Ask me anything about AML, KYC, regulations, or how SENTINEL works.</div>
            </div>"""
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    chat_html += f'<div class="chat-label">YOU</div><div class="chat-bubble-user">{msg["content"]}</div>'
                else:
                    chat_html += f'<div class="chat-label">SENTINEL ASSISTANT</div><div class="chat-bubble-bot">{msg["content"]}</div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

        # Input row
        user_input = st.text_input("", placeholder="Ask about AML, KYC, regulations, audit trail…",
                                   key="chat_input", label_visibility="collapsed")

        btn1, btn2, btn3 = st.columns([2, 2, 1])
        with btn1:
            if st.button("📤 Send", use_container_width=True, type="primary"):
                if user_input.strip():
                    st.session_state.chat_history.append({"role":"user","content":user_input})
                    with st.spinner("SENTINEL Assistant thinking…"):
                        reply = chat_api(TOKEN, st.session_state.chat_history)
                    st.session_state.chat_history.append({"role":"assistant","content":reply})
                    st.rerun()
        with btn2:
            if st.button("📘 App Tutorial", use_container_width=True):
                with st.spinner("Generating tutorial…"):
                    reply = chat_api(TOKEN, [], tutorial=True)
                st.session_state.chat_history.append({"role":"user","content":"📘 App Tutorial"})
                st.session_state.chat_history.append({"role":"assistant","content":reply})
                st.rerun()
        with btn3:
            if st.button("🗑 Clear", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    with col_info:
        st.markdown('<div class="s-header">Suggested Questions</div>', unsafe_allow_html=True)
        suggestions = [
            "What is smurfing and how does SENTINEL detect it?",
            "Why was TX-002 flagged as suspicious?",
            "What does a HIGH KYC risk tier mean?",
            "Explain the hash-chain audit trail.",
            "What is the EU AI Act Article 14?",
            "What happens when a HITL decision is pending?",
            "How does prompt injection protection work?",
            "What is AML 6th Directive Article 20 about PEPs?",
        ]
        for s in suggestions:
            if st.button(s, key=f"sug_{s[:20]}", use_container_width=True):
                st.session_state.chat_history.append({"role":"user","content":s})
                with st.spinner("Thinking…"):
                    reply = chat_api(TOKEN, st.session_state.chat_history)
                st.session_state.chat_history.append({"role":"assistant","content":reply})
                st.rerun()

        st.divider()
        st.markdown('<div class="s-header">System Info</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="s-card" style="font-size:12px;line-height:1.8;color:#5a7a9a">
        <b style="color:#7a9abb">Model:</b> Grok (xAI)<br>
        <b style="color:#7a9abb">Context:</b> Banking compliance only<br>
        <b style="color:#7a9abb">Logged:</b> Every query → audit trail<br>
        <b style="color:#7a9abb">Governed:</b> Governance layer enforced<br>
        <b style="color:#7a9abb">Auth:</b> JWT-protected endpoint
        </div>
        """, unsafe_allow_html=True)
