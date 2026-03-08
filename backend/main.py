import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import connect_to_mongo, close_mongo_connection
from services.liquidity_radar import run_liquidity_radar

from api.auth import router as auth_router
from api.ws import router as ws_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Radar state
radar_results = []

# Background task reference
radar_task = None


async def radar_loop():
    """
    Continuously scan market for opportunities.
    """

    global radar_results

    while True:

        try:

            results = await run_liquidity_radar()

            radar_results = results

        except Exception as e:

            logger.error(f"Radar loop error: {e}")

        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):

    global radar_task

    logger.info("Starting backend services")

    # Connect MongoDB
    await connect_to_mongo()

    # Start radar loop
    radar_task = asyncio.create_task(radar_loop())

    yield

    logger.info("Shutting down backend")

    # Stop radar loop
    if radar_task:
        radar_task.cancel()

    # Close MongoDB
    await close_mongo_connection()


app = FastAPI(
    title="Institutional Trading Dashboard API",
    lifespan=lifespan
)


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routes
app.include_router(auth_router, prefix="/auth")

# Register WebSocket routes
app.include_router(ws_router)


@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {"status": "Trading backend running"}


@app.get("/api/radar")
async def get_radar():
    """
    Return latest radar results.
    """
    return radar_results
