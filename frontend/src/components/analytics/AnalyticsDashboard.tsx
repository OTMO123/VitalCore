import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Analytics as AnalyticsIcon,
  GitBranch as Timeline, TimelineIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  Shield as SecurityIcon,
  HealthAndSafety as HealthIcon,
} from '@mui/icons-material';
import MetricsChart from '../charts/MetricsChart';
import HealthcareMetrics from '../charts/HealthcareMetrics';

interface KPIMetric {
  title: string;
  value: string | number;
  change: number;
  changeType: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

interface AnalyticsDashboardProps {
  timeRange?: '7d' | '30d' | '90d' | '1y';
  showRealTime?: boolean;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  timeRange: initialTimeRange = '30d',
  showRealTime = true,
}) => {
  const [timeRange, setTimeRange] = useState(initialTimeRange);
  const [viewMode, setViewMode] = useState<'summary' | 'detailed'>('summary');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['patients', 'compliance', 'performance']);

  // Mock KPI data
  const kpiMetrics: KPIMetric[] = [
    {
      title: 'Total Patients',
      value: '2,847',
      change: 12.5,
      changeType: 'increase',
      icon: <HealthIcon />,
      color: 'primary',
    },
    {
      title: 'PHI Access Events',
      value: '1,234',
      change: -5.2,
      changeType: 'decrease',
      icon: <SecurityIcon />,
      color: 'warning',
    },
    {
      title: 'FHIR Compliance',
      value: '94%',
      change: 2.1,
      changeType: 'increase',
      icon: <AssessmentIcon />,
      color: 'success',
    },
    {
      title: 'Avg Response Time',
      value: '145ms',
      change: -8.3,
      changeType: 'decrease',
      icon: <SpeedIcon />,
      color: 'success',
    },
    {
      title: 'IRIS Sync Success',
      value: '99.2%',
      change: 0.5,
      changeType: 'increase',
      icon: <TrendingUpIcon />,
      color: 'success',
    },
    {
      title: 'Active Sessions',
      value: '47',
      change: 15.7,
      changeType: 'increase',
      icon: <TimelineIcon />,
      color: 'primary',
    },
  ];

  // Mock chart data
  const realtimeData = [
    { time: '09:00', patients: 45, phiAccess: 12, apiCalls: 234 },
    { time: '10:00', patients: 52, phiAccess: 15, apiCalls: 267 },
    { time: '11:00', patients: 48, phiAccess: 18, apiCalls: 298 },
    { time: '12:00', patients: 67, phiAccess: 22, apiCalls: 345 },
    { time: '13:00', patients: 71, phiAccess: 19, apiCalls: 312 },
    { time: '14:00', patients: 58, phiAccess: 16, apiCalls: 289 },
    { time: '15:00', patients: 49, phiAccess: 14, apiCalls: 256 },
  ];

  const complianceData = [
    { name: 'HIPAA', value: 98, target: 95 },
    { name: 'SOC2', value: 96, target: 95 },
    { name: 'ISO 27001', value: 87, target: 90 },
    { name: 'FHIR R4', value: 94, target: 95 },
  ];

  const systemPerformanceData = [
    { metric: 'API Response Time', current: 145, baseline: 150, target: 100 },
    { metric: 'Database Query Time', current: 23, baseline: 25, target: 20 },
    { metric: 'PHI Encryption Time', current: 12, baseline: 15, target: 10 },
    { metric: 'IRIS Sync Time', current: 890, baseline: 950, target: 800 },
  ];

  const getTrendIcon = (changeType: string) => {
    switch (changeType) {
      case 'increase':
        return <TrendingUpIcon fontSize="small" />;
      case 'decrease':
        return <TrendingDownIcon fontSize="small" />;
      default:
        return null;
    }
  };

  const getTrendColor = (changeType: string, isPositive: boolean) => {
    if (changeType === 'neutral') return 'text.secondary';
    return (changeType === 'increase' && isPositive) || (changeType === 'decrease' && !isPositive)
      ? 'success.main'
      : 'error.main';
  };

  const KPICard: React.FC<{ metric: KPIMetric }> = ({ metric }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Box color={`${metric.color}.main`}>
              {metric.icon}
            </Box>
            <Typography variant="body2" color="text.secondary">
              {metric.title}
            </Typography>
          </Box>
          <Chip
            size="small"
            label={`${metric.change > 0 ? '+' : ''}${metric.change}%`}
            color={metric.changeType === 'increase' ? 'success' : metric.changeType === 'decrease' ? 'error' : 'default'}
            icon={getTrendIcon(metric.changeType)}
          />
        </Box>
        <Typography variant="h4" fontWeight={600} color={`${metric.color}.main`}>
          {metric.value}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          vs previous {timeRange}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Header Controls */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600}>
          Analytics Dashboard
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              label="Time Range"
            >
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
              <MenuItem value="1y">Last year</MenuItem>
            </Select>
          </FormControl>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(_, newMode) => newMode && setViewMode(newMode)}
            size="small"
          >
            <ToggleButton value="summary">Summary</ToggleButton>
            <ToggleButton value="detailed">Detailed</ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Box>

      {/* Real-time Status */}
      {showRealTime && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Box display="flex" alignItems="center" gap={1}>
            <AnalyticsIcon />
            <Typography variant="body2">
              Real-time analytics enabled • Last updated: {new Date().toLocaleTimeString()}
            </Typography>
          </Box>
        </Alert>
      )}

      {/* KPI Metrics Grid */}
      <Grid container spacing={3} mb={4}>
        {kpiMetrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={4} lg={2} key={index}>
            <KPICard metric={metric} />
          </Grid>
        ))}
      </Grid>

      {/* Charts Section */}
      {viewMode === 'summary' ? (
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} lg={8}>
            <MetricsChart
              data={realtimeData}
              type="area"
              title="Patient Activity (Real-time)"
              height={350}
              xAxisKey="time"
              yAxisKey="patients"
              showGrid={true}
            />
          </Grid>
          <Grid item xs={12} lg={4}>
            <MetricsChart
              data={complianceData}
              type="pie"
              title="Compliance Status"
              height={350}
              yAxisKey="value"
              showLegend={true}
            />
          </Grid>
        </Grid>
      ) : (
        <Box mb={4}>
          <HealthcareMetrics />
        </Box>
      )}

      {/* System Performance Metrics */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} mb={3}>
          System Performance Metrics
        </Typography>
        <Grid container spacing={3}>
          {systemPerformanceData.map((perf, index) => (
            <Grid item xs={12} md={6} lg={3} key={index}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {perf.metric}
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <Typography variant="h5" fontWeight={600}>
                      {perf.current}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ms
                    </Typography>
                    <Chip
                      size="small"
                      label={perf.current <= perf.target ? 'Good' : 'Needs Attention'}
                      color={perf.current <= perf.target ? 'success' : 'warning'}
                    />
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    Target: {perf.target}ms • Baseline: {perf.baseline}ms
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Additional Analytics */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title={
                <Typography variant="h6" fontWeight={600}>
                  Top PHI Access Events
                </Typography>
              }
            />
            <CardContent>
              <Box display="flex" flexDirection="column" gap={2}>
                {[
                  { user: 'Dr. Sarah Johnson', count: 45, time: '2h ago' },
                  { user: 'Nurse Williams', count: 32, time: '3h ago' },
                  { user: 'Admin User', count: 28, time: '4h ago' },
                  { user: 'Dr. Michael Chen', count: 21, time: '5h ago' },
                ].map((event, index) => (
                  <Box key={index} display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="body2" fontWeight={500}>
                        {event.user}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {event.time}
                      </Typography>
                    </Box>
                    <Chip
                      label={`${event.count} accesses`}
                      color="primary"
                      variant="outlined"
                      size="small"
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title={
                <Typography variant="h6" fontWeight={600}>
                  System Health Summary
                </Typography>
              }
            />
            <CardContent>
              <Box display="flex" flexDirection="column" gap={2}>
                {[
                  { service: 'IRIS API', status: 'Healthy', uptime: '99.9%' },
                  { service: 'Database', status: 'Healthy', uptime: '100%' },
                  { service: 'Redis Cache', status: 'Healthy', uptime: '99.8%' },
                  { service: 'Auth Service', status: 'Degraded', uptime: '97.2%' },
                ].map((service, index) => (
                  <Box key={index} display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="body2" fontWeight={500}>
                        {service.service}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Uptime: {service.uptime}
                      </Typography>
                    </Box>
                    <Chip
                      label={service.status}
                      color={service.status === 'Healthy' ? 'success' : 'warning'}
                      size="small"
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AnalyticsDashboard;