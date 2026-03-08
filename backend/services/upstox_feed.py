import asyncio
import json
import logging
import websockets

from config import settings
from database import get_db

from services.candle_engine import process_tick_to_candle
from services.order_flow import process_tick_order_flow
from utils.instrument_loader import load_nse_instruments


logger = logging.getLogger(__name__)

subscriptions = set()
latest_ticks = {}


async def connect_upstox_feed(access_token: str):
    """
    Maintain persistent connection to Upstox market feed.
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
    Subscribe to top NSE instruments.
    """

    instruments = await load_nse_instruments()

    if not instruments:
        logger.error("No instruments loaded")
        return

    # limit subscription for performance
    instruments = instruments[:200]

    keys = [i["instrument_key"] for i in instruments]

    payload = {
        "guid": "market-feed",
        "method": "sub",
        "data": {
            "mode": "full",
            "instrumentKeys": keys
        }
    }

    await ws.send(json.dumps(payload))

    logger.info(f"Subscribed to {len(keys)} instruments")


async def process_tick(message):
    """
    Process incoming market tick.
    """

    try:

        data = message.get("data")

        if not data:
            return

        for tick in data:

            instrument = tick.get("instrument_key")

            if not instrument:
                continue

            latest_ticks[instrument] = tick

            # process for candles
            await process_tick_to_candle(tick)

            # process order flow
            process_tick_order_flow(tick)

            db = get_db()

            if db:

                await db.ticks.insert_one({
                    "instrument_key": instrument,
                    "tick": tick
                })

    except Exception as e:

        logger.error(f"Tick processing error: {e}")


def get_latest_tick(instrument_key):
    """
    Return latest cached tick.
    """

    return latest_ticks.get(instrument_key)
