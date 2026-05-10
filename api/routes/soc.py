"""
/api/soc — SOC (Security Operations Center) endpoints.
"""
import json, os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import require_permission
from agents.soc_agent import run_soc_agent
from agents.insider_threat_agent import run_insider_threat_agent

router = APIRouter()
_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _load(filename):
    with open(os.path.join(_DATA, filename)) as f:
        return json.load(f)


class SOCAnalyzeRequest(BaseModel):
    event: dict


@router.get("/events")
def get_soc_events(claims: dict = Depends(require_permission("soc"))):
    try:
        return _load("soc_events.json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employees")
def get_employees(claims: dict = Depends(require_permission("soc"))):
    try:
        return _load("employees.json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
def analyze_soc_event(req: SOCAnalyzeRequest, claims: dict = Depends(require_permission("soc"))):
    try:
        result = run_soc_agent(req.event)
        result["analyzed_by"] = claims["sub"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-all")
def analyze_all_soc_events(claims: dict = Depends(require_permission("soc"))):
    try:
        events = _load("soc_events.json")
        results = [run_soc_agent(e) for e in events]
        critical = sum(1 for r in results if r["decision"] == "CRITICAL_ESCALATION")
        waiting  = sum(1 for r in results if r["decision"] == "WAITING_HUMAN_APPROVAL")
        return {
            "total":    len(results),
            "critical": critical,
            "waiting":  waiting,
            "results":  results,
            "analyzed_by": claims["sub"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insider-threat/{employee_id}")
def analyze_insider_threat(employee_id: str, claims: dict = Depends(require_permission("soc"))):
    try:
        employees  = _load("employees.json")
        soc_events = _load("soc_events.json")
        employee   = next((e for e in employees if e["id"] == employee_id), None)
        if not employee:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found.")
        result = run_insider_threat_agent(employee, soc_events)
        result["analyzed_by"] = claims["sub"]
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insider-threat-all")
def analyze_all_insider_threats(claims: dict = Depends(require_permission("soc"))):
    try:
        employees  = _load("employees.json")
        soc_events = _load("soc_events.json")
        results    = [run_insider_threat_agent(e, soc_events) for e in employees]
        return {
            "total":   len(results),
            "results": results,
            "analyzed_by": claims["sub"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
