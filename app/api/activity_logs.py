from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from core.dependencies import require_admin, get_db
from db.models.activity_log import ActivityLog, ActionType
from db.models.user import Users
from pydantic import BaseModel

router = APIRouter(prefix="/auth/admin/activity-logs", tags=["activity-logs"])

class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_username: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ActivityLogResponse])
def get_activity_logs(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[Users, Depends(require_admin)],
    user_id: Optional[int] = Query(None, description="Фильтр по пользователю"),
    user_role: Optional[str] = Query(None, description="Фильтр по роли"),
    action: Optional[str] = Query(None, description="Фильтр по типу действия"),
    entity_type: Optional[str] = Query(None, description="Фильтр по типу объекта"),
    date_from: Optional[datetime] = Query(None, description="Дата начала"),
    date_to: Optional[datetime] = Query(None, description="Дата конца"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    query = db.query(ActivityLog)

    if user_id is not None: query = query.filter(ActivityLog.user_id == user_id)
    if user_role: query = query.filter(ActivityLog.user_role == user_role)
    if action: query = query.filter(ActivityLog.action == action)
    if entity_type: query = query.filter(ActivityLog.entity_type == entity_type)
    if date_from: query = query.filter(ActivityLog.created_at >= date_from)
    if date_to: query = query.filter(ActivityLog.created_at <= date_to)

    logs = query.order_by(desc(ActivityLog.created_at)).offset(skip).limit(limit).all()
    return logs

@router.get("/action-types")
def get_action_types(admin: Annotated[Users, Depends(require_admin)]):
    return [{"value": a.value, "label": a.value} for a in ActionType]