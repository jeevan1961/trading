import React, { useEffect, useRef } from "react";
import { createChart, CandlestickSeries } from "lightweight-charts";

export default function ChartPanel() {

  const chartContainerRef = useRef(null);

  useEffect(() => {

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: "#161a23" },
        textColor: "#d1d4dc"
      },
      grid: {
        vertLines: { color: "#2b2f3a" },
        horzLines: { color: "#2b2f3a" }
      }
    });

    const candleSeries = chart.addSeries(CandlestickSeries);

    const socket = new WebSocket("ws://localhost:8000/stream");

    socket.onmessage = (event) => {

      try {

        const data = JSON.parse(event.data);

        if (data.type === "market_data" && data.candle) {

          const candle = data.candle;

          candleSeries.update({
            time: Math.floor(new Date(candle.timestamp).getTime() / 1000),
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close
          });

        }

      } catch (err) {
        console.error("Chart update error", err);
      }

    };

    return () => {
      socket.close();
      chart.remove();
    };

  }, []);

  return (
    <div>
      <h3>Live Chart</h3>

      <div
        ref={chartContainerRef}
        style={{ width: "100%", height: "400px" }}
      />
    </div>
  );

}
