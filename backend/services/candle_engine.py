import logging
from datetime import datetime
from database import get_db

logger = logging.getLogger(__name__)

# Active in-memory candles
current_candles = {}


def normalize_minute(ts: datetime):
    """
    Normalize timestamp to minute precision.
    """
    return ts.replace(second=0, microsecond=0)


async def process_tick_to_candle(tick: dict):
    """
    Convert tick data into OHLC candles.
    """

    try:

        instrument = tick.get("instrument_key")
        price = tick.get("ltp")

        volume = tick.get("volume") or 0

        if not instrument or price is None:
            return

        # Prefer tick timestamp if available
        ts = tick.get("timestamp")

        if ts:
            try:
                timestamp = datetime.fromisoformat(ts)
            except Exception:
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()

        minute = normalize_minute(timestamp)

        key = f"{instrument}-{minute}"

        if key not in current_candles:

            current_candles[key] = {
                "instrument_key": instrument,
                "interval": "1minute",
                "timestamp": minute,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume
            }

        else:

            candle = current_candles[key]

            candle["high"] = max(candle["high"], price)
            candle["low"] = min(candle["low"], price)
            candle["close"] = price
            candle["volume"] += volume

        await close_old_candles(minute)

    except Exception as e:

        logger.error(f"Candle processing error: {e}")


async def close_old_candles(current_minute):
    """
    Close completed candles and store them in MongoDB.
    """

    try:

        db = get_db()

        if not db:
            return

        keys_to_remove = []

        for key, candle in current_candles.items():

            candle_minute = candle["timestamp"]

            if candle_minute < current_minute:

                await db.candles.insert_one(candle)

                keys_to_remove.append(key)

        for key in keys_to_remove:
            del current_candles[key]

    except Exception as e:

        logger.error(f"Candle closing error: {e}")


def get_latest_candle(instrument_key):
    """
    Return latest active candle for instrument.
    """

    for candle in current_candles.values():

        if candle["instrument_key"] == instrument_key:

            return candle

    return None
