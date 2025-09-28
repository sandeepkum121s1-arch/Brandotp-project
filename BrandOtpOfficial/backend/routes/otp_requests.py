from datetime import datetime
from bson import ObjectId
from typing import Dict, Optional, List
import pymongo
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from backend.db import db, otp_requests_collection, services_collection, users_collection, wallets_collection
from backend.utils.auth_utils import get_current_user
from backend.models.otp_request import OtpRequestCreate, OtpRequestResponse, OtpRequestInDB

# Create router instance
router = APIRouter()

# ✅ Wallet utility functions (sync versions for this module)
def get_user_wallet_balance(user_id: str) -> dict:
    """Get user wallet balance"""
    try:
        if "@" in user_id:
            user = users_collection.find_one({"email": user_id})
        else:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return {"success": False, "error": "User not found", "balance": 0.0}
        
        return {
            "success": True,
            "balance": user.get("balance", 0.0),
            "user_id": user_id
        }
    except Exception as e:
        return {"success": False, "error": str(e), "balance": 0.0}

def debit_user_wallet_sync(user_id: str, amount: float, reason: str = "OTP Service"):
    """Debit money from user wallet"""
    try:
        if "@" in user_id:
            user = users_collection.find_one({"email": user_id})
        else:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        current_balance = user.get("balance", 0.0)
        if current_balance < amount:
            return {"success": False, "error": "Insufficient balance"}
        
        new_balance = current_balance - amount
        
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
            
            return {
                "success": True,
                "new_balance": new_balance,
                "transaction_id": str(transaction.get("_id"))
            }
        
        return {"success": False, "error": "Failed to update balance"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def credit_user_wallet_sync(user_id: str, amount: float, reason: str = "OTP Refund"):
    """Credit money to user wallet"""
    try:
        if "@" in user_id:
            user = users_collection.find_one({"email": user_id})
        else:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        current_balance = user.get("balance", 0.0)
        new_balance = current_balance + amount
        
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
            
            return {
                "success": True,
                "new_balance": new_balance,
                "transaction_id": str(transaction.get("_id"))
            }
        
        return {"success": False, "error": "Failed to update balance"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ✅ Routes
@router.get("/history", response_model=List[OtpRequestResponse])
async def get_otp_history(
    limit: int = Query(10, ge=1, le=100, description="Number of records to fetch"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    current_user = Depends(get_current_user)
):
    """Get user's OTP request history"""
    try:
        user_id = str(current_user.get("email"))
        
        # Get OTP requests for the user
        cursor = otp_requests_collection.find({"user_id": user_id})\
            .sort("created_at", pymongo.DESCENDING)\
            .skip(skip)\
            .limit(limit)
        
        # Convert to list of OtpRequestResponse
        otp_requests = []
        for doc in cursor:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
            # Format datetime objects to strings
            if "created_at" in doc:
                doc["created_at"] = doc["created_at"].isoformat()
            if "updated_at" in doc:
                doc["updated_at"] = doc["updated_at"].isoformat()
            otp_requests.append(doc)
        
        return otp_requests
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OTP history: {str(e)}"
        )

@router.post("/request", response_model=dict)
async def request_otp(request: OtpRequestCreate, current_user = Depends(get_current_user)):
    """Request a new OTP for a service"""
    try:
        # Validate service_id
        try:
            service_object_id = ObjectId(request.service_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid service ID format")
        
        # Get service details
        service = services_collection.find_one({"_id": service_object_id})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        if service.get("status") != "active":
            raise HTTPException(status_code=400, detail="Service is not active")
        
        # Get user details
        user_id = str(current_user.get("email"))
        
        # Check wallet balance
        wallet_info = get_user_wallet_balance(user_id)
        if not wallet_info["success"]:
            raise HTTPException(status_code=400, detail=wallet_info["error"])
        
        # Check if user has enough balance
        service_price = service.get("my_price", 0)
        current_balance = wallet_info["balance"]
        
        if current_balance < service_price:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient wallet balance. Required: ₹{service_price}, Available: ₹{current_balance}"
            )
        
        # Deduct from wallet
        debit_result = debit_user_wallet_sync(
            user_id, 
            service_price, 
            f"OTP service: {service.get('name', 'Unknown Service')}"
        )
        
        if not debit_result["success"]:
            raise HTTPException(status_code=400, detail=f"Payment failed: {debit_result['error']}")
        
        # Create OTP request
        otp_request = {
            "user_id": user_id,
            "service_id": request.service_id,
            "service_name": service.get("name", "Unknown Service"),
            "number": None,  # Will be filled by admin/system
            "status": "pending",
            "otp_code": None,  # Will be filled when OTP is received
            "amount_paid": service_price,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = otp_requests_collection.insert_one(otp_request)
        request_id = str(result.inserted_id)
        
        return {
            "success": True,
            "request_id": request_id,
            "status": "pending",
            "message": "OTP request created successfully",
            "service": service["name"],
            "price": service_price,
            "new_wallet_balance": debit_result["new_balance"],
            "transaction_id": debit_result.get("transaction_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create OTP request: {str(e)}"
        )

@router.get("/status/{request_id}", response_model=dict)
async def get_otp_status(request_id: str = Path(...), current_user = Depends(get_current_user)):
    """Get the status of an OTP request"""
    try:
        # Validate request_id
        try:
            request_object_id = ObjectId(request_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid request ID format")
        
        # Get user ID
        user_id = str(current_user.get("email"))
        
        # Get OTP request
        otp_request = otp_requests_collection.find_one({
            "_id": request_object_id,
            "user_id": user_id
        })
        
        if not otp_request:
            raise HTTPException(status_code=404, detail="OTP request not found")
        
        # Prepare response
        response = {
            "success": True,
            "request_id": request_id,
            "status": otp_request["status"],
            "service_name": otp_request.get("service_name", "Unknown"),
            "amount_paid": otp_request.get("amount_paid", 0),
            "created_at": otp_request["created_at"].isoformat(),
            "updated_at": otp_request["updated_at"].isoformat()
        }
        
        # Include number if available
        if otp_request.get("number"):
            response["number"] = otp_request["number"]
        
        # Include OTP code if available
        if otp_request.get("otp_code"):
            response["otp_code"] = otp_request["otp_code"]
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OTP status: {str(e)}"
        )

@router.post("/cancel/{request_id}", response_model=dict)
async def cancel_otp_request(request_id: str = Path(...), current_user = Depends(get_current_user)):
    """Cancel an OTP request and refund the wallet"""
    try:
        # Validate request_id
        try:
            request_object_id = ObjectId(request_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid request ID format")
        
        # Get user ID
        user_id = str(current_user.get("email"))
        
        # Get OTP request
        otp_request = otp_requests_collection.find_one({
            "_id": request_object_id,
            "user_id": user_id
        })
        
        if not otp_request:
            raise HTTPException(status_code=404, detail="OTP request not found")
        
        # Check if request can be cancelled
        if otp_request["status"] not in ["pending", "active"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel request with status '{otp_request['status']}'"
            )
        
        # Get refund amount
        refund_amount = otp_request.get("amount_paid", 0)
        
        if refund_amount <= 0:
            # Still cancel the request even if no refund
            otp_requests_collection.update_one(
                {"_id": request_object_id},
                {
                    "$set": {
                        "status": "cancelled",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": True,
                "request_id": request_id,
                "status": "cancelled",
                "message": "OTP request cancelled (no refund applicable)",
                "refund_amount": 0
            }
        
        # Process refund
        credit_result = credit_user_wallet_sync(
            user_id, 
            refund_amount, 
            f"Refund for cancelled OTP request {request_id}"
        )
        
        if not credit_result["success"]:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to process refund: {credit_result['error']}"
            )
        
        # Update OTP request status
        otp_requests_collection.update_one(
            {"_id": request_object_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "request_id": request_id,
            "status": "cancelled",
            "message": "OTP request cancelled and refunded successfully",
            "refund_amount": refund_amount,
            "new_wallet_balance": credit_result["new_balance"],
            "transaction_id": credit_result.get("transaction_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel OTP request: {str(e)}"
        )

@router.get("/stats", response_model=dict)
async def get_otp_stats(current_user = Depends(get_current_user)):
    """Get user's OTP request statistics"""
    try:
        user_id = str(current_user.get("email"))
        
        # Get various counts
        total_requests = otp_requests_collection.count_documents({"user_id": user_id})
        pending_requests = otp_requests_collection.count_documents({
            "user_id": user_id, 
            "status": "pending"
        })
        completed_requests = otp_requests_collection.count_documents({
            "user_id": user_id, 
            "status": "completed"
        })
        cancelled_requests = otp_requests_collection.count_documents({
            "user_id": user_id, 
            "status": "cancelled"
        })
        
        # Get total amount spent
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total_spent": {"$sum": "$amount_paid"}}}
        ]
        spent_result = list(otp_requests_collection.aggregate(pipeline))
        total_spent = spent_result[0]["total_spent"] if spent_result else 0
        
        return {
            "success": True,
            "stats": {
                "total_requests": total_requests,
                "pending_requests": pending_requests,
                "completed_requests": completed_requests,
                "cancelled_requests": cancelled_requests,
                "total_amount_spent": total_spent
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OTP stats: {str(e)}"
        )

@router.put("/{request_id}/update-status")
async def update_otp_status(
    request_id: str = Path(...),
    status: str = Query(..., description="New status (active, completed, failed)"),
    number: Optional[str] = Query(None, description="Phone number assigned"),
    otp_code: Optional[str] = Query(None, description="OTP code received"),
    current_user = Depends(get_current_user)
):
    """Update OTP request status (Admin or system use)"""
    try:
        # Validate request_id
        try:
            request_object_id = ObjectId(request_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid request ID format")
        
        # Validate status
        valid_statuses = ["pending", "active", "completed", "failed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        # Get OTP request
        otp_request = otp_requests_collection.find_one({"_id": request_object_id})
        if not otp_request:
            raise HTTPException(status_code=404, detail="OTP request not found")
        
        # Prepare update data
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if number:
            update_data["number"] = number
        
        if otp_code:
            update_data["otp_code"] = otp_code
        
        # Update the request
        result = otp_requests_collection.update_one(
            {"_id": request_object_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "request_id": request_id,
                "message": f"OTP request status updated to {status}",
                "updated_fields": update_data
            }
        else:
            return {
                "success": False,
                "request_id": request_id,
                "message": "No changes made to the request"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update OTP request: {str(e)}"
        )
