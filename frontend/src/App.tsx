import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider as CustomThemeProvider } from './contexts/ThemeContext';
import { SnackbarProvider } from './contexts/SnackbarContext';
import { PreferencesProvider } from './contexts/PreferencesContext';
import { GlobalErrorBoundary, PageErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';
import Layout from './components/Layout/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Contexts from './pages/Contexts';
import Chat from './pages/Chat';
import OfflinePage from './pages/OfflinePage';
import Settings from './pages/Settings';
import AuthCallback from './pages/AuthCallback';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import InstallBanner from './components/PWA/InstallBanner';
import OfflineIndicator from './components/Offline/OfflineIndicator';
import { errorService } from './services/errorService';
import { syncService } from './services/syncService';

function App() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  useEffect(() => {
    // Initialize error service
    errorService.initialize();
    
    // Initialize sync service
    syncService.initialize().catch(error => {
      console.error('Failed to initialize sync service:', error);
    });
    
    // Add application startup breadcrumb
    errorService.addBreadcrumb('info', 'Application started', {
      userAgent: navigator.userAgent,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      online: navigator.onLine,
      syncServiceInitialized: true,
    });

    // Monitor online/offline status
    const handleOnline = () => {
      setIsOnline(true);
      errorService.addBreadcrumb('info', 'Network connection restored');
    };

    const handleOffline = () => {
      setIsOnline(false);
      errorService.addBreadcrumb('info', 'Network connection lost');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <GlobalErrorBoundary>
      <CustomThemeProvider>
        <ThemeProvider theme={createTheme()}>
          <CssBaseline />
          <SnackbarProvider>
            <AuthProvider>
              <PreferencesProvider>
              <Router>
                <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
                  <Routes>
                    {/* Public routes */}
                    <Route path="/login" element={
                      <PageErrorBoundary pageName="Login">
                        <Login />
                      </PageErrorBoundary>
                    } />
                    <Route path="/register" element={
                      <PageErrorBoundary pageName="Register">
                        <Register />
                      </PageErrorBoundary>
                    } />
                    <Route path="/auth/callback" element={
                      <PageErrorBoundary pageName="AuthCallback">
                        <AuthCallback />
                      </PageErrorBoundary>
                    } />
                    <Route path="/offline" element={
                      <PageErrorBoundary pageName="Offline">
                        <OfflinePage />
                      </PageErrorBoundary>
                    } />

                    {/* Protected routes */}
                    <Route path="/" element={
                      <ProtectedRoute>
                        <Layout />
                      </ProtectedRoute>
                    }>
                      <Route index element={<Navigate to="/dashboard" replace />} />
                      <Route path="dashboard" element={
                        <PageErrorBoundary pageName="Dashboard">
                          <Dashboard />
                        </PageErrorBoundary>
                      } />
                      <Route path="contexts" element={
                        <PageErrorBoundary pageName="Contexts">
                          <Contexts />
                        </PageErrorBoundary>
                      } />
                      <Route path="chat" element={
                        <PageErrorBoundary pageName="Chat">
                          <Chat />
                        </PageErrorBoundary>
                      } />
                      <Route path="chat/:sessionId" element={
                        <PageErrorBoundary pageName="Chat">
                          <Chat />
                        </PageErrorBoundary>
                      } />
                      <Route path="settings" element={
                        <PageErrorBoundary pageName="Settings">
                          <Settings />
                        </PageErrorBoundary>
                      } />
                    </Route>

                    {/* Catch all route */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Box>

                {/* PWA Components */}
                <InstallBanner />
                <OfflineIndicator 
                  showOnlineStatus={true}
                  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                />
              </Router>
              </PreferencesProvider>
            </AuthProvider>
          </SnackbarProvider>
        </ThemeProvider>
      </CustomThemeProvider>
    </GlobalErrorBoundary>
  );
}

export default App;
