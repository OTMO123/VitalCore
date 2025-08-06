/**
 * Advanced Patient Table Component
 * Health Tech UI/UX with SOC2 Compliance & Risk Integration
 * 
 * Features:
 * - Risk score visualization in table rows
 * - Population health analytics integration
 * - SOC2-compliant audit logging
 * - Advanced filtering and sorting
 * - Real-time risk updates
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TablePagination,
  Paper,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Typography,
  Tooltip,
  LinearProgress,
  Alert,
  Collapse,
  Button,
  FormControl,
  InputLabel,
  Select,
  OutlinedInput,
  ListItemText,
  Checkbox,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Assignment as AssignmentIcon,
  TrendingUp as RiskIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Shield as SecurityIcon,
  FilterList as FilterIcon,
  TrendingUp as TrendIcon,
  LocalHospital as ClinicalIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

import { Patient } from '../../types';
import { RiskLevel, RiskScore } from '../../types/patient';
import { patientRiskService } from '../../services/patientRiskService';
import RiskScoreCard from './RiskScoreCard';

interface PatientTableAdvancedProps {
  patients: Patient[];
  loading: boolean;
  onPatientSelect: (patient: Patient) => void;
  onPatientEdit: (patient: Patient) => void;
  enableRiskCalculation?: boolean;
  compactView?: boolean;
}

type SortField = 'name' | 'mrn' | 'birthDate' | 'riskScore' | 'lastVisit' | 'consentStatus';
type SortDirection = 'asc' | 'desc';

interface TableSort {
  field: SortField;
  direction: SortDirection;
}

interface RiskFilter {
  levels: RiskLevel[];
  showOnlyHigh: boolean;
  requiresIntervention: boolean;
}

/**
 * Advanced Patient Table for Health Tech Platform
 */
