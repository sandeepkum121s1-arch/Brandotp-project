from fastapi import APIRouter, Depends, HTTPException, status, Path, Form, Query
from fastapi.responses import JSONResponse
from backend.db import services_collection, get_db
from backend.models.service import ServiceCreate, ServiceUpdate, ServiceResponse, ServiceInDB
from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId

# Import wallet utilities
from backend.routes.wallet import debit_user_wallet, credit_user_wallet
from backend.utils.auth_utils import get_current_user

# Create router instance
router = APIRouter()

# Define routes for services
@router.get("/", response_model=List[ServiceResponse])
async def get_services(
    status_filter: Optional[str] = Query("active", description="Filter by status"),
    db=Depends(get_db)
):
    """Get all services with optional status filter"""
    try:
        query = {}
        if status_filter:
            query["status"] = status_filter
            
        services = list(services_collection.find(query))
        # Convert ObjectId to string for JSON serialization
        for service in services:
            service["id"] = str(service["_id"])
            del service["_id"]
        return services
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch services: {str(e)}"
        )

@router.post("/add", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def add_service(service: ServiceCreate, db=Depends(get_db)):
    """Add a new service"""
    try:
        # Create service document
        service_dict = service.dict()
        service_dict["created_at"] = datetime.now(timezone.utc)
        service_dict["status"] = "active"  # Default status
        
        # Insert into database
        result = services_collection.insert_one(service_dict)
        
        # Return created service
        created_service = services_collection.find_one({"_id": result.inserted_id})
        created_service["id"] = str(created_service["_id"])
        del created_service["_id"]
        
        return created_service
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create service: {str(e)}"
        )

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service_by_id(
    service_id: str = Path(..., title="The ID of the service to get"),
    db=Depends(get_db)
):
    """Get a specific service by ID"""
    try:
        # Check if service exists
        try:
            object_id = ObjectId(service_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid service ID format")
        
        service = services_collection.find_one({"_id": object_id})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Convert ObjectId to string
        service["id"] = str(service["_id"])
        del service["_id"]
        
        return service
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service: {str(e)}"
        )

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str = Path(..., title="The ID of the service to update"),
    service_update: ServiceUpdate = None, 
    db=Depends(get_db)
):
    """Update a service's my_price or status"""
    try:
        # Check if service exists
        try:
            object_id = ObjectId(service_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid service ID format")
        
        existing_service = services_collection.find_one({"_id": object_id})
        if not existing_service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Update only provided fields
        update_data = {k: v for k, v in service_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update service
        result = services_collection.update_one({"_id": object_id}, {"$set": update_data})
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made to service")
        
        # Return updated service
        updated_service = services_collection.find_one({"_id": object_id})
        updated_service["id"] = str(updated_service["_id"])
        del updated_service["_id"]
        
        return updated_service
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update service: {str(e)}"
        )

@router.delete("/{service_id}", response_model=ServiceResponse)
async def delete_service(
    service_id: str = Path(..., title="The ID of the service to delete"),
    db=Depends(get_db)
):
    """Soft delete a service by setting status to inactive"""
    try:
        # Check if service exists
        try:
            object_id = ObjectId(service_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid service ID format")
        
        existing_service = services_collection.find_one({"_id": object_id})
        if not existing_service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Soft delete by setting status to inactive
        result = services_collection.update_one(
            {"_id": object_id}, 
            {
                "$set": {
                    "status": "inactive",
                    "deleted_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to delete service")
        
        # Return updated service
        updated_service = services_collection.find_one({"_id": object_id})
        updated_service["id"] = str(updated_service["_id"])
        del updated_service["_id"]
        
        return updated_service
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete service: {str(e)}"
        )

@router.post("/{service_id}/purchase")
async def purchase_service(
    service_id: str = Path(..., title="The ID of the service to purchase"),
    user_id: str = Form(..., title="User ID for purchase"),
    quantity: int = Form(1, ge=1, le=100, title="Quantity to purchase"),
    db=Depends(get_db)
):
    """Purchase a service and debit user wallet"""
    try:
        # Check if service exists
        try:
            object_id = ObjectId(service_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid service ID format")
        
        service = services_collection.find_one({"_id": object_id, "status": "active"})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found or inactive")
        
        # Calculate total cost
        service_price = service.get("my_price", 0)
        total_cost = service_price * quantity
        
        if total_cost <= 0:
            raise HTTPException(status_code=400, detail="Invalid service price")
        
        # Debit user wallet
        result = debit_user_wallet(
            user_id, 
            total_cost, 
            f"Purchase of {service.get('name', 'service')} (qty: {quantity})"
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Payment failed: {result['error']}"
            )
        
        return {
            "success": True,
            "message": f"Service purchased successfully",
            "service_name": service.get("name"),
            "service_id": service_id,
            "quantity": quantity,
            "unit_price": service_price,
            "total_cost": total_cost,
            "new_balance": result["new_balance"],
            "transaction_id": result.get("transaction_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purchase service: {str(e)}"
        )

@router.get("/search/{search_term}")
async def search_services(
    search_term: str = Path(..., title="Search term for services"),
    db=Depends(get_db)
):
    """Search services by name or category"""
    try:
        # Search in name and category fields
        search_query = {
            "$and": [
                {"status": "active"},
                {
                    "$or": [
                        {"name": {"$regex": search_term, "$options": "i"}},
                        {"category": {"$regex": search_term, "$options": "i"}},
                        {"description": {"$regex": search_term, "$options": "i"}}
                    ]
                }
            ]
        }
        
        services = list(services_collection.find(search_query))
        
        # Convert ObjectId to string
        for service in services:
            service["id"] = str(service["_id"])
            del service["_id"]
        
        return {
            "success": True,
            "search_term": search_term,
            "results_count": len(services),
            "services": services
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search services: {str(e)}"
        )

@router.get("/category/{category}")
async def get_services_by_category(
    category: str = Path(..., title="Category name to filter services"),
    db=Depends(get_db)
):
    """Get services by category"""
    try:
        services = list(services_collection.find({
            "category": {"$regex": category, "$options": "i"},
            "status": "active"
        }))
        
        # Convert ObjectId to string
        for service in services:
            service["id"] = str(service["_id"])
            del service["_id"]
        
        return {
            "success": True,
            "category": category,
            "results_count": len(services),
            "services": services
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get services by category: {str(e)}"
        )

@router.get("/price-range/{min_price}/{max_price}")
async def get_services_by_price_range(
    min_price: float = Path(..., ge=0, title="Minimum price"),
    max_price: float = Path(..., ge=0, title="Maximum price"),
    db=Depends(get_db)
):
    """Get services within a price range"""
    try:
        if min_price > max_price:
            raise HTTPException(status_code=400, detail="Minimum price cannot be greater than maximum price")
        
        services = list(services_collection.find({
            "my_price": {"$gte": min_price, "$lte": max_price},
            "status": "active"
        }))
        
        # Convert ObjectId to string
        for service in services:
            service["id"] = str(service["_id"])
            del service["_id"]
        
        return {
            "success": True,
            "price_range": {"min": min_price, "max": max_price},
            "results_count": len(services),
            "services": services
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get services by price range: {str(e)}"
        )

# Utility functions for other modules to use
async def get_service_price(service_id: str) -> float:
    """Get service price by ID"""
    try:
        service = services_collection.find_one({"_id": ObjectId(service_id)})
        return service.get("my_price", 0.0) if service else 0.0
    except:
        return 0.0

async def validate_service_exists(service_id: str) -> bool:
    """Check if service exists and is active"""
    try:
        service = services_collection.find_one({
            "_id": ObjectId(service_id), 
            "status": "active"
        })
        return service is not None
    except:
        return False

async def get_service_details(service_id: str) -> dict:
    """Get complete service details by ID"""
    try:
        service = services_collection.find_one({"_id": ObjectId(service_id)})
        if service:
            service["id"] = str(service["_id"])
            del service["_id"]
            return service
        return {}
    except:
        return {}

# Stats endpoint
@router.get("/stats/overview")
async def get_services_stats(db=Depends(get_db)):
    """Get services statistics overview"""
    try:
        total_services = services_collection.count_documents({})
        active_services = services_collection.count_documents({"status": "active"})
        inactive_services = services_collection.count_documents({"status": "inactive"})
        
        # Get average price
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": None, "avg_price": {"$avg": "$my_price"}}}
        ]
        avg_result = list(services_collection.aggregate(pipeline))
        avg_price = avg_result[0]["avg_price"] if avg_result else 0
        
        return {
            "success": True,
            "stats": {
                "total_services": total_services,
                "active_services": active_services,
                "inactive_services": inactive_services,
                "average_price": round(avg_price, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service stats: {str(e)}"
        )
