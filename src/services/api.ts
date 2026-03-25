import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiResponse, ErrorResponse } from '@/types/api.types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

let authTokens = {
  accessToken: '',
  refreshToken: '',
};

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

function setCookie(name: string, value: string, days: number, secure: boolean = true): void {
  if (typeof document === 'undefined') return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  const flags = [
    `${name}=${encodeURIComponent(value)}`,
    `expires=${expires}`,
    'path=/',
    'SameSite=Strict',
  ];
  if (secure && window.location.protocol === 'https:') {
    flags.push('Secure');
  }
  document.cookie = flags.join('; ');
}

function deleteCookie(name: string): void {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Strict`;
}

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = authTokens.accessToken || getCookie('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = authTokens.refreshToken || getCookie('refreshToken');
        if (!refreshToken) {
          clearAuthTokens();
          window.location.href = '/';
          return Promise.reject(error);
        }

        const response = await axios.post<ApiResponse<{ accessToken: string; expiresIn: number }>>(
          `${API_BASE_URL}/auth/refresh`,
          { refreshToken }
        );

        const newAccessToken = response.data.data?.accessToken;
        if (newAccessToken) {
          authTokens.accessToken = newAccessToken;
          setCookie('accessToken', newAccessToken, 1);
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return axiosInstance(originalRequest);
        }
      } catch {
        clearAuthTokens();
        window.location.href = '/';
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export const setAuthTokens = (accessToken: string, refreshToken: string): void => {
  authTokens = { accessToken, refreshToken };
  setCookie('accessToken', accessToken, 1);
  setCookie('refreshToken', refreshToken, 7);
};

export const getAuthTokens = (): { accessToken: string; refreshToken: string } => {
  return {
    accessToken: authTokens.accessToken || getCookie('accessToken') || '',
    refreshToken: authTokens.refreshToken || getCookie('refreshToken') || '',
  };
};

export const clearAuthTokens = (): void => {
  authTokens = { accessToken: '', refreshToken: '' };
  deleteCookie('accessToken');
  deleteCookie('refreshToken');
};

export default axiosInstance;
