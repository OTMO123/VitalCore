

## 📱 Frontend Architecture Patterns

### **1. Patient Management - Complete Implementation**

#### **Patient Service Layer**

```typescript
// frontend/src/services/patient.service.ts

import { apiClient } from './api';
import { 
  Patient, 
  CreatePatientRequest, 
  UpdatePatientRequest, 
  PatientFilters,
  PaginatedResponse 
} from '@/types/patient';

export class PatientService {
  private baseUrl = '/healthcare/patients';

  async getPatients(params: {
    page?: number;
    size?: number;
    search?: string;
    filters?: PatientFilters;
  } = {}): Promise<PaginatedResponse<Patient>> {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.size) queryParams.append('size', params.size.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.filters?.gender) queryParams.append('gender', params.filters.gender);
    if (params.filters?.ageMin) queryParams.append('age_min', params.filters.ageMin.toString());
    if (params.filters?.ageMax) queryParams.append('age_max', params.filters.ageMax.toString());

    const response = await apiClient.get<PaginatedResponse<Patient>>(
      `${this.baseUrl}?${queryParams.toString()}`
    );

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data!;
  }

  async getPatient(patientId: string, purpose: string = 'treatment'): Promise<Patient> {
    const response = await apiClient.get<Patient>(
      `${this.baseUrl}/${patientId}?purpose=${purpose}`
    );

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data!;
  }

  async createPatient(patientData: CreatePatientRequest): Promise<Patient> {
    const response = await apiClient.post<Patient>(this.baseUrl, patientData);

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data!;
  }

  async updatePatient(patientId: string, updates: UpdatePatientRequest): Promise<Patient> {
    const response = await apiClient.put<Patient>(`${this.baseUrl}/${patientId}`, updates);

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data!;
  }

  async deletePatient(patientId: string, reason: string): Promise<void> {
    const response = await apiClient.delete(
      `${this.baseUrl}/${patientId}?reason=${encodeURIComponent(reason)}`
    );

    if (response.error) {
      throw new Error(response.error);
    }
  }

  async getPatientAuditLog(patientId: string): Promise<any[]> {
    const response = await apiClient.get(`${this.baseUrl}/${patientId}/audit-log`);

    if (response.error) {
      throw new Error(response.error);
    }

    return response.data?.audit_logs || [];
  }

  async exportPatients(format: 'csv' | 'xlsx' | 'json', filters?: PatientFilters): Promise<Blob> {
    const queryParams = new URLSearchParams();
    queryParams.append('format', format);
    
    if (filters) {
      queryParams.append('filters', JSON.stringify(filters));
    }

    const response = await fetch(`/api/v1${this.baseUrl}/export?${queryParams.toString()}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response.blob();
  }

  async importPatients(file: File): Promise<{ imported: number; errors: string[] }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`/api/v1${this.baseUrl}/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error('Import failed');
    }

    return response.json();
  }
}

export const patientService = new PatientService();
```

#### **Enhanced Redux Store**

```typescript
// frontend/src/store/slices/patientSlice.ts

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Patient, CreatePatientRequest, UpdatePatientRequest, PatientFilters } from '@/types/patient';
import { patientService } from '@/services/patient.service';

interface PatientState {
  // Data
  patients: Patient[];
  currentPatient: Patient | null;
  selectedPatients: string[];
  
  // UI State
  loading: boolean;
  error: string | null;
  
  // Search & Filtering
  searchQuery: string;
  filters: PatientFilters;
  
  // Pagination
  pagination: {
    page: number;
    size: number;
    total: number;
    pages: number;
  };
  
  // Operations
  creating: boolean;
  updating: boolean;
  deleting: boolean;
  importing: boolean;
  exporting: boolean;
}

const initialState: PatientState = {
  patients: [],
  currentPatient: null,
  selectedPatients: [],
  loading: false,
  error: null,
  searchQuery: '',
  filters: {},
  pagination: {
    page: 1,
    size: 20,
    total: 0,
    pages: 0
  },
  creating: false,
  updating: false,
  deleting: false,
  importing: false,
  exporting: false
};

// Async Thunks
export const fetchPatients = createAsyncThunk(
  'patient/fetchPatients',
  async (params: { 
    page?: number; 
    size?: number; 
    search?: string; 
    filters?: PatientFilters 
  } = {}) => {
    const response = await patientService.getPatients(params);
    return response;
  }
);

export const fetchPatient = createAsyncThunk(
  'patient/fetchPatient',
  async ({ patientId, purpose }: { patientId: string; purpose?: string }) => {
    const patient = await patientService.getPatient(patientId, purpose);
    return patient;
  }
);

export const createPatient = createAsyncThunk(
  'patient/createPatient',
  async (patientData: CreatePatientRequest) => {
    const patient = await patientService.createPatient(patientData);
    return patient;
  }
);

export const updatePatient = createAsyncThunk(
  'patient/updatePatient',
  async ({ patientId, updates }: { patientId: string; updates: UpdatePatientRequest }) => {
    const patient = await patientService.updatePatient(patientId, updates);
    return patient;
  }
);

export const deletePatient = createAsyncThunk(
  'patient/deletePatient',
  async ({ patientId, reason }: { patientId: string; reason: string }) => {
    await patientService.deletePatient(patientId, reason);
    return patientId;
  }
);

export const importPatients = createAsyncThunk(
  'patient/importPatients',
  async (file: File) => {
    const result = await patientService.importPatients(file);
    return result;
  }
);

export const exportPatients = createAsyncThunk(
  'patient/exportPatients',
  async ({ format, filters }: { format: 'csv' | 'xlsx' | 'json'; filters?: PatientFilters }) => {
    const blob = await patientService.exportPatients(format, filters);
    
    // Trigger download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `patients_export_${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    return { format, timestamp: new Date().toISOString() };
  }
);

const patientSlice = createSlice({
  name: 'patient',
  initialState,
  reducers: {
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    
    setFilters: (state, action: PayloadAction<PatientFilters>) => {
      state.filters = action.payload;
    },
    
    clearFilters: (state) => {
      state.filters = {};
      state.searchQuery = '';
    },
    
    selectPatient: (state, action: PayloadAction<string>) => {
      if (!state.selectedPatients.includes(action.payload)) {
        state.selectedPatients.push(action.payload);
      }
    },
    
    deselectPatient: (state, action: PayloadAction<string>) => {
      state.selectedPatients = state.selectedPatients.filter(id => id !== action.payload);
    },
    
    selectAllPatients: (state) => {
      state.selectedPatients = state.patients.map(p => p.id);
    },
    
    clearSelection: (state) => {
      state.selectedPatients = [];
    },
    
    clearError: (state) => {
      state.error = null;
    },
    
    clearCurrentPatient: (state) => {
      state.currentPatient = null;
    }
  },
  
  extraReducers: (builder) => {
    // Fetch Patients
    builder
      .addCase(fetchPatients.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPatients.fulfilled, (state, action) => {
        state.loading = false;
        state.patients = action.payload.items;
        state.pagination = action.payload.pagination;
      })
      .addCase(fetchPatients.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch patients';
      });

    // Fetch Single Patient
    builder
      .addCase(fetchPatient.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPatient.fulfilled, (state, action) => {
        state.loading = false;
        state.currentPatient = action.payload;
      })
      .addCase(fetchPatient.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch patient';
      });

    // Create Patient
    builder
      .addCase(createPatient.pending, (state) => {
        state.creating = true;
        state.error = null;
      })
      .addCase(createPatient.fulfilled, (state, action) => {
        state.creating = false;
        state.patients.unshift(action.payload);
      })
      .addCase(createPatient.rejected, (state, action) => {
        state.creating = false;
        state.error = action.error.message || 'Failed to create patient';
      });

    // Update Patient
    builder
      .addCase(updatePatient.pending, (state) => {
        state.updating = true;
        state.error = null;
      })
      .addCase(updatePatient.fulfilled, (state, action) => {
        state.updating = false;
        const index = state.patients.findIndex(p => p.id === action.payload.id);
        if (index !== -1) {
          state.patients[index] = action.payload;
        }
        if (state.currentPatient?.id === action.payload.id) {
          state.currentPatient = action.payload;
        }
      })
      .addCase(updatePatient.rejected, (state, action) => {
        state.updating = false;
        state.error = action.error.message || 'Failed to update patient';
      });

    // Delete Patient
    builder
      .addCase(deletePatient.pending, (state) => {
        state.deleting = true;
        state.error = null;
      })
      .addCase(deletePatient.fulfilled, (state, action) => {
        state.deleting = false;
        state.patients = state.patients.filter(p => p.id !== action.payload);
        state.selectedPatients = state.selectedPatients.filter(id => id !== action.payload);
        if (state.currentPatient?.id === action.payload) {
          state.currentPatient = null;
        }
      })
      .addCase(deletePatient.rejected, (state, action) => {
        state.deleting = false;
        state.error = action.error.message || 'Failed to delete patient';
      });

    // Import Patients
    builder
      .addCase(importPatients.pending, (state) => {
        state.importing = true;
        state.error = null;
      })
      .addCase(importPatients.fulfilled, (state, action) => {
        state.importing = false;
        // Refresh patient list after import
      })
      .addCase(importPatients.rejected, (state, action) => {
        state.importing = false;
        state.error = action.error.message || 'Failed to import patients';
      });

    // Export Patients
    builder
      .addCase(exportPatients.pending, (state) => {
        state.exporting = true;
        state.error = null;
      })
      .addCase(exportPatients.fulfilled, (state) => {
        state.exporting = false;
      })
      .addCase(exportPatients.rejected, (state, action) => {
        state.exporting = false;
        state.error = action.error.message || 'Failed to export patients';
      });
  }
});

