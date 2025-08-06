import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TablePagination,
  Avatar,
  Badge,
  Tooltip,
  Menu,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Skeleton,
  Stack,
  Divider,
  Collapse,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  CalendarToday as DateIcon,
  Label as TagIcon,
  Category as CategoryIcon,
  Psychology as AIIcon,
  FileDownload as ExportIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  InsertDriveFile as DocumentIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  Description as TextIcon,
  CheckBox,
  CheckBoxOutlineBlank,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { debounce } from 'lodash';

import { 
  documentService, 
  DocumentMetadata, 
  DocumentSearchParams, 
  DocumentType 
} from '@/services/document.service';
import { useAppDispatch } from '@/store';
import { showSnackbar } from '@/store/slices/uiSlice';

// Document type options
const DOCUMENT_TYPE_OPTIONS: Array<{ value: DocumentType; label: string; color: string }> = [
  { value: 'LAB_RESULT', label: 'Lab Result', color: '#2196f3' },
  { value: 'IMAGING', label: 'Medical Imaging', color: '#9c27b0' },
  { value: 'CLINICAL_NOTE', label: 'Clinical Note', color: '#4caf50' },
  { value: 'PRESCRIPTION', label: 'Prescription', color: '#ff9800' },
  { value: 'DISCHARGE_SUMMARY', label: 'Discharge Summary', color: '#f44336' },
  { value: 'OPERATIVE_REPORT', label: 'Operative Report', color: '#e91e63' },
  { value: 'PATHOLOGY_REPORT', label: 'Pathology Report', color: '#673ab7' },
  { value: 'RADIOLOGY_REPORT', label: 'Radiology Report', color: '#3f51b5' },
  { value: 'CONSULTATION_NOTE', label: 'Consultation Note', color: '#009688' },
  { value: 'PROGRESS_NOTE', label: 'Progress Note', color: '#8bc34a' },
  { value: 'MEDICATION_LIST', label: 'Medication List', color: '#ffc107' },
  { value: 'ALLERGY_LIST', label: 'Allergy List', color: '#ff5722' },
  { value: 'VITAL_SIGNS', label: 'Vital Signs', color: '#795548' },
  { value: 'INSURANCE_CARD', label: 'Insurance Card', color: '#607d8b' },
  { value: 'IDENTIFICATION_DOCUMENT', label: 'ID Document', color: '#9e9e9e' },
  { value: 'CONSENT_FORM', label: 'Consent Form', color: '#00bcd4' },
  { value: 'REFERRAL', label: 'Referral', color: '#cddc39' },
  { value: 'OTHER', label: 'Other', color: '#666666' },
];

interface DocumentSearchAdvancedProps {
  patientId?: string;
  onDocumentSelect?: (document: DocumentMetadata) => void;
  onDocumentView?: (document: DocumentMetadata) => void;
  onDocumentEdit?: (document: DocumentMetadata) => void;
  onDocumentDelete?: (document: DocumentMetadata) => void;
  showPatientFilter?: boolean;
  showBulkActions?: boolean;
}

