/**
 * Authentication Context
 *
 * Manages user authentication state, JWT tokens, and OAuth2 flow
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';

interface User {
  user_id: string;
  email: string;
  roles: string[];
  permissions: string[];
}

interface TokenData {
  sub: string;
  email: string;
  roles: string[];
  exp: number;
  iat: number;
  jti: string;
  type: 'access' | 'refresh';
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loginWithOAuth: (provider: 'google' | 'github' | 'microsoft') => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      const accessToken = localStorage.getItem('access_token');

      if (accessToken) {
        try {
          // Verify token is not expired
          const decoded = jwtDecode<TokenData>(accessToken);

          if (decoded.exp * 1000 > Date.now()) {
            // Token is valid, fetch user info
            await fetchUserInfo(accessToken);
          } else {
            // Token expired, try to refresh
            await refreshAccessToken();
          }
        } catch (error) {
          console.error('Failed to load user:', error);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }

      setIsLoading(false);
    };

    loadUser();
  }, []);

  // Auto-refresh token before expiry
  useEffect(() => {
    const accessToken = localStorage.getItem('access_token');

    if (!accessToken) return;

    try {
      const decoded = jwtDecode<TokenData>(accessToken);
      const expiresIn = decoded.exp * 1000 - Date.now();

      // Refresh 5 minutes before expiry
      const refreshTime = expiresIn - 5 * 60 * 1000;

      if (refreshTime > 0) {
        const timeoutId = setTimeout(async () => {
          await refreshAccessToken();
        }, refreshTime);

        return () => clearTimeout(timeoutId);
      }
    } catch (error) {
      console.error('Failed to setup auto-refresh:', error);
    }
  }, [user]);

  const fetchUserInfo = async (accessToken: string) => {
    const response = await fetch(`${API_URL}/api/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user info');
    }

    const userData = await response.json();
    setUser(userData);
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          email,
          password,
        }),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      // Fetch user info
      await fetchUserInfo(data.access_token);
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithOAuth = async (provider: 'google' | 'github' | 'microsoft') => {
    // Get authorization URL
    const response = await fetch(`${API_URL}/auth/login/${provider}`);
    const data = await response.json();

    // Redirect to OAuth provider
    window.location.href = data.authorization_url;
  };

  const logout = async () => {
    setIsLoading(true);

    try {
      const accessToken = localStorage.getItem('access_token');

      if (accessToken) {
        // Call logout endpoint to revoke token
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsLoading(false);
    }
  };

  const refreshAccessToken = async () => {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        // Refresh token expired, logout
        await logout();
        throw new Error('Refresh token expired');
      }

      const data = await response.json();

      // Store new access token
      localStorage.setItem('access_token', data.access_token);

      // Fetch user info with new token
      await fetchUserInfo(data.access_token);
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission);
  };

  const hasRole = (role: string): boolean => {
    if (!user) return false;
    return user.roles.includes(role);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    loginWithOAuth,
    refreshAccessToken,
    hasPermission,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
