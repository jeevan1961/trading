import os
from dotenv import load_dotenv
from pathlib import Path

# Ensure .env loads from the backend folder
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Settings:

    # =============================
    # Upstox API Configuration
    # =============================
    UPSTOX_API_KEY = os.getenv("UPSTOX_API_KEY")
    UPSTOX_API_SECRET = os.getenv("UPSTOX_API_SECRET")
    UPSTOX_REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")

    # =============================
    # Database Configuration
    # =============================
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "trading_dashboard")

    # =============================
    # Security
    # =============================
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    # =============================
    # Frontend URL
    # =============================
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # =============================
    # Market Data Feed
    # =============================
    UPSTOX_WS = "wss://api.upstox.com/v2/feed/market-data-feed"


# Global settings object
settings = Settings()
