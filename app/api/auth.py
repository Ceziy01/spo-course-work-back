from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from schemas.auth import Token, CreateUserRequest, UsersMe
from core.dependencies import get_db, get_current_user
from services.auth_service import authenticate_user, create_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/", status_code=201)
def register(
    request: CreateUserRequest,
    db: Annotated[Session, Depends(get_db)]
):
    create_user(request.username, request.password, False, db)
    return {"message": "User created"}


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = login_user(user, db)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/users/me", response_model=UsersMe)
def me(user=Depends(get_current_user)):
    return {
        "username": user.username,
        "is_admin": user.is_admin
    }