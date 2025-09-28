import httpx
import os
import json
import asyncio
from typing import List, Dict, Any, Optional

# Load API key from environment
SMSMAN_API_KEY = os.getenv("SMSMAN_API_KEY")
SMSMAN_BASE_URL = "https://api.sms-man.com/control"

# Pricing configuration
PROFIT_MARGIN = 1.70  # 70% markup

print(f"🔑 SMSMan API Key: {SMSMAN_API_KEY[:10] if SMSMAN_API_KEY else 'NOT FOUND'}...")
print(f"🌐 Using SMSMan API v2.0: {SMSMAN_BASE_URL}")

async def get_countries() -> List[Dict[str, Any]]:
    """Fetch ALL countries from SMSMan API v2.0"""
    
    if not SMSMAN_API_KEY:
        return []
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{SMSMAN_BASE_URL}/countries",
                params={"token": SMSMAN_API_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                countries = []
                
                if isinstance(data, dict):
                    for country_id, country_info in data.items():
                        try:
                            clean_id = int(str(country_id).strip())
                            
                            if isinstance(country_info, dict):
                                clean_name = str(country_info.get('title', country_info.get('name', ''))).strip()
                            elif isinstance(country_info, str):
                                clean_name = str(country_info).strip()
                            else:
                                continue
                            
                            if clean_name and len(clean_name) > 1:
                                countries.append({
                                    "id": clean_id,
                                    "title": clean_name,
                                    "code": generate_country_code(clean_name)
                                })
                                
                        except Exception:
                            continue
                
                if countries:
                    countries.sort(key=lambda x: x['title'])
                    return countries
                        
    except Exception as e:
        print(f"❌ Countries error: {e}")
    
    return []

async def get_services() -> List[Dict[str, Any]]:
    """Fetch services with CORRECTED PRICING - HANDLE LIST & DICT FORMATS"""
    
    if not SMSMAN_API_KEY:
        return []
    
    try:
        print("📱 Fetching services from SMSMan API v2.0...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Get all services
            services_response = await client.get(
                f"{SMSMAN_BASE_URL}/applications",
                params={"token": SMSMAN_API_KEY}
            )
            
            if services_response.status_code != 200:
                return []
            
            services_data = services_response.json()
            print(f"📋 Got {len(services_data)} services from API")
            
            # Step 2: Get live pricing for India
            print("💰 Fetching LIVE pricing for India (country 91)...")
            
            pricing_response = await client.get(
                f"{SMSMAN_BASE_URL}/get-prices",
                params={
                    "token": SMSMAN_API_KEY,
                    "country_id": 91  # India
                }
            )
            
            print(f"💰 Pricing Status: {pricing_response.status_code}")
            
            if pricing_response.status_code != 200:
                print(f"❌ Pricing API failed: {pricing_response.text}")
                return []
            
            try:
                pricing_raw = pricing_response.json()
                print(f"📊 Raw pricing response type: {type(pricing_raw)}")
                print(f"📊 Raw pricing sample: {str(pricing_raw)[:500]}...")
                
            except json.JSONDecodeError as e:
                print(f"❌ Pricing JSON error: {e}")
                return []
            
            # Step 3: Parse pricing - HANDLE BOTH LIST & DICT FORMATS
            all_pricing = {}
            
            try:
                if isinstance(pricing_raw, list):
                    print("🔄 Processing LIST format pricing...")
                    # Handle list format: [{"application_id": "1", "cost": "15", "count": 6455}, ...]
                    for item in pricing_raw:
                        if isinstance(item, dict):
                            try:
                                service_id = int(item.get('application_id', 0))
                                cost = float(item.get('cost', 0))
                                count = int(item.get('count', 0))
                                
                                if service_id > 0 and cost > 0:
                                    all_pricing[service_id] = {
                                        'original': cost,
                                        'user_price': cost * PROFIT_MARGIN,
                                        'count': count
                                    }
                                    print(f"✅ List format - Service {service_id}: ₹{cost} -> ₹{cost * PROFIT_MARGIN:.2f}")
                                    
                            except (ValueError, TypeError, KeyError):
                                continue
                    
                elif isinstance(pricing_raw, dict):
                    print("🔄 Processing DICT format pricing...")
                    
                    # Format 1: Direct service ID mapping {"1": {"cost": "15", "count": 6455}}
                    for key, value in pricing_raw.items():
                        try:
                            service_id = int(str(key).strip())
                            if isinstance(value, dict) and 'cost' in value:
                                original_cost = float(value['cost'])
                                all_pricing[service_id] = {
                                    'original': original_cost,
                                    'user_price': original_cost * PROFIT_MARGIN,
                                    'count': int(value.get('count', 0))
                                }
                                print(f"✅ Dict Format1 - Service {service_id}: ₹{original_cost} -> ₹{original_cost * PROFIT_MARGIN:.2f}")
                        except (ValueError, TypeError):
                            # Format 2: Nested country format {"91": {"1": {"cost": "15"}}}
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    try:
                                        service_id = int(str(sub_key).strip())
                                        if isinstance(sub_value, dict) and 'cost' in sub_value:
                                            original_cost = float(sub_value['cost'])
                                            all_pricing[service_id] = {
                                                'original': original_cost,
                                                'user_price': original_cost * PROFIT_MARGIN,
                                                'count': int(sub_value.get('count', 0))
                                            }
                                            print(f"✅ Dict Format2 - Service {service_id}: ₹{original_cost} -> ₹{original_cost * PROFIT_MARGIN:.2f}")
                                    except (ValueError, TypeError):
                                        continue
                else:
                    print(f"❌ Unknown pricing response type: {type(pricing_raw)}")
                    return []
                
                print(f"✅ Successfully parsed pricing for {len(all_pricing)} services")
                
            except Exception as e:
                print(f"❌ Pricing parsing error: {e}")
                return []
            
            # If no pricing found, try Russia as fallback
            if not all_pricing:
                print("⚠️ No pricing for India, trying Russia (country 7)...")
                
                russia_response = await client.get(
                    f"{SMSMAN_BASE_URL}/get-prices",
                    params={
                        "token": SMSMAN_API_KEY,
                        "country_id": 7  # Russia
                    }
                )
                
                if russia_response.status_code == 200:
                    try:
                        russia_pricing = russia_response.json()
                        print(f"🇷🇺 Russia pricing type: {type(russia_pricing)}")
                        
                        # Same parsing logic for Russia
                        if isinstance(russia_pricing, list):
                            for item in russia_pricing:
                                if isinstance(item, dict):
                                    try:
                                        service_id = int(item.get('application_id', 0))
                                        cost = float(item.get('cost', 0))
                                        count = int(item.get('count', 0))
                                        
                                        if service_id > 0 and cost > 0:
                                            all_pricing[service_id] = {
                                                'original': cost,
                                                'user_price': cost * PROFIT_MARGIN,
                                                'count': count
                                            }
                                            
                                    except (ValueError, TypeError, KeyError):
                                        continue
                        
                        elif isinstance(russia_pricing, dict):
                            for key, value in russia_pricing.items():
                                try:
                                    service_id = int(str(key).strip())
                                    if isinstance(value, dict) and 'cost' in value:
                                        original_cost = float(value['cost'])
                                        all_pricing[service_id] = {
                                            'original': original_cost,
                                            'user_price': original_cost * PROFIT_MARGIN,
                                            'count': int(value.get('count', 0))
                                        }
                                except (ValueError, TypeError):
                                    if isinstance(value, dict):
                                        for sub_key, sub_value in value.items():
                                            try:
                                                service_id = int(str(sub_key).strip())
                                                if isinstance(sub_value, dict) and 'cost' in sub_value:
                                                    original_cost = float(sub_value['cost'])
                                                    all_pricing[service_id] = {
                                                        'original': original_cost,
                                                        'user_price': original_cost * PROFIT_MARGIN,
                                                        'count': int(sub_value.get('count', 0))
                                                    }
                                            except (ValueError, TypeError):
                                                continue
                        
                        print(f"🇷🇺 Added {len(all_pricing)} services from Russia")
                        
                    except json.JSONDecodeError:
                        pass
            
            # If still no pricing, return empty (as requested)
            if not all_pricing:
                print("❌ No pricing data found in any country - returning empty")
                return []
            
            # Step 4: Build services list with ONLY live pricing
            services = []
            
            if isinstance(services_data, dict):
                for service_id, service_info in services_data.items():
                    try:
                        clean_id = int(str(service_id).strip())
                        
                        if isinstance(service_info, dict):
                            clean_name = str(service_info.get('title', service_info.get('name', ''))).strip()
                        elif isinstance(service_info, str):
                            clean_name = str(service_info).strip()
                        else:
                            continue
                        
                        if clean_name and len(clean_name) > 1:
                            # ONLY ADD IF LIVE PRICING EXISTS
                            if clean_id in all_pricing:
                                pricing_info = all_pricing[clean_id]
                                user_price = pricing_info['user_price']
                                original_price = pricing_info['original']
                                
                                services.append({
                                    "id": clean_id,
                                    "name": clean_name,
                                    "display_price": f"₹{user_price:.2f}",
                                    "pricing": {
                                        "user_price": round(user_price, 2),
                                        "original_price": round(original_price, 2),
                                        "profit_amount": round(user_price - original_price, 2),
                                        "margin_percent": 70,
                                        "live_api": True,
                                        "availability": pricing_info['count']
                                    }
                                })
                                
                    except Exception:
                        continue
                
                services.sort(key=lambda x: x['name'].lower())
                
                print(f"🎯 FINAL RESULT: {len(services)} services with live pricing")
                
                if services:
                    # Show sample prices
                    samples = [(s['name'], s['display_price']) for s in services[:10]]
                    print(f"🌟 Sample prices: {samples}")
                    
                return services
                    
    except Exception as e:
        print(f"❌ Services error: {e}")
    
    return []

async def get_service_price(application_id: int, country_id: int = 91) -> Dict[str, Any]:
    """Get LIVE price for specific service"""
    
    try:
        if not SMSMAN_API_KEY:
            return {"error": "No API key available", "live_api": False}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{SMSMAN_BASE_URL}/get-prices",
                params={
                    "token": SMSMAN_API_KEY,
                    "country_id": country_id,
                    "application_id": application_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and int(item.get('application_id', 0)) == application_id:
                            if 'cost' in item:
                                original_price = float(item['cost'])
                                user_price = original_price * PROFIT_MARGIN
                                
                                return {
                                    "user_price": round(user_price, 2),
                                    "original_price": round(original_price, 2),
                                    "profit_amount": round(user_price - original_price, 2),
                                    "display_price": f"₹{user_price:.2f}",
                                    "live_api": True,
                                    "availability": int(item.get('count', 0))
                                }
                
                elif isinstance(data, dict):
                    # Parse dict formats
                    for key, value in data.items():
                        if isinstance(value, dict):
                            # Format: {"91": {"123": {"cost": "25"}}}
                            for sub_key, sub_value in value.items():
                                if str(sub_key) == str(application_id) and isinstance(sub_value, dict):
                                    if 'cost' in sub_value:
                                        original_price = float(sub_value['cost'])
                                        user_price = original_price * PROFIT_MARGIN
                                        
                                        return {
                                            "user_price": round(user_price, 2),
                                            "original_price": round(original_price, 2),
                                            "profit_amount": round(user_price - original_price, 2),
                                            "display_price": f"₹{user_price:.2f}",
                                            "live_api": True,
                                            "availability": int(sub_value.get('count', 0))
                                        }
                        elif str(key) == str(application_id) and isinstance(value, dict):
                            # Format: {"123": {"cost": "25"}}
                            if 'cost' in value:
                                original_price = float(value['cost'])
                                user_price = original_price * PROFIT_MARGIN
                                
                                return {
                                    "user_price": round(user_price, 2),
                                    "original_price": round(original_price, 2),
                                    "profit_amount": round(user_price - original_price, 2),
                                    "display_price": f"₹{user_price:.2f}",
                                    "live_api": True,
                                    "availability": int(value.get('count', 0))
                                }
        
        return {"error": "No live pricing available", "live_api": False}
        
    except Exception as e:
        return {"error": str(e), "live_api": False}

async def buy_number(application_id: int, country_id: int = 91) -> Dict[str, Any]:
    """Buy number from SMSMan API v2.0"""
    
    try:
        if not SMSMAN_API_KEY:
            return {"error": "No API key available", "status": "error"}
            
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{SMSMAN_BASE_URL}/get-number",
                params={
                    "token": SMSMAN_API_KEY,
                    "application_id": application_id,
                    "country_id": country_id
                }
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if "number" in data and "request_id" in data:
                            return {
                                "number": data["number"],
                                "request_id": data["request_id"],
                                "status": "success",
                                "live_purchase": True
                            }
                        elif "error_msg" in data:
                            return {
                                "error": data["error_msg"],
                                "status": "api_error",
                                "live_purchase": False
                            }
                            
                except json.JSONDecodeError:
                    pass
        
        return {"error": "Purchase failed", "status": "error"}
        
    except Exception as e:
        return {"error": str(e), "status": "error"}

def generate_country_code(country_name: str) -> str:
    """Generate country code from country name"""
    name = country_name.lower().strip()
    
    mappings = {
        "russia": "RU", "india": "IN", "ukraine": "UA", "china": "CN",
        "kazakhstan": "KZ", "usa": "US", "uk": "GB", "germany": "DE",
        "france": "FR", "italy": "IT", "japan": "JP", "brazil": "BR"
    }
    
    if name in mappings:
        return mappings[name]
    
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    elif len(name) >= 2:
        return name[:2].upper()
    else:
        return "XX"
# 🌍 ADD THIS NEW FUNCTION AT THE END OF smsman_client.py

async def get_services_by_country(country_id: int) -> List[Dict[str, Any]]:
    """Fetch services with country-specific pricing - DYNAMIC PRICING"""
    
    if not SMSMAN_API_KEY:
        print(f"❌ No API key for country {country_id}")
        return []
    
    try:
        print(f"📱 Fetching services for country {country_id}...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Get all services (same as before)
            services_response = await client.get(
                f"{SMSMAN_BASE_URL}/applications",
                params={"token": SMSMAN_API_KEY}
            )
            
            if services_response.status_code != 200:
                print(f"❌ Services API failed for country {country_id}")
                return []
            
            services_data = services_response.json()
            print(f"📋 Got {len(services_data)} services for country {country_id}")
            
            # Step 2: Get country-specific pricing
            print(f"💰 Fetching LIVE pricing for country {country_id}...")
            
            pricing_response = await client.get(
                f"{SMSMAN_BASE_URL}/get-prices",
                params={
                    "token": SMSMAN_API_KEY,
                    "country_id": country_id
                }
            )
            
            print(f"💰 Country {country_id} pricing status: {pricing_response.status_code}")
            
            if pricing_response.status_code != 200:
                print(f"❌ Pricing API failed for country {country_id}")
                return []
            
            try:
                pricing_raw = pricing_response.json()
                print(f"📊 Country {country_id} pricing type: {type(pricing_raw)}")
                
            except json.JSONDecodeError as e:
                print(f"❌ Country {country_id} pricing JSON error: {e}")
                return []
            
            # Step 3: Parse country-specific pricing (same logic as main function)
            country_pricing = {}
            
            try:
                if isinstance(pricing_raw, list):
                    print(f"🔄 Processing LIST format for country {country_id}...")
                    for item in pricing_raw:
                        if isinstance(item, dict):
                            try:
                                service_id = int(item.get('application_id', 0))
                                cost = float(item.get('cost', 0))
                                count = int(item.get('count', 0))
                                
                                if service_id > 0 and cost > 0:
                                    country_pricing[service_id] = {
                                        'original': cost,
                                        'user_price': cost * PROFIT_MARGIN,
                                        'count': count
                                    }
                                    
                            except (ValueError, TypeError, KeyError):
                                continue
                    
                elif isinstance(pricing_raw, dict):
                    print(f"🔄 Processing DICT format for country {country_id}...")
                    
                    for key, value in pricing_raw.items():
                        try:
                            service_id = int(str(key).strip())
                            if isinstance(value, dict) and 'cost' in value:
                                original_cost = float(value['cost'])
                                country_pricing[service_id] = {
                                    'original': original_cost,
                                    'user_price': original_cost * PROFIT_MARGIN,
                                    'count': int(value.get('count', 0))
                                }
                        except (ValueError, TypeError):
                            # Handle nested format
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    try:
                                        service_id = int(str(sub_key).strip())
                                        if isinstance(sub_value, dict) and 'cost' in sub_value:
                                            original_cost = float(sub_value['cost'])
                                            country_pricing[service_id] = {
                                                'original': original_cost,
                                                'user_price': original_cost * PROFIT_MARGIN,
                                                'count': int(sub_value.get('count', 0))
                                            }
                                    except (ValueError, TypeError):
                                        continue
                
                print(f"✅ Country {country_id}: Parsed pricing for {len(country_pricing)} services")
                
            except Exception as e:
                print(f"❌ Country {country_id} pricing parsing error: {e}")
                return []
            
            # If no pricing for this country, return empty
            if not country_pricing:
                print(f"❌ No pricing data for country {country_id}")
                return []
            
            # Step 4: Build services list with country-specific pricing
            services = []
            
            if isinstance(services_data, dict):
                for service_id, service_info in services_data.items():
                    try:
                        clean_id = int(str(service_id).strip())
                        
                        if isinstance(service_info, dict):
                            clean_name = str(service_info.get('title', service_info.get('name', ''))).strip()
                        elif isinstance(service_info, str):
                            clean_name = str(service_info).strip()
                        else:
                            continue
                        
                        if clean_name and len(clean_name) > 1:
                            # ONLY ADD IF COUNTRY-SPECIFIC PRICING EXISTS
                            if clean_id in country_pricing:
                                pricing_info = country_pricing[clean_id]
                                user_price = pricing_info['user_price']
                                original_price = pricing_info['original']
                                
                                services.append({
                                    "id": clean_id,
                                    "name": clean_name,
                                    "display_price": f"₹{user_price:.2f}",
                                    "pricing": {
                                        "user_price": round(user_price, 2),
                                        "original_price": round(original_price, 2),
                                        "profit_amount": round(user_price - original_price, 2),
                                        "margin_percent": 70,
                                        "live_api": True,
                                        "availability": pricing_info['count'],
                                        "country_id": country_id
                                    }
                                })
                                
                    except Exception:
                        continue
                
                services.sort(key=lambda x: x['name'].lower())
                
                print(f"🎯 Country {country_id} RESULT: {len(services)} services with live pricing")
                
                if services:
                    samples = [(s['name'], s['display_price']) for s in services[:5]]
                    print(f"🌟 Country {country_id} samples: {samples}")
                    
                return services
                    
    except Exception as e:
        print(f"❌ Country {country_id} services error: {e}")
    
    return []
# Add this function to your existing smsman_client.py

async def get_sms(request_id: str) -> Dict[str, Any]:
    """Get SMS for a request ID"""
    
    try:
        if not SMSMAN_API_KEY:
            return {"error": "No API key available", "status": "error"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{SMSMAN_BASE_URL}/get-sms",
                params={
                    "token": SMSMAN_API_KEY,
                    "request_id": request_id
                }
            )
            
            print(f"📨 SMS API response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if isinstance(data, dict):
                        if "sms_code" in data and data["sms_code"]:
                            return {
                                "sms_code": data["sms_code"],
                                "sms_text": data.get("sms_text", ""),
                                "sender": data.get("sender", "Service"),
                                "status": "received"
                            }
                        elif data.get("status") == "wait":
                            return {"status": "waiting", "message": "Waiting for SMS"}
                        else:
                            return {"status": "waiting", "message": "No SMS yet"}
                            
                except json.JSONDecodeError:
                    pass
        
        return {"status": "waiting", "message": "Waiting for SMS"}
        
    except Exception as e:
        return {"error": str(e), "status": "error"}