const DocumentSearchAdvanced: React.FC<DocumentSearchAdvancedProps> = ({
  patientId,
  onDocumentSelect,
  onDocumentView,
  onDocumentEdit,
  onDocumentDelete,
  showPatientFilter = false,
  showBulkActions = true,
}) => {
  const dispatch = useAppDispatch();

  // State
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  
  // Search & Filter State
  const [searchParams, setSearchParams] = useState<DocumentSearchParams>({
    patient_id: patientId,
    search_text: '',
    document_types: [],
    document_category: '',
    tags: [],
    date_from: undefined,
    date_to: undefined,
    sort_by: 'uploaded_at',
    sort_order: 'desc',
    page: 0,
    limit: 10,
  });

  // UI State
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedDocument, setSelectedDocument] = useState<DocumentMetadata | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<DocumentMetadata | null>(null);

  // Get file icon based on mime type
  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return <ImageIcon />;
    if (mimeType === 'application/pdf') return <PdfIcon />;
    if (mimeType.startsWith('text/')) return <TextIcon />;
    return <DocumentIcon />;
  };

  // Get document type color
  const getDocumentTypeColor = (type: DocumentType) => {
    return DOCUMENT_TYPE_OPTIONS.find(opt => opt.value === type)?.color || '#666666';
  };

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce(async (params: DocumentSearchParams) => {
      setLoading(true);
      try {
        const response = await documentService.searchDocuments(params);
        setDocuments(response.documents);
        setTotal(response.total);
      } catch (error) {
        console.error('Search failed:', error);
        dispatch(showSnackbar({
          message: 'Failed to search documents',
          severity: 'error'
        }));
      } finally {
        setLoading(false);
      }
    }, 300),
    [dispatch]
  );

  // Search effect
  useEffect(() => {
    const params = {
      ...searchParams,
      page,
      limit: rowsPerPage,
    };
    debouncedSearch(params);
  }, [debouncedSearch, searchParams, page, rowsPerPage]);

  // Handle search input change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchParams(prev => ({
      ...prev,
      search_text: event.target.value,
    }));
    setPage(0);  // Reset to first page on new search
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof DocumentSearchParams, value: any) => {
    setSearchParams(prev => ({
      ...prev,
      [key]: value,
    }));
    setPage(0);  // Reset to first page on filter change
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchParams({
      patient_id: patientId,
      search_text: '',
      document_types: [],
      document_category: '',
      tags: [],
      date_from: undefined,
      date_to: undefined,
      sort_by: 'uploaded_at',
      sort_order: 'desc',
      page: 0,
      limit: rowsPerPage,
    });
    setPage(0);
  };

  // Handle sort
  const handleSort = (sortBy: string) => {
    const isAsc = searchParams.sort_by === sortBy && searchParams.sort_order === 'asc';
    setSearchParams(prev => ({
      ...prev,
      sort_by: sortBy as any,
      sort_order: isAsc ? 'desc' : 'asc',
    }));
  };

  // Handle selection
  const handleSelectDocument = (documentId: string) => {
    setSelectedDocuments(prev => 
      prev.includes(documentId) 
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const handleSelectAll = () => {
    setSelectedDocuments(
      selectedDocuments.length === documents.length 
        ? [] 
        : documents.map(doc => doc.document_id)
    );
  };

  // Document actions
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, document: DocumentMetadata) => {
    setMenuAnchor(event.currentTarget);
    setSelectedDocument(document);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedDocument(null);
  };

  const handleView = () => {
    if (selectedDocument) {
      onDocumentView?.(selectedDocument);
    }
    handleMenuClose();
  };

  const handleEdit = () => {
    if (selectedDocument) {
      onDocumentEdit?.(selectedDocument);
    }
    handleMenuClose();
  };

  const handleDownload = async () => {
    if (selectedDocument) {
      try {
        const blob = await documentService.downloadDocument(selectedDocument.document_id);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = selectedDocument.filename;
        a.click();
        URL.revokeObjectURL(url);
      } catch (error) {
        dispatch(showSnackbar({
          message: 'Failed to download document',
          severity: 'error'
        }));
      }
    }
    handleMenuClose();
  };

  const handleDeleteConfirm = () => {
    if (selectedDocument) {
      setConfirmDelete(selectedDocument);
    }
    handleMenuClose();
  };

  const handleDelete = async () => {
    if (confirmDelete) {
      try {
        await documentService.deleteDocument(confirmDelete.document_id);
        dispatch(showSnackbar({
          message: 'Document deleted successfully',
          severity: 'success'
        }));
        // Refresh the search
        debouncedSearch(searchParams);
      } catch (error) {
        dispatch(showSnackbar({
          message: 'Failed to delete document',
          severity: 'error'
        }));
      }
    }
    setConfirmDelete(null);
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
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        {/* Search Header */}
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  placeholder="Search documents by filename or content..."
                  value={searchParams.search_text}
                  onChange={handleSearchChange}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                    endAdornment: searchParams.search_text && (
                      <IconButton
                        size="small"
                        onClick={() => handleFilterChange('search_text', '')}
                      >
                        <ClearIcon />
                      </IconButton>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Box display="flex" justifyContent="flex-end" gap={1}>
                  <Button
                    variant="outlined"
                    startIcon={<FilterIcon />}
                    onClick={() => setFiltersOpen(!filtersOpen)}
                    color={filtersOpen ? 'primary' : 'inherit'}
                  >
                    Filters
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<ClearIcon />}
                    onClick={clearFilters}
                  >
                    Clear
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={() => debouncedSearch(searchParams)}
                    disabled={loading}
                  >
                    Refresh
                  </Button>
                </Box>
              </Grid>
            </Grid>

            {/* Active Filters Display */}
            {(searchParams.document_types?.length || searchParams.tags?.length || searchParams.document_category) && (
              <Box mt={2}>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {searchParams.document_types?.map(type => (
                    <Chip
                      key={type}
                      label={DOCUMENT_TYPE_OPTIONS.find(opt => opt.value === type)?.label || type}
                      onDelete={() => handleFilterChange('document_types', 
                        searchParams.document_types?.filter(t => t !== type)
                      )}
                      size="small"
                      sx={{ bgcolor: getDocumentTypeColor(type), color: 'white' }}
                    />
                  ))}
                  {searchParams.document_category && (
                    <Chip
                      label={`Category: ${searchParams.document_category}`}
                      onDelete={() => handleFilterChange('document_category', '')}
                      size="small"
                      color="primary"
                    />
                  )}
                  {searchParams.tags?.map(tag => (
                    <Chip
                      key={tag}
                      label={`#${tag}`}
                      onDelete={() => handleFilterChange('tags', 
                        searchParams.tags?.filter(t => t !== tag)
                      )}
                      size="small"
                      color="secondary"
                    />
                  ))}
                </Stack>
              </Box>
            )}

            {/* Filters Panel */}
            <Collapse in={filtersOpen}>
              <Box mt={3}>
                <Divider sx={{ mb: 3 }} />
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Autocomplete
                      multiple
                      options={DOCUMENT_TYPE_OPTIONS}
                      getOptionLabel={(option) => option.label}
                      value={DOCUMENT_TYPE_OPTIONS.filter(opt => 
                        searchParams.document_types?.includes(opt.value)
                      )}
                      onChange={(_, newValue) => handleFilterChange('document_types', 
                        newValue.map(opt => opt.value)
                      )}
                      renderInput={(params) => (
                        <TextField {...params} label="Document Types" />
                      )}
                      renderTags={(value, getTagProps) =>
                        value.map((option, index) => (
                          <Chip
                            variant="outlined"
                            label={option.label}
                            {...getTagProps({ index })}
                            sx={{ bgcolor: option.color, color: 'white' }}
                          />
                        ))
                      }
                    />
                  </Grid>

                  <Grid item xs={12} md={4}>
                    <TextField
                      fullWidth
                      label="Category"
                      value={searchParams.document_category}
                      onChange={(e) => handleFilterChange('document_category', e.target.value)}
                    />
                  </Grid>

                  <Grid item xs={12} md={4}>
                    <Autocomplete
                      multiple
                      freeSolo
                      options={[]}
                      value={searchParams.tags || []}
                      onChange={(_, newValue) => handleFilterChange('tags', newValue)}
                      renderInput={(params) => (
                        <TextField {...params} label="Tags" placeholder="Add tags..." />
                      )}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <DatePicker
                      label="Date From"
                      value={searchParams.date_from}
                      onChange={(date) => handleFilterChange('date_from', date)}
                      slotProps={{ textField: { fullWidth: true } }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <DatePicker
                      label="Date To"
                      value={searchParams.date_to}
                      onChange={(date) => handleFilterChange('date_to', date)}
                      slotProps={{ textField: { fullWidth: true } }}
                    />
                  </Grid>
                </Grid>
              </Box>
            </Collapse>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardContent sx={{ p: 0 }}>
            {/* Results Header */}
            <Box px={3} py={2} borderBottom={1} borderColor="divider">
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">
                  Documents ({total})
                </Typography>
                {showBulkActions && selectedDocuments.length > 0 && (
                  <Box display="flex" gap={1}>
                    <Button
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={() => {/* Handle bulk download */}}
                    >
                      Download ({selectedDocuments.length})
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => {/* Handle bulk delete */}}
                    >
                      Delete ({selectedDocuments.length})
                    </Button>
                  </Box>
                )}
              </Box>
            </Box>

            {/* Table */}
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    {showBulkActions && (
                      <TableCell padding="checkbox">
                        <CheckBox
                          indeterminate={selectedDocuments.length > 0 && selectedDocuments.length < documents.length}
                          checked={documents.length > 0 && selectedDocuments.length === documents.length}
                          onChange={handleSelectAll}
                        />
                      </TableCell>
                    )}
                    <TableCell>
                      <TableSortLabel
                        active={searchParams.sort_by === 'filename'}
                        direction={searchParams.sort_order}
                        onClick={() => handleSort('filename')}
                      >
                        Document
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={searchParams.sort_by === 'document_type'}
                        direction={searchParams.sort_order}
                        onClick={() => handleSort('document_type')}
                      >
                        Type
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={searchParams.sort_by === 'file_size'}
                        direction={searchParams.sort_order}
                        onClick={() => handleSort('file_size')}
                      >
                        Size
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={searchParams.sort_by === 'uploaded_at'}
                        direction={searchParams.sort_order}
                        onClick={() => handleSort('uploaded_at')}
                      >
                        Uploaded
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>Tags</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    [...Array(rowsPerPage)].map((_, index) => (
                      <TableRow key={index}>
                        {showBulkActions && <TableCell><Skeleton /></TableCell>}
                        <TableCell><Skeleton /></TableCell>
                        <TableCell><Skeleton /></TableCell>
                        <TableCell><Skeleton /></TableCell>
                        <TableCell><Skeleton /></TableCell>
                        <TableCell><Skeleton /></TableCell>
                        <TableCell><Skeleton /></TableCell>
                      </TableRow>
                    ))
                  ) : documents.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={showBulkActions ? 7 : 6} align="center" sx={{ py: 6 }}>
                        <Typography variant="body2" color="text.secondary">
                          No documents found
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    documents.map((document) => (
                      <TableRow
                        key={document.document_id}
                        hover
                        onClick={() => onDocumentSelect?.(document)}
                        sx={{ cursor: onDocumentSelect ? 'pointer' : 'default' }}
                      >
                        {showBulkActions && (
                          <TableCell padding="checkbox">
                            <CheckBox
                              checked={selectedDocuments.includes(document.document_id)}
                              onChange={() => handleSelectDocument(document.document_id)}
                              onClick={(e) => e.stopPropagation()}
                            />
                          </TableCell>
                        )}
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={2}>
                            <Avatar sx={{ width: 32, height: 32 }}>
                              {getFileIcon(document.mime_type)}
                            </Avatar>
                            <Box>
                              <Typography variant="body2" fontWeight={500}>
                                {document.filename}
                              </Typography>
                              {document.auto_classification_confidence && (
                                <Box display="flex" alignItems="center" gap={1}>
                                  <AIIcon sx={{ fontSize: 12, color: 'primary.main' }} />
                                  <Typography variant="caption" color="primary">
                                    {Math.round(document.auto_classification_confidence * 100)}% confidence
                                  </Typography>
                                </Box>
                              )}
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={DOCUMENT_TYPE_OPTIONS.find(opt => opt.value === document.document_type)?.label || document.document_type}
                            size="small"
                            sx={{ 
                              bgcolor: getDocumentTypeColor(document.document_type), 
                              color: 'white',
                              fontSize: '0.75rem'
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatFileSize(document.file_size)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(document.uploaded_at)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            by {document.uploaded_by}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={0.5} flexWrap="wrap">
                            {document.tags.slice(0, 2).map(tag => (
                              <Chip
                                key={tag}
                                label={tag}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.7rem', height: 20 }}
                              />
                            ))}
                            {document.tags.length > 2 && (
                              <Chip
                                label={`+${document.tags.length - 2}`}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.7rem', height: 20 }}
                              />
                            )}
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMenuOpen(e, document);
                            }}
                          >
                            <MoreIcon />
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
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={total}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              onRowsPerPageChange={(event) => {
                setRowsPerPage(parseInt(event.target.value, 10));
                setPage(0);
              }}
            />
          </CardContent>
        </Card>

        {/* Action Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleView}>
            <ListItemIcon><ViewIcon /></ListItemIcon>
            <ListItemText>View</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleDownload}>
            <ListItemIcon><DownloadIcon /></ListItemIcon>
            <ListItemText>Download</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleEdit}>
            <ListItemIcon><EditIcon /></ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleDeleteConfirm} sx={{ color: 'error.main' }}>
            <ListItemIcon><DeleteIcon color="error" /></ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        </Menu>

        {/* Delete Confirmation */}
        <Dialog open={!!confirmDelete} onClose={() => setConfirmDelete(null)}>
          <DialogTitle>Confirm Delete</DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to delete "{confirmDelete?.filename}"? This action cannot be undone.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setConfirmDelete(null)}>Cancel</Button>
            <Button onClick={handleDelete} color="error" variant="contained">
              Delete
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default DocumentSearchAdvanced;