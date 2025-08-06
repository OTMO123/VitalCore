import { apiClient } from './api';
import { AuditLog, ComplianceReport, ApiResponse } from '@/types';

// ============================================
// AUDIT SERVICE
// ============================================

export class AuditService {
  /**
   * Get audit service health
   */
  async getHealth(): Promise<ApiResponse<{
    status: string;
    service: string;
    audit_handlers: number;
    integrity_status: string;
  }>> {
    return apiClient.get('/audit/health');
  }

  /**
   * Get recent activities for dashboard
   */
  async getRecentActivities(limit: number = 10): Promise<ApiResponse<{
    activities: Array<{
      id: string;
      type: 'patient_created' | 'user_login' | 'sync_completed' | 'audit_event' | 'phi_access';
      description: string;
      timestamp: string;
      user?: string;
      severity?: 'info' | 'warning' | 'error' | 'success';
    }>;
  }>> {
    return apiClient.get(`/audit/recent-activities?limit=${limit}`);
  }

  /**
   * Get enhanced security activities for SOC2 dashboard
   */
  async getEnhancedActivities(params?: {
    limit?: number;
    category?: 'security' | 'phi' | 'admin' | 'system' | 'compliance';
    severity?: 'critical' | 'high' | 'medium' | 'low';
    hours?: number;
  }): Promise<ApiResponse<{
    activities: Array<{
      id: string;
      type: string;
      category: 'security' | 'phi' | 'admin' | 'system' | 'compliance';
      title: string;
      description: string;
      timestamp: string;
      user?: string;
      userId?: string;
      severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
      ipAddress?: string;
      userAgent?: string;
      resourceId?: string;
      resourceType?: string;
      metadata?: Record<string, any>;
      complianceFlags?: string[];
    }>;
    summary: {
      total_events: number;
      security_events: number;
      phi_events: number;
      critical_events: number;
      failed_logins: number;
      phi_access_count: number;
      admin_actions: number;
      time_range_hours: number;
    };
    filters_applied: {
      category?: string;
      severity?: string;
      hours: number;
      limit: number;
    };
  }>> {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.category) queryParams.append('category', params.category);
    if (params?.severity) queryParams.append('severity', params.severity);
    if (params?.hours) queryParams.append('hours', params.hours.toString());
    
