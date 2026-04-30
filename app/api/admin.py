from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pathlib import Path
from sqlalchemy.orm import Session
import os, shutil
from datetime import datetime

from core.dependencies import require_admin, get_db
from schemas.auth import CreateUserRequest, UpdateUserRequest
from services.auth_service import create_user
from db.models.user import Users
from core.security import create_access_token, hash_password
from datetime import timedelta
from config import settings
from schemas.auth import ResetPasswordRequest
from db.models.activity_log import ActionType
from services.activity_log import log_action

router = APIRouter(prefix="/auth/admin", tags=["admin"])

@router.get("/")
def admin_panel(admin: Annotated[Users, Depends(require_admin)]):
    return {"message": "Welcome admin"}

@router.post("/create-user", status_code=201)
def admin_create_user(
    request: CreateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)],
    req: Request = None
):
    user = create_user(request.username, request.first_name, request.last_name, request.email, request.password, request.role, db)
    log_action(
        db, admin, ActionType.USER_CREATED,
        entity_type="user", entity_id=user.id,
        entity_name=f"{request.first_name} {request.last_name} ({request.username})",
        ip_address=req.client.host if req else None
    )
    return {"message": "User created"}


@router.get("/users")
def all_users(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)]
):
    users = db.query(Users).all()
    return [
        {"id": u.id, "username": u.username, "first_name": u.first_name, "last_name": u.last_name, "email": u.email, "role": u.role.value}
        for u in users
    ]

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)],
    req: Request = None
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log_action(
        db, admin, ActionType.USER_DELETED,
        entity_type="user", entity_id=user.id,
        entity_name=f"{user.first_name} {user.last_name} ({user.username})",
        ip_address=req.client.host if req else None
    )

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@router.patch("/users/{user_id}")
def admin_update_user(
    user_id: int,
    request: UpdateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)],
    req: Request = None
):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = {}

    if request.username is not None:
        existing = db.query(Users).filter(Users.username == request.username, Users.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        if user.username != request.username:
            changes["username"] = {"old": user.username, "new": request.username}
        user.username = request.username

    if request.first_name is not None:
        if user.first_name != request.first_name:
            changes["first_name"] = {"old": user.first_name, "new": request.first_name}
        user.first_name = request.first_name

    if request.last_name is not None:
        if user.last_name != request.last_name:
            changes["last_name"] = {"old": user.last_name, "new": request.last_name}
        user.last_name = request.last_name

    if request.email is not None:
        existing = db.query(Users).filter(Users.email == request.email, Users.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        if user.email != request.email:
            changes["email"] = {"old": user.email, "new": request.email}
        user.email = request.email

    if request.role is not None:
        if user.role.value != request.role:
            changes["role"] = {"old": user.role.value, "new": request.role}
        user.role = request.role

    db.commit()
    db.refresh(user)

    log_action(
        db, admin, ActionType.USER_UPDATED,
        entity_type="user", entity_id=user.id,
        entity_name=f"{user.first_name} {user.last_name} ({user.username})",
        ip_address=req.client.host if req else None
    )

    return {"message": "User updated"}


@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    request: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)],
    req: Request = None
):
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password too short (min 8 characters)")

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(request.new_password)
    db.commit()

    log_action(
        db, admin, ActionType.USER_PASSWORD_RESET,
        entity_type="user", entity_id=user.id,
        entity_name=f"{user.first_name} {user.last_name} ({user.username})",
        ip_address=req.client.host if req else None
    )

    return {"message": "Password reset successfully"}


@router.post("/impersonate/{user_id}")
def impersonate_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)],
    req: Request = None
):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token(
        username=user.username,
        id=user.id,
        exps=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    log_action(
        db, admin, ActionType.USER_IMPERSONATED,
        entity_type="user", entity_id=user.id,
        entity_name=f"{user.first_name} {user.last_name} ({user.username})",
        ip_address=req.client.host if req else None
    )

    return {"access_token": token, "token_type": "bearer"}

@router.get("/backup")
def backup_database(
    admin: Annotated[Users, Depends(require_admin)]
):
    db_url = settings.DATABASE_URL
    if not db_url.startswith("sqlite:///"):
        raise HTTPException(status_code=500, detail="Резервное копирование поддерживается только для SQLite")

    relative_db_path = db_url[len("sqlite:///"):]
    db_path = Path(relative_db_path)

    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path

    db_path = str(db_path.resolve())

    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail=f"Файл базы данных не найден: {db_path}")

    backups_dir = os.path.join(os.path.dirname(db_path), "backups")
    os.makedirs(backups_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(backups_dir, backup_filename)

    shutil.copy2(db_path, backup_path)

    return {"message": "Бэкап успешно создан", "file": backup_filename}