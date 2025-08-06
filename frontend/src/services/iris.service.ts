import { apiClient } from './api';
import { IRISEndpoint, SyncResult, HealthCheckResponse, SystemHealthResponse, ApiResponse } from '@/types';

// ============================================
// IRIS API SERVICE
// ============================================

export class IRISService {
  /**
   * Get health status of IRIS endpoints
   */
  async getHealthCheck(endpointId?: string): Promise<ApiResponse<HealthCheckResponse[]>> {
    const params = endpointId ? { endpoint_id: endpointId } : undefined;
    return apiClient.get('/iris/health', params);
  }

  /**
   * Get overall system health summary
   */
  async getHealthSummary(): Promise<ApiResponse<SystemHealthResponse>> {
    return apiClient.get('/iris/health/summary');
  }

  /**
   * Create new API endpoint configuration
   */
  async createEndpoint(endpointData: {
    name: string;
    url: string;
    auth_type: 'oauth2' | 'hmac' | 'basic';
    description?: string;
    timeout_seconds?: number;
    retry_attempts?: number;
  }): Promise<ApiResponse<IRISEndpoint>> {
    return apiClient.post('/iris/endpoints', endpointData);
  }

  /**
   * Get all IRIS endpoints
   */
  async getEndpoints(): Promise<ApiResponse<IRISEndpoint[]>> {
    return apiClient.get('/iris/endpoints');
  }

  /**
   * Get specific endpoint
   */
  async getEndpoint(endpointId: string): Promise<ApiResponse<IRISEndpoint>> {
    return apiClient.get(`/iris/endpoints/${endpointId}`);
  }

  /**
   * Update endpoint configuration
   */
  async updateEndpoint(endpointId: string, endpointData: Partial<IRISEndpoint>): Promise<ApiResponse<IRISEndpoint>> {
    return apiClient.put(`/iris/endpoints/${endpointId}`, endpointData);
  }

  /**
   * Delete endpoint
   */
  async deleteEndpoint(endpointId: string): Promise<ApiResponse> {
    return apiClient.delete(`/iris/endpoints/${endpointId}`);
  }

  /**
   * Add credentials to endpoint
   */
  async addEndpointCredentials(endpointId: string, credentials: {
    credential_type: 'oauth2' | 'hmac' | 'basic';
    client_id?: string;
    client_secret?: string;
    username?: string;
    password?: string;
    api_key?: string;
    shared_secret?: string;
  }): Promise<ApiResponse> {
    return apiClient.post(`/iris/endpoints/${endpointId}/credentials`, credentials);
  }

  /**
   * Trigger data synchronization
   */
  async triggerSync(syncData?: {
    endpoint_id?: string;
    patient_id?: string;
    sync_type?: 'full' | 'incremental';
    force?: boolean;
  }): Promise<ApiResponse<SyncResult>> {
    return apiClient.post('/iris/sync', syncData);
  }

  /**
   * Get synchronization status
   */
  async getSyncStatus(syncId: string): Promise<ApiResponse<SyncResult>> {
    return apiClient.get(`/iris/sync/status/${syncId}`);
  }

  /**
   * Get all sync operations
   */
  async getSyncOperations(params?: {
    status?: string;
    endpoint_id?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<SyncResult[]>> {
    return apiClient.get('/iris/sync/operations', params);
  }

  /**
   * Cancel sync operation
   */
  async cancelSync(syncId: string): Promise<ApiResponse> {
    return apiClient.post(`/iris/sync/${syncId}/cancel`);
  }

  /**
   * Get sync statistics
   */
  async getSyncStatistics(params?: {
    period?: 'day' | 'week' | 'month';
    endpoint_id?: string;
  }): Promise<ApiResponse<{
    total_syncs: number;
    successful_syncs: number;
    failed_syncs: number;
    avg_sync_time: number;
    records_synced: number;
    error_rate: number;
  }>> {
    return apiClient.get('/iris/sync/statistics', params);
  }

  /**
   * Test endpoint connectivity
   */
  async testEndpoint(endpointId: string): Promise<ApiResponse<{
    status: 'success' | 'failure';
    response_time: number;
    error_message?: string;
    test_timestamp: string;
  }>> {
    return apiClient.post(`/iris/endpoints/${endpointId}/test`);
  }

  /**
   * Get endpoint metrics
   */
  async getEndpointMetrics(endpointId: string, params?: {
    start_date?: string;
    end_date?: string;
    metric_type?: 'response_time' | 'success_rate' | 'error_count';
  }): Promise<ApiResponse<{
    endpoint_id: string;
    metrics: Array<{
      timestamp: string;
      value: number;
      metric_type: string;
    }>;
  }>> {
    return apiClient.get(`/iris/endpoints/${endpointId}/metrics`, params);
  }

  /**
   * Get circuit breaker status
   */
  async getCircuitBreakerStatus(): Promise<ApiResponse<{
    circuit_breakers: Array<{
      name: string;
      state: 'closed' | 'open' | 'half_open';
      failure_count: number;
      last_failure_time?: string;
      next_attempt_time?: string;
    }>;
  }>> {
    return apiClient.get('/iris/circuit-breakers/status');
  }

  /**
   * Reset circuit breaker
   */
  async resetCircuitBreaker(breakerName: string): Promise<ApiResponse> {
    return apiClient.post(`/iris/circuit-breakers/${breakerName}/reset`);
  }

  /**
   * Get IRIS API logs
   */
  async getAPILogs(params?: {
    endpoint_id?: string;
    level?: 'debug' | 'info' | 'warning' | 'error';
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<Array<{
    id: string;
    timestamp: string;
    level: string;
    message: string;
    endpoint_id?: string;
    request_id?: string;
    details?: any;
  }>>> {
    return apiClient.get('/iris/logs', params);
  }

  /**
   * Get legacy IRIS status (backward compatibility)
   */
  async getLegacyStatus(): Promise<ApiResponse<{
    status: string;
    endpoints: number;
    last_sync: string;
    message?: string;
  }>> {
    return apiClient.get('/iris/status');
  }
}

export const irisService = new IRISService();