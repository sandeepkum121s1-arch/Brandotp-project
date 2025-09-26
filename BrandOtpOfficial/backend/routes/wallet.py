from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Dict, Any
import logging
from bson import ObjectId

# Import dependencies
from backend.db import get_db, users_collection, wallets_collection
from backend.utils.auth_utils import get_current_user, get_current_active_user

# ✅ CREATE ROUTER INSTANCE
router = APIRouter()

# ✅ ADD MISSING UTILITY FUNCTIONS
def credit_user_wallet(user_id: str, amount: float, reason: str = "Credit") -> Dict[str, Any]:
    """Credit money to user wallet - Utility function"""
    try:
        # Get current user
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Get current balance
        current_balance = float(user.get("balance", 0.0))
        new_balance = current_balance + amount
        
        # Update user balance
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"balance": new_balance}}
        )
        
        if result.modified_count > 0:
            # Create transaction record
            transaction = {
                "user_id": user_id,
                "user_email": user.get("email", ""),
                "type": "credit",
                "amount": amount,
                "previous_balance": current_balance,
                "new_balance": new_balance,
                "reason": reason,
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            
            wallets_collection.insert_one(transaction)
            
            print(f"✅ Credited ₹{amount} to user {user_id}")
            return {
                "success": True,
                "new_balance": new_balance,
                "previous_balance": current_balance,
                "transaction_id": str(transaction["_id"]) if "_id" in transaction else None
            }
        else:
            return {"success": False, "error": "Failed to update balance"}
            
    except Exception as e:
        print(f"❌ Credit wallet error: {e}")
        return {"success": False, "error": f"Credit failed: {str(e)}"}

def debit_user_wallet(user_id: str, amount: float, reason: str = "Debit") -> Dict[str, Any]:
    """Debit money from user wallet - Utility function"""
    try:
        # Get current user
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Get current balance
        current_balance = float(user.get("balance", 0.0))
        
        # Check if sufficient balance
        if current_balance < amount:
            return {"success": False, "error": "Insufficient balance"}
        
        new_balance = current_balance - amount
        
        # Update user balance
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"balance": new_balance}}
        )
        
        if result.modified_count > 0:
            # Create transaction record
            transaction = {
                "user_id": user_id,
                "user_email": user.get("email", ""),
                "type": "debit",
                "amount": amount,
                "previous_balance": current_balance,
                "new_balance": new_balance,
                "reason": reason,
                "status": "completed",
                "created_at": datetime.utcnow()
            }
            
            wallets_collection.insert_one(transaction)
            
            print(f"✅ Debited ₹{amount} from user {user_id}")
            return {
                "success": True,
                "new_balance": new_balance,
                "previous_balance": current_balance,
                "transaction_id": str(transaction["_id"]) if "_id" in transaction else None
            }
        else:
            return {"success": False, "error": "Failed to update balance"}
            
    except Exception as e:
        print(f"❌ Debit wallet error: {e}")
        return {"success": False, "error": f"Debit failed: {str(e)}"}

# ✅ EXISTING ROUTE HANDLERS (Keep all your existing routes)
@router.get("/balance")
async def get_balance(current_user: dict = Depends(get_current_user)):
    """Get user wallet balance"""
    try:
        # Ensure user has balance field
        if "balance" not in current_user or current_user["balance"] is None:
            # Initialize balance to 0 if not exists
            users_collection.update_one(
                {"_id": ObjectId(current_user["id"])},
                {"$set": {"balance": 0.0}}
            )
            current_user["balance"] = 0.0
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "balance": float(current_user.get("balance", 0.0)),
                "user": {
                    "username": current_user.get("username", "User"),
                    "email": current_user.get("email", "")
                }
            }
        )
    except Exception as e:
        print(f"❌ Get balance error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": f"Failed to get balance: {str(e)}",
                "balance": 0.0
            }
        )

@router.post("/add-money")
async def add_money(
    request: Request,
    current_user: dict = Depends(get_current_user),
    amount: float = Form(...),
    payment_method: str = Form("manual"),
    transaction_id: str = Form(None),
    mobile_number: str = Form(None)
):
    """Add money to user wallet"""
    try:
        # ✅ UPDATED VALIDATION: ₹50 to ₹5000
        if amount < 50:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": "Minimum amount is ₹50"
                }
            )
        
        if amount > 5000:  # ✅ UPDATED MAXIMUM LIMIT
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": "Maximum amount limit is ₹5,000"
                }
            )
        
        # Use the credit_user_wallet utility function
        result = credit_user_wallet(
            user_id=current_user["id"],
            amount=amount,
            reason=f"Money added via {payment_method}"
        )
        
        if result["success"]:
            print(f"✅ Money added: ₹{amount} for user {current_user['email']}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"₹{amount} added successfully to your wallet",
                    "balance": result["new_balance"],
                    "transaction": {
                        "amount": amount,
                        "type": "credit",
                        "payment_method": payment_method,
                        "new_balance": result["new_balance"]
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "detail": result.get("error", "Failed to add money")
                }
            )
        
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "detail": f"Invalid amount: {str(ve)}"
            }
        )
    except Exception as e:
        print(f"❌ Add money error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": f"Failed to add money: {str(e)}"
            }
        )

@router.get("/transactions")
async def get_transactions(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    skip: int = 0
):
    """Get user wallet transactions"""
    try:
        # Get transactions from database
        transactions = list(
            wallets_collection
            .find({"user_id": current_user["id"]})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        
        # Convert ObjectId to string and format dates
        for transaction in transactions:
            transaction["_id"] = str(transaction["_id"])
            if "created_at" in transaction:
                transaction["created_at"] = transaction["created_at"].isoformat()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "transactions": transactions,
                "total": len(transactions),
                "current_balance": float(current_user.get("balance", 0.0))
            }
        )
        
    except Exception as e:
        print(f"❌ Get transactions error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": f"Failed to get transactions: {str(e)}",
                "transactions": [],
                "total": 0,
                "current_balance": 0.0
            }
        )

# ✅ ADD CORS HANDLING (if needed)
@router.options("/balance")
@router.options("/add-money") 
@router.options("/transactions")
async def handle_options():
    return JSONResponse(
        status_code=200,
        content={"message": "OK"}
    )
