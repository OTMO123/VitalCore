/**
 * Population Health Dashboard Component
 * Advanced Analytics for Health Tech Platform
 * 
 * Features:
 * - Risk distribution analytics
 * - Population trends visualization
 * - Cost-effectiveness metrics
 * - Quality measures tracking
 * - SOC2-compliant data aggregation
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as StableIcon,
  People as PopulationIcon,
  AttachMoney as CostIcon,
  LocalHospital as QualityIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  Info as InfoIcon,
  Analytics as AnalyticsIcon,
  Assessment as ReportIcon,
  Speed as PerformanceIcon,
  Security as ComplianceIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

import { RiskLevel } from '../../types/patient';

interface PopulationMetrics {
  totalPatients: number;
  riskDistribution: {
    low: number;
    moderate: number;
    high: number;
    critical: number;
  };
  trends: {
    metric: string;
    value: number;
    change: number;
    trend: 'up' | 'down' | 'stable';
  }[];
  qualityMeasures: {
    measureId: string;
    name: string;
    currentScore: number;
    benchmark: number;
    status: 'above' | 'below' | 'at';
  }[];
  costMetrics: {
    totalCost: number;
    costPerPatient: number;
    estimatedSavings: number;
    roi: number;
  };
  interventionOpportunities: {
    priority: 'high' | 'medium' | 'low';
    description: string;
    estimatedImpact: string;
    patientCount: number;
  }[];
}

interface PopulationHealthDashboardProps {
  timeRange: '30d' | '90d' | '1y';
  organizationFilter?: string;
  onTimeRangeChange: (range: '30d' | '90d' | '1y') => void;
}

/**
 * Population Health Analytics Dashboard
 */
