import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Avatar,
  LinearProgress,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  Paper,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Shield as SecurityIcon,
  CloudSync as CloudSyncIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Shield as ShieldIcon,
  AdminPanelSettings as AdminIcon,
} from '@mui/icons-material';

import { useAppDispatch, useAppSelector } from '@/store';
import { showSnackbar } from '@/store/slices/uiSlice';
import { authService, patientService, irisService, auditService, dashboardService } from '@/services';
import LoadingCard from '@/components/common/LoadingCard';
import MetricCard from '@/components/dashboard/MetricCard';
import SystemHealthCard from '@/components/dashboard/SystemHealthCard';
import RecentActivityCard from '@/components/dashboard/RecentActivityCard';
import EnhancedActivityCard from '@/components/dashboard/EnhancedActivityCard';
import ComplianceOverviewCard from '@/components/dashboard/ComplianceOverviewCard';
import QuickActionsCard from '@/components/dashboard/QuickActionsCard';
import AnalyticsDashboard from '@/components/analytics/AnalyticsDashboard';
import MetricsChart from '@/components/charts/MetricsChart';
import HealthcareMetrics from '@/components/charts/HealthcareMetrics';

// ============================================
// DASHBOARD DATA TYPES
// ============================================

interface DashboardMetrics {
  totalPatients: number;
  activeUsers: number;
  apiRequestsToday: number;
  complianceScore: number;
  systemUptime: number;
  recentActivities: ActivityItem[];
  enhancedActivities: EnhancedActivityItem[];
  securitySummary: SecuritySummary;
  systemHealth: SystemHealthData;
  irisStatus: IRISStatusData;
}

interface SecuritySummary {
  total_events: number;
  security_events: number;
  phi_events: number;
  critical_events: number;
  failed_logins: number;
  phi_access_count: number;
  admin_actions: number;
  time_range_hours: number;
}

interface EnhancedActivityItem {
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
}

interface ActivityItem {
  id: string;
  type: 'patient_created' | 'user_login' | 'sync_completed' | 'audit_event' | 'phi_access';
  description: string;
  timestamp: string;
  user?: string;
  severity?: 'info' | 'warning' | 'error' | 'success';
}

interface SystemHealthData {
  overall: 'healthy' | 'degraded' | 'unhealthy';
  api: 'healthy' | 'degraded' | 'unhealthy';
  database: 'healthy' | 'degraded' | 'unhealthy';
  redis: 'healthy' | 'degraded' | 'unhealthy';
  eventBus: 'healthy' | 'degraded' | 'unhealthy';
}

interface IRISStatusData {
  overall: 'healthy' | 'degraded' | 'unhealthy';
  totalEndpoints: number;
  healthyEndpoints: number;
  avgResponseTime: number;
  syncOperationsToday: number;
  successRate: number;
}

// ============================================
// DASHBOARD PAGE CONTENT COMPONENT
// ============================================

