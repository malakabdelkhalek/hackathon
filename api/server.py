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

from api.routes import auth, aml, kyc, hitl, audit, chat

app = FastAPI(
    title="SENTINEL API",
    description=(
        "NORDA Bank Autonomous Compliance System — Zero Trust REST API.\n\n"
        "Obtain a JWT via `POST /auth/token`, then send it as `Authorization: Bearer <token>`."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Netlify frontend and local dashboard
ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Add your Netlify URL here when deployed:
    # "https://your-app.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router,  prefix="/auth",      tags=["Authentication"])
app.include_router(aml.router,   prefix="/api/aml",   tags=["AML"])
app.include_router(kyc.router,   prefix="/api/kyc",   tags=["KYC"])
app.include_router(hitl.router,  prefix="/api/hitl",  tags=["HITL"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(chat.router,  prefix="/api/chat",  tags=["AI Assistant"])


@app.get("/health", tags=["System"])
def health():
    return {"status": "operational", "service": "SENTINEL API", "version": "1.0.0"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_login():
    """Serve the login page for local development."""
    idx = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
    if os.path.exists(idx):
        with open(idx) as f:
            return f.read()
    return "<h1>SENTINEL API</h1><p>Visit <a href='/docs'>/docs</a> for the API.</p>"
