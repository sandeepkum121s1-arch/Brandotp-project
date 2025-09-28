from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from bson import ObjectId

# Import database
from backend.db import users_collection

# JWT Configuration
SECRET_KEY = "brandotpsecretkey2025"
ALGORITHM = "HS256"

# Create HTTPBearer instance
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Get user from database
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Return user data
        return {
            "id": str(user["_id"]),
            "username": user.get("username", "User"),
            "email": user.get("email", ""),
            "balance": float(user.get("balance", 0.0)),
            "is_active": user.get("is_active", True)
        }
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    except Exception as e:
        print(f"❌ Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
