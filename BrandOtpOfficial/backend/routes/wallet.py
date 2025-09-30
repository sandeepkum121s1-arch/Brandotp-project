from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import logging
from bson import ObjectId
import uuid

# Import dependencies
from backend.db import get_db, users_collection, wallets_collection
from backend.utils.auth_utils import get_current_user, get_current_active_user

# ✅ CREATE ROUTER INSTANCE
router = APIRouter()

# ✅ PYDANTIC MODELS FOR JSON REQUEST HANDLING
class AddMoneyRequest(BaseModel):
    amount: float = Field(..., ge=50, le=5000, description="Amount between ₹50-₹5000")
    mobile_number: str = Field(..., min_length=10, max_length=10, description="10-digit mobile number")
    payment_method: str = Field(default="pay0", description="Payment gateway method")

class ManualCreditRequest(BaseModel):
    user_id: str = Field(..., description="User ID to credit")
    amount: float = Field(..., gt=0, description="Amount to credit")
    reason: str = Field(default="Manual credit", description="Reason for credit")

# ✅ UTILITY FUNCTIONS
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
            
            transaction_result = wallets_collection.insert_one(transaction)
            
            print(f"✅ Credited ₹{amount} to user {user_id}")
            return {
                "success": True,
                "new_balance": new_balance,
                "previous_balance": current_balance,
                "transaction_id": str(transaction_result.inserted_id)
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
            
            transaction_result = wallets_collection.insert_one(transaction)
            
            print(f"✅ Debited ₹{amount} from user {user_id}")
            return {
                "success": True,
                "new_balance": new_balance,
                "previous_balance": current_balance,
                "transaction_id": str(transaction_result.inserted_id)
            }
        else:
            return {"success": False, "error": "Failed to update balance"}
            
    except Exception as e:
        print(f"❌ Debit wallet error: {e}")
        return {"success": False, "error": f"Debit failed: {str(e)}"}

# ✅ ROUTE HANDLERS

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
    request: AddMoneyRequest,
    current_user: dict = Depends(get_current_user)
):
    """✅ NEW PAY0 INTEGRATED ADD MONEY ENDPOINT"""
    try:
        print(f"💳 Add Money Request: {request.dict()}")
        print(f"👤 Current User: {current_user.get('email')}")
        
        # ✅ VALIDATION
        if request.amount < 50:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": "Minimum amount is ₹50"
                }
            )
        
        if request.amount > 5000:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": "Maximum amount is ₹5,000"
                }
            )

        # Mobile number validation
        if not request.mobile_number.isdigit() or len(request.mobile_number) != 10:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": "Please enter a valid 10-digit mobile number"
                }
            )
        
        # ✅ PAY0 INTEGRATION
        try:
            # Import Pay0 SDK
            from pay0_sdk import pay0_sdk
            
            # Create unique order ID
            order_id = f"BRANDOTP_{uuid.uuid4().hex[:12].upper()}_{int(datetime.now().timestamp())}"
            
            print(f"🚀 Creating Pay0 order: {order_id}")
            
            # Create Pay0 order
            pay0_result = pay0_sdk.create_order(
                customer_mobile=request.mobile_number,
                amount=request.amount,
                order_id=order_id,
                redirect_url=f"https://brandotp-project1.onrender.com/payment/success?order_id={order_id}",
                remark1="BrandOtp Wallet Recharge",
                remark2=f"Add ₹{request.amount} to wallet - User: {current_user.get('email', 'Unknown')}"
            )
            
            print(f"📊 Pay0 Response: {pay0_result}")
            
            if pay0_result.get("success", False):
                # ✅ SAVE PAYMENT RECORD IN DATABASE
                payment_record = {
                    "user_id": current_user["id"],
                    "user_email": current_user.get("email", ""),
                    "order_id": order_id,
                    "amount": request.amount,
                    "mobile_number": request.mobile_number,
                    "payment_method": request.payment_method,
                    "status": "pending",
                    "pay0_data": pay0_result.get("data", {}),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Insert payment record in wallets collection
                payment_result = wallets_collection.insert_one(payment_record)
                
                print(f"💾 Payment record saved: {payment_result.inserted_id}")
                
                # Extract payment URL from Pay0 response
                pay0_data = pay0_result.get("data", {})
                payment_url = pay0_data.get("payment_url") or pay0_data.get("redirect_url")
                
                if not payment_url:
                    # Try to construct payment URL manually
                    if "order_id" in pay0_data:
                        payment_url = f"https://pay0.shop/payment/{pay0_data['order_id']}"
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": f"Payment order created successfully! Amount: ₹{request.amount}",
                        "payment_url": payment_url,
                        "order_id": order_id,
                        "amount": request.amount,
                        "mobile_number": request.mobile_number,
                        "redirect_in": 2000  # Frontend will redirect after 2 seconds
                    }
                )
                
            else:
                # Pay0 order creation failed
                error_message = pay0_result.get("message", "Payment gateway error")
                print(f"❌ Pay0 order creation failed: {error_message}")
                
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "detail": f"Payment creation failed: {error_message}"
                    }
                )
                
        except ImportError:
            print("⚠️ Pay0 SDK not available, falling back to manual credit")
            
            # ✅ FALLBACK: MANUAL CREDIT (FOR TESTING)
            result = credit_user_wallet(
                user_id=current_user["id"],
                amount=request.amount,
                reason=f"Manual wallet recharge - ₹{request.amount}"
            )
            
            if result["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": f"₹{request.amount} added successfully to your wallet (Manual)",
                        "balance": result["new_balance"],
                        "transaction": {
                            "amount": request.amount,
                            "type": "credit",
                            "payment_method": "manual",
                            "new_balance": result["new_balance"],
                            "transaction_id": result["transaction_id"]
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
                
        except Exception as pay0_error:
            print(f"❌ Pay0 SDK error: {pay0_error}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "detail": f"Payment gateway error: {str(pay0_error)}"
                }
            )
        
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "detail": f"Invalid input: {str(ve)}"
            }
        )
    except Exception as e:
        print(f"❌ Add money error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": f"Failed to process payment: {str(e)}"
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
            if "updated_at" in transaction:
                transaction["updated_at"] = transaction["updated_at"].isoformat()
        
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

# ✅ PAYMENT SUCCESS HANDLER
@router.post("/payment/success")
async def payment_success_handler(request: Request):
    """Handle Pay0 payment success webhook/callback"""
    try:
        # Get request data
        if request.headers.get("content-type") == "application/json":
            data = await request.json()
        else:
            form_data = await request.form()
            data = dict(form_data)
        
        print(f"💰 Payment Success Data: {data}")
        
        order_id = data.get("order_id") or data.get("orderId")
        status = data.get("status", "").lower()
        
        if not order_id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "detail": "Order ID missing"}
            )
        
        # Find payment record
        payment_record = wallets_collection.find_one({"order_id": order_id})
        
        if not payment_record:
            print(f"❌ Payment record not found: {order_id}")
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Payment record not found"}
            )
        
        # Check if payment is successful
        if status in ["success", "completed", "paid"]:
            # Credit user wallet
            result = credit_user_wallet(
                user_id=payment_record["user_id"],
                amount=payment_record["amount"],
                reason=f"Pay0 payment success - Order: {order_id}"
            )
            
            if result["success"]:
                # Update payment record status
                wallets_collection.update_one(
                    {"order_id": order_id},
                    {
                        "$set": {
                            "status": "completed",
                            "updated_at": datetime.utcnow(),
                            "success_data": data
                        }
                    }
                )
                
                print(f"✅ Payment completed: {order_id} - ₹{payment_record['amount']}")
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": f"Payment successful! ₹{payment_record['amount']} added to wallet",
                        "amount": payment_record['amount'],
                        "new_balance": result["new_balance"]
                    }
                )
        
        # Payment failed
        wallets_collection.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": "failed",
                    "updated_at": datetime.utcnow(),
                    "failure_data": data
                }
            }
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "detail": f"Payment failed - Status: {status}"
            }
        )
        
    except Exception as e:
        print(f"❌ Payment success handler error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": f"Payment processing error: {str(e)}"
            }
        )

# ✅ ADMIN ROUTES (MANUAL CREDIT)
@router.post("/admin/credit")
async def admin_credit_wallet(
    request: ManualCreditRequest,
    current_user: dict = Depends(get_current_user)
):
    """Admin route to manually credit wallet"""
    try:
        # Check if user is admin (you can add proper admin check here)
        if current_user.get("role") != "admin":
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "detail": "Admin access required"
                }
            )
        
        result = credit_user_wallet(
            user_id=request.user_id,
            amount=request.amount,
            reason=f"Admin credit - {request.reason}"
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"₹{request.amount} credited successfully",
                    "transaction_id": result["transaction_id"],
                    "new_balance": result["new_balance"]
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": result["error"]
                }
            )
            
    except Exception as e:
        print(f"❌ Admin credit error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": f"Failed to credit wallet: {str(e)}"
            }
        )

# ✅ CORS HANDLERS
@router.options("/balance")
@router.options("/add-money") 
@router.options("/transactions")
@router.options("/payment/success")
async def handle_options():
    """Handle CORS preflight requests"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"}
    )

# ✅ HEALTH CHECK
@router.get("/health")
async def wallet_health_check():
    """Wallet service health check"""
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "service": "wallet",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
