# backend/routes/pay0_order.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, constr

from backend.utils.pay0_client import create_order   # Pay0 API helper

router = APIRouter()
# Pydantic v2 syntax
from pydantic import BaseModel, Field, constr

class OrderBody(BaseModel):
    mobile: constr(pattern=r"^\d{10}$")       # ⬅️  regex → pattern
    amount: float = Field(gt=49, lt=5001)
    remark1: str | None = None
    remark2: str | None = None


@router.post("/order")
def pay0_create(body: OrderBody):
    res = create_order(
        mobile   = body.mobile,
        amount   = body.amount,
        redirect = "http://localhost:8000/payment-success",
        remark1  = body.remark1 or "",
        remark2  = body.remark2 or ""
    )

    if not res.get("status"):
        raise HTTPException(400, res.get("message", "Pay0 error"))

    return {
        "order_id"   : res["result"]["orderId"],
        "payment_url": res["result"]["payment_url"]
    }
