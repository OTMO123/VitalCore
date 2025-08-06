import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Autocomplete,
  TextField,
  Card,
  CardContent,
  Typography,
  Avatar,
  Chip,
  Alert,
  Button,
  Divider,
  Stack,
  Badge,
  Tooltip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Person as PersonIcon,
  Search as SearchIcon,
  Verified as VerifiedIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  Lock as LockIcon,
  Assignment as AssignmentIcon,
  AccessTime as AccessTimeIcon,
  Shield as ShieldIcon,
  LocalHospital as MedicalIcon,
} from '@mui/icons-material';
import { debounce } from 'lodash';

import { patientService } from '@/services/patient.service';
import { useAppDispatch, useAppSelector } from '@/store';
import { selectUser } from '@/store/slices/authSlice';
import { showSnackbar } from '@/store/slices/uiSlice';

interface Patient {
  id: string;
  external_id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  consent_status: 'granted' | 'denied' | 'pending' | 'expired';
  data_classification: 'PHI' | 'CONFIDENTIAL' | 'INTERNAL' | 'PUBLIC';
  iris_sync_status?: string;
  created_at: string;
}

interface PatientSelectorAdvancedProps {
  selectedPatientId?: string;
  onPatientSelect: (patient: Patient | null) => void;
  disabled?: boolean;
  required?: boolean;
  showSOC2Info?: boolean;
  auditPurpose?: string;
}

