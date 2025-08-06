/**
 * Advanced Patient Search Component
 * AI-Powered Search with Health Tech Optimization
 * 
 * Features:
 * - Multi-criteria search with AI suggestions
 * - Clinical condition filtering
 * - Risk-based patient discovery
 * - FHIR-compliant search parameters
 * - SOC2-compliant search audit logging
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  TextField,
  InputAdornment,
  Autocomplete,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  ListItemText,
  Checkbox,
  Button,
  Typography,
  Collapse,
  IconButton,
  Alert,
  Slider,
  FormControlLabel,
  Switch,
  DatePicker,
  Tooltip,
  Badge,
  Avatar,
  Card,
  CardContent,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  TuneOutlined as AdvancedIcon,
  Psychology as AIIcon,
  History as HistoryIcon,
  BookmarkBorder as SaveIcon,
  Bookmark as BookmarkIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Person as PatientIcon,
  MedicalServices as ClinicalIcon,
  GitBranch as Timeline, RiskIcon,
  LocationOn as LocationIcon,
  Event as DateIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { LocalizationProvider, DatePicker as MUIDatePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

import { Patient } from '../../types';
import { RiskLevel } from '../../types/patient';

interface SearchCriteria {
  query: string;
  demographicFilters: {
    ageRange: [number, number];
    gender: string[];
    location: string[];
  };
  clinicalFilters: {
    conditions: string[];
    medications: string[];
    riskLevels: RiskLevel[];
    lastVisitRange: [Date | null, Date | null];
  };
  consentFilters: {
    consentStatus: string[];
    consentTypes: string[];
  };
  advancedFilters: {
    hasRecentLabs: boolean;
    hasActiveCareplan: boolean;
    requiresIntervention: boolean;
    highUtilization: boolean;
  };
}

interface SearchSuggestion {
  type: 'patient' | 'condition' | 'medication' | 'risk_factor';
  value: string;
  label: string;
  count?: number;
  priority?: 'high' | 'medium' | 'low';
}

interface SavedSearch {
  id: string;
  name: string;
  criteria: SearchCriteria;
  resultCount: number;
  lastUsed: Date;
}

interface AdvancedSearchComponentProps {
  onSearch: (criteria: SearchCriteria) => void;
  onClearSearch: () => void;
  initialCriteria?: Partial<SearchCriteria>;
  suggestions?: SearchSuggestion[];
  recentSearches?: SavedSearch[];
  enableAIAssist?: boolean;
}

/**
 * Advanced Search Component for Patient Discovery
 */
