from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


# ===============================
# Candle Data Model
# ===============================
class CandleData(BaseModel):

    instrument_key: str
    interval: str

    timestamp: datetime

    open: float
    high: float
    low: float
    close: float

    volume: float


# ===============================
# Instrument Model
# ===============================
class Instrument(BaseModel):

    instrument_key: str
    trading_symbol: str
    name: str

    exchange: str
    segment: str
    instrument_type: str


# ===============================
# Pattern Detection Model
# ===============================
class PatternDetection(BaseModel):

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    instrument_key: str
    pattern_type: str

    timestamp: datetime

    price_level: Optional[float] = None
    direction: Optional[str] = None

    confidence: Optional[str] = "medium"
    description: Optional[str] = None


# ===============================
# Market Structure Model
# ===============================
class MarketStructure(BaseModel):

    instrument_key: str
    trend: str

    higher_highs: List[dict] = Field(default_factory=list)
    higher_lows: List[dict] = Field(default_factory=list)

    lower_highs: List[dict] = Field(default_factory=list)
    lower_lows: List[dict] = Field(default_factory=list)

    last_updated: datetime


# ===============================
# Liquidity Pool Model
# ===============================
class LiquidityPool(BaseModel):

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    instrument_key: str
    pool_type: str

    price_level: float
    timestamp: datetime

    swept: bool = False
    sweep_timestamp: Optional[datetime] = None


# ===============================
# User Session Model
# ===============================
class UserSession(BaseModel):

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    access_token: str

    token_obtained_at: datetime
    token_expires_at: datetime

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ===============================
# Paper Trading Account
# ===============================
class PaperTradingAccount(BaseModel):

    user_id: str

    balance: float = 100000.0

    positions: List[dict] = Field(default_factory=list)
    orders: List[dict] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
