import { createSlice, PayloadAction, createSelector } from '@reduxjs/toolkit';

// ============================================
// UI SLICE STATE
// ============================================

interface UIState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  notifications: Notification[];
  loading: {
    global: boolean;
    components: Record<string, boolean>;
  };
  modals: {
    [key: string]: {
      open: boolean;
      data?: any;
    };
  };
  snackbar: {
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
    autoHideDuration?: number;
  };
  pagination: {
    [key: string]: {
      page: number;
      pageSize: number;
      total: number;
    };
  };
  filters: {
    [key: string]: Record<string, any>;
  };
  sortOptions: {
    [key: string]: {
      field: string;
      direction: 'asc' | 'desc';
    };
  };
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  timestamp: string;
  read: boolean;
  persistent?: boolean;
  actions?: Array<{
    label: string;
    action: string;
    data?: any;
  }>;
}

const initialState: UIState = {
  theme: 'light',
  sidebarOpen: true,
  notifications: [],
  loading: {
    global: false,
    components: {},
  },
  modals: {},
  snackbar: {
    open: false,
    message: '',
    severity: 'info',
  },
  pagination: {},
  filters: {},
  sortOptions: {},
};

// ============================================
// SLICE DEFINITION
// ============================================

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Theme Management
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
      localStorage.setItem('theme', action.payload);
    },
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', state.theme);
    },

    // Sidebar Management
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },

    // Loading Management
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.global = action.payload;
    },
    setComponentLoading: (state, action: PayloadAction<{ component: string; loading: boolean }>) => {
      state.loading.components[action.payload.component] = action.payload.loading;
    },
    clearComponentLoading: (state, action: PayloadAction<string>) => {
      delete state.loading.components[action.payload];
    },

    // Notification Management
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp' | 'read'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        read: false,
      };
      state.notifications.unshift(notification);
      
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },
    markNotificationRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification) {
        notification.read = true;
      }
    },
    markAllNotificationsRead: (state) => {
      state.notifications.forEach(notification => {
        notification.read = true;
      });
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },

    // Modal Management
    openModal: (state, action: PayloadAction<{ modal: string; data?: any }>) => {
      state.modals[action.payload.modal] = {
        open: true,
        data: action.payload.data,
      };
    },
    closeModal: (state, action: PayloadAction<string>) => {
      state.modals[action.payload] = {
        open: false,
        data: undefined,
      };
    },
    closeAllModals: (state) => {
      Object.keys(state.modals).forEach(modal => {
        state.modals[modal] = {
          open: false,
          data: undefined,
        };
      });
    },

    // Snackbar Management
    showSnackbar: (state, action: PayloadAction<{
      message: string;
      severity?: 'success' | 'error' | 'warning' | 'info';
      autoHideDuration?: number;
    }>) => {
      state.snackbar = {
        open: true,
        message: action.payload.message,
        severity: action.payload.severity || 'info',
        autoHideDuration: action.payload.autoHideDuration,
      };
    },
    hideSnackbar: (state) => {
      state.snackbar.open = false;
    },

    // Pagination Management
    setPagination: (state, action: PayloadAction<{
      key: string;
      page: number;
      pageSize: number;
      total: number;
    }>) => {
      state.pagination[action.payload.key] = {
        page: action.payload.page,
        pageSize: action.payload.pageSize,
        total: action.payload.total,
      };
    },
    updatePaginationPage: (state, action: PayloadAction<{ key: string; page: number }>) => {
      if (state.pagination[action.payload.key]) {
        state.pagination[action.payload.key].page = action.payload.page;
      }
    },
    updatePaginationPageSize: (state, action: PayloadAction<{ key: string; pageSize: number }>) => {
      if (state.pagination[action.payload.key]) {
        state.pagination[action.payload.key].pageSize = action.payload.pageSize;
        state.pagination[action.payload.key].page = 1; // Reset to first page
      }
    },

    // Filter Management
    setFilters: (state, action: PayloadAction<{ key: string; filters: Record<string, any> }>) => {
      state.filters[action.payload.key] = action.payload.filters;
    },
    updateFilter: (state, action: PayloadAction<{ key: string; filter: string; value: any }>) => {
      if (!state.filters[action.payload.key]) {
        state.filters[action.payload.key] = {};
      }
      state.filters[action.payload.key][action.payload.filter] = action.payload.value;
    },
    clearFilters: (state, action: PayloadAction<string>) => {
      state.filters[action.payload] = {};
    },

    // Sort Options Management
    setSortOptions: (state, action: PayloadAction<{
      key: string;
      field: string;
      direction: 'asc' | 'desc';
    }>) => {
      state.sortOptions[action.payload.key] = {
        field: action.payload.field,
        direction: action.payload.direction,
      };
    },
    toggleSortDirection: (state, action: PayloadAction<{ key: string; field: string }>) => {
      const current = state.sortOptions[action.payload.key];
      if (current && current.field === action.payload.field) {
        current.direction = current.direction === 'asc' ? 'desc' : 'asc';
      } else {
        state.sortOptions[action.payload.key] = {
          field: action.payload.field,
          direction: 'asc',
        };
      }
    },

    // Initialize UI from localStorage
    initializeUIFromStorage: (state) => {
      const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
      if (savedTheme) {
        state.theme = savedTheme;
      }

      const savedSidebarState = localStorage.getItem('sidebarOpen');
      if (savedSidebarState !== null) {
        state.sidebarOpen = JSON.parse(savedSidebarState);
      }
    },
  },
});

