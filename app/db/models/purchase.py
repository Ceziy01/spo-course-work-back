from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum

class PurchaseStatus(str, enum.Enum):
    CREATED = "created"
    INITIATED = "initiated"
    COMPLETED = "completed"

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)          
    quantity = Column(Integer, nullable=False)             
    purchase_price = Column(Float, nullable=False)         
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(SqlEnum(PurchaseStatus), default=PurchaseStatus.CREATED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    supplier = relationship("Supplier")
    warehouse = relationship("Warehouse")