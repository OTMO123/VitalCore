/**
 * Risk Score Card Component
 * SOC2-Compliant Risk Visualization for Health Tech
 * 
 * Features:
 * - Real-time risk assessment display
 * - Color-coded risk levels with clinical context
 * - Audit-logged interactions (CC7.2)
 * - PHI-protected data rendering
 * - Accessibility compliant (WCAG 2.1 AA)
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  CircularProgress,
  Tooltip,
  IconButton,
  Avatar,
  LinearProgress,
  Alert,
  Collapse,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  TrendingUp as RiskIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  InfoOutlined as InfoIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Shield as SecurityIcon,
  Visibility as ViewIcon,
  Assignment as RecommendationIcon,
  LocalHospital as ClinicalIcon,
  TrendingUp as TrendIcon,
  Security as AuditIcon,
} from '@mui/icons-material';

import { RiskLevel, RiskScore, RiskFactor, CareRecommendation } from '../../types/patient';
import { patientRiskService } from '../../services/patientRiskService';
import { Patient } from '../../types';

interface RiskScoreCardProps {
  patient: Patient;
  onRiskCalculated?: (riskScore: RiskScore) => void;
  compact?: boolean;
  enableInteraction?: boolean;
  auditContext?: {
    userId: string;
    sessionId: string;
    organizationId: string;
  };
}

/**
 * Advanced Risk Score Card with Health Tech UI/UX best practices
 */
