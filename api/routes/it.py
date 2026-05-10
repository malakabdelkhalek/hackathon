"""
/api/it — IT Risk Monitor endpoints (DORA-aligned).
"""
import json, os
from fastapi import APIRouter, Depends, HTTPException
from api.auth import require_permission
from agents.it_monitor import run_it_monitor_agent

router = APIRouter()
_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load_systems():
    with open(os.path.join(_DATA, "it_systems.json")) as f:
        return json.load(f)


@router.get("/systems")
def get_it_systems(claims: dict = Depends(require_permission("it"))):
    try:
        return _load_systems()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor")
def monitor_all_systems(claims: dict = Depends(require_permission("it"))):
    try:
        systems = _load_systems()
        result  = run_it_monitor_agent(systems)
        result["analyzed_by"] = claims["sub"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
