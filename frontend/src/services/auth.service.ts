import { apiClient } from './api';
import { LoginRequest, RegisterRequest, TokenResponse, User, ApiResponse } from '@/types';

// ============================================
// AUTHENTICATION SERVICE
// ============================================

export class AuthService {
  /**
   * Login user with username and password
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<TokenResponse>> {
    return apiClient.login(credentials.username, credentials.password);
  }

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<ApiResponse<User>> {
    return apiClient.post('/auth/register', userData);
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    return apiClient.get('/auth/me');
  }

  /**
   * Update user profile
   */
  async updateProfile(userData: Partial<User>): Promise<ApiResponse<User>> {
    return apiClient.put('/auth/me', userData);
  }

  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<ApiResponse> {
    return apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<ApiResponse> {
    return apiClient.post('/auth/forgot-password', { email });
  }

  /**
   * Confirm password reset with token
   */
  async confirmPasswordReset(token: string, newPassword: string): Promise<ApiResponse> {
    return apiClient.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Ignore logout errors, clear tokens anyway
      console.warn('Logout request failed:', error);
    } finally {
      apiClient.logout();
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return apiClient.isAuthenticated();
  }

  /**
   * Get current user from token (without API call)
   */
  getCurrentUserFromToken(): any {
    return apiClient.getCurrentUser();
  }

  /**
   * Get all users (admin only)
   */
  async getUsers(params?: {
    offset?: number;
    limit?: number;
    search?: string;
    role?: string;
  }): Promise<ApiResponse<User[]>> {
    return apiClient.get('/auth/users', params);
  }

  /**
   * Create new user (admin only)
   */
  async createUser(userData: RegisterRequest): Promise<ApiResponse<User>> {
    return apiClient.post('/auth/users', userData);
  }

  /**
   * Update user (admin only)
   */
  async updateUser(userId: string, userData: Partial<User>): Promise<ApiResponse<User>> {
    return apiClient.put(`/auth/users/${userId}`, userData);
  }

  /**
   * Delete user (admin only)
   */
  async deleteUser(userId: string): Promise<ApiResponse> {
    return apiClient.delete(`/auth/users/${userId}`);
  }

  /**
   * Get user roles
   */
  async getRoles(): Promise<ApiResponse> {
    return apiClient.get('/auth/roles');
  }

  /**
   * Get user permissions
   */
  async getPermissions(): Promise<ApiResponse> {
    return apiClient.get('/auth/permissions');
  }
}

export const authService = new AuthService();