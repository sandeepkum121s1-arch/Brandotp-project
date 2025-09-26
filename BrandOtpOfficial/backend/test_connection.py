import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

print("🔍 Environment Variables Test:")
print(f"MONGO_URI exists: {'MONGO_URI' in os.environ}")
print(f"MONGO_URI value: {os.getenv('MONGO_URI', 'NOT_FOUND')[:60]}...")

# Test MongoDB connection
try:
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        raise ValueError("MONGO_URI not found")
    
    print("🔄 Testing MongoDB connection...")
    client = MongoClient(mongo_uri)
    
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB Atlas connection successful!")
    
    # Test database operations
    db = client.brandotp
    collection = db.test_collection
    
    # Insert test document
    test_doc = {"test": "connection", "timestamp": "now"}
    result = collection.insert_one(test_doc)
    print(f"✅ Test document inserted: {result.inserted_id}")
    
    # Clean up
    collection.delete_one({"_id": result.inserted_id})
    print("✅ Test document cleaned up")
    
except Exception as e:
    print(f"❌ Connection test failed: {e}")
    
    # Debug info
    print("\n🔍 Debug Information:")
    print(f"Current directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    with open('.env', 'r') as f:
        content = f.read()
        print(f".env file content length: {len(content)}")
        print("First few lines:")
        for i, line in enumerate(content.split('\n')[:3]):
            print(f"  {i+1}: {line[:50]}...")
