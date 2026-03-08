import logging

from database import get_db
from services.order_flow import get_order_flow
from analyzers.price_action_analyzer import PriceActionAnalyzer

logger = logging.getLogger(__name__)

analyzer = PriceActionAnalyzer()


async def calculate_score(instrument_key, candles, analysis, order_flow):
    """
    Score trading opportunities using price action + order flow.
    """

    score = 0
    signals = []

    try:

        # Liquidity sweeps
        sweeps = analysis.get("liquidity_sweeps", [])

        if sweeps:
            score += 40
            signals.append("liquidity_sweep")

        # Market structure shift
        mss = analysis.get("mss", [])

        if mss:
            score += 30
            signals.append("market_structure_shift")

        # Order blocks
        order_blocks = analysis.get("order_blocks", [])

        if order_blocks:
            score += 25
            signals.append("order_block")

        # Fair value gaps
        fvgs = analysis.get("fvg", [])

        if fvgs:
            score += 20
            signals.append("fvg")

        # Order flow delta
        if order_flow:

            delta = order_flow.get("delta", 0)

            if delta > 3000:
                score += 35
                signals.append("buy_delta_spike")

            elif delta < -3000:
                score += 35
                signals.append("sell_delta_spike")

        return {
            "instrument": instrument_key,
            "score": score,
            "signals": signals
        }

    except Exception as e:

        logger.error(f"Radar scoring error: {e}")

        return None


async def run_liquidity_radar():
    """
    Scan all instruments and rank best trading setups.
    """

    try:

        db = get_db()

        if not db:
            return []

        instruments = await db.candles.distinct("instrument_key")

        results = []

        for instrument in instruments:

            candles = await db.candles.find(
                {"instrument_key": instrument}
            ).sort("timestamp", -1).limit(200).to_list(200)

            if not candles or len(candles) < 20:
                continue

            # analyzer expects chronological order
            candles.reverse()

            analysis = analyzer.analyze_candles(candles)

            order_flow = get_order_flow(instrument)

            score_data = await calculate_score(
                instrument,
                candles,
                analysis,
                order_flow
            )

            if score_data and score_data["score"] >= 50:
                results.append(score_data)

        results.sort(key=lambda x: x["score"], reverse=True)

        # return top opportunities
        return results[:10]

    except Exception as e:

        logger.error(f"Liquidity radar error: {e}")

        return []
