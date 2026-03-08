import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

export function TradingChart({ data, patterns = {}, width = 800, height = 400 }) {
  const chartContainerRef = useRef();
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    try {
      // Create chart
      const chart = createChart(chartContainerRef.current, {
        width,
        height,
        layout: {
          background: { color: '#1a1a1a' },
          textColor: '#d1d4dc',
        },
        grid: {
          vertLines: { color: '#2B2B43' },
          horzLines: { color: '#2B2B43' },
        },
        crosshair: {
          mode: 1,
        },
        rightPriceScale: {
          borderColor: '#2B2B43',
        },
        timeScale: {
          borderColor: '#2B2B43',
          timeVisible: true,
          secondsVisible: false,
        },
      });

      // Create candlestick series
      const candleSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });

      chartRef.current = chart;
      candleSeriesRef.current = candleSeries;

      // Cleanup
      return () => {
        if (chart) {
          chart.remove();
        }
      };
    } catch (error) {
      console.error('Chart initialization error:', error);
    }
  }, [width, height]);

  useEffect(() => {
    if (!candleSeriesRef.current || !data || data.length === 0) return;

    try {
      // Transform data for lightweight-charts
      const chartData = data.map(candle => {
        const timestamp = candle.timestamp;
        let time;
        
        if (typeof timestamp === 'string') {
          time = new Date(timestamp).getTime() / 1000;
        } else if (timestamp instanceof Date) {
          time = timestamp.getTime() / 1000;
        } else {
          time = timestamp / 1000;
        }

        return {
          time: Math.floor(time),
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        };
      });

      // lightweight-charts requires data to be strictly sorted by time ascending
      const sortedData = chartData.sort((a, b) => a.time - b.time);
      candleSeriesRef.current.setData(sortedData);

      // Add pattern markers
      if (patterns && patterns.liquidity_sweeps && patterns.liquidity_sweeps.length > 0) {
        const markers = patterns.liquidity_sweeps.map(sweep => {
          const sweepTime = typeof sweep.timestamp === 'string'
            ? new Date(sweep.timestamp).getTime() / 1000
            : sweep.timestamp / 1000;

          return {
            time: Math.floor(sweepTime),
            position: sweep.type === 'buy_side_sweep' ? 'aboveBar' : 'belowBar',
            color: sweep.type === 'buy_side_sweep' ? '#ef5350' : '#26a69a',
            shape: sweep.type === 'buy_side_sweep' ? 'arrowDown' : 'arrowUp',
            text: 'Sweep',
          };
        });
        
        const sortedMarkers = markers.sort((a, b) => a.time - b.time);
        candleSeriesRef.current.setMarkers(sortedMarkers);
      } else {
        // Clear markers if no patterns exist
        candleSeriesRef.current.setMarkers([]);
      }
    } catch (error) {
      console.error('Chart data update error:', error);
    }
  }, [data, patterns]);

  return (
    <div className="trading-chart-wrapper">
      <div ref={chartContainerRef} />
    </div>
  );
}