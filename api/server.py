"""
SENTINEL FastAPI server — Zero Trust REST API with JWT authentication.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.routes import auth, aml, kyc, hitl, audit, chat, fraud, soc, risk, it, legal

app = FastAPI(
    title="NORDA Intelligence Platform",
    description=(
        "NORDA AI Banking Governance, Compliance, SOC & Behavioral Intelligence\n\n"
        "Obtain a JWT via `POST /auth/token`, then send it as `Authorization: Bearer <token>`."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Streamlit dashboard and local dev
_extra = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    *[o.strip() for o in _extra.split(",") if o.strip()],
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router,  prefix="/auth",        tags=["Authentication"])
app.include_router(aml.router,   prefix="/api/aml",     tags=["AML"])
app.include_router(kyc.router,   prefix="/api/kyc",     tags=["KYC"])
app.include_router(hitl.router,  prefix="/api/hitl",    tags=["HITL"])
app.include_router(audit.router, prefix="/api/audit",   tags=["Audit"])
app.include_router(chat.router,  prefix="/api/chat",    tags=["AI Assistant"])
app.include_router(fraud.router, prefix="/api/fraud",   tags=["Fraud Detection"])
app.include_router(soc.router,   prefix="/api/soc",     tags=["SOC"])
app.include_router(risk.router,  prefix="/api/risk",    tags=["Risk Management"])
app.include_router(it.router,    prefix="/api/it",      tags=["IT Risk Monitor"])
app.include_router(legal.router, prefix="/api/legal",   tags=["Legal Review"])


@app.get("/health", tags=["System"])
def health():
    return {"status": "operational", "service": "NORDA Intelligence Platform", "version": "2.0.0"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_login():
    streamlit_url = os.environ.get("STREAMLIT_URL", "http://localhost:8501")
    idx = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
    if os.path.exists(idx):
        with open(idx) as f:
            html = f.read()
        html = html.replace("http://localhost:8501", streamlit_url)
        return html
    return "<h1>NORDA API</h1><p>Visit <a href='/docs'>/docs</a> for the API.</p>"
