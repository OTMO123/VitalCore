import axios, { AxiosInstance, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiResponse } from '@/types';

interface RetryableAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// ============================================
// API CLIENT CONFIGURATION
// ============================================

class ApiClient {
  private client: AxiosInstance;
  private refreshTokenPromise: Promise<string> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: 'http://localhost:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for adding auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add request correlation ID for audit logging
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for handling token refresh
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as RetryableAxiosRequestConfig;
        
        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const newAccessToken = await this.refreshAccessToken();
            if (newAccessToken && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            this.handleAuthError();
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  private getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  private clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async refreshAccessToken(): Promise<string> {
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise;
    }

    this.refreshTokenPromise = this.performTokenRefresh();
    
    try {
      const newAccessToken = await this.refreshTokenPromise;
      return newAccessToken;
    } finally {
      this.refreshTokenPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string> {
    const refreshToken = this.getRefreshToken();
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await axios.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token: newRefreshToken } = response.data;
      this.setTokens(access_token, newRefreshToken);
      
      return access_token;
    } catch (error) {
      this.clearTokens();
      throw error;
    }
  }

  private handleAuthError(): void {
    this.clearTokens();
    // Dispatch logout action or redirect to login
    window.location.href = '/login';
  }

  // ============================================
  // UTILITY METHODS
  // ============================================

  getBaseURL(): string {
    return this.client.defaults.baseURL || 'http://localhost:8000/api/v1';
  }

  // ============================================
  // HTTP METHODS
  // ============================================

  async get<T = any>(url: string, params?: any, config?: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.client.get(url, { ...config, params });
      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  async post<T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.client.post(url, data, config);
      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  async put<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.client.put(url, data);
      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  async patch<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.client.patch(url, data);
      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  async delete<T = any>(url: string): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.client.delete(url);
      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  private handleError(error: AxiosError): ApiResponse {
    const responseData = error.response?.data as any;
    
    // Handle Pydantic validation errors specifically
    if (responseData?.detail && Array.isArray(responseData.detail)) {
      const validationErrors = responseData.detail.map((err: any) => 
        `${err.loc?.join(' -> ') || 'Field'}: ${err.msg || 'Invalid value'}`
      ).join('; ');
      return {
        error: validationErrors,
        status: error.response?.status || 500,
      };
    }
    
    const errorMessage = responseData?.detail || 
                        responseData?.message || 
                        error.message || 
                        'An unexpected error occurred';
    
    // Ensure error is always a string
    const finalError = typeof errorMessage === 'object' 
      ? JSON.stringify(errorMessage) 
      : String(errorMessage);

    return {
      error: finalError,
      status: error.response?.status || 500,
    };
  }

  // ============================================
  // AUTHENTICATION METHODS
  // ============================================

  async login(username: string, password: string): Promise<ApiResponse> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await this.client.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token, refresh_token } = response.data;
      this.setTokens(access_token, refresh_token);

      return { data: response.data, status: response.status };
    } catch (error) {
      return this.handleError(error as AxiosError);
    }
  }

  logout(): void {
    this.clearTokens();
  }

  isAuthenticated(): boolean {
    const token = this.getAccessToken();
    if (!token) return false;

    try {
      // Simple token expiry check (you might want to decode JWT for proper validation)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Date.now() / 1000;
      
      return payload.exp > now;
    } catch {
      return false;
    }
  }

  getCurrentUser(): any {
    const token = this.getAccessToken();
    if (!token) return null;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.user || payload;
    } catch {
      return null;
    }
  }
}

// ============================================
// SINGLETON INSTANCE
// ============================================

export const apiClient = new ApiClient();
export default apiClient;