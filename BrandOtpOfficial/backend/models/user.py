from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import jwt
from datetime import datetime
from bson import ObjectId

# Import database and auth
from backend.db import users_collection
from backend.utils.auth_utils import get_current_user

router = APIRouter()

# ✅ GET USER PROFILE
@router.get("/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile for dashboard"""
    try:
        # Get fresh user data from database
        user = users_collection.find_one({"_id": ObjectId(current_user["id"])})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return user profile data
        profile_data = {
            "id": str(user["_id"]),
            "username": user.get("username", "User"),
            "email": user.get("email", ""),
            "balance": float(user.get("balance", 0.0)),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
            "total_orders": 0,  # You can count from orders collection later
            "total_spent": 0.0   # You can calculate from transactions later
        }
        
        return {
            "success": True,
            "user": profile_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load profile")

# ✅ GET DASHBOARD STATS
@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    try:
        # You can expand this with real data from your collections
        stats = {
            "total_balance": float(current_user.get("balance", 0.0)),
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
        raise HTTPException(status_code=500, detail="Failed to load stats")

# ✅ UPDATE USER PROFILE
@router.put("/profile")
async def update_user_profile(
    current_user: dict = Depends(get_current_user),
    username: str = None
):
    """Update user profile"""
    try:
        update_data = {}
        
        if username:
            # Check if username is taken by another user
            existing_user = users_collection.find_one({
                "username": username,
                "_id": {"$ne": ObjectId(current_user["id"])}
            })
            
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already taken")
            
            update_data["username"] = username
        
        if update_data:
            # Update user in database
            result = users_collection.update_one(
                {"_id": ObjectId(current_user["id"])},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return {"success": True, "message": "Profile updated successfully"}
            else:
                return {"success": False, "message": "No changes made"}
        else:
            return {"success": False, "message": "No data to update"}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")
