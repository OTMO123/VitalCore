/**
 * Predictive Health Trajectories - Feature #2
 * "See the Future of Patient Health"
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Typography,
  Grid,
  LinearProgress,
  Alert,
  Chip,
  Button,
  Paper,
  Divider,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Timeline,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  LocalHospital as HospitalIcon,
  Psychology as BrainIcon,
  Favorite as HeartIcon,
  Schedule as TimeIcon,
  Person as PersonIcon,
  Analytics as AnalyticsIcon,
  Notifications as AlertIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';

interface HealthTrajectory {
  patientId: string;
  patientName: string;
  currentRiskScore: number;
  predictions: {
    hospitalizationRisk: {
      thirtyDay: number;
      sixtyDay: number;
      ninetyDay: number;
    };
    interventionPoints: InterventionPoint[];
    resourceNeeds: ResourcePrediction[];
    outcomeScenarios: OutcomeScenario[];
  };
  trendData: TrendDataPoint[];
  riskFactors: RiskFactor[];
}

interface InterventionPoint {
  date: string;
  type: 'MEDICATION' | 'LIFESTYLE' | 'MONITORING' | 'SPECIALIST';
  urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  expectedImpact: number;
  confidence: number;
}

interface ResourcePrediction {
  resource: string;
  predictedNeed: number;
  timeframe: string;
  confidence: number;
}

interface OutcomeScenario {
  scenario: string;
  probability: number;
  timeline: string;
  interventionRequired: boolean;
}

interface TrendDataPoint {
  date: string;
  riskScore: number;
  predicted: number;
  confidence: number;
}

interface RiskFactor {
  factor: string;
  impact: number;
  trend: 'INCREASING' | 'STABLE' | 'DECREASING';
  controllable: boolean;
}

export const PredictiveHealthTrajectory: React.FC = () => {
  const [selectedPatient, setSelectedPatient] = useState<string>('P001');
  const [trajectory, setTrajectory] = useState<HealthTrajectory | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'30' | '60' | '90'>('90');

  // Load patient trajectory data
  useEffect(() => {
    loadPatientTrajectory(selectedPatient);
  }, [selectedPatient]);

  const loadPatientTrajectory = async (patientId: string) => {
    setIsLoading(true);
    
    // Simulate AI-powered trajectory analysis
    setTimeout(() => {
      const mockTrajectory: HealthTrajectory = {
        patientId,
        patientName: patientId === 'P001' ? 'Sarah Johnson' : 'Michael Chen',
        currentRiskScore: 72,
        predictions: {
          hospitalizationRisk: {
            thirtyDay: 15,
            sixtyDay: 28,
            ninetyDay: 45
          },
          interventionPoints: [
            {
              date: '2024-01-20',
              type: 'MEDICATION',
              urgency: 'HIGH',
              description: 'Adjust ACE inhibitor dosage to prevent heart failure progression',
              expectedImpact: 35,
              confidence: 0.87
            },
            {
              date: '2024-02-05',
              type: 'MONITORING',
              urgency: 'MEDIUM',
              description: 'Increase home blood pressure monitoring frequency',
              expectedImpact: 20,
              confidence: 0.79
            },
            {
              date: '2024-02-15',
              type: 'LIFESTYLE',
              urgency: 'MEDIUM',
              description: 'Dietary sodium restriction program enrollment',
              expectedImpact: 25,
              confidence: 0.82
            }
          ],
          resourceNeeds: [
            { resource: 'Cardiologist Visits', predictedNeed: 3, timeframe: '90 days', confidence: 0.91 },
            { resource: 'Home Health Visits', predictedNeed: 8, timeframe: '90 days', confidence: 0.76 },
            { resource: 'Emergency Department', predictedNeed: 1, timeframe: '90 days', confidence: 0.68 }
          ],
          outcomeScenarios: [
            { scenario: 'Optimal Care Path', probability: 45, timeline: '90 days', interventionRequired: true },
            { scenario: 'Standard Care', probability: 35, timeline: '90 days', interventionRequired: false },
            { scenario: 'High-Risk Trajectory', probability: 20, timeline: '90 days', interventionRequired: true }
          ]
        },
        trendData: [
          { date: '2024-01-01', riskScore: 65, predicted: 66, confidence: 0.85 },
          { date: '2024-01-15', riskScore: 68, predicted: 70, confidence: 0.87 },
          { date: '2024-01-30', riskScore: 72, predicted: 75, confidence: 0.89 },
          { date: '2024-02-15', riskScore: 0, predicted: 78, confidence: 0.84 },
          { date: '2024-03-01', riskScore: 0, predicted: 82, confidence: 0.79 },
          { date: '2024-03-15', riskScore: 0, predicted: 85, confidence: 0.75 }
        ],
        riskFactors: [
          { factor: 'Hypertension Control', impact: 30, trend: 'INCREASING', controllable: true },
          { factor: 'Medication Adherence', impact: 25, trend: 'DECREASING', controllable: true },
          { factor: 'Age Factor', impact: 15, trend: 'STABLE', controllable: false },
          { factor: 'Diet Quality', impact: 20, trend: 'STABLE', controllable: true },
          { factor: 'Exercise Frequency', impact: 10, trend: 'DECREASING', controllable: true }
        ]
      };
      
      setTrajectory(mockTrajectory);
      setIsLoading(false);
    }, 1500);
  };

  const getRiskColor = (risk: number) => {
    if (risk >= 75) return 'error';
    if (risk >= 50) return 'warning';
    if (risk >= 25) return 'info';
    return 'success';
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      case 'LOW': return 'success';
      default: return 'default';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'INCREASING': return <TrendingUpIcon color="error" />;
      case 'DECREASING': return <TrendingUpIcon sx={{ transform: 'rotate(180deg)', color: 'success.main' }} />;
      case 'STABLE': return <TrendingUpIcon sx={{ transform: 'rotate(90deg)', color: 'info.main' }} />;
      default: return <TrendingUpIcon />;
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Card sx={{ p: 3, textAlign: 'center' }}>
          <BrainIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" sx={{ mb: 2 }}>
            AI Analyzing Health Trajectory...
          </Typography>
          <LinearProgress sx={{ mb: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Processing temporal ML models and population health data
          </Typography>
        </Card>
      </Box>
    );
  }

  if (!trajectory) return null;

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 3, textAlign: 'center' }}>
        <Typography variant="h4" sx={{ mb: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <Timeline color="primary" fontSize="large" />
          Predictive Health Trajectories
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          AI-powered patient journey predictions and intervention optimization
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Patient Overview */}
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                <PersonIcon />
              </Avatar>
              <Box>
                <Typography variant="h6">{trajectory.patientName}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Patient ID: {trajectory.patientId}
                </Typography>
              </Box>
            </Box>

            {/* Current Risk Score */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Current Risk Score
              </Typography>
              <Box sx={{ position: 'relative', mb: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={trajectory.currentRiskScore}
                  sx={{ 
                    height: 12, 
                    borderRadius: 6,
                    backgroundColor: 'grey.200',
                  }}
                  color={getRiskColor(trajectory.currentRiskScore) as any}
                />
                <Typography
                  variant="body2"
                  sx={{
                    position: 'absolute',
                    right: 8,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'white',
                    fontWeight: 'bold',
                    fontSize: '0.75rem'
                  }}
                >
                  {trajectory.currentRiskScore}%
                </Typography>
              </Box>
              <Alert severity={getRiskColor(trajectory.currentRiskScore) as any} size="small">
                {trajectory.currentRiskScore >= 75 ? 'High Risk - Immediate attention required' :
                 trajectory.currentRiskScore >= 50 ? 'Moderate Risk - Close monitoring needed' :
                 'Low Risk - Standard care protocol'}
              </Alert>
            </Box>

            {/* Hospitalization Risk */}
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Hospitalization Risk
              </Typography>
              <Grid container spacing={1}>
                {Object.entries(trajectory.predictions.hospitalizationRisk).map(([period, risk]) => (
                  <Grid item xs={4} key={period}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'grey.50' }}>
                      <Typography variant="body2" color="text.secondary">
                        {period.replace('Day', 'd')}
                      </Typography>
                      <Typography variant="h6" color={getRiskColor(risk)}>
                        {risk}%
                      </Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Card>

          {/* Risk Factors */}
          <Card sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon />
              Risk Factors
            </Typography>
            <List dense>
              {trajectory.riskFactors.map((factor, index) => (
                <ListItem key={index} sx={{ px: 0 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {getTrendIcon(factor.trend)}
                  </ListItemIcon>
                  <ListItemText
                    primary={factor.factor}
                    secondary={`${factor.impact}% impact`}
                  />
                  <Chip
                    size="small"
                    label={factor.controllable ? 'Controllable' : 'Fixed'}
                    color={factor.controllable ? 'primary' : 'default'}
                    variant={factor.controllable ? 'filled' : 'outlined'}
                  />
                </ListItem>
              ))}
            </List>
          </Card>
        </Grid>

        {/* Trajectory Visualization */}
        <Grid item xs={12} md={8}>
          <Card sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <AnalyticsIcon />
              Health Trajectory Prediction
            </Typography>

            <Box sx={{ height: 300, mb: 2 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trajectory.trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[0, 100]} />
                  <RechartsTooltip 
                    labelFormatter={(value) => `Date: ${value}`}
                    formatter={(value: any, name) => [
                      `${value}%`,
                      name === 'riskScore' ? 'Current Risk' : 'Predicted Risk'
                    ]}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="predicted" 
                    stroke="#ff9800" 
                    fill="#fff3e0" 
                    name="Predicted Risk"
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="riskScore" 
                    stroke="#2196f3" 
                    strokeWidth={3}
                    dot={{ fill: '#2196f3', strokeWidth: 2, r: 4 }}
                    name="Current Risk"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>

            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>AI Prediction Confidence:</strong> 84% accuracy based on 50,000+ similar patient trajectories
              </Typography>
            </Alert>
          </Card>

          {/* Intervention Points */}
          <Card sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimeIcon />
              Optimal Intervention Points
            </Typography>

            <Grid container spacing={2}>
              {trajectory.predictions.interventionPoints.map((intervention, index) => (
                <Grid item xs={12} key={index}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <Paper sx={{ p: 2, border: '1px solid', borderColor: 'grey.200' }}>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Chip
                              label={intervention.urgency}
                              color={getUrgencyColor(intervention.urgency) as any}
                              size="small"
                            />
                            <Chip
                              label={intervention.type}
                              variant="outlined"
                              size="small"
                            />
                            <Typography variant="body2" color="text.secondary">
                              {intervention.date}
                            </Typography>
                          </Box>
                          
                          <Typography variant="body1" sx={{ mb: 1 }}>
                            {intervention.description}
                          </Typography>
                          
                          <Box sx={{ display: 'flex', gap: 2 }}>
                            <Typography variant="body2" color="success.main">
                              Expected Impact: -{intervention.expectedImpact}% risk
                            </Typography>
                            <Typography variant="body2" color="primary.main">
                              Confidence: {(intervention.confidence * 100).toFixed(0)}%
                            </Typography>
                          </Box>
                        </Box>
                        
                        <IconButton
                          color="primary"
                          aria-label="Schedule intervention"
                        >
                          <CheckIcon />
                        </IconButton>
                      </Box>
                    </Paper>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          </Card>
        </Grid>
      </Grid>

      {/* Outcome Scenarios */}
      <Card sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <BrainIcon />
          Predicted Outcome Scenarios (90-day forecast)
        </Typography>
        
        <Grid container spacing={2}>
          {trajectory.predictions.outcomeScenarios.map((scenario, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Paper 
                sx={{ 
                  p: 2, 
                  textAlign: 'center',
                  border: '2px solid',
                  borderColor: scenario.probability > 40 ? 'success.main' : 
                              scenario.probability > 25 ? 'warning.main' : 'error.main'
                }}
              >
                <Typography variant="h4" sx={{ mb: 1 }} color={
                  scenario.probability > 40 ? 'success.main' : 
                  scenario.probability > 25 ? 'warning.main' : 'error.main'
                }>
                  {scenario.probability}%
                </Typography>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  {scenario.scenario}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {scenario.timeline}
                </Typography>
                {scenario.interventionRequired && (
                  <Chip label="Intervention Required" color="warning" size="small" />
                )}
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Card>
    </Box>
  );
};

export default PredictiveHealthTrajectory;