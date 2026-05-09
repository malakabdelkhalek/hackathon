"""
/api/audit — Audit log retrieval and chain verification.
Read-only for operators; verify endpoint open to all authenticated users.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, List, Optional

from api.auth import verify_token
import governance.audit_log as audit_log

router = APIRouter()


class AuditEntry(BaseModel):
    entry_id: str
    timestamp: str
    agent_id: str
    agent_version: str
    domain: str
    action: str
    input_snapshot: dict
    output_snapshot: Any
    llm_model: str
    risk_score: Optional[float]
    decision: str
    requires_human: bool
    previous_entry_hash: str
    current_entry_hash: str


class ChainVerifyResult(BaseModel):
    index: int
    entry_id: str
    agent_id: str
    action: str
    valid: bool
    hash_match: bool
    chain_intact: bool
    current_hash: str


@router.get("/log", response_model=List[AuditEntry])
def get_log(claims: dict = Depends(verify_token)):
    return audit_log.get_all_entries()


@router.get("/verify", response_model=List[ChainVerifyResult])
def verify_chain(claims: dict = Depends(verify_token)):
    return audit_log.verify_chain_integrity()
