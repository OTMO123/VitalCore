import { apiClient } from './api';
import { ApiResponse } from '@/types';

// ============================================
// DASHBOARD SERVICE TYPES
// ============================================

export interface DashboardStats {
  total_patients: number;
  active_users: number;
  api_requests_today: number;
  compliance_score: number;
  system_uptime: number;
  recent_sync_operations: number;
  failed_operations_24h: number;
  encryption_events_24h: number;
  phi_access_events_24h: number;
  security_summary: {
    security_events_today: number;
    failed_logins_24h: number;
    phi_access_events: number;
    admin_actions: number;
    total_audit_events_24h: number;
    critical_alerts: number;
    compliance_score: number;
  };
  metadata: {
    last_updated: string;
    cache_hit: boolean;
    generation_time_ms: number;
  };
}

export interface DashboardActivity {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: 'security' | 'phi' | 'admin' | 'system' | 'compliance';
  timestamp: string;
  user_id?: string;
  user_name?: string;
  details?: Record<string, any>;
  status?: string;
}

export interface DashboardActivities {
  activities: DashboardActivity[];
  total_count: number;
  categories: Record<string, number>;
  severity_counts: Record<string, number>;
  last_updated: string;
}

export interface DashboardAlert {
  id: string;
  type: 'security' | 'compliance' | 'system' | 'performance' | 'data_quality';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  timestamp: string;
  status: 'active' | 'acknowledged' | 'resolved';
  affected_resource?: string;
  recommended_action?: string;
  metadata?: Record<string, any>;
}

export interface DashboardAlerts {
  alerts: DashboardAlert[];
  total_count: number;
  critical_count: number;
  high_count: number;
  metadata: {
    last_updated: string;
    cache_hit: boolean;
    generation_time_ms: number;
  };
}

export interface DashboardHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    database: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      response_time_ms?: number;
      details?: string;
    };
    redis: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      response_time_ms?: number;
      details?: string;
    };
    event_bus: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      active_handlers?: number;
      details?: string;
    };
    audit_service: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      logs_processed_today?: number;
      details?: string;
    };
    iris_integration: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      healthy_endpoints?: number;
      total_endpoints?: number;
      details?: string;
    };
  };
  metadata: {
    check_timestamp: string;
    generation_time_ms: number;
  };
}

export interface BulkDashboardResponse {
  stats?: DashboardStats;
  activities?: DashboardActivities;
  alerts?: DashboardAlerts;
  health?: DashboardHealth;
  metadata: {
    request_id: string;
    generation_time_ms: number;
    cache_performance: {
      stats_cache_hit: boolean;
      activities_cache_hit: boolean;
      alerts_cache_hit: boolean;
      health_cache_hit: boolean;
    };
    data_freshness: {
      stats_age_seconds: number;
      activities_age_seconds: number;
      alerts_age_seconds: number;
      health_age_seconds: number;
    };
  };
}

export interface BulkRefreshRequest {
  include_stats?: boolean;
  include_activities?: boolean;
  include_alerts?: boolean;
  include_health?: boolean;
  activities_config?: {
    limit?: number;
    categories?: string[];
    time_range_hours?: number;
  };
  alerts_config?: {
    time_range_hours?: number;
  };
  force_refresh?: boolean;
}

export interface PerformanceMetrics {
  total_requests: number;
  avg_response_time_ms: number;
  cache_hit_rate: number;
  error_rate: number;
  requests_per_minute: number;
  peak_response_time_ms: number;
  memory_usage_mb: number;
  active_connections: number;
  background_tasks_pending: number;
  metadata: {
    measurement_period_hours: number;
    last_reset: string;
  };
}

// ============================================
// DASHBOARD SERVICE CLASS
// ============================================

export class DashboardService {
  /**
   * Get all dashboard data in a single optimized API call
   */
  async bulkRefresh(request: BulkRefreshRequest = {}): Promise<ApiResponse<BulkDashboardResponse>> {
    const defaultRequest: BulkRefreshRequest = {
      include_stats: true,
      include_activities: true,
      include_alerts: true,
      include_health: true,
      activities_config: {
        limit: 50,
        time_range_hours: 24,
      },
      alerts_config: {
        time_range_hours: 24,
      },
      force_refresh: false,
      ...request,
    };

    return apiClient.post('/dashboard/refresh', defaultRequest);
  }