export const {
  setSearchQuery,
  setFilters,
  clearFilters,
  selectPatient,
  deselectPatient,
  selectAllPatients,
  clearSelection,
  clearError,
  clearCurrentPatient
} = patientSlice.actions;

export default patientSlice.reducer;

// Selectors
export const selectPatients = (state: any) => state.patient.patients;
export const selectCurrentPatient = (state: any) => state.patient.currentPatient;
export const selectPatientLoading = (state: any) => state.patient.loading;
export const selectPatientError = (state: any) => state.patient.error;
export const selectSelectedPatients = (state: any) => state.patient.selectedPatients;
export const selectPatientPagination = (state: any) => state.patient.pagination;
export const selectPatientFilters = (state: any) => state.patient.filters;
export const selectSearchQuery = (state: any) => state.patient.searchQuery;
```

#### **Complete Patient List Component**

```typescript
// frontend/src/components/patient/PatientListPage.tsx

import React, { useEffect, useState, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { 
  fetchPatients, 
  setSearchQuery, 
  setFilters, 
  clearFilters,
  selectPatient,
  clearSelection,
  deletePatient,
  exportPatients,
  importPatients,
  selectPatients,
  selectPatientLoading,
  selectPatientError,
  selectSelectedPatients,
  selectPatientPagination,
  selectPatientFilters,
  selectSearchQuery
} from '@/store/slices/patientSlice';
import { useDebounce } from '@/hooks/useDebounce';
import { usePermissions } from '@/hooks/usePermissions';
import { toast } from 'react-hot-toast';

// Components
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle 
} from '@/components/ui/alert-dialog';

// Icons
import { 
  Search, 
  Plus, 
  Filter, 
  Download, 
  Upload, 
  Trash2, 
  MoreHorizontal,
  Eye,
  Edit,
  FileText
} from 'lucide-react';

// Local Components
import PatientFilters from './PatientFilters';
import PatientTable from './PatientTable';
import CreatePatientDialog from './CreatePatientDialog';
import PatientDetailDrawer from './PatientDetailDrawer';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ErrorAlert from '@/components/common/ErrorAlert';
import Pagination from '@/components/common/Pagination';

const PatientListPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { canCreatePatient, canDeletePatient, canExportPatients } = usePermissions();

  // Redux state
  const patients = useAppSelector(selectPatients);
  const loading = useAppSelector(selectPatientLoading);
  const error = useAppSelector(selectPatientError);
  const selectedPatients = useAppSelector(selectSelectedPatients);
  const pagination = useAppSelector(selectPatientPagination);
  const filters = useAppSelector(selectPatientFilters);
  const searchQuery = useAppSelector(selectSearchQuery);

  // Local state
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [showPatientDetail, setShowPatientDetail] = useState(false);

  // Debounced search
  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  // Load patients on mount and when filters change
  useEffect(() => {
    dispatch(fetchPatients({
      page: pagination.page,
      size: pagination.size,
      search: debouncedSearchQuery,
      filters
    }));
  }, [dispatch, pagination.page, pagination.size, debouncedSearchQuery, filters]);

  // Handle search
  const handleSearch = useCallback((query: string) => {
    dispatch(setSearchQuery(query));
  }, [dispatch]);

  // Handle filter changes
  const handleFiltersChange = useCallback((newFilters: any) => {
    dispatch(setFilters(newFilters));
  }, [dispatch]);

  // Handle filter clear
  const handleClearFilters = useCallback(() => {
    dispatch(clearFilters());
  }, [dispatch]);

  // Handle page change
  const handlePageChange = useCallback((page: number) => {
    dispatch(fetchPatients({
      page,
      size: pagination.size,
      search: debouncedSearchQuery,
      filters
    }));
  }, [dispatch, pagination.size, debouncedSearchQuery, filters]);

  // Handle patient selection
  const handlePatientSelect = useCallback((patientId: string) => {
    dispatch(selectPatient(patientId));
  }, [dispatch]);

  // Handle patient view
  const handlePatientView = useCallback((patientId: string) => {
    setSelectedPatientId(patientId);
    setShowPatientDetail(true);
  }, []);

  // Handle patient edit
  const handlePatientEdit = useCallback((patientId: string) => {
    // Navigate to edit page or open edit dialog
    window.location.href = `/patients/${patientId}/edit`;
  }, []);

  // Handle patient delete
  const handlePatientDelete = useCallback(async (patientId: string) => {
    if (!deleteReason.trim()) {
      toast.error('Please provide a reason for deletion');
      return;
    }

    try {
      await dispatch(deletePatient({ patientId, reason: deleteReason })).unwrap();
      toast.success('Patient deleted successfully');
      setShowDeleteDialog(false);
      setDeleteReason('');
      setSelectedPatientId(null);
    } catch (error) {
      toast.error('Failed to delete patient');
    }
  }, [dispatch, deleteReason]);

  // Handle bulk export
  const handleExport = useCallback(async (format: 'csv' | 'xlsx' | 'json') => {
    try {
      await dispatch(exportPatients({ format, filters })).unwrap();
      toast.success('Export completed successfully');
    } catch (error) {
      toast.error('Export failed');
    }
  }, [dispatch, filters]);

  // Handle import
  const handleImport = useCallback(async (file: File) => {
    try {
      const result = await dispatch(importPatients(file)).unwrap();
      toast.success(`Imported ${result.imported} patients successfully`);
      if (result.errors.length > 0) {
        toast.error(`${result.errors.length} errors occurred during import`);
      }
      // Refresh patient list
      dispatch(fetchPatients({
        page: 1,
        size: pagination.size,
        search: debouncedSearchQuery,
        filters
      }));
    } catch (error) {
      toast.error('Import failed');
    }
  }, [dispatch, pagination.size, debouncedSearchQuery, filters]);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    dispatch(fetchPatients({
      page: pagination.page,
      size: pagination.size,
      search: debouncedSearchQuery,
      filters
    }));
  }, [dispatch, pagination.page, pagination.size, debouncedSearchQuery, filters]);

  if (error) {
    return (
      <ErrorAlert 
        message={error}
        onRetry={handleRefresh}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Patients</h1>
          <p className="text-muted-foreground">
            Manage patient records and healthcare information
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {canExportPatients && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => handleExport('csv')}>
                  Export as CSV
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('xlsx')}>
                  Export as Excel
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('json')}>
                  Export as JSON
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {canCreatePatient && (
            <Button
              onClick={() => setShowCreateDialog(true)}
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Patient
            </Button>
          )}
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search patients by name, email, phone, or MRN..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className={showFilters ? 'bg-muted' : ''}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
              {Object.keys(filters).length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {Object.keys(filters).length}
                </Badge>
              )}
            </Button>

            {Object.keys(filters).length > 0 && (
              <Button
                variant="ghost"
                onClick={handleClearFilters}
                size="sm"
              >
                Clear Filters
              </Button>
            )}
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t">
              <PatientFilters
                filters={filters}
                onFiltersChange={handleFiltersChange}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Patient Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              Patients ({pagination.total})
            </CardTitle>
            
            {selectedPatients.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {selectedPatients.length} selected
                </span>
                
                {canDeletePatient && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setShowDeleteDialog(true)}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Selected
                  </Button>
                )}
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => dispatch(clearSelection())}
                >
                  Clear Selection
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        
        <CardContent>
          {loading && patients.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : (
            <>
              <PatientTable
                patients={patients}
                selectedPatients={selectedPatients}
                onPatientSelect={handlePatientSelect}
                onPatientView={handlePatientView}
                onPatientEdit={handlePatientEdit}
                loading={loading}
              />
              
              {pagination.pages > 1 && (
                <div className="mt-6">
                  <Pagination
                    currentPage={pagination.page}
                    totalPages={pagination.pages}
                    onPageChange={handlePageChange}
                  />
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Create Patient Dialog */}
      <CreatePatientDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={() => {
          setShowCreateDialog(false);
          handleRefresh();
        }}
      />

      {/* Patient Detail Drawer */}
      <PatientDetailDrawer
        patientId={selectedPatientId}
        open={showPatientDetail}
        onOpenChange={setShowPatientDetail}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Patient(s)</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. Please provide a reason for deletion.
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          <div className="py-4">
            <Input
              placeholder="Reason for deletion..."
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
            />
          </div>
          
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => selectedPatientId && handlePatientDelete(selectedPatientId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default PatientListPage;
```

#### **Patient Table Component with Real-time Updates**

```typescript
// frontend/src/components/patient/PatientTable.tsx

import React, { useState } from 'react';
import { format } from 'date-fns';
import { Patient } from '@/types/patient';
import { usePermissions } from '@/hooks/usePermissions';

// Components
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Icons
import { MoreHorizontal, Eye, Edit, FileText, Phone, Mail } from 'lucide-react';

interface PatientTableProps {
  patients: Patient[];
  selectedPatients: string[];
  onPatientSelect: (patientId: string) => void;
  onPatientView: (patientId: string) => void;
  onPatientEdit: (patientId: string) => void;
  loading?: boolean;
}

const PatientTable: React.FC<PatientTableProps> = ({
  patients,
  selectedPatients,
  onPatientSelect,
  onPatientView,
  onPatientEdit,
  loading = false
}) => {
  const { canViewPatient, canEditPatient } = usePermissions();
  const [sortField, setSortField] = useState<keyof Patient>('lastName');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const handleSort = (field: keyof Patient) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const getPatientInitials = (patient: Patient) => {
    return `${patient.firstName?.[0] || ''}${patient.lastName?.[0] || ''}`.toUpperCase();
  };

  const calculateAge = (dateOfBirth: string) => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    
    return age;
  };

  const getGenderBadge = (gender: string) => {
    const variants = {
      'M': 'default',
      'F': 'secondary',
      'O': 'outline'
    } as const;
    
    return (
      <Badge variant={variants[gender as keyof typeof variants] || 'outline'}>
        {gender === 'M' ? 'Male' : gender === 'F' ? 'Female' : 'Other'}
      </Badge>
    );
  };

  if (patients.length === 0 && !loading) {
    return (
      <div className="text-center py-12">
        <div className="text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium">No patients found</h3>
          <p>Try adjusting your search criteria or create a new patient.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      {loading && (
        <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-10 flex items-center justify-center">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary" />
            <span className="text-sm text-muted-foreground">Loading...</span>
          </div>
        </div>
      )}
      
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={selectedPatients.length === patients.length && patients.length > 0}
                onCheckedChange={(checked) => {
                  if (checked) {
                    patients.forEach(patient => onPatientSelect(patient.id));
                  } else {
                    selectedPatients.forEach(patientId => onPatientSelect(patientId));
                  }
                }}
              />
            </TableHead>
            
            <TableHead>Patient</TableHead>
            
            <TableHead 
              className="cursor-pointer hover:bg-muted/50"
              onClick={() => handleSort('dateOfBirth')}
            >
              Age
            </TableHead>
            
            <TableHead>Gender</TableHead>
            
            <TableHead>Contact</TableHead>
            
            <TableHead>Insurance</TableHead>
            
            <TableHead 
              className="cursor-pointer hover:bg-muted/50"
              onClick={() => handleSort('createdAt')}
            >
              Created
            </TableHead>
            
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        
        <TableBody>
          {patients.map((patient) => (
            <TableRow 
              key={patient.id}
              className="hover:bg-muted/50 cursor-pointer"
              onClick={() => onPatientView(patient.id)}
            >
              <TableCell onClick={(e) => e.stopPropagation()}>
                <Checkbox
                  checked={selectedPatients.includes(patient.id)}
                  onCheckedChange={() => onPatientSelect(patient.id)}
                />
              </TableCell>
              
              <TableCell>
                <div className="flex items-center gap-3">
                  <Avatar>
                    <AvatarFallback className="bg-primary/10 text-primary">
                      {getPatientInitials(patient)}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div>
                    <div className="font-medium">
                      {patient.firstName} {patient.lastName}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      MRN: {patient.medicalRecordNumber}
                    </div>
                  </div>
                </div>
              </TableCell>
              
              <TableCell>
                {patient.dateOfBirth ? calculateAge(patient.dateOfBirth) : 'N/A'}
              </TableCell>
              
              <TableCell>
                {patient.gender ? getGenderBadge(patient.gender) : 'N/A'}
              </TableCell>
              
              <TableCell>
                <div className="space-y-1">
                  {patient.phone && (
                    <div className="flex items-center gap-1 text-sm">
                      <Phone className="h-3 w-3" />
                      {patient.phone}
                    </div>
                  )}
                  {patient.email && (
                    <div className="flex items-center gap-1 text-sm">
                      <Mail className="h-3 w-3" />
                      {patient.email}
                    </div>
                  )}
                </div>
              </TableCell>
              
              <TableCell>
                {patient.insuranceProvider ? (
                  <div>
                    <div className="font-medium text-sm">{patient.insuranceProvider}</div>
                    {patient.insuranceId && (
                      <div className="text-xs text-muted-foreground">
                        ID: {patient.insuranceId}
                      </div>
                    )}
                  </div>
                ) : (
                  <span className="text-muted-foreground">No insurance</span>
                )}
              </TableCell>
              
              <TableCell>
                {patient.createdAt ? format(new Date(patient.createdAt), 'MMM d, yyyy') : 'N/A'}
              </TableCell>
              
              <TableCell onClick={(e) => e.stopPropagation()}>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  
                  <DropdownMenuContent align="end">
                    {canViewPatient && (
                      <DropdownMenuItem onClick={() => onPatientView(patient.id)}>
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                    )}
                    
                    {canEditPatient && (
                      <DropdownMenuItem onClick={() => onPatientEdit(patient.id)}>
                        <Edit className="h-4 w-4 mr-2" />
                        Edit Patient
                      </DropdownMenuItem>
                    )}
                    
                    <DropdownMenuItem onClick={() => window.open(`/patients/${patient.id}/documents`)}>
                      <FileText className="h-4 w-4 mr-2" />
                      View Documents
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default PatientTable;
```

## 🔄 Real-time Dashboard Implementation

### **Live Dashboard with Server-Sent Events**

```typescript
// frontend/src/components/dashboard/LiveDashboard.tsx

import React, { useEffect, useState, useRef } from 'react';
import { useAppSelector } from '@/store/hooks';
import { DashboardData, SystemHealth } from '@/types/dashboard';
import { toast } from 'react-hot-toast';

// Components
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import LoadingSpinner from '@/components/common/LoadingSpinner';

// Icons
import { 
  Activity, 
  Users, 
  FileText, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Wifi,
  WifiOff
} from 'lucide-react';

const LiveDashboard: React.FC = () => {
  const { user } = useAppSelector(state => state.auth);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Initial data load
    loadDashboardData();
    
    // Setup real-time connection
    setupRealtimeConnection();
    
    return () => {
      cleanup();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await fetch('/api/v1/dashboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load dashboard data');
      }

      const data = await response.json();
      setDashboardData(data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      toast.error('Failed to load dashboard data');
    }
  };

  const setupRealtimeConnection = () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setError('No authentication token available');
      return;
    }

    try {
      // Create EventSource with authentication
      const eventSource = new EventSource(`/api/v1/dashboard/live-updates?token=${token}`);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setConnected(true);
        setError(null);
        console.log('Dashboard real-time connection established');
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setDashboardData(data);
          setLastUpdate(new Date());
        } catch (err) {
          console.error('Failed to parse dashboard update:', err);
        }
      };

      eventSource.onerror = (event) => {
        console.error('Dashboard EventSource error:', event);
        setConnected(false);
        
        // Attempt to reconnect after 5 seconds
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect dashboard...');
          setupRealtimeConnection();
        }, 5000);
      };

    } catch (err) {
      console.error('Failed to setup real-time connection:', err);
      setError('Failed to establish real-time connection');
      
      // Fallback to polling
      setupPolling();
    }
  };

  const setupPolling = () => {
    const pollInterval = setInterval(() => {
      loadDashboardData();
    }, 30000); // Poll every 30 seconds

    return () => clearInterval(pollInterval);
  };

  const cleanup = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection Status Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time overview of your healthcare system
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {connected ? (
              <>
                <Wifi className="h-4 w-4 text-green-500" />
                <Badge variant="outline" className="text-green-600 border-green-200">
                  Live
                </Badge>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-500" />
                <Badge variant="outline" className="text-red-600 border-red-200">
                  Offline
                </Badge>
              </>
            )}
          </div>
          
          {lastUpdate && (
            <div className="text-sm text-muted-foreground">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            <span className="text-destructive font-medium">Connection Error</span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{error}</p>
        </div>
      )}

      {/* Dashboard Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Total Patients */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Patients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.totalPatients}</div>
            <p className="text-xs text-muted-foreground">
              +{dashboardData.newPatientsToday} new today
            </p>
          </CardContent>
        </Card>

        {/* Active Users */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.activeUsers}</div>
            <p className="text-xs text-muted-foreground">
              {dashboardData.onlineUsers} currently online
            </p>
          </CardContent>
        </Card>

        {/* Documents */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.totalDocuments}</div>
            <p className="text-xs text-muted-foreground">
              +{dashboardData.documentsUploadedToday} uploaded today
            </p>
          </CardContent>
        </Card>

        {/* Security Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security Status</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {dashboardData.securityAlerts === 0 ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm font-medium text-green-600">Secure</span>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="text-sm font-medium text-red-600">
                    {dashboardData.securityAlerts} alerts
                  </span>
                </>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Last scan: {new Date(dashboardData.lastSecurityScan).toLocaleTimeString()}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          <SystemHealthDisplay health={dashboardData.systemHealth} />
        </CardContent>
      </Card>

      {/* Recent Activities */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activities</CardTitle>
        </CardHeader>
        <CardContent>
          <RecentActivitiesList activities={dashboardData.recentActivities} />
        </CardContent>
      </Card>
    </div>
  );
};

// System Health Component
const SystemHealthDisplay: React.FC<{ health: SystemHealth }> = ({ health }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return null;
    }
  };

  return (
    <div className="space-y-4">
      {Object.entries(health).map(([service, status]) => (
        <div key={service} className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon(status.status)}
            <span className="font-medium capitalize">{service.replace('_', ' ')}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge 
              variant="outline" 
              className={getStatusColor(status.status)}
            >
              {status.status}
            </Badge>
            
            {status.responseTime && (
              <span className="text-sm text-muted-foreground">
                {status.responseTime}ms
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

// Recent Activities Component
const RecentActivitiesList: React.FC<{ activities: any[] }> = ({ activities }) => {
  return (
    <div className="space-y-3">
      {activities.map((activity, index) => (
        <div key={index} className="flex items-start gap-3">
          <div className="mt-1">
            <Activity className="h-4 w-4 text-muted-foreground" />
          </div>
          
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{activity.description}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-muted-foreground">
                {activity.user}
              </span>
              <span className="text-xs text-muted-foreground">•</span>
              <span className="text-xs text-muted-foreground">
                {new Date(activity.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
          
          <Badge variant="outline" className="text-xs">
            {activity.type}
          </Badge>
        </div>
      ))}
    </div>
  );
};

export default LiveDashboard;
```

## 📋 Implementation Checklist

### **Week 1: Complete Backend APIs**
- [ ] Enhanced Patient Service with PHI encryption
- [ ] Complete CRUD operations with audit logging
- [ ] Role-based access control implementation
- [ ] Error handling and validation
- [ ] Comprehensive test coverage

### **Week 2: Frontend Integration**
- [ ] Redux store setup and integration
- [ ] Patient management components
- [ ] Real-time dashboard implementation
- [ ] Error handling and loading states
- [ ] File upload/download functionality

### **Week 3: Advanced Features**
- [ ] Search and filtering system
- [ ] Bulk operations (import/export)
- [ ] Real-time updates via SSE
- [ ] Advanced UI components
- [ ] Performance optimization

### **Week 4: Polish & Testing**
- [ ] End-to-end testing
- [ ] Performance testing
- [ ] Security validation
- [ ] Documentation
- [ ] Production deployment preparation

---

**Focus**: Build working features with solid foundations, ready for security enhancements without over-engineering the current implementation.