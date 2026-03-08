import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

export function AuthCallback({ onLogin }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setStatus('error');
      setError(decodeURIComponent(errorParam));
      setTimeout(() => {
        navigate('/login');
      }, 3000);
      return;
    }

    if (token) {
      localStorage.setItem('token', token);
      setStatus('success');
      onLogin(token);
      
      setTimeout(() => {
        navigate('/');
      }, 1500);
    } else {
      setStatus('error');
      setError('No authentication token received');
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    }
  }, [searchParams, navigate, onLogin]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">
            {status === 'processing' && 'Authenticating...'}
            {status === 'success' && '✓ Authentication Successful!'}
            {status === 'error' && '✗ Authentication Failed'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {status === 'processing' && (
            <div className="flex flex-col items-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              <p className="text-gray-600 dark:text-gray-400">
                Processing your Upstox login...
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="flex flex-col items-center space-y-4">
              <div className="text-6xl text-green-500">✓</div>
              <p className="text-gray-600 dark:text-gray-400">
                Successfully authenticated with Upstox!
              </p>
              <p className="text-sm text-gray-500">
                Redirecting to dashboard...
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="flex flex-col items-center space-y-4">
              <div className="text-6xl text-red-500">✗</div>
              <p className="text-red-600 dark:text-red-400 font-medium">
                {error || 'Authentication failed'}
              </p>
              <p className="text-sm text-gray-500">
                Redirecting to login page...
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
