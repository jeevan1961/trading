import csv
import httpx
import logging

logger = logging.getLogger(__name__)

INSTRUMENT_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv"


async def load_nse_instruments():
    """
    Download NSE instrument list from Upstox and
    return equity instruments.
    """

    instruments = []

    try:

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(INSTRUMENT_URL)

        if response.status_code != 200:
            logger.error("Failed to download instruments list")
            return []

        lines = response.text.splitlines()

        reader = csv.DictReader(lines)

        for row in reader:

            instrument_type = row.get("instrument_type")

            # filter equity stocks
            if instrument_type == "EQ":

                instruments.append({
                    "instrument_key": row.get("instrument_key"),
                    "symbol": row.get("tradingsymbol"),
                    "name": row.get("name")
                })

        logger.info(f"Loaded {len(instruments)} NSE instruments")

        return instruments

    except Exception as e:

        logger.error(f"Instrument loader error: {e}")

        return []
