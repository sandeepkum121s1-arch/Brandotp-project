from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
import uvicorn
import os
import asyncio
import sqlite3
import time
from contextlib import suppress
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Import custom routers
from backend.routes import register_all_routers
from backend.routes.smsman_numbers import router as smsman_router

# PAY0 Configuration
PAY0_USER_TOKEN = "your-live-or-test-token"

# Security
security = HTTPBearer(auto_error=False)

# ✅ App Initialization (Only once!)
app = FastAPI(
    title="BrandOtp Official API",
    description="Complete OTP Service API with Authentication & Payments + SMSMan Integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://brandotpofficial.shop",
        "https://www.brandotpofficial.shop", 
        "https://brandotp-official.netlify.app",
        "https://brandotp-project1.onrender.com",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Database initialization
def init_database():
    """Initialize database with required tables"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create number_orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS number_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            country TEXT NOT NULL,
            amount REAL NOT NULL,
            sms_status TEXT DEFAULT 'waiting',
            order_status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database tables initialized")

# Helper function to get current user (simplified version)
async def get_current_user(request: Request):
    """Get current user from session/token - replace with your auth logic"""
    # This is a simplified version - replace with your actual authentication
    # For demo purposes, returning user_id = 1
    return {"user_id": 1, "username": "demo_user"}

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "detail": "Validation failed",
            "errors": [str(error) for error in exc.errors()]
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"❌ Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": "Internal server error. Please try again later."
        }
    )

# ✅ HISTORY API ROUTES - NEW ADDITIONS
@app.get("/api/history/numbers")
async def get_number_history(request: Request):
    """Get user's number purchase history"""
    try:
        # Get current user
        current_user = await get_current_user(request)
        user_id = current_user["user_id"]
        
        # Query database
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT order_id, service, phone_number, country, amount, sms_status, order_status, created_at
            FROM number_orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Format the data
        formatted_history = []
        for row in rows:
            formatted_history.append({
                'orderId': row['order_id'],
                'service': row['service'],
                'phoneNumber': row['phone_number'],
                'country': row['country'],
                'amount': f"₹{row['amount']:.2f}",
                'smsStatus': row['sms_status'],
                'orderStatus': row['order_status'],
                'dateTime': row['created_at']
            })
        
        return {
            "success": True,
            "history": formatted_history
        }
    
    except Exception as e:
        print(f"Error fetching history: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to fetch history"
            }
        )

@app.post("/api/buy-number")
async def buy_number_api(
    request: Request,
    service: str = Form(...),
    country: str = Form(...)
):
    """Buy a number and save to database"""
    try:
        # Get current user
        current_user = await get_current_user(request)
        user_id = current_user["user_id"]
        
        # Generate unique order ID
        order_id = f"ORD{int(time.time())}"
        
        # TODO: Replace with your actual SMS API call
        # Example API call to get number
        phone_number = "+91 98765 43210"  # Replace with actual API response
        amount = 25.00  # Set based on service/country
        
        # Save to database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO number_orders (order_id, user_id, service, phone_number, country, amount, sms_status, order_status)
            VALUES (?, ?, ?, ?, ?, ?, 'waiting', 'active')
        """, (order_id, user_id, service, phone_number, country, amount))
        
        conn.commit()
        conn.close()
        
        # TODO: Deduct amount from user balance
        
        return {
            "success": True,
            "order_id": order_id,
            "phone_number": phone_number,
            "amount": amount,
            "message": "Number purchased successfully!"
        }
    
    except Exception as e:
        print(f"Error buying number: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to purchase number"
            }
        )

@app.post("/api/update-sms-status")
async def update_sms_status(
    request: Request,
    order_id: str = Form(...),
    status: str = Form(...)  # 'received', 'timeout', 'cancelled'
):
    """Update SMS status when SMS is received"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Determine order status based on SMS status
        if status == 'received':
            order_status = 'completed'
        elif status == 'timeout':
            order_status = 'expired'
        elif status == 'cancelled':
            order_status = 'cancelled'
        else:
            order_status = 'active'
        
        cursor.execute("""
            UPDATE number_orders 
            SET sms_status = ?, order_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
        """, (status, order_status, order_id))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Status updated to {status}"
        }
    
    except Exception as e:
        print(f"Error updating SMS status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Failed to update status"
            }
        )

# ✅ Register all existing routers FIRST
register_all_routers(app)

