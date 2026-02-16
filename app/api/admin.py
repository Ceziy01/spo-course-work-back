from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import require_admin, get_db
from schemas.auth import CreateUserRequest
from services.auth_service import create_user
from models import Users

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
    create_user(request.username, request.password, request.is_admin, db)
    return {"message": "User created"}

@router.get("/users")
def all_users(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)]
):
    users = db.query(Users).all()
    return [
        {"id": u.id, "username": u.username, "is_admin": u.is_admin}
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
