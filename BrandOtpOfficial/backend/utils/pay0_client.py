# backend/utils/pay0_client.py
import os, requests, uuid, typing as t

BASE_URL  = "https://pay0.shop/api"
USER_TOKEN = os.getenv("PAY0_USER_TOKEN")        # put in .env

def _post(endpoint: str, data: dict) -> dict:
    resp = requests.post(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    return resp.json() if resp.content else {"status": False, "message": "Empty response"}

def create_order(mobile: str, amount: float, redirect: str,
                 remark1: str = "", remark2: str = "") -> dict:
    payload = {
        "customer_mobile": mobile,
        "customer_name"  : "BrandOtp User",
        "user_token"     : USER_TOKEN,
        "amount"         : f"{amount:.2f}",
        "order_id"       : f"ORD_{uuid.uuid4().hex[:12]}",
        "redirect_url"   : redirect,
        "remark1"        : remark1,
        "remark2"        : remark2
    }
    return _post("/create-order", payload)

def check_status(order_id: str) -> dict:
    return _post("/check-order-status",
                 {"user_token": USER_TOKEN, "order_id": order_id})
