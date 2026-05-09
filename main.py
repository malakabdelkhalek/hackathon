"""
SENTINEL — Main Entry Point
HACK'N'BIZ 2026 | NORDA Bank Challenge
Starts FastAPI (port 8000) then Streamlit (port 8501).
"""
import os
import subprocess
import sys
import threading
import time

from dotenv import load_dotenv
load_dotenv()

BANNER = r"""
███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝

  NORDA Bank Autonomous Compliance System
  HACK'N'BIZ 2026 — Fortum Junior Entreprise
"""


def check_api_key():
    key = os.environ.get("GROQ_API_KEY", "")
    if not key or key == "placeholder_replace_with_real_key":
        print("ERROR: GROQ_API_KEY is not set or still placeholder.")
        print("  1. Get a free key at https://console.groq.com/keys")
        print("  2. Set it in .env: GROQ_API_KEY=your_key_here")
        return False
    print(f"  [OK] GROQ_API_KEY loaded (ends with …{key[-6:]})")

    xai_key = os.environ.get("XAI_API_KEY", "")
    if not xai_key or xai_key == "your_xai_api_key_here":
        print("  [WARN] XAI_API_KEY not set — AI Assistant will be unavailable.")
        print("         Get your key at: https://console.x.ai")
    else:
        print(f"  [OK] XAI_API_KEY loaded (ends with …{xai_key[-6:]})")
    return True


def ensure_rag_setup():
    chroma_path = os.path.join(os.path.dirname(__file__), "chroma_db")
    if not os.path.exists(chroma_path):
        print("\n  ChromaDB not found. Running RAG setup...")
        setup_path = os.path.join(os.path.dirname(__file__), "rag", "setup.py")
        result = subprocess.run([sys.executable, setup_path])
        if result.returncode != 0:
            print("  ERROR: RAG setup failed. Check rag/setup.py.")
            sys.exit(1)
        print("  [OK] RAG setup complete.")
    else:
        print("  [OK] ChromaDB found.")


def start_api_server():
    """Run FastAPI with uvicorn in a daemon thread."""
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        log_level="warning",
        access_log=False,
    )


def wait_for_api(timeout: int = 15) -> bool:
    """Poll until the API responds or timeout."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://localhost:8000/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    print(BANNER)
    print("Initializing SENTINEL...\n")

    if not check_api_key():
        sys.exit(1)

    ensure_rag_setup()

    print("\n  Starting FastAPI backend on port 8000...")
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    if wait_for_api():
        print("  [OK] API server ready at http://localhost:8000")
        print("       Swagger docs: http://localhost:8000/docs")
    else:
        print("  WARNING: API server did not respond in time — continuing anyway.")

    print("\n  Starting Streamlit dashboard on port 8501...")
    print("  Login page:  http://localhost:8000")
    print("  Dashboard:   http://localhost:8501")
    print("  API docs:    http://localhost:8000/docs\n")
    print("=" * 65)
    print("  Demo credentials:")
    print("    operator / sentinel2026      (Compliance Officer)")
    print("    admin    / norda_admin_2026  (Security Admin)")
    print("    analyst  / analyst2026       (Risk Analyst — read-only)")
    print("=" * 65 + "\n")

    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    os.system(f'streamlit run "{dashboard_path}" --server.headless true')


if __name__ == "__main__":
    main()