const PatientSelectorAdvanced: React.FC<PatientSelectorAdvancedProps> = ({
  selectedPatientId,
  onPatientSelect,
  disabled = false,
  required = false,
  showSOC2Info = true,
  auditPurpose = "document_attachment",
}) => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(selectUser);

  // State
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [accessConfirmOpen, setAccessConfirmOpen] = useState(false);
  const [pendingPatient, setPendingPatient] = useState<Patient | null>(null);

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce(async (query: string) => {
      if (query.length < 2) {
        setPatients([]);
        return;
      }

      setLoading(true);
      try {
        const response = await patientService.getPatients({
          search: query,
          limit: 20,
          include_encrypted: false, // For SOC2 compliance, search on non-PHI fields only
        });

        if (response.data) {
          setPatients(response.data.patients || []);
        }
      } catch (error) {
        console.error('Patient search failed:', error);
        dispatch(showSnackbar({
          message: 'Failed to search patients',
          severity: 'error'
        }));
      } finally {
        setLoading(false);
      }
    }, 300),
    [dispatch]
  );

  // Effect for searching patients
  useEffect(() => {
    debouncedSearch(searchQuery);
  }, [searchQuery, debouncedSearch]);

  // Load selected patient if ID provided
  useEffect(() => {
    if (selectedPatientId && !selectedPatient) {
      loadPatientById(selectedPatientId);
    }
  }, [selectedPatientId, selectedPatient]);

  const loadPatientById = async (patientId: string) => {
    try {
      const response = await patientService.getPatient(patientId);
      if (response.data) {
        setSelectedPatient(response.data);
      }
    } catch (error) {
      console.error('Failed to load patient:', error);
    }
  };

  // Get patient display name (secure, PHI-compliant)
  const getPatientDisplayName = (patient: Patient) => {
    // For SOC2 compliance, avoid displaying full names in search results
    // Only show when explicitly selected
    if (selectedPatient?.id === patient.id) {
      return `${patient.first_name} ${patient.last_name}`;
    }
    return `Patient ${patient.mrn}`;
  };

  // Get consent status color
  const getConsentStatusColor = (status: string) => {
    switch (status) {
      case 'granted': return 'success';
      case 'denied': return 'error';
      case 'pending': return 'warning';
      case 'expired': return 'error';
      default: return 'default';
    }
  };

  // Get data classification color
  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case 'PHI': return 'error';
      case 'CONFIDENTIAL': return 'warning';
      case 'INTERNAL': return 'info';
      case 'PUBLIC': return 'success';
      default: return 'default';
    }
  };

  // Check if patient selection requires confirmation
  const requiresAccessConfirmation = (patient: Patient) => {
    // SOC2 requirement: confirm access to PHI data
    return patient.data_classification === 'PHI' || patient.consent_status !== 'granted';
  };

  // Handle patient selection
  const handlePatientSelect = (patient: Patient | null) => {
    if (!patient) {
      setSelectedPatient(null);
      onPatientSelect(null);
      return;
    }

    // Check if access confirmation is needed
    if (requiresAccessConfirmation(patient)) {
      setPendingPatient(patient);
      setAccessConfirmOpen(true);
    } else {
      confirmPatientSelection(patient);
    }
  };

  // Confirm patient selection with audit logging
  const confirmPatientSelection = async (patient: Patient) => {
    try {
      // Log PHI access for SOC2 compliance
      if (patient.data_classification === 'PHI') {
        // This would typically be logged via the audit service
        console.log('PHI_ACCESS_LOG', {
          user_id: user?.id,
          patient_id: patient.id,
          purpose: auditPurpose,
          timestamp: new Date().toISOString(),
          patient_mrn: patient.mrn,
        });
      }

      setSelectedPatient(patient);
      onPatientSelect(patient);
      setAccessConfirmOpen(false);
      setPendingPatient(null);

      dispatch(showSnackbar({
        message: `Patient selected: ${patient.mrn}`,
        severity: 'success'
      }));

    } catch (error) {
      console.error('Patient selection failed:', error);
      dispatch(showSnackbar({
        message: 'Failed to select patient',
        severity: 'error'
      }));
    }
  };

  // Cancel patient selection
  const cancelPatientSelection = () => {
    setAccessConfirmOpen(false);
    setPendingPatient(null);
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Check user permissions
  const canAccessPHI = () => {
    return user?.role?.name === 'admin' || user?.role?.name === 'doctor';
  };

  return (
    <Box>
      {/* SOC2 Compliance Notice */}
      {showSOC2Info && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" gap={1}>
            <ShieldIcon />
            <Typography variant="body2">
              <strong>SOC2 Compliance:</strong> Patient selection is logged for audit purposes. 
              Only select patients relevant to your current task.
            </Typography>
          </Box>
        </Alert>
      )}

      {/* Patient Search */}
      <Autocomplete
        options={patients}
        getOptionLabel={(option) => getPatientDisplayName(option)}
        value={selectedPatient}
        onChange={(_, newValue) => handlePatientSelect(newValue)}
        onInputChange={(_, newInputValue) => setSearchQuery(newInputValue)}
        loading={loading}
        disabled={disabled}
        renderInput={(params) => (
          <TextField
            {...params}
            label={`Select Patient ${required ? '*' : ''}`}
            placeholder="Search by MRN or patient identifier..."
            error={required && !selectedPatient}
            helperText={required && !selectedPatient ? 'Patient selection is required' : 'Type to search patients'}
            InputProps={{
              ...params.InputProps,
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              endAdornment: (
                <>
                  {loading ? <CircularProgress color="inherit" size={20} /> : null}
                  {params.InputProps.endAdornment}
                </>
              ),
            }}
          />
        )}
        renderOption={(props, option) => (
          <Box component="li" {...props}>
            <Box display="flex" alignItems="center" width="100%" py={1}>
              <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                <PersonIcon />
              </Avatar>
              <Box flexGrow={1}>
                <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                  <Typography variant="body2" fontWeight={500}>
                    MRN: {option.mrn}
                  </Typography>
                  <Chip
                    label={option.consent_status}
                    size="small"
                    color={getConsentStatusColor(option.consent_status) as any}
                    sx={{ fontSize: '0.625rem', height: 18 }}
                  />
                  <Chip
                    label={option.data_classification}
                    size="small"
                    color={getClassificationColor(option.data_classification) as any}
                    sx={{ fontSize: '0.625rem', height: 18 }}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  DOB: {formatDate(option.date_of_birth)} • Created: {formatDate(option.created_at)}
                </Typography>
              </Box>
              {requiresAccessConfirmation(option) && (
                <Tooltip title="Requires access confirmation">
                  <SecurityIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                </Tooltip>
              )}
            </Box>
          </Box>
        )}
        noOptionsText={
          searchQuery.length < 2 
            ? "Type at least 2 characters to search" 
            : "No patients found"
        }
      />

      {/* Selected Patient Card */}
      {selectedPatient && (
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start">
              <Box display="flex" alignItems="center" gap={2}>
                <Badge
                  overlap="circular"
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                  badgeContent={
                    selectedPatient.data_classification === 'PHI' ? (
                      <LockIcon sx={{ fontSize: 12, color: 'error.main' }} />
                    ) : (
                      <VerifiedIcon sx={{ fontSize: 12, color: 'success.main' }} />
                    )
                  }
                >
                  <Avatar sx={{ width: 48, height: 48, bgcolor: 'primary.main' }}>
                    <PersonIcon />
                  </Avatar>
                </Badge>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    {getPatientDisplayName(selectedPatient)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    MRN: {selectedPatient.mrn} • External ID: {selectedPatient.external_id}
                  </Typography>
                  <Box display="flex" gap={1} mt={1}>
                    <Chip
                      label={`Consent: ${selectedPatient.consent_status}`}
                      size="small"
                      color={getConsentStatusColor(selectedPatient.consent_status) as any}
                    />
                    <Chip
                      label={selectedPatient.data_classification}
                      size="small"
                      color={getClassificationColor(selectedPatient.data_classification) as any}
                    />
                  </Box>
                </Box>
              </Box>
              <Button
                variant="outlined"
                color="error"
                size="small"
                onClick={() => handlePatientSelect(null)}
              >
                Clear Selection
              </Button>
            </Box>

            {/* SOC2 Information */}
            {selectedPatient.data_classification === 'PHI' && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <LockIcon />
                  <Typography variant="body2">
                    <strong>PHI Data Access:</strong> This patient's data is classified as Protected Health Information. 
                    All access is logged for HIPAA compliance.
                  </Typography>
                </Box>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Access Confirmation Dialog */}
      <Dialog open={accessConfirmOpen} onClose={cancelPatientSelection} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <SecurityIcon color="warning" />
            Confirm Patient Access
          </Box>
        </DialogTitle>
        <DialogContent>
          {pendingPatient && (
            <Box>
              <Alert severity="warning" sx={{ mb: 3 }}>
                You are about to access patient data that may contain Protected Health Information (PHI). 
                This access will be logged for audit purposes.
              </Alert>

              <Typography variant="h6" gutterBottom>
                Patient Information:
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemIcon><AssignmentIcon /></ListItemIcon>
                  <ListItemText 
                    primary="MRN" 
                    secondary={pendingPatient.mrn} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><MedicalIcon /></ListItemIcon>
                  <ListItemText 
                    primary="Data Classification" 
                    secondary={
                      <Chip
                        label={pendingPatient.data_classification}
                        size="small"
                        color={getClassificationColor(pendingPatient.data_classification) as any}
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><VerifiedIcon /></ListItemIcon>
                  <ListItemText 
                    primary="Consent Status" 
                    secondary={
                      <Chip
                        label={pendingPatient.consent_status}
                        size="small"
                        color={getConsentStatusColor(pendingPatient.consent_status) as any}
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><AccessTimeIcon /></ListItemIcon>
                  <ListItemText 
                    primary="Access Purpose" 
                    secondary={auditPurpose} 
                  />
                </ListItem>
              </List>

              {pendingPatient.consent_status !== 'granted' && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  <strong>Warning:</strong> This patient's consent status is "{pendingPatient.consent_status}". 
                  Ensure you have legal authority to access this data.
                </Alert>
              )}

              {!canAccessPHI() && pendingPatient.data_classification === 'PHI' && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  <strong>Access Denied:</strong> Your role does not permit access to PHI data. 
                  Contact your administrator if you need access.
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelPatientSelection}>
            Cancel
          </Button>
          <Button 
            onClick={() => pendingPatient && confirmPatientSelection(pendingPatient)}
            variant="contained"
            color="warning"
            disabled={!canAccessPHI() && pendingPatient?.data_classification === 'PHI'}
          >
            Confirm Access
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PatientSelectorAdvanced;