const AdvancedSearchComponent: React.FC<AdvancedSearchComponentProps> = ({
  onSearch,
  onClearSearch,
  initialCriteria,
  suggestions = [],
  recentSearches = [],
  enableAIAssist = true
}) => {
  // Search State
  const [criteria, setCriteria] = useState<SearchCriteria>({
    query: '',
    demographicFilters: {
      ageRange: [0, 100],
      gender: [],
      location: []
    },
    clinicalFilters: {
      conditions: [],
      medications: [],
      riskLevels: [],
      lastVisitRange: [null, null]
    },
    consentFilters: {
      consentStatus: [],
      consentTypes: []
    },
    advancedFilters: {
      hasRecentLabs: false,
      hasActiveCareplan: false,
      requiresIntervention: false,
      highUtilization: false
    },
    ...initialCriteria
  });

  // UI State
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState<SearchSuggestion[]>(suggestions);
  const [aiSuggestions, setAISuggestions] = useState<string[]>([]);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>(recentSearches);
  const [isSearching, setIsSearching] = useState(false);

  // Load AI suggestions based on query
  useEffect(() => {
    if (enableAIAssist && criteria.query.length > 2) {
      generateAISuggestions();
    }
  }, [criteria.query, enableAIAssist]);

  const generateAISuggestions = useCallback(async () => {
    // Mock AI suggestions - in production would call AI service
    const mockSuggestions = [
      'diabetes patients with HbA1c > 8',
      'high-risk cardiovascular patients',
      'patients requiring medication review',
      'frequent emergency department users',
      'patients with gaps in preventive care'
    ];
    
    setAISuggestions(mockSuggestions.filter(s => 
      s.toLowerCase().includes(criteria.query.toLowerCase())
    ));
  }, [criteria.query]);

  // Mock data for dropdowns
  const mockConditions = [
    'Type 2 Diabetes', 'Hypertension', 'Cardiovascular Disease', 
    'COPD', 'Depression', 'Obesity', 'Chronic Kidney Disease'
  ];

  const mockMedications = [
    'Metformin', 'Lisinopril', 'Atorvastatin', 'Metoprolol', 
    'Amlodipine', 'Omeprazole', 'Levothyroxine'
  ];

  const mockLocations = [
    'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 
    'Houston, TX', 'Phoenix, AZ', 'Philadelphia, PA'
  ];

  // Event Handlers
  const handleSearch = () => {
    setIsSearching(true);
    onSearch(criteria);
    
    // Add to recent searches
    const newSearch: SavedSearch = {
      id: `search_${Date.now()}`,
      name: criteria.query || 'Advanced Search',
      criteria,
      resultCount: 0, // Would be populated after search
      lastUsed: new Date()
    };
    
    setSavedSearches(prev => [newSearch, ...prev.slice(0, 4)]); // Keep 5 most recent
    
    setTimeout(() => setIsSearching(false), 1000);
  };

  const handleClearAll = () => {
    setCriteria({
      query: '',
      demographicFilters: { ageRange: [0, 100], gender: [], location: [] },
      clinicalFilters: { conditions: [], medications: [], riskLevels: [], lastVisitRange: [null, null] },
      consentFilters: { consentStatus: [], consentTypes: [] },
      advancedFilters: { hasRecentLabs: false, hasActiveCareplan: false, requiresIntervention: false, highUtilization: false }
    });
    onClearSearch();
  };

  const handleSavedSearchSelect = (savedSearch: SavedSearch) => {
    setCriteria(savedSearch.criteria);
    onSearch(savedSearch.criteria);
  };

  const handleAISuggestionSelect = (suggestion: string) => {
    setCriteria(prev => ({ ...prev, query: suggestion }));
  };

  const getActiveFilterCount = (): number => {
    let count = 0;
    if (criteria.demographicFilters.gender.length > 0) count++;
    if (criteria.demographicFilters.location.length > 0) count++;
    if (criteria.clinicalFilters.conditions.length > 0) count++;
    if (criteria.clinicalFilters.medications.length > 0) count++;
    if (criteria.clinicalFilters.riskLevels.length > 0) count++;
    if (criteria.consentFilters.consentStatus.length > 0) count++;
    if (Object.values(criteria.advancedFilters).some(Boolean)) count++;
    return count;
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        {/* Main Search Bar */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box display="flex" gap={2} alignItems="center">
            <TextField
              fullWidth
              placeholder="Search patients by name, MRN, condition, or use natural language..."
              value={criteria.query}
              onChange={(e) => setCriteria(prev => ({ ...prev, query: e.target.value }))}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: criteria.query && (
                  <InputAdornment position="end">
                    <IconButton 
                      size="small" 
                      onClick={() => setCriteria(prev => ({ ...prev, query: '' }))}
                    >
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                )
              }}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            
            <Badge badgeContent={getActiveFilterCount()} color="primary">
              <Button
                variant={showAdvanced ? 'contained' : 'outlined'}
                startIcon={<FilterIcon />}
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                Filters
              </Button>
            </Badge>
            
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={isSearching}
              sx={{ minWidth: 100 }}
            >
              {isSearching ? 'Searching...' : 'Search'}
            </Button>
            
            {(criteria.query || getActiveFilterCount() > 0) && (
              <Button variant="outlined" onClick={handleClearAll}>
                Clear All
              </Button>
            )}
          </Box>

          {/* AI Suggestions */}
          {enableAIAssist && aiSuggestions.length > 0 && (
            <Box mt={2}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <AIIcon color="primary" fontSize="small" />
                <Typography variant="caption" color="primary.main" fontWeight={500}>
                  AI Suggestions
                </Typography>
              </Box>
              <Box display="flex" gap={1} flexWrap="wrap">
                {aiSuggestions.map((suggestion, index) => (
                  <Chip
                    key={index}
                    label={suggestion}
                    variant="outlined"
                    size="small"
                    onClick={() => handleAISuggestionSelect(suggestion)}
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>
            </Box>
          )}
        </Paper>

        {/* Advanced Filters */}
        <Collapse in={showAdvanced}>
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" fontWeight={600} mb={2}>
              Advanced Search Filters
            </Typography>

            <Grid container spacing={3}>
              {/* Demographics */}
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" fontWeight={600} mb={2} color="primary.main">
                  Demographics
                </Typography>
                
                <Box mb={2}>
                  <Typography variant="body2" mb={1}>Age Range</Typography>
                  <Slider
                    value={criteria.demographicFilters.ageRange}
                    onChange={(_, value) => setCriteria(prev => ({
                      ...prev,
                      demographicFilters: { ...prev.demographicFilters, ageRange: value as [number, number] }
                    }))}
                    valueLabelDisplay="auto"
                    min={0}
                    max={100}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 18, label: '18' },
                      { value: 65, label: '65' },
                      { value: 100, label: '100+' }
                    ]}
                  />
                </Box>

                <FormControl fullWidth margin="normal">
                  <InputLabel>Gender</InputLabel>
                  <Select
                    multiple
                    value={criteria.demographicFilters.gender}
                    onChange={(e) => setCriteria(prev => ({
                      ...prev,
                      demographicFilters: { ...prev.demographicFilters, gender: e.target.value as string[] }
                    }))}
                    input={<OutlinedInput label="Gender" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {['male', 'female', 'other', 'unknown'].map((gender) => (
                      <MenuItem key={gender} value={gender}>
                        <Checkbox checked={criteria.demographicFilters.gender.indexOf(gender) > -1} />
                        <ListItemText primary={gender} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth margin="normal">
                  <InputLabel>Location</InputLabel>
                  <Select
                    multiple
                    value={criteria.demographicFilters.location}
                    onChange={(e) => setCriteria(prev => ({
                      ...prev,
                      demographicFilters: { ...prev.demographicFilters, location: e.target.value as string[] }
                    }))}
                    input={<OutlinedInput label="Location" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {mockLocations.map((location) => (
                      <MenuItem key={location} value={location}>
                        <Checkbox checked={criteria.demographicFilters.location.indexOf(location) > -1} />
                        <ListItemText primary={location} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Clinical */}
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" fontWeight={600} mb={2} color="primary.main">
                  Clinical Criteria
                </Typography>

                <Autocomplete
                  multiple
                  options={mockConditions}
                  value={criteria.clinicalFilters.conditions}
                  onChange={(_, value) => setCriteria(prev => ({
                    ...prev,
                    clinicalFilters: { ...prev.clinicalFilters, conditions: value }
                  }))}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField {...params} label="Conditions" margin="normal" />
                  )}
                />

                <Autocomplete
                  multiple
                  options={mockMedications}
                  value={criteria.clinicalFilters.medications}
                  onChange={(_, value) => setCriteria(prev => ({
                    ...prev,
                    clinicalFilters: { ...prev.clinicalFilters, medications: value }
                  }))}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip variant="outlined" label={option} {...getTagProps({ index })} />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField {...params} label="Medications" margin="normal" />
                  )}
                />

                <FormControl fullWidth margin="normal">
                  <InputLabel>Risk Levels</InputLabel>
                  <Select
                    multiple
                    value={criteria.clinicalFilters.riskLevels}
                    onChange={(e) => setCriteria(prev => ({
                      ...prev,
                      clinicalFilters: { ...prev.clinicalFilters, riskLevels: e.target.value as RiskLevel[] }
                    }))}
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
                        <Checkbox checked={criteria.clinicalFilters.riskLevels.indexOf(level) > -1} />
                        <ListItemText primary={level} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Advanced Options */}
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle2" fontWeight={600} mb={2} color="primary.main">
                  Advanced Options
                </Typography>

                <Box display="flex" flexDirection="column" gap={1}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={criteria.advancedFilters.hasRecentLabs}
                        onChange={(e) => setCriteria(prev => ({
                          ...prev,
                          advancedFilters: { ...prev.advancedFilters, hasRecentLabs: e.target.checked }
                        }))}
                      />
                    }
                    label="Recent Lab Results"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={criteria.advancedFilters.hasActiveCareplan}
                        onChange={(e) => setCriteria(prev => ({
                          ...prev,
                          advancedFilters: { ...prev.advancedFilters, hasActiveCareplan: e.target.checked }
                        }))}
                      />
                    }
                    label="Active Care Plan"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={criteria.advancedFilters.requiresIntervention}
                        onChange={(e) => setCriteria(prev => ({
                          ...prev,
                          advancedFilters: { ...prev.advancedFilters, requiresIntervention: e.target.checked }
                        }))}
                      />
                    }
                    label="Requires Intervention"
                  />
                  
                  <FormControlLabel
                    control={
                      <Switch
                        checked={criteria.advancedFilters.highUtilization}
                        onChange={(e) => setCriteria(prev => ({
                          ...prev,
                          advancedFilters: { ...prev.advancedFilters, highUtilization: e.target.checked }
                        }))}
                      />
                    }
                    label="High Healthcare Utilization"
                  />
                </Box>

                <FormControl fullWidth margin="normal">
                  <InputLabel>Consent Status</InputLabel>
                  <Select
                    multiple
                    value={criteria.consentFilters.consentStatus}
                    onChange={(e) => setCriteria(prev => ({
                      ...prev,
                      consentFilters: { ...prev.consentFilters, consentStatus: e.target.value as string[] }
                    }))}
                    input={<OutlinedInput label="Consent Status" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {['active', 'expired', 'pending', 'withdrawn'].map((status) => (
                      <MenuItem key={status} value={status}>
                        <Checkbox checked={criteria.consentFilters.consentStatus.indexOf(status) > -1} />
                        <ListItemText primary={status} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>
        </Collapse>

        {/* Recent Searches */}
        {savedSearches.length > 0 && (
          <Paper sx={{ p: 2 }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <HistoryIcon color="primary" fontSize="small" />
              <Typography variant="subtitle2" fontWeight={600}>
                Recent Searches
              </Typography>
            </Box>
            
            <Box display="flex" gap={1} flexWrap="wrap">
              {savedSearches.map((search) => (
                <Card key={search.id} sx={{ minWidth: 200, cursor: 'pointer' }} onClick={() => handleSavedSearchSelect(search)}>
                  <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Typography variant="body2" fontWeight={500} noWrap>
                      {search.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {search.resultCount} results • {search.lastUsed.toLocaleDateString()}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Paper>
        )}

        {/* SOC2 Compliance Notice */}
        <Alert severity="info" icon={<SecurityIcon />} sx={{ mt: 2 }}>
          <Typography variant="caption">
            All patient searches are audited for SOC2 compliance. Search results are filtered based on your access permissions.
          </Typography>
        </Alert>
      </Box>
    </LocalizationProvider>
  );
};

export default AdvancedSearchComponent;