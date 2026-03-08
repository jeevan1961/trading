import logging

logger = logging.getLogger(__name__)

# In-memory order flow state
order_flow_stats = {}


def process_tick_order_flow(tick: dict):
    """
    Update order flow stats using incoming tick.
    """

    try:

        instrument = tick.get("instrument_key")
        price = tick.get("ltp")

        volume = tick.get("volume") or 0

        if not instrument or price is None:
            return

        bid = tick.get("bid")
        ask = tick.get("ask")

        if instrument not in order_flow_stats:

            order_flow_stats[instrument] = {
                "buy_volume": 0,
                "sell_volume": 0
            }

        stats = order_flow_stats[instrument]

        # Detect aggressor side

        if ask is not None and price >= ask:

            stats["buy_volume"] += volume

        elif bid is not None and price <= bid:

            stats["sell_volume"] += volume

        else:
            # If no bid/ask data, ignore tick
            return

    except Exception as e:

        logger.error(f"Order flow processing error: {e}")


def get_order_flow(instrument_key: str):
    """
    Return order flow metrics.
    """

    stats = order_flow_stats.get(instrument_key)

    if not stats:
        return None

    buy_volume = stats["buy_volume"]
    sell_volume = stats["sell_volume"]

    delta = buy_volume - sell_volume

    return {
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "delta": delta
    }


def reset_order_flow(instrument_key: str):
    """
    Reset stats for instrument.
    """

    if instrument_key in order_flow_stats:

        order_flow_stats[instrument_key] = {
            "buy_volume": 0,
            "sell_volume": 0
        }