// ============================================
// EXPORTS
// ============================================

export const {
  setTheme,
  toggleTheme,
  toggleSidebar,
  setSidebarOpen,
  setGlobalLoading,
  setComponentLoading,
  clearComponentLoading,
  addNotification,
  markNotificationRead,
  markAllNotificationsRead,
  removeNotification,
  clearNotifications,
  openModal,
  closeModal,
  closeAllModals,
  showSnackbar,
  hideSnackbar,
  setPagination,
  updatePaginationPage,
  updatePaginationPageSize,
  setFilters,
  updateFilter,
  clearFilters,
  setSortOptions,
  toggleSortDirection,
  initializeUIFromStorage,
} = uiSlice.actions;

export default uiSlice.reducer;

// ============================================
// SELECTORS
// ============================================

// Basic selectors for primitive values (these are already memoized by default)
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;
export const selectSidebarOpen = (state: { ui: UIState }) => state.ui.sidebarOpen;
export const selectGlobalLoading = (state: { ui: UIState }) => state.ui.loading.global;
export const selectSnackbar = (state: { ui: UIState }) => state.ui.snackbar;

// Base selectors for complex data
const selectNotificationsBase = (state: { ui: UIState }) => state.ui.notifications;
const selectModalsBase = (state: { ui: UIState }) => state.ui.modals;
const selectPaginationBase = (state: { ui: UIState }) => state.ui.pagination;
const selectFiltersBase = (state: { ui: UIState }) => state.ui.filters;
const selectSortOptionsBase = (state: { ui: UIState }) => state.ui.sortOptions;

// Memoized selectors for arrays and objects
export const selectNotifications = createSelector(
  [selectNotificationsBase],
  (notifications) => notifications
);

export const selectUnreadNotifications = createSelector(
  [selectNotificationsBase],
  (notifications) => notifications.filter(n => !n.read)
);

// Factory functions for parameterized selectors with caching
const modalSelectorCache = new Map<string, ReturnType<typeof createSelector>>();
export const selectModal = (modal: string) => {
  if (!modalSelectorCache.has(modal)) {
    modalSelectorCache.set(
      modal,
      createSelector(
        [selectModalsBase],
        (modals) => modals[modal] || { open: false }
      )
    );
  }
  return modalSelectorCache.get(modal)!;
};

const componentLoadingSelectorCache = new Map<string, ReturnType<typeof createSelector>>();
export const selectComponentLoading = (component: string) => {
  if (!componentLoadingSelectorCache.has(component)) {
    componentLoadingSelectorCache.set(
      component,
      createSelector(
        [(state: { ui: UIState }) => state.ui.loading.components],
        (components) => components[component] || false
      )
    );
  }
  return componentLoadingSelectorCache.get(component)!;
};

const paginationSelectorCache = new Map<string, ReturnType<typeof createSelector>>();
export const selectPagination = (key: string) => {
  if (!paginationSelectorCache.has(key)) {
    paginationSelectorCache.set(
      key,
      createSelector(
        [selectPaginationBase],
        (pagination) => pagination[key]
      )
    );
  }
  return paginationSelectorCache.get(key)!;
};

const filtersSelectorCache = new Map<string, ReturnType<typeof createSelector>>();
export const selectFilters = (key: string) => {
  if (!filtersSelectorCache.has(key)) {
    filtersSelectorCache.set(
      key,
      createSelector(
        [selectFiltersBase],
        (filters) => filters[key] || {}
      )
    );
  }
  return filtersSelectorCache.get(key)!;
};

const sortOptionsSelectorCache = new Map<string, ReturnType<typeof createSelector>>();
export const selectSortOptions = (key: string) => {
  if (!sortOptionsSelectorCache.has(key)) {
    sortOptionsSelectorCache.set(
      key,
      createSelector(
        [selectSortOptionsBase],
        (sortOptions) => sortOptions[key]
      )
    );
  }
  return sortOptionsSelectorCache.get(key)!;
};