import os
import requests
from dotenv import load_dotenv
  
# Load environment variables
load_dotenv()
  
USE_PAYMENTS_SANDBOX = os.getenv("USE_PAYMENTS_SANDBOX", "true").lower() == "true"

class PayProSDK:
    def __init__(self, base_url="https://pay0.shop"):
        self.base_url = base_url
      
    def create_order(self, customer_mobile, user_token, amount, order_id, redirect_url, remark1="", remark2=""):
        """
        Create a payment order with the Pay0 payment gateway.
        
        Args:
            customer_mobile (str): Customer's phone number
            user_token (str): User's authentication token
            amount (float): Payment amount
            order_id (str): Unique order ID
            redirect_url (str): Callback/redirect URL after payment
            remark1 (str, optional): Custom remark 1
            remark2 (str, optional): Custom remark 2

        Returns:
            dict: Response from the payment gateway
        """

        # Sandbox mode (no real API call)
        if USE_PAYMENTS_SANDBOX:
            payment_url = f"https://sandbox.payments.local/pay?order_id={order_id}&amount={amount}&token={user_token}"
            return {
                "success": True,
                "order_id": order_id,
                "payment_url": payment_url,
                "amount": amount,
                "status": "CREATED"
            }

        # Production mode (real API call)
        try:
            endpoint = f"{self.base_url}/api/create-order"
            
            # Example payload (adjust according to Pay0 API docs)
            payload = {
                "customer_mobile": customer_mobile,
                "user_token": user_token,
                "amount": amount,
                "order_id": order_id,
                "redirect_url": redirect_url,
                "remark1": remark1,
                "remark2": remark2
            }

            response = requests.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()

            return response.json()
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
