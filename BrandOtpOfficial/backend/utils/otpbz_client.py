import httpx, os, json

API_KEY = os.getenv("OTPBZ_API_KEY")
BASE = "https://flashsms.pro/stubs/handler_api.php"

async def _raw(action: str, **kw):
    params = {"api_key": API_KEY, "action": action, **kw}
    async with httpx.AsyncClient(timeout=15) as c:
        txt = (await c.get(BASE, params=params)).text.strip()
    
    # Better error handling
    if any(err in txt for err in ["BAD_KEY", "ERROR_SQL", "NO_BALANCE", "NO_NUMBERS", "BAD_SERVICE", "BAD_SERVER"]):
        raise RuntimeError(txt)
    return txt

async def balance() -> float:
    try:
        txt = await _raw("getBalance")
        if ":" in txt:
            return float(txt.split(":")[1])
        return 0.0
    except:
        return 0.0

def _merge_services(api_services: list[str], popular_services: list[str]) -> list[str]:
    """Merge API services with popular ones, remove duplicates, preserve order"""
    # Clean both lists
    clean_api = [s.strip().replace("{", "").replace("}", "").replace('"', '') 
                 for s in api_services if s and len(str(s).strip()) >= 2]
    
    # Combine and deduplicate while preserving order
    combined = clean_api + popular_services
    seen = set()
    result = []
    for service in combined:
        service = str(service).strip()
        if service and len(service) >= 2 and service.isalnum() and service not in seen:
            seen.add(service)
            result.append(service)
    
    return result[:60]  # Limit for better UX

async def services() -> list[str]:
    try:
        # Get API response
        txt = await _raw("getServices")
        print(f"API Response: {txt[:200]}")  # Debug log
        
        api_services = []
        
        # Try JSON parsing first
        if txt.startswith('{') or txt.startswith('['):
            try:
                data = json.loads(txt)
                if isinstance(data, dict):
                    api_services = list(data.keys())
                elif isinstance(data, list):
                    api_services = data
            except json.JSONDecodeError:
                pass
        
        # Fallback to line-by-line parsing
        if not api_services:
            for line in txt.splitlines():
                line = line.strip()
                if line and ":" in line:
                    code = line.split(":")[0].strip()
                    if code:
                        api_services.append(code)
        
        # Popular services (Admin confirmed these should be available)
        popular_services = [
            "wa", "fb", "ig", "tg", "go", "tw", "ub", "nf", "ts", 
            "am", "re", "oi", "wx", "wb", "ma", "mm", "dh", "ew",
            "hw", "ka", "lf", "mb", "dr", "rv", "adani", "angelone"
        ]
        
        # Merge and return
        merged = _merge_services(api_services, popular_services)
        print(f"Final services count: {len(merged)}")  # Debug log
        return sorted(merged) if merged else popular_services[:20]
        
    except Exception as e:
        print(f"Services error: {e}")
        # Comprehensive fallback
        return [
            "wa", "fb", "ig", "tg", "go", "tw", "ub", "nf", "ts", "am",
            "re", "oi", "wx", "wb", "ma", "mm", "dh", "ew", "hw", "ka",
            "lf", "mb", "dr", "rv", "4fun", "51exch", "51game", "567slots"
        ]

async def servers() -> list[int]:
    try:
        txt = await _raw("getServers")
        print(f"Servers API Response: {txt[:200]}")  # Debug log
        
        servers_list = []
        for line in txt.splitlines():
            line = line.strip()
            if line and (":" in line or line.isdigit()):
                try:
                    # Extract server number
                    if ":" in line:
                        server_part = line.split(":")[0].strip()
                    else:
                        server_part = line
                    
                    # Remove non-digit characters
                    server_num = ''.join(filter(str.isdigit, server_part))
                    if server_num:
                        servers_list.append(int(server_num))
                except ValueError:
                    continue
        
        # Default servers if empty
        if not servers_list:
            servers_list = [2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15]
        
        return sorted(list(set(servers_list)))[:15]  # Remove duplicates, sort, limit
        
    except Exception as e:
        print(f"Servers error: {e}")
        return [2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15]

async def buy(service: str, server: int):
    txt = await _raw("getNumber", service=service, server=server)
    if "ACCESS_NUMBER:" in txt:
        parts = txt.split(":")
        if len(parts) >= 3:
            return {"id": int(parts[1]), "number": parts[2]}
    raise RuntimeError("Failed to buy number")

async def sms(oid: int):
    txt = await _raw("getStatus", id=oid)
    if txt.startswith("STATUS_OK:"):
        return txt.split(":", 1)[1]
    return None

async def cancel(oid: int):
    await _raw("setStatus", id=oid, status=8)
