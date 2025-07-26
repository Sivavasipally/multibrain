import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider as CustomThemeProvider } from './contexts/ThemeContext';
import { SnackbarProvider } from './contexts/SnackbarContext';
import Layout from './components/Layout/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Contexts from './pages/Contexts';
import Chat from './pages/Chat';
import AuthCallback from './pages/AuthCallback';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import InstallBanner from './components/PWA/InstallBanner';
import OfflineIndicator from './components/PWA/OfflineIndicator';

function App() {
  return (
    <CustomThemeProvider>
      <ThemeProvider theme={createTheme()}>
        <CssBaseline />
        <SnackbarProvider>
          <AuthProvider>
            <Router>
              <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
                <Routes>
                  {/* Public routes */}
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/auth/callback" element={<AuthCallback />} />

                  {/* Protected routes */}
                  <Route path="/" element={
                    <ProtectedRoute>
                      <Layout />
                    </ProtectedRoute>
                  }>
                    <Route index element={<Navigate to="/dashboard" replace />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="contexts" element={<Contexts />} />
                    <Route path="chat" element={<Chat />} />
                    <Route path="chat/:sessionId" element={<Chat />} />
                  </Route>

                  {/* Catch all route */}
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </Box>

              {/* PWA Components */}
              <InstallBanner />
              <OfflineIndicator />
            </Router>
          </AuthProvider>
        </SnackbarProvider>
      </ThemeProvider>
    </CustomThemeProvider>
  );
}

export default App;