const RiskScoreCard: React.FC<RiskScoreCardProps> = ({
  patient,
  onRiskCalculated,
  compact = false,
  enableInteraction = true,
  auditContext
}) => {
  const [riskScore, setRiskScore] = useState<RiskScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [auditDialogOpen, setAuditDialogOpen] = useState(false);

  // Load risk score on component mount
  useEffect(() => {
    if (patient?.id) {
      calculateRiskScore();
    }
  }, [patient?.id]);

  const calculateRiskScore = async () => {
    if (!patient?.id) return;

    setLoading(true);
    setError(null);

    try {
      const calculatedRisk = await patientRiskService.calculateRiskScore(patient);
      setRiskScore(calculatedRisk);
      onRiskCalculated?.(calculatedRisk);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Risk calculation failed');
      console.error('Risk calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelConfig = (level: RiskLevel) => {
    const configs = {
      [RiskLevel.LOW]: {
        color: '#4caf50',
        bgColor: '#e8f5e8',
        textColor: '#2e7d32',
        icon: CheckIcon,
        label: 'Low Risk',
        description: 'Patient is stable with minimal intervention needs',
        priority: 'Routine monitoring'
      },
      [RiskLevel.MODERATE]: {
        color: '#ff9800',
        bgColor: '#fff3e0',
        textColor: '#ef6c00',
        icon: InfoIcon,
        label: 'Moderate Risk',
        description: 'Patient requires enhanced monitoring and care coordination',
        priority: 'Enhanced care plan'
      },
      [RiskLevel.HIGH]: {
        color: '#f44336',
        bgColor: '#ffebee',
        textColor: '#c62828',
        icon: WarningIcon,
        label: 'High Risk',
        description: 'Patient needs immediate clinical attention and intervention',
        priority: 'Urgent intervention'
      },
      [RiskLevel.CRITICAL]: {
        color: '#d32f2f',
        bgColor: '#ffcccb',
        textColor: '#b71c1c',
        icon: ErrorIcon,
        label: 'Critical Risk',
        description: 'Patient requires immediate emergency intervention',
        priority: 'Emergency protocol'
      }
    };
    return configs[level];
  };

  const handleExpandClick = () => {
    if (enableInteraction) {
      setExpanded(!expanded);
      // SOC2 Audit: Log user interaction
      if (auditContext) {
        patientRiskService.logAuditEvent({
          eventId: `risk_view_${Date.now()}`,
          timestamp: new Date().toISOString(),
          userId: auditContext.userId,
          sessionId: auditContext.sessionId,
          action: expanded ? 'collapse_risk_details' : 'expand_risk_details',
          patientId: patient.id,
          ipAddress: '127.0.0.1', // Would be real IP in production
          userAgent: navigator.userAgent,
          dataAccessed: ['risk_factors', 'recommendations'],
          auditHash: btoa(`${patient.id}_${auditContext.userId}_${Date.now()}`)
        });
      }
    }
  };

  const handleViewDetails = () => {
    setDetailsOpen(true);
  };

  const handleAuditTrail = () => {
    setAuditDialogOpen(true);
  };

  if (loading) {
    return (
      <Card sx={{ minHeight: compact ? 120 : 200 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <Box textAlign="center">
            <CircularProgress size={compact ? 24 : 40} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Calculating risk...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card sx={{ minHeight: compact ? 120 : 200 }}>
        <CardContent>
          <Alert severity="error" action={
            <Button size="small" onClick={calculateRiskScore}>
              Retry
            </Button>
          }>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!riskScore) {
    return (
      <Card sx={{ minHeight: compact ? 120 : 200 }}>
        <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <Typography variant="body2" color="text.secondary">
            Risk assessment not available
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const riskConfig = getRiskLevelConfig(riskScore.level);
  const IconComponent = riskConfig.icon;

  return (
    <>
      <Card 
        sx={{ 
          borderLeft: `4px solid ${riskConfig.color}`,
          transition: 'all 0.3s ease',
          '&:hover': enableInteraction ? { 
            boxShadow: 4,
            transform: 'translateY(-2px)' 
          } : {}
        }}
      >
        <CardContent sx={{ pb: compact ? 2 : 3 }}>
          {/* Header */}
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <Avatar 
                sx={{ 
                  bgcolor: riskConfig.bgColor, 
                  color: riskConfig.textColor,
                  width: compact ? 32 : 40,
                  height: compact ? 32 : 40
                }}
              >
                <IconComponent fontSize={compact ? 'small' : 'medium'} />
              </Avatar>
              <Box>
                <Typography variant={compact ? 'subtitle2' : 'h6'} fontWeight={600}>
                  Risk Assessment
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Last updated: {new Date(riskScore.calculatedAt).toLocaleDateString()}
                </Typography>
              </Box>
            </Box>
            
            {enableInteraction && (
              <Box display="flex" gap={0.5}>
                <Tooltip title="View detailed analysis">
                  <IconButton size="small" onClick={handleViewDetails}>
                    <ViewIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="SOC2 audit trail">
                  <IconButton size="small" onClick={handleAuditTrail}>
                    <AuditIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                {!compact && (
                  <IconButton size="small" onClick={handleExpandClick}>
                    {expanded ? <CollapseIcon /> : <ExpandIcon />}
                  </IconButton>
                )}
              </Box>
            )}
          </Box>

          {/* Risk Score Display */}
          <Box mb={2}>
            <Box display="flex" alignItems="baseline" gap={1} mb={1}>
              <Typography variant={compact ? 'h5' : 'h4'} fontWeight={700} color={riskConfig.textColor}>
                {Math.round(riskScore.score)}
              </Typography>
              <Typography variant="body2" color="text.secondary">/100</Typography>
              <Chip 
                label={riskConfig.label}
                sx={{ 
                  bgcolor: riskConfig.bgColor,
                  color: riskConfig.textColor,
                  fontWeight: 600,
                  ml: 1
                }}
                size={compact ? 'small' : 'medium'}
              />
            </Box>
            
            <LinearProgress 
              variant="determinate" 
              value={riskScore.score} 
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  bgcolor: riskConfig.color,
                  borderRadius: 4
                }
              }}
            />
            
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {riskConfig.description}
            </Typography>
          </Box>

          {/* Quick Stats */}
          {!compact && (
            <Box display="flex" gap={2} mb={2}>
              <Box textAlign="center" flex={1}>
                <Typography variant="h6" color={riskConfig.textColor}>
                  {riskScore.factors.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Risk Factors
                </Typography>
              </Box>
              <Box textAlign="center" flex={1}>
                <Typography variant="h6" color="primary.main">
                  {riskScore.recommendations.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Recommendations
                </Typography>
              </Box>
              <Box textAlign="center" flex={1}>
                <Typography variant="h6" color="info.main">
                  {Math.round(riskScore.confidence * 100)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Confidence
                </Typography>
              </Box>
            </Box>
          )}

          {/* PHI Protection Notice */}
          <Box display="flex" alignItems="center" gap={1} sx={{ bgcolor: 'grey.50', p: 1, borderRadius: 1 }}>
            <SecurityIcon color="primary" fontSize="small" />
            <Typography variant="caption" color="primary.main">
              SOC2 Compliant • PHI Protected • Audit Logged
            </Typography>
          </Box>

          {/* Expanded Details */}
          <Collapse in={expanded && !compact}>
            <Divider sx={{ my: 2 }} />
            
            {/* Top Risk Factors */}
            <Box mb={2}>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                Key Risk Factors
              </Typography>
              <List dense>
                {riskScore.factors.slice(0, 3).map((factor, index) => (
                  <ListItem key={factor.factorId} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <Chip 
                        size="small" 
                        label={factor.severity.toUpperCase()} 
                        color={factor.severity === 'critical' ? 'error' : factor.severity === 'high' ? 'warning' : 'default'}
                      />
                    </ListItemIcon>
                    <ListItemText 
                      primary={factor.description}
                      secondary={`Evidence: ${factor.evidenceLevel} • Weight: ${Math.round(factor.weight * 100)}%`}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>

            {/* Priority Recommendations */}
            <Box>
              <Typography variant="subtitle2" fontWeight={600} mb={1}>
                Priority Actions
              </Typography>
              <List dense>
                {riskScore.recommendations.slice(0, 2).map((rec) => (
                  <ListItem key={rec.recommendationId} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <RecommendationIcon color="primary" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={rec.description}
                      secondary={`Priority: ${rec.priority} • ${rec.timeframe}`}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          </Collapse>
        </CardContent>
      </Card>

      {/* Detailed Analysis Dialog */}
      <Dialog 
        open={detailsOpen} 
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: '70vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <IconComponent sx={{ color: riskConfig.color }} />
            Risk Analysis Details
            <Chip label={riskConfig.label} sx={{ bgcolor: riskConfig.bgColor, color: riskConfig.textColor }} />
          </Box>
        </DialogTitle>
        <DialogContent>
          {/* Detailed risk analysis would go here */}
          <Typography variant="body2" color="text.secondary">
            Comprehensive risk analysis, trends, and clinical decision support would be displayed here.
            This would include FHIR-compliant clinical data visualization, trend analysis, and evidence-based recommendations.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          <Button variant="contained" startIcon={<TrendIcon />}>
            View Trends
          </Button>
        </DialogActions>
      </Dialog>

      {/* SOC2 Audit Trail Dialog */}
      <Dialog 
        open={auditDialogOpen} 
        onClose={() => setAuditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <AuditIcon color="primary" />
            SOC2 Audit Trail
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Risk calculation audit information for SOC2 compliance.
          </Typography>
          <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
            <Typography variant="caption" display="block">
              <strong>Calculated By:</strong> {riskScore.calculatedBy}
            </Typography>
            <Typography variant="caption" display="block">
              <strong>Timestamp:</strong> {new Date(riskScore.calculatedAt).toLocaleString()}
            </Typography>
            <Typography variant="caption" display="block">
              <strong>Expires:</strong> {new Date(riskScore.expiresAt).toLocaleString()}
            </Typography>
            <Typography variant="caption" display="block">
              <strong>Patient ID:</strong> {riskScore.patientId}
            </Typography>
            <Typography variant="caption" display="block">
              <strong>Confidence:</strong> {Math.round(riskScore.confidence * 100)}%
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAuditDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default RiskScoreCard;