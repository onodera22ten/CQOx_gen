/**
 * OAuth2 Callback Handler
 *
 * Handles OAuth2 redirect and token exchange
 */
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const OAuthCallback: React.FC = () => {
  const [error, setError] = useState('');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const provider = window.location.pathname.split('/').pop();

      if (!code || !state) {
        setError('Invalid OAuth callback - missing code or state');
        return;
      }

      try {
        // Exchange code for tokens
        const response = await fetch(
          `${API_URL}/auth/callback/${provider}?code=${code}&state=${state}`
        );

        if (!response.ok) {
          throw new Error('OAuth authentication failed');
        }

        const data = await response.json();

        // Store tokens
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);

        // Redirect to home
        navigate('/', { replace: true });
      } catch (err: any) {
        setError(err.message || 'Authentication failed');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full space-y-8">
          <div className="rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">
              <h3 className="font-medium">Authentication Error</h3>
              <p className="mt-2">{error}</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/login')}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing authentication...</p>
      </div>
    </div>
  );
};
