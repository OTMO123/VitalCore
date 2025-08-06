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
  TextField,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  DatePicker,
  CircularProgress,
  Tooltip,
  Badge,
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker as MUIDatePicker } from '@mui/x-date-pickers/DatePicker';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Shield as SecurityIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Error as ErrorIcon,
  Person as PersonIcon,
  Visibility as VisibilityIcon,
  MoreVert as MoreVertIcon,
  Shield as ShieldIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Gavel as GavelIcon,
} from '@mui/icons-material';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_name: string;
  action: string;
  resource_type: string;
  resource_id: string;
  ip_address: string;
  user_agent: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  details: Record<string, any>;
  correlation_id: string;
}

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

const AuditLogsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [actionFilter, setActionFilter] = useState('all');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
    end: new Date(),
  });
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  useEffect(() => {
    setLoading(true);
    // Mock audit log data
    setTimeout(() => {
      setAuditLogs([
        {
          id: '1',
          timestamp: '2024-01-15T10:45:32Z',
          user_id: 'u123',
          user_name: 'Dr. Sarah Johnson',
          action: 'PHI_ACCESS',
          resource_type: 'Patient',
          resource_id: 'P001',
          ip_address: '192.168.1.100',
          user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          severity: 'info',
          details: { patient_name: 'John Doe', fields_accessed: ['ssn', 'address'] },
          correlation_id: 'req-12345',
        },
        {
          id: '2',
          timestamp: '2024-01-15T10:42:15Z',
          user_id: 'u456',
          user_name: 'Nurse Williams',
          action: 'PATIENT_UPDATE',
          resource_type: 'Patient',
          resource_id: 'P002',
          ip_address: '192.168.1.105',
          user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
          severity: 'info',
          details: { changes: { consent_status: 'active' } },
          correlation_id: 'req-12346',
        },
        {
          id: '3',
          timestamp: '2024-01-15T10:38:45Z',
          user_id: 'u789',
          user_name: 'Admin User',
          action: 'FAILED_LOGIN',
          resource_type: 'Authentication',
          resource_id: 'auth-001',
          ip_address: '203.0.113.42',
          user_agent: 'Python-requests/2.28.1',
          severity: 'warning',
          details: { reason: 'Invalid credentials', attempts: 3 },
          correlation_id: 'req-12347',
        },
        {
          id: '4',
          timestamp: '2024-01-15T10:35:22Z',
          user_id: 'system',
          user_name: 'System',
          action: 'DATA_EXPORT',
          resource_type: 'HealthcareRecord',
          resource_id: 'batch-001',
          ip_address: '127.0.0.1',
          user_agent: 'Internal System',
          severity: 'info',
          details: { export_type: 'anonymized', record_count: 150 },
          correlation_id: 'req-12348',
        },
        {
          id: '5',
          timestamp: '2024-01-15T10:30:10Z',
          user_id: 'u123',
          user_name: 'Dr. Sarah Johnson',
          action: 'ENCRYPTION_ERROR',
          resource_type: 'Patient',
          resource_id: 'P003',
          ip_address: '192.168.1.100',
          user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          severity: 'error',
          details: { error: 'Key rotation failed', retry_count: 2 },
          correlation_id: 'req-12349',
        },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'info':
        return 'info';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'info':
        return <InfoIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'error':
      case 'critical':
        return <ErrorIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, log: AuditLogEntry) => {
    setAnchorEl(event.currentTarget);
    setSelectedLog(log);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedLog(null);
  };

  const filteredLogs = auditLogs.filter(log => {
    const matchesSearch = searchTerm === '' || 
      log.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.resource_type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesSeverity = severityFilter === 'all' || log.severity === severityFilter;
    const matchesAction = actionFilter === 'all' || log.action === actionFilter;
    
    return matchesSearch && matchesSeverity && matchesAction;
  });

  const paginatedLogs = filteredLogs.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  const auditStats = {
    total: auditLogs.length,
    critical: auditLogs.filter(log => log.severity === 'critical').length,
    errors: auditLogs.filter(log => log.severity === 'error').length,
    warnings: auditLogs.filter(log => log.severity === 'warning').length,
    phiAccess: auditLogs.filter(log => log.action === 'PHI_ACCESS').length,
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" fontWeight={600}>
            Audit Logs & Security Monitoring
          </Typography>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => console.log('Export audit logs')}
            >
              Export Logs
            </Button>
            <Button
              variant="contained"
              startIcon={<AssessmentIcon />}
              onClick={() => console.log('Generate compliance report')}
            >
              Compliance Report
            </Button>
          </Box>
        </Box>

        {/* Statistics Overview */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} md={2.4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <ShieldIcon color="primary" />
                  <Typography variant="h6">Total Events</Typography>
                </Box>
                <Typography variant="h4" color="primary.main" fontWeight={600}>
                  {auditStats.total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 7 days
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <SecurityIcon color="primary" />
                  <Typography variant="h6">PHI Access</Typography>
                </Box>
                <Typography variant="h4" color="info.main" fontWeight={600}>
                  {auditStats.phiAccess}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  All logged & encrypted
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <WarningIcon color="warning" />
                  <Typography variant="h6">Warnings</Typography>
                </Box>
                <Typography variant="h4" color="warning.main" fontWeight={600}>
                  {auditStats.warnings}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Require attention
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <ErrorIcon color="error" />
                  <Typography variant="h6">Errors</Typography>
                </Box>
                <Typography variant="h4" color="error.main" fontWeight={600}>
                  {auditStats.errors}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Need investigation
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={2.4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <GavelIcon color="primary" />
                  <Typography variant="h6">Compliance</Typography>
                </Box>
                <Typography variant="h4" color="success.main" fontWeight={600}>
                  100%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  SOC2 + HIPAA
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={tabValue}
            onChange={(_, newValue) => setTabValue(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="Audit Logs" icon={<TimelineIcon />} />
            <Tab label="Security Events" icon={<SecurityIcon />} />
            <Tab label="PHI Access Logs" icon={<PersonIcon />} />
            <Tab label="Compliance Reports" icon={<GavelIcon />} />
          </Tabs>
        </Paper>

        {/* Tab Content */}
        <TabPanel value={tabValue} index={0}>
          {/* Filters */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  placeholder="Search logs by user, action, or resource..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Severity</InputLabel>
                  <Select
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value)}
                    label="Severity"
                  >
                    <MenuItem value="all">All Levels</MenuItem>
                    <MenuItem value="info">Info</MenuItem>
                    <MenuItem value="warning">Warning</MenuItem>
                    <MenuItem value="error">Error</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Action</InputLabel>
                  <Select
                    value={actionFilter}
                    onChange={(e) => setActionFilter(e.target.value)}
                    label="Action"
                  >
                    <MenuItem value="all">All Actions</MenuItem>
                    <MenuItem value="PHI_ACCESS">PHI Access</MenuItem>
                    <MenuItem value="PATIENT_UPDATE">Patient Update</MenuItem>
                    <MenuItem value="FAILED_LOGIN">Failed Login</MenuItem>
                    <MenuItem value="DATA_EXPORT">Data Export</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <MUIDatePicker
                  label="Start Date"
                  value={dateRange.start}
                  onChange={(date) => setDateRange(prev => ({ ...prev, start: date || new Date() }))}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <MUIDatePicker
                  label="End Date"
                  value={dateRange.end}
                  onChange={(date) => setDateRange(prev => ({ ...prev, end: date || new Date() }))}
                />
              </Grid>
            </Grid>
          </Paper>

          {/* Audit Logs Table */}
          <Paper>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>User</TableCell>
                    <TableCell>Action</TableCell>
                    <TableCell>Resource</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>IP Address</TableCell>
                    <TableCell>Details</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                        <CircularProgress />
                      </TableCell>
                    </TableRow>
                  ) : paginatedLogs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                        <Typography variant="body2" color="text.secondary">
                          No audit logs found matching your filters.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedLogs.map((log) => (
                      <TableRow key={log.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {new Date(log.timestamp).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {log.user_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ID: {log.user_id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {log.action.replace(/_/g, ' ')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {log.resource_type}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {log.resource_id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getSeverityIcon(log.severity)}
                            label={log.severity.toUpperCase()}
                            color={getSeverityColor(log.severity)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {log.ip_address}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Tooltip title={JSON.stringify(log.details, null, 2)}>
                            <Chip
                              label="View Details"
                              variant="outlined"
                              size="small"
                              clickable
                            />
                          </Tooltip>
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={(e) => handleMenuOpen(e, log)}
                          >
                            <MoreVertIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Pagination */}
            <TablePagination
              component="div"
              count={filteredLogs.length}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
              rowsPerPageOptions={[10, 25, 50, 100]}
            />
          </Paper>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Alert severity="warning" sx={{ mb: 3 }}>
            Security events require immediate attention and are automatically escalated.
          </Alert>
          <Card>
            <CardHeader title="Recent Security Events" />
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Security events including failed logins, suspicious access patterns, and encryption errors are displayed here.
                All events are automatically logged and investigated.
              </Typography>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Alert severity="info" sx={{ mb: 3 }}>
            All PHI access is tracked for HIPAA compliance. Access is logged with user, timestamp, and specific fields accessed.
          </Alert>
          <Card>
            <CardHeader title="Protected Health Information Access Logs" />
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Detailed logs of all PHI access including patient records, clinical documents, and encrypted fields.
                Every access is cryptographically signed and immutable.
              </Typography>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="HIPAA Compliance Report" />
                <CardContent>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Generate comprehensive HIPAA compliance reports including PHI access logs,
                    security measures, and audit trail documentation.
                  </Typography>
                  <Button variant="contained" size="small">
                    Generate HIPAA Report
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="SOC2 Type II Report" />
                <CardContent>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Security controls documentation and operational effectiveness evidence
                    for SOC2 Type II compliance audits.
                  </Typography>
                  <Button variant="contained" size="small">
                    Generate SOC2 Report
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Actions Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleMenuClose}>
            <VisibilityIcon sx={{ mr: 1 }} fontSize="small" />
            View Full Details
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <DownloadIcon sx={{ mr: 1 }} fontSize="small" />
            Export Entry
          </MenuItem>
        </Menu>
      </Box>
    </LocalizationProvider>
  );
};

export default AuditLogsPage;