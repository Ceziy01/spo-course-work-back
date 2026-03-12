from core.database import Base
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SqlEnum

class UserRole(str, Enum):
    ADMIN = "admin"
    WAREHOUSE_KEEPER = "warehouse_keeper"
    CUSTOMER = "customer"
    MANAGEMENT = "management"
    PURCHASE_MANAGER = "purchase_manager"
    SALES_MANAGER = "sales_manager"
    ACCOUNTANT = "accountant"
    SUPPLIER = "supplier"

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(70), unique=True, nullable=False)
    hashed_password = Column(String(72), nullable=False)
    role = Column(SqlEnum(UserRole), default=UserRole.CUSTOMER)

class Items(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, unique=True, nullable=False)
    count = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    on_sale = Column(Boolean, default=True)