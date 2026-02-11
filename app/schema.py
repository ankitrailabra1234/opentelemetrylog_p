from pydantic import BaseModel, Field, condecimal
from typing import Optional
from datetime import datetime

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[condecimal(max_digits=10, decimal_places=2)] = None

class ItemRead(ItemCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

