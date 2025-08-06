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
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Alert,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  Description as DocumentIcon,
  Shield as SecurityIcon,
  Verified as VerifiedIcon,
  HealthAndSafety as HealthIcon,
  Assessment as AssessmentIcon,
  Science as ScienceIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
} from '@mui/icons-material';

interface ClinicalDocument {
  id: string;
  title: string;
  type: string;
  patient_id: string;
  patient_name: string;
  provider: string;
  date: string;
  status: string;
  fhir_valid: boolean;
  phi_encrypted: boolean;
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

const HealthcareRecordsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [documents, setDocuments] = useState<ClinicalDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedDocument, setSelectedDocument] = useState<ClinicalDocument | null>(null);

  // Mock data
  useEffect(() => {
    setLoading(true);
    setTimeout(() => {
      setDocuments([
        {
          id: '1',
          title: 'Annual Physical Examination',
          type: 'Clinical Note',
          patient_id: 'P001',
          patient_name: 'John Doe',
          provider: 'Dr. Smith',
          date: '2024-01-15',
          status: 'Final',
          fhir_valid: true,
          phi_encrypted: true,
        },
        {
          id: '2',
          title: 'COVID-19 Vaccination Record',
          type: 'Immunization',
          patient_id: 'P002',
          patient_name: 'Jane Smith',
          provider: 'Nurse Wilson',
          date: '2024-01-10',
          status: 'Final',
          fhir_valid: true,
          phi_encrypted: true,
        },
        {
          id: '3',
          title: 'Lab Results - CBC',
          type: 'Laboratory',
          patient_id: 'P001',
          patient_name: 'John Doe',
          provider: 'LabCorp',
          date: '2024-01-08',
          status: 'Final',
          fhir_valid: false,
          phi_encrypted: true,
        },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, document: ClinicalDocument) => {
    setAnchorEl(event.currentTarget);
    setSelectedDocument(document);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDocument(null);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'final':
        return 'success';
      case 'draft':
        return 'warning';
      case 'pending':
        return 'info';
      default:
        return 'default';
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600}>
          Healthcare Records
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => console.log('Add new document')}
        >
          New Document
        </Button>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Clinical Documents" icon={<DocumentIcon />} />
          <Tab label="FHIR Validation" icon={<VerifiedIcon />} />
          <Tab label="Data Anonymization" icon={<ScienceIcon />} />
          <Tab label="Compliance Reports" icon={<AssessmentIcon />} />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <TabPanel value={tabValue} index={0}>
        {/* Search and Filters */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Search documents by title, patient, or type..."
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
        </Paper>

        {/* Documents Table */}
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Document Title</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Patient</TableCell>
                  <TableCell>Provider</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>FHIR</TableCell>
                  <TableCell>PHI Protection</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : filteredDocuments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                      <Typography variant="body2" color="text.secondary">
                        No documents found.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredDocuments.map((doc) => (
                    <TableRow key={doc.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {doc.title}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={doc.type} variant="outlined" size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {doc.patient_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ID: {doc.patient_id}
                        </Typography>
                      </TableCell>
                      <TableCell>{doc.provider}</TableCell>
                      <TableCell>{doc.date}</TableCell>
                      <TableCell>
                        <Chip
                          label={doc.status}
                          color={getStatusColor(doc.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={<VerifiedIcon />}
                          label={doc.fhir_valid ? 'Valid' : 'Invalid'}
                          color={doc.fhir_valid ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <SecurityIcon color="primary" fontSize="small" />
                          <Typography variant="caption" color="primary.main">
                            Encrypted
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, doc)}
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
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="FHIR R4 Validation" />
              <CardContent>
                <Alert severity="info" sx={{ mb: 2 }}>
                  All healthcare documents are validated against FHIR R4 standards.
                </Alert>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <VerifiedIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Valid Documents"
                      secondary="2 of 3 documents are FHIR R4 compliant"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <HealthIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary="US Core Profile Support"
                      secondary="Validates against US Core implementation guide"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Validation Statistics" />
              <CardContent>
                <Typography variant="h3" color="primary.main" fontWeight={600}>
                  67%
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Overall FHIR Compliance Rate
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2">
                  1 document requires validation fixes
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Card>
          <CardHeader title="Data Anonymization & Research" />
          <CardContent>
            <Alert severity="warning" sx={{ mb: 3 }}>
              Data anonymization removes PHI to create research-ready datasets.
            </Alert>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  K-Anonymity
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Ensures each record is indistinguishable from at least k-1 other records.
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Differential Privacy
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Adds statistical noise to protect individual privacy while preserving utility.
                </Typography>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Research Export
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Export anonymized datasets for approved research studies.
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Card>
          <CardHeader title="Compliance & Audit Reports" />
          <CardContent>
            <Alert severity="info" sx={{ mb: 3 }}>
              Automated compliance reporting for SOC2, HIPAA, and healthcare regulations.
            </Alert>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  HIPAA Compliance
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  All PHI access is logged and audited. Encryption at rest and in transit.
                </Typography>
                <Button variant="outlined" size="small">
                  Generate HIPAA Report
                </Button>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  SOC2 Type II
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Security controls and operational effectiveness reporting.
                </Typography>
                <Button variant="outlined" size="small">
                  Generate SOC2 Report
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <ViewIcon sx={{ mr: 1 }} fontSize="small" />
          View Document
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <EditIcon sx={{ mr: 1 }} fontSize="small" />
          Edit Metadata
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <DownloadIcon sx={{ mr: 1 }} fontSize="small" />
          Download
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default HealthcareRecordsPage;