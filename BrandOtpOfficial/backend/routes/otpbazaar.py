from fastapi import APIRouter, Depends, HTTPException, status, Body
import requests
import os
import json
from dotenv import load_dotenv
from typing import Dict, Optional, List
from datetime import datetime
from bson import ObjectId

# Fixed imports - Correct paths
from backend.db import db, get_db, otp_requests_collection, users_collection, wallets_collection
from backend.utils.auth_utils import get_current_user  # ✅ Fixed import
from backend.models.otp_request import OtpRequestCreate, OtpRequestResponse  # ✅ Fixed import path

# Load environment variables
load_dotenv()

# Get API key from environment variables
OTPB_API_KEY = os.getenv("OTPB_API_KEY")
if not OTPB_API_KEY:
    print("Warning: OTPB_API_KEY not found in environment variables")

# Base URL for OTP Bazaar API
BASE_URL = "https://otpbazzar.com/api"

# Create router
router = APIRouter()

# ✅ Added wallet utility functions (sync versions)
def debit_user_wallet_sync(user_id: str, amount: float, reason: str = "Service charge"):
    """Sync function to debit from user wallet"""
    try:
        # Find user by email or ObjectId
        if "@" in user_id:
            user = users_collection.find_one({"email": user_id})
        else:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise ValueError("User not found")
        
        current_balance = user.get("balance", 0.0)
        if current_balance < amount:
            raise ValueError("Insufficient balance")
        
        new_balance = current_balance - amount
        
        # Update balance
        result = users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"balance": new_balance}}
        )
        
        if result.modified_count > 0:
            # Create transaction record
            transaction = {
                "user_id": str(user["_id"]),
                "user_email": user["email"],
                "type": "debit",
                "amount": amount,
                "previous_balance": current_balance,
                "new_balance": new_balance,
                "reason": reason,
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            wallets_collection.insert_one(transaction)
            
            return {"success": True, "new_balance": new_balance}
        else:
            raise ValueError("Failed to update balance")
            
    except Exception as e:
        raise ValueError(f"Wallet debit failed: {str(e)}")

def credit_user_wallet_sync(user_id: str, amount: float, reason: str = "Money added"):
    """Sync function to credit to user wallet"""
    try:
        # Find user by email or ObjectId
        if "@" in user_id:
            user = users_collection.find_one({"email": user_id})
        else:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise ValueError("User not found")
        
        current_balance = user.get("balance", 0.0)
        new_balance = current_balance + amount
        
        # Update balance
        result = users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"balance": new_balance}}
        )
        
        if result.modified_count > 0:
            # Create transaction record
            transaction = {
                "user_id": str(user["_id"]),
                "user_email": user["email"],
                "type": "credit",
                "amount": amount,
                "previous_balance": current_balance,
                "new_balance": new_balance,
                "reason": reason,
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            wallets_collection.insert_one(transaction)
            
            return {"success": True, "new_balance": new_balance}
        else:
            raise ValueError("Failed to update balance")
            
    except Exception as e:
        raise ValueError(f"Wallet credit failed: {str(e)}")

# Helper function to make API requests to OTP Bazaar
async def make_api_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API request to OTP Bazaar"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {OTPB_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                            detail=f"Error communicating with OTP service: {str(e)}")

@router.get("/services", response_model=List[Dict])
async def get_available_services(current_user = Depends(get_current_user)):
    """Get list of available services from OTP Bazaar"""
    try:
        result = await make_api_request("services")
        return result.get("services", [])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Failed to fetch services: {str(e)}")

@router.post("/request", response_model=Dict)
async def create_otp_request(
    request_data: OtpRequestCreate = Body(...),
    current_user = Depends(get_current_user)
):
    """Create a new OTP request with OTP Bazaar"""
    user_id = str(current_user.get("email"))
    service_id = request_data.service_id
    
    # Prepare request to OTP Bazaar API
    api_data = {
        "service": service_id,
        "action": "getNumber"
    }
    
    try:
        # Call OTP Bazaar API
        result = await make_api_request("request", method="POST", data=api_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"OTP service error: {result.get('message', 'Unknown error')}")
        
        # Extract response data
        number = result.get("number")
        request_id = result.get("request_id")
        price = result.get("price", 0)
        
        # ✅ Fixed: Use sync wallet function (no await)
        try:
            debit_result = debit_user_wallet_sync(user_id, price, f"OTP request for service {service_id}")
            if not debit_result["success"]:
                raise ValueError("Wallet debit failed")
        except ValueError as e:
            # If wallet debit fails, cancel the OTP request
            try:
                await make_api_request(f"cancel/{request_id}", method="POST")
            except:
                pass  # Ignore cancel errors
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
        # Save request to database
        otp_request = {
            "user_id": user_id,
            "service_id": service_id,
            "number": number,
            "external_request_id": request_id,
            "status": "active",
            "price": price,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = otp_requests_collection.insert_one(otp_request)
        otp_request["id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "request_id": otp_request["id"],
            "number": number,
            "status": "active",
            "price": price
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to create OTP request: {str(e)}")

@router.get("/status/{request_id}", response_model=Dict)
async def check_otp_status(request_id: str, current_user = Depends(get_current_user)):
    """Check status of an OTP request"""
    user_id = str(current_user.get("email"))
    
    # ✅ Fixed: Use ObjectId for MongoDB query
    try:
        otp_request = otp_requests_collection.find_one({
            "_id": ObjectId(request_id), 
            "user_id": user_id
        })
    except:
        # If ObjectId fails, try with string ID
        otp_request = otp_requests_collection.find_one({
            "_id": request_id, 
            "user_id": user_id
        })
    
    if not otp_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP request not found")
    
    external_id = otp_request.get("external_request_id")
    
    try:
        # Call OTP Bazaar API to check status
        result = await make_api_request(f"status/{external_id}", method="GET")
        
        # Update local status if needed
        new_status = result.get("status")
        otp_code = result.get("code")
        
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        # If OTP code is received, mark as completed
        if otp_code:
            update_data["status"] = "completed"
            update_data["otp_code"] = otp_code
        else:
            update_data["status"] = new_status
        
        # Update the database record
        otp_requests_collection.update_one(
            {"_id": otp_request["_id"]},
            {"$set": update_data}
        )
        
        return {
            "request_id": request_id,
            "status": update_data["status"],
            "number": otp_request.get("number"),
            "otp_code": otp_code,
            "service_id": otp_request.get("service_id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to check OTP status: {str(e)}")

@router.post("/cancel/{request_id}", response_model=Dict)
async def cancel_otp_request(request_id: str, current_user = Depends(get_current_user)):
    """Cancel an active OTP request and process refund"""
    user_id = str(current_user.get("email"))
    
    # ✅ Fixed: Use ObjectId for MongoDB query
    try:
        otp_request = otp_requests_collection.find_one({
            "_id": ObjectId(request_id), 
            "user_id": user_id
        })
    except:
        # If ObjectId fails, try with string ID
        otp_request = otp_requests_collection.find_one({
            "_id": request_id, 
            "user_id": user_id
        })
    
    if not otp_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP request not found")
    
    if otp_request.get("status") not in ["active", "pending"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Cannot cancel completed or already cancelled request")
    
    external_id = otp_request.get("external_request_id")
    price = otp_request.get("price", 0)
    
    try:
        # Call OTP Bazaar API to cancel
        result = await make_api_request(f"cancel/{external_id}", method="POST")
        
        # Update local status
        otp_requests_collection.update_one(
            {"_id": otp_request["_id"]},
            {
                "$set": {
                    "status": "cancelled",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # ✅ Fixed: Use sync wallet function (no await)
        if price > 0:
            try:
                credit_result = credit_user_wallet_sync(
                    user_id, 
                    price, 
                    f"Refund for cancelled OTP request {request_id}"
                )
                if not credit_result["success"]:
                    print(f"Failed to process refund for user {user_id}")
            except Exception as e:
                print(f"Refund error: {e}")
                # Don't fail the cancellation if refund fails
        
        return {
            "success": True,
            "message": "Request cancelled successfully",
            "refund_processed": price > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to cancel OTP request: {str(e)}")

# ✅ Additional utility endpoints
@router.get("/my-requests", response_model=List[Dict])
async def get_my_otp_requests(current_user = Depends(get_current_user)):
    """Get all OTP requests for current user"""
    try:
        user_id = str(current_user.get("email"))
        
        requests = list(
            otp_requests_collection
            .find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(50)
        )
        
        # Convert ObjectId to string
        for req in requests:
            req["id"] = str(req["_id"])
            req.pop("_id", None)
        
        return requests
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to fetch requests: {str(e)}")
