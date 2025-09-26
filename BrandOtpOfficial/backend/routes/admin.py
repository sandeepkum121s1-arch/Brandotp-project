from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from datetime import datetime
from bson import ObjectId
from typing import List, Optional, Dict, Any
import pymongo

from backend.db import db, users_collection, services_collection, otp_requests_collection, orders_collection, wallets_collection
from backend.models.service import ServiceUpdate, ServiceResponse
from backend.utils.auth_utils import get_current_user

# Create router instance
router = APIRouter()

# ✅ Wallet utility functions for admin
def get_user_wallet_balance_by_email(user_email: str) -> float:
    """Get user wallet balance by email"""
    try:
        user = users_collection.find_one({"email": user_email})
        if user:
            return user.get("balance", 0.0)
        return 0.0
    except Exception as e:
        print(f"Error getting wallet balance: {e}")
        return 0.0

def get_user_wallet_balance_by_id(user_id: str) -> float:
    """Get user wallet balance by user ID"""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return user.get("balance", 0.0)
        return 0.0
    except Exception as e:
        print(f"Error getting wallet balance: {e}")
        return 0.0

# ✅ Improved admin verification
async def verify_admin(current_user=Depends(get_current_user)):
    """Verify that the current user has admin privileges"""
    try:
        user_email = current_user.get("email", "")
        user_id = current_user.get("id", "")
        
        # Check multiple admin criteria
        admin_emails = [
            "admin@brandotp.com",
            "admin@admin.com", 
            "superadmin@brandotp.com",
            "support@brandotp.com"
        ]
        
        # Check if user email is in admin list or ends with admin domain
        is_admin = (
            user_email in admin_emails or 
            user_email.endswith("@admin.com") or
            user_email.endswith("@brandotp.com")
        )
        
        if not is_admin:
            # You can also check by user role in database
            user = users_collection.find_one({"email": user_email})
            if user and user.get("role") == "admin":
                is_admin = True
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required. Contact administrator for access."
            )
            
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Admin verification failed: {str(e)}"
        )

