from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.dependencies import require_admin

from schemas.auth import CreateUserRequest, UsersMe, ChangePasswordRequest, TokenResponse, RefreshRequest
from core.dependencies import get_db, get_current_user
from services.auth_service import authenticate_user, create_user, login_user
from core.security import verify_password, hash_password, create_refresh_token, create_access_token, verify_refresh_token
from db.models.user import Users
from db.models.refresh_token import RefreshToken
from datetime import timedelta
from config import settings
from db.models.activity_log import ActionType
from services.activity_log import log_action

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/", status_code=201)
def register(
    request: CreateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin)]
):
    create_user(request.username, request.first_name, request.last_name, request.email, request.password, request.role, db)
    return {"message": "User created"}


@router.post("/token", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    try:
        user = authenticate_user(form_data.username, form_data.password, db)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        if expire_minutes is None or expire_minutes <= 0:
            raise HTTPException(status_code=500, detail="Server configuration error")

        access_token = create_access_token(
            username=user.username,
            id=user.id,
            exps=timedelta(minutes=expire_minutes)
        )
        refresh_token = create_refresh_token(user.id, db)

        ip_address = request.client.host if request.client else "unknown"
        log_action(
            db, user, ActionType.USER_LOGIN,
            entity_type="user", entity_id=user.id,
            entity_name=f"{user.first_name} {user.last_name} ({user.username})",
            ip_address=ip_address
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise  # не трогаем наши собственные HTTP-исключения
    except Exception as e:
        print("ERROR in /token:", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshRequest,
    db: Annotated[Session, Depends(get_db)]
):
    user_id = verify_refresh_token(data.refresh_token, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(
        username=user.username,
        id=user.id,
        exps=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.query(RefreshToken).filter(RefreshToken.token == data.refresh_token).delete()
    new_refresh_token = create_refresh_token(user.id, db)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/users/me", response_model=UsersMe)
def me(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value
    }

@router.patch("/users/me/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный старый пароль")

    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Пароль должен быть не менее 8 символов")

    current_user.hashed_password = hash_password(request.new_password)
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()
    db.commit()

    log_action(
        db, current_user, ActionType.USER_PASSWORD_CHANGED,
        entity_type="user", entity_id=current_user.id,
        entity_name=f"{current_user.first_name} {current_user.last_name} ({current_user.username})"
    )

    return {"message": "Пароль успешно изменён"}

@router.post("/logout")
def logout(
    refresh_token: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    log_action(
        db, current_user, ActionType.USER_LOGOUT,
        entity_type="user", entity_id=current_user.id,
        entity_name=f"{current_user.first_name} {current_user.last_name} ({current_user.username})"
    )

    db.query(RefreshToken).filter(RefreshToken.token == refresh_token).delete()
    db.commit()
    return {"message": "Logged out"}