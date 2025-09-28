from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Literal

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ServiceBase(BaseModel):
    name: str
    code: str
    base_price: float
    my_price: float
    status: str = "active"

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    my_price: Optional[float] = None
    status: Optional[str] = None

class ServiceInDB(ServiceBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ServiceResponse(ServiceBase):
    id: str
    created_at: datetime