@router.get("/users")
async def get_all_users(
    limit: int = Query(50, ge=1, le=200, description="Number of users to fetch"),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    admin=Depends(verify_admin)
):
    """Return list of all users with their wallet balances"""
    try:
        # Get users with pagination
        users = list(
            users_collection
            .find({}, {"hashed_password": 0})  # Exclude password hash
            .sort("created_at", pymongo.DESCENDING)
            .skip(skip)
            .limit(limit)
        )

        # Add wallet balance and format user data
        result = []
        for user in users:
            user_data = {
                "id": str(user["_id"]),
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "balance": user.get("balance", 0.0),  # Direct from user document
                "is_active": user.get("is_active", True),
                "is_verified": user.get("is_verified", False),
                "created_at": user.get("created_at", datetime.utcnow()).isoformat(),
                "last_login": user.get("last_login").isoformat() if user.get("last_login") else None
            }
            result.append(user_data)

        # Get total count for pagination info
        total_users = users_collection.count_documents({})

        return {
            "success": True,
            "users": result,
            "pagination": {
                "total": total_users,
                "limit": limit,
                "skip": skip,
                "has_more": skip + limit < total_users
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/services")
async def get_all_services(
    status_filter: Optional[str] = Query(None, description="Filter by status (active, inactive)"),
    admin=Depends(verify_admin)
):
    """Return list of all services (including inactive)"""
    try:
        # Build query
        query = {}
        if status_filter:
            query["status"] = status_filter

        services = list(services_collection.find(query).sort("created_at", pymongo.DESCENDING))

        # Convert ObjectId to string for JSON serialization
        result = []
        for service in services:
            service_data = {
                "id": str(service["_id"]),
                "name": service.get("name", ""),
                "category": service.get("category", ""),
                "my_price": service.get("my_price", 0),
                "base_price": service.get("base_price", 0),
                "status": service.get("status", "active"),
                "created_at": service.get("created_at", datetime.utcnow()).isoformat()
            }
            result.append(service_data)

        return {
            "success": True,
            "services": result,
            "total": len(result)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch services: {str(e)}"
        )

@router.put("/service/{service_id}", response_model=Dict[str, Any])
async def update_service(
    service_id: str = Path(..., title="The ID of the service to update"),
    service_update: Optional[ServiceUpdate] = None,
    admin=Depends(verify_admin)
):
    """Update a service's my_price, base_price, or status"""
    try:
        # Validate service ID
        try:
            object_id = ObjectId(service_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid service ID format")

        # Check if service exists
        existing_service = services_collection.find_one({"_id": object_id})
        if not existing_service:
            raise HTTPException(status_code=404, detail="Service not found")

        if not service_update:
            raise HTTPException(status_code=400, detail="No update data provided")

        # Prepare update data
        update_data = service_update.dict(exclude_unset=True)
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")

        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()

        # Update service
        result = services_collection.update_one({"_id": object_id}, {"$set": update_data})
        
        if result.modified_count == 0:
            return {
                "success": False,
                "message": "No changes made to service"
            }

        # Return updated service
        updated_service = services_collection.find_one({"_id": object_id})
        updated_service["id"] = str(updated_service["_id"])
        del updated_service["_id"]

        return {
            "success": True,
            "message": "Service updated successfully",
            "service": updated_service
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update service: {str(e)}"
        )

@router.get("/transactions")
async def get_all_transactions(
    user_id: Optional[str] = Query(None, description="Filter transactions by user ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by type (credit, debit)"),
    start_date: Optional[str] = Query(None, description="Filter transactions by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter transactions by end date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200, description="Number of transactions to fetch"),
    skip: int = Query(0, ge=0, description="Number of transactions to skip"),
    admin=Depends(verify_admin)
):
    """Return all wallet transactions with optional filters"""
    try:
        # Build query filter
        query = {}

        if user_id:
            query["user_id"] = user_id

        if transaction_type:
            valid_types = ["credit", "debit", "transfer_in", "transfer_out"]
            if transaction_type in valid_types:
                query["type"] = transaction_type

        # Add date range filter if provided
        if start_date or end_date:
            date_filter = {}
            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                    date_filter["$gte"] = start_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

            if end_date:
                try:
                    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                    end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                    date_filter["$lte"] = end_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

            if date_filter:
                query["created_at"] = date_filter

        # Get transactions with pagination
        transactions = list(
            wallets_collection
            .find(query)
            .sort("created_at", pymongo.DESCENDING)
            .skip(skip)
            .limit(limit)
        )

        # Format transactions
        result = []
        for transaction in transactions:
            transaction_data = {
                "id": str(transaction["_id"]),
                "user_id": transaction.get("user_id"),
                "user_email": transaction.get("user_email"),
                "type": transaction.get("type"),
                "amount": transaction.get("amount", 0),
                "previous_balance": transaction.get("previous_balance", 0),
                "new_balance": transaction.get("new_balance", 0),
                "reason": transaction.get("reason", ""),
                "status": transaction.get("status", "completed"),
                "created_at": transaction.get("created_at", datetime.utcnow()).isoformat()
            }
            result.append(transaction_data)

        # Get total count
        total_transactions = wallets_collection.count_documents(query)

        return {
            "success": True,
            "transactions": result,
            "pagination": {
                "total": total_transactions,
                "limit": limit,
                "skip": skip,
                "has_more": skip + limit < total_transactions
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transactions: {str(e)}"
        )

@router.get("/search/users")
async def search_users(
    email: Optional[str] = Query(None, description="Search users by email"),
    username: Optional[str] = Query(None, description="Search users by username"),
    admin=Depends(verify_admin)
):
    """Search users by email or username"""
    try:
        # Build query filter
        query = {}

        if email:
            query["email"] = {"$regex": email, "$options": "i"}

        if username:
            query["username"] = {"$regex": username, "$options": "i"}

        if not query:
            raise HTTPException(
                status_code=400, 
                detail="At least one search parameter (email or username) is required"
            )

        # Find matching users
        users = list(users_collection.find(query, {"hashed_password": 0}).limit(20))

        # Format user data
        result = []
        for user in users:
            user_data = {
                "id": str(user["_id"]),
                "email": user.get("email", ""),
                "username": user.get("username", ""),
                "balance": user.get("balance", 0.0),
                "is_active": user.get("is_active", True),
                "created_at": user.get("created_at", datetime.utcnow()).isoformat()
            }
            result.append(user_data)

        return {
            "success": True,
            "users": result,
            "total": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )

@router.get("/reports/summary")
async def get_summary_report(admin=Depends(verify_admin)):
    """Get summary report with key metrics"""
    try:
        # Count total users
        total_users = users_collection.count_documents({})
        active_users = users_collection.count_documents({"is_active": True})

        # Count total wallet transactions
        total_transactions = wallets_collection.count_documents({})

        # Calculate total wallet balances
        pipeline = [
            {"$group": {"_id": None, "total_balance": {"$sum": "$balance"}}}
        ]
        balance_result = list(users_collection.aggregate(pipeline))
        total_wallet_balance = balance_result[0]["total_balance"] if balance_result else 0

        # Calculate total revenue (sum of completed orders)
        revenue_pipeline = [
            {"$match": {"status": {"$in": ["COMPLETED", "SUCCESS"]}}},
            {"$group": {"_id": None, "total_revenue": {"$sum": "$amount"}}}
        ]
        revenue_result = list(orders_collection.aggregate(revenue_pipeline))
        total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0

        # Count services
        total_services = services_collection.count_documents({})
        active_services = services_collection.count_documents({"status": "active"})

        # Count OTP requests
        total_otp_requests = otp_requests_collection.count_documents({})
        pending_otp_requests = otp_requests_collection.count_documents({"status": "pending"})

        # Get recent activity (last 7 days)
        week_ago = datetime.utcnow() - pymongo.timedelta(days=7)
        recent_users = users_collection.count_documents({"created_at": {"$gte": week_ago}})
        recent_transactions = wallets_collection.count_documents({"created_at": {"$gte": week_ago}})

        return {
            "success": True,
            "summary": {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "recent_registrations": recent_users
                },
                "transactions": {
                    "total": total_transactions,
                    "recent": recent_transactions
                },
                "finances": {
                    "total_wallet_balance": total_wallet_balance,
                    "total_revenue": total_revenue
                },
                "services": {
                    "total": total_services,
                    "active": active_services
                },
                "otp_requests": {
                    "total": total_otp_requests,
                    "pending": pending_otp_requests
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary report: {str(e)}"
        )

@router.get("/search/otp")
async def search_otp_requests(
    status: Optional[str] = Query(None, description="Filter by OTP status"),
    service_id: Optional[str] = Query(None, description="Filter by service ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of records to fetch"),
    admin=Depends(verify_admin)
):
    """Search OTP requests by status, service_id, and user_id"""
    try:
        # Build query filter
        query = {}

        if status:
            valid_statuses = ["pending", "active", "completed", "cancelled"]
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            query["status"] = status

        if service_id:
            query["service_id"] = service_id

        if user_id:
            query["user_id"] = user_id

        # Find matching OTP requests
        otp_requests = list(
            otp_requests_collection
            .find(query)
            .sort("created_at", pymongo.DESCENDING)
            .limit(limit)
        )

        # Format OTP request data
        result = []
        for request in otp_requests:
            request_data = {
                "id": str(request["_id"]),
                "user_id": request.get("user_id"),
                "service_id": request.get("service_id"),
                "service_name": request.get("service_name", ""),
                "number": request.get("number"),
                "otp_code": request.get("otp_code"),
                "status": request.get("status"),
                "amount_paid": request.get("amount_paid", 0),
                "created_at": request.get("created_at").isoformat() if request.get("created_at") else None,
                "updated_at": request.get("updated_at").isoformat() if request.get("updated_at") else None
            }
            result.append(request_data)

        return {
            "success": True,
            "otp_requests": result,
            "total": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search OTP requests: {str(e)}"
        )

@router.get("/search/orders")
async def search_orders(
    status: Optional[str] = Query(None, description="Filter by order status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[str] = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200, description="Number of records to fetch"),
    admin=Depends(verify_admin)
):
    """Search orders by status, user_id, and date range"""
    try:
        # Build query filter
        query = {}

        if status:
            valid_statuses = ["PENDING", "COMPLETED", "FAILED", "CANCELLED", "SUCCESS"]
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            query["status"] = status

        if user_id:
            query["user_id"] = user_id

        # Add date range filter if provided
        if start_date or end_date:
            date_filter = {}
            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                    date_filter["$gte"] = start_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

            if end_date:
                try:
                    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                    end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                    date_filter["$lte"] = end_datetime
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

            if date_filter:
                query["created_at"] = date_filter

        # Find matching orders
        orders = list(
            orders_collection
            .find(query)
            .sort("created_at", pymongo.DESCENDING)
            .limit(limit)
        )

        # Format order data
        result = []
        for order in orders:
            order_data = {
                "id": str(order["_id"]),
                "order_id": order.get("order_id"),
                "amount": order.get("amount", 0),
                "status": order.get("status"),
                "user_id": order.get("user_id"),
                "payment_url": order.get("payment_url"),
                "transaction_id": order.get("transaction_id"),
                "created_at": order.get("created_at").isoformat() if order.get("created_at") else None,
                "updated_at": order.get("updated_at").isoformat() if order.get("updated_at") else None
            }
            result.append(order_data)

        return {
            "success": True,
            "orders": result,
            "total": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search orders: {str(e)}"
        )

@router.post("/user/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str = Path(..., title="User ID to toggle status"),
    admin=Depends(verify_admin)
):
    """Toggle user active/inactive status"""
    try:
        # Validate user ID
        try:
            object_id = ObjectId(user_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        # Find user
        user = users_collection.find_one({"_id": object_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Toggle status
        current_status = user.get("is_active", True)
        new_status = not current_status

        # Update user status
        result = users_collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "is_active": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            status_text = "activated" if new_status else "deactivated"
            return {
                "success": True,
                "message": f"User {status_text} successfully",
                "user": {
                    "id": user_id,
                    "email": user.get("email"),
                    "is_active": new_status
                }
            }
        else:
            return {
                "success": False,
                "message": "No changes made to user status"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle user status: {str(e)}"
        )
