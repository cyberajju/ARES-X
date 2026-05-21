'use client';

import { useState, useEffect } from 'react';
import type { User } from '@/lib/types';
import {
  isAuthenticated as checkAuth,
  getCurrentUser,
  login as performLogin,
  logout as performLogout,
} from '@/lib/auth';

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; mfaRequired?: boolean }>;
  logout: () => void;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const authed = checkAuth();
    setAuthenticated(authed);
    if (authed) {
      setUser(getCurrentUser());
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const result = await performLogin(email, password);
    if (result.success) {
      setAuthenticated(true);
      setUser(getCurrentUser());
    }
    return result;
  };

  const logout = () => {
    performLogout();
    setAuthenticated(false);
    setUser(null);
  };

  return {
    user,
    isAuthenticated: authenticated,
    isLoading,
    login,
    logout,
  };
}

export default useAuth;
