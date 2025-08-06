import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Patient, LoadingState } from '@/types';
// Note: patientService import removed to avoid circular dependency during store initialization

// ============================================
// TYPES
// ============================================

export interface PatientFilters {
  search?: string;
  gender?: string;
  ageMin?: number;
  ageMax?: number;
  departmentId?: string;
}

export interface PaginationInfo {
  page: number;
  size: number;
  total: number;
  pages: number;
}

export interface CreatePatientRequest {
  resourceType: "Patient";
  identifier: Array<{
    system: string;
    value: string;
    use?: string;
  }>;
  active: boolean;
  name: Array<{
    use: string;
    family: string;
    given: string[];
  }>;
  telecom?: Array<{
    system: string;
    value: string;
    use?: string;
  }>;
  gender?: string;
  birthDate?: string;
  address?: Array<{
    use: string;
    line: string[];
    city: string;
    state: string;
    postalCode: string;
    country: string;
  }>;
  consent_status: string;
  consent_types: string[];
  organization_id: string;
}

export interface UpdatePatientRequest {
  name?: Array<{
    use: string;
    family: string;
    given: string[];
  }>;
  telecom?: Array<{
    system: string;
    value: string;
    use?: string;
  }>;
  gender?: string;
  birthDate?: string;
  address?: Array<{
    use: string;
    line: string[];
    city: string;
    state: string;
    postalCode: string;
    country: string;
  }>;
  active?: boolean;
  consent_status?: string;
  consent_types?: string[];
}

// ============================================
// ASYNC THUNKS
// ============================================

export const fetchPatients = createAsyncThunk(
  'patient/fetchPatients',
  async (params: { page?: number; size?: number; search?: string; filters?: PatientFilters } = {}, { rejectWithValue }) => {
    try {
      const { patientService } = await import('@/services');
      const response = await patientService.getPatients(params);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch patients');
    }
  }
);

export const fetchPatientById = createAsyncThunk(
  'patient/fetchPatientById',
  async ({ patientId, purpose = 'treatment' }: { patientId: string; purpose?: string }, { rejectWithValue }) => {
    try {
      const { patientService } = await import('@/services');
      const response = await patientService.getPatientById(patientId, purpose);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch patient');
    }
  }
);

export const createPatient = createAsyncThunk(
  'patient/createPatient',
  async (patientData: CreatePatientRequest, { rejectWithValue }) => {
    try {
      const { patientService } = await import('@/services');
      const response = await patientService.createPatient(patientData);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create patient');
    }
  }
);

export const updatePatient = createAsyncThunk(
  'patient/updatePatient',
  async ({ id, data }: { id: string; data: UpdatePatientRequest }, { rejectWithValue }) => {
    try {
      const { patientService } = await import('@/services');
      const response = await patientService.updatePatient(id, data);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update patient');
    }
  }
);

export const deletePatient = createAsyncThunk(
  'patient/deletePatient',
  async ({ patientId, reason }: { patientId: string; reason: string }, { rejectWithValue }) => {
    try {
      const { patientService } = await import('@/services');
      const response = await patientService.deletePatient(patientId, reason);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return { patientId };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to delete patient');
    }
  }
);

export const searchPatients = createAsyncThunk(
  'patient/searchPatients',
  async (params: { query: string; filters?: PatientFilters; page?: number; size?: number }, { rejectWithValue }) => {
    try {
      const { patientService } = await import('@/services');
      const response = await patientService.searchPatients(params);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to search patients');
    }
  }
);

export const bulkImportPatients = createAsyncThunk(
  'patient/bulkImportPatients',
  async (file: File, { rejectWithValue }) => {
    try {
      const { patientService } = await import('@/services');
      const response = await patientService.bulkImportPatients(file);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to import patients');
    }
  }
);

export const exportPatients = createAsyncThunk(
  'patient/exportPatients',
  async (params: { format: string; filters?: PatientFilters }, { rejectWithValue }) => {
    try {
      const { patientService } = await import('@/services');
      const response = await patientService.exportPatients(params);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to export patients');
    }
  }
);

// ============================================
// SLICE STATE
// ============================================

interface PatientState {
  patients: Patient[];
  currentPatient: Patient | null;
  loading: LoadingState;
  error: string | null;
  filters: PatientFilters;
  pagination: PaginationInfo;
  searchResults: Patient[];
  searchLoading: boolean;
  bulkOperations: {
    importing: boolean;
    exporting: boolean;
    progress: number;
  };
  selectedPatients: string[];
}

