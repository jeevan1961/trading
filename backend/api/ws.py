import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.candle_engine import get_latest_candle
from services.order_flow import get_order_flow
from services.liquidity_radar import run_liquidity_radar


logger = logging.getLogger(__name__)

router = APIRouter()

# Active websocket connections
connections = []


@router.websocket("/stream")
async def websocket_stream(ws: WebSocket):

    await ws.accept()

    connections.append(ws)

    logger.info("WebSocket client connected")

    try:

        while True:

            # Send heartbeat to keep connection alive
            await ws.send_json({"type": "heartbeat"})

            await asyncio.sleep(5)

    except WebSocketDisconnect:

        if ws in connections:
            connections.remove(ws)

        logger.info("WebSocket client disconnected")


async def broadcast_market_data(instrument):

    candle = get_latest_candle(instrument)

    order_flow = get_order_flow(instrument)

    message = {
        "type": "market_data",
        "instrument": instrument,
        "candle": candle,
        "order_flow": order_flow
    }

    dead_connections = []

    for ws in connections:

        try:
            await ws.send_json(message)

        except Exception:
            dead_connections.append(ws)

    for ws in dead_connections:
        connections.remove(ws)


async def broadcast_radar():

    results = await run_liquidity_radar()

    message = {
        "type": "radar",
        "data": results
    }

    dead_connections = []

    for ws in connections:

        try:
            await ws.send_json(message)

        except Exception:
            dead_connections.append(ws)

    for ws in dead_connections:
        connections.remove(ws)
