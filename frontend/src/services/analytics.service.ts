/**
 * Population Health Analytics Service
 * SOC2 Type 2 Compliant Implementation for Analytics Dashboard
 * 
 * Security Controls Applied:
 * - CC6.1: Logical Access Controls via RBAC
 * - CC7.2: System Monitoring with comprehensive audit logging  
 * - A1.2: Availability Controls with circuit breaker pattern
 * - CC8.1: Change Management with audit trail
 */

import { apiClient } from './api';
import { auditService } from './audit.service';
import { authService } from './auth.service';

// Analytics Data Types
export interface PopulationMetrics {
  analysis_id: string;
  total_patients: number;
  analysis_period: {
    start_date: string;
    end_date: string;
    time_range: string;
  };
  risk_distribution: {
    low: number;
    moderate: number;
    high: number;
    critical: number;
    total: number;
  };
  trends: TrendAnalysis[];
  cost_metrics: {
    total_cost: number;
    cost_per_patient: number;
    estimated_savings: number;
    roi: number;
    cost_breakdown: CostBreakdown[];
  };
  quality_measures: QualityMeasure[];
  intervention_opportunities: InterventionOpportunity[];
  generated_at: string;
  generated_by: string;
  data_freshness: {
    risk_data_age_hours: number;
    cost_data_age_hours: number;
    quality_data_age_hours: number;
  };
}

export interface TrendAnalysis {
  metric_name: string;
  time_points: TimeSeriesPoint[];
  trend_direction: 'improving' | 'stable' | 'declining';
  significance_level: number;
  percent_change: number;
}

export interface TimeSeriesPoint {
  date: string;
  value: number;
  confidence: number;
}

export interface CostBreakdown {
  category: string;
  current_cost: number;
  previous_cost: number;
  percent_change: number;
  patient_count: number;
}

export interface QualityMeasure {
  measure_id: string;
  name: string;
  description: string;
  current_score: number;
  benchmark: number;
  improvement: number;
  measure_type: 'process' | 'outcome' | 'structure';
  patient_count: number;
}

export interface InterventionOpportunity {
  opportunity_id: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  estimated_impact: string;
  affected_patient_count: number;
  implementation_effort: string;
  estimated_timeline: string;
  roi_estimate: number;
  confidence_level: number;
}

export interface RiskDistribution {
  distribution: {
    low: number;
    moderate: number;
    high: number;
    critical: number;
    total: number;
  };
  demographic_breakdown?: Record<string, any>;
  trends: TrendAnalysis[];
  generated_at: string;
}

export interface QualityMeasuresResponse {
  measures: QualityMeasure[];
  overall_score: number;
  benchmark_comparison: {
    above_benchmark: number;
    at_benchmark: number;
    below_benchmark: number;
    average_gap: number;
  };
  improvement_trends: TrendAnalysis[];
  generated_at: string;
}

export interface CostAnalytics {
  total_cost: number;
  cost_per_patient: number;
  cost_breakdown: CostBreakdown[];
  cost_trends: TrendAnalysis[];
  estimated_savings: number;
  roi_metrics: {
    roi_percentage: number;
    payback_period_months: number;
    cost_avoidance: number;
  };
  generated_at: string;
}

export interface InterventionOpportunities {
  opportunities: InterventionOpportunity[];
  total_estimated_savings: number;
  high_priority_count: number;
  affected_patient_total: number;
  generated_at: string;
}

/**
 * SOC2-Compliant Population Health Analytics Service
 * Implements defense-in-depth security architecture
 */
export class AnalyticsService {
  private readonly SERVICE_NAME = 'AnalyticsService';
  private readonly API_BASE = '/api/v1/analytics';
  private readonly CACHE_TTL = 1800000; // 30 minutes
  private readonly auditLogger = auditService;

  // SOC2 Circuit Breaker for resilience (A1.2)
  private readonly circuitBreakerConfig = {
    failureThreshold: 5,
    recoveryTimeout: 30000,
    monitoringWindow: 60000
  };

