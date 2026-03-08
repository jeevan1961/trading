import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

export function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/simple-login`, null, {
        params: { username, password }
      });

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        onLogin(response.data.access_token);
      }
    } catch (err) {
      setError('Invalid credentials. Try: admin / admin123');
    } finally {
      setLoading(false);
    }
  };

  const handleUpstoxLogin = () => {
    window.location.href = `${API}/auth/login`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Trading Dashboard Login</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Username</label>
              <Input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
                data-testid="username-input"
              />
            </div>
            
            <div>
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="admin123"
                required
                data-testid="password-input"
              />
            </div>

            {error && (
              <p className="text-sm text-red-500" data-testid="error-message">{error}</p>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={loading}
              data-testid="login-button"
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t">
            <p className="text-sm text-center text-gray-500 mb-3">
              Or connect with Upstox
            </p>
            <Button
              variant="outline"
              className="w-full"
              onClick={handleUpstoxLogin}
              data-testid="upstox-login-button"
            >
              Login with Upstox
            </Button>
          </div>

          <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              <strong>Demo Credentials:</strong><br />
              Username: admin<br />
              Password: admin123
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
