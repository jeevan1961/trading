import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from 'axios';

// Added a fallback to localhost just in case the .env variable isn't loaded properly
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

const MarketContext = createContext(null);

export function MarketProvider({ children }) {
  const [candles, setCandles] = useState({});
  const [analysis, setAnalysis] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const [selectedInstrument, setSelectedInstrument] = useState(null);
  const [ws, setWs] = useState(null);

  const addCandle = useCallback((instrumentKey, candle) => {
    setCandles(prev => ({
      ...prev,
      [instrumentKey]: [...(prev[instrumentKey] || []), candle]
    }));
  }, []);

  const loadHistoricalData = useCallback(async (instrumentKey, interval = '1minute') => {
    try {
      const response = await axios.get(`${API}/candles/historical`, {
        params: { instrument_key: instrumentKey, interval }
      });
      
      if (response.data.status === 'success') {
        setCandles(prev => ({
          ...prev,
          [instrumentKey]: response.data.candles
        }));
      }
    } catch (error) {
      console.error('Failed to load historical data:', error);
    }
  }, []);

  const loadAnalysis = useCallback(async (instrumentKey, interval = '1minute') => {
    try {
      const response = await axios.get(`${API}/analysis/price-action`, {
        params: { instrument_key: instrumentKey, interval }
      });
      
      if (response.data.status === 'success') {
        setAnalysis(prev => ({
          ...prev,
          [instrumentKey]: response.data.analysis
        }));
      }
    } catch (error) {
      console.error('Failed to load analysis:', error);
    }
  }, []);

  const connectWebSocket = useCallback((userId) => {
    // Safety check so .replace() doesn't crash if BACKEND_URL is undefined
    if (!BACKEND_URL) {
      console.error('BACKEND_URL is not defined in environment variables.');
      return;
    }

    const wsUrl = `${BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/ws/market-data?user_id=${userId}`;
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'market_update') {
        addCandle(data.instrument_key, data.data);
      }
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(websocket);
    return websocket;
  }, [addCandle]);

  const subscribeToInstruments = useCallback((instrumentKeys) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'subscribe',
        instrument_keys: instrumentKeys
      }));
    }
  }, [ws]);

  return (
    <MarketContext.Provider value={{
      candles,
      analysis,
      isConnected,
      selectedInstrument,
      setSelectedInstrument,
      addCandle,
      loadHistoricalData,
      loadAnalysis,
      connectWebSocket,
      subscribeToInstruments
    }}>
      {children}
    </MarketContext.Provider>
  );
}

export function useMarket() {
  const context = useContext(MarketContext);
  if (!context) throw new Error('useMarket must be used within MarketProvider');
  return context;
}