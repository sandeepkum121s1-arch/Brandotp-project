
- # BrandOTP Application
- 
- A full-stack application for OTP service management with admin dashboard.
- 
- ## Setup Instructions
- 
- ### Backend Setup
- 
- 1. Navigate to the backend directory
-    ```
-    cd backend
-    ```
- 
- 2. Create a virtual environment (optional but recommended)
-    ```
-    python -m venv venv
-    venv\Scripts\activate  # On Windows
-    source venv/bin/activate  # On macOS/Linux
-    ```
- 
- 3. Install dependencies
-    ```
-    pip install -r requirements.txt
-    ```
- 
- 4. Create a `.env` file based on `.env.example`
-    ```
-    cp .env.example .env
-    ```
-    Then edit the `.env` file with your actual configuration values.
- 
- 5. Run the backend server
-    ```
-    uvicorn main:app --reload --host 0.0.0.0 --port 8000
-    ```
-    Alternatively, you can use the provided batch file:
-    ```
-    ..\run_backend.bat
-    ```
- 
- ### Frontend Setup
- 
- 1. The frontend is built with vanilla JavaScript and can be served using any static file server.
- 
- 2. For development, you can use the Live Server extension in VS Code or any other static file server.
- 
- 3. Make sure the `API_BASE_URL` in `frontend/app.js` points to your backend server.
- 
- ## Features
- 
- - User authentication (signup, login)
- - Service management
- - OTP request handling
- - Wallet management
- - Admin dashboard
- - Transaction history
- 
- ## Technologies Used
+ ## How to run (dev)
  
- - **Backend**: FastAPI, MongoDB, JWT Authentication
- - **Frontend**: HTML, CSS, JavaScript
- - **Payment Integration**: Pay0 API
- - **OTP Service**: OTPBazaar API
+ 1. Create a virtual environment:
+    - On Linux/macOS: `python -m venv .venv && source .venv/bin/activate`
+    - On Windows: `python -m venv .venv && .venv\Scripts\activate`
+ 2. Install dependencies:
+    - `pip install -r backend/requirements.txt`
+ 3. Copy environment file and fill values:
+    - `cp backend/.env.example backend/.env` (or manually create `backend/.env`)
+ 4. Run the development server:
+    - `uvicorn backend.main:app --reload`
+    - Or: `python backend/run_server.py`
+ 5. Health check:
+    - Open: GET http://localhost:8000/health → `{"status":"ok"}`