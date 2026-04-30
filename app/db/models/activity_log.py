from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum

class ActionType(str, enum.Enum):
    
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_PASSWORD_RESET = "user_password_reset"
    USER_IMPERSONATED = "user_impersonated"
    
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PASSWORD_CHANGED = "user_password_changed"
    
    ITEM_CREATED = "item_created"
    ITEM_UPDATED = "item_updated"
    ITEM_DELETED = "item_deleted"
    
    WAREHOUSE_CREATED = "warehouse_created"
    WAREHOUSE_UPDATED = "warehouse_updated"
    WAREHOUSE_DELETED = "warehouse_deleted"
    
    CATEGORY_CREATED = "category_created"
    CATEGORY_UPDATED = "category_updated"
    CATEGORY_DELETED = "category_deleted"
    
    ORDER_CREATED = "order_created"
    ORDER_STATUS_CHANGED = "order_status_changed"
    ORDER_DELETED = "order_deleted"
    
    PURCHASE_CREATED = "purchase_created"
    PURCHASE_STATUS_CHANGED = "purchase_status_changed"
    PURCHASE_COMPLETED = "purchase_completed"
    PURCHASE_DELETED = "purchase_deleted"
    
    SUPPLIER_CREATED = "supplier_created"
    SUPPLIER_UPDATED = "supplier_updated"
    SUPPLIER_DELETED = "supplier_deleted"

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_username = Column(String(20), nullable=True)  
    user_role = Column(String(30), nullable=True)
    action = Column(SqlEnum(ActionType), nullable=False)
    entity_type = Column(String(50), nullable=True)   
    entity_id = Column(Integer, nullable=True)         
    entity_name = Column(String(255), nullable=True)                
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("Users", backref="activity_logs")