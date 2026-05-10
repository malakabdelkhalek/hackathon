"""
NORDA Intelligence Platform — Operator Dashboard v2.0
Enterprise UI · Role-based access · 15 modules · JWT-authenticated
"""
import json, os, sys, time, random, base64
import streamlit.components.v1 as _components
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── NORDA logo (base64 embedded) ────────────────────────────────────
def _logo_b64() -> str:
    _path = os.path.join(os.path.dirname(__file__), "norda_logo.jpeg")
    try:
        with open(_path, "rb") as _f:
            return base64.b64encode(_f.read()).decode()
    except Exception:
        return ""

_LOGO = _logo_b64()
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="NORDA — Intelligence Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── session defaults ────────────────────────────────────────────────
_defaults = {
    "jwt_token": None, "operator_name": None, "operator_role": None,
    "operator_dept": None, "operator_initials": None,
    "scan_results": {}, "investigation_results": {}, "kyc_result": None,
    "pipeline_status": "ACTIVE", "chat_history": [],
    "fraud_results": {}, "soc_results": {}, "insider_results": {},
    "fraud_scan_all": None, "soc_scan_all": None, "insider_scan_all": None,
    "it_monitor_result": None, "legal_results": {},
    "nav": "Overview", "dark_mode": True, "chat_open": False,
    "captcha_a": None, "captcha_b": None, "robot_done": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── dark / light CSS ────────────────────────────────────────────────
def _css():
    if st.session_state.dark_mode:
        bg, bg2, text, muted = "#0a1628", "#112240", "#e0f0ff", "#5a7a9a"
        card_bg, card_border  = "rgba(17,34,64,0.85)", "rgba(0,212,170,0.13)"
        accent, accent_dim    = "#00d4aa", "rgba(0,212,170,0.08)"
        input_bg              = "rgba(255,255,255,0.04)"
        sidebar_bg            = "linear-gradient(180deg,#0d1f3c 0%,#0a1628 100%)"
        metric_bg             = "rgba(17,34,64,0.7)"
        table_bg              = "#0d1f3c"
    else:
        bg, bg2, text, muted = "#f0f4f8", "#ffffff", "#1a2332", "#6b7a8d"
        card_bg, card_border  = "rgba(255,255,255,0.95)", "rgba(0,135,90,0.18)"
        accent, accent_dim    = "#00875a", "rgba(0,135,90,0.06)"
        input_bg              = "rgba(0,0,0,0.03)"
        sidebar_bg            = "linear-gradient(180deg,#e8f4f1 0%,#f0f4f8 100%)"
        metric_bg             = "rgba(255,255,255,0.8)"
        table_bg              = "#ffffff"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html,body,[class*="css"]{{font-family:'Inter',sans-serif!important;}}
#MainMenu,footer{{visibility:hidden;}}
.stApp{{background:{bg};color:{text};transition:background 0.3s,color 0.3s;}}
.stApp>header{{background:transparent;}}
.block-container{{padding:1.5rem 2rem;max-width:1440px;}}

[data-testid="stSidebar"]{{
    background:{sidebar_bg}!important;
    border-right:1px solid {card_border};
    transition:background 0.3s;
}}
[data-testid="stSidebar"] *{{color:{text}!important;}}

/* ── Cards ── */
.nc{{
    background:{card_bg};border:1px solid {card_border};
    border-radius:14px;padding:20px 24px;margin-bottom:14px;
    backdrop-filter:blur(12px);transition:border-color 0.2s,transform 0.2s;
    animation:slideUp 0.35s ease both;
}}
.nc:hover{{border-color:{accent};transform:translateY(-1px);}}

/* ── Page load animations ── */
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes drawCheck{{from{{stroke-dashoffset:100}}to{{stroke-dashoffset:0}}}}

.page-content{{animation:fadeIn 0.4s ease both;}}

/* ── Section header ── */
.nh{{
    font-size:10px;font-weight:700;letter-spacing:0.22em;
    text-transform:uppercase;color:{accent};
    margin-bottom:16px;padding-bottom:8px;
    border-bottom:1px solid {card_border};
}}

/* ── Page title ── */
.pt{{font-size:22px;font-weight:800;color:{text};margin-bottom:3px;}}
.ps{{font-size:12px;color:{muted};margin-bottom:22px;letter-spacing:0.04em;}}

/* ── Decision badges ── */
.badge{{display:inline-block;padding:3px 11px;border-radius:20px;
    font-size:10px;font-weight:700;letter-spacing:0.06em;
    font-family:'JetBrains Mono',monospace;}}
.bc{{background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.35);animation:pulse 2s infinite;}}
.bw{{background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.35);}}
.bm{{background:rgba(59,130,246,0.15);color:#3b82f6;border:1px solid rgba(59,130,246,0.35);}}
.ba{{background:rgba(16,185,129,0.15);color:#10b981;border:1px solid rgba(16,185,129,0.35);}}
.bh{{background:rgba(239,68,68,0.12);color:#ef4444;border:1px solid rgba(239,68,68,0.25);}}
.bmed{{background:rgba(245,158,11,0.12);color:#f59e0b;border:1px solid rgba(245,158,11,0.25);}}
.bl{{background:rgba(16,185,129,0.12);color:#10b981;border:1px solid rgba(16,185,129,0.25);}}

/* ── Inject alert ── */
.ia{{
    background:linear-gradient(135deg,rgba(120,0,0,0.5),rgba(60,0,0,0.3));
    border:1px solid rgba(239,68,68,0.5);border-left:4px solid #ef4444;
    border-radius:10px;padding:15px 19px;margin:10px 0;
    animation:pulse 2.5s ease-in-out infinite;
}}

/* ── Hash mono ── */
.hm{{font-family:'JetBrains Mono',monospace;font-size:11px;color:{accent};
    background:{accent_dim};padding:2px 7px;border-radius:4px;
    border:1px solid {card_border};}}

/* ── Metrics ── */
[data-testid="metric-container"]{{
    background:{metric_bg}!important;border:1px solid {card_border}!important;
    border-radius:12px!important;padding:15px!important;transition:background 0.3s;
}}
[data-testid="metric-container"] label{{color:{muted}!important;font-size:11px!important;letter-spacing:0.08em;}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{
    color:{accent}!important;font-family:'JetBrains Mono',monospace!important;
}}

/* ── Buttons ── */
.stButton>button{{
    background:{accent_dim}!important;border:1px solid {card_border}!important;
    color:{accent}!important;border-radius:8px!important;font-size:13px!important;
    font-weight:500!important;transition:all 0.2s!important;
}}
.stButton>button:hover{{
    background:rgba(0,212,170,0.15)!important;border-color:{accent}!important;
    transform:scale(1.02)!important;box-shadow:0 4px 14px rgba(0,212,170,0.15)!important;
}}
.stButton>button:active{{transform:scale(0.98)!important;}}
.stButton>button[kind="primary"]{{
    background:linear-gradient(135deg,rgba(0,212,170,0.22),rgba(0,130,255,0.12))!important;
    border-color:{accent}!important;
}}

/* ── Nav buttons in sidebar ── */
[data-testid="stSidebar"] [data-testid="stButton"] > button {{
    text-align:left!important;justify-content:flex-start!important;
    padding:9px 14px!important;font-size:13px!important;font-weight:500!important;
    border-radius:9px!important;width:100%!important;
    transition:all 0.15s ease!important;margin-bottom:2px!important;
    letter-spacing:0.01em!important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"] {{
    background:rgba(255,255,255,0.02)!important;color:#6a8aa5!important;
    border-color:rgba(0,212,170,0.06)!important;
    box-shadow:none!important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="secondary"]:hover {{
    background:rgba(0,212,170,0.08)!important;color:{accent}!important;
    border-color:rgba(0,212,170,0.22)!important;transform:none!important;
    box-shadow:none!important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{
    background:rgba(0,212,170,0.13)!important;color:{accent}!important;
    border-color:rgba(0,212,170,0.45)!important;font-weight:600!important;
    border-left:3px solid {accent}!important;
    box-shadow:0 0 12px rgba(0,212,170,0.08)!important;transform:none!important;
}}

/* ── Data table ── */
[data-testid="stDataFrame"]{{border:1px solid {card_border}!important;border-radius:10px!important;}}
[data-testid="stDataFrame"] th{{background:{bg2}!important;color:{muted}!important;font-size:11px!important;}}

/* ── Expander ── */
.streamlit-expanderHeader{{
    background:{card_bg}!important;border:1px solid {card_border}!important;
    border-radius:8px!important;color:{muted}!important;
}}

/* ── Chat bubbles ── */
.cb-user{{
    background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.2);
    border-radius:12px 12px 3px 12px;padding:11px 15px;margin:8px 0;
    color:{text};font-size:14px;margin-left:40px;animation:slideUp 0.2s ease;
}}
.cb-bot{{
    background:{accent_dim};border:1px solid {card_border};
    border-radius:12px 12px 12px 3px;padding:11px 15px;margin:8px 0;
    color:{text};font-size:14px;margin-right:40px;animation:slideUp 0.2s ease;
}}
.cl{{font-size:10px;color:{muted};margin-bottom:3px;letter-spacing:0.1em;}}
.ca{{max-height:430px;overflow-y:auto;padding:6px;
    scrollbar-width:thin;scrollbar-color:{card_border} transparent;}}

/* ── Live dot ── */
.ld{{display:inline-block;width:7px;height:7px;background:{accent};
    border-radius:50%;margin-right:5px;animation:pulse 2s infinite;}}

/* ── Avatar ── */
.av{{
    display:inline-flex;align-items:center;justify-content:center;
    width:38px;height:38px;border-radius:50%;
    background:linear-gradient(135deg,{accent},rgba(0,130,255,0.7));
    color:#fff;font-weight:700;font-size:14px;letter-spacing:0.05em;
    flex-shrink:0;
}}

/* ── Score bar ── */
.sb-wrap{{background:rgba(255,255,255,0.06);border-radius:4px;height:5px;margin-top:5px;}}

/* ── HITL panel ── */
.hp{{
    background:{accent_dim};border:1px solid rgba(0,212,170,0.22);
    border-radius:12px;padding:17px;margin-top:13px;
}}

/* ── Status indicators ── */
.status-operational{{color:#10b981;font-weight:600;}}
.status-degraded{{color:#f59e0b;font-weight:600;animation:pulse 2s infinite;}}
.status-incident{{color:#ef4444;font-weight:700;animation:pulse 1.5s infinite;}}

/* ── Toggle switch ── */
.toggle-wrap{{display:flex;align-items:center;gap:8px;cursor:pointer;}}
.toggle-track{{
    width:40px;height:22px;border-radius:11px;
    background:{"#00d4aa" if st.session_state.dark_mode else "#d1d5db"};
    position:relative;transition:background 0.3s;border:1px solid {card_border};
}}
.toggle-thumb{{
    position:absolute;top:2px;
    left:{"20px" if st.session_state.dark_mode else "2px"};
    width:16px;height:16px;border-radius:50%;
    background:#fff;transition:left 0.3s;
    box-shadow:0 1px 4px rgba(0,0,0,0.3);
}}

/* ── IT system status bars ── */
.sys-bar-wrap{{display:flex;align-items:center;gap:10px;margin-bottom:6px;}}
.sys-bar-bg{{flex:1;height:8px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden;}}
</style>""", unsafe_allow_html=True)

_css()

# ─── DATA ─────────────────────────────────────────────────────────────
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

@st.cache_data
def _load(fn):
    with open(os.path.join(_DATA_DIR, fn)) as f:
        return json.load(f)

TRANSACTIONS = _load("transactions.json")
CLIENTS      = _load("clients.json")
CLIENT_MAP   = {c["id"]: c for c in CLIENTS}

from dashboard.api_client import (
    login, health,
    scan_transaction, investigate_transaction, assess_client,
    get_pending, approve, reject, suspend_decision, modify_and_approve,
    get_audit_log, verify_chain,
    get_fraud_events, scan_fraud_event, scan_all_fraud,
    get_soc_events, get_employees, analyze_soc_event, analyze_all_soc,
    analyze_insider, analyze_all_insider,
    get_risk_summary, get_risk_thresholds, evaluate_risk,
    get_it_systems, monitor_it_systems,
    get_legal_documents, review_legal_document, review_all_legal_documents,
    send_chat,
    APIError,
)

# ─── AUTO-LOGIN FROM URL TOKEN ────────────────────────────────────────
if not st.session_state.jwt_token:
    params = st.query_params
    if "token" in params:
        try:
            from api.auth import verify_token_data
            claims = verify_token_data(params["token"])
            st.session_state.jwt_token        = params["token"]
            st.session_state.operator_name    = claims.get("full_name", claims["sub"])
            st.session_state.operator_role    = claims.get("role", "analyst")
            st.session_state.operator_dept    = claims.get("department", "")
            st.session_state.operator_initials = claims.get("initials", "?")
            st.query_params.clear()
        except Exception:
            pass

# ─── HELPERS ──────────────────────────────────────────────────────────
def _dbadge(d):
    m = {"CRITICAL_ESCALATION":("bc","CRITICAL"),
         "WAITING_HUMAN_APPROVAL":("bw","WAITING"),
         "MONITOR_ONLY":("bm","MONITOR"),
         "AUTO_APPROVED":("ba","APPROVED")}
    c, l = m.get(d, ("bl", d or "—"))
    return f'<span class="badge {c}">{l}</span>'

def _rbadge(lv):
    m = {"CRITICAL":"bc","HIGH":"bh","MEDIUM":"bmed","LOW":"bl"}
    return f'<span class="badge {m.get((lv or "").upper(),"bl")}">{lv}</span>'

def _scorebar(v, mx=100):
    pct = min(v/mx*100,100)
    col = "#ef4444" if pct>=90 else "#f59e0b" if pct>=70 else "#3b82f6" if pct>=30 else "#10b981"
    return f'<div class="sb-wrap"><div style="background:{col};height:5px;border-radius:4px;width:{pct}%"></div></div>'

def _sbadge(s):
    if s>=0.75: return f'<span class="badge bh">HIGH {s:.2f}</span>'
    if s>=0.4:  return f'<span class="badge bmed">MED {s:.2f}</span>'
    return f'<span class="badge bl">LOW {s:.2f}</span>'

def _tbadge(t):
    m = {"HIGH":"bh","MEDIUM":"bmed","LOW":"bl","REJECTED":"bc"}
    return f'<span class="badge {m.get(t,"bl")}" style="font-size:15px;padding:5px 18px">{t}</span>'

def _sys_status_class(s):
    return {"operational":"status-operational","degraded":"status-degraded","incident":"status-incident"}.get(s,"")

def _gauge(val, label, max_val=100, warn=70, danger=85):
    col = "#ef4444" if val>=danger else "#f59e0b" if val>=warn else "#10b981"
    return f"""
    <div style="margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted,#5a7a9a);margin-bottom:3px">
        <span>{label}</span><span style="color:{col};font-family:JetBrains Mono,monospace;font-weight:600">{val}%</span>
      </div>
      <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:6px">
        <div style="background:{col};height:6px;border-radius:4px;width:{min(val,100)}%;transition:width 0.5s"></div>
      </div>
    </div>"""

def hitl_panel(decision_id, prefix):
    CAN = st.session_state.operator_role in ("admin", "compliance_officer")
    if not CAN:
        st.markdown('<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:8px;padding:11px;font-size:12px;color:#a07830">Your role cannot approve decisions. Requires Compliance Officer or Admin.</div>', unsafe_allow_html=True)
        return
    st.markdown('<div class="hp">', unsafe_allow_html=True)
    st.markdown("**Human Decision Required**")
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("Approve", key=f"{prefix}_ap_{decision_id}"):
            try: approve(TOKEN, decision_id); st.success("Approved.")
            except APIError as e: st.error(e.detail)
    with c2:
        if st.button("Reject",  key=f"{prefix}_rj_{decision_id}"):
            try: reject(TOKEN, decision_id); st.error("Rejected.")
            except APIError as e: st.error(e.detail)
    with c3:
        if st.button("Suspend", key=f"{prefix}_su_{decision_id}"):
            try: suspend_decision(TOKEN, decision_id); st.warning("Suspended.")
            except APIError as e: st.error(e.detail)
    mod = st.text_input("Modify & Approve:", key=f"{prefix}_mod_{decision_id}",
                         label_visibility="collapsed", placeholder="Enter modification…")
    if st.button("Modify & Approve", key=f"{prefix}_ma_{decision_id}"):
        if mod:
            try: modify_and_approve(TOKEN, decision_id, mod); st.success(f"Modified: {mod}")
            except APIError as e: st.error(e.detail)
        else: st.warning("Enter a modification first.")
    st.markdown('</div>', unsafe_allow_html=True)

# ─── SVG ICONS ────────────────────────────────────────────────────────
ICONS = {
    "Overview":      '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    "AML Monitor":   '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L3 7v7c0 5 9 8 9 8s9-3 9-8V7L12 2z"/><circle cx="12" cy="11" r="3"/></svg>',
    "KYC Review":    '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>',
    "Fraud Detection":'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/><line x1="12" y1="15" x2="12" y2="15" stroke-width="3" stroke-linecap="round"/></svg>',
    "Risk Management":'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "SOC Center":    '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "Insider Threats":'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    "Payments":      '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>',
    "Credit & Lending":'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "IT Risk Monitor":'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6" stroke-linecap="round" stroke-width="3"/><line x1="6" y1="18" x2="6.01" y2="18" stroke-linecap="round" stroke-width="3"/></svg>',
    "DORA Resilience":'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "Legal Review":  '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="3" x2="12" y2="21"/><path d="M3 8h18"/><path d="M3 8c0 2.2 1.8 4 4 4s4-1.8 4-4"/><path d="M17 8c0 2.2-1.8 4-4 4s-4-1.8-4-4"/><line x1="8" y1="21" x2="16" y2="21"/></svg>',
    "Legal Governance":'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="3" x2="12" y2="21"/><path d="M3 8h18"/><path d="M3 8c0 2.2 1.8 4 4 4s4-1.8 4-4"/><path d="M17 8c0 2.2-1.8 4-4 4s-4-1.8-4-4"/><line x1="8" y1="21" x2="16" y2="21"/></svg>',
    "Audit Log":     '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "AI Assistant":  '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "Security Posture":'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
}

# ─── ROLE → NAV MAPPING ───────────────────────────────────────────────
_ALL_ROLES = ["admin","compliance_officer","analyst","soc_analyst","auditor","it_officer","legal_counsel"]

ROLE_NAV = {
    "admin":              ["Overview","AML Monitor","KYC Review","Fraud Detection","Risk Management",
                           "SOC Center","Insider Threats","Payments","Credit & Lending","IT Risk Monitor",
                           "DORA Resilience","Legal Review","Legal Governance","Audit Log","Security Posture"],
    "compliance_officer": ["Overview","AML Monitor","KYC Review","Fraud Detection","Risk Management",
                           "Payments","Credit & Lending","Legal Governance","Audit Log"],
    "analyst":            ["Overview","AML Monitor","KYC Review","Risk Management","Audit Log"],
    "soc_analyst":        ["Overview","SOC Center","Insider Threats","Fraud Detection","Risk Management","Audit Log"],
    "auditor":            ["Audit Log"],
    "it_officer":         ["Overview","IT Risk Monitor","DORA Resilience","SOC Center","Risk Management","Audit Log","Security Posture"],
    "legal_counsel":      ["Overview","Legal Review","Legal Governance","Risk Management","Audit Log"],
}

# ─── LOGIN ────────────────────────────────────────────────────────────
def _gen_captcha():
    a, b = random.randint(3,15), random.randint(2,10)
    st.session_state.captcha_a = a
    st.session_state.captcha_b = b

def show_login():
    dark = st.session_state.dark_mode
    bg_col  = "#0a1628" if dark else "#f0f4f8"
    card_bg = "rgba(17,34,64,0.9)" if dark else "rgba(255,255,255,0.97)"
    border  = "rgba(0,212,170,0.2)" if dark else "rgba(0,135,90,0.2)"
    text_c  = "#e0f0ff" if dark else "#1a2332"
    muted_c = "#5a7a9a" if dark else "#6b7a8d"
    accent  = "#00d4aa" if dark else "#00875a"

    if st.session_state.captcha_a is None:
        _gen_captcha()

    # Dark/light toggle on login page
    col_tgl = st.columns([8,1])[1]
    with col_tgl:
        lbl = "Dark" if dark else "Light"
        if st.button(lbl, key="login_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    logo_html = f'<img src="data:image/jpeg;base64,{_LOGO}" style="width:160px;height:160px;object-fit:contain;margin-bottom:8px">' if _LOGO else ""
    st.markdown(f"""
    <div style='text-align:center;padding:32px 0 20px;animation:fadeIn 0.5s ease'>
      {logo_html}
      <div style='font-size:10px;letter-spacing:0.3em;color:{muted_c};text-transform:uppercase;margin-top:2px'>
        AI Banking Governance Platform
      </div>
    </div>""", unsafe_allow_html=True)

    _, mid, _ = st.columns([1,1.2,1])
    with mid:
        if not health():
            st.error("API server unreachable — run `python main.py` first.")
            return

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. thomas.martin")
            password = st.text_input("Password", type="password", placeholder="••••••••••")

            a, b = st.session_state.captcha_a, st.session_state.captcha_b
            st.markdown(f'<div style="font-size:12px;color:{muted_c};margin-bottom:6px">Security check: what is {a} + {b}?</div>', unsafe_allow_html=True)
            captcha_ans = st.text_input("Answer", placeholder="Type the answer", label_visibility="collapsed")

            robot = st.checkbox("I confirm I am an authorised NORDA operator")
            submitted = st.form_submit_button("Authenticate", use_container_width=True, type="primary")

        if submitted:
            if not robot:
                st.error("Please confirm you are an authorised operator.")
            elif not captcha_ans or not captcha_ans.strip().isdigit() or int(captcha_ans.strip()) != a+b:
                st.error(f"Incorrect answer to the security question. Try again.")
                _gen_captcha(); st.rerun()
            elif not username or not password:
                st.error("Username and password are required.")
            else:
                with st.spinner("Authenticating…"):
                    try:
                        data = login(username, password)
                        from api.auth import verify_token_data
                        claims = verify_token_data(data["access_token"])
                        st.session_state.jwt_token         = data["access_token"]
                        st.session_state.operator_name     = data["operator"]
                        st.session_state.operator_role     = data["role"]
                        st.session_state.operator_dept     = claims.get("department","")
                        st.session_state.operator_initials = claims.get("initials","?")
                        st.session_state.nav = "Overview" if data["role"] != "auditor" else "Audit Log"
                        st.rerun()
                    except APIError as e:
                        st.error(f"Authentication failed: {e.detail}")
                    except Exception as e:
                        st.error(f"Cannot reach API: {e}")

        st.markdown(f"""
        <div style='background:rgba(0,212,170,0.04);border:1px solid {border};border-radius:10px;
                    padding:14px;margin-top:16px;font-size:12px;color:{muted_c}'>
        <b style='color:{accent}'>Demo credentials</b><br><br>
        <code>thomas.martin</code> / <code>compliance2026</code> &mdash; Compliance Officer<br>
        <code>sarah.chen</code> &nbsp;&nbsp;&nbsp;/ <code>itops2026</code> &nbsp;&nbsp;&nbsp;&nbsp;&mdash; IT Risk Officer<br>
        <code>marc.dubois</code> &nbsp;&nbsp;/ <code>legal2026</code> &nbsp;&nbsp;&nbsp;&nbsp;&mdash; Legal Counsel<br>
        <code>admin</code> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/ <code>norda_admin_2026</code> &mdash; System Admin<br>
        <code>soc_analyst</code> &nbsp;&nbsp;/ <code>soc2026</code> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&mdash; SOC Analyst
        </div>""", unsafe_allow_html=True)


if not st.session_state.jwt_token:
    show_login()
    st.stop()

TOKEN = st.session_state.jwt_token
ROLE  = st.session_state.operator_role or "analyst"

# ─── SIDEBAR ──────────────────────────────────────────────────────────
with st.sidebar:
    # Header
    initials = st.session_state.operator_initials or "?"
    name     = st.session_state.operator_name or "Operator"
    dept     = st.session_state.operator_dept or ""
    role_labels = {
        "admin":"System Administrator","compliance_officer":"Compliance Officer",
        "analyst":"Risk Analyst","soc_analyst":"SOC Analyst","auditor":"Senior Auditor",
        "it_officer":"IT Risk Officer","legal_counsel":"Legal Counsel",
    }
    accent_col = "#00d4aa" if st.session_state.dark_mode else "#00875a"

    logo_sidebar = f'<img src="data:image/jpeg;base64,{_LOGO}" style="width:100%;max-width:120px;object-fit:contain;display:block;margin:0 auto 6px">' if _LOGO else ""
    st.markdown(f"""
    <div style='padding:10px 0 4px;text-align:center'>
      {logo_sidebar}
      <div style='font-size:9px;letter-spacing:.28em;color:#4a6a8a;text-transform:uppercase;margin-top:2px'>AI Banking Intelligence</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    # User card
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:10px;margin-bottom:14px'>
      <div class='av'>{initials}</div>
      <div>
        <div style='font-size:13px;font-weight:600'>{name}</div>
        <div style='font-size:11px;color:{accent_col}'>{role_labels.get(ROLE,ROLE)}</div>
        <div style='font-size:10px;color:#4a6a8a'>{dept}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Dark/light toggle
    mode_lbl = "Dark mode" if st.session_state.dark_mode else "Light mode"
    if st.button(f"{'☽' if st.session_state.dark_mode else '☀'} {mode_lbl}", use_container_width=True, key="mode_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        _css()
        st.rerun()

    st.divider()

    # Navigation — clean labeled buttons per nav item
    nav_options = ROLE_NAV.get(ROLE, ["Audit Log"])
    if st.session_state.nav not in nav_options:
        st.session_state.nav = nav_options[0]

    _NAV_PREFIX = {
        "Overview":        "▣  ",
        "AML Monitor":     "◉  ",
        "KYC Review":      "⊙  ",
        "Fraud Detection": "⚡  ",
        "Risk Management": "◬  ",
        "SOC Center":      "⬡  ",
        "Insider Threats": "⚠  ",
        "Payments":        "⊕  ",
        "Credit & Lending":"≋  ",
        "IT Risk Monitor": "⊟  ",
        "DORA Resilience": "⊠  ",
        "Legal Review":    "⊢  ",
        "Legal Governance":"⊣  ",
        "Audit Log":       "≡  ",
        "Security Posture":"⊥  ",
    }
    st.markdown('<div style="margin-top:4px">', unsafe_allow_html=True)
    for item in nav_options:
        is_active = st.session_state.nav == item
        label = _NAV_PREFIX.get(item, "·  ") + item
        if st.button(label, key=f"nav_{item}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.nav = item
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # System status
    try:
        pending_count = len(get_pending(TOKEN))
    except Exception:
        pending_count = 0

    st.markdown(f'<span class="ld"></span><b>OPERATIONAL</b>', unsafe_allow_html=True)
    if pending_count:
        st.warning(f"{pending_count} pending HITL decisions")
    else:
        st.success("Queue clear")

    pip_col = accent_col if st.session_state.pipeline_status == "ACTIVE" else "#ef4444"
    st.markdown(f'<div style="font-size:11px;color:{pip_col};font-weight:600;margin:4px 0">● {st.session_state.pipeline_status}</div>', unsafe_allow_html=True)

    if st.session_state.pipeline_status == "ACTIVE":
        if st.button("Suspend Pipeline", use_container_width=True):
            st.session_state.pipeline_status = "SUSPENDED"; st.rerun()
    else:
        if st.button("Resume Pipeline", use_container_width=True):
            st.session_state.pipeline_status = "ACTIVE"; st.rerun()

    st.divider()

    with st.expander("Active JWT"):
        st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:{accent_col};word-break:break-all;line-height:1.5">{TOKEN[:60]}…</div>', unsafe_allow_html=True)

    if st.button("Logout", use_container_width=True):
        for k in _defaults: st.session_state[k] = _defaults[k]
        st.rerun()

    st.divider()
    st.caption("HACK'N'BIZ 2026 · Fortum Junior Entreprise")


# ══════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════

def _page_header(title: str, subtitle: str = ""):
    """Render a page header with the NORDA logo badge + title."""
    logo_html = (
        f'<img src="data:image/jpeg;base64,{_LOGO}" '
        f'style="width:40px;height:40px;object-fit:contain;'
        f'margin-right:12px;vertical-align:middle;flex-shrink:0">'
        if _LOGO else ""
    )
    sub_html = f'<div class="ps">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div style="display:flex;align-items:center;margin-bottom:2px">'
        f'{logo_html}'
        f'<div><div class="pt" style="margin-bottom:0">{title}</div>{sub_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="page-content">', unsafe_allow_html=True)
nav = st.session_state.nav

# ─── OVERVIEW ──────────────────────────────────────────────────────────
if nav == "Overview":
    _page_header('Dashboard', 'Executive summary · All domains · Real-time status')

    try:
        summary = get_risk_summary(TOKEN)
    except Exception:
        summary = {}

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Events",     summary.get("total_events",0))
    c2.metric("Critical",         summary.get("critical_count",0))
    c3.metric("Waiting Approval", summary.get("waiting_approval_count",0))
    c4.metric("Monitoring",       summary.get("monitor_count",0))
    c5.metric("Auto-Approved",    summary.get("approved_count",0))

    st.divider()
    col_l, col_r = st.columns([5,5], gap="large")

    with col_l:
        st.markdown('<div class="nh">Decision Distribution</div>', unsafe_allow_html=True)
        total = max(summary.get("total_events",1), 1)
        for lbl, key, cls in [
            ("Critical Escalation",    "critical_count",         "bc"),
            ("Waiting Human Approval", "waiting_approval_count", "bw"),
            ("Monitor Only",           "monitor_count",          "bm"),
            ("Auto-Approved",          "approved_count",         "ba"),
        ]:
            val = summary.get(key, 0)
            pct = val / total * 100
            st.markdown(f"""
            <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
              <span style='font-size:13px'>{lbl}</span>
              <span class='badge {cls}'>{val}</span>
            </div>
            {_scorebar(pct)}
            <div style='font-size:10px;color:#4a6a8a;text-align:right;margin-bottom:12px'>{pct:.1f}%</div>
            """, unsafe_allow_html=True)

        # Simple chart using streamlit
        st.markdown('<div class="nh" style="margin-top:20px">Risk Score Trend (30 days)</div>', unsafe_allow_html=True)
        import random as rnd; rnd.seed(42)
        scores_data = {"Risk Score": [max(0,min(100, 35+rnd.gauss(0,15))) for _ in range(30)]}
        st.line_chart(scores_data, height=160)

    with col_r:
        st.markdown('<div class="nh">Platform Metrics</div>', unsafe_allow_html=True)
        for lbl, val, unit, warn in [
            ("Highest Risk Score", summary.get("highest_risk_score",0), "/100", 70),
            ("Average Risk Score", summary.get("average_risk_score",0), "/100", 50),
            ("Total HITL Decisions", summary.get("hitl_total",0), "", 0),
            ("Pending Approvals",  summary.get("pending_approvals",0), "", 0),
        ]:
            col_v = "#ef4444" if isinstance(val,(int,float)) and val>=warn and warn>0 else "#00d4aa"
            st.markdown(f"""
            <div class='nc' style='padding:13px 17px;margin-bottom:7px'>
              <div style='font-size:10px;color:#4a6a8a;letter-spacing:.1em;text-transform:uppercase'>{lbl}</div>
              <div style='font-size:26px;font-weight:700;color:{col_v};font-family:JetBrains Mono,monospace'>{val}{unit}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="nh" style="margin-top:8px">Domain Breakdown</div>', unsafe_allow_html=True)
        breakdown = summary.get("domains_breakdown",{})
        if breakdown:
            names = list(breakdown.keys())
            vals  = [breakdown[k] for k in names]
            st.bar_chart(dict(zip(names, vals)), height=150)
        else:
            st.info("Run agent scans to populate domain data.")


# ─── AML MONITOR ───────────────────────────────────────────────────────
elif nav == "AML Monitor":
    _page_header('AML Transaction Monitor', 'Real-time risk scoring · Smurfing detection · Injection protection')
    if st.session_state.pipeline_status == "SUSPENDED":
        st.error("PIPELINE SUSPENDED — All agent actions are halted.")

    col_l, col_r = st.columns([6,4], gap="large")

    with col_l:
        st.markdown('<div class="nh">Transaction Feed</div>', unsafe_allow_html=True)
        rows = []
        for tx in TRANSACTIONS:
            cl = CLIENT_MAP.get(tx["client_id"],{})
            r  = st.session_state.scan_results.get(tx["id"])
            rows.append({"TX ID":tx["id"],"Client":cl.get("name",tx["client_id"]),
                         "Amount":f"€{tx['amount']:,.0f}","Dest":tx["country_destination"],
                         "Memo":tx["memo"][:36]+("…" if len(tx["memo"])>36 else ""),
                         "Risk":f"{r['risk_score']:.2f}" if r else "—","Flag":r["flag"] if r else "—"})
        st.dataframe(rows, use_container_width=True, hide_index=True)

        if st.button("Run AML Scan on All Transactions", type="primary", use_container_width=True):
            prog = st.progress(0, text="Initialising…")
            ph   = st.empty()
            for i, tx in enumerate(TRANSACTIONS):
                cl = CLIENT_MAP.get(tx["client_id"],{})
                ph.info(f"Scanning {tx['id']}…")
                try:
                    result = scan_transaction(TOKEN, tx, cl, st.session_state.pipeline_status)
                    st.session_state.scan_results[tx["id"]] = result
                except APIError as e:
                    if e.status_code == 401:
                        st.session_state.jwt_token = None; st.rerun()
                prog.progress((i+1)/len(TRANSACTIONS), text=f"Scanned {i+1}/{len(TRANSACTIONS)}")
                time.sleep(0.04)
            ph.success(f"Scan complete — {len(TRANSACTIONS)} transactions processed.")

    with col_r:
        st.markdown('<div class="nh">Flagged Cases</div>', unsafe_allow_html=True)
        if not st.session_state.scan_results:
            st.markdown('<div class="nc" style="text-align:center;color:#3a5a7a;padding:30px">Run a scan to see flagged transactions</div>', unsafe_allow_html=True)
        else:
            flagged = sorted([r for r in st.session_state.scan_results.values()
                              if r.get("risk_score",0)>0.4 or r.get("injection_detected")],
                             key=lambda x: x.get("risk_score",0), reverse=True)
            if not flagged: st.success("No suspicious transactions detected.")
            for result in flagged:
                tx_id = result["transaction_id"]
                cl    = CLIENT_MAP.get(result["client_id"],{})
                score = result.get("risk_score",0)
                if result.get("injection_detected"):
                    st.markdown(f'<div class="ia"><b style="color:#ef4444">PROMPT INJECTION BLOCKED</b><br><span style="font-size:12px;color:#cc8888">{tx_id} — {cl.get("name","?")} — Input rejected before LLM.</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="nc"><div style="display:flex;justify-content:space-between"><b>{tx_id}</b>{_sbadge(score)}</div></div>', unsafe_allow_html=True)
                with st.expander(f"Reasoning — {tx_id}"):
                    st.markdown(f'<div style="font-size:13px;color:#8899aa;line-height:1.6">{result.get("reasoning","—")}</div>', unsafe_allow_html=True)
                if not result.get("injection_detected"):
                    if st.button(f"Investigate {tx_id}", key=f"inv_{tx_id}"):
                        tx_obj = next((t for t in TRANSACTIONS if t["id"]==tx_id),{})
                        cl2    = CLIENT_MAP.get(result["client_id"],{})
                        with st.status(f"Investigating {tx_id}…", expanded=True) as s:
                            st.write("Loading client history…"); time.sleep(0.3)
                            st.write("Querying ChromaDB…"); time.sleep(0.3)
                            st.write("Running Investigator Agent…")
                            try:
                                inv = investigate_transaction(TOKEN, tx_obj, cl2, st.session_state.pipeline_status)
                                st.session_state.investigation_results[tx_id] = inv
                                s.update(label="Investigation complete", state="complete")
                            except APIError as e:
                                s.update(label="Failed", state="error"); st.error(e.detail)
                if tx_id in st.session_state.investigation_results:
                    inv = st.session_state.investigation_results[tx_id]
                    with st.expander("Investigation Report", expanded=True):
                        rec = inv.get("recommendation","UNKNOWN")
                        rc  = {"FREEZE_ACCOUNT":"#ef4444","FREEZE_TRANSFERS":"#f97316","ESCALATE_TO_AUTHORITIES":"#ef4444","ENHANCED_MONITORING":"#f59e0b","CLEAR":"#10b981"}.get(rec,"#888")
                        st.markdown(f"**Recommendation:** <span style='color:{rc};font-weight:700;font-size:14px'>{rec}</span>", unsafe_allow_html=True)
                        st.text_area("Report", value=inv.get("investigation_report",""), height=200,
                                     key=f"rep_{tx_id}", disabled=True, label_visibility="collapsed")
                        if inv.get("requires_human") and inv.get("decision_id"):
                            hitl_panel(inv["decision_id"], f"aml_{tx_id}")
                st.divider()


# ─── KYC REVIEW ────────────────────────────────────────────────────────
elif nav == "KYC Review":
    _page_header('KYC Client Onboarding', 'Sanctions screening · PEP verification · Risk tier assignment')
    NATS = ["French","German","British","Spanish","Italian","Belgian","Dutch","Swedish","Polish",
            "Romanian","Algerian","Moroccan","Tunisian","Russian","Chinese","Iranian","North Korean",
            "Emirati","Saudi","Nigerian","Pakistani","American","Other"]
    col_f, col_r = st.columns([5,5], gap="large")
    with col_f:
        st.markdown('<div class="nh">Onboarding Form</div>', unsafe_allow_html=True)
        with st.form("kyc_form"):
            name   = st.text_input("Full Name",           placeholder="e.g. Viktor Petrov")
            nat    = st.selectbox("Nationality",           NATS)
            res    = st.text_input("Country of Residence", placeholder="e.g. France")
            acc    = st.selectbox("Account Type",          ["retail","corporate","private_banking"])
            sof    = st.selectbox("Source of Funds",       ["salary","business","investment_portfolio","offshore_company","other"])
            pep    = st.checkbox("Politically Exposed Person (PEP)")
            biz    = st.text_area("Business Description",  placeholder="Corporate/private banking…", label_visibility="visible") if acc!="retail" else ""
            sub    = st.form_submit_button("Run KYC Assessment", type="primary", use_container_width=True)
        if sub:
            st.session_state.kyc_result = None
            form = {"name":name,"nationality":nat,"country_of_residence":res,
                    "account_type":acc,"source_of_funds":sof,"pep_declared":pep,"business_description":biz}
            with st.status("Running KYC Pipeline…", expanded=True) as s:
                st.write("Step 1 — Sanitizing data…"); time.sleep(0.4)
                st.write("Step 2 — Sanctions screening…"); time.sleep(0.4)
                st.write("Step 3 — PEP verification…"); time.sleep(0.3)
                st.write("Step 4 — Risk assessment (Groq/Llama)…")
                try:
                    r = assess_client(TOKEN, form, st.session_state.pipeline_status)
                    st.session_state.kyc_result = r
                    s.update(label="KYC Complete", state="complete")
                except APIError as e:
                    s.update(label="Failed", state="error")
                    if e.status_code==401: st.session_state.jwt_token=None; st.rerun()
                    st.error(e.detail)
    with col_r:
        st.markdown('<div class="nh">Assessment Results</div>', unsafe_allow_html=True)
        r = st.session_state.kyc_result
        if r is None:
            st.markdown('<div class="nc" style="text-align:center;color:#3a5a7a;padding:30px">Submit the form to run the pipeline</div>', unsafe_allow_html=True)
        elif r.get("injection_detected"):
            st.markdown('<div class="ia"><b style="color:#ef4444">INJECTION BLOCKED</b><br>Malicious input detected in form data.</div>', unsafe_allow_html=True)
        elif r.get("rejected"):
            st.error(f"ONBOARDING REJECTED\n\n{r.get('reject_reason','')}")
        else:
            san = r.get("sanctions_result",{}); pep_r = r.get("pep_result",{})
            st.markdown(f"{'Sanctioned' if san.get('sanctioned') else 'Clear'} — Sanctions: {san.get('reason','N/A')}")
            st.markdown(f"{'PEP Confirmed' if pep_r.get('pep_confirmed') else 'Not PEP'} — {pep_r.get('reason','N/A')}")
            if r.get("llm_summary"):
                with st.expander("Collector Agent Summary"):
                    st.markdown(f'<div style="font-size:13px;color:#8899aa;line-height:1.6">{r["llm_summary"]}</div>', unsafe_allow_html=True)
            st.divider()
            st.markdown(f'<div style="text-align:center;padding:18px 0">{_tbadge(r.get("risk_tier","LOW"))}</div>', unsafe_allow_html=True)
            dec = r.get("decision","APPROVE")
            dc  = "#ef4444" if dec in ("REJECT","ESCALATE") else "#f59e0b" if dec=="APPROVE_WITH_CONDITIONS" else "#10b981"
            st.markdown(f"**Decision:** <span style='color:{dc};font-weight:700'>{dec}</span>", unsafe_allow_html=True)
            with st.expander("Full Risk Assessment", expanded=True):
                st.text_area("Assessment", value=r.get("llm_assessment",""), height=250,
                             disabled=True, key="kyc_txt", label_visibility="collapsed")
            if r.get("requires_human") and r.get("decision_id"):
                hitl_panel(r["decision_id"], "kyc")


# ─── FRAUD DETECTION ────────────────────────────────────────────────────
elif nav == "Fraud Detection":
    _page_header('Fraud Detection', 'Card fraud · Account takeover · Wire fraud · Synthetic identity')
    try:    fraud_events = get_fraud_events(TOKEN)
    except: fraud_events = []

    col_l, col_r = st.columns([6,4], gap="large")
    with col_l:
        st.markdown('<div class="nh">Fraud Event Feed</div>', unsafe_allow_html=True)
        rows = []
        for ev in fraud_events:
            r = st.session_state.fraud_results.get(ev.get("event_id",""))
            rows.append({"Event ID":ev.get("event_id",""),"Type":ev.get("fraud_type",""),
                         "Amount":f"€{ev.get('amount',0):,.0f}","Country":ev.get("country",""),
                         "Score":f"{r['risk_score']:.1f}" if r else "—","Decision":r["decision"] if r else "—"})
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if st.button("Scan All Fraud Events", type="primary", use_container_width=True):
            with st.spinner("Running fraud detection…"):
                try:
                    res = scan_all_fraud(TOKEN)
                    st.session_state.fraud_scan_all = res
                    for r in res.get("results",[]): st.session_state.fraud_results[r.get("event_id","")] = r
                    st.success(f"{res['total']} events — {res['critical']} critical, {res['waiting']} waiting.")
                except APIError as e: st.error(e.detail)
        if st.session_state.fraud_scan_all:
            res = st.session_state.fraud_scan_all
            c1,c2,c3 = st.columns(3)
            c1.metric("Total",    res.get("total",0))
            c2.metric("Critical", res.get("critical",0))
            c3.metric("Waiting",  res.get("waiting",0))
    with col_r:
        st.markdown('<div class="nh">Scan Single Event</div>', unsafe_allow_html=True)
        eids     = [ev.get("event_id","") for ev in fraud_events]
        selected = st.selectbox("Select Event", eids, key="fraud_sel", label_visibility="collapsed")
        if st.button("Scan Selected", use_container_width=True):
            ev = next((e for e in fraud_events if e.get("event_id")==selected), None)
            if ev:
                with st.spinner(f"Scanning {selected}…"):
                    try:
                        r = scan_fraud_event(TOKEN, ev)
                        st.session_state.fraud_results[selected] = r
                    except APIError as e: st.error(e.detail)
        if selected in st.session_state.fraud_results:
            r = st.session_state.fraud_results[selected]
            st.markdown(f"""<div class='nc'>
            <div style='font-size:13px;font-weight:600'>{selected}</div>
            <div style='margin:8px 0'>{_dbadge(r.get('decision',''))}</div>
            <div style='font-size:12px;color:#4a6a8a'>Type: {r.get('fraud_type','')}</div>
            <div style='font-size:12px;color:#4a6a8a'>Score: <b style='color:#00d4aa'>{r.get('risk_score',0):.1f}/100</b></div>
            {_scorebar(r.get('risk_score',0))}
            </div>""", unsafe_allow_html=True)
            with st.expander("AI Analysis"):
                st.markdown(f'<div style="font-size:13px;color:#8899aa;line-height:1.6">{r.get("analysis","—")}</div>', unsafe_allow_html=True)
            if r.get("requires_human") and r.get("decision_id"):
                hitl_panel(r["decision_id"], f"fraud_{selected}")


# ─── RISK MANAGEMENT ────────────────────────────────────────────────────
elif nav == "Risk Management":
    _page_header('Risk Management', 'Adaptive decision engine · Cross-domain scoring · Thresholds')
    try:    summary = get_risk_summary(TOKEN)
    except: summary = {}
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Highest Score",  f"{summary.get('highest_risk_score',0):.1f}")
    c2.metric("Average Score",  f"{summary.get('average_risk_score',0):.1f}")
    c3.metric("Total HITL",     summary.get("hitl_total",0))
    c4.metric("Pending",        summary.get("pending_approvals",0))
    st.divider()
    col_l, col_r = st.columns([5,5], gap="large")
    with col_l:
        st.markdown('<div class="nh">Decision Tiers</div>', unsafe_allow_html=True)
        for tier, rng, desc, cls in [
            ("AUTO_APPROVED",          "Score < 30",  "Low risk — automatic clearance",     "ba"),
            ("MONITOR_ONLY",           "Score 30–69", "Moderate — flag for periodic review","bm"),
            ("WAITING_HUMAN_APPROVAL", "Score 70–89", "High risk — human decision required","bw"),
            ("CRITICAL_ESCALATION",    "Score ≥ 90",  "Critical — immediate escalation",    "bc"),
        ]:
            st.markdown(f"""
            <div class='nc' style='padding:12px 17px;margin-bottom:6px'>
              <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                <span class='badge {cls}'>{tier}</span>
                <span style='font-size:12px;color:#5a7a9a;font-family:JetBrains Mono,monospace'>{rng}</span>
              </div>
              <div style='font-size:12px;color:#4a6a8a'>{desc}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="nh" style="margin-top:18px">Domain Activity</div>', unsafe_allow_html=True)
        bd = summary.get("domains_breakdown",{})
        if bd: st.bar_chart(bd, height=180)
        else:  st.info("No domain data yet.")

    with col_r:
        st.markdown('<div class="nh">Manual Risk Evaluation</div>', unsafe_allow_html=True)
        domain = st.selectbox("Domain", ["transaction","fraud","soc","insider"])
        defaults = {
            "transaction":'{"amount":50000,"country_risk_score":0.7,"velocity_score":0.4,"smurfing_score":0.3,"pep_involved":0}',
            "fraud":'{"velocity_score":0.6,"geo_anomaly_score":0.5,"device_risk_score":0.3,"account_age_days":30,"amount_anomaly":0.4}',
            "soc":'{"threat_severity":0.8,"lateral_movement":0.5,"data_exfil_volume_mb":200,"impossible_travel":1,"privilege_escalation":0}',
            "insider":'{"after_hours_logins":8,"data_exfil_volume_mb":150,"resignation_flag":1,"access_sensitive_files_count":60,"policy_violation_count":2}',
        }
        factors_str = st.text_area("Risk Factors (JSON)", value=defaults[domain], height=150, label_visibility="visible")
        if st.button("Evaluate Risk", type="primary", use_container_width=True):
            try:
                fac = json.loads(factors_str)
                res = evaluate_risk(TOKEN, domain, fac)
                score = res.get("composite_score", res.get("risk_score",0))
                dec   = res.get("decision","")
                st.markdown(f"""
                <div class='nc'>
                  <div style='margin-bottom:8px'>{_dbadge(dec)}</div>
                  <div style='font-size:28px;font-weight:700;font-family:JetBrains Mono,monospace;color:#00d4aa'>
                    {score:.1f}<span style='font-size:14px;color:#4a6a8a'>/100</span></div>
                  {_scorebar(score)}
                  <div style='font-size:12px;color:#4a6a8a;margin-top:8px'>Level: {res.get('risk_level','')} · Human required: {'Yes' if res.get('requires_human') else 'No'}</div>
                </div>""", unsafe_allow_html=True)
            except json.JSONDecodeError: st.error("Invalid JSON.")
            except APIError as e:       st.error(e.detail)


# ─── SOC CENTER ────────────────────────────────────────────────────────
elif nav == "SOC Center":
    _page_header('Security Operations Center', 'Threat detection · Brute force · Data exfiltration · Credential attacks')
    try:    soc_events = get_soc_events(TOKEN)
    except: soc_events = []
    col_l, col_r = st.columns([6,4], gap="large")
    with col_l:
        st.markdown('<div class="nh">Security Event Feed</div>', unsafe_allow_html=True)
        rows = []
        for ev in soc_events:
            r = st.session_state.soc_results.get(ev.get("event_id",""))
            rows.append({"Event":ev.get("event_id",""),"Type":ev.get("event_type",""),
                         "Severity":ev.get("severity",""),"Source IP":ev.get("source_ip",""),
                         "Score":f"{r['risk_score']:.1f}" if r else "—","Decision":r["decision"] if r else "—"})
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if st.button("Analyse All SOC Events", type="primary", use_container_width=True):
            with st.spinner("Running SOC analysis…"):
                try:
                    res = analyze_all_soc(TOKEN)
                    st.session_state.soc_scan_all = res
                    for r in res.get("results",[]): st.session_state.soc_results[r.get("event_id","")] = r
                    st.success(f"{res['total']} events — {res['critical']} critical, {res['waiting']} waiting.")
                except APIError as e: st.error(e.detail)
    with col_r:
        st.markdown('<div class="nh">Analyse Single Event</div>', unsafe_allow_html=True)
        eids     = [ev.get("event_id","") for ev in soc_events]
        selected = st.selectbox("Select Event", eids, key="soc_sel", label_visibility="collapsed")
        if st.button("Analyse", use_container_width=True):
            ev = next((e for e in soc_events if e.get("event_id")==selected), None)
            if ev:
                with st.spinner(f"Analysing {selected}…"):
                    try:
                        r = analyze_soc_event(TOKEN, ev)
                        st.session_state.soc_results[selected] = r
                    except APIError as e: st.error(e.detail)
        if selected in st.session_state.soc_results:
            r = st.session_state.soc_results[selected]
            st.markdown(f"""<div class='nc'>
            <div style='font-size:13px;font-weight:600'>{selected}</div>
            <div style='margin:8px 0'>{_dbadge(r.get('decision',''))}</div>
            <div style='font-size:12px;color:#4a6a8a'>Threat: <b>{r.get('threat_class','')}</b></div>
            <div style='font-size:12px;color:#4a6a8a'>Score: <b style='color:#00d4aa'>{r.get('risk_score',0):.1f}/100</b></div>
            {_scorebar(r.get('risk_score',0))}
            <div style='font-size:12px;color:#4a6a8a;margin-top:6px'>{r.get('recommended_action','')}</div>
            </div>""", unsafe_allow_html=True)
            with st.expander("Threat Analysis"):
                st.markdown(f'<div style="font-size:13px;color:#8899aa;line-height:1.6">{r.get("analysis","—")}</div>', unsafe_allow_html=True)
            if r.get("requires_human") and r.get("decision_id"):
                hitl_panel(r["decision_id"], f"soc_{selected}")


# ─── INSIDER THREATS ────────────────────────────────────────────────────
elif nav == "Insider Threats":
    _page_header('Insider Threat Intelligence', 'Behavioural profiling · Resignation flags · Data exfiltration · Privilege abuse')
    try:    employees = get_employees(TOKEN)
    except: employees = []
    col_l, col_r = st.columns([6,4], gap="large")
    with col_l:
        st.markdown('<div class="nh">Employee Risk Roster</div>', unsafe_allow_html=True)
        rows = []
        for emp in employees:
            r = st.session_state.insider_results.get(emp.get("id",""))
            rows.append({"ID":emp.get("id",""),"Name":emp.get("name",""),"Dept":emp.get("department",""),
                         "Performance":emp.get("recent_performance",""),
                         "Resignation":"Yes" if emp.get("resignation_notice") else "No",
                         "Score":f"{r['risk_score']:.1f}" if r else "—","Decision":r["decision"] if r else "—"})
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if st.button("Analyse All Employees", type="primary", use_container_width=True):
            with st.spinner("Building behavioural profiles…"):
                try:
                    res = analyze_all_insider(TOKEN)
                    st.session_state.insider_scan_all = res
                    for r in res.get("results",[]): st.session_state.insider_results[r.get("employee_id","")] = r
                    critical = sum(1 for r in res.get("results",[]) if r.get("decision")=="CRITICAL_ESCALATION")
                    st.success(f"{res['total']} employees — {critical} critical.")
                except APIError as e: st.error(e.detail)
    with col_r:
        st.markdown('<div class="nh">Individual Analysis</div>', unsafe_allow_html=True)
        opts = {f"{e.get('id')} — {e.get('name','')}": e.get("id","") for e in employees}
        sel_lbl = st.selectbox("Employee", list(opts.keys()), key="insider_sel", label_visibility="collapsed")
        sel_id  = opts.get(sel_lbl,"")
        if st.button("Analyse Employee", use_container_width=True):
            if sel_id:
                with st.spinner(f"Profiling {sel_id}…"):
                    try:
                        r = analyze_insider(TOKEN, sel_id)
                        st.session_state.insider_results[sel_id] = r
                    except APIError as e: st.error(e.detail)
        if sel_id in st.session_state.insider_results:
            r     = st.session_state.insider_results[sel_id]
            flags = r.get("behavioral_flags",[])
            st.markdown(f"""<div class='nc'>
            <div style='font-size:14px;font-weight:600'>{r.get('employee_name','')}</div>
            <div style='margin:8px 0'>{_dbadge(r.get('decision',''))}</div>
            <div style='font-size:12px;color:#4a6a8a'>Score: <b style='color:#00d4aa'>{r.get('risk_score',0):.1f}/100</b></div>
            {_scorebar(r.get('risk_score',0))}
            </div>""", unsafe_allow_html=True)
            if flags:
                st.markdown('<div class="nh" style="margin-top:14px">Behavioural Flags</div>', unsafe_allow_html=True)
                for f in flags:
                    st.markdown(f'<span class="badge bw" style="margin:2px">{f}</span>', unsafe_allow_html=True)
                st.markdown("")
            with st.expander("Behavioural Analysis"):
                st.markdown(f'<div style="font-size:13px;color:#8899aa;line-height:1.6">{r.get("analysis","—")}</div>', unsafe_allow_html=True)
                st.info(f"Recommended: {r.get('recommended_action','Monitor.')}")
            if r.get("requires_human") and r.get("decision_id"):
                hitl_panel(r["decision_id"], f"insider_{sel_id}")


# ─── PAYMENTS ───────────────────────────────────────────────────────────
elif nav == "Payments":
    _page_header('Payments Overview', 'Real-time payment monitoring · Cross-border risk · Wire transfer analysis')
    try:    payments = _load("payments_data.json")
    except: payments = []
    if payments:
        total_vol = sum(p.get("amount_eur",0) for p in payments)
        high_risk = sum(1 for p in payments if p.get("risk_score",0)>=0.7)
        flagged_n = sum(1 for p in payments if p.get("flagged"))
        avg_score = sum(p.get("risk_score",0) for p in payments)/len(payments)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Volume",   f"€{total_vol:,.0f}")
        c2.metric("High Risk",      high_risk)
        c3.metric("Flagged",        flagged_n)
        c4.metric("Avg Risk Score", f"{avg_score:.2f}")
        st.divider()
        # Chart: risk scores
        st.markdown('<div class="nh">Payment Risk Scores</div>', unsafe_allow_html=True)
        chart_data = {p.get("payment_id","?"): p.get("risk_score",0)*100 for p in payments}
        st.bar_chart(chart_data, height=180)
        st.markdown('<div class="nh">Transactions</div>', unsafe_allow_html=True)
        for p in sorted(payments, key=lambda x: x.get("risk_score",0), reverse=True):
            score = p.get("risk_score",0); flg = p.get("flagged",False)
            with st.expander(f"{'[HIGH RISK] ' if score>=0.7 else ''}{p.get('payment_id','?')} — {p.get('sender_name','?')} → {p.get('recipient_bank_country','?')} — €{p.get('amount_eur',0):,.0f}"):
                cc1,cc2,cc3 = st.columns(3)
                cc1.markdown(f"**ID:** `{p.get('payment_id','')}`\n**Type:** {p.get('payment_type','')}\n**Amount:** €{p.get('amount_eur',0):,.0f}")
                cc2.markdown(f"**Sender:** {p.get('sender_name','')}\n**Recipient:** {p.get('recipient_name','')}\n**Country:** {p.get('recipient_bank_country','')}")
                cc3.markdown(f"**Risk Score:** `{score:.2f}`")
                cc3.markdown(_scorebar(score*100), unsafe_allow_html=True)
                cc3.markdown(f"**Flagged:** {'Yes' if flg else 'No'}")
                fls = p.get("flags",[])
                if fls: st.markdown("**Flags:** " + " ".join(f'<span class="badge bw">{f}</span>' for f in fls), unsafe_allow_html=True)
    else: st.info("No payments data available.")


# ─── CREDIT & LENDING ───────────────────────────────────────────────────
elif nav == "Credit & Lending":
    _page_header('Credit & Lending', 'Loan portfolio · Credit scoring · DTI ratio · Default risk')
    try:    loans = _load("loans.json")
    except: loans = []
    if loans:
        approved_n = sum(1 for l in loans if l.get("status")=="approved")
        under_rev  = sum(1 for l in loans if l.get("status")=="under_review")
        rejected_n = sum(1 for l in loans if l.get("status")=="rejected")
        total_exp  = sum(l.get("loan_amount_eur",0) for l in loans if l.get("status")=="approved")
        avg_credit = sum(l.get("credit_score",0) for l in loans)/len(loans)
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Approved",       approved_n)
        c2.metric("Under Review",   under_rev)
        c3.metric("Rejected",       rejected_n)
        c4.metric("Exposure",       f"€{total_exp:,.0f}")
        c5.metric("Avg Credit",     f"{avg_credit:.0f}")
        st.divider()
        # Chart: credit scores
        st.markdown('<div class="nh">Credit Score Distribution</div>', unsafe_allow_html=True)
        credit_data = {l.get("loan_id","?"): l.get("credit_score",0) for l in loans}
        st.bar_chart(credit_data, height=160)
        st.markdown('<div class="nh">Loan Portfolio</div>', unsafe_allow_html=True)
        for loan in loans:
            status = loan.get("status",""); rr = loan.get("risk_rating","")
            sc = {"approved":"#10b981","under_review":"#f59e0b","rejected":"#ef4444"}.get(status,"#888")
            with st.expander(f"{loan.get('loan_id','?')} — {loan.get('applicant_name','?')} — €{loan.get('loan_amount_eur',0):,.0f}"):
                cc1,cc2,cc3 = st.columns(3)
                cc1.markdown(f"**ID:** `{loan.get('loan_id','')}`\n**Purpose:** {loan.get('purpose','')}\n**Amount:** €{loan.get('loan_amount_eur',0):,.0f}\n**Term:** {loan.get('term_months',0)} months")
                cc2.markdown(f"**Applicant:** {loan.get('applicant_name','')}\n**Type:** {loan.get('applicant_type','')}\n**Credit Score:** `{loan.get('credit_score',0)}`")
                cc2.markdown(_scorebar(loan.get('credit_score',0), 850), unsafe_allow_html=True)
                cc3.markdown(f"**DTI:** `{loan.get('dti_ratio',0):.2f}`\n**Collateral:** {'Yes' if loan.get('collateral') else 'No'}\n**Risk Rating:** <span style='color:{sc};font-weight:700'>{rr}</span>", unsafe_allow_html=True)
                cc3.markdown(f"**Status:** <span style='color:{sc};font-weight:700'>{status.upper()}</span>", unsafe_allow_html=True)
    else: st.info("No loan data available.")


# ─── IT RISK MONITOR ─────────────────────────────────────────────────────
elif nav == "IT Risk Monitor":
    _page_header('IT Risk Monitor', 'System health · DORA compliance · Incident detection · Predictive risk')
    try:    systems = get_it_systems(TOKEN)
    except: systems = []

    if systems:
        operational = sum(1 for s in systems if s.get("status")=="operational")
        degraded    = sum(1 for s in systems if s.get("status")=="degraded")
        incidents   = sum(1 for s in systems if s.get("status")=="incident")
        avg_cpu     = sum(s.get("cpu",0) for s in systems)/len(systems)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Operational",    operational)
        c2.metric("Degraded",       degraded)
        c3.metric("Incidents",      incidents)
        c4.metric("Avg CPU Usage",  f"{avg_cpu:.0f}%")

        if st.button("Run DORA Risk Analysis (AI)", type="primary", use_container_width=True):
            with st.spinner("Analysing IT infrastructure with Groq/Llama…"):
                try:
                    result = monitor_it_systems(TOKEN)
                    st.session_state.it_monitor_result = result
                    lvl = "critical" if incidents else "warning" if degraded else "success"
                    msg = f"Analysis complete — max risk: {result['max_risk_score']}/100, {result['incident_count']} incidents, {result['degraded_count']} degraded"
                    (st.error if lvl=="critical" else st.warning if lvl=="warning" else st.success)(msg)
                except APIError as e: st.error(e.detail)

        st.divider()
        st.markdown('<div class="nh">System Health Dashboard</div>', unsafe_allow_html=True)

        # Resource usage charts
        col_a, col_b = st.columns(2)
        with col_a:
            cpu_data  = {s.get("system","?"):s.get("cpu",0) for s in systems}
            st.markdown("**CPU Usage (%)**")
            st.bar_chart(cpu_data, height=180)
        with col_b:
            mem_data  = {s.get("system","?"):s.get("memory",0) for s in systems}
            st.markdown("**Memory Usage (%)**")
            st.bar_chart(mem_data, height=180)

        st.divider()
        st.markdown('<div class="nh">System Status Detail</div>', unsafe_allow_html=True)
        for sys in systems:
            status = sys.get("status","")
            scls   = _sys_status_class(status)
            tier   = sys.get("dora_tier",2)
            crit   = sys.get("criticality","MEDIUM")
            with st.expander(f"[DORA Tier {tier}] {sys.get('system','')} — {status.upper()}"):
                cc1,cc2,cc3 = st.columns(3)
                cc1.markdown(f"**Status:** <span class='{scls}'>{status.upper()}</span>", unsafe_allow_html=True)
                cc1.markdown(f"**Criticality:** {crit}")
                cc1.markdown(f"**Region:** {sys.get('region','')}")
                cc1.markdown(f"**Last Incident:** {sys.get('last_incident','')}")
                cc2.markdown(_gauge(sys.get("cpu",0),"CPU Usage"), unsafe_allow_html=True)
                cc2.markdown(_gauge(sys.get("memory",0),"Memory Usage"), unsafe_allow_html=True)
                cc3.markdown(f"**Latency:** `{sys.get('latency_ms',0)} ms`")
                cc3.markdown(f"**Error Rate:** `{sys.get('error_rate',0)}%`")
                cc3.markdown(f"**Uptime:** `{sys.get('uptime_pct',0)}%`")
                if sys.get("status") in ("degraded","incident"):
                    st.warning(f"DORA Alert: This system requires immediate attention per DORA Art.17.")

        if st.session_state.it_monitor_result:
            res = st.session_state.it_monitor_result
            st.divider()
            st.markdown('<div class="nh">AI Risk Analysis</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:13px;color:#8899aa;line-height:1.7;white-space:pre-wrap">{res.get("analysis","—")}</div>', unsafe_allow_html=True)
            if res.get("requires_human") and res.get("decision_id"):
                hitl_panel(res["decision_id"], "it_monitor")


# ─── DORA RESILIENCE ─────────────────────────────────────────────────────
elif nav == "DORA Resilience":
    _page_header('DORA Resilience Dashboard', 'Digital Operational Resilience Act compliance · ICT risk management · Continuity')

    dora_articles = [
        {"art":"Art. 5","title":"ICT Risk Management Framework","status":"COMPLIANT","score":92,
         "detail":"Comprehensive ICT risk management framework documented. Annual review process in place. Board-level oversight confirmed."},
        {"art":"Art. 8","title":"ICT Asset Identification","status":"COMPLIANT","score":88,
         "detail":"Full IT asset inventory maintained. Critical systems classified by DORA tier. Dependencies mapped."},
        {"art":"Art. 11","title":"ICT Business Continuity","status":"PARTIAL","score":71,
         "detail":"BCP exists but Client Portal recovery time objective (RTO) of 4h exceeds DORA requirement of 2h for Tier 1 services."},
        {"art":"Art. 17","title":"ICT Incident Management","status":"COMPLIANT","score":95,
         "detail":"Incident detection, classification and escalation procedures operational. Current Client Portal incident being managed."},
        {"art":"Art. 25","title":"Digital Resilience Testing","status":"NON_COMPLIANT","score":45,
         "detail":"Penetration testing last conducted 18 months ago. DORA requires annual TLPT for critical systems. Overdue."},
        {"art":"Art. 28","title":"ICT Third-Party Risk Management","status":"PARTIAL","score":68,
         "detail":"3 of 7 critical third-party ICT providers have complete DORA-compliant contracts. CloudCore Inc contract under renegotiation."},
    ]

    compliant = sum(1 for a in dora_articles if a["status"]=="COMPLIANT")
    partial   = sum(1 for a in dora_articles if a["status"]=="PARTIAL")
    non_comp  = sum(1 for a in dora_articles if a["status"]=="NON_COMPLIANT")
    avg_score = sum(a["score"] for a in dora_articles)/len(dora_articles)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Compliant",      compliant)
    c2.metric("Partial",        partial)
    c3.metric("Non-Compliant",  non_comp)
    c4.metric("Overall Score",  f"{avg_score:.0f}/100")

    st.divider()
    # Compliance score chart
    st.markdown('<div class="nh">Compliance Score by Article</div>', unsafe_allow_html=True)
    chart_data = {f"{a['art']}": a["score"] for a in dora_articles}
    st.bar_chart(chart_data, height=200)
    st.divider()

    st.markdown('<div class="nh">Article Status</div>', unsafe_allow_html=True)
    for art in dora_articles:
        sc_map  = {"COMPLIANT":"ba","PARTIAL":"bw","NON_COMPLIANT":"bc"}
        ic_map  = {"COMPLIANT":"10b981","PARTIAL":"f59e0b","NON_COMPLIANT":"ef4444"}
        cls     = sc_map.get(art["status"],"bl")
        col_ic  = ic_map.get(art["status"],"888")
        with st.expander(f"{art['art']} — {art['title']}"):
            cc1,cc2 = st.columns([3,2])
            with cc1:
                st.markdown(f'<span class="badge {cls}">{art["status"]}</span>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:13px;color:#8899aa;margin-top:10px;line-height:1.6">{art["detail"]}</div>', unsafe_allow_html=True)
            with cc2:
                st.markdown(f'<div style="font-size:32px;font-weight:700;font-family:JetBrains Mono,monospace;color:#{col_ic}">{art["score"]}<span style="font-size:14px;color:#5a7a9a">/100</span></div>', unsafe_allow_html=True)
                st.markdown(_scorebar(art["score"]), unsafe_allow_html=True)


# ─── LEGAL REVIEW ────────────────────────────────────────────────────────
elif nav == "Legal Review":
    _page_header('Legal Document Review', 'AI-assisted regulatory compliance · Risk assessment · GDPR · DORA · Basel IV')
    try:    docs = get_legal_documents(TOKEN)
    except: docs = []

    high_n = sum(1 for d in docs if d.get("risk_level")=="HIGH")
    med_n  = sum(1 for d in docs if d.get("risk_level")=="MEDIUM")
    low_n  = sum(1 for d in docs if d.get("risk_level")=="LOW")
    pend_n = sum(1 for d in docs if d.get("status")=="pending_review")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Documents", len(docs))
    c2.metric("High Risk",       high_n)
    c3.metric("Pending Review",  pend_n)
    c4.metric("Approved",        sum(1 for d in docs if d.get("status")=="approved"))

    st.divider()

    # Risk distribution chart
    if docs:
        st.markdown('<div class="nh">Risk Distribution</div>', unsafe_allow_html=True)
        st.bar_chart({"HIGH":high_n,"MEDIUM":med_n,"LOW":low_n}, height=150)
    st.divider()

    col_l, col_r = st.columns([5,5], gap="large")
    with col_l:
        st.markdown('<div class="nh">Document Queue</div>', unsafe_allow_html=True)
        for doc in sorted(docs, key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x.get("risk_level","LOW"),2)):
            rl  = doc.get("risk_level","LOW")
            cls = {"HIGH":"bc","MEDIUM":"bmed","LOW":"bl"}.get(rl,"bl")
            st.markdown(f"""<div class='nc' style='padding:13px 17px;margin-bottom:7px'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start'>
              <div>
                <div style='font-size:13px;font-weight:600'>{doc.get('id')} — {doc.get('title','')[:45]}{'…' if len(doc.get('title',''))>45 else ''}</div>
                <div style='font-size:11px;color:#4a6a8a;margin-top:3px'>{doc.get('counterparty','')} · {doc.get('jurisdiction','')} · {doc.get('pages')} pages</div>
                <div style='font-size:10px;color:#3a5a7a;margin-top:2px'>{' · '.join(doc.get('regulatory_tags',[]))}</div>
              </div>
              <span class='badge {cls}'>{rl}</span>
            </div>
            </div>""", unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="nh">AI Document Analysis</div>', unsafe_allow_html=True)
        doc_ids = [d.get("id","") for d in docs]
        sel_doc = st.selectbox("Select Document", doc_ids, key="legal_sel", label_visibility="collapsed")

        if st.button("Analyse with AI", type="primary", use_container_width=True):
            with st.spinner(f"Analysing {sel_doc} with Groq/Llama…"):
                try:
                    r = review_legal_document(TOKEN, sel_doc)
                    st.session_state.legal_results[sel_doc] = r
                except APIError as e: st.error(e.detail)

        if st.button("Analyse All Documents", use_container_width=True):
            with st.spinner("Running batch legal review…"):
                try:
                    res = review_all_legal_documents(TOKEN)
                    for r in res.get("results",[]): st.session_state.legal_results[r.get("doc_id","")] = r
                    st.success(f"{res['total']} documents — {res['high_risk']} high risk.")
                except APIError as e: st.error(e.detail)

        if sel_doc in st.session_state.legal_results:
            r = st.session_state.legal_results[sel_doc]
            rl  = r.get("risk_level","LOW")
            cls = {"HIGH":"bc","MEDIUM":"bmed","LOW":"bl"}.get(rl,"bl")
            st.markdown(f"""<div class='nc'>
            <div style='font-size:13px;font-weight:600'>{r.get('title','')}</div>
            <div style='margin:8px 0'>
              <span class='badge {cls}'>{rl} RISK</span>
              <span style='font-size:11px;color:#4a6a8a;margin-left:8px'>Score: {r.get('risk_score',0)}/100</span>
            </div>
            {_scorebar(r.get('risk_score',0))}
            <div style='font-size:11px;color:#4a6a8a;margin-top:6px'>Frameworks: {', '.join(r.get('frameworks',[]))}</div>
            </div>""", unsafe_allow_html=True)
            with st.expander("Full Legal Analysis", expanded=True):
                st.markdown(f'<div style="font-size:13px;color:#8899aa;line-height:1.7;white-space:pre-wrap">{r.get("analysis","—")}</div>', unsafe_allow_html=True)
            if r.get("requires_human") and r.get("decision_id"):
                hitl_panel(r["decision_id"], f"legal_{sel_doc}")


# ─── LEGAL GOVERNANCE (read-only for compliance_officer) ─────────────────
elif nav == "Legal Governance":
    _page_header('Legal & Regulatory Governance', 'EU AI Act · AML 6AMLD · GDPR · DORA · MiFID II · Compliance framework')
    regulations = [
        {"name":"EU AI Act 2024","status":"COMPLIANT","articles":["Art. 9 — Risk management","Art. 10 — Data governance","Art. 13 — Transparency","Art. 14 — Human oversight (HITL)","Art. 17 — Quality management"],"desc":"NORDA operates as a high-risk AI system with mandatory human oversight, full audit trails, and explainable decisions."},
        {"name":"AML 6th Directive","status":"COMPLIANT","articles":["Art. 1 — Predicate offences","Art. 6 — Aiding & abetting","Art. 20 — PEP due diligence","Art. 36 — SAR reporting"],"desc":"Full AML pipeline with transaction monitoring, sanctions screening, PEP verification, and automated SAR generation."},
        {"name":"GDPR (2016/679)","status":"COMPLIANT","articles":["Art. 5 — Processing principles","Art. 22 — Automated decisions","Art. 25 — Privacy by design","Art. 30 — Processing records"],"desc":"All AI decisions include human review capability. Data minimisation enforced. Audit log provides processing records."},
        {"name":"DORA","status":"MONITORING","articles":["Art. 5 — ICT risk management","Art. 11 — Backup & recovery","Art. 17 — Incident management","Art. 25 — Resilience testing"],"desc":"SOC monitors operational threats. Incident detection pipeline active. Resilience testing schedule overdue for review."},
        {"name":"MiCA","status":"PLANNED","articles":["Art. 16 — Authorization","Art. 45 — Transaction monitoring"],"desc":"Crypto-asset transaction monitoring module planned for Q3 2026."},
    ]
    for reg in regulations:
        sc_map = {"COMPLIANT":"ba","MONITORING":"bm","PLANNED":"bw","NON_COMPLIANT":"bc"}
        cls    = sc_map.get(reg["status"],"bl")
        with st.expander(f"{reg['name']} — {reg['status']}"):
            cc1,cc2 = st.columns([6,4])
            with cc1:
                st.markdown(f'<span class="badge {cls}">{reg["status"]}</span>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:13px;color:#8899aa;margin-top:10px;line-height:1.6">{reg["desc"]}</div>', unsafe_allow_html=True)
            with cc2:
                st.markdown("**Key Articles**")
                for art in reg["articles"]:
                    st.markdown(f'<div style="font-size:12px;color:#5a7a9a;padding:2px 0">· {art}</div>', unsafe_allow_html=True)


# ─── AUDIT LOG ────────────────────────────────────────────────────────────
elif nav == "Audit Log":
    _page_header('Immutable Audit Log', 'SHA-256 hash-chained · Every decision traceable · Tamper-evident')
    try:    entries = get_audit_log(TOKEN)
    except APIError as e:
        st.error(f"Failed to load audit log: {e.detail}"); entries = []

    approved = sum(1 for e in entries if e.get("decision") in ("CLEAN","COLLECTED","APPROVE","AUTO_APPROVED","RESPONDED"))
    rejected = sum(1 for e in entries if e.get("decision") in ("REJECTED","BLOCKED","INJECTION_DETECTED","CRITICAL_ESCALATION"))
    try:    pending = len(get_pending(TOKEN))
    except: pending = 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Entries",      len(entries))
    c2.metric("Approved / Clear",   approved)
    c3.metric("Rejected / Blocked", rejected)
    c4.metric("Pending HITL",       pending)

    st.divider()
    if st.button("Verify Chain Integrity", type="primary"):
        with st.spinner("Verifying SHA-256 hash chain…"):
            try:
                chain  = verify_chain(TOKEN)
                all_ok = all(r["valid"] for r in chain)
                if all_ok: st.success(f"All {len(chain)} entries verified — chain intact.")
                else:      st.error(f"TAMPERED — {sum(1 for r in chain if not r['valid'])} entries failed!")
                for r in chain:
                    icon = "OK" if r["valid"] else "FAIL"
                    st.markdown(f'`{icon}` **#{r["index"]+1}** `{r["entry_id"][:14]}` · `{r["agent_id"]}` · <span class="hm">{r["current_hash"][:16]}</span>', unsafe_allow_html=True)
            except APIError as e: st.error(e.detail)

    st.divider()
    domain_filter = st.multiselect("Filter by Domain", ["AML","KYC","FRAUD","SOC","INSIDER","CHAT","RISK","IT","LEGAL"], default=[])
    st.markdown('<div class="nh">Decision History</div>', unsafe_allow_html=True)

    if not entries:
        st.markdown('<div class="nc" style="text-align:center;color:#3a5a7a;padding:30px">No audit entries yet — run agent scans.</div>', unsafe_allow_html=True)
    else:
        filtered = [e for e in reversed(entries) if not domain_filter or e.get("domain","") in domain_filter]
        for entry in filtered:
            dom      = entry.get("domain","?")
            decision = entry.get("decision","?")
            dom_cols = {"AML":"#0066ff","KYC":"#9900cc","FRAUD":"#f97316","SOC":"#aa00ff",
                        "INSIDER":"#ef4444","CHAT":"#10b981","RISK":"#3b82f6","IT":"#06b6d4","LEGAL":"#8b5cf6"}
            dc = "#ef4444" if decision in ("REJECTED","BLOCKED","INJECTION_DETECTED","CRITICAL_ESCALATION") else \
                 "#f59e0b" if decision in ("SUSPICIOUS","WAITING_HUMAN_APPROVAL","MONITOR_ONLY") else "#10b981"
            dom_c = dom_cols.get(dom,"#446688")

            with st.expander(f"[{entry.get('timestamp','')[:19]}]  {entry.get('agent_id','')}  —  {entry.get('action','')}"):
                cc1,cc2,cc3 = st.columns(3)
                cc1.markdown(f"**Entry** `{entry.get('entry_id','')[:14]}…`")
                cc1.markdown(f"<span style='background:{dom_c};color:#fff;padding:2px 7px;border-radius:8px;font-size:10px'>{dom}</span>", unsafe_allow_html=True)
                cc2.markdown(f"**Agent** `{entry.get('agent_id','')}`")
                cc2.markdown(f"**Model** `{entry.get('llm_model','N/A')}`")
                cc3.markdown(f"**Decision** <span style='color:{dc};font-weight:700'>{decision}</span>", unsafe_allow_html=True)
                cc3.markdown(f"**Score** `{entry.get('risk_score','—')}`")
                cc3.markdown(f"**HITL** {'Yes' if entry.get('requires_human') else 'No'}")

                ph = entry.get("previous_entry_hash","GENESIS")
                ch = entry.get("current_entry_hash","")
                h1,h2 = st.columns(2)
                h1.markdown(f"Prev: <span class='hm'>{ph[:16] if ph!='GENESIS' else 'GENESIS'}</span>", unsafe_allow_html=True)
                h2.markdown(f"Curr: <span class='hm'>{ch[:16]}</span>", unsafe_allow_html=True)

                # Use columns instead of nested expander (avoids Streamlit bug)
                st.markdown("**Input / Output Snapshots**")
                snap_c1, snap_c2 = st.columns(2)
                with snap_c1:
                    st.caption("Input")
                    st.json(entry.get("input_snapshot",{}))
                with snap_c2:
                    st.caption("Output")
                    st.json(entry.get("output_snapshot",{}))




# ─── SECURITY POSTURE ─────────────────────────────────────────────────────
elif nav == "Security Posture":
    _page_header('Security Posture', '7-layer defence model · Zero-trust architecture · Real-time threat surface')
    layers = [
        {"name":"Prompt Injection Shield",    "score":98, "status":"SECURE",    "detail":"12 injection patterns blocked before LLM processing. All inputs sanitised."},
        {"name":"JWT Zero-Trust Auth",        "score":99, "status":"SECURE",    "detail":"HS256 JWT tokens. bcrypt-12 password hashing. 8-hour token expiry enforced."},
        {"name":"RBAC Permissions",           "score":95, "status":"SECURE",    "detail":"7 roles: admin, compliance_officer, analyst, soc_analyst, auditor, it_officer, legal_counsel."},
        {"name":"Agent Governance Validator", "score":91, "status":"SECURE",    "detail":"Action whitelist per agent. 6-rule Zero Trust enforcement. Duplicate action prevention."},
        {"name":"Adaptive Decision Engine",   "score":88, "status":"ACTIVE",    "detail":"4-tier risk scoring 0–100. Automated HITL escalation. Domain-specific evaluators."},
        {"name":"Immutable Audit Chain",      "score":100,"status":"SECURE",    "detail":"SHA-256 hash-chained log. Every decision timestamped and signed. Tamper-evident."},
        {"name":"SOC Threat Detection",       "score":82, "status":"MONITORING","detail":"Real-time brute force, exfiltration and insider threat detection. Groq AI analysis."},
    ]
    overall = sum(l["score"] for l in layers)/len(layers)
    c1,c2,c3 = st.columns(3)
    c1.metric("Overall Score",    f"{overall:.1f}/100")
    c2.metric("Secure Layers",    sum(1 for l in layers if l["status"]=="SECURE"))
    c3.metric("Monitoring",       sum(1 for l in layers if l["status"] in ("ACTIVE","MONITORING")))

    # Score chart
    st.divider()
    st.markdown('<div class="nh">Layer Scores</div>', unsafe_allow_html=True)
    chart_data = {l["name"][:22]:l["score"] for l in layers}
    st.bar_chart(chart_data, height=200)
    st.divider()

    st.markdown('<div class="nh">Defence Layers</div>', unsafe_allow_html=True)
    for i, layer in enumerate(layers):
        score  = layer["score"]; status = layer["status"]
        col_v  = "#10b981" if status=="SECURE" else "#3b82f6" if status=="ACTIVE" else "#f59e0b"
        sc_cls = {"SECURE":"ba","ACTIVE":"bm","MONITORING":"bw"}.get(status,"bm")
        st.markdown(f"""
        <div class='nc' style='padding:15px 19px'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:7px'>
            <span style='font-size:13px;font-weight:600'>Layer {i+1} — {layer["name"]}</span>
            <div style='display:flex;align-items:center;gap:10px'>
              <span style='font-family:JetBrains Mono,monospace;font-size:13px;color:{col_v};font-weight:700'>{score}/100</span>
              <span class='badge {sc_cls}'>{status}</span>
            </div>
          </div>
          {_scorebar(score)}
          <div style='font-size:12px;color:#4a6a8a;margin-top:7px'>{layer["detail"]}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="nh">Zero-Trust Principles</div>', unsafe_allow_html=True)
    for title, desc in [
        ("Never trust, always verify",   "Every API call requires a valid JWT token regardless of origin."),
        ("Least-privilege access",        "7 RBAC roles. Each role sees only its permitted endpoints and data."),
        ("Assume breach posture",         "All decisions logged. Hash-chain ensures forensic integrity."),
        ("AI decisions are never final",  "HITL queue for all high-risk decisions. Human always in the loop."),
        ("Defence in depth",              "7 independent security layers. Compromise of one does not cascade."),
    ]:
        st.markdown(f'<div style="padding:9px 0;border-bottom:1px solid rgba(0,212,170,0.06)"><div style="font-size:13px;font-weight:600">{title}</div><div style="font-size:12px;color:#4a6a8a;margin-top:2px">{desc}</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ─── CHAT DIALOG (opened by FAB) ──────────────────────────────────────
_role_suggestions = {
    "compliance_officer": [
        "Show me the highest risk AML transactions",
        "What does WAITING_HUMAN_APPROVAL mean?",
        "Explain the KYC risk tier system",
        "What is smurfing and how is it detected?",
        "When should I escalate to authorities?",
    ],
    "it_officer": [
        "Which IT systems are currently at risk?",
        "What does DORA Article 17 require?",
        "What is the DORA TLPT testing requirement?",
        "Explain ICT continuity requirements",
    ],
    "legal_counsel": [
        "What are the key risks in a DORA ICT contract?",
        "Explain Basel IV output floor requirements",
        "What GDPR clauses are mandatory in a DPA?",
    ],
    "soc_analyst": [
        "What is impossible travel and why is it suspicious?",
        "What triggers a CRITICAL_ESCALATION in SOC?",
        "What actions should I take for a data exfiltration alert?",
    ],
    "admin": [
        "Give me a full platform overview",
        "Explain the Zero Trust security architecture",
        "How does the SHA-256 hash chain work?",
        "What are all the user roles and permissions?",
    ],
}

@st.dialog("NORDA AI Assistant", width="large")
def _chat_dialog():
    # Reset flag at dialog start so closing via X doesn't reopen
    st.session_state.chat_open = False

    _name = st.session_state.operator_name or "Operator"
    _role = st.session_state.operator_role or "analyst"
    _dept = st.session_state.operator_dept or ""

    # Logo + header inside dialog
    if _LOGO:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">'
            f'<img src="data:image/jpeg;base64,{_LOGO}" style="width:32px;height:32px;object-fit:contain">'
            f'<span style="font-size:13px;color:#5a7a9a">Groq · Llama-3.3-70b · {_name} · {_dept}</span></div>',
            unsafe_allow_html=True,
        )

    # Chat history
    chat_area = st.container(height=340)
    with chat_area:
        if not st.session_state.chat_history:
            st.markdown(
                f'<div style="text-align:center;padding:48px 0;color:#3a5a7a">'
                f'<div style="font-size:32px;margin-bottom:8px">◎</div>'
                f'<div>Ask me anything, {_name}.</div></div>',
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

    # Suggested questions (collapsed)
    suggestions = _role_suggestions.get(_role, _role_suggestions["admin"])
    with st.expander("Quick questions"):
        for s in suggestions:
            if st.button(s, key=f"dlg_sug_{s[:20]}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": s})
                with st.spinner("Thinking…"):
                    try:    reply = send_chat(TOKEN, st.session_state.chat_history)
                    except APIError as e: reply = f"Error: {e.detail}"
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.session_state.chat_open = True
                st.rerun()

    # Input row
    col_inp, col_send, col_clr = st.columns([7, 2, 1])
    with col_inp:
        user_msg = st.text_input("msg", placeholder="Ask about your domain…",
                                 label_visibility="collapsed", key="chat_dlg_input")
    with col_send:
        if st.button("Send", type="primary", use_container_width=True, key="chat_dlg_send"):
            if user_msg.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                with st.spinner("Thinking…"):
                    try:    reply = send_chat(TOKEN, st.session_state.chat_history)
                    except APIError as e: reply = f"Error: {e.detail}"
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.session_state.chat_open = True
                st.rerun()
    with col_clr:
        if st.button("✕", key="chat_dlg_clear", help="Clear history"):
            st.session_state.chat_history = []
            st.session_state.chat_open = True
            st.rerun()


# ── Hidden Streamlit trigger (manages session state when FAB is clicked) ──────
_fab_clicked = st.button("NORDACHATFAB", key="chat_fab_trigger")
if _fab_clicked:
    st.session_state.chat_open = True
    st.rerun()

# Open the chat dialog when triggered
if st.session_state.get("chat_open"):
    _chat_dialog()

# ── Floating AI Assistant button — implemented as a real iframe component ─────
# The iframe:
#   1. Self-positions to fixed bottom-right via window.frameElement
#   2. Renders the visual NORDA circle button
#   3. Hides the NORDACHATFAB Streamlit button in the parent document (same origin)
#   4. Clicks NORDACHATFAB programmatically when the circle is pressed
_logo_img = (
    f'<img src="data:image/jpeg;base64,{_LOGO}" '
    f'style="width:34px;height:34px;object-fit:contain;pointer-events:none">'
    if _LOGO else
    '<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="#fff" stroke-width="2" style="pointer-events:none">'
    '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
)

_components.html(f"""<!DOCTYPE html>
<html>
<head>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:transparent;overflow:hidden;width:62px;height:62px}}
#fab{{
    width:62px;height:62px;border-radius:50%;
    background:linear-gradient(135deg,#00d4aa 0%,#0055cc 100%);
    border:none;cursor:pointer;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 4px 24px rgba(0,212,170,0.55),0 2px 8px rgba(0,0,0,0.35);
    transition:transform .18s ease,box-shadow .18s ease;
    animation:pulse 3s ease-in-out infinite;
    position:relative;
}}
#fab:hover{{transform:scale(1.12);box-shadow:0 8px 32px rgba(0,212,170,0.7)}}
#tip{{
    position:absolute;bottom:70px;right:0;
    background:rgba(10,22,40,0.95);color:#00d4aa;
    font-family:Inter,sans-serif;font-size:11px;font-weight:600;
    letter-spacing:.05em;padding:5px 11px;border-radius:8px;
    white-space:nowrap;border:1px solid rgba(0,212,170,0.3);
    display:none;pointer-events:none;
}}
@keyframes pulse{{0%,100%{{opacity:1;box-shadow:0 4px 24px rgba(0,212,170,0.55)}}50%{{opacity:0.88;box-shadow:0 4px 32px rgba(0,212,170,0.8)}}}}
</style>
</head>
<body>
<button id="fab"
    onmouseenter="document.getElementById('tip').style.display='block'"
    onmouseleave="document.getElementById('tip').style.display='none'"
    onclick="openChat()"
    title="NORDA AI Assistant">
  {_logo_img}
  <span id="tip">NORDA Assistant</span>
</button>
<script>
// 1. Self-position this iframe as a fixed element at bottom-right
(function(){{
    try{{
        var f=window.frameElement;
        if(f){{
            f.style.cssText=[
                'position:fixed','bottom:24px','right:24px',
                'width:62px','height:62px','border:none',
                'background:transparent','z-index:99999',
                'border-radius:50%','overflow:visible'
            ].join('!important;')+'!important';
        }}
    }}catch(e){{}}
}})();

// 2. Hide the NORDACHATFAB Streamlit button in the parent document
function hideCHATFAB(){{
    try{{
        var ps=window.parent.document.querySelectorAll('[data-testid="stButton"] button p');
        for(var i=0;i<ps.length;i++){{
            if(ps[i].textContent.trim()==='NORDACHATFAB'){{
                var w=ps[i].closest('[data-testid="stButton"]');
                if(w)w.style.cssText='display:none!important;height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;';
            }}
        }}
    }}catch(e){{}}
}}
hideCHATFAB();
[100,300,700,1500,3000].forEach(function(ms){{setTimeout(hideCHATFAB,ms);}});
try{{new MutationObserver(hideCHATFAB).observe(window.parent.document.body,{{childList:true,subtree:true}});}}catch(e){{}}

// 3. Click the hidden NORDACHATFAB button to open the chat dialog
function openChat(){{
    try{{
        var ps=window.parent.document.querySelectorAll('[data-testid="stButton"] button p');
        for(var i=0;i<ps.length;i++){{
            if(ps[i].textContent.trim()==='NORDACHATFAB'){{
                ps[i].closest('button').click();return;
            }}
        }}
    }}catch(e){{console.error('FAB click error',e);}}
}}
</script>
</body>
</html>""", height=1, scrolling=False)
