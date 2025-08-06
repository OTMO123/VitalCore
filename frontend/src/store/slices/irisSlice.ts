import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { SystemHealthResponse, LoadingState } from '@/types';
// Note: irisService import removed to avoid circular dependency during store initialization

// ============================================
// ASYNC THUNKS
// ============================================

export const fetchIRISHealth = createAsyncThunk(
  'iris/fetchHealth',
  async (_, { rejectWithValue }) => {
    try {
      const { irisService } = await import('@/services');
      const response = await irisService.getHealthSummary();
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch IRIS health');
    }
  }
);

// ============================================
// SLICE STATE
// ============================================

interface IRISState {
  healthData: SystemHealthResponse | null;
  loading: LoadingState;
  error: string | null;
}

const initialState: IRISState = {
  healthData: null,
  loading: 'idle',
  error: null,
};

// ============================================
// SLICE DEFINITION
// ============================================

const irisSlice = createSlice({
  name: 'iris',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchIRISHealth.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(fetchIRISHealth.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.healthData = action.payload;
        state.error = null;
      })
      .addCase(fetchIRISHealth.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = irisSlice.actions;
export default irisSlice.reducer;