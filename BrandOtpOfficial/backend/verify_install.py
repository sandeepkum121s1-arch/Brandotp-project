# Test if python-dotenv is properly installed
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv imported successfully!")
    
    # Test environment loading
    import os
    load_dotenv()
    print(f"✅ load_dotenv() executed successfully!")
    print(f"✅ .env file exists: {os.path.exists('.env')}")
    print(f"✅ MONGO_URI in env: {'MONGO_URI' in os.environ}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
