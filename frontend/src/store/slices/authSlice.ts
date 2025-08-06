import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { User, LoginRequest, RegisterRequest, LoadingState } from '@/types';
// Note: authService import removed to avoid circular dependency during store initialization

// ============================================
// ASYNC THUNKS
// ============================================

export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const { authService } = await import('@/services');
      const response = await authService.login(credentials);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Login failed');
    }
  }
);

export const registerUser = createAsyncThunk(
  'auth/registerUser',
  async (userData: RegisterRequest, { rejectWithValue }) => {
    try {
      const { authService } = await import('@/services');
      const response = await authService.register(userData);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Registration failed');
    }
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const { authService } = await import('@/services');
      const response = await authService.getCurrentUser();
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to get user info');
    }
  }
);

export const updateUserProfile = createAsyncThunk(
  'auth/updateUserProfile',
  async (userData: Partial<User>, { rejectWithValue }) => {
    try {
      const { authService } = await import('@/services');
      const response = await authService.updateProfile(userData);
      if (response.error) {
        return rejectWithValue(response.error);
      }
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Profile update failed');
    }
  }
);

export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { rejectWithValue }) => {
    try {
      const { authService } = await import('@/services');
      await authService.logout();
      return true;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Logout failed');
    }
  }
);

// ============================================
// SLICE STATE
// ============================================

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: LoadingState;
  error: string | null;
  lastLogin: string | null;
  sessionTimeout: number | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  loading: 'idle',
  error: null,
  lastLogin: null,
  sessionTimeout: null,
};

// ============================================
// SLICE DEFINITION
// ============================================

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearAuth: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.loading = 'idle';
      state.error = null;
      state.lastLogin = null;
      state.sessionTimeout = null;
    },
    setSessionTimeout: (state, action: PayloadAction<number>) => {
      state.sessionTimeout = action.payload;
    },
    updateLastLogin: (state) => {
      state.lastLogin = new Date().toISOString();
    },
    initializeAuthFromToken: (state) => {
      // Check if user is authenticated from stored token
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          // Simple token expiry check
          const payload = JSON.parse(atob(token.split('.')[1]));
          const now = Date.now() / 1000;
          
          if (payload.exp > now) {
            const user = payload.user || payload;
            if (user) {
              state.user = user;
              state.isAuthenticated = true;
            }
          }
        } catch (error) {
          // Invalid token, ignore
          console.warn('Invalid token during initialization:', error);
        }
      }
    },
  },
  extraReducers: (builder) => {
    // Login User
    builder
      .addCase(loginUser.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.user = action.payload.user;
        state.isAuthenticated = true;
        state.lastLogin = new Date().toISOString();
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
        state.isAuthenticated = false;
        state.user = null;
      });

    // Register User
    builder
      .addCase(registerUser.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.user = action.payload;
        state.error = null;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      });

    // Get Current User
    builder
      .addCase(getCurrentUser.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.user = action.payload;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
        state.isAuthenticated = false;
        state.user = null;
      });

    // Update User Profile
    builder
      .addCase(updateUserProfile.pending, (state) => {
        state.loading = 'loading';
        state.error = null;
      })
      .addCase(updateUserProfile.fulfilled, (state, action) => {
        state.loading = 'succeeded';
        state.user = action.payload;
        state.error = null;
      })
      .addCase(updateUserProfile.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      });

    // Logout User
    builder
      .addCase(logoutUser.pending, (state) => {
        state.loading = 'loading';
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.loading = 'idle';
        state.user = null;
        state.isAuthenticated = false;
        state.error = null;
        state.lastLogin = null;
        state.sessionTimeout = null;
      })
      .addCase(logoutUser.rejected, (state, action) => {
        state.loading = 'failed';
        state.error = action.payload as string;
      });
  },
});

// ============================================
// EXPORTS
// ============================================

export const {
  clearError,
  clearAuth,
  setSessionTimeout,
  updateLastLogin,
  initializeAuthFromToken,
} = authSlice.actions;

export default authSlice.reducer;

// ============================================
// SELECTORS
// ============================================

export const selectAuth = (state: { auth: AuthState }) => state.auth;
export const selectUser = (state: { auth: AuthState }) => state.auth.user;
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.loading;
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error;