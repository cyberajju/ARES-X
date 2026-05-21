import type { User } from './types';
import api from './api';

const ACCESS_TOKEN_KEY = 'ares_x_access_token';
const REFRESH_TOKEN_KEY = 'ares_x_refresh_token';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  const token = getAccessToken();
  if (!token) return false;

  // Check if token is expired (basic JWT decode)
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

export function getCurrentUser(): User | null {
  const token = getAccessToken();
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      id: payload.sub,
      email: payload.email,
      name: payload.name,
      role: payload.role,
      clearanceLevel: payload.clearance_level || 1,
    };
  } catch {
    return null;
  }
}

export async function login(email: string, password: string): Promise<{ success: boolean; mfaRequired?: boolean }> {
  try {
    const response = await api.post<{ access_token: string; refresh_token: string; mfa_required?: boolean }>(
      '/api/v1/auth/login',
      { email, password }
    );

    if (response.mfa_required) {
      return { success: false, mfaRequired: true };
    }

    localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);
    return { success: true };
  } catch {
    return { success: false };
  }
}

export async function verifyMfa(code: string): Promise<boolean> {
  try {
    const response = await api.post<{ access_token: string; refresh_token: string }>(
      '/api/v1/auth/mfa/verify',
      { code }
    );

    localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);
    return true;
  } catch {
    return false;
  }
}

export function logout(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.location.href = '/login';
}
