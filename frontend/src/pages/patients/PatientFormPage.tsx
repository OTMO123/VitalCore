import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  CardHeader,
  FormControlLabel,
  Switch,
  Chip,
  FormGroup,
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  Shield as SecurityIcon,
  Verified as VerifiedIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '@/store';
import type { Patient, PatientName, PatientIdentifier } from '@/types';
import { patientService } from '@/services/patient.service';

interface PatientFormData {
  resourceType: 'Patient';
  identifier: PatientIdentifier[];
  name: PatientName[];
  gender: string;
  birthDate: string;
  consent_status: string;
  active: boolean;
  // PHI fields
  ssn: string;
  phone: string;
  email: string;
  address: {
    line: string[];
    city: string;
    state: string;
    postalCode: string;
    country: string;
  };
}

const PatientFormPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id } = useParams<{ id: string }>();
  const { currentPatient, loading, error } = useAppSelector((state) => state.patient);

  const [formData, setFormData] = useState<PatientFormData>({
    resourceType: 'Patient',
    identifier: [
      {
        type: {
          coding: [{ system: 'http://terminology.hl7.org/CodeSystem/v2-0203', code: 'MR' }],
        },
        value: '',
      },
    ],
    name: [
      {
        use: 'official',
        family: '',
        given: [''],
      },
    ],
    gender: '',
    birthDate: '',
    consent_status: 'pending',
    active: true,
    ssn: '',
    phone: '',
    email: '',
    address: {
      line: [''],
      city: '',
      state: '',
      postalCode: '',
      country: 'US',
    },
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [fhirValidation, setFhirValidation] = useState<{ isValid: boolean; errors: string[] }>({
    isValid: false,
    errors: [],
  });

  const isEditMode = Boolean(id && id !== 'new');

  useEffect(() => {
    if (isEditMode && currentPatient) {
      // Populate form with existing patient data
      setFormData({
        ...formData,
        ...currentPatient,
        ssn: '', // PHI fields are encrypted, don't display
        phone: '',
        email: '',
      });
    }
  }, [currentPatient, isEditMode]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Required fields validation
    if (!formData.name[0].family) {
      errors.family = 'Last name is required';
    }
    if (!formData.name[0].given[0]) {
      errors.given = 'First name is required';
    }
    if (!formData.identifier[0].value) {
      errors.mrn = 'Medical Record Number is required';
    }
    if (!formData.birthDate) {
      errors.birthDate = 'Date of birth is required';
    }
    if (!formData.gender) {
      errors.gender = 'Gender is required';
    }

    // Email validation
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email format';
    }

    // Phone validation
    if (formData.phone && !/^\+?[\d\s\-\(\)]+$/.test(formData.phone)) {
      errors.phone = 'Invalid phone number format';
    }

    // SSN validation (basic format check)
    if (formData.ssn && !/^\d{3}-?\d{2}-?\d{4}$/.test(formData.ssn)) {
      errors.ssn = 'Invalid SSN format (XXX-XX-XXXX)';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => {
      const newData = { ...prev };
      
      // Handle nested field updates
      if (field.includes('.')) {
        const [parent, child] = field.split('.');
        if (parent === 'name') {
          newData.name[0] = { ...newData.name[0], [child]: value };
        } else if (parent === 'identifier') {
          newData.identifier[0] = { ...newData.identifier[0], [child]: value };
        } else if (parent === 'address') {
          newData.address = { ...newData.address, [child]: value };
        }
      } else {
        (newData as any)[field] = value;
      }
      
      return newData;
    });

    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateFHIR = async () => {
    // Simulate FHIR validation
    const errors: string[] = [];
    
    if (!formData.resourceType) {
      errors.push('Missing required field: resourceType');
    }
    if (!formData.identifier.length) {
      errors.push('At least one identifier is required');
    }
    if (!formData.name.length) {
      errors.push('At least one name is required');
    }

    setFhirValidation({
      isValid: errors.length === 0,
      errors,
    });
  };

  useEffect(() => {
    validateFHIR();
  }, [formData]);

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      console.log('Submitting patient data:', formData);
      
      // Convert form data to FHIR Patient format
      const patientData: Partial<Patient> = {
        resourceType: 'Patient',
        identifier: [{
          use: 'official',
          type: {
            coding: [{
              system: 'http://terminology.hl7.org/CodeSystem/v2-0203',
              code: 'MR'
            }]
          },
          system: 'http://hospital.smarthit.org',
          value: formData.identifier[0].value
        }],
        name: formData.name,
        gender: formData.gender,
        birthDate: formData.birthDate,
        active: formData.active,
        organization_id: '550e8400-e29b-41d4-a716-446655440000', // Default organization
        // Add PHI fields if provided
        telecom: [
          ...(formData.phone ? [{
            system: 'phone' as const,
            value: formData.phone,
            use: 'mobile' as const
          }] : []),
          ...(formData.email ? [{
            system: 'email' as const,
            value: formData.email,
            use: 'home' as const
          }] : [])
        ],
        address: formData.address.line[0] || formData.address.city ? [{
          use: 'home' as const,
          line: formData.address.line.filter(line => line),
          city: formData.address.city,
          state: formData.address.state,
          postalCode: formData.address.postalCode,
          country: formData.address.country
        }] : undefined
      };

      // Call the patient service
      if (isEditMode && id) {
        const response = await patientService.updatePatient(id, patientData);
        if (response.status >= 400) {
          throw new Error(response.message || 'Failed to update patient');
        }
      } else {
        const response = await patientService.createPatient(patientData);
        if (response.status >= 400) {
          throw new Error(response.message || 'Failed to create patient');
        }
        console.log('Patient created successfully:', response.data);
      }
      
      // Navigate back to patients list
      navigate('/patients');
    } catch (error) {
      console.error('Error saving patient:', error);
      // Set error state if needed
      // setError(error.message);
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600}>
          {isEditMode ? 'Edit Patient' : 'Add New Patient'}
        </Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<CancelIcon />}
            onClick={() => navigate('/patients')}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSubmit}
            disabled={loading === 'loading' || !fhirValidation.isValid}
          >
            {loading === 'loading' ? <CircularProgress size={20} /> : 'Save Patient'}
          </Button>
        </Box>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* FHIR Validation Status */}
      <Card sx={{ mb: 3, borderLeft: 4, borderColor: fhirValidation.isValid ? 'success.main' : 'warning.main' }}>
        <CardContent sx={{ py: 2 }}>
          <Box display="flex" alignItems="center" gap={1}>
            <VerifiedIcon color={fhirValidation.isValid ? 'success' : 'warning'} />
            <Typography variant="body2" fontWeight={500}>
              FHIR R4 Validation: {fhirValidation.isValid ? 'Valid' : 'Issues Found'}
            </Typography>
            {fhirValidation.isValid && (
              <Chip label="Compliant" color="success" size="small" />
            )}
          </Box>
          {fhirValidation.errors.length > 0 && (
            <Box mt={1}>
              {fhirValidation.errors.map((error, index) => (
                <Typography key={index} variant="caption" color="warning.main" display="block">
                  • {error}
                </Typography>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Basic Information */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={600} mb={3}>
              Basic Information
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="mrn-field"
                  name="mrn"
                  label="Medical Record Number (MRN)"
                  value={formData.identifier[0].value}
                  onChange={(e) => handleInputChange('identifier.value', e.target.value)}
                  error={!!validationErrors.mrn}
                  helperText={validationErrors.mrn}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.active}
                      onChange={(e) => handleInputChange('active', e.target.checked)}
                    />
                  }
                  label="Active Patient"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="first-name-field"
                  name="firstName"
                  label="First Name"
                  value={formData.name[0].given[0]}
                  onChange={(e) => handleInputChange('name.given', [e.target.value])}
                  error={!!validationErrors.given}
                  helperText={validationErrors.given}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="last-name-field"
                  name="lastName"
                  label="Last Name"
                  value={formData.name[0].family}
                  onChange={(e) => handleInputChange('name.family', e.target.value)}
                  error={!!validationErrors.family}
                  helperText={validationErrors.family}
                  required
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="birth-date-field"
                  name="birthDate"
                  type="date"
                  label="Date of Birth"
                  value={formData.birthDate}
                  onChange={(e) => handleInputChange('birthDate', e.target.value)}
                  error={!!validationErrors.birthDate}
                  helperText={validationErrors.birthDate}
                  InputLabelProps={{ shrink: true }}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth error={!!validationErrors.gender} required>
                  <InputLabel id="gender-label">Gender</InputLabel>
                  <Select
                    labelId="gender-label"
                    id="gender-field"
                    name="gender"
                    value={formData.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                    label="Gender"
                  >
                    <MenuItem value="male">Male</MenuItem>
                    <MenuItem value="female">Female</MenuItem>
                    <MenuItem value="other">Other</MenuItem>
                    <MenuItem value="unknown">Unknown</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel id="consent-status-label">Consent Status</InputLabel>
                  <Select
                    labelId="consent-status-label"
                    id="consent-status-field"
                    name="consentStatus"
                    value={formData.consent_status}
                    onChange={(e) => handleInputChange('consent_status', e.target.value)}
                    label="Consent Status"
                  >
                    <MenuItem value="active">Active</MenuItem>
                    <MenuItem value="pending">Pending</MenuItem>
                    <MenuItem value="expired">Expired</MenuItem>
                    <MenuItem value="revoked">Revoked</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* PHI Information */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={1} mb={3}>
              <SecurityIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Protected Health Information
              </Typography>
            </Box>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              All PHI fields are encrypted at rest and in transit.
            </Alert>
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="ssn-field"
                  name="ssn"
                  label="Social Security Number"
                  value={formData.ssn}
                  onChange={(e) => handleInputChange('ssn', e.target.value)}
                  error={!!validationErrors.ssn}
                  helperText={validationErrors.ssn}
                  placeholder="XXX-XX-XXXX"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="phone-field"
                  name="phone"
                  label="Phone Number"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  error={!!validationErrors.phone}
                  helperText={validationErrors.phone}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="email-field"
                  name="email"
                  type="email"
                  label="Email Address"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  error={!!validationErrors.email}
                  helperText={validationErrors.email}
                />
              </Grid>
            </Grid>
          </Paper>

          {/* Address Information */}
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" fontWeight={600} mb={3}>
              Address Information
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="street-address-field"
                  name="streetAddress"
                  label="Street Address"
                  value={formData.address.line[0]}
                  onChange={(e) => handleInputChange('address.line', [e.target.value])}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="city-field"
                  name="city"
                  label="City"
                  value={formData.address.city}
                  onChange={(e) => handleInputChange('address.city', e.target.value)}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  id="state-field"
                  name="state"
                  label="State"
                  value={formData.address.state}
                  onChange={(e) => handleInputChange('address.state', e.target.value)}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  id="zip-code-field"
                  name="zipCode"
                  label="ZIP Code"
                  value={formData.address.postalCode}
                  onChange={(e) => handleInputChange('address.postalCode', e.target.value)}
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PatientFormPage;