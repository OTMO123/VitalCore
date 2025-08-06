import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  details?: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'SUCCESS' | 'FAILURE';
}

export interface AuditFilters {
  startDate?: string;
  endDate?: string;
  userId?: string;
  action?: string;
  resource?: string;
  severity?: string;
  status?: string;
}

interface AuditState {
  logs: AuditLog[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  pageSize: number;
  filters: AuditFilters;
}

const initialState: AuditState = {
  logs: [],
  loading: false,
  error: null,
  totalCount: 0,
  currentPage: 1,
  pageSize: 20,
  filters: {},
};

export const fetchAuditLogs = createAsyncThunk(
  'audit/fetchLogs',
  async (params: { page?: number; pageSize?: number; filters?: AuditFilters }) => {
    const response = await fetch('/api/v1/audit/logs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch audit logs');
    }
    
    return response.json();
  }
);

const auditSlice = createSlice({
  name: 'audit',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<AuditFilters>) => {
      state.filters = action.payload;
      state.currentPage = 1;
    },
    setPage: (state, action: PayloadAction<number>) => {
      state.currentPage = action.payload;
    },
    setPageSize: (state, action: PayloadAction<number>) => {
      state.pageSize = action.payload;
      state.currentPage = 1;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAuditLogs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAuditLogs.fulfilled, (state, action) => {
        state.loading = false;
        state.logs = action.payload.logs;
        state.totalCount = action.payload.totalCount;
      })
      .addCase(fetchAuditLogs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch audit logs';
      });
  },
});

export const { setFilters, setPage, setPageSize, clearError } = auditSlice.actions;

export default auditSlice.reducer;