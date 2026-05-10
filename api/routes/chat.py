"""
/api/chat — AI Assistant endpoint (Grok-powered, JWT-protected, audit-logged).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from api.auth import require_permission
from dashboard.chatbot import call_grok, TUTORIAL_MESSAGE
import governance.audit_log as audit_log

router = APIRouter()


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    tutorial: bool = False


class ChatResponse(BaseModel):
    reply: str
    logged: bool


@router.post("/message", response_model=ChatResponse)
def chat(req: ChatRequest, claims: dict = Depends(require_permission("chat"))):
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    if req.tutorial:
        messages = [{"role": "user", "content": TUTORIAL_MESSAGE}]

    reply = call_grok(messages)

    audit_log.log_decision(
        agent_id="norda_assistant_v1.0.0",
        domain="CHAT",
        action="ai_assistant_query",
        input_snapshot={
            "user": claims["sub"],
            "role": claims["role"],
            "message_count": len(messages),
            "tutorial": req.tutorial,
            "last_query": messages[-1]["content"][:200] if messages else "",
        },
        output_snapshot={"reply_preview": reply[:300]},
        risk_score=None,
        decision="RESPONDED",
        requires_human=False,
        llm_model="llama-3.3-70b-versatile",
    )

    return ChatResponse(reply=reply, logged=True)
