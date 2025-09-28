import requests
import os
from datetime import datetime
from typing import Dict, Any, Optional

class Pay0SDK:
    """Pay0 Payment Gateway SDK for BrandOtp"""
    
    def __init__(self):
        self.base_url = "https://pay0.shop/api/"
        self.api_key = os.getenv("PAY0_API_KEY")
        
        if not self.api_key:
            raise ValueError("PAY0_API_KEY not found in environment variables")
    
    def create_order(
        self, 
        customer_mobile: str, 
        amount: float, 
        order_id: str, 
        redirect_url: str,
        remark1: str = "BrandOtp Wallet Recharge",
        remark2: str = "Add money to wallet"
    ) -> Dict[str, Any]:
        """Create payment order with Pay0"""
        
        endpoint = self.base_url + "create-order"
        
        payload = {
            "customer_mobile": customer_mobile,
            "user_token": self.api_key,  # Using API key as user token
            "amount": str(amount),
            "order_id": order_id,
            "redirect_url": redirect_url,
            "remark1": remark1,
            "remark2": remark2
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            print(f"📤 Pay0 Create Order Request:")
            print(f"   Endpoint: {endpoint}")
            print(f"   Order ID: {order_id}")
            print(f"   Amount: ₹{amount}")
            print(f"   Mobile: {customer_mobile}")
            
            response = requests.post(endpoint, data=payload, headers=headers, timeout=30)
            
            print(f"📥 Pay0 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Pay0 Order Created: {result}")
                return {
                    "success": True,
                    "data": result
                }
            else:
                print(f"❌ Pay0 API Error: {response.status_code} - {response.text}")
                return {
                    "success": False, 
                    "message": f"Pay0 API Error: {response.status_code}",
                    "error": response.text
                }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Pay0 Request Exception: {e}")
            return {
                "success": False, 
                "message": f"Network error: {str(e)}"
            }
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check payment status with Pay0"""
        
        endpoint = self.base_url + "check-order-status"
        
        payload = {
            "user_token": self.api_key,
            "order_id": order_id
        }
        
        try:
            print(f"📤 Pay0 Status Check: {order_id}")
            
            response = requests.post(endpoint, data=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"📊 Pay0 Status: {result}")
                return {
                    "success": True,
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "message": f"Status check failed: {response.status_code}"
                }
                
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return {
                "success": False,
                "message": str(e)
            }

# Initialize global SDK instance
pay0_sdk = Pay0SDK()
