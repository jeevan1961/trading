from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Optional
import os
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
import httpx
import json
import uuid
from models import (
    CandleData, Instrument, PatternDetection,
    MarketStructure, LiquidityPool, UserSession,
    PaperTradingAccount
)
from price_action_analyzer import PriceActionAnalyzer
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Upstox Configuration
UPSTOX_API_KEY = os.environ.get('UPSTOX_API_KEY')
UPSTOX_API_SECRET = os.environ.get('UPSTOX_API_SECRET')
UPSTOX_REDIRECT_URI = os.environ.get('UPSTOX_REDIRECT_URI')
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-secret-key')

# Create the main app
app = FastAPI(title="Institutional Trading Dashboard API")

# Create API router
api_router = APIRouter(prefix="/api")

# Initialize Price Action Analyzer
analyzer = PriceActionAnalyzer()

# NSE 500 Stock Symbols (starting with top 10)
NSE_STOCKS = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TATAMOTORS",
    "SBIN", "AXISBANK", "TCS", "BAJFINANCE", "KOTAKBANK"
]

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.subscriptions: Dict[str, set] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logging.info(f"Client {user_id} connected")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logging.info(f"Client {user_id} disconnected")

    async def broadcast_market_data(self, data: dict, instrument_key: str):
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json({
                        "type": "market_update",
                        "instrument_key": instrument_key,
                        "data": data
                    })
                except:
                    pass

manager = ConnectionManager()

# JWT Token Creation
def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTHENTICATION ENDPOINTS ====================

@api_router.get("/auth/login")
async def login():
    """Initiate Upstox OAuth 2.0 flow."""
    state = str(uuid.uuid4())
    auth_url = (
        f"https://api.upstox.com/v2/login/authorization/dialog?"
        f"response_type=code&client_id={UPSTOX_API_KEY}"
        f"&redirect_uri={UPSTOX_REDIRECT_URI}&state={state}"
    )
    return RedirectResponse(url=auth_url)

@api_router.get("/auth/callback")
async def oauth_callback(code: str = Query(...), state: str = Query(...)):
    """Handle OAuth callback and exchange code for access token."""
    try:
        token_url = "https://api.upstox.com/v2/login/authorization/token"

        token_data = {
            "code": code,
            "client_id": UPSTOX_API_KEY,
            "client_secret": UPSTOX_API_SECRET,
            "redirect_uri": UPSTOX_REDIRECT_URI,
            "grant_type": "authorization_code"
        }

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")

        token_response = response.json()
        access_token = token_response.get("access_token")

        # Store session in MongoDB
        session_doc = {
            "id": str(uuid.uuid4()),
            "access_token": access_token,
            "token_obtained_at": datetime.utcnow(),
            "token_expires_at": datetime.utcnow() + timedelta(hours=20),
            "state": state,
            "created_at": datetime.utcnow()
        }

        await db.user_sessions.insert_one(session_doc)

        # Create JWT token for frontend
        jwt_token = create_access_token({"sub": session_doc["id"], "upstox_token": access_token})

        return {
            "status": "success",
            "jwt_token": jwt_token,
            "upstox_token": access_token,
            "expires_at": session_doc["token_expires_at"].isoformat()
        }

    except Exception as e:
        logging.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/simple-login")
