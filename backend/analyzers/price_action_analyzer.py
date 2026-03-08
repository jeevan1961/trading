from typing import List, Dict
from datetime import datetime


class PriceActionAnalyzer:
    """
    Institutional price action analyzer.
    """

    def __init__(self):
        self.swing_period = 5

    def analyze_candles(self, candles: List[Dict]) -> Dict:

        if len(candles) < 20:
            return {}

        return {
            "market_structure": self.detect_market_structure(candles),
            "bos": self.detect_break_of_structure(candles),
            "mss": self.detect_market_structure_shift(candles),
            "liquidity_pools": self.detect_liquidity_pools(candles),
            "liquidity_sweeps": self.detect_liquidity_sweeps(candles),
            "order_blocks": self.detect_order_blocks(candles),
            "fvg": self.detect_fair_value_gaps(candles),
            "timestamp": datetime.utcnow().isoformat()
        }

    # -----------------------------------------------------

    def detect_market_structure(self, candles):

        swing_highs = []
        swing_lows = []

        for i in range(self.swing_period, len(candles) - self.swing_period):

            high = candles[i].get("high")
            low = candles[i].get("low")

            if high is None or low is None:
                continue

            is_high = True
            is_low = True

            for j in range(i - self.swing_period, i + self.swing_period + 1):

                if j == i:
                    continue

                if candles[j].get("high", 0) >= high:
                    is_high = False

                if candles[j].get("low", 0) <= low:
                    is_low = False

            if is_high:
                swing_highs.append(high)

            if is_low:
                swing_lows.append(low)

        trend = "range"

        if len(swing_highs) >= 2 and swing_highs[-1] > swing_highs[-2]:
            trend = "uptrend"

        if len(swing_lows) >= 2 and swing_lows[-1] < swing_lows[-2]:
            trend = "downtrend"

        return {
            "trend": trend,
            "swing_highs": swing_highs[-5:],
            "swing_lows": swing_lows[-5:]
        }

    # -----------------------------------------------------

    def detect_break_of_structure(self, candles):

        signals = []

        for i in range(2, len(candles)):

            prev_high = candles[i - 1].get("high")
            prev_low = candles[i - 1].get("low")
            close = candles[i].get("close")

            if prev_high is None or prev_low is None or close is None:
                continue

            if close > prev_high:

                signals.append({
                    "type": "bullish_bos",
                    "timestamp": candles[i].get("timestamp")
                })

            elif close < prev_low:

                signals.append({
                    "type": "bearish_bos",
                    "timestamp": candles[i].get("timestamp")
                })

        return signals

    # -----------------------------------------------------

    def detect_market_structure_shift(self, candles):

        signals = []

        for i in range(2, len(candles)):

            close = candles[i].get("close")
            prev_high = candles[i - 1].get("high")
            prev_low = candles[i - 1].get("low")

            if close is None:
                continue

            if prev_high and close > prev_high:

                signals.append({
                    "type": "bullish_mss",
                    "timestamp": candles[i].get("timestamp")
                })

            if prev_low and close < prev_low:

                signals.append({
                    "type": "bearish_mss",
                    "timestamp": candles[i].get("timestamp")
                })

        return signals

    # -----------------------------------------------------

    def detect_liquidity_pools(self, candles):

        highs = {}
        lows = {}

        for candle in candles:

            high = round(candle.get("high", 0), 2)
            low = round(candle.get("low", 0), 2)

            highs[high] = highs.get(high, 0) + 1
            lows[low] = lows.get(low, 0) + 1

        equal_highs = [price for price, count in highs.items() if count >= 2]
        equal_lows = [price for price, count in lows.items() if count >= 2]

        return {
            "equal_highs": equal_highs,
            "equal_lows": equal_lows
        }

    # -----------------------------------------------------

    def detect_liquidity_sweeps(self, candles):

        sweeps = []

        for i in range(1, len(candles)):

            prev_high = candles[i - 1].get("high")
            prev_low = candles[i - 1].get("low")

            high = candles[i].get("high")
            low = candles[i].get("low")
            close = candles[i].get("close")

            if prev_high and high and close:

                if high > prev_high and close < prev_high:

                    sweeps.append({
                        "type": "buy_side_sweep",
                        "timestamp": candles[i].get("timestamp")
                    })

            if prev_low and low and close:

                if low < prev_low and close > prev_low:

                    sweeps.append({
                        "type": "sell_side_sweep",
                        "timestamp": candles[i].get("timestamp")
                    })

        return sweeps

    # -----------------------------------------------------

    def detect_order_blocks(self, candles):

        blocks = []

        for i in range(3, len(candles)):

            if (
                candles[i].get("close", 0) > candles[i].get("open", 0)
                and candles[i - 1].get("close", 0) > candles[i - 1].get("open", 0)
                and candles[i - 2].get("close", 0) > candles[i - 2].get("open", 0)
                and candles[i - 3].get("close", 0) < candles[i - 3].get("open", 0)
            ):

                blocks.append({
                    "type": "bullish_ob",
                    "timestamp": candles[i - 3].get("timestamp")
                })

        return blocks

    # -----------------------------------------------------

    def detect_fair_value_gaps(self, candles):

        fvgs = []

        for i in range(2, len(candles)):

            if candles[i].get("low", 0) > candles[i - 2].get("high", 0):

                fvgs.append({
                    "type": "bullish_fvg",
                    "timestamp": candles[i].get("timestamp")
                })

            if candles[i].get("high", 0) < candles[i - 2].get("low", 0):

                fvgs.append({
                    "type": "bearish_fvg",
                    "timestamp": candles[i].get("timestamp")
                })

        return fvgs