    const queryString = queryParams.toString();
    const url = `/audit/enhanced-activities${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.get(url);
  }

  /**
   * Get audit logging statistics
   */
  async getStats(): Promise<ApiResponse<{
    total_logs: number;
    logs_today: number;
    security_events: number;
    compliance_events: number;
    avg_logs_per_hour: number;
    integrity_checks_passed: number;
    last_integrity_check: string;
  }>> {
    return apiClient.get('/audit/stats');
  }

  /**
   * Query audit logs with advanced filters
   */
  async queryLogs(queryParams: {
    event_types?: string[];
    severity_levels?: string[];
    user_ids?: string[];
    resource_types?: string[];
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
    include_details?: boolean;
  }): Promise<ApiResponse<{
    logs: AuditLog[];
    total_count: number;
    query_metadata: {
      execution_time_ms: number;
      filtered_count: number;
      index_used: boolean;
    };
  }>> {
    return apiClient.post('/audit/logs/query', queryParams);
  }

  /**
   * Get basic audit logs
   */
  async getLogs(params?: {
    event_type?: string;
    severity?: string;
    user_id?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<ApiResponse<AuditLog[]>> {
    return apiClient.get('/audit/logs', params);
  }

  /**
   * Generate compliance report
   */
  async generateComplianceReport(reportParams: {
    report_type: 'soc2' | 'hipaa' | 'gdpr' | 'custom';
    period_start: string;
    period_end: string;
    include_details?: boolean;
    export_format?: 'json' | 'pdf' | 'csv';
    notification_email?: string;
  }): Promise<ApiResponse<{
    report_id: string;
    status: 'generating' | 'completed';
    estimated_completion?: string;
    download_url?: string;
  }>> {
    return apiClient.post('/audit/reports/compliance', reportParams);
  }

  /**
   * Get available report types
   */
  async getReportTypes(): Promise<ApiResponse<Array<{
    type: string;
    name: string;
    description: string;
    required_fields: string[];
    supported_formats: string[];
  }>>> {
    return apiClient.get('/audit/reports/types');
  }

  /**
   * Get compliance report status
   */
  async getReportStatus(reportId: string): Promise<ApiResponse<ComplianceReport>> {
    return apiClient.get(`/audit/reports/${reportId}/status`);
  }

  /**
   * Download compliance report
   */
  async downloadReport(reportId: string, format: 'json' | 'pdf' | 'csv' = 'json'): Promise<ApiResponse<Blob>> {
    return apiClient.get(`/audit/reports/${reportId}/download?format=${format}`, {
      responseType: 'blob',
    });
  }

  /**
   * Verify audit log integrity
   */
  async verifyIntegrity(params?: {
    start_date?: string;
    end_date?: string;
    log_ids?: string[];
    full_verification?: boolean;
  }): Promise<ApiResponse<{
    verification_id: string;
    status: 'verified' | 'corrupted' | 'processing';
    total_logs_checked: number;
    integrity_violations: Array<{
      log_id: string;
      violation_type: string;
      description: string;
      severity: string;
    }>;
    verification_timestamp: string;
    chain_integrity: boolean;
  }>> {
    return apiClient.post('/audit/integrity/verify', params);
  }

  /**
   * Get SIEM export configurations
   */
  async getSIEMConfigs(): Promise<ApiResponse<Array<{
    id: string;
    name: string;
    siem_type: 'splunk' | 'elastic' | 'azure_sentinel' | 'custom';
    endpoint_url: string;
    status: 'active' | 'inactive' | 'error';
    last_export: string;
    events_exported_today: number;
  }>>> {
    return apiClient.get('/audit/siem/configs');
  }

  /**
   * Export logs to SIEM
   */
  async exportToSIEM(configId: string, params?: {
    start_date?: string;
    end_date?: string;
    event_types?: string[];
    batch_size?: number;
  }): Promise<ApiResponse<{
    export_id: string;
    status: 'processing' | 'completed' | 'failed';
    events_exported: number;
    export_started: string;
    estimated_completion?: string;
  }>> {
    return apiClient.post(`/audit/siem/export/${configId}`, params);
  }

  /**
   * Replay events for investigation
   */
  async replayEvents(replayParams: {
    event_ids?: string[];
    time_range?: {
      start: string;
      end: string;
    };
    event_filters?: {
      event_types?: string[];
      user_ids?: string[];
      resource_types?: string[];
    };
    replay_speed?: number; // 1.0 = real-time, 0.5 = half-speed, 2.0 = double-speed
    output_format?: 'json' | 'timeline' | 'graph';
  }): Promise<ApiResponse<{
    replay_id: string;
    status: 'processing' | 'completed';
    events_count: number;
    timeline_data?: any[];
    replay_summary: {
      duration_minutes: number;
      unique_users: number;
      resource_types: string[];
      security_events: number;
    };
  }>> {
    return apiClient.post('/audit/replay/events', replayParams);
  }

  /**
   * Get security event summaries
   */
  async getSecurityEventSummary(params?: {
    period?: 'hour' | 'day' | 'week' | 'month';
    event_types?: string[];
  }): Promise<ApiResponse<{
    summary_period: string;
    total_events: number;
    security_events: number;
    failed_logins: number;
    unauthorized_access_attempts: number;
    phi_access_violations: number;
    high_severity_events: number;
    trending_threats: Array<{
      threat_type: string;
      count: number;
      severity: string;
      first_seen: string;
      last_seen: string;
    }>;
  }>> {
    return apiClient.get('/audit/security/summary', params);
  }

  /**
   * Get audit log retention policies
   */
  async getRetentionPolicies(): Promise<ApiResponse<Array<{
    id: string;
    name: string;
    event_types: string[];
    retention_days: number;
    archive_after_days: number;
    encryption_required: boolean;
    compliance_requirement: string;
    status: 'active' | 'inactive';
  }>>> {
    return apiClient.get('/audit/retention/policies');
  }

  /**
   * Update retention policy
   */
  async updateRetentionPolicy(policyId: string, policyData: {
    name?: string;
    event_types?: string[];
    retention_days?: number;
    archive_after_days?: number;
    encryption_required?: boolean;
  }): Promise<ApiResponse> {
    return apiClient.put(`/audit/retention/policies/${policyId}`, policyData);
  }

  /**
   * Get compliance dashboard data
   */
  async getComplianceDashboard(): Promise<ApiResponse<{
    overall_compliance_score: number;
    soc2_compliance: {
      status: 'compliant' | 'non_compliant' | 'pending';
      score: number;
      last_assessment: string;
      findings: number;
    };
    hipaa_compliance: {
      status: 'compliant' | 'non_compliant' | 'pending';
      score: number;
      phi_access_events: number;
      consent_violations: number;
    };
    audit_metrics: {
      logs_per_day: number;
      integrity_check_success_rate: number;
      siem_export_success_rate: number;
      average_response_time: number;
    };
    recent_violations: Array<{
      id: string;
      type: string;
      severity: string;
      description: string;
      timestamp: string;
    }>;
  }>> {
    return apiClient.get('/audit/compliance/dashboard');
  }

  /**
   * Log an audit event (for SOC2 compliance)
   */
  async logEvent(event: {
    event_type: string;
    severity: string;
    user_id: string;
    resource_type: string;
    resource_id: string;
    action: string;
    outcome: string;
    timestamp: string;
    details: any;
    ip_address: string;
    user_agent: string;
  }): Promise<void> {
    try {
      // In production, this would call the backend audit API
      console.log('Audit Event Logged:', event);
      
      // Mock API call for development
      await new Promise(resolve => setTimeout(resolve, 100));
    } catch (error) {
      console.error('Failed to log audit event:', error);
      throw error;
    }
  }
}

export const auditService = new AuditService();