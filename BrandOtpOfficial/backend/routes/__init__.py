# backend/routes/__init__.py
from fastapi import FastAPI

from .auth      import router as auth_router
from .user      import router as user_router
from .wallet    import router as wallet_router
from .payments  import router as payments_router      # ← यही ज़रूरी है

def register_all_routers(app: FastAPI) -> None:
    app.include_router(auth_router,     prefix="/api/auth",     tags=["Auth"])
    app.include_router(user_router,     prefix="/api/users",    tags=["Users"])
    app.include_router(wallet_router,   prefix="/api/wallet",   tags=["Wallet"])
    app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