  /**
   * Get core dashboard statistics only
   */
  async getStats(): Promise<ApiResponse<DashboardStats>> {
    return apiClient.get('/dashboard/stats');
  }

  /**
   * Get recent dashboard activities
   */
  async getActivities(params?: {
    limit?: number;
    categories?: string[];
    time_range_hours?: number;
  }): Promise<ApiResponse<DashboardActivities>> {
    const queryParams = new URLSearchParams();
    
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    
    if (params?.categories && params.categories.length > 0) {
      queryParams.append('categories', params.categories.join(','));
    }
    
    if (params?.time_range_hours) {
      queryParams.append('time_range_hours', params.time_range_hours.toString());
    }

    const queryString = queryParams.toString();
    const url = `/dashboard/activities${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.get(url);
  }

  /**
   * Get dashboard alerts
   */
  async getAlerts(params?: {
    time_range_hours?: number;
  }): Promise<ApiResponse<DashboardAlerts>> {
    const queryParams = new URLSearchParams();
    
    if (params?.time_range_hours) {
      queryParams.append('time_range_hours', params.time_range_hours.toString());
    }

    const queryString = queryParams.toString();
    const url = `/dashboard/alerts${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.get(url);
  }

  /**
   * Get dashboard service health and performance metrics
   */
  async getHealth(): Promise<ApiResponse<DashboardHealth>> {
    return apiClient.get('/dashboard/health');
  }

  /**
   * Get dashboard performance metrics (admin only)
   */
  async getPerformanceMetrics(): Promise<ApiResponse<PerformanceMetrics>> {
    return apiClient.get('/dashboard/performance');
  }

  /**
   * Clear dashboard cache (admin only)
   */
  async clearCache(): Promise<ApiResponse<{
    message: string;
    keys_cleared: number;
  }>> {
    return apiClient.post('/dashboard/cache/clear');
  }

  /**
   * Get dashboard cache statistics (admin only)
   */
  async getCacheStats(): Promise<ApiResponse<{
    cache_enabled: boolean;
    cache_hits: number;
    cache_misses: number;
    total_requests: number;
    hit_rate_percentage: number;
    redis_memory_mb?: number;
    redis_connected: boolean;
  }>> {
    return apiClient.get('/dashboard/cache/stats');
  }

  // ============================================
  // CONVENIENCE METHODS
  // ============================================

  /**
   * Get dashboard data optimized for real-time updates
   */
  async getRealtimeData(): Promise<ApiResponse<BulkDashboardResponse>> {
    return this.bulkRefresh({
      include_stats: true,
      include_activities: true,
      include_alerts: true,
      include_health: true,
      activities_config: {
        limit: 20,
        categories: ['security', 'system', 'critical'],
        time_range_hours: 1,
      },
      alerts_config: {
        time_range_hours: 24,
      },
      force_refresh: true,
    });
  }

  /**
   * Get security-focused dashboard data
   */
  async getSecurityDashboard(): Promise<ApiResponse<BulkDashboardResponse>> {
    return this.bulkRefresh({
      include_stats: true,
      include_activities: true,
      include_alerts: true,
      include_health: false,
      activities_config: {
        limit: 100,
        categories: ['security', 'phi', 'compliance'],
        time_range_hours: 24,
      },
      alerts_config: {
        time_range_hours: 24,
      },
    });
  }

  /**
   * Get compliance-focused dashboard data
   */
  async getComplianceDashboard(): Promise<ApiResponse<BulkDashboardResponse>> {
    return this.bulkRefresh({
      include_stats: true,
      include_activities: true,
      include_alerts: true,
      include_health: false,
      activities_config: {
        limit: 50,
        categories: ['compliance', 'phi', 'audit'],
        time_range_hours: 168, // 7 days
      },
      alerts_config: {
        time_range_hours: 168, // 7 days
      },
    });
  }

  /**
   * Check if dashboard service is healthy
   */
  async isHealthy(): Promise<boolean> {
    try {
      const response = await this.getHealth();
      return response.data?.status === 'healthy';
    } catch (error) {
      console.error('Dashboard health check failed:', error);
      return false;
    }
  }
}

export const dashboardService = new DashboardService();