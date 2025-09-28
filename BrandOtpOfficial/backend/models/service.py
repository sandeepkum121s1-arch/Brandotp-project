from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ServiceCreate(BaseModel):
    name: str
    price: float
    is_active: bool = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None

class ServiceInDB(BaseModel):
    id: Optional[str] = None
    name: str
    price: float
    is_active: bool = True

class ServiceResponse(BaseModel):
    id: Optional[str] = None
    name: str
    price: float
    is_active: bool = True