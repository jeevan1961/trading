import asyncio
import json
import logging
import websockets

from config import settings
from database import get_db

logger = logging.getLogger(__name__)

# Active subscriptions
subscriptions = set()

# Latest tick cache
latest_ticks = {}


async def connect_upstox_feed(access_token: str):
    """
    Maintain persistent connection to Upstox market feed.
    Auto reconnect if connection drops.
    """

    ws_url = settings.UPSTOX_WS

    while True:

        try:
            logger.info("Connecting to Upstox WebSocket...")

            async with websockets.connect(
                ws_url,
                extra_headers={
                    "Authorization": f"Bearer {access_token}"
                }
            ) as ws:

                logger.info("Connected to Upstox feed")

                await subscribe_initial_instruments(ws)

                while True:

                    message = await ws.recv()

                    try:
                        data = json.loads(message)
                        await process_tick(data)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:

            logger.error(f"WebSocket disconnected: {e}")
            logger.info("Reconnecting in 3 seconds...")

            await asyncio.sleep(3)


async def subscribe_initial_instruments(ws):
    """
    Subscribe to initial instruments.
    """

    instruments = [
        "NSE_EQ|RELIANCE",
        "NSE_EQ|TCS",
        "NSE_EQ|INFY",
        "NSE_EQ|HDFCBANK",
        "NSE_EQ|ICICIBANK"
    ]

    for instrument in instruments:
        subscriptions.add(instrument)

    payload = {
        "guid": "market-feed",
        "method": "sub",
        "data": {
            "mode": "full",
            "instrumentKeys": list(subscriptions)
        }
    }

    await ws.send(json.dumps(payload))

    logger.info(f"Subscribed to {len(instruments)} instruments")


async def process_tick(message):
    """
    Process incoming market data.
    """

    try:

        # Upstox sends nested data
        data = message.get("data")

        if not data:
            return

        for tick in data:

            instrument = tick.get("instrument_key")

            if not instrument:
                continue

            latest_ticks[instrument] = tick

            db = get_db()

            if db:
                await db.ticks.insert_one({
                    "instrument_key": instrument,
                    "tick": tick
                })

    except Exception as e:

        logger.error(f"Tick processing error: {e}")


def get_latest_tick(instrument_key: str):
    """
    Return latest cached tick.
    """

    return latest_ticks.get(instrument_key)
