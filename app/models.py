from database import Base
from sqlalchemy import Column, Integer, String, Boolean

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

class Items(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    count = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    on_sale = Column(Boolean, default=True)