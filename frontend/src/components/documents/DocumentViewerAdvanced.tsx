import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Grid,
  Paper,
  Divider,
  Avatar,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Skeleton,
  Stack,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Badge,
  CircularProgress,
  LinearProgress,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Share as ShareIcon,
  History as HistoryIcon,
  Security as SecurityIcon,
  Visibility as ViewIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  RotateLeft as RotateLeftIcon,
  RotateRight as RotateRightIcon,
  Fullscreen as FullscreenIcon,
  Close as CloseIcon,
  ExpandMore as ExpandIcon,
  Psychology as AIIcon,
  FileDownload as FileIcon,
  Info as InfoIcon,
  Schedule as TimeIcon,
  Person as PersonIcon,
  Label as TagIcon,
  Category as CategoryIcon,
  Fingerprint as HashIcon,
  Storage as StorageIcon,
  CloudDownload as CloudIcon,
  InsertDriveFile as DocumentIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  Description as TextIcon,
} from '@mui/icons-material';

import { 
  documentService, 
  DocumentMetadata, 
  VersionInfo 
} from '@/services/document.service';
import { useAppDispatch } from '@/store';
import { showSnackbar } from '@/store/slices/uiSlice';

interface DocumentViewerAdvancedProps {
  documentId: string;
  onClose?: () => void;
  onEdit?: (document: DocumentMetadata) => void;
  onDelete?: (document: DocumentMetadata) => void;
  fullscreen?: boolean;
}