async def simple_login(username: str, password: str):
    """Simple JWT authentication for demo purposes."""
    # In production, validate against database
    if username == "admin" and password == "admin123":
        token = create_access_token({"sub": username, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# ==================== INSTRUMENTS ENDPOINTS ====================

@api_router.get("/instruments")
async def get_instruments():
    """Get list of NSE 500 instruments."""
    # Return cached instruments or fetch from Upstox
    cached = await db.instruments.find({}).to_list(500)
    if cached:
        return {"status": "success", "instruments": cached}

    # Return hardcoded top 10 for now
    instruments = [
        {"symbol": symbol, "exchange": "NSE", "instrument_key": f"NSE_EQ|{symbol}"}
        for symbol in NSE_STOCKS
    ]
    return {"status": "success", "instruments": instruments}

@api_router.get("/instruments/{symbol}")
async def get_instrument_details(symbol: str):
    """Get details of specific instrument."""
    instrument = await db.instruments.find_one({"trading_symbol": symbol.upper()})
    if not instrument:
        return {
            "symbol": symbol.upper(),
            "exchange": "NSE",
            "instrument_key": f"NSE_EQ|{symbol.upper()}"
        }
    return instrument

# ==================== MARKET DATA ENDPOINTS ====================

@api_router.get("/candles/historical")
async def get_historical_candles(
    instrument_key: str,
    interval: str = "1minute",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """Fetch historical OHLCV data."""
    try:
        # Check cache first
        cached_candles = await db.candles.find({
            "instrument_key": instrument_key,
            "interval": interval
        }, {"_id": 0}).sort("timestamp", -1).limit(500).to_list(500)

        if cached_candles:
            # Convert ISO timestamps back to datetime strings
            for candle in cached_candles:
                if isinstance(candle.get("timestamp"), str):
                    pass  # Already ISO format

            return {
                "status": "success",
                "instrument_key": instrument_key,
                "interval": interval,
                "candles": cached_candles,
                "source": "cache"
            }

        # Generate mock data for demo (replace with Upstox API call)
        mock_candles = generate_mock_candles(100)

        # Store in cache (convert datetime to ISO format for MongoDB)
        for candle in mock_candles:
            candle_copy = candle.copy()
            candle_copy["instrument_key"] = instrument_key
            candle_copy["interval"] = interval
            if isinstance(candle_copy.get("timestamp"), datetime):
                candle_copy["timestamp"] = candle_copy["timestamp"].isoformat()
            await db.candles.insert_one(candle_copy)

        return {
            "status": "success",
            "instrument_key": instrument_key,
            "interval": interval,
            "candles": mock_candles,
            "source": "generated"
        }

    except Exception as e:
        logging.error(f"Error fetching candles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/candles/intraday")
async def get_intraday_candles(
    instrument_key: str,
    interval: str = "1minute"
):
    """Fetch intraday OHLCV data for current trading day."""
    try:
        # Get today's candles
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        candles = await db.candles.find({
            "instrument_key": instrument_key,
            "interval": interval,
            "timestamp": {"$gte": today_start.isoformat()}
        }, {"_id": 0}).sort("timestamp", 1).to_list(500)

        if not candles:
            # Generate mock intraday data
            candles = generate_mock_candles(50)

        return {
            "status": "success",
            "instrument_key": instrument_key,
            "candles": candles
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PRICE ACTION ANALYSIS ENDPOINTS ====================

@api_router.get("/analysis/price-action")
async def analyze_price_action(
    instrument_key: str,
    interval: str = "1minute"
):
    """Perform institutional price action analysis."""
    try:
        # Get recent candles
        candles = await db.candles.find({
            "instrument_key": instrument_key,
            "interval": interval
        }, {"_id": 0}).sort("timestamp", -1).limit(200).to_list(200)

        if len(candles) < 20:
            raise HTTPException(status_code=400, detail="Insufficient data for analysis")

        # Reverse to chronological order
        candles.reverse()

        # Perform analysis
        analysis = analyzer.analyze_candles(candles)

        # Store patterns in database
        if analysis.get("liquidity_traps"):
            for trap in analysis["liquidity_traps"]:
                pattern_doc = {
                    "id": str(uuid.uuid4()),
                    "instrument_key": instrument_key,
                    "pattern_type": "liquidity_trap",
                    "timestamp": datetime.utcnow(),
                    "data": trap,
                    "confidence": trap.get("confidence", "medium")
                }
                await db.patterns.insert_one(pattern_doc)

        return {
            "status": "success",
            "instrument_key": instrument_key,
            "analysis": analysis
        }

    except Exception as e:
        logging.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analysis/market-structure")
async def get_market_structure(instrument_key: str):
    """Get current market structure analysis."""
    candles = await db.candles.find({
        "instrument_key": instrument_key
    }, {"_id": 0}).sort("timestamp", -1).limit(100).to_list(100)

    if len(candles) < 20:
        return {"error": "Insufficient data"}

    candles.reverse()
    structure = analyzer.detect_market_structure(candles)

    return {
        "status": "success",
        "instrument_key": instrument_key,
        "market_structure": structure
    }

@api_router.get("/analysis/liquidity-zones")
async def get_liquidity_zones(instrument_key: str):
    """Get detected liquidity pools and zones."""
    candles = await db.candles.find({
        "instrument_key": instrument_key
    }, {"_id": 0}).sort("timestamp", -1).limit(150).to_list(150)

    candles.reverse()
    pools = analyzer.detect_liquidity_pools(candles)

    return {
        "status": "success",
        "instrument_key": instrument_key,
        "liquidity_pools": pools
    }

# ==================== PAPER TRADING ENDPOINTS ====================

@api_router.post("/paper-trading/create-account")
async def create_paper_account(user_id: str, initial_balance: float = 100000.0):
    """Create a paper trading account."""
    account_doc = {
        "user_id": user_id,
        "balance": initial_balance,
        "positions": [],
        "orders": [],
        "created_at": datetime.utcnow()
    }

    result = await db.paper_accounts.insert_one(account_doc)
    return {
        "status": "success",
        "account_id": str(result.inserted_id),
        "balance": initial_balance
    }

@api_router.get("/paper-trading/account/{user_id}")
async def get_paper_account(user_id: str):
    """Get paper trading account details."""
    account = await db.paper_accounts.find_one({"user_id": user_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account["_id"] = str(account["_id"])
    return {"status": "success", "account": account}

@api_router.post("/paper-trading/order")
async def place_paper_order(
    user_id: str,
    instrument_key: str,
    order_type: str,  # buy/sell
    quantity: int,
    price: float
):
    """Place a paper trading order."""
    account = await db.paper_accounts.find_one({"user_id": user_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    order = {
        "id": str(uuid.uuid4()),
        "instrument_key": instrument_key,
        "type": order_type,
        "quantity": quantity,
        "price": price,
        "status": "executed",
        "timestamp": datetime.utcnow()
    }

    # Update account
    if order_type == "buy":
        cost = price * quantity
        if account["balance"] < cost:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        account["balance"] -= cost
        account["positions"].append({
            "instrument_key": instrument_key,
            "quantity": quantity,
            "avg_price": price,
            "current_value": price * quantity
        })

    account["orders"].append(order)

    await db.paper_accounts.update_one(
        {"user_id": user_id},
        {"$set": account}
    )

    return {"status": "success", "order": order, "balance": account["balance"]}

# ==================== WEBSOCKET ENDPOINT ====================

@app.websocket("/ws/market-data")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...)
):
    """WebSocket endpoint for real-time market data."""
    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                instrument_keys = data.get("instrument_keys", [])

                # Send confirmation
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "instruments": instrument_keys
                })

                # Send initial data
                for key in instrument_keys:
                    candles = await db.candles.find({
                        "instrument_key": key
                    }).sort("timestamp", -1).limit(1).to_list(1)

                    if candles:
                        await websocket.send_json({
                            "type": "market_update",
                            "instrument_key": key,
                            "data": candles[0]
                        })

            elif data.get("type") == "unsubscribe":
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)

# ==================== HELPER FUNCTIONS ====================

def generate_mock_candles(count: int) -> List[dict]:
    """Generate mock candlestick data for testing."""
    candles = []
    base_price = 150.0
    base_time = datetime.utcnow() - timedelta(minutes=count)

    for i in range(count):
        # Random walk
        change = (hash(str(i)) % 100 - 50) / 100
        base_price += change

        candle = {
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "open": base_price,
            "high": base_price + abs(change) * 2,
            "low": base_price - abs(change) * 2,
            "close": base_price + change,
            "volume": 10000 + (hash(str(i)) % 50000)
        }
        candles.append(candle)

    return candles

# ==================== MAIN APP SETUP ====================

# Include API router
app.include_router(api_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Starting Institutional Trading Dashboard API")
    logger.info(f"Upstox API Key configured: {bool(UPSTOX_API_KEY)}")

    # Create indexes
    await db.candles.create_index([("instrument_key", 1), ("timestamp", -1)])
    await db.patterns.create_index([("instrument_key", 1), ("timestamp", -1)])
    await db.instruments.create_index("trading_symbol")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Cleanup on shutdown."""
    client.close()
    logger.info("Database connection closed")
