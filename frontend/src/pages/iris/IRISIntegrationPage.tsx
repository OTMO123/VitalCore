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
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  LinearProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Sync as SyncIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Api as ApiIcon,
  Shield as SecurityIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  ExpandMore as ExpandMoreIcon,
  NetworkCheck as NetworkCheckIcon,
  CloudSync as CloudSyncIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '@/store';
import { fetchIRISHealth } from '@/store/slices/irisSlice';

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

interface SyncOperation {
  id: string;
  type: string;
  status: 'running' | 'completed' | 'failed';
  startTime: string;
  endTime?: string;
  recordsProcessed: number;
  totalRecords: number;
  errors: number;
}

interface EndpointStatus {
  name: string;
  url: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime: number;
  lastCheck: string;
  uptime: number;
}

const IRISIntegrationPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { healthData, loading, error } = useAppSelector((state) => state.iris);
  
  const [tabValue, setTabValue] = useState(0);
  const [syncOperations, setSyncOperations] = useState<SyncOperation[]>([]);
  const [endpoints, setEndpoints] = useState<EndpointStatus[]>([]);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [manualSyncRunning, setManualSyncRunning] = useState(false);

  useEffect(() => {
    dispatch(fetchIRISHealth());
    
    // Mock data for sync operations
    setSyncOperations([
      {
        id: '1',
        type: 'Immunization Records Sync',
        status: 'completed',
        startTime: '2024-01-15T09:00:00Z',
        endTime: '2024-01-15T09:15:00Z',
        recordsProcessed: 1247,
        totalRecords: 1247,
        errors: 0,
      },
      {
        id: '2',
        type: 'Patient Demographics Sync',
        status: 'running',
        startTime: '2024-01-15T10:30:00Z',
        recordsProcessed: 834,
        totalRecords: 1500,
        errors: 2,
      },
      {
        id: '3',
        type: 'Provider Directory Sync',
        status: 'failed',
        startTime: '2024-01-15T08:00:00Z',
        endTime: '2024-01-15T08:05:00Z',
        recordsProcessed: 0,
        totalRecords: 250,
        errors: 1,
      },
    ]);

    // Mock endpoint status data
    setEndpoints([
      {
        name: 'Primary IRIS API',
        url: 'https://iris.api.primary.com/v1',
        status: 'healthy',
        responseTime: 145,
        lastCheck: '2024-01-15T10:45:00Z',
        uptime: 99.9,
      },
      {
        name: 'Backup IRIS API',
        url: 'https://iris.api.backup.com/v1',
        status: 'healthy',
        responseTime: 210,
        lastCheck: '2024-01-15T10:45:00Z',
        uptime: 98.5,
      },
      {
        name: 'IRIS Auth Service',
        url: 'https://iris.auth.com/oauth2',
        status: 'degraded',
        responseTime: 850,
        lastCheck: '2024-01-15T10:45:00Z',
        uptime: 97.2,
      },
    ]);
  }, [dispatch]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'completed':
        return 'success';
      case 'degraded':
      case 'running':
        return 'warning';
      case 'unhealthy':
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'completed':
        return <CheckCircleIcon />;
      case 'degraded':
      case 'running':
        return <WarningIcon />;
      case 'unhealthy':
      case 'failed':
        return <ErrorIcon />;
      default:
        return <CheckCircleIcon />;
    }
  };

  const handleManualSync = async () => {
    setManualSyncRunning(true);
    // Simulate manual sync operation
    setTimeout(() => {
      setManualSyncRunning(false);
      // Add new sync operation
      const newSync: SyncOperation = {
        id: Date.now().toString(),
        type: 'Manual Full Sync',
        status: 'completed',
        startTime: new Date().toISOString(),
        endTime: new Date().toISOString(),
        recordsProcessed: 2500,
        totalRecords: 2500,
        errors: 0,
      };
      setSyncOperations(prev => [newSync, ...prev]);
    }, 3000);
  };

  const handleRefreshHealth = () => {
    dispatch(fetchIRISHealth());
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600}>
          IRIS Integration
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshHealth}
            disabled={loading === 'loading'}
          >
            Refresh Status
          </Button>
          <Button
            variant="contained"
            startIcon={manualSyncRunning ? <CircularProgress size={16} /> : <SyncIcon />}
            onClick={handleManualSync}
            disabled={manualSyncRunning}
          >
            {manualSyncRunning ? 'Syncing...' : 'Manual Sync'}
          </Button>
        </Box>
      </Box>

      {/* System Status Overview */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <ApiIcon color="primary" />
                <Typography variant="h6">API Status</Typography>
              </Box>
              <Typography variant="h4" color="success.main" fontWeight={600}>
                Healthy
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All endpoints operational
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <CloudSyncIcon color="primary" />
                <Typography variant="h6">Last Sync</Typography>
              </Box>
              <Typography variant="h4" color="primary.main" fontWeight={600}>
                15m ago
              </Typography>
              <Typography variant="body2" color="text.secondary">
                1,247 records processed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <SecurityIcon color="primary" />
                <Typography variant="h6">Security</Typography>
              </Box>
              <Typography variant="h4" color="success.main" fontWeight={600}>
                Secure
              </Typography>
              <Typography variant="body2" color="text.secondary">
                OAuth2 + HMAC active
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <TimelineIcon color="primary" />
                <Typography variant="h6">Uptime</Typography>
              </Box>
              <Typography variant="h4" color="success.main" fontWeight={600}>
                99.9%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                30-day average
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Sync Operations" icon={<SyncIcon />} />
          <Tab label="Endpoints Health" icon={<NetworkCheckIcon />} />
          <Tab label="Configuration" icon={<SettingsIcon />} />
          <Tab label="Security & Auth" icon={<SecurityIcon />} />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={tabValue} index={0}>
        <Card>
          <CardHeader title="Synchronization Operations" />
          <CardContent>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Operation Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Start Time</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Errors</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {syncOperations.map((operation) => {
                    const progress = (operation.recordsProcessed / operation.totalRecords) * 100;
                    const duration = operation.endTime
                      ? Math.round((new Date(operation.endTime).getTime() - new Date(operation.startTime).getTime()) / 60000)
                      : 'In progress';

                    return (
                      <TableRow key={operation.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {operation.type}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getStatusIcon(operation.status)}
                            label={operation.status.charAt(0).toUpperCase() + operation.status.slice(1)}
                            color={getStatusColor(operation.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ minWidth: 120 }}>
                            <LinearProgress
                              variant="determinate"
                              value={progress}
                              color={operation.status === 'failed' ? 'error' : 'primary'}
                              sx={{ mb: 1 }}
                            />
                            <Typography variant="caption">
                              {operation.recordsProcessed} / {operation.totalRecords} records
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          {new Date(operation.startTime).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          {typeof duration === 'number' ? `${duration}m` : duration}
                        </TableCell>
                        <TableCell>
                          {operation.errors > 0 ? (
                            <Chip label={operation.errors} color="error" size="small" />
                          ) : (
                            '0'
                          )}
                        </TableCell>
                        <TableCell>
                          <IconButton size="small">
                            <SettingsIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          {endpoints.map((endpoint, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card>
                <CardHeader
                  title={endpoint.name}
                  action={
                    <Chip
                      icon={getStatusIcon(endpoint.status)}
                      label={endpoint.status.charAt(0).toUpperCase() + endpoint.status.slice(1)}
                      color={getStatusColor(endpoint.status)}
                      size="small"
                    />
                  }
                />
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {endpoint.url}
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Response Time
                      </Typography>
                      <Typography variant="h6" color={endpoint.responseTime > 500 ? 'warning.main' : 'success.main'}>
                        {endpoint.responseTime}ms
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Uptime (30d)
                      </Typography>
                      <Typography variant="h6" color="success.main">
                        {endpoint.uptime}%
                      </Typography>
                    </Grid>
                  </Grid>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                    Last checked: {new Date(endpoint.lastCheck).toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Sync Configuration" />
              <CardContent>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Auto Sync Interval"
                      secondary="Every 15 minutes"
                    />
                    <Button size="small" variant="outlined" onClick={() => setConfigDialogOpen(true)}>
                      Edit
                    </Button>
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Retry Policy"
                      secondary="3 attempts with exponential backoff"
                    />
                    <Button size="small" variant="outlined">
                      Edit
                    </Button>
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Batch Size"
                      secondary="100 records per batch"
                    />
                    <Button size="small" variant="outlined">
                      Edit
                    </Button>
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Data Mapping" />
              <CardContent>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Patient Demographics</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary">
                      IRIS Patient → FHIR Patient resource mapping with PHI encryption
                    </Typography>
                  </AccordionDetails>
                </Accordion>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Immunization Records</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary">
                      IRIS Immunization → FHIR Immunization resource with CVX code mapping
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Authentication Status" />
              <CardContent>
                <Alert severity="success" sx={{ mb: 2 }}>
                  OAuth2 authentication active and tokens valid
                </Alert>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="OAuth2 Token"
                      secondary="Valid until: Jan 16, 2024 10:45 AM"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="HMAC Signatures"
                      secondary="All requests signed with SHA-256"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="TLS Encryption"
                      secondary="TLS 1.3 for all communications"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Security Monitoring" />
              <CardContent>
                <Typography variant="body2" color="text.secondary" paragraph>
                  All API requests are monitored for security compliance:
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="• Request/Response encryption" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="• PHI data masking in logs" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="• Failed authentication tracking" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="• Rate limiting protection" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onClose={() => setConfigDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Sync Configuration</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Sync Interval (minutes)"
            type="number"
            defaultValue={15}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Batch Size"
            type="number"
            defaultValue={100}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Retry Attempts"
            type="number"
            defaultValue={3}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setConfigDialogOpen(false)}>
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default IRISIntegrationPage;