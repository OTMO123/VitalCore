import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  LinearProgress,
  Avatar,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Shield as ShieldIcon,
  Shield as SecurityIcon,
  VerifiedUser as VerifiedIcon,
  Policy as PolicyIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

// ============================================
// COMPLIANCE OVERVIEW CARD COMPONENT
// ============================================

interface ComplianceOverviewCardProps {
  complianceScore: number;
  loading?: boolean;
  onRefresh?: () => void;
}

const ComplianceOverviewCard: React.FC<ComplianceOverviewCardProps> = ({
  complianceScore,
  loading = false,
  onRefresh,
}) => {
  const complianceData = [
    {
      standard: 'HIPAA',
      score: 99.2,
      status: 'compliant',
      icon: <ShieldIcon />,
      color: 'success.main',
      requirements: ['PHI Encryption', 'Access Controls', 'Audit Logging', 'Patient Consent'],
    },
    {
      standard: 'SOC2 Type II',
      score: 98.5,
      status: 'compliant',
      icon: <SecurityIcon />,
      color: 'success.main',
      requirements: ['Security Controls', 'Availability', 'Processing Integrity', 'Confidentiality'],
    },
    {
      standard: 'FHIR R4',
      score: 97.8,
      status: 'compliant',
      icon: <VerifiedIcon />,
      color: 'success.main',
      requirements: ['Resource Validation', 'Profile Conformance', 'Terminology', 'Security'],
    },
    {
      standard: 'GDPR',
      score: 96.1,
      status: 'compliant',
      icon: <PolicyIcon />,
      color: 'warning.main',
      requirements: ['Data Protection', 'Consent Management', 'Right to be Forgotten', 'Data Portability'],
    },
  ];

  const getScoreColor = (score: number) => {
    if (score >= 98) return 'success';
    if (score >= 95) return 'warning';
    return 'error';
  };

  const getStatusChip = (status: string, score: number) => {
    const color = getScoreColor(score);
    return (
      <Chip
        label={status.toUpperCase()}
        size="small"
        color={color as any}
        sx={{ fontWeight: 600, fontSize: '0.625rem' }}
      />
    );
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
          <Box display="flex" alignItems="center">
            <Avatar sx={{ bgcolor: 'success.main', mr: 2, width: 48, height: 48 }}>
              <AssessmentIcon />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                Compliance Overview
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Regulatory compliance status and scores
              </Typography>
            </Box>
          </Box>
          
          <Box display="flex" alignItems="center">
            <Box textAlign="right" mr={2}>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {complianceScore}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Overall Score
              </Typography>
            </Box>
            
            {onRefresh && (
              <Tooltip title="Refresh compliance data">
                <IconButton 
                  onClick={onRefresh} 
                  disabled={loading} 
                  size="small"
                  aria-label="Refresh compliance data"
                >
                  <RefreshIcon sx={{ 
                    animation: loading ? 'spin 1s linear infinite' : 'none',
                    '@keyframes spin': {
                      '0%': { transform: 'rotate(0deg)' },
                      '100%': { transform: 'rotate(360deg)' },
                    }
                  }} />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        <Grid container spacing={3}>
          {complianceData.map((compliance) => (
            <Grid item xs={12} md={6} key={compliance.standard}>
              <Box
                p={2}
                border={1}
                borderColor="divider"
                borderRadius={2}
                sx={{
                  backgroundColor: 'background.paper',
                  transition: 'box-shadow 0.2s ease-in-out',
                  '&:hover': {
                    boxShadow: 2,
                  },
                }}
              >
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Box display="flex" alignItems="center">
                    <Avatar
                      sx={{
                        bgcolor: compliance.color,
                        width: 32,
                        height: 32,
                        mr: 2,
                      }}
                    >
                      {compliance.icon}
                    </Avatar>
                    <Typography variant="h6" fontWeight={600}>
                      {compliance.standard}
                    </Typography>
                  </Box>
                  {getStatusChip(compliance.status, compliance.score)}
                </Box>

                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2" color="text.secondary">
                      Compliance Score
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {compliance.score}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={compliance.score}
                    color={getScoreColor(compliance.score) as any}
                    sx={{ height: 6, borderRadius: 3 }}
                    aria-label={`${compliance.standard} compliance score: ${compliance.score}%`}
                  />
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary" mb={1}>
                    Key Requirements:
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5}>
                    {compliance.requirements.map((requirement) => (
                      <Chip
                        key={requirement}
                        label={requirement}
                        size="small"
                        variant="outlined"
                        sx={{ 
                          fontSize: '0.625rem',
                          height: 20,
                          borderColor: compliance.color,
                          color: compliance.color,
                        }}
                      />
                    ))}
                  </Box>
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>

        <Box mt={3} p={2} bgcolor="info.light" borderRadius={1}>
          <Typography variant="body2" color="info.dark" fontWeight={500}>
            📋 Compliance Status: All critical requirements are met. Regular audits and monitoring ensure continuous compliance.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ComplianceOverviewCard;