import React, { useEffect, useState } from 'react';
import { useMarket } from '../context/MarketContext';
import { TradingChart } from '../components/TradingChart';
import { PatternPanel } from '../components/PatternPanel';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

const NSE_STOCKS = [
  'RELIANCE', 'HDFCBANK', 'ICICIBANK', 'INFY', 'TATAMOTORS',
  'SBIN', 'AXISBANK', 'TCS', 'BAJFINANCE', 'KOTAKBANK'
];

export function Dashboard() {
  const {
    candles,
    analysis,
    isConnected,
    selectedInstrument,
    setSelectedInstrument,
    loadHistoricalData,
    loadAnalysis,
    connectWebSocket,
    subscribeToInstruments
  } = useMarket();

  const [instruments, setInstruments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [timeframe, setTimeframe] = useState('1minute');
  const [paperAccount, setPaperAccount] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load instruments
    loadInstruments();
    
    // Connect WebSocket
    connectWebSocket('user_demo');

    // Load or create paper trading account
    loadPaperAccount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedInstrument) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedInstrument, timeframe]);

  const loadInstruments = async () => {
    try {
      const response = await axios.get(`${API}/instruments`);
      if (response.data.status === 'success') {
        setInstruments(response.data.instruments);
      }
    } catch (error) {
      console.error('Failed to load instruments:', error);
      // Use fallback
      setInstruments(NSE_STOCKS.map(symbol => ({
        symbol,
        instrument_key: `NSE_EQ|${symbol}`,
        exchange: 'NSE'
      })));
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      await loadHistoricalData(selectedInstrument, timeframe);
      await loadAnalysis(selectedInstrument, timeframe);
      
      // Subscribe to real-time updates
      subscribeToInstruments([selectedInstrument]);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPaperAccount = async () => {
    try {
      const response = await axios.get(`${API}/paper-trading/account/user_demo`);
      if (response.data.status === 'success') {
        setPaperAccount(response.data.account);
      }
    } catch (error) {
      // Create new account
      try {
        const createResponse = await axios.post(`${API}/paper-trading/create-account`, null, {
          params: { user_id: 'user_demo', initial_balance: 100000 }
        });
        if (createResponse.data.status === 'success') {
          setPaperAccount({
            user_id: 'user_demo',
            balance: 100000,
            positions: [],
            orders: []
          });
        }
      } catch (createError) {
        console.error('Failed to create account:', createError);
      }
    }
  };

  const handleSelectInstrument = (instrumentKey, symbol) => {
    setSelectedInstrument(instrumentKey);
  };

  const handlePlaceOrder = async (type, quantity = 1) => {
    if (!selectedInstrument || !candles[selectedInstrument]) return;

    const latestCandle = candles[selectedInstrument][candles[selectedInstrument].length - 1];
    const price = latestCandle.close;

    try {
      const response = await axios.post(`${API}/paper-trading/order`, null, {
        params: {
          user_id: 'user_demo',
          instrument_key: selectedInstrument,
          order_type: type,
          quantity,
          price
        }
      });

      if (response.data.status === 'success') {
        alert(`Order placed: ${type.toUpperCase()} ${quantity} @ ₹${price.toFixed(2)}`);
        loadPaperAccount();
      }
    } catch (error) {
      console.error('Order failed:', error);
      alert('Order failed: ' + error.message);
    }
  };

  const filteredInstruments = instruments.filter(inst =>
    (inst.symbol || inst.trading_symbol || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const currentCandles = selectedInstrument ? candles[selectedInstrument] : [];
  const currentAnalysis = selectedInstrument ? analysis[selectedInstrument] : null;
  const latestCandle = currentCandles?.length > 0 ? currentCandles[currentCandles.length - 1] : null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Institutional Trading Dashboard
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">NSE Market Analysis</p>
            </div>
            
            <div className="flex items-center gap-4">
              {paperAccount && (
                <Card className="border-green-500">
                  <CardContent className="p-3">
                    <p className="text-sm text-gray-500">Paper Balance</p>
                    <p className="text-xl font-bold text-green-600">₹{paperAccount.balance?.toLocaleString()}</p>
                  </CardContent>
                </Card>
              )}
              
              <Badge variant={isConnected ? 'default' : 'destructive'}>
                {isConnected ? '✓ Live' : '✗ Disconnected'}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Stock List */}
          <div className="col-span-3">
            <Card>
              <CardHeader>
                <CardTitle>NSE Stocks</CardTitle>
                <Input
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="mt-2"
                />
              </CardHeader>
              <CardContent>
                <div className="space-y-1 max-h-[600px] overflow-y-auto">
                  {filteredInstruments.map((inst) => {
                    const symbol = inst.symbol || inst.trading_symbol;
                    const key = inst.instrument_key;
                    const isSelected = selectedInstrument === key;
                    
                    return (
                      <Button
                        key={key}
                        variant={isSelected ? 'default' : 'ghost'}
                        className="w-full justify-start"
                        onClick={() => handleSelectInstrument(key, symbol)}
                        data-testid={`stock-${symbol}`}
                      >
                        <span className="font-medium">{symbol}</span>
                      </Button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content - Chart */}
          <div className="col-span-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>
                    {selectedInstrument ? selectedInstrument.split('|')[1] : 'Select a stock'}
                  </CardTitle>
                  
                  <div className="flex gap-2">
                    {['1minute', '5minute', '1hour', 'day'].map(tf => (
                      <Button
                        key={tf}
                        size="sm"
                        variant={timeframe === tf ? 'default' : 'outline'}
                        onClick={() => setTimeframe(tf)}
                        data-testid={`timeframe-${tf}`}
                      >
                        {tf}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center h-[400px]">
                    <p className="text-gray-500">Loading...</p>
                  </div>
                ) : currentCandles?.length > 0 ? (
                  <div data-testid="trading-chart">
                    <TradingChart
                      data={currentCandles}
                      patterns={currentAnalysis}
                      width={700}
                      height={400}
                    />
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-[400px]">
                    <p className="text-gray-500">Select a stock to view chart</p>
                  </div>
                )}

                {/* Latest Price Info */}
                {latestCandle && (
                  <div className="mt-4 grid grid-cols-5 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded">
                    <div>
                      <p className="text-xs text-gray-500">Open</p>
                      <p className="text-sm font-medium">₹{latestCandle.open?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">High</p>
                      <p className="text-sm font-medium text-green-600">₹{latestCandle.high?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Low</p>
                      <p className="text-sm font-medium text-red-600">₹{latestCandle.low?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Close</p>
                      <p className="text-sm font-medium">₹{latestCandle.close?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Volume</p>
                      <p className="text-sm font-medium">{latestCandle.volume?.toLocaleString()}</p>
                    </div>
                  </div>
                )}

                {/* Paper Trading Controls */}
                {selectedInstrument && (
                  <div className="mt-4 flex gap-2" data-testid="paper-trading-controls">
                    <Button
                      className="flex-1"
                      variant="default"
                      onClick={() => handlePlaceOrder('buy', 1)}
                      data-testid="buy-button"
                    >
                      BUY
                    </Button>
                    <Button
                      className="flex-1"
                      variant="destructive"
                      onClick={() => handlePlaceOrder('sell', 1)}
                      data-testid="sell-button"
                    >
                      SELL
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Sidebar - Pattern Analysis */}
          <div className="col-span-3">
            <div className="space-y-4" data-testid="pattern-panel">
              <PatternPanel analysis={currentAnalysis} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}