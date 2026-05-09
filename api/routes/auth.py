"""
/auth — token issuance endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.auth import authenticate_operator, create_access_token

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    operator: str
    role: str
    expires_in_hours: int


@router.post("/token", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    """Issue a signed JWT. Used by the dashboard and any external client."""
    op = authenticate_operator(form.username, form.password)
    if not op:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(op["username"], op["role"], op["full_name"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        operator=op["full_name"],
        role=op["role"],
        expires_in_hours=8,
    )
