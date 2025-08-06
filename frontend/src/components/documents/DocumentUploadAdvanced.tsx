import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Chip,
  IconButton,
  Divider,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Autocomplete,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Fade,
  Zoom,
  CircularProgress,
  Stack,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  DragIndicator as DragIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Psychology as AIIcon,
  Visibility as PreviewIcon,
  FileUpload as FileIcon,
  InsertDriveFile as DocumentIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  Description as TextIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

import { documentService, DocumentType, UploadProgress, UploadMetadata, ClassificationResult } from '@/services/document.service';
import { useAppDispatch } from '@/store';
import { showSnackbar } from '@/store/slices/uiSlice';
import PatientSelectorAdvanced from './PatientSelectorAdvanced';

// Document type options with labels
const DOCUMENT_TYPE_OPTIONS: Array<{ value: DocumentType; label: string; description: string }> = [
  { value: 'LAB_RESULT', label: 'Lab Result', description: 'Laboratory test results and reports' },
  { value: 'IMAGING', label: 'Medical Imaging', description: 'X-rays, MRI, CT scans, ultrasounds' },
  { value: 'CLINICAL_NOTE', label: 'Clinical Note', description: 'Progress notes, SOAP notes' },
  { value: 'PRESCRIPTION', label: 'Prescription', description: 'Medication prescriptions' },
  { value: 'DISCHARGE_SUMMARY', label: 'Discharge Summary', description: 'Hospital discharge summaries' },
  { value: 'OPERATIVE_REPORT', label: 'Operative Report', description: 'Surgical procedure reports' },
  { value: 'PATHOLOGY_REPORT', label: 'Pathology Report', description: 'Pathology analysis results' },
  { value: 'RADIOLOGY_REPORT', label: 'Radiology Report', description: 'Radiology interpretation reports' },
  { value: 'CONSULTATION_NOTE', label: 'Consultation Note', description: 'Specialist consultation notes' },
  { value: 'PROGRESS_NOTE', label: 'Progress Note', description: 'Patient progress documentation' },
  { value: 'MEDICATION_LIST', label: 'Medication List', description: 'Current medications list' },
  { value: 'ALLERGY_LIST', label: 'Allergy List', description: 'Patient allergies documentation' },
  { value: 'VITAL_SIGNS', label: 'Vital Signs', description: 'Vital sign measurements' },
  { value: 'INSURANCE_CARD', label: 'Insurance Card', description: 'Insurance documentation' },
  { value: 'IDENTIFICATION_DOCUMENT', label: 'ID Document', description: 'Patient identification' },
  { value: 'CONSENT_FORM', label: 'Consent Form', description: 'Medical consent forms' },
  { value: 'REFERRAL', label: 'Referral', description: 'Provider referrals' },
  { value: 'OTHER', label: 'Other', description: 'Miscellaneous documents' },
];

// Common document categories
const CATEGORY_OPTIONS = [
  'Administrative',
  'Clinical',
  'Diagnostic',
  'Treatment',
  'Billing',
  'Legal',
  'Emergency',
  'Preventive Care',
];

// Common tags
const TAG_OPTIONS = [
  'urgent',
  'routine',
  'follow-up',
  'emergency',
  'chronic',
  'acute',
  'preventive',
  'diagnostic',
  'treatment',
  'medication',
  'allergy',
  'insurance',
  'billing',
  'legal',
  'consent',
];

interface DocumentUploadAdvancedProps {
  patientId?: string;
  onUploadComplete?: (documents: any[]) => void;
  maxFiles?: number;
  maxFileSize?: number; // in MB
  requirePatientSelection?: boolean;
  showPatientSelector?: boolean;
}

