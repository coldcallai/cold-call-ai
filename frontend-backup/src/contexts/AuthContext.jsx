import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionToken, setSessionToken] = useState(localStorage.getItem('session_token'));

  const checkAuth = useCallback(async () => {
    // CRITICAL: If returning from OAuth callback, skip the /me check.
    // AuthCallback will exchange the session_id and establish the session first.
    if (window.location.hash?.includes('session_id=')) {
      setLoading(false);
      return;
    }

    const token = localStorage.getItem('session_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true
      });
      setUser(response.data);
      setSessionToken(token);
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('session_token');
      setUser(null);
      setSessionToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password }, { withCredentials: true });
    const { user, session_token } = response.data;
    localStorage.setItem('session_token', session_token);
    setSessionToken(session_token);
    setUser(user);
    return user;
  };

  const register = async (email, password, name) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, name }, { withCredentials: true });
    const { user, session_token } = response.data;
    localStorage.setItem('session_token', session_token);
    setSessionToken(session_token);
    setUser(user);
    return user;
  };

  const exchangeSessionId = async (sessionId) => {
    const response = await axios.post(`${API}/auth/session`, { session_id: sessionId }, { withCredentials: true });
    const { user, session_token } = response.data;
    localStorage.setItem('session_token', session_token);
    setSessionToken(session_token);
    setUser(user);
    return user;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { 
        headers: { Authorization: `Bearer ${sessionToken}` },
        withCredentials: true 
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    localStorage.removeItem('session_token');
    setSessionToken(null);
    setUser(null);
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const loginWithGoogle = () => {
    const redirectUrl = window.location.origin + '/app';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const value = {
    user,
    loading,
    sessionToken,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    loginWithGoogle,
    exchangeSessionId,
    refreshUser: checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
