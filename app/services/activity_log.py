from sqlalchemy.orm import Session
from db.models.activity_log import ActivityLog, ActionType
from db.models.user import Users

def log_action(
    db: Session,
    user: Users,
    action: ActionType,
    entity_type: str = None,
    entity_id: int = None,
    entity_name: str = None,
    ip_address: str = None
):
    entry = ActivityLog(
        user_id=user.id if user else None,
        user_username=user.username if user else None,
        user_role=user.role.value if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        ip_address=ip_address
    )
    db.add(entry)
    db.commit()
    return entry