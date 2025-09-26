# backend/routes/pay0_webhook.py
from fastapi import APIRouter, Request, BackgroundTasks
from backend.utils.pay0_client import check_status

router = APIRouter()

@router.post("/webhook")
async def pay0_webhook(req: Request, bg: BackgroundTasks):
    form = await req.form()
    if form.get("status") == "SUCCESS":
        bg.add_task(_credit_wallet, form.get("order_id"))
    return {"ok": True}            # ACK immediately

def _credit_wallet(order_id: str):
    info = check_status(order_id)
    if info.get("status") and info["result"]["txnStatus"] == "SUCCESS":
        amount = float(info["result"]["amount"])
        # TODO: increment user balance in DB using order_id ↔ user mapping
