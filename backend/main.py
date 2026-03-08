import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import connect_to_mongo, close_mongo_connection
from services.liquidity_radar import run_liquidity_radar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

radar_results = []
radar_task = None


async def radar_loop():
    """
    Continuously run liquidity radar.
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

    await connect_to_mongo()

    radar_task = asyncio.create_task(radar_loop())

    yield

    logger.info("Shutting down backend")

    if radar_task:
        radar_task.cancel()

    await close_mongo_connection()


app = FastAPI(
    title="Institutional Trading Dashboard API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "Trading backend running"}


@app.get("/api/radar")
async def get_radar():
    """
    Return latest radar results.
    """
    return radar_results
