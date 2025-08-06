import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Chip,
  Divider,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  CircularProgress,
  Avatar,
  IconButton,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Edit as EditIcon,
  Shield as SecurityIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Home as HomeIcon,
  CalendarToday as CalendarIcon,
  Assignment as AssignmentIcon,
  HealthAndSafety as HealthIcon,
  Schedule as TimelineIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '@/store';
import type { Patient } from '@/types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const PatientDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { currentPatient, loading, error } = useAppSelector((state) => state.patient);

  const [tabValue, setTabValue] = useState(0);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [clinicalDocuments, setClinicalDocuments] = useState<any[]>([]);

  useEffect(() => {
    if (id) {
      // Simulate fetching patient details, audit logs, and clinical documents
      setAuditLogs([
        {
          id: '1',
          action: 'Patient Record Accessed',
          user: 'Dr. Smith',
          timestamp: '2024-01-15T10:30:00Z',
          ip_address: '192.168.1.100',
        },
        {
          id: '2',
          action: 'PHI Data Viewed',
          user: 'Nurse Johnson',
          timestamp: '2024-01-14T14:20:00Z',
          ip_address: '192.168.1.101',
        },
      ]);

      setClinicalDocuments([
        {
          id: '1',
          title: 'Annual Physical Exam',
          type: 'Examination',
          date: '2024-01-10',
          provider: 'Dr. Smith',
          status: 'Final',
        },
        {
          id: '2',
          title: 'COVID-19 Vaccination Record',
          type: 'Immunization',
          date: '2023-12-15',
          provider: 'Nurse Wilson',
          status: 'Final',
        },
      ]);
    }
  }, [id]);

  if (loading === 'loading') {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 3 }}>
        {error}
      </Alert>
    );
  }

  if (!currentPatient) {
    return (
      <Alert severity="warning" sx={{ m: 3 }}>
        Patient not found.
      </Alert>
    );
  }

  const formatPatientName = (patient: Patient) => {
    if (patient.name && patient.name.length > 0) {
      const name = patient.name[0];
      return `${name.given?.join(' ') || ''} ${name.family || ''}`.trim();
    }
    return 'Unknown Patient';
  };

  const getPatientMRN = (patient: Patient) => {
    const mrnIdentifier = patient.identifier?.find(id => id.type?.coding?.[0]?.code === 'MR');
    return mrnIdentifier?.value || 'N/A';
  };

  const getConsentStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'success';
      case 'expired':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Header Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main' }}>
              <PersonIcon fontSize="large" />
            </Avatar>
            <Box>
              <Typography variant="h4" fontWeight={600}>
                {formatPatientName(currentPatient)}
              </Typography>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                MRN: {getPatientMRN(currentPatient)}
              </Typography>
              <Box display="flex" gap={1} alignItems="center">
                <Chip
                  label={currentPatient.consent_status || 'Unknown'}
                  color={getConsentStatusColor(currentPatient.consent_status || '')}
                  size="small"
                />
                <Chip
                  icon={<SecurityIcon />}
                  label="PHI Protected"
                  color="primary"
                  variant="outlined"
                  size="small"
                />
              </Box>
            </Box>
          </Box>
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/patients/${id}/edit`)}
          >
            Edit Patient
          </Button>
        </Box>
      </Paper>

      {/* Tabs Navigation */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Overview" icon={<PersonIcon />} />
          <Tab label="Clinical Documents" icon={<AssignmentIcon />} />
          <Tab label="Immunizations" icon={<HealthIcon />} />
          <Tab label="Timeline" icon={<TimelineIcon />} />
          <Tab label="Audit Trail" icon={<HistoryIcon />} />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          {/* Demographics */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Demographics" />
              <CardContent>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <CalendarIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Date of Birth"
                      secondary={currentPatient.birthDate || 'Not provided'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <PersonIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Gender"
                      secondary={currentPatient.gender || 'Not specified'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <PhoneIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Phone"
                      secondary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <SecurityIcon fontSize="small" color="primary" />
                          <Typography variant="body2" color="primary.main">
                            Encrypted - Access Logged
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <EmailIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Email"
                      secondary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <SecurityIcon fontSize="small" color="primary" />
                          <Typography variant="body2" color="primary.main">
                            Encrypted - Access Logged
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <HomeIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Address"
                      secondary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <SecurityIcon fontSize="small" color="primary" />
                          <Typography variant="body2" color="primary.main">
                            Encrypted - Access Logged
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Patient Status */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Patient Status" />
              <CardContent>
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Active Status
                  </Typography>
                  <Chip
                    label={currentPatient.active ? 'Active' : 'Inactive'}
                    color={currentPatient.active ? 'success' : 'default'}
                  />
                </Box>
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Consent Status
                  </Typography>
                  <Chip
                    label={currentPatient.consent_status || 'Unknown'}
                    color={getConsentStatusColor(currentPatient.consent_status || '')}
                  />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    FHIR Resource Type
                  </Typography>
                  <Chip
                    label={currentPatient.resourceType}
                    variant="outlined"
                    color="primary"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Card>
          <CardHeader title="Clinical Documents" />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Document Title</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Provider</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {clinicalDocuments.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell>{doc.title}</TableCell>
                      <TableCell>{doc.type}</TableCell>
                      <TableCell>{doc.date}</TableCell>
                      <TableCell>{doc.provider}</TableCell>
                      <TableCell>
                        <Chip label={doc.status} color="success" size="small" />
                      </TableCell>
                      <TableCell>
                        <Button size="small" variant="outlined">
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Card>
          <CardHeader title="Immunization Records" />
          <CardContent>
            <Alert severity="info" sx={{ mb: 2 }}>
              Immunization data is synchronized with IRIS API system.
            </Alert>
            <Typography variant="body2" color="text.secondary">
              No immunization records found. Data will be populated from IRIS integration.
            </Typography>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Card>
          <CardHeader title="Patient Timeline" />
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              GitBranch as Timeline view showing patient interactions, appointments, and medical events will be displayed here.
            </Typography>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        <Card>
          <CardHeader title="PHI Access Audit Trail" />
          <CardContent>
            <Alert severity="warning" sx={{ mb: 2 }}>
              All access to Protected Health Information is logged for compliance.
            </Alert>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Action</TableCell>
                    <TableCell>User</TableCell>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>IP Address</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {auditLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>{log.action}</TableCell>
                      <TableCell>{log.user}</TableCell>
                      <TableCell>
                        {new Date(log.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>{log.ip_address}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default PatientDetailPage;