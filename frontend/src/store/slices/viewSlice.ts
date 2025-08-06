import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { RootState } from '../index';

export type ViewMode = 'admin' | 'doctor' | 'patient';

interface ViewState {
  currentView: ViewMode;
  availableViews: ViewMode[];
}

const initialState: ViewState = {
  currentView: 'admin',
  availableViews: ['admin', 'doctor', 'patient'],
};

const viewSlice = createSlice({
  name: 'view',
  initialState,
  reducers: {
    setCurrentView: (state, action: PayloadAction<ViewMode>) => {
      if (state.availableViews.includes(action.payload)) {
        state.currentView = action.payload;
      }
    },
    setAvailableViews: (state, action: PayloadAction<ViewMode[]>) => {
      state.availableViews = action.payload;
      // If current view is not available anymore, reset to first available
      if (!action.payload.includes(state.currentView) && action.payload.length > 0) {
        state.currentView = action.payload[0];
      }
    },
  },
});

export const { setCurrentView, setAvailableViews } = viewSlice.actions;

// Selectors
export const selectCurrentView = (state: RootState) => state.view.currentView;
export const selectAvailableViews = (state: RootState) => state.view.availableViews;

export default viewSlice.reducer;