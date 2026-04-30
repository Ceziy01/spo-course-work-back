from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_db, get_current_user
from db.models.user import Users, UserRole
from schemas.auth import UsersMe

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/customers", response_model=List[UsersMe])
def get_customers(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    allowed_roles = [UserRole.ADMIN, UserRole.SALES_MANAGER, UserRole.PURCHASE_MANAGER, UserRole.MANAGEMENT, UserRole.ACCOUNTANT, UserRole.WAREHOUSE_KEEPER]
    if current_user.role not in allowed_roles:
        raise HTTPException(403, "Недостаточно прав")
    customers = db.query(Users).filter(Users.role == UserRole.CUSTOMER).all()
    return [
        UsersMe(
            id=c.id,
            username=c.username,
            first_name=c.first_name,
            last_name=c.last_name,
            email=c.email,
            role=c.role.value
        ) for c in customers
    ]