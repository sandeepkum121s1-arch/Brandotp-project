from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, constr, conint

from backend.utils.otpbz_client import (
    balance, services, servers, buy, sms, cancel
)

router = APIRouter()

class BuyBody(BaseModel):
    service: constr(min_length=1)
    server : conint(gt=0)

@router.get("/meta")
async def meta():
    return {
        "balance" : await balance(),
        "services": await services(),
        "servers" : await servers()
    }

@router.post("/new")
async def new_number(body: BuyBody):
    try:
        return await buy(body.service, body.server)
    except RuntimeError as e:
        raise HTTPException(400, str(e))

@router.get("/{oid}/sms")
async def get_sms(oid:int):
    try:
        code = await sms(oid)
        return {"code": code}
    except RuntimeError as e:
        raise HTTPException(400, str(e))

@router.post("/{oid}/cancel")
async def cancel_num(oid:int):
    try:
        await cancel(oid)
        return {"cancelled": True}
    except RuntimeError as e:
        raise HTTPException(400, str(e))
