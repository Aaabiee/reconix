import api, { setAuthTokens, clearAuthTokens } from './api';
import {
  LoginRequest,
  LoginResponse,
  User,
  ChangePasswordRequest,
  UpdateProfileRequest,
} from '@/types/auth.types';
import { ApiResponse } from '@/types/api.types';

export const authService = {
  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<ApiResponse<LoginResponse>>('/auth/login', request);
    const loginData = response.data.data;

    if (loginData) {
      setAuthTokens(loginData.accessToken, loginData.refreshToken);
      return loginData;
    }

    throw new Error('No login data returned');
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      clearAuthTokens();
    }
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<ApiResponse<User>>('/auth/me');
    if (!response.data.data) {
      throw new Error('No user data returned');
    }
    return response.data.data;
  },

  async refreshToken(): Promise<string> {
    const response = await api.post<ApiResponse<{ accessToken: string; expiresIn: number }>>('/auth/refresh');
    const accessToken = response.data.data?.accessToken;

    if (!accessToken) {
      throw new Error('No access token returned');
    }

    return accessToken;
  },

  async changePassword(request: ChangePasswordRequest): Promise<void> {
    await api.post('/auth/change-password', request);
  },

  async updateProfile(request: UpdateProfileRequest): Promise<User> {
    const response = await api.put<ApiResponse<User>>('/auth/profile', request);
    if (!response.data.data) {
      throw new Error('No user data returned');
    }
    return response.data.data;
  },

  isTokenExpired(token: string): boolean {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return true;

      const decoded = JSON.parse(atob(parts[1]));
      const expiresAt = decoded.exp * 1000;

      return Date.now() >= expiresAt;
    } catch {
      return true;
    }
  },
};
