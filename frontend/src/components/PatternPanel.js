import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

export function PatternPanel({ analysis }) {
  if (!analysis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pattern Detection</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">No analysis available</p>
        </CardContent>
      </Card>
    );
  }

  const { market_structure, bos, mss, liquidity_sweeps, liquidity_traps, fvg, order_blocks } = analysis;

  return (
    <div className="space-y-4">
      {/* Market Structure */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Market Structure</span>
            <Badge variant={market_structure?.trend === 'uptrend' ? 'default' : market_structure?.trend === 'downtrend' ? 'destructive' : 'secondary'}>
              {market_structure?.trend || 'Unknown'}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Higher Highs: {market_structure?.hh_count || 0}</p>
              <p className="text-gray-500">Higher Lows: {market_structure?.hl_count || 0}</p>
            </div>
            <div>
              <p className="text-gray-500">Lower Highs: {market_structure?.lh_count || 0}</p>
              <p className="text-gray-500">Lower Lows: {market_structure?.ll_count || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Break of Structure */}
      {bos && bos.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Break of Structure (BOS)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {bos.slice(0, 3).map((signal, idx) => (
                <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  <Badge variant={signal.type.includes('bullish') ? 'default' : 'destructive'}>
                    {signal.type}
                  </Badge>
                  <span className="text-sm">₹{signal.price?.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Market Structure Shift */}
      {mss && mss.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Market Structure Shift (MSS)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {mss.slice(0, 3).map((signal, idx) => (
                <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  <Badge variant={signal.type.includes('bullish') ? 'default' : 'destructive'}>
                    {signal.type}
                  </Badge>
                  <span className="text-sm">₹{signal.price?.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Liquidity Sweeps */}
      {liquidity_sweeps && liquidity_sweeps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Liquidity Sweeps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {liquidity_sweeps.slice(0, 3).map((sweep, idx) => (
                <div key={idx} className="p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                  <div className="flex justify-between items-center">
                    <Badge variant="outline">{sweep.type}</Badge>
                    <span className="text-sm font-medium">₹{sweep.pool_price?.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Liquidity Traps */}
      {liquidity_traps && liquidity_traps.length > 0 && (
        <Card className="border-yellow-500">
          <CardHeader>
            <CardTitle className="text-yellow-600 dark:text-yellow-400">⚠️ Liquidity Traps Detected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {liquidity_traps.map((trap, idx) => (
                <div key={idx} className="p-3 bg-yellow-100 dark:bg-yellow-900/30 rounded">
                  <div className="flex justify-between items-center mb-2">
                    <Badge variant="destructive">HIGH PROBABILITY SETUP</Badge>
                    <span className="text-xs">{trap.confidence}</span>
                  </div>
                  <p className="text-sm">{trap.sweep_type}</p>
                  <div className="text-xs mt-2 text-gray-600 dark:text-gray-400">
                    <span>Rejection: {trap.has_rejection ? '✓' : '✗'}</span>
                    <span className="ml-3">MSS: {trap.has_mss ? '✓' : '✗'}</span>
                    <span className="ml-3">FVG: {trap.has_fvg ? '✓' : '✗'}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Fair Value Gaps */}
      {fvg && fvg.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Fair Value Gaps (FVG)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {fvg.slice(0, 3).map((gap, idx) => (
                <div key={idx} className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                  <Badge variant={gap.type.includes('bullish') ? 'default' : 'destructive'}>
                    {gap.type}
                  </Badge>
                  <div className="text-sm mt-1">
                    ₹{gap.gap_low?.toFixed(2)} - ₹{gap.gap_high?.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Order Blocks */}
      {order_blocks && order_blocks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Order Blocks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {order_blocks.map((ob, idx) => (
                <div key={idx} className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded">
                  <Badge variant={ob.type.includes('bullish') ? 'default' : 'destructive'}>
                    {ob.type}
                  </Badge>
                  <div className="text-sm mt-1">
                    ₹{ob.low?.toFixed(2)} - ₹{ob.high?.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}