# ✅ ADD SMSMan routes with /api/ prefix - IMPORTANT!
app.include_router(smsman_router, prefix="/api/smsman", tags=["SMSMan API"])

# Frontend Configuration
frontend_dir = "frontend"
assets_dir = os.path.join(frontend_dir, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    print("✅ Static assets mounted at /assets")
else:
    print(f"⚠️ Assets directory not found at: {assets_dir}")

# Helper for HTML file serving
def serve_html_file(page: str, fallback_html: str):
    page_path = os.path.join(frontend_dir, f"{page}.html")
    if os.path.exists(page_path):
        return FileResponse(page_path, media_type='text/html')
    return HTMLResponse(content=fallback_html, status_code=200)

# Page Routes
@app.get("/", response_class=HTMLResponse)
async def serve_root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BrandOtp Official - SMS & OTP Services</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .logo { text-align: center; margin-bottom: 40px; }
            .logo h1 { color: #4361ee; font-size: 2.5rem; margin: 0; }
            .services { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 40px 0; }
            .service-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; transition: transform 0.2s; }
            .service-card:hover { transform: translateY(-2px); }
            .btn { display: inline-block; background: #4361ee; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px; }
            .btn:hover { background: #3651ce; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <h1>🚀 BrandOtp Official</h1>
                <p>Premium SMS & OTP Services</p>
            </div>
            
            <div class="services">
                <div class="service-card">
                    <h3>📱 SMS Numbers</h3>
                    <p>Get virtual numbers for OTP verification</p>
                    <a href="/buy-number" class="btn">Buy Number</a>
                </div>
                
                <div class="service-card">
                    <h3>💰 Wallet</h3>
                    <p>Manage your account balance</p>
                    <a href="/wallet" class="btn">View Wallet</a>
                </div>
                
                <div class="service-card">
                    <h3>📊 History</h3>
                    <p>View your purchase history</p>
                    <a href="/history" class="btn">View History</a>
                </div>
                
                <div class="service-card">
                    <h3>👤 Account</h3>
                    <p>Login or Register</p>
                    <a href="/login" class="btn">Login</a>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                <p><strong>🔥 API Status: ACTIVE</strong></p>
                <a href="/docs" class="btn">API Documentation</a>
                <a href="/api/health" class="btn">Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/login", response_class=HTMLResponse)
async def serve_login():
    return serve_html_file("login", """
    <!DOCTYPE html>
    <html>
    <head><title>Login - BrandOtp</title></head>
    <body>
        <h1>Login</h1>
        <p>Login page will be here</p>
        <a href="/">← Back to Home</a>
    </body>
    </html>
    """)

@app.get("/register", response_class=HTMLResponse)
async def serve_register():
    return serve_html_file("register", """
    <!DOCTYPE html>
    <html>
    <head><title>Register - BrandOtp</title></head>
    <body>
        <h1>Register</h1>
        <p>Registration page will be here</p>
        <a href="/">← Back to Home</a>
    </body>
    </html>
    """)

@app.get("/wallet", response_class=HTMLResponse)
async def serve_wallet():
    return serve_html_file("wallet", """
    <!DOCTYPE html>
    <html>
    <head><title>Wallet - BrandOtp</title></head>
    <body>
        <h1>Wallet</h1>
        <p>Wallet management page will be here</p>
        <a href="/">← Back to Home</a>
    </body>
    </html>
    """)

@app.get("/buy-number", response_class=HTMLResponse)
async def serve_buy_number():
    return serve_html_file("buy-number", """
    <!DOCTYPE html>
    <html>
    <head><title>Buy Number - BrandOtp</title></head>
    <body>
        <h1>Buy Number</h1>
        <p>Number purchase page will be here</p>
        <a href="/">← Back to Home</a>
    </body>
    </html>
    """)

@app.get("/history", response_class=HTMLResponse)
async def serve_history():
    return serve_html_file("history", """
    <!DOCTYPE html>
    <html>
    <head><title>History - BrandOtp</title></head>
    <body>
        <h1>History</h1>
        <p>Purchase history will be here</p>
        <a href="/">← Back to Home</a>
    </body>
    </html>
    """)

# Health Check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "BrandOtp Official API",
        "version": "1.0.0",
        "timestamp": time.time()
    }

# ✅ Startup Event
@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    print("🚀 Starting BrandOtp Official API...")
    init_database()
    print("✅ API Ready!")

# ✅ Main function for local development
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
