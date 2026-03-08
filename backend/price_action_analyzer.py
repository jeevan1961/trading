from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np

class PriceActionAnalyzer:
    """
    Institutional Price Action Analysis Engine.
    Detects market structure, liquidity zones, sweeps, and institutional patterns.
    """
    
    def __init__(self):
        self.swing_period = 5  # Lookback for swing highs/lows
        
    def analyze_candles(self, candles: List[Dict]) -> Dict:
        """
        Main analysis function that detects all patterns.
        Returns comprehensive analysis including trend, patterns, liquidity zones.
        """
        if len(candles) < 20:
            return {"error": "Insufficient data for analysis"}
            
        analysis = {
            "market_structure": self.detect_market_structure(candles),
            "bos": self.detect_break_of_structure(candles),
            "mss": self.detect_market_structure_shift(candles),
            "liquidity_pools": self.detect_liquidity_pools(candles),
            "liquidity_sweeps": self.detect_liquidity_sweeps(candles),
            "wick_rejections": self.detect_wick_rejections(candles),
            "false_breakouts": self.detect_false_breakouts(candles),
            "momentum_candles": self.detect_momentum_candles(candles),
            "order_blocks": self.detect_order_blocks(candles),
            "fvg": self.detect_fair_value_gaps(candles),
            "liquidity_traps": self.detect_liquidity_traps(candles),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return analysis
    
    def detect_market_structure(self, candles: List[Dict]) -> Dict:
        """
        Detect market structure: HH, HL, LH, LL patterns.
        Returns trend classification and swing points.
        """
        swing_highs = self._find_swing_highs(candles)
        swing_lows = self._find_swing_lows(candles)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {"trend": "insufficient_data", "swing_highs": [], "swing_lows": []}
        
        # Analyze trend based on swing points
        hh_count = sum(1 for i in range(1, len(swing_highs)) if swing_highs[i]['price'] > swing_highs[i-1]['price'])
        hl_count = sum(1 for i in range(1, len(swing_lows)) if swing_lows[i]['price'] > swing_lows[i-1]['price'])
        lh_count = sum(1 for i in range(1, len(swing_highs)) if swing_highs[i]['price'] < swing_highs[i-1]['price'])
        ll_count = sum(1 for i in range(1, len(swing_lows)) if swing_lows[i]['price'] < swing_lows[i-1]['price'])
        
        if hh_count > 0 and hl_count > 0:
            trend = "uptrend"
        elif ll_count > 0 and lh_count > 0:
            trend = "downtrend"
        else:
            trend = "range"
            
        return {
            "trend": trend,
            "swing_highs": swing_highs[-5:],  # Last 5 swing highs
            "swing_lows": swing_lows[-5:],    # Last 5 swing lows
            "hh_count": hh_count,
            "hl_count": hl_count,
            "lh_count": lh_count,
            "ll_count": ll_count
        }
    
    def _find_swing_highs(self, candles: List[Dict]) -> List[Dict]:
        """Find swing high points."""
        swing_highs = []
        for i in range(self.swing_period, len(candles) - self.swing_period):
            current_high = candles[i]['high']
            is_swing_high = True
            
            # Check if higher than surrounding candles
            for j in range(i - self.swing_period, i + self.swing_period + 1):
                if j != i and candles[j]['high'] >= current_high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    'index': i,
                    'price': current_high,
                    'timestamp': candles[i]['timestamp']
                })
        
        return swing_highs
    
    def _find_swing_lows(self, candles: List[Dict]) -> List[Dict]:
        """Find swing low points."""
        swing_lows = []
        for i in range(self.swing_period, len(candles) - self.swing_period):
            current_low = candles[i]['low']
            is_swing_low = True
            
            # Check if lower than surrounding candles
            for j in range(i - self.swing_period, i + self.swing_period + 1):
                if j != i and candles[j]['low'] <= current_low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    'index': i,
                    'price': current_low,
                    'timestamp': candles[i]['timestamp']
                })
        
        return swing_lows
    
    def detect_break_of_structure(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect Break of Structure (BOS).
        Bullish BOS: price breaks most recent swing high in uptrend.
        Bearish BOS: price breaks most recent swing low in downtrend.
        """
        bos_signals = []
        swing_highs = self._find_swing_highs(candles)
        swing_lows = self._find_swing_lows(candles)
        
        if not swing_highs or not swing_lows:
            return []
        
        # Check for bullish BOS
        for i in range(len(swing_highs) - 1, len(candles)):
            if i >= len(candles):
                break
            last_swing_high = swing_highs[-1]['price']
            if candles[i]['close'] > last_swing_high:
                bos_signals.append({
                    'type': 'bullish_bos',
                    'index': i,
                    'price': candles[i]['close'],
                    'broken_level': last_swing_high,
                    'timestamp': candles[i]['timestamp']
                })
                break
        
        # Check for bearish BOS
        for i in range(len(swing_lows) - 1, len(candles)):
            if i >= len(candles):
                break
            last_swing_low = swing_lows[-1]['price']
            if candles[i]['close'] < last_swing_low:
                bos_signals.append({
                    'type': 'bearish_bos',
                    'index': i,
                    'price': candles[i]['close'],
                    'broken_level': last_swing_low,
                    'timestamp': candles[i]['timestamp']
                })
                break
        
        return bos_signals
    
    def detect_market_structure_shift(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect Market Structure Shift (MSS) - reversal signal.
        Bullish MSS: price breaks most recent Lower High (LH).
        Bearish MSS: price breaks most recent Higher Low (HL).
        """
        mss_signals = []
        swing_highs = self._find_swing_highs(candles)
        swing_lows = self._find_swing_lows(candles)
        
        # Detect Lower Highs and check for breaks
        for i in range(1, len(swing_highs)):
            if swing_highs[i]['price'] < swing_highs[i-1]['price']:
                # This is a Lower High
                lh_price = swing_highs[i]['price']
                # Check if broken in subsequent candles
                for j in range(swing_highs[i]['index'], min(len(candles), swing_highs[i]['index'] + 20)):
                    if candles[j]['close'] > lh_price:
                        mss_signals.append({
                            'type': 'bullish_mss',
                            'index': j,
                            'price': candles[j]['close'],
                            'broken_level': lh_price,
                            'timestamp': candles[j]['timestamp']
                        })
                        break
        
        # Detect Higher Lows and check for breaks
        for i in range(1, len(swing_lows)):
            if swing_lows[i]['price'] > swing_lows[i-1]['price']:
                # This is a Higher Low
                hl_price = swing_lows[i]['price']
                # Check if broken in subsequent candles
                for j in range(swing_lows[i]['index'], min(len(candles), swing_lows[i]['index'] + 20)):
                    if candles[j]['close'] < hl_price:
                        mss_signals.append({
                            'type': 'bearish_mss',
                            'index': j,
                            'price': candles[j]['close'],
                            'broken_level': hl_price,
                            'timestamp': candles[j]['timestamp']
                        })
                        break
        
        return mss_signals
    
    def detect_liquidity_pools(self, candles: List[Dict]) -> Dict:
        """
        Detect liquidity pools: equal highs/lows, PDH, PDL, opening range.
        """
        pools = {
            'equal_highs': [],
            'equal_lows': [],
            'pdh': None,
            'pdl': None,
            'opening_range_high': None,
            'opening_range_low': None
        }
        
        # Find equal highs (within 0.05-0.15% price distance)
        swing_highs = self._find_swing_highs(candles)
        for i in range(len(swing_highs) - 1):
            for j in range(i + 1, len(swing_highs)):
                price_diff_pct = abs(swing_highs[i]['price'] - swing_highs[j]['price']) / swing_highs[i]['price'] * 100
                if 0.05 <= price_diff_pct <= 0.15:
                    pools['equal_highs'].append({
                        'price': (swing_highs[i]['price'] + swing_highs[j]['price']) / 2,
                        'indices': [swing_highs[i]['index'], swing_highs[j]['index']]
                    })
        
        # Find equal lows
        swing_lows = self._find_swing_lows(candles)
        for i in range(len(swing_lows) - 1):
            for j in range(i + 1, len(swing_lows)):
                price_diff_pct = abs(swing_lows[i]['price'] - swing_lows[j]['price']) / swing_lows[i]['price'] * 100
                if 0.05 <= price_diff_pct <= 0.15:
                    pools['equal_lows'].append({
                        'price': (swing_lows[i]['price'] + swing_lows[j]['price']) / 2,
                        'indices': [swing_lows[i]['index'], swing_lows[j]['index']]
                    })
        
        # Previous Day High/Low (last 75 candles for 1-min = ~1 day)
        if len(candles) > 75:
            pdh = max([c['high'] for c in candles[-75:-1]])
            pdl = min([c['low'] for c in candles[-75:-1]])
            pools['pdh'] = pdh
            pools['pdl'] = pdl
        
        # Opening range (first 5 candles)
        if len(candles) >= 5:
            pools['opening_range_high'] = max([c['high'] for c in candles[:5]])
            pools['opening_range_low'] = min([c['low'] for c in candles[:5]])
        
        return pools
    
    def detect_liquidity_sweeps(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect liquidity sweeps: price briefly breaks zone and reverses.
        """
        sweeps = []
        liquidity_pools = self.detect_liquidity_pools(candles)
        
        # Check for buy-side sweeps (equal highs)
        for pool in liquidity_pools['equal_highs']:
            pool_price = pool['price']
            # Check candles after the pool formation
            start_idx = max(pool['indices']) + 1
            for i in range(start_idx, min(len(candles), start_idx + 20)):
                candle = candles[i]
                # Check if high breaks pool but close is below
                if candle['high'] > pool_price and candle['close'] < pool_price:
                    # Check wick size
                    upper_wick = candle['high'] - max(candle['open'], candle['close'])
                    body = abs(candle['close'] - candle['open'])
                    if body > 0 and upper_wick > 2 * body:
                        sweeps.append({
                            'type': 'buy_side_sweep',
                            'index': i,
                            'pool_price': pool_price,
                            'sweep_high': candle['high'],
                            'close': candle['close'],
                            'timestamp': candle['timestamp']
                        })
        
        # Check for sell-side sweeps (equal lows)
        for pool in liquidity_pools['equal_lows']:
            pool_price = pool['price']
            start_idx = max(pool['indices']) + 1
            for i in range(start_idx, min(len(candles), start_idx + 20)):
                candle = candles[i]
                if candle['low'] < pool_price and candle['close'] > pool_price:
                    lower_wick = min(candle['open'], candle['close']) - candle['low']
                    body = abs(candle['close'] - candle['open'])
                    if body > 0 and lower_wick > 2 * body:
                        sweeps.append({
                            'type': 'sell_side_sweep',
                            'index': i,
                            'pool_price': pool_price,
                            'sweep_low': candle['low'],
                            'close': candle['close'],
                            'timestamp': candle['timestamp']
                        })
        
        return sweeps
    
    def detect_wick_rejections(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect rejection candles with long wicks.
        """
        rejections = []
        
        for i, candle in enumerate(candles):
            body = abs(candle['close'] - candle['open'])
            if body == 0:
                continue
            
            upper_wick = candle['high'] - max(candle['open'], candle['close'])
            lower_wick = min(candle['open'], candle['close']) - candle['low']
            
            # Bullish rejection (long lower wick)
            if lower_wick >= 2 * body:
                rejections.append({
                    'type': 'bullish_rejection',
                    'index': i,
                    'price': candle['close'],
                    'wick_size': lower_wick,
                    'body_size': body,
                    'timestamp': candle['timestamp']
                })
            
            # Bearish rejection (long upper wick)
            if upper_wick >= 2 * body:
                rejections.append({
                    'type': 'bearish_rejection',
                    'index': i,
                    'price': candle['close'],
                    'wick_size': upper_wick,
                    'body_size': body,
                    'timestamp': candle['timestamp']
                })
        
        return rejections[-10:]  # Return last 10
    
    def detect_false_breakouts(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect false breakouts: price breaks level but reverses.
        """
        false_breakouts = []
        swing_highs = self._find_swing_highs(candles)
        swing_lows = self._find_swing_lows(candles)
        
        # Check for false breakout of swing highs
        for swing in swing_highs:
            idx = swing['index']
            price = swing['price']
            # Check next 3 candles
            for i in range(idx + 1, min(len(candles), idx + 4)):
                if candles[i]['high'] > price:
                    # Breakout occurred
                    # Check if next candle closes back inside
                    if i + 1 < len(candles) and candles[i + 1]['close'] < price:
                        false_breakouts.append({
                            'type': 'false_breakout_high',
                            'level': price,
                            'breakout_index': i,
                            'reversal_index': i + 1,
                            'timestamp': candles[i + 1]['timestamp']
                        })
                    break
        
        # Check for false breakout of swing lows
        for swing in swing_lows:
            idx = swing['index']
            price = swing['price']
            for i in range(idx + 1, min(len(candles), idx + 4)):
                if candles[i]['low'] < price:
                    if i + 1 < len(candles) and candles[i + 1]['close'] > price:
                        false_breakouts.append({
                            'type': 'false_breakout_low',
                            'level': price,
                            'breakout_index': i,
                            'reversal_index': i + 1,
                            'timestamp': candles[i + 1]['timestamp']
                        })
                    break
        
        return false_breakouts
    
    def detect_momentum_candles(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect strong momentum candles (body >= 70% of range).
        """
        momentum_candles = []
        
        for i, candle in enumerate(candles):
            total_range = candle['high'] - candle['low']
            if total_range == 0:
                continue
            
            body = abs(candle['close'] - candle['open'])
            body_pct = (body / total_range) * 100
            
            if body_pct >= 70:
                direction = 'bullish' if candle['close'] > candle['open'] else 'bearish'
                momentum_candles.append({
                    'index': i,
                    'direction': direction,
                    'body_percentage': body_pct,
                    'price': candle['close'],
                    'timestamp': candle['timestamp']
                })
        
        return momentum_candles[-10:]  # Last 10
    
    def detect_order_blocks(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect order blocks: last opposite candle before strong move.
        """
        order_blocks = []
        
        for i in range(3, len(candles)):
            # Bullish Order Block
            if (candles[i]['close'] > candles[i]['open'] and  # Current bullish
                candles[i-1]['close'] > candles[i-1]['open'] and  # Previous bullish
                candles[i-2]['close'] > candles[i-2]['open'] and  # 2nd previous bullish
                candles[i-3]['close'] < candles[i-3]['open']):  # 3rd previous bearish
                
                order_blocks.append({
                    'type': 'bullish_ob',
                    'index': i - 3,
                    'high': candles[i-3]['high'],
                    'low': candles[i-3]['low'],
                    'timestamp': candles[i-3]['timestamp']
                })
            
            # Bearish Order Block
            if (candles[i]['close'] < candles[i]['open'] and
                candles[i-1]['close'] < candles[i-1]['open'] and
                candles[i-2]['close'] < candles[i-2]['open'] and
                candles[i-3]['close'] > candles[i-3]['open']):
                
                order_blocks.append({
                    'type': 'bearish_ob',
                    'index': i - 3,
                    'high': candles[i-3]['high'],
                    'low': candles[i-3]['low'],
                    'timestamp': candles[i-3]['timestamp']
                })
        
        return order_blocks[-5:]  # Last 5
    
    def detect_fair_value_gaps(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect Fair Value Gaps (FVG) - imbalance zones.
        """
        fvgs = []
        
        for i in range(2, len(candles)):
            # Bullish FVG: low of candle 3 > high of candle 1
            if candles[i]['low'] > candles[i-2]['high']:
                fvgs.append({
                    'type': 'bullish_fvg',
                    'index': i - 1,
                    'gap_low': candles[i-2]['high'],
                    'gap_high': candles[i]['low'],
                    'timestamp': candles[i-1]['timestamp']
                })
            
            # Bearish FVG: high of candle 3 < low of candle 1
            if candles[i]['high'] < candles[i-2]['low']:
                fvgs.append({
                    'type': 'bearish_fvg',
                    'index': i - 1,
                    'gap_high': candles[i-2]['low'],
                    'gap_low': candles[i]['high'],
                    'timestamp': candles[i-1]['timestamp']
                })
        
        return fvgs[-10:]  # Last 10
    
    def detect_liquidity_traps(self, candles: List[Dict]) -> List[Dict]:
        """
        Detect institutional liquidity trap setups.
        """
        traps = []
        
        # Get all required patterns
        pools = self.detect_liquidity_pools(candles)
        sweeps = self.detect_liquidity_sweeps(candles)
        rejections = self.detect_wick_rejections(candles)
        mss = self.detect_market_structure_shift(candles)
        fvgs = self.detect_fair_value_gaps(candles)
        
        # Look for liquidity trap pattern
        for sweep in sweeps:
            sweep_idx = sweep['index']
            
            # Check if there's a rejection nearby
            nearby_rejection = any(
                abs(r['index'] - sweep_idx) <= 2 
                for r in rejections
            )
            
            # Check if MSS follows
            mss_follows = any(
                m['index'] > sweep_idx and m['index'] <= sweep_idx + 10
                for m in mss
            )
            
            # Check if FVG exists
            fvg_nearby = any(
                abs(f['index'] - sweep_idx) <= 5
                for f in fvgs
            )
            
            if nearby_rejection and mss_follows:
                traps.append({
                    'type': 'liquidity_trap',
                    'sweep_index': sweep_idx,
                    'sweep_type': sweep['type'],
                    'has_rejection': nearby_rejection,
                    'has_mss': mss_follows,
                    'has_fvg': fvg_nearby,
                    'confidence': 'high',
                    'timestamp': sweep['timestamp']
                })
        
        return traps