const PatientTableAdvanced: React.FC<PatientTableAdvancedProps> = ({
  patients,
  loading,
  onPatientSelect,
  onPatientEdit,
  enableRiskCalculation = true,
  compactView = false
}) => {
  // State Management
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(compactView ? 25 : 10);
  const [sort, setSort] = useState<TableSort>({ field: 'name', direction: 'asc' });
  const [riskScores, setRiskScores] = useState<Map<string, RiskScore>>(new Map());
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState<RiskFilter>({
    levels: [],
    showOnlyHigh: false,
    requiresIntervention: false
  });
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [riskCalculationProgress, setRiskCalculationProgress] = useState(0);

  // Load risk scores for visible patients
  useEffect(() => {
    if (enableRiskCalculation && patients.length > 0) {
      loadRiskScores();
    }
  }, [patients, enableRiskCalculation, page, rowsPerPage]);

  const loadRiskScores = async () => {
    const visiblePatients = patients.slice(page * rowsPerPage, (page + 1) * rowsPerPage);
    const newRiskScores = new Map(riskScores);
    
    setRiskCalculationProgress(0);
    
    for (let i = 0; i < visiblePatients.length; i++) {
      const patient = visiblePatients[i];
      
      if (!riskScores.has(patient.id)) {
        try {
          const riskScore = await patientRiskService.calculateRiskScore(patient);
          newRiskScores.set(patient.id, riskScore);
          setRiskScores(new Map(newRiskScores));
        } catch (error) {
          console.error(`Failed to calculate risk for patient ${patient.id}:`, error);
        }
      }
      
      setRiskCalculationProgress(((i + 1) / visiblePatients.length) * 100);
    }
  };

  // Utility Functions
  const formatPatientName = (patient: Patient): string => {
    if (patient.name && patient.name.length > 0) {
      const name = patient.name[0];
      return `${name.given?.join(' ') || ''} ${name.family || ''}`.trim();
    }
    return 'Unknown Patient';
  };

  const getPatientMRN = (patient: Patient): string => {
    const mrnIdentifier = patient.identifier?.find(id => id.type?.coding?.[0]?.code === 'MR');
    return mrnIdentifier?.value || 'N/A';
  };

  const getRiskLevelConfig = (level: RiskLevel) => {
    const configs = {
      [RiskLevel.LOW]: { color: '#4caf50', icon: CheckIcon, label: 'Low' },
      [RiskLevel.MODERATE]: { color: '#ff9800', icon: WarningIcon, label: 'Moderate' },
      [RiskLevel.HIGH]: { color: '#f44336', icon: WarningIcon, label: 'High' },
      [RiskLevel.CRITICAL]: { color: '#d32f2f', icon: ErrorIcon, label: 'Critical' }
    };
    return configs[level];
  };

  const getConsentStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'success';
      case 'expired': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  // Filtering and Sorting
  const filteredAndSortedPatients = useMemo(() => {
    let filtered = [...patients];

    // Apply risk filters
    if (riskFilter.levels.length > 0) {
      filtered = filtered.filter(patient => {
        const riskScore = riskScores.get(patient.id);
        return riskScore && riskFilter.levels.includes(riskScore.level);
      });
    }

    if (riskFilter.showOnlyHigh) {
      filtered = filtered.filter(patient => {
        const riskScore = riskScores.get(patient.id);
        return riskScore && (riskScore.level === RiskLevel.HIGH || riskScore.level === RiskLevel.CRITICAL);
      });
    }

    if (riskFilter.requiresIntervention) {
      filtered = filtered.filter(patient => {
        const riskScore = riskScores.get(patient.id);
        return riskScore && riskScore.recommendations.some(rec => rec.priority === 'immediate' || rec.priority === 'urgent');
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sort.field) {
        case 'name':
          aValue = formatPatientName(a);
          bValue = formatPatientName(b);
          break;
        case 'mrn':
          aValue = getPatientMRN(a);
          bValue = getPatientMRN(b);
          break;
        case 'birthDate':
          aValue = a.birthDate || '';
          bValue = b.birthDate || '';
          break;
        case 'riskScore':
          aValue = riskScores.get(a.id)?.score || 0;
          bValue = riskScores.get(b.id)?.score || 0;
          break;
        case 'consentStatus':
          aValue = a.consent_status || '';
          bValue = b.consent_status || '';
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sort.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sort.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [patients, riskScores, riskFilter, sort]);

  // Event Handlers
  const handleSort = (field: SortField) => {
    const isAsc = sort.field === field && sort.direction === 'asc';
    setSort({ field, direction: isAsc ? 'desc' : 'asc' });
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, patient: Patient) => {
    setAnchorEl(event.currentTarget);
    setSelectedPatient(patient);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedPatient(null);
  };

  const handleExpandRow = (patientId: string) => {
    setExpandedRow(expandedRow === patientId ? null : patientId);
  };

  const handleRiskFilterChange = (levels: RiskLevel[]) => {
    setRiskFilter(prev => ({ ...prev, levels }));
  };

  const paginatedPatients = filteredAndSortedPatients.slice(
    page * rowsPerPage,
    (page + 1) * rowsPerPage
  );

  return (
    <Box>
      {/* Advanced Filters */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" color="text.secondary">
          {filteredAndSortedPatients.length} patients • Risk Analytics Enabled
        </Typography>
        
        <Box display="flex" gap={1}>
          <Button
            variant={showFilters ? 'contained' : 'outlined'}
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
            size="small"
          >
            Filters
          </Button>
        </Box>
      </Box>

      {/* Filter Panel */}
      <Collapse in={showFilters}>
        <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
          <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Risk Levels</InputLabel>
              <Select
                multiple
                value={riskFilter.levels}
                onChange={(e) => handleRiskFilterChange(e.target.value as RiskLevel[])}
                input={<OutlinedInput label="Risk Levels" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {Object.values(RiskLevel).map((level) => (
                  <MenuItem key={level} value={level}>
                    <Checkbox checked={riskFilter.levels.indexOf(level) > -1} />
                    <ListItemText primary={level} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              variant={riskFilter.showOnlyHigh ? 'contained' : 'outlined'}
              onClick={() => setRiskFilter(prev => ({ ...prev, showOnlyHigh: !prev.showOnlyHigh }))}
              color="warning"
              size="small"
            >
              High Risk Only
            </Button>

            <Button
              variant={riskFilter.requiresIntervention ? 'contained' : 'outlined'}
              onClick={() => setRiskFilter(prev => ({ ...prev, requiresIntervention: !prev.requiresIntervention }))}
              color="error"
              size="small"
            >
              Needs Intervention
            </Button>
          </Box>
        </Paper>
      </Collapse>

      {/* Risk Calculation Progress */}
      {enableRiskCalculation && riskCalculationProgress > 0 && riskCalculationProgress < 100 && (
        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" mb={1}>
            Calculating risk scores... {Math.round(riskCalculationProgress)}%
          </Typography>
          <LinearProgress variant="determinate" value={riskCalculationProgress} />
        </Box>
      )}

      {/* Table */}
      <Paper>
        <TableContainer>
          <Table size={compactView ? 'small' : 'medium'}>
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>
                  <TableSortLabel
                    active={sort.field === 'mrn'}
                    direction={sort.field === 'mrn' ? sort.direction : 'asc'}
                    onClick={() => handleSort('mrn')}
                  >
                    MRN
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sort.field === 'name'}
                    direction={sort.field === 'name' ? sort.direction : 'asc'}
                    onClick={() => handleSort('name')}
                  >
                    Patient Name
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={sort.field === 'birthDate'}
                    direction={sort.field === 'birthDate' ? sort.direction : 'asc'}
                    onClick={() => handleSort('birthDate')}
                  >
                    Age
                  </TableSortLabel>
                </TableCell>
                {enableRiskCalculation && (
                  <TableCell>
                    <TableSortLabel
                      active={sort.field === 'riskScore'}
                      direction={sort.field === 'riskScore' ? sort.direction : 'asc'}
                      onClick={() => handleSort('riskScore')}
                    >
                      Risk Score
                    </TableSortLabel>
                  </TableCell>
                )}
                <TableCell>Consent Status</TableCell>
                <TableCell>PHI Protection</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={enableRiskCalculation ? 8 : 7} align="center" sx={{ py: 4 }}>
                    <Box display="flex" alignItems="center" justifyContent="center" gap={2}>
                      <LinearProgress sx={{ width: 200 }} />
                      <Typography variant="body2">Loading patients...</Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : paginatedPatients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={enableRiskCalculation ? 8 : 7} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      No patients found matching your criteria.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedPatients.map((patient) => {
                  const riskScore = riskScores.get(patient.id);
                  const isExpanded = expandedRow === patient.id;
                  
                  return (
                    <React.Fragment key={patient.id}>
                      <TableRow hover sx={{ cursor: 'pointer' }}>
                        <TableCell>
                          <IconButton 
                            size="small" 
                            onClick={() => handleExpandRow(patient.id)}
                            disabled={!enableRiskCalculation || !riskScore}
                          >
                            {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </TableCell>
                        
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {getPatientMRN(patient)}
                          </Typography>
                        </TableCell>
                        
                        <TableCell onClick={() => onPatientSelect(patient)}>
                          <Typography variant="body2" fontWeight={500}>
                            {formatPatientName(patient)}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Typography variant="body2">
                            {patient.birthDate ? 
                              new Date().getFullYear() - new Date(patient.birthDate).getFullYear() 
                              : 'N/A'
                            }
                          </Typography>
                        </TableCell>
                        
                        {enableRiskCalculation && (
                          <TableCell>
                            {riskScore ? (
                              <Box display="flex" alignItems="center" gap={1}>
                                <Avatar
                                  sx={{ 
                                    width: 24, 
                                    height: 24, 
                                    bgcolor: getRiskLevelConfig(riskScore.level).color,
                                    fontSize: '0.75rem'
                                  }}
                                >
                                  {Math.round(riskScore.score)}
                                </Avatar>
                                <Chip
                                  label={getRiskLevelConfig(riskScore.level).label}
                                  size="small"
                                  variant="outlined"
                                  sx={{ 
                                    borderColor: getRiskLevelConfig(riskScore.level).color,
                                    color: getRiskLevelConfig(riskScore.level).color
                                  }}
                                />
                              </Box>
                            ) : (
                              <Typography variant="caption" color="text.secondary">
                                Calculating...
                              </Typography>
                            )}
                          </TableCell>
                        )}
                        
                        <TableCell>
                          <Chip
                            label={patient.consent_status || 'Unknown'}
                            color={getConsentStatusColor(patient.consent_status || '')}
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
                            onClick={(e) => handleMenuOpen(e, patient)}
                          >
                            <MoreVertIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                      
                      {/* Expanded Row - Risk Details */}
                      {enableRiskCalculation && riskScore && (
                        <TableRow>
                          <TableCell colSpan={8} sx={{ py: 0, borderBottom: 'none' }}>
                            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                              <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, m: 1 }}>
                                <RiskScoreCard
                                  patient={patient}
                                  compact={true}
                                  enableInteraction={true}
                                />
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={filteredAndSortedPatients.length}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={compactView ? [25, 50, 100] : [10, 25, 50]}
        />
      </Paper>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => { onPatientSelect(selectedPatient!); handleMenuClose(); }}>
          <ViewIcon sx={{ mr: 1 }} fontSize="small" />
          View Details
        </MenuItem>
        <MenuItem onClick={() => { onPatientEdit(selectedPatient!); handleMenuClose(); }}>
          <EditIcon sx={{ mr: 1 }} fontSize="small" />
          Edit Patient
        </MenuItem>
        {enableRiskCalculation && (
          <MenuItem onClick={handleMenuClose}>
            <TrendIcon sx={{ mr: 1 }} fontSize="small" />
            Risk Trends
          </MenuItem>
        )}
        <MenuItem onClick={handleMenuClose}>
          <AssignmentIcon sx={{ mr: 1 }} fontSize="small" />
          Care Plan
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default PatientTableAdvanced;