const PopulationHealthDashboard: React.FC<PopulationHealthDashboardProps> = ({
  timeRange,
  organizationFilter,
  onTimeRangeChange
}) => {
  const [metrics, setMetrics] = useState<PopulationMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Load population metrics
  useEffect(() => {
    loadPopulationMetrics();
  }, [timeRange, organizationFilter]);

  const loadPopulationMetrics = async () => {
    setLoading(true);
    try {
      // Mock data - in production would call analytics API
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      
      setMetrics({
        totalPatients: 2847,
        riskDistribution: {
          low: 1423,
          moderate: 852,
          high: 431,
          critical: 141
        },
        trends: [
          { metric: 'Average Risk Score', value: 42.3, change: -2.1, trend: 'down' },
          { metric: 'High-Risk Patients', value: 20.1, change: -0.8, trend: 'down' },
          { metric: 'Care Plan Adherence', value: 78.4, change: 3.2, trend: 'up' },
          { metric: 'Readmission Rate', value: 8.7, change: -1.4, trend: 'down' },
          { metric: 'Patient Satisfaction', value: 4.6, change: 0.2, trend: 'up' },
          { metric: 'Cost Per Patient', value: 8425, change: -2.3, trend: 'down' }
        ],
        qualityMeasures: [
          { measureId: 'hba1c_control', name: 'HbA1c Control (<7%)', currentScore: 68.2, benchmark: 70.0, status: 'below' },
          { measureId: 'bp_control', name: 'Blood Pressure Control', currentScore: 72.5, benchmark: 70.0, status: 'above' },
          { measureId: 'medication_adherence', name: 'Medication Adherence', currentScore: 81.3, benchmark: 80.0, status: 'above' },
          { measureId: 'preventive_care', name: 'Preventive Care Completion', currentScore: 76.8, benchmark: 75.0, status: 'above' }
        ],
        costMetrics: {
          totalCost: 23985420,
          costPerPatient: 8425,
          estimatedSavings: 1240000,
          roi: 2.8
        },
        interventionOpportunities: [
          {
            priority: 'high',
            description: 'Diabetes care optimization for uncontrolled patients',
            estimatedImpact: '$485K annual savings',
            patientCount: 127
          },
          {
            priority: 'high',
            description: 'Enhanced discharge planning for frequent readmissions',
            estimatedImpact: '$320K annual savings',
            patientCount: 84
          },
          {
            priority: 'medium',
            description: 'Medication adherence program expansion',
            estimatedImpact: '$215K annual savings',
            patientCount: 246
          }
        ]
      });
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load population metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelColor = (level: keyof PopulationMetrics['riskDistribution']) => {
    const colors = {
      low: '#4caf50',
      moderate: '#ff9800',
      high: '#f44336',
      critical: '#d32f2f'
    };
    return colors[level];
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return <TrendingUpIcon color="success" />;
      case 'down': return <TrendingDownIcon color="error" />;
      case 'stable': return <StableIcon color="action" />;
    }
  };

  const getQualityStatusColor = (status: 'above' | 'below' | 'at') => {
    switch (status) {
      case 'above': return 'success';
      case 'below': return 'error';
      case 'at': return 'warning';
    }
  };

  if (loading || !metrics) {
    return (
      <Box display="flex" alignItems="center" justifyContent="center" minHeight={400}>
        <Box textAlign="center">
          <LinearProgress sx={{ width: 300, mb: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Loading population health analytics...
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" fontWeight={600} mb={1}>
            Population Health Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Last updated: {lastUpdated.toLocaleString()} • {metrics.totalPatients.toLocaleString()} patients
          </Typography>
        </Box>
        
        <Box display="flex" gap={1} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => onTimeRangeChange(e.target.value as any)}
              label="Time Range"
            >
              <MenuItem value="30d">30 Days</MenuItem>
              <MenuItem value="90d">90 Days</MenuItem>
              <MenuItem value="1y">1 Year</MenuItem>
            </Select>
          </FormControl>
          
          <Tooltip title="Refresh data">
            <IconButton onClick={loadPopulationMetrics}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Risk Distribution */}
        <Grid item xs={12} md={6} lg={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <PopulationIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  Risk Distribution
                </Typography>
              </Box>
              
              <Box mb={2}>
                <Typography variant="h4" fontWeight={700} color="primary.main">
                  {metrics.totalPatients.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Patients
                </Typography>
              </Box>

              {Object.entries(metrics.riskDistribution).map(([level, count]) => {
                const percentage = (count / metrics.totalPatients) * 100;
                return (
                  <Box key={level} mb={1}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                        {level} Risk
                      </Typography>
                      <Typography variant="body2" fontWeight={500}>
                        {count} ({percentage.toFixed(1)}%)
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={percentage}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        bgcolor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: getRiskLevelColor(level as keyof PopulationMetrics['riskDistribution']),
                          borderRadius: 4
                        }
                      }}
                    />
                  </Box>
                );
              })}
            </CardContent>
          </Card>
        </Grid>

        {/* Key Metrics Trends */}
        <Grid item xs={12} md={6} lg={8}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <AnalyticsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  Key Performance Trends
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                {metrics.trends.map((trend, index) => (
                  <Grid item xs={12} sm={6} key={index}>
                    <Box
                      sx={{
                        p: 2,
                        border: '1px solid',
                        borderColor: 'grey.200',
                        borderRadius: 1,
                        bgcolor: 'grey.50'
                      }}
                    >
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2" color="text.secondary">
                          {trend.metric}
                        </Typography>
                        {getTrendIcon(trend.trend)}
                      </Box>
                      
                      <Typography variant="h6" fontWeight={600}>
                        {trend.metric.includes('Cost') 
                          ? `$${trend.value.toLocaleString()}`
                          : trend.metric.includes('Rate') || trend.metric.includes('Adherence') || trend.metric.includes('Patients')
                          ? `${trend.value}%`
                          : trend.value
                        }
                      </Typography>
                      
                      <Typography
                        variant="caption"
                        color={trend.change > 0 ? 'success.main' : trend.change < 0 ? 'error.main' : 'text.secondary'}
                      >
                        {trend.change > 0 ? '+' : ''}{trend.change}% vs previous period
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Quality Measures */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <QualityIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  Quality Measures
                </Typography>
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Measure</TableCell>
                      <TableCell align="center">Current</TableCell>
                      <TableCell align="center">Benchmark</TableCell>
                      <TableCell align="center">Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {metrics.qualityMeasures.map((measure) => (
                      <TableRow key={measure.measureId}>
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {measure.name}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" fontWeight={600}>
                            {measure.currentScore}%
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2" color="text.secondary">
                            {measure.benchmark}%
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            size="small"
                            label={measure.status === 'above' ? 'Above' : measure.status === 'below' ? 'Below' : 'At'}
                            color={getQualityStatusColor(measure.status)}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Cost Analytics */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CostIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  Cost Analytics
                </Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box textAlign="center" p={1}>
                    <Typography variant="h5" fontWeight={700} color="primary.main">
                      ${(metrics.costMetrics.totalCost / 1000000).toFixed(1)}M
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Total Cost
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Box textAlign="center" p={1}>
                    <Typography variant="h5" fontWeight={700} color="success.main">
                      ${metrics.costMetrics.costPerPatient.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Cost Per Patient
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Box textAlign="center" p={1}>
                    <Typography variant="h5" fontWeight={700} color="success.main">
                      ${(metrics.costMetrics.estimatedSavings / 1000).toFixed(0)}K
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Estimated Savings
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Box textAlign="center" p={1}>
                    <Typography variant="h5" fontWeight={700} color="warning.main">
                      {metrics.costMetrics.roi.toFixed(1)}x
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ROI Multiple
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Intervention Opportunities */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <PerformanceIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  High-Impact Intervention Opportunities
                </Typography>
              </Box>

              <List>
                {metrics.interventionOpportunities.map((opportunity, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemIcon>
                        <Avatar
                          sx={{
                            bgcolor: opportunity.priority === 'high' ? 'error.main' : 
                                     opportunity.priority === 'medium' ? 'warning.main' : 'info.main',
                            width: 32,
                            height: 32
                          }}
                        >
                          {opportunity.priority === 'high' ? <WarningIcon fontSize="small" /> : 
                           opportunity.priority === 'medium' ? <InfoIcon fontSize="small" /> : 
                           <SuccessIcon fontSize="small" />}
                        </Avatar>
                      </ListItemIcon>
                      
                      <ListItemText
                        primary={
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="body1" fontWeight={500}>
                              {opportunity.description}
                            </Typography>
                            <Chip
                              label={`${opportunity.priority.toUpperCase()} PRIORITY`}
                              size="small"
                              color={opportunity.priority === 'high' ? 'error' : 
                                     opportunity.priority === 'medium' ? 'warning' : 'info'}
                            />
                          </Box>
                        }
                        secondary={
                          <Box display="flex" justifyContent="space-between" mt={1}>
                            <Typography variant="body2" color="success.main" fontWeight={500}>
                              {opportunity.estimatedImpact}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {opportunity.patientCount} patients affected
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < metrics.interventionOpportunities.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* SOC2 Compliance Notice */}
        <Grid item xs={12}>
          <Alert 
            severity="info" 
            icon={<ComplianceIcon />}
            sx={{ bgcolor: 'primary.50', borderColor: 'primary.200' }}
          >
            <Typography variant="body2">
              <strong>SOC2 Compliance:</strong> All population health analytics are de-identified and aggregated 
              in compliance with HIPAA and SOC2 Type 2 security controls. Individual patient data is encrypted 
              and access is audited.
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PopulationHealthDashboard;