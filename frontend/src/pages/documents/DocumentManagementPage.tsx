import React, { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Fab,
  Tooltip,
  Breadcrumbs,
  Link,
  Alert,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Search as SearchIcon,
  Analytics as AnalyticsIcon,
  Security as SecurityIcon,
  History as HistoryIcon,
  Close as CloseIcon,
  Add as AddIcon,
  Home as HomeIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';

import { DocumentMetadata } from '@/services/document.service';
import DocumentUploadAdvanced from '@/components/documents/DocumentUploadAdvanced';
import DocumentSearchAdvanced from '@/components/documents/DocumentSearchAdvanced';
import DocumentViewerAdvanced from '@/components/documents/DocumentViewerAdvanced';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`document-tabpanel-${index}`}
      aria-labelledby={`document-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

const DocumentManagementPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Get initial tab from URL params
  const getInitialTab = () => {
    const tab = searchParams.get('tab');
    switch (tab) {
      case 'search': return 1;
      case 'analytics': return 2;
      case 'security': return 3;
      case 'history': return 4;
      default: return 0;
    }
  };

  // State
  const [currentTab, setCurrentTab] = useState(getInitialTab);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [viewerDocument, setViewerDocument] = useState<string | null>(null);
  const [selectedPatientId, setSelectedPatientId] = useState<string>(''); // Would come from context or props

  // Sync tab state with URL params
  useEffect(() => {
    setCurrentTab(getInitialTab());
  }, [searchParams]);

  // Handlers
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
    
    // Update URL params
    const tabParam = (() => {
      switch (newValue) {
        case 1: return 'search';
        case 2: return 'analytics';
        case 3: return 'security';
        case 4: return 'history';
        default: return null;
      }
    })();
    
    if (tabParam) {
      setSearchParams({ tab: tabParam });
    } else {
      setSearchParams({});
    }
  };

  const handleUploadComplete = useCallback((documents: any[]) => {
    setUploadDialogOpen(false);
    // Refresh search results if on search tab
    if (currentTab === 1) {
      // Trigger refresh of search component
    }
  }, [currentTab]);

  const handleDocumentView = useCallback((document: DocumentMetadata) => {
    setViewerDocument(document.document_id);
  }, []);

  const handleDocumentEdit = useCallback((document: DocumentMetadata) => {
    // Open edit dialog or navigate to edit page
    console.log('Edit document:', document);
  }, []);

  const handleDocumentDelete = useCallback((document: DocumentMetadata) => {
    // Handle delete with confirmation
    console.log('Delete document:', document);
  }, []);

  const handleCloseViewer = () => {
    setViewerDocument(null);
  };

  // Tab accessibility
  const a11yProps = (index: number) => {
    return {
      id: `document-tab-${index}`,
      'aria-controls': `document-tabpanel-${index}`,
    };
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box mb={3}>
        <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
          <Link
            underline="hover"
            sx={{ display: 'flex', alignItems: 'center' }}
            color="inherit"
            href="/dashboard"
          >
            <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
            Dashboard
          </Link>
          <Typography
            sx={{ display: 'flex', alignItems: 'center' }}
            color="text.primary"
          >
            <FolderIcon sx={{ mr: 0.5 }} fontSize="inherit" />
            Document Management
          </Typography>
        </Breadcrumbs>

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4" fontWeight={600} gutterBottom>
              Document Management
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Upload, search, and manage patient documents with AI-powered classification
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
            size="large"
          >
            Upload Documents
          </Button>
        </Box>
      </Box>

      {/* Main Content */}
      <Paper elevation={1}>
        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            aria-label="document management tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab
              label="Upload Documents"
              icon={<UploadIcon />}
              iconPosition="start"
              {...a11yProps(0)}
            />
            <Tab
              label="Search & Browse"
              icon={<SearchIcon />}
              iconPosition="start"
              {...a11yProps(1)}
            />
            <Tab
              label="Analytics"
              icon={<AnalyticsIcon />}
              iconPosition="start"
              {...a11yProps(2)}
            />
            <Tab
              label="Security & Audit"
              icon={<SecurityIcon />}
              iconPosition="start"
              {...a11yProps(3)}
            />
            <Tab
              label="Version History"
              icon={<HistoryIcon />}
              iconPosition="start"
              {...a11yProps(4)}
            />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <Box sx={{ p: 3 }}>
          {/* Upload Tab */}
          <TabPanel value={currentTab} index={0}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Upload New Documents
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Drag & drop files or click to browse. AI will automatically classify and organize your documents.
              </Typography>
              
              <Alert severity="info" sx={{ mb: 3 }}>
                All uploads are encrypted and HIPAA compliant. File processing includes OCR, text extraction, and automatic classification.
              </Alert>

              <DocumentUploadAdvanced
                patientId={selectedPatientId || 'demo-patient-id'}
                onUploadComplete={handleUploadComplete}
                maxFiles={20}
                maxFileSize={100}
              />
            </Box>
          </TabPanel>

          {/* Search Tab */}
          <TabPanel value={currentTab} index={1}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Search & Browse Documents
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Advanced search with filters, sorting, and bulk operations.
              </Typography>

              <DocumentSearchAdvanced
                patientId={selectedPatientId}
                onDocumentView={handleDocumentView}
                onDocumentEdit={handleDocumentEdit}
                onDocumentDelete={handleDocumentDelete}
                showPatientFilter={!selectedPatientId}
                showBulkActions={true}
              />
            </Box>
          </TabPanel>

          {/* Analytics Tab */}
          <TabPanel value={currentTab} index={2}>
            <Box textAlign="center" py={8}>
              <AnalyticsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Document Analytics Dashboard
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Coming soon: AI classification performance, document type distribution, and usage analytics.
              </Typography>
              <Button variant="outlined" disabled>
                Feature in Development
              </Button>
            </Box>
          </TabPanel>

          {/* Security Tab */}
          <TabPanel value={currentTab} index={3}>
            <Box textAlign="center" py={8}>
              <SecurityIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Security & Compliance Dashboard
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                HIPAA audit trails, access logs, and compliance monitoring.
              </Typography>
              <Button variant="outlined" disabled>
                Feature in Development
              </Button>
            </Box>
          </TabPanel>

          {/* Version History Tab */}
          <TabPanel value={currentTab} index={4}>
            <Box textAlign="center" py={8}>
              <HistoryIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Document Version History
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Track document changes, view version diffs, and manage document lifecycle.
              </Typography>
              <Button variant="outlined" disabled>
                Feature in Development
              </Button>
            </Box>
          </TabPanel>
        </Box>
      </Paper>

      {/* Floating Action Button */}
      <Tooltip title="Upload Documents">
        <Fab
          color="primary"
          aria-label="upload documents"
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
          }}
          onClick={() => setUploadDialogOpen(true)}
        >
          <AddIcon />
        </Fab>
      </Tooltip>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Upload Documents</Typography>
            <IconButton onClick={() => setUploadDialogOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 3 }}>
          <DocumentUploadAdvanced
            patientId={selectedPatientId || 'demo-patient-id'}
            onUploadComplete={handleUploadComplete}
            maxFiles={20}
            maxFileSize={100}
          />
        </DialogContent>
      </Dialog>

      {/* Document Viewer Dialog */}
      <Dialog
        open={!!viewerDocument}
        onClose={handleCloseViewer}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '95vh' }
        }}
      >
        <DialogContent sx={{ p: 0 }}>
          {viewerDocument && (
            <DocumentViewerAdvanced
              documentId={viewerDocument}
              onClose={handleCloseViewer}
              onEdit={handleDocumentEdit}
              onDelete={handleDocumentDelete}
              fullscreen={true}
            />
          )}
        </DialogContent>
      </Dialog>
    </Container>
  );
};

export default DocumentManagementPage;