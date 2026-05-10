"""
JWT authentication core — bcrypt hashing, RBAC, token creation/validation.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

SECRET_KEY = os.environ.get("SECRET_KEY", "sentinel_secret_jwt_key_2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()


def _verify(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


# Five roles: admin > compliance_officer > analyst / soc_analyst / auditor
# Passwords are bcrypt-hashed — never stored plain-text
USERS = {
    "admin": {
        "username": "admin",
        "password_hash": _hash("norda_admin_2026"),
        "role": "admin",
        "full_name": "System Admin",
        "department": "Operations",
        "initials": "SA",
    },
    "operator": {
        "username": "operator",
        "password_hash": _hash("sentinel2026"),
        "role": "compliance_officer",
        "full_name": "NORDA Compliance Officer",
        "department": "AML & KYC",
        "initials": "CO",
    },
    "analyst": {
        "username": "analyst",
        "password_hash": _hash("analyst2026"),
        "role": "analyst",
        "full_name": "NORDA Risk Analyst",
        "department": "Risk Management",
        "initials": "RA",
    },
    "soc_analyst": {
        "username": "soc_analyst",
        "password_hash": _hash("soc2026"),
        "role": "soc_analyst",
        "full_name": "NORDA SOC Analyst",
        "department": "Security Operations",
        "initials": "SA",
    },
    "auditor": {
        "username": "auditor",
        "password_hash": _hash("audit2026"),
        "role": "auditor",
        "full_name": "NORDA Senior Auditor",
        "department": "Internal Audit",
        "initials": "AU",
    },
    # Named users
    "thomas.martin": {
        "username": "thomas.martin",
        "password_hash": _hash("compliance2026"),
        "role": "compliance_officer",
        "full_name": "Thomas Martin",
        "department": "AML & KYC",
        "initials": "TM",
    },
    "sarah.chen": {
        "username": "sarah.chen",
        "password_hash": _hash("itops2026"),
        "role": "it_officer",
        "full_name": "Sarah Chen",
        "department": "Information Technology",
        "initials": "SC",
    },
    "marc.dubois": {
        "username": "marc.dubois",
        "password_hash": _hash("legal2026"),
        "role": "legal_counsel",
        "full_name": "Marc Dubois",
        "department": "Legal & Regulatory",
        "initials": "MD",
    },
}

ROLE_PERMISSIONS = {
    "admin":              {"scan", "investigate", "kyc", "approve", "audit", "chat", "admin", "soc", "fraud", "risk", "it", "legal"},
    "compliance_officer": {"scan", "investigate", "kyc", "approve", "audit", "chat", "fraud", "risk"},
    "analyst":            {"scan", "investigate", "kyc", "audit", "chat", "risk"},
    "soc_analyst":        {"scan", "audit", "chat", "soc", "fraud", "risk"},
    "auditor":            {"audit", "chat"},
    "it_officer":         {"scan", "audit", "chat", "soc", "risk", "it"},
    "legal_counsel":      {"audit", "chat", "risk", "legal"},
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def authenticate_operator(username: str, password: str) -> Optional[dict]:
    user = USERS.get(username)
    if user and _verify(password, user["password_hash"]):
        return user
    return None


def create_access_token(username: str, role: str, full_name: str) -> str:
    user = USERS.get(username, {})
    payload = {
        "sub": username,
        "role": role,
        "full_name": full_name,
        "department": user.get("department", ""),
        "initials": user.get("initials", full_name[:2].upper() if full_name else "??"),
        "permissions": list(ROLE_PERMISSIONS.get(role, [])),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency — validates JWT and returns claims."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Re-authenticate at /auth/token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise exc
        return payload
    except JWTError:
        raise exc


def verify_token_data(token: str) -> dict:
    """Non-dependency version — for Streamlit URL token validation."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise ValueError("Invalid token")
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")


def require_permission(permission: str):
    """Dependency factory for permission-gated endpoints."""
    def check(claims: dict = Depends(verify_token)) -> dict:
        perms = set(claims.get("permissions", []))
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{claims.get('role')}' does not have '{permission}' permission.",
            )
        return claims
    return check
