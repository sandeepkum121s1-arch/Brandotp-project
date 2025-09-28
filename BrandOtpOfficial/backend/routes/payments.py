# backend/routes/payments.py
"""
Single entry-point router that exposes ONLY Pay0-related endpoints.
No legacy /create-payment route.
"""

from fastapi import APIRouter

# Pay0 sub-routers
from .pay0_order   import router as pay0_order
from .pay0_webhook import router as pay0_hook   # ← यदि webhook फ़ाइल मौजूद है

router = APIRouter()
router.include_router(pay0_order, prefix="/pay0", tags=["Pay0"])
router.include_router(pay0_hook,  prefix="/pay0", tags=["Pay0"])
from .otpbz_numbers import router as otpbz_router
router.include_router(otpbz_router, prefix="/otpbz", tags=["OTP Bazaar"])