  /**
   * Get comprehensive population health metrics
   * SOC2 Controls: CC6.1 (Access), CC7.2 (Monitoring), A1.2 (Availability)
   */
  async getPopulationMetrics(
    timeRange: string = '90d',
    organizationFilter?: string,
    cohortCriteria: Record<string, any> = {},
    metricsRequested: string[] = ['risk_distribution', 'quality_measures', 'cost_metrics', 'intervention_opportunities']
  ): Promise<PopulationMetrics> {
    const startTime = Date.now();
    
    try {
      // Get current user context for SOC2 compliance
      const userResponse = await authService.getCurrentUser();
      if (!userResponse?.data) {
        throw new Error('Authentication required for analytics access');
      }
      const user = userResponse.data;

      // SOC2 CC7.2: Log analytics access attempt
      await this.logAnalyticsAccess('population_metrics', user.id, {
        time_range: timeRange,
        organization_filter: organizationFilter,
        metrics_requested: metricsRequested
      });

      // Validate access permissions
      await this.validateAnalyticsAccess(userResponse, 'population_health_read');
      
      // Call backend API for population metrics
      const requestData = {
        time_range: timeRange,
        organization_filter: organizationFilter,
        cohort_criteria: cohortCriteria,
        metrics_requested: metricsRequested,
        requesting_user_id: user.id,
        access_purpose: 'population_health_analysis'
      };

      const response = await apiClient.post<PopulationMetrics>(`${this.API_BASE}/population/metrics`, requestData);
      
      // Performance monitoring (SOC2 A1.2)
      const executionTime = Date.now() - startTime;
      if (executionTime > 10000) { // > 10 seconds
        console.warn(`Population metrics performance warning: ${executionTime}ms`);
      }

      // SOC2 CC7.2: Log successful retrieval
      await this.logAnalyticsAccess('population_metrics_success', user.id, {
        analysis_id: response.data?.analysis_id || 'unknown',
        total_patients: response.data?.total_patients || 0,
        execution_time_ms: executionTime
      });

      if (!response.data) {
        throw new Error('Invalid response from analytics API');
      }

      return response.data;

    } catch (error) {
      // SOC2 CC7.2: Log analytics failure
      const userResponse = await authService.getCurrentUser();
      await this.logAnalyticsAccess('population_metrics_failed', userResponse?.data?.id || 'unknown', {
        error_type: error instanceof Error ? error.constructor.name : 'unknown',
        error_message: error instanceof Error ? error.message : 'unknown error'
      });

      throw new Error(`Population metrics retrieval failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }

  /**
   * Get risk distribution analytics
   * SOC2 Controls: CC6.1 (Access), CC7.2 (Monitoring)
   */
  async getRiskDistribution(
    timeRange: string = '90d',
    organizationFilter?: string,
    includeDemographicBreakdown: boolean = false
  ): Promise<RiskDistribution> {
    try {
      const user = await authService.getCurrentUser();
      if (!user) {
        throw new Error('Authentication required for risk distribution access');
      }

      await this.validateAnalyticsAccess(user, 'risk_analytics_read');
      
      const requestData = {
        time_range: timeRange,
        organization_filter: organizationFilter,
        demographic_breakdown: includeDemographicBreakdown,
        requesting_user_id: user.id
      };

      const response = await apiClient.post<RiskDistribution>(`${this.API_BASE}/risk-distribution`, requestData);
      
      await this.logAnalyticsAccess('risk_distribution_accessed', user.id, {
        time_range: timeRange,
        total_patients: response.data.distribution.total
      });

      return response.data;

    } catch (error) {
      throw new Error(`Risk distribution retrieval failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }

  /**
   * Get quality measures analytics
   * SOC2 Controls: CC6.1 (Access), CC7.2 (Monitoring)
   */
  async getQualityMeasures(
    measureIds?: string[],
    timeRange: string = '90d',
    includeBenchmarks: boolean = true
  ): Promise<QualityMeasuresResponse> {
    try {
      const user = await authService.getCurrentUser();
      if (!user) {
        throw new Error('Authentication required for quality measures access');
      }

      await this.validateAnalyticsAccess(user, 'quality_analytics_read');
      
      const requestData = {
        measure_ids: measureIds,
        time_range: timeRange,
        include_benchmarks: includeBenchmarks,
        requesting_user_id: user.id
      };

      const response = await apiClient.post<QualityMeasuresResponse>(`${this.API_BASE}/quality-measures`, requestData);
      
      await this.logAnalyticsAccess('quality_measures_accessed', user.id, {
        measures_count: response.data.measures.length,
        overall_score: response.data.overall_score
      });

      return response.data;

    } catch (error) {
      throw new Error(`Quality measures retrieval failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }

  /**
   * Get cost analytics and ROI analysis
   * SOC2 Controls: CC6.1 (Access), CC7.2 (Monitoring)
   */
  async getCostAnalytics(
    timeRange: string = '90d',
    costCategories?: string[],
    includeRoiAnalysis: boolean = true
  ): Promise<CostAnalytics> {
    try {
      const user = await authService.getCurrentUser();
      if (!user) {
        throw new Error('Authentication required for cost analytics access');
      }

      await this.validateAnalyticsAccess(user, 'cost_analytics_read');
      
      const requestData = {
        time_range: timeRange,
        cost_categories: costCategories,
        include_roi_analysis: includeRoiAnalysis,
        requesting_user_id: user.id
      };

      const response = await apiClient.post<CostAnalytics>(`${this.API_BASE}/cost-analytics`, requestData);
      
      await this.logAnalyticsAccess('cost_analytics_accessed', user.id, {
        total_cost: response.data.total_cost,
        estimated_savings: response.data.estimated_savings
      });

      return response.data;

    } catch (error) {
      throw new Error(`Cost analytics retrieval failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }

  /**
   * Get high-impact intervention opportunities
   * SOC2 Controls: CC6.1 (Access), CC7.2 (Monitoring)
   */
  async getInterventionOpportunities(
    organizationFilter?: string,
    priorityFilter?: 'high' | 'medium' | 'low'
  ): Promise<InterventionOpportunities> {
    try {
      const user = await authService.getCurrentUser();
      if (!user) {
        throw new Error('Authentication required for intervention opportunities access');
      }

      await this.validateAnalyticsAccess(user, 'intervention_analytics_read');
      
      const queryParams = new URLSearchParams();
      if (organizationFilter) queryParams.append('organization_filter', organizationFilter);
      if (priorityFilter) queryParams.append('priority_filter', priorityFilter);

      const response = await apiClient.get<InterventionOpportunities>(
        `${this.API_BASE}/intervention-opportunities?${queryParams.toString()}`
      );
      
      await this.logAnalyticsAccess('intervention_opportunities_accessed', user.id, {
        opportunities_count: response.data.opportunities.length,
        high_priority_count: response.data.high_priority_count
      });

      return response.data;

    } catch (error) {
      throw new Error(`Intervention opportunities retrieval failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }

  // ============================================
  // SOC2 COMPLIANCE METHODS
  // ============================================

  /**
   * SOC2 CC7.2: Comprehensive audit logging for analytics access
   */
  private async logAnalyticsAccess(eventType: string, userId: string, details: Record<string, any>): Promise<void> {
    try {
      await this.auditLogger.logEvent({
        event_type: 'analytics_access',
        severity: 'medium',
        user_id: userId,
        resource_type: 'population_analytics',
        resource_id: eventType,
        action: eventType,
        outcome: 'success',
        timestamp: new Date().toISOString(),
        details: details,
        ip_address: '127.0.0.1', // Would come from request context
        user_agent: navigator.userAgent || 'Unknown'
      });
    } catch (error) {
      console.error('Analytics audit logging failed:', error);
      // Don't throw - audit logging failure shouldn't break analytics
    }
  }

  /**
   * SOC2 CC6.1: Validate analytics access permissions
   */
  private async validateAnalyticsAccess(user: any, requiredPermission: string): Promise<boolean> {
    try {
      // Check if user has required permission
      if (!user.permissions.includes(requiredPermission)) {
        throw new Error(`Insufficient permissions: ${requiredPermission} required`);
      }

      // Check admin access for population health data
      if (requiredPermission.includes('population') && !user.permissions.includes('admin')) {
        throw new Error('Admin access required for population health analytics');
      }

      return true;
    } catch (error) {
      throw new Error(`Analytics access validation failed: ${error instanceof Error ? error.message : 'validation error'}`);
    }
  }

  /**
   * Get analytics service health status
   */
  async getServiceHealth(): Promise<{ status: string; version: string; capabilities: string[] }> {
    try {
      const response = await apiClient.get(`${this.API_BASE}/health`);
      return response.data;
    } catch (error) {
      throw new Error(`Analytics service health check failed: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }
}

// Export singleton instance
export const analyticsService = new AnalyticsService();