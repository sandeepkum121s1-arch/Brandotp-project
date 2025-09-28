# Test script to verify imports

try:
    from models import OtpRequestCreate, OtpRequestResponse, OtpRequestInDB
    print("Import from models package successful!")
except ImportError as e:
    print(f"Import from models package failed: {e}")

try:
    from models.py import OtpRequestCreate, OtpRequestResponse, OtpRequestInDB
    print("Import from models.py successful!")
except ImportError as e:
    print(f"Import from models.py failed: {e}")

try:
    import models
    print("Import models module successful!")
    print(f"Available attributes: {dir(models)}")
except ImportError as e:
    print(f"Import models module failed: {e}")