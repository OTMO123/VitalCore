/**
 * Intelligent PHI Guardian - Feature #3
 * "Zero-Trust AI for Healthcare Privacy"
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  Typography,
  Grid,
  Alert,
  Chip,
  Button,
  Paper,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Switch,
  FormControlLabel,
  Divider,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Shield as ShieldIcon,
  Security as SecurityIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Block as BlockIcon,
  Psychology as AIIcon,
  Lock as LockIcon,
  Key as KeyIcon,
  Timeline as TimelineIcon,
  Person as PersonIcon,
  Fingerprint as FingerprintIcon,
  Analytics as AnalyticsIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';

interface PHIGuardianStatus {
  overallSecurityScore: number;
  activeThreats: number;
  blockedAttempts: number;
  complianceScore: number;
  encryptionStatus: 'ACTIVE' | 'DEGRADED' | 'FAILED';
  anomalies: SecurityAnomaly[];
  accessPatterns: AccessPattern[];
  riskAssessment: RiskAssessment;
  consentStatus: ConsentStatus[];
}

interface SecurityAnomaly {
  id: string;
  type: 'UNUSUAL_ACCESS' | 'MULTIPLE_LOGINS' | 'OFF_HOURS' | 'LOCATION_ANOMALY' | 'DATA_PATTERN';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  timestamp: string;
  description: string;
  affectedRecords: number;
  aiConfidence: number;
  status: 'MONITORING' | 'INVESTIGATING' | 'RESOLVED' | 'BLOCKED';
}

interface AccessPattern {
  userId: string;
  userName: string;
  accessCount: number;
  riskScore: number;
  lastAccess: string;
  dataTypes: string[];
  timePattern: 'NORMAL' | 'UNUSUAL' | 'SUSPICIOUS';
}

interface RiskAssessment {
  currentLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  factors: {
    factor: string;
    impact: number;
    trend: 'IMPROVING' | 'STABLE' | 'DEGRADING';
  }[];
  predictions: {
    nextHour: number;
    next24Hours: number;
    nextWeek: number;
  };
}

interface ConsentStatus {
  patientId: string;
  patientName: string;
  consentTypes: {
    type: string;
    granted: boolean;
    expiryDate: string;
    lastUpdated: string;
  }[];
  gdprCompliant: boolean;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
}

export const IntelligentPHIGuardian: React.FC = () => {
  const [guardianStatus, setGuardianStatus] = useState<PHIGuardianStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAnomaly, setSelectedAnomaly] = useState<SecurityAnomaly | null>(null);
  const [autoMitigationEnabled, setAutoMitigationEnabled] = useState(true);
  const [realTimeMonitoring, setRealTimeMonitoring] = useState(true);
  const [anomalyDialogOpen, setAnomalyDialogOpen] = useState(false);

  // Load PHI Guardian status
  useEffect(() => {
    loadGuardianStatus();
    
    // Simulate real-time updates
    const interval = setInterval(() => {
      if (realTimeMonitoring) {
        updateRealTimeMetrics();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [realTimeMonitoring]);

  const loadGuardianStatus = async () => {
    setIsLoading(true);
    
    // Simulate AI-powered security analysis
    setTimeout(() => {
      const mockStatus: PHIGuardianStatus = {
        overallSecurityScore: 94,
        activeThreats: 2,
        blockedAttempts: 156,
        complianceScore: 98,
        encryptionStatus: 'ACTIVE',
        anomalies: [
          {
            id: 'ANOM001',
            type: 'UNUSUAL_ACCESS',
            severity: 'HIGH',
            timestamp: '2024-01-15T14:30:00Z',
            description: 'User accessing 3x more PHI records than normal pattern',
            affectedRecords: 45,
            aiConfidence: 0.89,
            status: 'INVESTIGATING'
          },
          {
            id: 'ANOM002',
            type: 'OFF_HOURS',
            severity: 'MEDIUM',
            timestamp: '2024-01-15T02:15:00Z',
            description: 'Off-hours access to sensitive cardiology records',
            affectedRecords: 12,
            aiConfidence: 0.76,
            status: 'MONITORING'
          },
          {
            id: 'ANOM003',
            type: 'LOCATION_ANOMALY',
            severity: 'CRITICAL',
            timestamp: '2024-01-15T13:45:00Z',
            description: 'Access attempt from unusual geographic location',
            affectedRecords: 0,
            aiConfidence: 0.95,
            status: 'BLOCKED'
          }
        ],
        accessPatterns: [
          {
            userId: 'U001',
            userName: 'Dr. Sarah Wilson',
            accessCount: 234,
            riskScore: 15,
            lastAccess: '2024-01-15T15:30:00Z',
            dataTypes: ['cardiology', 'general'],
            timePattern: 'NORMAL'
          },
          {
            userId: 'U002',
            userName: 'Nurse Mike Johnson',
            accessCount: 89,
            riskScore: 67,
            lastAccess: '2024-01-15T14:45:00Z',
            dataTypes: ['emergency', 'general', 'pharmacy'],
            timePattern: 'UNUSUAL'
          }
        ],
        riskAssessment: {
          currentLevel: 'MEDIUM',
          factors: [
            { factor: 'Unusual Access Patterns', impact: 35, trend: 'DEGRADING' },
            { factor: 'Geographic Anomalies', impact: 25, trend: 'STABLE' },
            { factor: 'Failed Login Attempts', impact: 15, trend: 'IMPROVING' },
            { factor: 'Off-Hours Activity', impact: 20, trend: 'STABLE' },
            { factor: 'Consent Compliance', impact: 5, trend: 'IMPROVING' }
          ],
          predictions: {
            nextHour: 35,
            next24Hours: 28,
            nextWeek: 22
          }
        },
        consentStatus: [
          {
            patientId: 'P001',
            patientName: 'Sarah Johnson',
            consentTypes: [
              { type: 'Treatment', granted: true, expiryDate: '2024-12-31', lastUpdated: '2024-01-01' },
              { type: 'Research', granted: false, expiryDate: 'N/A', lastUpdated: '2024-01-01' },
              { type: 'Marketing', granted: false, expiryDate: 'N/A', lastUpdated: '2024-01-01' }
            ],
            gdprCompliant: true,
            riskLevel: 'LOW'
          }
        ]
      };
      
      setGuardianStatus(mockStatus);
      setIsLoading(false);
    }, 1500);
  };

  const updateRealTimeMetrics = () => {
    if (guardianStatus) {
      setGuardianStatus(prev => prev ? {
        ...prev,
        activeThreats: prev.activeThreats + Math.floor(Math.random() * 3) - 1,
        blockedAttempts: prev.blockedAttempts + Math.floor(Math.random() * 5),
        overallSecurityScore: Math.max(85, Math.min(100, prev.overallSecurityScore + (Math.random() - 0.5) * 2))
      } : null);
    }
  };

  const handleAnomalyClick = (anomaly: SecurityAnomaly) => {
    setSelectedAnomaly(anomaly);
    setAnomalyDialogOpen(true);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      case 'LOW': return 'success';
      default: return 'default';
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      case 'LOW': return 'success';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'BLOCKED': return <BlockIcon color="error" />;
      case 'INVESTIGATING': return <AnalyticsIcon color="warning" />;
      case 'MONITORING': return <VisibilityIcon color="info" />;
      case 'RESOLVED': return <CheckIcon color="success" />;
      default: return <SecurityIcon />;
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Card sx={{ p: 3, textAlign: 'center' }}>
          <ShieldIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" sx={{ mb: 2 }}>
            Initializing PHI Guardian AI...
          </Typography>
          <LinearProgress sx={{ mb: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Analyzing access patterns, threat vectors, and compliance status
          </Typography>
        </Card>
      </Box>
    );
  }

  if (!guardianStatus) return null;

  const pieData = [
    { name: 'Secure Access', value: 95, color: '#4caf50' },
    { name: 'Monitored', value: 3, color: '#ff9800' },
    { name: 'Blocked', value: 2, color: '#f44336' }
  ];

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 3, textAlign: 'center' }}>
        <Typography variant="h4" sx={{ mb: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <ShieldIcon color="primary" fontSize="large" />
          Intelligent PHI Guardian
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Zero-Trust AI for Healthcare Privacy Protection
        </Typography>
      </Box>

      {/* Control Panel */}
      <Card sx={{ p: 2, mb: 3, bgcolor: 'primary.50' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControlLabel
                control={
                  <Switch 
                    checked={autoMitigationEnabled} 
                    onChange={(e) => setAutoMitigationEnabled(e.target.checked)}
                    color="primary"
                  />
                }
                label="Auto-Mitigation"
              />
              <FormControlLabel
                control={
                  <Switch 
                    checked={realTimeMonitoring} 
                    onChange={(e) => setRealTimeMonitoring(e.target.checked)}
                    color="primary"
                  />
                }
                label="Real-Time Monitoring"
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={6} sx={{ textAlign: { md: 'right' } }}>
            <Typography variant="body2" color="text.secondary">
              Last Updated: {new Date().toLocaleTimeString()}
            </Typography>
          </Grid>
        </Grid>
      </Card>

      <Grid container spacing={3}>
        {/* Security Overview */}
        <Grid item xs={12} md={4}>
          <Card sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon />
              Security Overview
            </Typography>

            {/* Overall Security Score */}
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography variant="h2" color="primary.main" sx={{ mb: 1 }}>
                {guardianStatus.overallSecurityScore}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Overall Security Score
              </Typography>
              <LinearProgress
                variant="determinate"
                value={guardianStatus.overallSecurityScore}
                sx={{ mt: 1, height: 8, borderRadius: 4 }}
                color={guardianStatus.overallSecurityScore >= 90 ? 'success' : guardianStatus.overallSecurityScore >= 75 ? 'warning' : 'error'}
              />
            </Box>

            {/* Key Metrics */}
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'error.50' }}>
                  <Typography variant="h5" color="error.main">
                    {guardianStatus.activeThreats}
                  </Typography>
                  <Typography variant="caption">Active Threats</Typography>
                </Paper>
              </Grid>
              <Grid item xs={6}>
                <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'success.50' }}>
                  <Typography variant="h5" color="success.main">
                    {guardianStatus.blockedAttempts}
                  </Typography>
                  <Typography variant="caption">Blocked Today</Typography>
                </Paper>
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            {/* Compliance Status */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Compliance Score: {guardianStatus.complianceScore}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={guardianStatus.complianceScore}
                sx={{ height: 6, borderRadius: 3 }}
                color={guardianStatus.complianceScore >= 95 ? 'success' : 'warning'}
              />
            </Box>

            {/* Encryption Status */}
            <Alert 
              severity={guardianStatus.encryptionStatus === 'ACTIVE' ? 'success' : 'error'} 
              sx={{ mt: 2 }}
              icon={<LockIcon />}
            >
              <Typography variant="body2">
                <strong>Encryption Status:</strong> {guardianStatus.encryptionStatus}
                <br />
                AES-256-GCM with key rotation every 30 days
              </Typography>
            </Alert>
          </Card>

          {/* Access Patterns Pie Chart */}
          <Card sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <AnalyticsIcon />
              Access Distribution
            </Typography>
            <Box sx={{ height: 200, display: 'flex', justifyContent: 'center' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip formatter={(value) => [`${value}%`, '']} />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Card>
        </Grid>

        {/* Security Anomalies */}
        <Grid item xs={12} md={8}>
          <Card sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon />
              Security Anomalies ({guardianStatus.anomalies.length})
            </Typography>

            <Grid container spacing={2}>
              {guardianStatus.anomalies.map((anomaly, index) => (
                <Grid item xs={12} key={anomaly.id}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <Paper 
                      sx={{ 
                        p: 2, 
                        border: '1px solid',
                        borderColor: `${getSeverityColor(anomaly.severity)}.main`,
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'grey.50' }
                      }}
                      onClick={() => handleAnomalyClick(anomaly)}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            {getStatusIcon(anomaly.status)}
                            <Chip
                              label={anomaly.severity}
                              color={getSeverityColor(anomaly.severity) as any}
                              size="small"
                            />
                            <Chip
                              label={anomaly.type.replace('_', ' ')}
                              variant="outlined"
                              size="small"
                            />
                            <Typography variant="body2" color="text.secondary">
                              {new Date(anomaly.timestamp).toLocaleString()}
                            </Typography>
                          </Box>
                          
                          <Typography variant="body1" sx={{ mb: 1 }}>
                            {anomaly.description}
                          </Typography>
                          
                          <Box sx={{ display: 'flex', gap: 2 }}>
                            <Typography variant="body2" color="warning.main">
                              {anomaly.affectedRecords} records affected
                            </Typography>
                            <Typography variant="body2" color="primary.main">
                              AI Confidence: {(anomaly.aiConfidence * 100).toFixed(0)}%
                            </Typography>
                            <Chip
                              label={anomaly.status}
                              size="small"
                              color={anomaly.status === 'BLOCKED' ? 'error' : 
                                     anomaly.status === 'INVESTIGATING' ? 'warning' : 'info'}
                            />
                          </Box>
                        </Box>
                      </Box>
                    </Paper>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          </Card>

          {/* Risk Assessment */}
          <Card sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimelineIcon />
              Risk Assessment & Predictions
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  Current Risk Level: 
                  <Chip 
                    label={guardianStatus.riskAssessment.currentLevel} 
                    color={getRiskColor(guardianStatus.riskAssessment.currentLevel) as any}
                    sx={{ ml: 1 }}
                  />
                </Typography>

                <List dense>
                  {guardianStatus.riskAssessment.factors.map((factor, index) => (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <FingerprintIcon color={factor.trend === 'DEGRADING' ? 'error' : 'primary'} />
                      </ListItemIcon>
                      <ListItemText
                        primary={factor.factor}
                        secondary={`${factor.impact}% impact - ${factor.trend}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  Risk Predictions
                </Typography>
                
                <Grid container spacing={1}>
                  <Grid item xs={4}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'warning.50' }}>
                      <Typography variant="h6" color="warning.main">
                        {guardianStatus.riskAssessment.predictions.nextHour}%
                      </Typography>
                      <Typography variant="caption">Next Hour</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={4}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'info.50' }}>
                      <Typography variant="h6" color="info.main">
                        {guardianStatus.riskAssessment.predictions.next24Hours}%
                      </Typography>
                      <Typography variant="caption">24 Hours</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={4}>
                    <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'success.50' }}>
                      <Typography variant="h6" color="success.main">
                        {guardianStatus.riskAssessment.predictions.nextWeek}%
                      </Typography>
                      <Typography variant="caption">Next Week</Typography>
                    </Paper>
                  </Grid>
                </Grid>

                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    <strong>AI Analysis:</strong> Risk decreasing due to enhanced monitoring
                  </Typography>
                </Alert>
              </Grid>
            </Grid>
          </Card>
        </Grid>
      </Grid>

      {/* Anomaly Detail Dialog */}
      <Dialog
        open={anomalyDialogOpen}
        onClose={() => setAnomalyDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Security Anomaly Details
        </DialogTitle>
        <DialogContent>
          {selectedAnomaly && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {selectedAnomaly.description}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Chip label={selectedAnomaly.severity} color={getSeverityColor(selectedAnomaly.severity) as any} />
                    <Chip label={selectedAnomaly.type.replace('_', ' ')} variant="outlined" />
                    <Chip label={selectedAnomaly.status} />
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Anomaly Details</Typography>
                  <TableContainer component={Paper} sx={{ mt: 1 }}>
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Timestamp</TableCell>
                          <TableCell>{new Date(selectedAnomaly.timestamp).toLocaleString()}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Affected Records</TableCell>
                          <TableCell>{selectedAnomaly.affectedRecords}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>AI Confidence</TableCell>
                          <TableCell>{(selectedAnomaly.aiConfidence * 100).toFixed(1)}%</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Recommended Actions</Typography>
                  <List dense sx={{ mt: 1 }}>
                    <ListItem>
                      <ListItemIcon><CheckIcon color="primary" /></ListItemIcon>
                      <ListItemText primary="Enhanced monitoring activated" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><SecurityIcon color="warning" /></ListItemIcon>
                      <ListItemText primary="User access privileges reviewed" />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon><ShieldIcon color="info" /></ListItemIcon>
                      <ListItemText primary="Additional authentication required" />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnomalyDialogOpen(false)}>Close</Button>
          <Button variant="contained" color="primary">
            Take Action
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default IntelligentPHIGuardian;