const DashboardPageContent: React.FC = () => {
  const dispatch = useAppDispatch();
  const user = useAppSelector((state) => state.auth.user);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardMetrics | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Load dashboard data using the new bulk API
  const loadDashboardData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      // Use the new dashboard bulk API for optimized data fetching
      const bulkResponse = await dashboardService.bulkRefresh({
        include_stats: true,
        include_activities: true,
        include_alerts: true,
        include_health: true,
        activities_config: {
          limit: 15,
          time_range_hours: 24,
        },
        alerts_config: {
          time_range_hours: 24,
        },
        force_refresh: isRefresh,
      });

      if (bulkResponse.error) {
        throw new Error(bulkResponse.error);
      }

      const bulkData = bulkResponse.data;
      if (!bulkData) {
        throw new Error('No data received from dashboard API');
      }
      
      

      // Transform the new API response to match the existing interface
      const transformedDashboardData: DashboardMetrics = {
        totalPatients: bulkData.stats?.total_patients || 0,
        activeUsers: bulkData.stats?.active_users || 0,
        apiRequestsToday: bulkData.stats?.api_requests_today || 0,
        complianceScore: bulkData.stats?.compliance_score || 0,
        systemUptime: bulkData.stats?.system_uptime || 0,
        
        // Transform activities to match the old format
        recentActivities: bulkData.activities?.activities?.slice(0, 5)?.map(activity => ({
          id: activity.id,
          type: activity.type as 'patient_created' | 'user_login' | 'sync_completed' | 'audit_event' | 'phi_access',
          description: activity.description,
          timestamp: activity.timestamp,
          user: activity.user,
          severity: activity.severity === 'critical' || activity.severity === 'high' ? 'error' :
                   activity.severity === 'medium' ? 'warning' :
                   activity.severity === 'low' ? 'info' : 'success',
        })) || [],

        // Enhanced activities - FIXED: map backend DashboardActivity fields correctly
        enhancedActivities: bulkData.activities?.activities?.map(activity => {
          // Map common audit event titles to proper types
          const typeMapping: Record<string, string> = {
            'User Login': 'user_login',
            'User Login Failed': 'user_login_failed', 
            'User Created': 'user_created',
            'User Updated': 'user_updated',
            'PHI Accessed': 'phi_accessed',
            'Patient Created': 'patient_created',
            'Patient Updated': 'patient_updated',
            'Security Violation': 'security_violation',
            'Config Changed': 'config_changed',
            'System Error': 'system_error'
          };
          
          const mappedType = typeMapping[activity.title] || 
                           activity.title?.toLowerCase().replace(/\s+/g, '_') || 
                           'system_event';
          
          return {
            id: activity.id,
            type: mappedType,
            category: activity.category,
            title: activity.title,
            description: activity.description,
            timestamp: activity.timestamp,
            user: activity.user_name, // Backend field is user_name not user
            userId: activity.user_id,
            severity: activity.severity,
            ipAddress: undefined, // Backend doesn't provide this yet
            userAgent: undefined, // Backend doesn't provide this yet  
            resourceId: activity.details?.resource_id,
            resourceType: activity.details?.resource_type,
            metadata: activity.details || {},
            complianceFlags: [], // Backend doesn't provide this yet
          };
        }) || [],

        // Transform security summary - FIXED: map backend field names to frontend expectations
        securitySummary: {
          total_events: bulkData.stats?.security_summary?.total_audit_events_24h || 0,
          security_events: bulkData.stats?.security_summary?.security_events_today || 0,
          phi_events: bulkData.stats?.security_summary?.phi_access_events || 0,
          critical_events: bulkData.stats?.security_summary?.critical_alerts || 0,
          failed_logins: bulkData.stats?.security_summary?.failed_logins_24h || 0,
          phi_access_count: bulkData.stats?.security_summary?.phi_access_events || 0,
          admin_actions: bulkData.stats?.security_summary?.admin_actions || 0,
          time_range_hours: 24,
        },

        // Transform system health
        systemHealth: {
          overall: bulkData.health?.status || 'healthy',
          api: bulkData.health?.services?.database?.status || 'healthy',
          database: bulkData.health?.services?.database?.status || 'healthy',
          redis: bulkData.health?.services?.redis?.status || 'healthy',
          eventBus: bulkData.health?.services?.event_bus?.status || 'healthy',
        },

        // Transform IRIS status - FIXED: map backend field names correctly
        irisStatus: {
          overall: bulkData.stats?.iris_integration?.status || 'healthy',
          totalEndpoints: bulkData.stats?.iris_integration?.endpoints_total || 0,
          healthyEndpoints: bulkData.stats?.iris_integration?.endpoints_healthy || 0,
          avgResponseTime: bulkData.stats?.iris_integration?.avg_response_time || 0,
          syncOperationsToday: bulkData.stats?.iris_integration?.syncs_today || 0,
          successRate: bulkData.stats?.iris_integration?.success_rate || 98.7,
        },
      };

      
      setDashboardData(transformedDashboardData);
      setLastUpdated(new Date());
      
      if (isRefresh) {
        dispatch(showSnackbar({
          message: `Dashboard refreshed successfully (${bulkData.metadata.generation_time_ms}ms)`,
          severity: 'success',
        }));
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      
      // Fallback to individual API calls if bulk API fails
      try {
        console.log('Falling back to individual API calls...');
        await loadDashboardDataFallback(isRefresh);
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
        dispatch(showSnackbar({
          message: 'Failed to load dashboard data',
          severity: 'error',
        }));
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Fallback method using individual API calls (original implementation)
  const loadDashboardDataFallback = async (isRefresh = false) => {
    // Fetch data from multiple endpoints in parallel
    const [
      patientsResponse,
      irisHealthResponse,
      auditStatsResponse,
      recentActivitiesResponse,
      enhancedActivitiesResponse,
      complianceResponse,
    ] = await Promise.all([
      patientService.getPatients({ limit: 1 }), // Just get count
      irisService.getHealthSummary(),
      auditService.getStats(),
      auditService.getRecentActivities(5), // Get basic recent activities
      auditService.getEnhancedActivities({ limit: 15, hours: 24 }), // Get SOC2 activities
      patientService.getComplianceSummary(),
    ]);

    // Process enhanced activities data
    const enhancedData = enhancedActivitiesResponse.data || {};
    const enhancedActivities = enhancedData.activities || [];
    const securitySummary = enhancedData.summary || {
      total_events: 0,
      security_events: 0,
      phi_events: 0,
      critical_events: 0,
      failed_logins: 0,
      phi_access_count: 0,
      admin_actions: 0,
      time_range_hours: 24,
    };

    // Mock some additional data for demo purposes
    const mockDashboardData: DashboardMetrics = {
      totalPatients: patientsResponse.data?.total || 0,
      activeUsers: 42, // Would come from user service
      apiRequestsToday: auditStatsResponse.data?.logs_today || securitySummary.total_events,
      complianceScore: 98.5,
      systemUptime: 99.9,
      recentActivities: recentActivitiesResponse.data?.activities || [
        // Fallback to mock data if real data unavailable
        {
          id: '1',
          type: 'patient_created',
          description: 'New patient record created (fallback)',
          timestamp: new Date(Date.now() - Math.floor(Math.random() * 30 + 5) * 60000).toISOString(),
          user: 'Dr. Smith',
          severity: 'success',
        },
        {
          id: '2',
          type: 'sync_completed',
          description: 'IRIS sync completed successfully (fallback)',
          timestamp: new Date(Date.now() - Math.floor(Math.random() * 60 + 30) * 60000).toISOString(),
          severity: 'info',
        },
      ],
      enhancedActivities: enhancedActivities,
      securitySummary: securitySummary,
      systemHealth: {
        overall: 'healthy',
        api: 'healthy',
        database: 'healthy',
        redis: 'healthy',
        eventBus: 'healthy',
      },
      irisStatus: {
        overall: irisHealthResponse.data?.overall_status || 'healthy',
        totalEndpoints: irisHealthResponse.data?.total_endpoints || 0,
        healthyEndpoints: irisHealthResponse.data?.healthy_endpoints || 0,
        avgResponseTime: irisHealthResponse.data?.avg_response_time || 0,
        syncOperationsToday: 23, // Would come from IRIS service
        successRate: 98.7,
      },
    };

    setDashboardData(mockDashboardData);
    setLastUpdated(new Date());
    
    if (isRefresh) {
      dispatch(showSnackbar({
        message: 'Dashboard data refreshed successfully (fallback mode)',
        severity: 'warning',
      }));
    }
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    loadDashboardData();
    
    const interval = setInterval(() => {
      loadDashboardData(true);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    loadDashboardData(true);
  };

  if (loading) {
    return (
      <Box>
        <Grid container spacing={3}>
          {[...Array(6)].map((_, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <LoadingCard height={120} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (!dashboardData) {
    return (
      <Alert severity="error">
        Failed to load dashboard data. Please try refreshing the page.
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%', maxWidth: '1200px', py: 0 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={600} gutterBottom>
            Welcome back, {user?.username || 'User'}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Healthcare AI Platform Dashboard - Last updated: {lastUpdated.toLocaleTimeString()}
          </Typography>
        </Box>
        <Tooltip title="Refresh dashboard data">
          <IconButton 
            onClick={handleRefresh} 
            disabled={refreshing}
            sx={{ 
              bgcolor: 'primary.main', 
              color: 'white',
              '&:hover': { bgcolor: 'primary.dark' }
            }}
          >
            <RefreshIcon sx={{ 
              animation: refreshing ? 'spin 1s linear infinite' : 'none',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' },
              }
            }} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Patients"
            value={dashboardData.totalPatients.toLocaleString()}
            icon={<PeopleIcon />}
            color="primary"
            change="+12 this week"
            changeType="positive"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="System Uptime"
            value={`${dashboardData.systemUptime}%`}
            icon={<CheckCircleIcon />}
            color="success"
            change="Last 30 days"
            changeType="neutral"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Compliance Score"
            value={`${dashboardData.complianceScore}%`}
            icon={<SecurityIcon />}
            color="info"
            change="SOC2 & HIPAA"
            changeType="positive"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Security Events Today"
            value={dashboardData.securitySummary.security_events.toLocaleString()}
            icon={<SecurityIcon />}
            color={dashboardData.securitySummary.critical_events > 0 ? "error" : "success"}
            change={`${dashboardData.securitySummary.critical_events} critical`}
            changeType={dashboardData.securitySummary.critical_events > 0 ? "negative" : "positive"}
          />
        </Grid>
      </Grid>

      {/* SOC2 Security Metrics Row */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="PHI Access Events"
            value={dashboardData.securitySummary.phi_access_count.toLocaleString()}
            icon={<ShieldIcon />}
            color="warning"
            change="HIPAA monitored"
            changeType="neutral"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Failed Login Attempts"
            value={dashboardData.securitySummary.failed_logins.toLocaleString()}
            icon={<WarningIcon />}
            color={dashboardData.securitySummary.failed_logins > 5 ? "error" : "success"}
            change="Last 24 hours"
            changeType={dashboardData.securitySummary.failed_logins > 5 ? "negative" : "positive"}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Admin Actions"
            value={dashboardData.securitySummary.admin_actions.toLocaleString()}
            icon={<AdminIcon />}
            color="info"
            change="SOC2 tracked"
            changeType="neutral"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Audit Events"
            value={dashboardData.securitySummary.total_events.toLocaleString()}
            icon={<AssessmentIcon />}
            color="primary"
            change={`${dashboardData.securitySummary.time_range_hours}h period`}
            changeType="neutral"
          />
        </Grid>
      </Grid>

      {/* System Health & IRIS Status */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6}>
          <SystemHealthCard 
            title="System Health"
            healthData={dashboardData.systemHealth}
            refreshing={refreshing}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <CloudSyncIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    IRIS Integration Status
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    External API connectivity
                  </Typography>
                </Box>
              </Box>
              
              <Box mb={2}>
                <Chip
                  label={dashboardData.irisStatus.overall.toUpperCase()}
                  color={
                    dashboardData.irisStatus.overall === 'healthy' ? 'success' :
                    dashboardData.irisStatus.overall === 'degraded' ? 'warning' : 'error'
                  }
                  size="small"
                />
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Endpoints
                  </Typography>
                  <Typography variant="h6">
                    {dashboardData.irisStatus.healthyEndpoints}/{dashboardData.irisStatus.totalEndpoints}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Avg Response
                  </Typography>
                  <Typography variant="h6">
                    {dashboardData.irisStatus.avgResponseTime}ms
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Syncs Today
                  </Typography>
                  <Typography variant="h6">
                    {dashboardData.irisStatus.syncOperationsToday}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Success Rate
                  </Typography>
                  <Typography variant="h6">
                    {dashboardData.irisStatus.successRate}%
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Enhanced Security Activity & Quick Actions */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <EnhancedActivityCard 
            activities={dashboardData.enhancedActivities}
            loading={refreshing}
            maxItems={12}
            showFilters={true}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <QuickActionsCard />
        </Grid>
      </Grid>

      {/* Compliance Overview */}
      <Grid container spacing={3} mt={0}>
        <Grid item xs={12}>
          <ComplianceOverviewCard 
            complianceScore={dashboardData.complianceScore}
            loading={refreshing}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPageContent;