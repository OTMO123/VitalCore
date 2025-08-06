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
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Shield as SecurityIcon,
  Gavel as GavelIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  Shield as ShieldIcon,
  VerifiedUser as VerifiedUserIcon,
  Policy as PolicyIcon,
  Visibility as VisibilityIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';

interface ComplianceFramework {
  id: string;
  name: string;
  description: string;
  status: 'compliant' | 'partial' | 'non-compliant';
  score: number;
  lastAudit: string;
  nextAudit: string;
  controls: ComplianceControl[];
}

interface ComplianceControl {
  id: string;
  title: string;
  description: string;
  status: 'implemented' | 'partial' | 'not-implemented';
  evidence: string[];
  lastReview: string;
}

const CompliancePage: React.FC = () => {
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([]);
  const [selectedFramework, setSelectedFramework] = useState<ComplianceFramework | null>(null);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [reportType, setReportType] = useState('');

  useEffect(() => {
    // Mock compliance frameworks data
    setFrameworks([
      {
        id: 'hipaa',
        name: 'HIPAA',
        description: 'Health Insurance Portability and Accountability Act',
        status: 'compliant',
        score: 98,
        lastAudit: '2024-01-01',
        nextAudit: '2024-07-01',
        controls: [
          {
            id: 'hipaa-164.502',
            title: 'Uses and Disclosures of PHI',
            description: 'Standards for uses and disclosures of protected health information',
            status: 'implemented',
            evidence: ['Access control policies', 'Audit logs', 'Staff training records'],
            lastReview: '2024-01-15',
          },
          {
            id: 'hipaa-164.312',
            title: 'Technical Safeguards',
            description: 'Technology controls for PHI access',
            status: 'implemented',
            evidence: ['Encryption documentation', 'Access logs', 'System configurations'],
            lastReview: '2024-01-10',
          },
        ],
      },
      {
        id: 'soc2',
        name: 'SOC2 Type II',
        description: 'Service Organization Control 2',
        status: 'compliant',
        score: 96,
        lastAudit: '2023-12-15',
        nextAudit: '2024-06-15',
        controls: [
          {
            id: 'soc2-cc6.1',
            title: 'Logical Access Controls',
            description: 'Controls over logical access to systems and data',
            status: 'implemented',
            evidence: ['IAM policies', 'MFA implementation', 'Access reviews'],
            lastReview: '2024-01-12',
          },
          {
            id: 'soc2-cc6.7',
            title: 'Data Transmission',
            description: 'Controls over data transmission',
            status: 'partial',
            evidence: ['TLS configuration', 'Encryption standards'],
            lastReview: '2024-01-08',
          },
        ],
      },
      {
        id: 'iso27001',
        name: 'ISO 27001',
        description: 'Information Security Management System',
        status: 'partial',
        score: 87,
        lastAudit: '2023-11-20',
        nextAudit: '2024-05-20',
        controls: [
          {
            id: 'iso-a.9.1.1',
            title: 'Access Control Policy',
            description: 'Access control policy and procedures',
            status: 'implemented',
            evidence: ['Access control policy', 'Role definitions', 'Access reviews'],
            lastReview: '2024-01-05',
          },
          {
            id: 'iso-a.12.3.1',
            title: 'Information Backup',
            description: 'Information backup procedures',
            status: 'not-implemented',
            evidence: [],
            lastReview: '2023-12-01',
          },
        ],
      },
    ]);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
      case 'implemented':
        return 'success';
      case 'partial':
        return 'warning';
      case 'non-compliant':
      case 'not-implemented':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
      case 'implemented':
        return <CheckCircleIcon />;
      case 'partial':
        return <WarningIcon />;
      case 'non-compliant':
      case 'not-implemented':
        return <ErrorIcon />;
      default:
        return <CheckCircleIcon />;
    }
  };

  const handleGenerateReport = (frameworkId: string) => {
    setReportType(frameworkId);
    setReportDialogOpen(true);
  };

  const overallCompliance = Math.round(
    frameworks.reduce((sum, framework) => sum + framework.score, 0) / frameworks.length
  );

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600}>
          Compliance Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AssessmentIcon />}
          onClick={() => setReportDialogOpen(true)}
        >
          Generate Report
        </Button>
      </Box>

      {/* Overall Compliance Score */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={3}>
            <Box textAlign="center">
              <Typography variant="h2" color="primary.main" fontWeight={600}>
                {overallCompliance}%
              </Typography>
              <Typography variant="h6" color="text.secondary">
                Overall Compliance Score
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={9}>
            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body2" fontWeight={500}>
                  Compliance Progress
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {overallCompliance}% Complete
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={overallCompliance}
                color={overallCompliance >= 95 ? 'success' : overallCompliance >= 80 ? 'warning' : 'error'}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
            <Alert severity={overallCompliance >= 95 ? 'success' : 'warning'} sx={{ mt: 2 }}>
              {overallCompliance >= 95
                ? 'All compliance frameworks are within acceptable thresholds.'
                : 'Some compliance areas require attention to maintain certification standards.'}
            </Alert>
          </Grid>
        </Grid>
      </Paper>

      {/* Compliance Frameworks */}
      <Grid container spacing={3} mb={3}>
        {frameworks.map((framework) => (
          <Grid item xs={12} md={4} key={framework.id}>
            <Card>
              <CardHeader
                title={framework.name}
                subheader={framework.description}
                action={
                  <Chip
                    icon={getStatusIcon(framework.status)}
                    label={framework.status.replace('-', ' ').toUpperCase()}
                    color={getStatusColor(framework.status)}
                    size="small"
                  />
                }
              />
              <CardContent>
                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2" fontWeight={500}>
                      Compliance Score
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {framework.score}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={framework.score}
                    color={getStatusColor(framework.status)}
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                </Box>
                <Divider sx={{ my: 2 }} />
                <List dense>
                  <ListItem disablePadding>
                    <ListItemIcon>
                      <ScheduleIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Last Audit"
                      secondary={new Date(framework.lastAudit).toLocaleDateString()}
                    />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemIcon>
                      <ScheduleIcon fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Next Audit"
                      secondary={new Date(framework.nextAudit).toLocaleDateString()}
                    />
                  </ListItem>
                </List>
                <Box mt={2} display="flex" gap={1}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => setSelectedFramework(framework)}
                  >
                    View Details
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={() => handleGenerateReport(framework.id)}
                  >
                    Report
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Compliance Controls Detail */}
      {selectedFramework && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5" fontWeight={600}>
              {selectedFramework.name} Controls
            </Typography>
            <Button
              variant="outlined"
              onClick={() => setSelectedFramework(null)}
            >
              Close Details
            </Button>
          </Box>
          
          {selectedFramework.controls.map((control) => (
            <Accordion key={control.id}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" width="100%">
                  <Box mr={2}>
                    {getStatusIcon(control.status)}
                  </Box>
                  <Box flexGrow={1}>
                    <Typography variant="body1" fontWeight={500}>
                      {control.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {control.id}
                    </Typography>
                  </Box>
                  <Chip
                    label={control.status.replace('-', ' ')}
                    color={getStatusColor(control.status)}
                    size="small"
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {control.description}
                </Typography>
                <Typography variant="body2" fontWeight={500} gutterBottom>
                  Evidence:
                </Typography>
                <List dense>
                  {control.evidence.map((evidence, index) => (
                    <ListItem key={index} disablePadding>
                      <ListItemIcon>
                        <VerifiedUserIcon fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText primary={evidence} />
                    </ListItem>
                  ))}
                </List>
                <Typography variant="caption" color="text.secondary">
                  Last reviewed: {new Date(control.lastReview).toLocaleDateString()}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))}
        </Paper>
      )}

      {/* Quick Actions */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Security Policies"
              avatar={<PolicyIcon color="primary" />}
            />
            <CardContent>
              <Typography variant="body2" color="text.secondary" paragraph>
                Access security policies, procedures, and documentation for compliance frameworks.
              </Typography>
              <Button variant="outlined" startIcon={<VisibilityIcon />}>
                View Policies
              </Button>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Risk Assessments"
              avatar={<ShieldIcon color="primary" />}
            />
            <CardContent>
              <Typography variant="body2" color="text.secondary" paragraph>
                Review risk assessments and mitigation strategies for identified security risks.
              </Typography>
              <Button variant="outlined" startIcon={<AssessmentIcon />}>
                View Assessments
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Report Generation Dialog */}
      <Dialog open={reportDialogOpen} onClose={() => setReportDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate Compliance Report</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Generate a comprehensive compliance report for auditors and stakeholders.
          </Typography>
          <TextField
            fullWidth
            label="Report Title"
            defaultValue={`${reportType ? frameworks.find(f => f.id === reportType)?.name : 'Overall'} Compliance Report`}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Report Period"
            defaultValue="Last 12 months"
            margin="normal"
          />
          <TextField
            fullWidth
            label="Recipient Email"
            type="email"
            placeholder="auditor@company.com"
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReportDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => {
              console.log('Generating compliance report...');
              setReportDialogOpen(false);
            }}
          >
            Generate Report
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CompliancePage;