const DocumentUploadAdvanced: React.FC<DocumentUploadAdvancedProps> = ({
  patientId,
  onUploadComplete,
  maxFiles = 10,
  maxFileSize = 50,
  requirePatientSelection = true,
  showPatientSelector = true,
}) => {
  const dispatch = useAppDispatch();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, UploadProgress>>({});
  const [isUploading, setIsUploading] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<any>(null);
  const [metadata, setMetadata] = useState<UploadMetadata>({
    patient_id: patientId || '',
    auto_classify: true,
    auto_generate_filename: true,
    tags: [],
  });
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [previewFile, setPreviewFile] = useState<File | null>(null);
  const [classificationResults, setClassificationResults] = useState<Record<string, ClassificationResult>>({});

  // Handle patient selection
  const handlePatientSelect = (patient: any) => {
    setSelectedPatient(patient);
    setMetadata(prev => ({
      ...prev,
      patient_id: patient?.id || '',
    }));
  };

  // Check if upload is allowed
  const canUpload = () => {
    if (requirePatientSelection && !selectedPatient && !patientId) {
      return false;
    }
    return files.length > 0 && !isUploading;
  };

  // Dropzone configuration
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.filter(file => {
      if (file.size > maxFileSize * 1024 * 1024) {
        dispatch(showSnackbar({
          message: `File ${file.name} is too large (max ${maxFileSize}MB)`,
          severity: 'error'
        }));
        return false;
      }
      return true;
    });

    if (files.length + newFiles.length > maxFiles) {
      dispatch(showSnackbar({
        message: `Maximum ${maxFiles} files allowed`,
        severity: 'warning'
      }));
      return;
    }

    setFiles(prev => [...prev, ...newFiles]);
  }, [files.length, maxFiles, maxFileSize, dispatch]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'application/rtf': ['.rtf'],
    },
    multiple: true,
  });

  // File management
  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearFiles = () => {
    setFiles([]);
    setUploadProgress({});
    setClassificationResults({});
  };

  // Get file icon
  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <ImageIcon />;
    if (file.type === 'application/pdf') return <PdfIcon />;
    if (file.type.startsWith('text/')) return <TextIcon />;
    return <DocumentIcon />;
  };

  // Upload handling
  const handleUpload = async () => {
    if (files.length === 0) return;

    // Validate patient selection
    if (requirePatientSelection && !selectedPatient && !patientId) {
      dispatch(showSnackbar({
        message: 'Please select a patient before uploading documents',
        severity: 'error'
      }));
      return;
    }

    setIsUploading(true);
    const results = [];

    try {
      const uploadResults = await documentService.uploadMultipleDocuments(
        files,
        metadata,
        (fileIndex, progress) => {
          const fileName = files[fileIndex]?.name;
          if (fileName) {
            setUploadProgress(prev => ({
              ...prev,
              [fileName]: progress
            }));

            // Store classification results
            if (progress.classification) {
              setClassificationResults(prev => ({
                ...prev,
                [fileName]: progress.classification!
              }));
            }
          }
        }
      );

      results.push(...uploadResults);

      const successCount = uploadResults.filter(r => !r.error).length;
      const errorCount = uploadResults.filter(r => r.error).length;

      if (successCount > 0) {
        dispatch(showSnackbar({
          message: `Successfully uploaded ${successCount} document${successCount > 1 ? 's' : ''}`,
          severity: 'success'
        }));
      }

      if (errorCount > 0) {
        dispatch(showSnackbar({
          message: `Failed to upload ${errorCount} document${errorCount > 1 ? 's' : ''}`,
          severity: 'error'
        }));
      }

      onUploadComplete?.(results.filter(r => !r.error));

      // Clear files after successful upload
      if (errorCount === 0) {
        clearFiles();
      }

    } catch (error) {
      console.error('Upload failed:', error);
      dispatch(showSnackbar({
        message: 'Upload failed. Please try again.',
        severity: 'error'
      }));
    } finally {
      setIsUploading(false);
    }
  };

  // Settings dialog
  const SettingsDialog = () => (
    <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Upload Settings</DialogTitle>
      <DialogContent>
        <Grid container spacing={3} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Document Type</InputLabel>
              <Select
                value={metadata.document_type || ''}
                onChange={(e) => setMetadata(prev => ({ ...prev, document_type: e.target.value as DocumentType }))}
                label="Document Type"
              >
                <MenuItem value="">Auto-detect</MenuItem>
                {DOCUMENT_TYPE_OPTIONS.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    <Box>
                      <Typography variant="body2">{option.label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {option.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={metadata.document_category || ''}
                onChange={(e) => setMetadata(prev => ({ ...prev, document_category: e.target.value }))}
                label="Category"
              >
                <MenuItem value="">None</MenuItem>
                {CATEGORY_OPTIONS.map(category => (
                  <MenuItem key={category} value={category}>{category}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <Autocomplete
              multiple
              options={TAG_OPTIONS}
              value={metadata.tags || []}
              onChange={(_, newValue) => setMetadata(prev => ({ ...prev, tags: newValue }))}
              freeSolo
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip key={index} variant="outlined" label={option} {...getTagProps({ index })} />
                ))
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  variant="outlined"
                  label="Tags"
                  placeholder="Add tags..."
                />
              )}
            />
          </Grid>

          <Grid item xs={6}>
            <Button
              variant={metadata.auto_classify ? 'contained' : 'outlined'}
              onClick={() => setMetadata(prev => ({ ...prev, auto_classify: !prev.auto_classify }))}
              startIcon={<AIIcon />}
              fullWidth
            >
              AI Classification
            </Button>
          </Grid>

          <Grid item xs={6}>
            <Button
              variant={metadata.auto_generate_filename ? 'contained' : 'outlined'}
              onClick={() => setMetadata(prev => ({ ...prev, auto_generate_filename: !prev.auto_generate_filename }))}
              startIcon={<FileIcon />}
              fullWidth
            >
              Smart Filename
            </Button>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setSettingsOpen(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box>
      {/* Patient Selection */}
      {showPatientSelector && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Patient Selection
            </Typography>
            <PatientSelectorAdvanced
              selectedPatientId={patientId}
              onPatientSelect={handlePatientSelect}
              required={requirePatientSelection}
              auditPurpose="document_upload"
              showSOC2Info={true}
            />
          </CardContent>
        </Card>
      )}

      {/* Upload Area */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'primary.lighter' : 'transparent',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'primary.lighter',
              },
            }}
          >
            <input {...getInputProps()} ref={fileInputRef} />
            <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop files here...' : 'Drag & drop files or click to browse'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Supports: PDF, Images, Word documents, Text files
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Max {maxFiles} files, up to {maxFileSize}MB each
            </Typography>
          </Box>

          {/* Action Buttons */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
            <Box display="flex" gap={1}>
              <Button
                variant="outlined"
                onClick={() => fileInputRef.current?.click()}
                startIcon={<FileIcon />}
              >
                Browse Files
              </Button>
              <Button
                variant="outlined"
                onClick={() => setSettingsOpen(true)}
                startIcon={<AIIcon />}
              >
                Settings
              </Button>
            </Box>
            <Box display="flex" gap={1}>
              {files.length > 0 && (
                <Button
                  variant="outlined"
                  color="error"
                  onClick={clearFiles}
                  disabled={isUploading}
                >
                  Clear All
                </Button>
              )}
              <Button
                variant="contained"
                onClick={handleUpload}
                disabled={!canUpload()}
                startIcon={isUploading ? <CircularProgress size={20} /> : <UploadIcon />}
              >
                {isUploading ? 'Uploading...' : 
                 !selectedPatient && requirePatientSelection && !patientId ? 'Select Patient First' :
                 `Upload ${files.length} File${files.length !== 1 ? 's' : ''}`}
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Files Ready for Upload ({files.length})
            </Typography>
            <List>
              {files.map((file, index) => {
                const progress = uploadProgress[file.name];
                const classification = classificationResults[file.name];
                
                return (
                  <React.Fragment key={`${file.name}-${index}`}>
                    <ListItem>
                      <ListItemIcon>
                        {getFileIcon(file)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body2" fontWeight={500}>
                              {file.name}
                            </Typography>
                            {progress?.status === 'completed' && (
                              <CheckIcon color="success" sx={{ fontSize: 16 }} />
                            )}
                            {progress?.status === 'error' && (
                              <ErrorIcon color="error" sx={{ fontSize: 16 }} />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              {(file.size / 1024 / 1024).toFixed(2)} MB • {file.type}
                            </Typography>
                            
                            {/* Upload Progress */}
                            {progress && progress.status !== 'pending' && (
                              <Box mt={1}>
                                <LinearProgress
                                  variant="determinate"
                                  value={progress.progress}
                                  color={progress.status === 'error' ? 'error' : 'primary'}
                                  sx={{ height: 4, borderRadius: 2 }}
                                />
                                <Typography variant="caption" color="text.secondary">
                                  {progress.status === 'uploading' && `${progress.progress}%`}
                                  {progress.status === 'processing' && 'Processing...'}
                                  {progress.status === 'completed' && 'Completed'}
                                  {progress.status === 'error' && `Error: ${progress.error}`}
                                </Typography>
                              </Box>
                            )}

                            {/* AI Classification Results */}
                            {classification && (
                              <Box mt={1}>
                                <Stack direction="row" spacing={1} flexWrap="wrap">
                                  <Chip
                                    label={`${classification.document_type} (${Math.round(classification.confidence * 100)}%)`}
                                    size="small"
                                    color="primary"
                                    icon={<AIIcon />}
                                  />
                                  {classification.category && (
                                    <Chip
                                      label={classification.category}
                                      size="small"
                                      variant="outlined"
                                    />
                                  )}
                                </Stack>
                              </Box>
                            )}
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box display="flex" gap={1}>
                          <IconButton
                            edge="end"
                            onClick={() => setPreviewFile(file)}
                            size="small"
                            disabled={isUploading}
                          >
                            <PreviewIcon />
                          </IconButton>
                          <IconButton
                            edge="end"
                            onClick={() => removeFile(index)}
                            size="small"
                            disabled={isUploading}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                    {index < files.length - 1 && <Divider />}
                  </React.Fragment>
                );
              })}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Settings Dialog */}
      <SettingsDialog />

      {/* File Preview Dialog */}
      <Dialog
        open={!!previewFile}
        onClose={() => setPreviewFile(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Preview: {previewFile?.name}
          <IconButton
            onClick={() => setPreviewFile(null)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {previewFile && previewFile.type.startsWith('image/') && (
            <Box textAlign="center">
              <img
                src={URL.createObjectURL(previewFile)}
                alt={previewFile.name}
                style={{ maxWidth: '100%', maxHeight: '500px', objectFit: 'contain' }}
              />
            </Box>
          )}
          {previewFile && !previewFile.type.startsWith('image/') && (
            <Box textAlign="center" py={4}>
              <DocumentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Preview not available for this file type
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {previewFile.type} • {(previewFile.size / 1024 / 1024).toFixed(2)} MB
              </Typography>
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default DocumentUploadAdvanced;