from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client
mongo_client = None
database = None


async def connect_to_mongo():
    """
    Initialize MongoDB connection.
    """

    global mongo_client, database

    try:

        mongo_client = AsyncIOMotorClient(settings.MONGO_URL)

        database = mongo_client[settings.DB_NAME]

        logger.info("MongoDB connected successfully")

        await create_indexes()

    except Exception as e:

        logger.error(f"MongoDB connection failed: {e}")

        raise e


async def close_mongo_connection():
    """
    Close MongoDB connection on shutdown.
    """

    global mongo_client

    if mongo_client:

        mongo_client.close()

        logger.info("MongoDB connection closed")


def get_db():
    """
    Return database instance.
    """

    return database


async def create_indexes():
    """
    Create indexes for faster queries.
    """

    db = database

    if db is None:
        return

    try:

        # Candle data index
        await db.candles.create_index([
            ("instrument_key", 1),
            ("timestamp", -1)
        ])

        # Pattern detection index
        await db.patterns.create_index([
            ("instrument_key", 1),
            ("timestamp", -1)
        ])

        # Liquidity zones
        await db.liquidity_zones.create_index([
            ("instrument_key", 1),
            ("price_level", 1)
        ])

        # User sessions
        await db.user_sessions.create_index([
            ("token_expires_at", 1)
        ])

        # Paper trading accounts
        await db.paper_accounts.create_index([
            ("user_id", 1)
        ])

        logger.info("MongoDB indexes created")

    except Exception as e:

        logger.error(f"Index creation failed: {e}")
