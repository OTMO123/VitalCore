import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';

import App from './App';
import { store } from './store';
import { createAppTheme } from './utils/theme';
import './styles/index.css';

// ============================================
// ERROR BOUNDARY
// ============================================

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<React.PropsWithChildren<{}>, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
          <h1 style={{ color: 'red' }}>Something went wrong</h1>
          <p>Error: {this.state.error?.message}</p>
          <pre style={{ background: '#f5f5f5', padding: '10px', overflow: 'auto' }}>
            {this.state.error?.stack}
          </pre>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: '10px', padding: '10px 20px' }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// ============================================
// ROOT COMPONENT
// ============================================

const Root: React.FC = () => {
  try {
    console.log('Root component rendering...');
    return (
      <React.StrictMode>
        <ErrorBoundary>
          <Provider store={store}>
            <BrowserRouter>
              <ThemeProvider theme={createAppTheme('light')}>
                <CssBaseline />
                <App />
              </ThemeProvider>
            </BrowserRouter>
          </Provider>
        </ErrorBoundary>
      </React.StrictMode>
    );
  } catch (error) {
    console.error('Root component initialization error:', error);
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h1>Initialization Error</h1>
        <p>Error: {String(error)}</p>
      </div>
    );
  }
};

// ============================================
// RENDER APPLICATION
// ============================================

console.log('About to render app...');

try {
  const rootElement = document.getElementById('root');
  console.log('Root element found:', rootElement);
  
  if (!rootElement) {
    throw new Error('Root element not found');
  }
  
  const reactRoot = ReactDOM.createRoot(rootElement);
  console.log('React root created');
  
  reactRoot.render(<Root />);
  console.log('App rendered successfully');
} catch (error) {
  console.error('Failed to render app:', error);
  
  // Fallback render
  const fallbackElement = document.getElementById('root');
  if (fallbackElement) {
    fallbackElement.innerHTML = `
      <div style="padding: 20px; color: red; font-family: Arial, sans-serif;">
        <h1>Failed to Start Application</h1>
        <p>Error: ${error}</p>
        <p>Check console for details</p>
      </div>
    `;
  }
}