from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import require_admin, get_db
from schemas.auth import CreateUserRequest, UpdateUserRequest
from services.auth_service import create_user
from db.models.user import Users

router = APIRouter(prefix="/auth/admin", tags=["admin"])

@router.get("/")
def admin_panel(admin: Annotated[Users, Depends(require_admin)]):
    return {"message": "Welcome admin"}

@router.post("/create-user", status_code=201)
def admin_create_user(
    request: CreateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)]
):
    create_user(request.username, request.first_name, request.last_name, request.email, request.password, request.role, db)
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
    admin: Annotated[Users, Depends(require_admin)]
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted"}

@router.patch("/users/{user_id}")
def admin_update_user(
    user_id: int,
    request: UpdateUserRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)]
):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if request.username is not None:
        existing = db.query(Users).filter(Users.username == request.username, Users.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = request.username

    if request.first_name is not None:
        user.first_name = request.first_name

    if request.last_name is not None:
        user.last_name = request.last_name

    if request.email is not None:
        existing = db.query(Users).filter(Users.email == request.email, Users.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = request.email

    if request.role is not None:
        user.role = request.role

    db.commit()
    db.refresh(user)
    return {"message": "User updated"}

from schemas.auth import ResetPasswordRequest
from core.security import hash_password

@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    request: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)]
):
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password too short (min 8 characters)")

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(request.new_password)
    db.commit()

    return {"message": "Password reset successfully"}