const initialState: PatientState = {
  patients: [],
  currentPatient: null,
  loading: 'idle',
  error: null,
  filters: {},
  pagination: {
    page: 1,
    size: 20,
    total: 0,
    pages: 0
  },
  searchResults: [],
  searchLoading: false,
  bulkOperations: {
    importing: false,
    exporting: false,
    progress: 0
  },
  selectedPatients: []
};

// ============================================
// SLICE DEFINITION
// ============================================

const patientSlice = createSlice({
  name: 'patient',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
      state.loading = 'failed';
    },
    clearError: (state) => {
      state.error = null;
    },
    setCurrentPatient: (state, action) => {
      state.currentPatient = action.payload;
    },
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setPagination: (state, action) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    setSelectedPatients: (state, action) => {
      state.selectedPatients = action.payload;
    },
    togglePatientSelection: (state, action) => {
      const patientId = action.payload;
      const index = state.selectedPatients.indexOf(patientId);
      if (index === -1) {
        state.selectedPatients.push(patientId);
      } else {
        state.selectedPatients.splice(index, 1);
      }
    },
    clearSelection: (state) => {
      state.selectedPatients = [];
    },
    setBulkOperationProgress: (state, action) => {
      state.bulkOperations.progress = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch patients list
      .addCase(fetchPatients.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(fetchPatients.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.patients = action.payload.patients || action.payload;
        state.pagination = action.payload.pagination || {
          page: 1,
          size: 20,
          total: action.payload.total || action.payload.length,
          pages: Math.ceil((action.payload.total || action.payload.length) / 20)
        };
        state.error = null;
      })
      .addCase(fetchPatients.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      })
      // Fetch single patient
      .addCase(fetchPatientById.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(fetchPatientById.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.currentPatient = action.payload;
        state.error = null;
      })
      .addCase(fetchPatientById.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      })
      // Create patient
      .addCase(createPatient.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(createPatient.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.patients.unshift(action.payload);
        state.pagination.total += 1;
        state.error = null;
      })
      .addCase(createPatient.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      })
      // Update patient
      .addCase(updatePatient.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(updatePatient.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        const index = state.patients.findIndex(p => p.id === action.payload.id);
        if (index !== -1) {
          state.patients[index] = action.payload;
        }
        if (state.currentPatient?.id === action.payload.id) {
          state.currentPatient = action.payload;
        }
        state.error = null;
      })
      .addCase(updatePatient.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      })
      // Delete patient
      .addCase(deletePatient.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(deletePatient.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.patients = state.patients.filter(p => p.id !== action.payload.patientId);
        state.pagination.total -= 1;
        if (state.currentPatient?.id === action.payload.patientId) {
          state.currentPatient = null;
        }
        state.error = null;
      })
      .addCase(deletePatient.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      })
      // Search patients
      .addCase(searchPatients.pending, (state) => {
        state.searchLoading = true;
        state.error = null;
      })
      .addCase(searchPatients.fulfilled, (state, action) => {
        state.searchLoading = false;
        state.searchResults = action.payload.patients || action.payload;
        state.error = null;
      })
      .addCase(searchPatients.rejected, (state, action) => {
        state.searchLoading = false;
        state.error = action.payload as string;
      })
      // Bulk import patients
      .addCase(bulkImportPatients.pending, (state) => {
        state.bulkOperations.importing = true;
        state.bulkOperations.progress = 0;
        state.error = null;
      })
      .addCase(bulkImportPatients.fulfilled, (state, action) => {
        state.bulkOperations.importing = false;
        state.bulkOperations.progress = 100;
        // Refresh patient list after import
        state.error = null;
      })
      .addCase(bulkImportPatients.rejected, (state, action) => {
        state.bulkOperations.importing = false;
        state.bulkOperations.progress = 0;
        state.error = action.payload as string;
      })
      // Export patients
      .addCase(exportPatients.pending, (state) => {
        state.bulkOperations.exporting = true;
        state.error = null;
      })
      .addCase(exportPatients.fulfilled, (state) => {
        state.bulkOperations.exporting = false;
        state.error = null;
      })
      .addCase(exportPatients.rejected, (state, action) => {
        state.bulkOperations.exporting = false;
        state.error = action.payload as string;
      });
  },
});

export const { 
  setLoading,
  setError,
  clearError, 
  setCurrentPatient,
  setFilters,
  clearFilters,
  setPagination,
  setSelectedPatients,
  togglePatientSelection,
  clearSelection,
  setBulkOperationProgress
} = patientSlice.actions;

export default patientSlice.reducer;