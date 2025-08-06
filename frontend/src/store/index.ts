import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

import authReducer from './slices/authSlice';
import patientReducer from './slices/patientSlice';
import irisReducer from './slices/irisSlice';
import auditReducer from './slices/auditSlice';
import uiReducer from './slices/uiSlice';
import viewReducer from './slices/viewSlice';

// ============================================
// STORE CONFIGURATION
// ============================================

export const store = configureStore({
  reducer: {
    auth: authReducer,
    patient: patientReducer,
    iris: irisReducer,
    audit: auditReducer,
    ui: uiReducer,
    view: viewReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

// ============================================
// TYPES
// ============================================

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// ============================================
// TYPED HOOKS
// ============================================

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

export default store;