from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PaymentOrderBase(BaseModel):
    amount: float
    status: str

class PaymentOrderCreate(BaseModel):
    amount: float
    status: str = "PENDING"

class PaymentOrderInDB(BaseModel):
    order_id: str
    amount: float
    status: str
    created_at: Optional[datetime] = None

class PaymentOrderResponse(BaseModel):
    order_id: str
    amount: float
    status: str
    created_at: Optional[datetime] = None