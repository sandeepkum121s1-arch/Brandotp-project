from fastapi import APIRouter, HTTPException
from backend.utils.smsman_client import get_services, get_countries, get_service_price, buy_number
# ✅ CORRECT IMPORTS - remove get_sms, cancel_number, get_service_price if not needed

router = APIRouter()

@router.get("/services")
async def get_services_endpoint():
    """Get all services with prices - MAIN ENDPOINT"""
    try:
        print("🔄 Loading services...")
        services = await get_services()
        print(f"✅ Loaded {len(services)} services")
        
        return {
            "success": True,
            "services": services,
            "count": len(services)
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/countries") 
async def get_countries_endpoint():
    """Get all countries"""
    try:
        print("🔄 Loading countries...")
        countries = await get_countries()
        print(f"✅ Loaded {len(countries)} countries")
        
        return {
            "success": True,
            "countries": countries,
            "count": len(countries)
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🌍 NEW COUNTRY-SPECIFIC ENDPOINT
@router.get("/services/{country_id}")
async def get_services_by_country_endpoint(country_id: int):
    """Get services with country-specific pricing - NEW DYNAMIC PRICING"""
    try:
        print(f"🌍 Loading services for country: {country_id}")
        
        # Import the function here
        from backend.utils.smsman_client import get_services_by_country
        
        services = await get_services_by_country(country_id)
        print(f"✅ Loaded {len(services)} services for country {country_id}")
        
        return {
            "success": True,
            "services": services,
            "count": len(services),
            "country_id": country_id
        }
    except Exception as e:
        print(f"❌ Error for country {country_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 💰 NEW SINGLE SERVICE PRICING ENDPOINT  
@router.get("/price/{service_id}/{country_id}")
async def get_service_price_endpoint(service_id: int, country_id: int):
    """Get live price for specific service and country"""
    try:
        print(f"💰 Getting price: Service {service_id}, Country {country_id}")
        
        pricing = await get_service_price(service_id, country_id)
        
        return {
            "success": True,
            "pricing": pricing,
            "service_id": service_id,
            "country_id": country_id
        }
    except Exception as e:
        print(f"❌ Price error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meta")
async def get_meta_endpoint():
    """Get services + countries together"""
    try:
        print("🔄 Loading meta data...")
        services = await get_services()
        countries = await get_countries()
        
        return {
            "success": True,
            "services": services,
            "countries": countries,
            "counts": {
                "services": len(services),
                "countries": len(countries)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/buy")
async def buy_endpoint(data: dict):
    """Buy number"""
    try:
        app_id = data.get("application_id")
        country_id = data.get("country_id", 91)
        
        if not app_id:
            raise HTTPException(status_code=400, detail="application_id required")
        
        print(f"🛒 Buying: Service {app_id}, Country {country_id}")
        
        # Get price
        price_info = await get_service_price(app_id, country_id)
        
        # Buy number
        result = await buy_number(app_id, country_id)
        
        return {
            "success": True,
            **result,
            "price_info": price_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Add this endpoint to your existing smsman_number.py

@router.post("/get-sms")
async def get_sms_endpoint(data: dict):
    """Get SMS for purchased number"""
    try:
        request_id = data.get("request_id")
        
        if not request_id:
            raise HTTPException(status_code=400, detail="request_id required")
        
        print(f"📨 Checking SMS for request: {request_id}")
        
        # Import the function here
        from backend.utils.smsman_client import get_sms
        
        sms_result = await get_sms(request_id)
        
        return {
            "success": True,
            **sms_result
        }
    except Exception as e:
        print(f"❌ SMS check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
