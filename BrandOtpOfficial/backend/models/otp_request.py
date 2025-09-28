from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

class OtpRequestBase(BaseModel):
    service_id: str
    number: Optional[str] = None
    status: Literal["pending", "active", "completed", "cancelled"] = "pending"
    otp_code: Optional[str] = None

class OtpRequestCreate(BaseModel):
    service_id: str

class OtpRequestInDB(OtpRequestBase):
    id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OtpRequestResponse(OtpRequestBase):
    id: str
    created_at: datetime
    updated_at: datetime