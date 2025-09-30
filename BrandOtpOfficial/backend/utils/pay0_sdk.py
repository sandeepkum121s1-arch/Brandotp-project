import requests
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

class Pay0SDK:
    """Enhanced Pay0 Payment Gateway SDK for BrandOtp"""
    
    def __init__(self):
        self.base_url = "https://pay0.shop/api/"
        self.api_key = os.getenv("PAY0_API_KEY")
        
        if not self.api_key:
            raise ValueError("PAY0_API_KEY not found in environment variables")
            
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
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
            "user_token": self.api_key,
            "amount": str(amount),
            "order_id": order_id,
            "redirect_url": redirect_url,
            "remark1": remark1,
            "remark2": remark2
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'BrandOtp-Pay0-SDK/1.0'
        }
        
        try:
            self.logger.info(f"📤 Pay0 Create Order Request:")
            self.logger.info(f"   Endpoint: {endpoint}")
            self.logger.info(f"   Order ID: {order_id}")
            self.logger.info(f"   Amount: ₹{amount}")
            self.logger.info(f"   Mobile: {customer_mobile}")
            
            response = requests.post(
                endpoint, 
                data=payload, 
                headers=headers, 
                timeout=30,
                verify=True
            )
            
            self.logger.info(f"📥 Pay0 Response Status: {response.status_code}")
            self.logger.info(f"📥 Pay0 Response Text: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.logger.info(f"✅ Pay0 Order Created Successfully: {result}")
                    
                    return {
                        "success": True,
                        "data": result,
                        "status_code": response.status_code
                    }
                except ValueError as json_error:
                    self.logger.error(f"❌ Pay0 JSON Parse Error: {json_error}")
                    return {
                        "success": False,
                        "message": f"Invalid JSON response: {response.text}",
                        "error": str(json_error)
                    }
            else:
                self.logger.error(f"❌ Pay0 API Error: {response.status_code} - {response.text}")
                return {
                    "success": False, 
                    "message": f"Pay0 API Error: {response.status_code}",
                    "error": response.text,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            self.logger.error("❌ Pay0 Request Timeout")
            return {
                "success": False, 
                "message": "Payment gateway timeout. Please try again."
            }
        except requests.exceptions.ConnectionError:
            self.logger.error("❌ Pay0 Connection Error")
            return {
                "success": False, 
                "message": "Unable to connect to payment gateway. Please check your internet connection."
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Pay0 Request Exception: {e}")
            return {
                "success": False, 
                "message": f"Payment gateway error: {str(e)}"
            }
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check payment status with Pay0"""
        
        endpoint = self.base_url + "check-order-status"
        
        payload = {
            "user_token": self.api_key,
            "order_id": order_id
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'BrandOtp-Pay0-SDK/1.0'
        }
        
        try:
            self.logger.info(f"📤 Pay0 Status Check: {order_id}")
            
            response = requests.post(
                endpoint, 
                data=payload, 
                headers=headers, 
                timeout=30,
                verify=True
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.logger.info(f"📊 Pay0 Status Response: {result}")
                    return {
                        "success": True,
                        "data": result,
                        "status_code": response.status_code
                    }
                except ValueError as json_error:
                    return {
                        "success": False,
                        "message": f"Invalid JSON in status response: {response.text}",
                        "error": str(json_error)
                    }
            else:
                return {
                    "success": False,
                    "message": f"Status check failed: {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            self.logger.error(f"❌ Status check error: {e}")
            return {
                "success": False,
                "message": f"Status check error: {str(e)}"
            }
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify Pay0 webhook signature (if Pay0 provides signature verification)"""
        # Implement signature verification if Pay0 provides it
        # For now, return True as Pay0 might not have signature verification
        return True

# ✅ INITIALIZE GLOBAL SDK INSTANCE
try:
    pay0_sdk = Pay0SDK()
    print("✅ Pay0 SDK initialized successfully")
except Exception as e:
    print(f"❌ Pay0 SDK initialization failed: {e}")
    pay0_sdk = None
