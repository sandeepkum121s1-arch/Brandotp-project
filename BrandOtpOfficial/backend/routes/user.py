from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import jwt
from datetime import datetime
from bson import ObjectId

# Import database
from backend.db import users_collection

router = APIRouter()

# JWT Configuration  
SECRET_KEY = "brandotp-secret-key-2024"
ALGORITHM = "HS256"

# Simple auth dependency (without separate auth_utils file)
def get_current_user_simple(token: str = None):
    """Simple current user function without auth_utils"""
    try:
        if not token:
            # Try to get from localStorage (this would be handled by frontend)
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Decode JWT token  
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        # Get user from database
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {
            "id": str(user["_id"]),
            "username": user.get("username", "User"),
            "email": user.get("email", ""),
            "balance": float(user.get("balance", 0.0)),
            "is_active": user.get("is_active", True)
        }
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

# ✅ GET USER PROFILE (Simple version without auth dependency)
@router.get("/profile")
async def get_user_profile():
    """Get current user profile - simplified version"""
    try:
        # For now, return a simple success message
        # This will be enhanced once auth is fully working
        return {
            "success": True,
            "message": "User profile endpoint working",
            "user": {
                "username": "User",
                "email": "user@example.com", 
                "balance": 0.0
            }
        }
        
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return {
            "success": False,
            "message": "Profile endpoint working but with demo data"
        }

# ✅ GET DASHBOARD STATS  
@router.get("/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = {
            "total_balance": 0.0,
            "total_orders": 0,
            "active_numbers": 0,
            "pending_requests": 0
        }
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return {
            "success": False,
            "message": "Stats endpoint error"
        }

# ✅ TEST ENDPOINT
@router.get("/test")
async def test_user_routes():
    """Test user routes"""
    return {
        "message": "User routes working!",
        "status": "success",
        "endpoints": [
            "/api/user/profile",
            "/api/user/stats", 
            "/api/user/test"
        ]
    }
