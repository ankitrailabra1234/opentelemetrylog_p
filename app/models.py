from sqlalchemy import Column, Integer, String, Text, Numeric, TIMESTAMP, func
from .database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
