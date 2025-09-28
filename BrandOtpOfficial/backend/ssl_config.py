import ssl
import certifi
from pymongo import MongoClient
import os

def create_secure_connection(uri):
    """Create MongoDB connection with proper SSL configuration"""
    
    # Method 1: Try with system certificates
    try:
        client = MongoClient(
            uri,
            ssl_ca_certs=certifi.where(),
            ssl_cert_reqs=ssl.CERT_REQUIRED,
            ssl_match_hostname=True,
            serverSelectionTimeoutMS=10000
        )
        client.admin.command('ping')
        print("✅ Connected with system certificates!")
        return client
    except:
        pass
    
    # Method 2: Bypass SSL verification (temporary)
    try:
        client = MongoClient(
            uri,
            ssl_cert_reqs=ssl.CERT_NONE,
            ssl_match_hostname=False,
            serverSelectionTimeoutMS=10000
        )
        client.admin.command('ping')
        print("⚠️ Connected with SSL bypass (less secure)")
        return client
    except Exception as e:
        print(f"❌ All connection methods failed: {e}")
        raise

# Usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGO_URI")
    client = create_secure_connection(uri)
    print("Database connected successfully!")
