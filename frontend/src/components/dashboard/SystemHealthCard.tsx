import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Grid,
  Chip,
  LinearProgress,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Storage as DatabaseIcon,
  Memory as RedisIcon,
  Api as ApiIcon,
  EventNote as EventBusIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

// ============================================
// SYSTEM HEALTH CARD COMPONENT
// ============================================

interface SystemHealthData {
  overall: 'healthy' | 'degraded' | 'unhealthy';
  api: 'healthy' | 'degraded' | 'unhealthy';
  database: 'healthy' | 'degraded' | 'unhealthy';
  redis: 'healthy' | 'degraded' | 'unhealthy';
  eventBus: 'healthy' | 'degraded' | 'unhealthy';
}

interface SystemHealthCardProps {
  title: string;
  healthData: SystemHealthData;
  refreshing?: boolean;
  onRefresh?: () => void;
}

const SystemHealthCard: React.FC<SystemHealthCardProps> = ({
  title,
  healthData,
  refreshing = false,
  onRefresh,
}) => {
  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'default';
    }
  };

  const getHealthIcon = (component: string) => {
    switch (component) {
      case 'api':
        return <ApiIcon fontSize="small" />;
      case 'database':
        return <DatabaseIcon fontSize="small" />;
      case 'redis':
        return <RedisIcon fontSize="small" />;
      case 'eventBus':
        return <EventBusIcon fontSize="small" />;
      default:
        return <ComputerIcon fontSize="small" />;
    }
  };

  const getOverallHealthScore = () => {
    const components = Object.values(healthData).filter(key => key !== 'overall');
    const healthyCount = components.filter(status => status === 'healthy').length;
    return (healthyCount / components.length) * 100;
  };

  const componentData = [
    { key: 'api', label: 'API Gateway', status: healthData.api },
    { key: 'database', label: 'PostgreSQL', status: healthData.database },
    { key: 'redis', label: 'Redis Cache', status: healthData.redis },
    { key: 'eventBus', label: 'Event Bus', status: healthData.eventBus },
  ];

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center">
            <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
              <ComputerIcon />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                {title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                System components status
              </Typography>
            </Box>
          </Box>
          
          {onRefresh && (
            <Tooltip title="Refresh health status">
              <IconButton 
                onClick={onRefresh} 
                disabled={refreshing} 
                size="small"
                aria-label="Refresh system health status"
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
          )}
        </Box>

        {/* Overall Status */}
        <Box mb={3}>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
            <Typography variant="body2" color="text.secondary">
              Overall Health
            </Typography>
            <Chip
              label={healthData.overall.toUpperCase()}
              color={getHealthColor(healthData.overall) as any}
              size="small"
              sx={{ fontWeight: 600 }}
            />
          </Box>
          <LinearProgress
            variant="determinate"
            value={getOverallHealthScore()}
            color={getHealthColor(healthData.overall) as any}
            sx={{ height: 8, borderRadius: 4 }}
            aria-label={`Overall system health: ${getOverallHealthScore().toFixed(1)}% healthy`}
          />
          <Typography variant="caption" color="text.secondary" mt={0.5} display="block">
            {getOverallHealthScore().toFixed(1)}% of components healthy
          </Typography>
        </Box>

        {/* Component Status */}
        <Grid container spacing={2}>
          {componentData.map((component) => (
            <Grid item xs={6} key={component.key}>
              <Box 
                display="flex" 
                alignItems="center" 
                p={1} 
                border={1} 
                borderColor="divider" 
                borderRadius={1}
              >
                <Box mr={1} color={`${getHealthColor(component.status)}.main`}>
                  {getHealthIcon(component.key)}
                </Box>
                <Box flexGrow={1}>
                  <Typography variant="body2" fontWeight={500}>
                    {component.label}
                  </Typography>
                  <Typography 
                    variant="caption" 
                    color={`${getHealthColor(component.status)}.main`}
                    fontWeight={600}
                  >
                    {component.status.toUpperCase()}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SystemHealthCard;