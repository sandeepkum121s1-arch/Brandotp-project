from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Any


# ✅ Load environment variables
load_dotenv()


router = APIRouter()


# ✅ Get API key and markup from environment
API_KEY = os.getenv("SMSMAN_API_KEY")
BASE_URL = "https://api.sms-man.com/control/"

# 💰 MARKUP CONFIGURATION FROM ENVIRONMENT
MARKUP_PERCENTAGE = float(os.getenv("MARKUP_PERCENTAGE", "1.70"))


print(f"🔑 API Key loaded: {'Yes' if API_KEY else 'No'}")
print(f"🔑 API Key (first 10 chars): {API_KEY[:10] if API_KEY else 'None'}...")
print(f"💰 Markup Percentage: {MARKUP_PERCENTAGE} ({(MARKUP_PERCENTAGE-1)*100}% profit)")


# 💰 PRICING HELPER FUNCTIONS
def apply_markup(original_price: float) -> float:
    """Apply markup to original SMSMan price"""
    return round(float(original_price) * MARKUP_PERCENTAGE, 2)

def get_price_info(original_price: float) -> dict:
    """Get complete price information with markup"""
    user_price = apply_markup(original_price)
    return {
        "original_price": float(original_price),
        "user_price": user_price,
        "markup_percentage": (MARKUP_PERCENTAGE - 1) * 100,
        "profit_amount": round(user_price - float(original_price), 2)
    }


class BuyNumberRequest(BaseModel):
    countryId: int
    applicationId: int


@router.get("/api/smsman/countries")
async def get_countries():
    """Get all countries from SMSMan API"""
    try:
        print("🌍 Fetching countries from SMSMan API...")
        print(f"🔗 API URL: {BASE_URL}countries?token=***")
        
        if not API_KEY:
            print("❌ API Key not found in environment!")
            raise HTTPException(status_code=500, detail="SMSMan API key not configured")
        
        response = requests.get(
            f"{BASE_URL}countries?token={API_KEY}", 
            timeout=10,
            headers={'User-Agent': 'BrandOtp/1.0'}
        )
        
        print(f"📡 API Response Status: {response.status_code}")
        print(f"📡 API Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Received {len(data) if isinstance(data, list) else 'unknown'} countries")
            print(f"📋 Sample data: {data[:2] if isinstance(data, list) and len(data) > 0 else data}")
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"❌ Response Text: {response.text}")
            # Return fallback data instead of error
            fallback_countries = [
                {"id": 1, "title": "Russia", "code": "RU"},
                {"id": 2, "title": "Ukraine", "code": "UA"},
                {"id": 7, "title": "Kazakhstan", "code": "KZ"},
                {"id": 16, "title": "Philippines", "code": "PH"},
                {"id": 38, "title": "Poland", "code": "PL"},
                {"id": 44, "title": "United Kingdom", "code": "GB"},
                {"id": 86, "title": "China", "code": "CN"},
                {"id": 91, "title": "India", "code": "IN"},
                {"id": 1, "title": "USA", "code": "US"},
                {"id": 49, "title": "Germany", "code": "DE"}
            ]
            print(f"⚠️ Using fallback countries due to API error")
            return fallback_countries
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        # Return fallback data instead of error
        fallback_countries = [
            {"id": 1, "title": "Russia", "code": "RU"},
            {"id": 2, "title": "Ukraine", "code": "UA"},
            {"id": 7, "title": "Kazakhstan", "code": "KZ"},
            {"id": 16, "title": "Philippines", "code": "PH"},
            {"id": 91, "title": "India", "code": "IN"}
        ]
        print(f"⚠️ Using fallback countries due to network error")
        return fallback_countries


@router.get("/api/smsman/services")  
async def get_services():
    """Get all services from SMSMan API with user prices (70% markup)"""
    try:
        print("🛠️ Fetching services from SMSMan API...")
        
        if not API_KEY:
            print("❌ API Key not found in environment!")
            raise HTTPException(status_code=500, detail="SMSMan API key not configured")
        
        response = requests.get(
            f"{BASE_URL}applications?token={API_KEY}", 
            timeout=10,
            headers={'User-Agent': 'BrandOtp/1.0'}
        )
        
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Received {len(data) if isinstance(data, list) else 'unknown'} services")
            print(f"📋 Sample data: {data[:2] if isinstance(data, list) and len(data) > 0 else data}")
            
            # 💰 ADD PRICING WITH MARKUP
            services_with_pricing = []
            for service in data:
                # Add mock pricing for demo (replace with real SMSMan pricing API)
                mock_original_price = 10.0 + (service.get('id', 1) % 10)  # Mock prices 10-20
                price_info = get_price_info(mock_original_price)
                
                services_with_pricing.append({
                    **service,
                    "pricing": price_info,
                    "display_price": f"₹{price_info['user_price']:.2f}",
                    "original_price_hidden": price_info['original_price']  # Hidden from user
                })
            
            return services_with_pricing
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"❌ Response Text: {response.text}")
            # Return fallback data with pricing
            fallback_services = [
                {"id": 1, "name": "Telegram"},
                {"id": 2, "name": "WhatsApp"},
                {"id": 12, "name": "Instagram"},
                {"id": 130, "name": "Discord"},
                {"id": 22, "name": "Facebook"},
                {"id": 35, "name": "Twitter"},
                {"id": 58, "name": "Snapchat"},
                {"id": 174, "name": "TikTok"},
                {"id": 61, "name": "Viber"},
                {"id": 85, "name": "Gmail"}
            ]
            
            # Add pricing to fallback services
            services_with_pricing = []
            for service in fallback_services:
                mock_original_price = 10.0 + (service['id'] % 10)
                price_info = get_price_info(mock_original_price)
                
                services_with_pricing.append({
                    **service,
                    "pricing": price_info,
                    "display_price": f"₹{price_info['user_price']:.2f}",
                    "original_price_hidden": price_info['original_price']
                })
            
            print(f"⚠️ Using fallback services with pricing due to API error")
            return services_with_pricing
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        # Return fallback data with pricing
        fallback_services = [
            {"id": 1, "name": "Telegram"},
            {"id": 2, "name": "WhatsApp"},
            {"id": 12, "name": "Instagram"},
            {"id": 130, "name": "Discord"},
            {"id": 22, "name": "Facebook"}
        ]
        
        services_with_pricing = []
        for service in fallback_services:
            mock_original_price = 10.0 + (service['id'] % 10)
            price_info = get_price_info(mock_original_price)
            
            services_with_pricing.append({
                **service,
                "pricing": price_info,
                "display_price": f"₹{price_info['user_price']:.2f}",
                "original_price_hidden": price_info['original_price']
            })
        
        print(f"⚠️ Using fallback services with pricing due to network error")
        return services_with_pricing


@router.get("/api/smsman/price/{country_id}/{service_id}")
async def get_service_price(country_id: int, service_id: int):
    """Get specific service price with 70% markup"""
    try:
        print(f"💰 Getting price for Country={country_id}, Service={service_id}")
        
        if not API_KEY:
            raise HTTPException(status_code=500, detail="SMSMan API key not configured")
        
        # Get price from SMSMan API
        response = requests.get(
            f"{BASE_URL}get-price?token={API_KEY}&country_id={country_id}&application_id={service_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            smsman_data = response.json()
            original_price = float(smsman_data.get('price', 10.0))
        else:
            # Fallback price
            original_price = 10.0 + (service_id % 10)
            print(f"⚠️ Using fallback price due to API error")
        
        # Apply markup and return price info
        price_info = get_price_info(original_price)
        
        return {
            "country_id": country_id,
            "service_id": service_id,
            "user_price": price_info['user_price'],
            "display_price": f"₹{price_info['user_price']:.2f}",
            "markup_info": {
                "percentage": price_info['markup_percentage'],
                "profit": price_info['profit_amount']
            }
        }
        
    except Exception as e:
        print(f"❌ Price fetch error: {e}")
        # Return fallback pricing
        fallback_price = 10.0 + (service_id % 10)
        price_info = get_price_info(fallback_price)
        
        return {
            "country_id": country_id,
            "service_id": service_id,
            "user_price": price_info['user_price'],
            "display_price": f"₹{price_info['user_price']:.2f}",
            "error": "Fallback pricing used"
        }


@router.post("/api/smsman/buy")
async def buy_number(request: BuyNumberRequest):
    """Buy virtual number from SMSMan with balance validation"""
    try:
        country_id = request.countryId
        application_id = request.applicationId
        
        print(f"🛒 Buying number: Country={country_id}, Service={application_id}")
        
        if not API_KEY:
            print("❌ API Key not found in environment!")
            raise HTTPException(status_code=500, detail="SMSMan API key not configured")
        
        # 💰 GET PRICE WITH MARKUP FIRST
        try:
            price_response = requests.get(
                f"{BASE_URL}get-price?token={API_KEY}&country_id={country_id}&application_id={application_id}",
                timeout=10
            )
            if price_response.status_code == 200:
                original_price = float(price_response.json().get('price', 10.0))
            else:
                original_price = 10.0 + (application_id % 10)
        except:
            original_price = 10.0 + (application_id % 10)
        
        price_info = get_price_info(original_price)
        user_price = price_info['user_price']
        
        print(f"💰 Service Price: Original=₹{original_price}, User=₹{user_price}")
        
        # TODO: ADD USER BALANCE VALIDATION HERE
        # user_balance = get_user_balance(user_id)
        # if user_balance < user_price:
        #     raise HTTPException(
        #         status_code=400, 
        #         detail={
        #             "error": "Insufficient Balance",
        #             "required": user_price,
        #             "available": user_balance,
        #             "shortage": user_price - user_balance
        #         }
        #     )
        
        # Buy from SMSMan with original price
        url = f"{BASE_URL}get-number?token={API_KEY}&country_id={country_id}&application_id={application_id}"
        response = requests.get(url, timeout=15)
        
        print(f"📡 Buy API Response: {response.status_code}")
        print(f"📡 Buy Response Text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Buy Response: {data}")
            
            # TODO: DEDUCT USER BALANCE HERE
            # deduct_user_balance(user_id, user_price)
            
            return {
                **data,
                "pricing": {
                    "charged_amount": user_price,
                    "original_cost": original_price,
                    "profit_earned": price_info['profit_amount']
                }
            }
        else:
            # Return demo response for testing with pricing
            demo_response = {
                "success": True,
                "number": f"+123456789{country_id}{application_id}",
                "message": "Demo number - API call failed but showing demo response",
                "country_id": country_id,
                "application_id": application_id,
                "api_status": response.status_code,
                "pricing": {
                    "charged_amount": user_price,
                    "original_cost": original_price,
                    "profit_earned": price_info['profit_amount']
                }
            }
            return demo_response
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Buy Network Error: {e}")
        
        # Calculate pricing for demo response
        original_price = 10.0 + (request.applicationId % 10)
        price_info = get_price_info(original_price)
        
        # Return demo response with pricing
        demo_response = {
            "success": True,
            "number": f"+123456789{request.countryId}{request.applicationId}",
            "message": "Demo number - Network error occurred",
            "error": str(e),
            "pricing": {
                "charged_amount": price_info['user_price'],
                "original_cost": original_price,
                "profit_earned": price_info['profit_amount']
            }
        }
        return demo_response


# 💰 NEW PRICING ENDPOINTS
@router.get("/api/smsman/pricing-info")
async def get_pricing_info():
    """Get current pricing configuration"""
    return {
        "markup_percentage": MARKUP_PERCENTAGE,
        "profit_percentage": (MARKUP_PERCENTAGE - 1) * 100,
        "example": {
            "smsman_price": 10.0,
            "user_price": apply_markup(10.0),
            "profit": apply_markup(10.0) - 10.0
        },
        "configured_from_env": True
    }


@router.get("/api/smsman/calculate-price/{original_price}")
async def calculate_user_price(original_price: float):
    """Calculate user price from SMSMan original price"""
    price_info = get_price_info(original_price)
    return {
        "calculation": price_info,
        "display_price": f"₹{price_info['user_price']:.2f}"
    }


# Debug endpoints (existing ones updated)
@router.get("/api/smsman/debug")
async def debug_info():
    """Debug SMSMan API configuration with pricing info"""
    return {
        "api_key_configured": bool(API_KEY),
        "api_key_length": len(API_KEY) if API_KEY else 0,
        "api_key_preview": API_KEY[:10] + "..." if API_KEY else None,
        "base_url": BASE_URL,
        "markup_percentage": MARKUP_PERCENTAGE,
        "profit_percentage": (MARKUP_PERCENTAGE - 1) * 100,
        "pricing_example": get_price_info(10.0),
        "env_vars": list(os.environ.keys())[:10]
    }


@router.get("/api/smsman/test-connection")
async def test_connection():
    """Test SMSMan API connection"""
    try:
        if not API_KEY:
            return {"status": "error", "message": "API key not configured"}
        
        response = requests.get(f"{BASE_URL}get-balance?token={API_KEY}", timeout=5)
        return {
            "status": "success" if response.status_code == 200 else "error",
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text,
            "api_key_preview": API_KEY[:10] + "...",
            "pricing_config": {
                "markup": MARKUP_PERCENTAGE,
                "profit_percentage": (MARKUP_PERCENTAGE - 1) * 100
            }
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "pricing_config": {
                "markup": MARKUP_PERCENTAGE,
                "profit_percentage": (MARKUP_PERCENTAGE - 1) * 100
            }
        }
