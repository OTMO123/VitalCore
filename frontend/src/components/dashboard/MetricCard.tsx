import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Chip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
} from '@mui/icons-material';

// ============================================
// METRIC CARD COMPONENT
// ============================================

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  loading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  color = 'primary',
  change,
  changeType = 'neutral',
  loading = false,
}) => {
  const getChangeIcon = () => {
    switch (changeType) {
      case 'positive':
        return <TrendingUpIcon fontSize="small" />;
      case 'negative':
        return <TrendingDownIcon fontSize="small" />;
      default:
        return <TrendingFlatIcon fontSize="small" />;
    }
  };

  const getChangeColor = () => {
    switch (changeType) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 4,
        },
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="body2" color="text.secondary" fontWeight={500}>
            {title}
          </Typography>
          <Avatar
            sx={{
              bgcolor: `${color}.main`,
              width: 40,
              height: 40,
            }}
          >
            {icon}
          </Avatar>
        </Box>

        <Typography variant="h4" fontWeight={700} mb={1}>
          {loading ? '...' : value}
        </Typography>

        {change && (
          <Box display="flex" alignItems="center">
            <Chip
              icon={getChangeIcon()}
              label={change}
              size="small"
              color={getChangeColor() as any}
              variant="outlined"
              sx={{
                fontSize: '0.75rem',
                height: 24,
                '& .MuiChip-icon': {
                  fontSize: '0.875rem',
                },
              }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default MetricCard;