const DocumentViewerAdvanced: React.FC<DocumentViewerAdvancedProps> = ({
  documentId,
  onClose,
  onEdit,
  onDelete,
  fullscreen = false,
}) => {
  const dispatch = useAppDispatch();

  // State
  const [document, setDocument] = useState<DocumentMetadata | null>(null);
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [showVersions, setShowVersions] = useState(false);
  const [downloadConfirm, setDownloadConfirm] = useState(false);

  // Load document metadata
  useEffect(() => {
    const loadDocument = async () => {
      try {
        setLoading(true);
        const [docData, versionsData] = await Promise.all([
          documentService.getDocument(documentId),
          documentService.getVersionHistory(documentId),
        ]);
        
        setDocument(docData);
        setVersions(versionsData);
      } catch (error) {
        console.error('Failed to load document:', error);
        dispatch(showSnackbar({
          message: 'Failed to load document',
          severity: 'error'
        }));
      } finally {
        setLoading(false);
      }
    };

    loadDocument();
  }, [documentId, dispatch]);

  // Load preview if supported
  useEffect(() => {
    const loadPreview = async () => {
      if (!document) return;

      const supportedTypes = ['image/', 'application/pdf'];
      const isSupported = supportedTypes.some(type => document.mime_type.startsWith(type));
      
      if (isSupported) {
        try {
          setPreviewLoading(true);
          const blob = await documentService.downloadDocument(documentId);
          const url = URL.createObjectURL(blob);
          setPreviewUrl(url);
        } catch (error) {
          console.error('Failed to load preview:', error);
        } finally {
          setPreviewLoading(false);
        }
      }
    };

    loadPreview();

    // Cleanup preview URL on unmount
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [document, documentId, previewUrl]);

  // Get file icon
  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return <ImageIcon />;
    if (mimeType === 'application/pdf') return <PdfIcon />;
    if (mimeType.startsWith('text/')) return <TextIcon />;
    return <DocumentIcon />;
  };

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Handle download
  const handleDownload = async () => {
    if (!document) return;

    try {
      const blob = await documentService.downloadDocument(documentId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = document.filename;
      a.click();
      URL.revokeObjectURL(url);
      
      dispatch(showSnackbar({
        message: 'Document downloaded successfully',
        severity: 'success'
      }));
    } catch (error) {
      console.error('Download failed:', error);
      dispatch(showSnackbar({
        message: 'Failed to download document',
        severity: 'error'
      }));
    }
    setDownloadConfirm(false);
  };

  // Preview controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.25));
  const handleRotateLeft = () => setRotation(prev => prev - 90);
  const handleRotateRight = () => setRotation(prev => prev + 90);
  const resetView = () => {
    setZoom(1);
    setRotation(0);
  };

  if (loading) {
    return (
      <Box p={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Skeleton variant="rectangular" height={400} />
          </Grid>
          <Grid item xs={12} md={4}>
            <Skeleton variant="rectangular" height={200} />
            <Box mt={2}>
              <Skeleton variant="rectangular" height={150} />
            </Box>
          </Grid>
        </Grid>
      </Box>
    );
  }

  if (!document) {
    return (
      <Alert severity="error">
        Document not found or failed to load.
      </Alert>
    );
  }

  const canPreview = document.mime_type.startsWith('image/') || document.mime_type === 'application/pdf';

  return (
    <Box sx={{ height: fullscreen ? '100vh' : 'auto' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              {getFileIcon(document.mime_type)}
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight={600}>
                {document.filename}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatFileSize(document.file_size)} • {document.mime_type}
              </Typography>
            </Box>
          </Box>
          
          <Box display="flex" gap={1}>
            {canPreview && (
              <>
                <IconButton onClick={handleZoomOut} disabled={zoom <= 0.25}>
                  <ZoomOutIcon />
                </IconButton>
                <Typography variant="body2" sx={{ minWidth: 50, textAlign: 'center', py: 1 }}>
                  {Math.round(zoom * 100)}%
                </Typography>
                <IconButton onClick={handleZoomIn} disabled={zoom >= 3}>
                  <ZoomInIcon />
                </IconButton>
                <IconButton onClick={handleRotateLeft}>
                  <RotateLeftIcon />
                </IconButton>
                <IconButton onClick={handleRotateRight}>
                  <RotateRightIcon />
                </IconButton>
                <Button size="small" onClick={resetView}>
                  Reset
                </Button>
              </>
            )}
            
            <Divider orientation="vertical" flexItem />
            
            <Tooltip title="Download">
              <IconButton onClick={() => setDownloadConfirm(true)}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            
            {onEdit && (
              <Tooltip title="Edit">
                <IconButton onClick={() => onEdit(document)}>
                  <EditIcon />
                </IconButton>
              </Tooltip>
            )}
            
            {onClose && (
              <Tooltip title="Close">
                <IconButton onClick={onClose}>
                  <CloseIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      </Paper>

      <Grid container spacing={3}>
        {/* Document Preview */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: fullscreen ? 'calc(100vh - 120px)' : 600 }}>
            <CardContent sx={{ height: '100%', p: 0 }}>
              {previewLoading ? (
                <Box display="flex" alignItems="center" justifyContent="center" height="100%">
                  <CircularProgress />
                </Box>
              ) : canPreview && previewUrl ? (
                <Box 
                  sx={{ 
                    height: '100%', 
                    overflow: 'auto',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: 'grey.100'
                  }}
                >
                  {document.mime_type.startsWith('image/') ? (
                    <img
                      src={previewUrl}
                      alt={document.filename}
                      style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        transform: `scale(${zoom}) rotate(${rotation}deg)`,
                        transition: 'transform 0.2s ease-in-out',
                        objectFit: 'contain',
                      }}
                    />
                  ) : document.mime_type === 'application/pdf' ? (
                    <embed
                      src={previewUrl}
                      type="application/pdf"
                      width="100%"
                      height="100%"
                      style={{
                        transform: `scale(${zoom})`,
                        transformOrigin: 'center',
                      }}
                    />
                  ) : null}
                </Box>
              ) : (
                <Box 
                  display="flex" 
                  flexDirection="column" 
                  alignItems="center" 
                  justifyContent="center" 
                  height="100%"
                  sx={{ bgcolor: 'grey.50' }}
                >
                  {getFileIcon(document.mime_type)}
                  <Typography variant="h6" color="text.secondary" mt={2}>
                    Preview not available
                  </Typography>
                  <Typography variant="body2" color="text.secondary" mb={3}>
                    {document.mime_type}
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    onClick={() => setDownloadConfirm(true)}
                  >
                    Download to View
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Document Information */}
        <Grid item xs={12} md={4}>
          <Stack spacing={2}>
            {/* Basic Information */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Document Information
                </Typography>
                
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Document Type
                    </Typography>
                    <Chip 
                      label={document.document_type} 
                      color="primary" 
                      size="small" 
                    />
                  </Box>

                  {document.document_category && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Category
                      </Typography>
                      <Typography variant="body2">
                        {document.document_category}
                      </Typography>
                    </Box>
                  )}

                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      File Size
                    </Typography>
                    <Typography variant="body2">
                      {formatFileSize(document.file_size)}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Uploaded
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(document.uploaded_at)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      by {document.uploaded_by}
                    </Typography>
                  </Box>

                  {document.updated_at && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Last Updated
                      </Typography>
                      <Typography variant="body2">
                        {formatDate(document.updated_at)}
                      </Typography>
                      {document.updated_by && (
                        <Typography variant="caption" color="text.secondary">
                          by {document.updated_by}
                        </Typography>
                      )}
                    </Box>
                  )}
                </Stack>
              </CardContent>
            </Card>

            {/* AI Classification */}
            {document.auto_classification_confidence && (
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <AIIcon color="primary" />
                    <Typography variant="h6">
                      AI Classification
                    </Typography>
                  </Box>
                  
                  <Box mb={2}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Confidence Score
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <LinearProgress
                        variant="determinate"
                        value={document.auto_classification_confidence * 100}
                        sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="body2" fontWeight={500}>
                        {Math.round(document.auto_classification_confidence * 100)}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Tags */}
            {document.tags.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Tags
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {document.tags.map(tag => (
                      <Chip
                        key={tag}
                        label={tag}
                        variant="outlined"
                        size="small"
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Version History */}
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Typography variant="h6">
                    Version History
                  </Typography>
                  <Badge badgeContent={versions.length} color="primary">
                    <HistoryIcon />
                  </Badge>
                </Box>
                
                {versions.length > 0 ? (
                  <List dense>
                    {versions.slice(0, 3).map((version) => (
                      <ListItem key={version.version_id} divider>
                        <ListItemIcon>
                          <Avatar sx={{ width: 24, height: 24, fontSize: '0.75rem' }}>
                            v{version.version_number}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText
                          primary={`Version ${version.version_number}`}
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {formatDate(version.created_at)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                by {version.created_by}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                    {versions.length > 3 && (
                      <ListItem>
                        <ListItemText>
                          <Button
                            size="small"
                            onClick={() => setShowVersions(true)}
                          >
                            View All Versions ({versions.length})
                          </Button>
                        </ListItemText>
                      </ListItem>
                    )}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No version history available
                  </Typography>
                )}
              </CardContent>
            </Card>

            {/* Security Information */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandIcon />}>
                <Box display="flex" alignItems="center" gap={1}>
                  <SecurityIcon />
                  <Typography variant="h6">Security & Compliance</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Document ID
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      {document.document_id}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Storage Key
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      {document.storage_key}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      SHA256 Hash
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace" fontSize="0.75rem">
                      {document.hash_sha256}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Version
                    </Typography>
                    <Typography variant="body2">
                      v{document.version} {document.is_latest_version && '(Latest)'}
                    </Typography>
                  </Box>
                </Stack>
              </AccordionDetails>
            </Accordion>
          </Stack>
        </Grid>
      </Grid>

      {/* Download Confirmation Dialog */}
      <Dialog open={downloadConfirm} onClose={() => setDownloadConfirm(false)}>
        <DialogTitle>Download Document</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            This download will be logged for compliance purposes.
          </Alert>
          <Typography>
            Are you sure you want to download "{document.filename}"?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDownloadConfirm(false)}>Cancel</Button>
          <Button onClick={handleDownload} variant="contained">
            Download
          </Button>
        </DialogActions>
      </Dialog>

      {/* All Versions Dialog */}
      <Dialog open={showVersions} onClose={() => setShowVersions(false)} maxWidth="md" fullWidth>
        <DialogTitle>Version History</DialogTitle>
        <DialogContent>
          <List>
            {versions.map((version) => (
              <ListItem key={version.version_id} divider>
                <ListItemIcon>
                  <Avatar sx={{ bgcolor: version.is_current ? 'primary.main' : 'grey.400' }}>
                    v{version.version_number}
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body1" fontWeight={500}>
                        Version {version.version_number}
                      </Typography>
                      {version.is_current && (
                        <Chip label="Current" size="small" color="primary" />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        {version.change_summary}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(version.created_at)} by {version.created_by}
                      </Typography>
                      <Typography variant="caption" display="block">
                        {formatFileSize(version.file_size)}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowVersions(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentViewerAdvanced;