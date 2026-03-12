from sqlalchemy import Column, Integer, String
from core.database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=False)