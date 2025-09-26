#!/usr/bin/env python3
"""
BrandOtp Official Server Runner
Run this file from project root to start the FastAPI server
"""

import uvicorn
import os
import sys
from pathlib import Path

def main():
    """Main server runner function"""
    
    # Get project root directory
    project_root = Path(__file__).parent.absolute()
    print(f"🚀 Starting BrandOtp Official Server...")
    print(f"📁 Project root: {project_root}")
    
    # Add project root to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"✅ Added {project_root} to Python path")
    
    # Change working directory to project root
    os.chdir(project_root)
    print(f"✅ Changed working directory to: {os.getcwd()}")
    
    # Verify backend directory exists
    backend_dir = project_root / "backend"
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        print("Please ensure you're running this from the correct project root.")
        return
    
    # Verify main.py exists
    main_py = backend_dir / "main.py"
    if not main_py.exists():
        print(f"❌ main.py not found: {main_py}")
        return
    
    print(f"✅ Found backend/main.py: {main_py}")
    
    # Verify .env file exists
    env_file = backend_dir / ".env"
    if env_file.exists():
        print(f"✅ Found .env file: {env_file}")
    else:
        print(f"⚠️ .env file not found: {env_file}")
        print("Make sure to create .env file with MongoDB connection string")
    
    print("\n🔄 Starting Uvicorn server...")
    print("📝 Access points:")
    print("   • API: http://localhost:8000")
    print("   • Docs: http://localhost:8000/docs")
    print("   • Login: http://localhost:8000/login")
    print("   • Signup: http://localhost:8000/signup")
    print("\n⚡ Server will auto-reload on file changes")
    print("⏹️  Press Ctrl+C to stop\n")
    
    try:
        # Run server
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["backend", "frontend"],
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
