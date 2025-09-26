import os
import requests
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USE_PAYMENTS_SANDBOX = os.getenv("USE_PAYMENTS_SANDBOX", "true").lower() == "true"

class OrderStatusSDK:
    def __init__(self, base_url="https://pay0.shop"):
        self.base_url = base_url

    def check_status(self, order_id, user_token):
        """
        Check the status of a payment order with the Pay0 payment gateway
        ...
        Returns:
            dict: Response containing order status
        """
        # In a real implementation, this would make an API call to the payment gateway
        # For now, we'll return a simulated response
        if USE_PAYMENTS_SANDBOX:
            return {
                "success": True,
                "order_id": order_id,
                "status": "success",
                "transaction_id": f"sandbox_txn_{order_id[:8]}"
            }
        try:
            # Construct API endpoint
            endpoint = f"{self.base_url}/api/order-status"
            payload = {
                "order_id": order_id,
                "token": user_token
            }
            # response = requests.post(endpoint, json=payload)
            # result = response.json()
            result = {
                "success": True,
                "order_id": order_id,
                "status": "PENDING",  # Could be PENDING, COMPLETED, FAILED, etc.
                "transaction_id": f"txn_{uuid.uuid4().hex[:10]}"
            }
            return result
        except Exception as e:
            # Handle exceptions
            return {
                "success": False,
                "error": str(e)
            }

    def check_order_status(self, user_token, order_id):
        """
        Alternative method to check order status with different parameter order
        ...
        Returns:
            dict: Response containing order status
        """
        # This is just a wrapper around check_status with reversed parameters
        return self.check_status(order_id, user_token)
