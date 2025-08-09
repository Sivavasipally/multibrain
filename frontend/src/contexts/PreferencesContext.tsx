/**
 * Preferences Context for RAG Chatbot PWA
 * 
 * Provides global preferences state management with automatic synchronization,
 * caching, and real-time updates across components.
 * 
 * Features:
 * - Global preferences state management
 * - Automatic persistence and synchronization
 * - Real-time preference updates
 * - Offline support with sync on reconnect
 * - Type-safe preference access
 * - Category-based organization
 * 
 * Usage:
 *   import { usePreferences } from '../contexts/PreferencesContext';
 *   
 *   const { preferences, updatePreference, resetCategory } = usePreferences();
 *   
 *   // Update a preference
 *   await updatePreference('appearance', 'theme', 'dark');
 *   
 *   // Get a preference with fallback
 *   const theme = preferences.appearance?.theme || 'light';
 * 
 * Author: RAG Chatbot Development Team
 * Version: 2.0.0
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { preferencesAPI } from '../services/api';
import { useSnackbar } from './SnackbarContext';
import { useAuth } from './AuthContext';
import { errorService } from '../services/errorService';
import { syncService } from '../services/syncService';

// Preference type definitions
export interface AppearancePreferences {
  theme: 'light' | 'dark' | 'system';
  fontSize: 'small' | 'medium' | 'large';
  fontFamily: string;
  compactMode: boolean;
  language: string;
  timezone: string;
}

export interface ChatPreferences {
  defaultModel: string;
  messageLimit: number;
  autoSave: boolean;
  showTimestamps: boolean;
  enableNotifications: boolean;
  soundEffects: boolean;
  typingIndicator: boolean;
}

export interface SearchPreferences {
  defaultSearchType: 'semantic' | 'keyword' | 'hybrid';
  maxResults: number;
  enableAutoComplete: boolean;
  searchHistory: boolean;
  indexingEnabled: boolean;
}

export interface PrivacyPreferences {
  shareUsageData: boolean;
  enableAnalytics: boolean;
  dataRetentionDays: number;
  exportFormat: 'json' | 'csv' | 'markdown';
}

export interface PerformancePreferences {
  cacheSize: number;
  prefetchEnabled: boolean;
  compressionLevel: number;
  batchSize: number;
}

export interface UserPreferences {
  appearance: AppearancePreferences;
  chat: ChatPreferences;
  search: SearchPreferences;
  privacy: PrivacyPreferences;
  performance: PerformancePreferences;
}

// Default preferences
export const DEFAULT_PREFERENCES: UserPreferences = {
  appearance: {
    theme: 'system',
    fontSize: 'medium',
    fontFamily: 'system',
    compactMode: false,
    language: 'en',
    timezone: 'UTC',
  },
  chat: {
    defaultModel: 'gemini-pro',
    messageLimit: 100,
    autoSave: true,
    showTimestamps: true,
    enableNotifications: true,
    soundEffects: false,
    typingIndicator: true,
  },
  search: {
    defaultSearchType: 'hybrid',
    maxResults: 20,
    enableAutoComplete: true,
    searchHistory: true,
    indexingEnabled: true,
  },
  privacy: {
    shareUsageData: false,
    enableAnalytics: false,
    dataRetentionDays: 90,
    exportFormat: 'json',
  },
  performance: {
    cacheSize: 100,
    prefetchEnabled: true,
    compressionLevel: 6,
    batchSize: 10,
  }
};

// Context type definitions
interface PreferencesContextType {
  preferences: UserPreferences;
  loading: boolean;
  error: string | null;
  
  // Preference operations
  updatePreference: (category: keyof UserPreferences, key: string, value: any) => Promise<void>;
  updateCategoryPreferences: (category: keyof UserPreferences, updates: Partial<any>) => Promise<void>;
  resetCategory: (category: keyof UserPreferences) => Promise<void>;
  resetAllPreferences: () => Promise<void>;
  
  // Data operations
  exportPreferences: (format?: 'json' | 'csv') => Promise<void>;
  importPreferences: (preferences: Partial<UserPreferences>, merge?: boolean) => Promise<void>;
  
  // Template operations
  applyTemplate: (templateId: number) => Promise<void>;
  
  // Utility functions
  getPreference: <T>(category: keyof UserPreferences, key: string, fallback?: T) => T;
  hasChanges: boolean;
  lastSyncTime: Date | null;
}

// Create context
const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

// Provider component
interface PreferencesProviderProps {
  children: ReactNode;
}

export const PreferencesProvider: React.FC<PreferencesProviderProps> = ({ children }) => {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(false); // Don't load by default
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  
  const { showSuccess, showError, showWarning } = useSnackbar();
  const { isAuthenticated, loading: authLoading } = useAuth();

  /**
   * Load preferences from server
   */
  const loadPreferences = useCallback(async () => {
    // Don't load if not authenticated
    if (!isAuthenticated) {
      setPreferences(DEFAULT_PREFERENCES);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await preferencesAPI.getPreferences();
      
      if (response.success) {
        // Merge with defaults to ensure all preferences are present
        const mergedPreferences = { ...DEFAULT_PREFERENCES };
        
        for (const [category, categoryPrefs] of Object.entries(response.preferences)) {
          if (category in mergedPreferences) {
            mergedPreferences[category as keyof UserPreferences] = {
              ...mergedPreferences[category as keyof UserPreferences],
              ...categoryPrefs
            };
          }
        }
        
        setPreferences(mergedPreferences);
        setLastSyncTime(new Date());
        setHasChanges(false);
        
        console.log('✅ Preferences loaded successfully');
      } else {
        throw new Error(response.message || 'Failed to load preferences');
      }
    } catch (error: any) {
      console.error('Failed to load preferences:', error);
      setError(error.message);
      
      // Use cached preferences as fallback
      try {
        const cached = localStorage.getItem('userPreferences');
        if (cached) {
          const parsedPreferences = JSON.parse(cached);
          setPreferences(prev => ({ ...prev, ...parsedPreferences }));
          showWarning('Using offline preferences');
        }
      } catch (cacheError) {
        console.warn('Failed to load cached preferences:', cacheError);
      }
      
      errorService.reportError(error, {
        component: 'PreferencesContext',
        action: 'loadPreferences',
      }, 'medium');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, showWarning]);

  // Load preferences when authenticated
  useEffect(() => {
    let mounted = true;
    
    const initializePreferences = async () => {
      // If not authenticated, just use defaults
      if (!isAuthenticated) {
        setPreferences(DEFAULT_PREFERENCES);
        setLoading(false);
        return;
      }

      // Load from cache first for immediate UI update
      try {
        const cached = localStorage.getItem('userPreferences');
        if (cached && mounted) {
          const parsedPreferences = JSON.parse(cached);
          setPreferences(prev => ({ ...prev, ...parsedPreferences }));
        }
      } catch (error) {
        console.warn('Failed to load cached preferences:', error);
      }
      
      // Then load from server if authenticated
      if (mounted && isAuthenticated) {
        await loadPreferences();
      }
    };
    
    // Only initialize when auth loading is complete
    if (!authLoading) {
      initializePreferences();
    }
    
    return () => {
      mounted = false;
    };
  }, [isAuthenticated, authLoading, loadPreferences]); // Depend on authentication state

  // Setup sync service integration - only once
  useEffect(() => {
    const handleSyncComplete = () => {
      setLastSyncTime(new Date());
      setHasChanges(false);
    };

    const handleSyncError = () => {
      setHasChanges(true);
    };

    syncService.on('sync-complete', handleSyncComplete);
    syncService.on('sync-error', handleSyncError);

    return () => {
      syncService.off('sync-complete', handleSyncComplete);
      syncService.off('sync-error', handleSyncError);
    };
  }, []); // Empty dependency array - only run once

  // Auto-save preferences to localStorage with debouncing
  useEffect(() => {
    // Skip saving on initial load
    if (Object.keys(preferences).length === 0) return;
    
    const timeoutId = setTimeout(() => {
      try {
        localStorage.setItem('userPreferences', JSON.stringify(preferences));
      } catch (error) {
        console.warn('Failed to save preferences to localStorage:', error);
      }
    }, 500); // Debounce saves by 500ms
    
    return () => clearTimeout(timeoutId);
  }, [preferences]); // Only save when preferences actually change

  // loadPreferences function is defined above to avoid circular dependency

  /**
   * Update a single preference
   */
  const updatePreference = useCallback(async (
    category: keyof UserPreferences, 
    key: string, 
    value: any
  ) => {
    // Don't sync if not authenticated, just update locally
    if (!isAuthenticated) {
      setPreferences(prev => ({
        ...prev,
        [category]: {
          ...prev[category],
          [key]: value
        }
      }));
      return;
    }

    try {
      // Optimistic update
      setPreferences(prev => ({
        ...prev,
        [category]: {
          ...prev[category],
          [key]: value
        }
      }));
      
      setHasChanges(true);
      
      // Queue for sync if offline
      if (!navigator.onLine) {
        await syncService.queueForSync('preferences', {
          category,
          preferences: { [key]: value }
        }, 'update', 8);
        
        showWarning('Preference saved offline. Will sync when connected.');
        return;
      }
      
      // Update on server
      const response = await preferencesAPI.updateCategoryPreferences(category, {
        [key]: value
      });
      
      if (response.success) {
        setLastSyncTime(new Date());
        setHasChanges(false);
        console.log(`✅ Updated ${category}.${key} = ${value}`);
      } else {
        throw new Error(response.message || 'Failed to update preference');
      }
      
    } catch (error: any) {
      console.error('Failed to update preference:', error);
      
      // Revert optimistic update
      loadPreferences();
      
      showError(`Failed to update ${category} preference`);
      
      errorService.reportError(error, {
        component: 'PreferencesContext',
        action: 'updatePreference',
        category,
        key,
        value,
      }, 'medium');
    }
  }, [isAuthenticated, loadPreferences, showError, showWarning]);

  /**
   * Update multiple preferences in a category
   */
  const updateCategoryPreferences = useCallback(async (
    category: keyof UserPreferences,
    updates: Partial<any>
  ) => {
    // Don't sync if not authenticated, just update locally
    if (!isAuthenticated) {
      setPreferences(prev => ({
        ...prev,
        [category]: {
          ...prev[category],
          ...updates
        }
      }));
      return;
    }

    try {
      // Optimistic update
      setPreferences(prev => ({
        ...prev,
        [category]: {
          ...prev[category],
          ...updates
        }
      }));
      
      setHasChanges(true);
      
      // Queue for sync if offline
      if (!navigator.onLine) {
        await syncService.queueForSync('preferences', {
          category,
          preferences: updates
        }, 'update', 8);
        
        showWarning('Preferences saved offline. Will sync when connected.');
        return;
      }
      
      // Update on server
      const response = await preferencesAPI.updateCategoryPreferences(category, updates);
      
      if (response.success) {
        setLastSyncTime(new Date());
        setHasChanges(false);
        showSuccess(`Updated ${category} preferences`);
        console.log(`✅ Updated ${category} preferences:`, updates);
      } else {
        throw new Error(response.message || 'Failed to update preferences');
      }
      
    } catch (error: any) {
      console.error('Failed to update category preferences:', error);
      
      // Revert optimistic update
      loadPreferences();
      
      showError(`Failed to update ${category} preferences`);
      
      errorService.reportError(error, {
        component: 'PreferencesContext',
        action: 'updateCategoryPreferences',
        category,
        updates,
      }, 'medium');
    }
  }, [isAuthenticated, loadPreferences, showError, showSuccess, showWarning]);

  /**
   * Reset preferences for a category
   */
  const resetCategory = useCallback(async (category: keyof UserPreferences) => {
    try {
      if (!navigator.onLine) {
        await syncService.queueForSync('preferences', {
          category,
          action: 'reset'
        }, 'update', 9);
        
        showWarning('Reset queued offline. Will sync when connected.');
        return;
      }
      
      const response = await preferencesAPI.resetPreferences(category);
      
      if (response.success) {
        // Update local state with defaults
        setPreferences(prev => ({
          ...prev,
          [category]: DEFAULT_PREFERENCES[category]
        }));
        
        setLastSyncTime(new Date());
        setHasChanges(false);
        showSuccess(`Reset ${category} preferences to defaults`);
        console.log(`✅ Reset ${category} preferences`);
      } else {
        throw new Error(response.message || 'Failed to reset preferences');
      }
      
    } catch (error: any) {
      console.error('Failed to reset category preferences:', error);
      showError(`Failed to reset ${category} preferences`);
      
      errorService.reportError(error, {
        component: 'PreferencesContext',
        action: 'resetCategory',
        category,
      }, 'medium');
    }
  }, [showError, showSuccess, showWarning]);

  /**
   * Reset all preferences
   */
  const resetAllPreferences = useCallback(async () => {
    try {
      if (!navigator.onLine) {
        await syncService.queueForSync('preferences', {
          action: 'resetAll'
        }, 'update', 9);
        
        showWarning('Reset queued offline. Will sync when connected.');
        return;
      }
      
      const response = await preferencesAPI.resetPreferences();
      
      if (response.success) {
        setPreferences(DEFAULT_PREFERENCES);
        setLastSyncTime(new Date());
        setHasChanges(false);
        showSuccess('Reset all preferences to defaults');
        console.log('✅ Reset all preferences');
      } else {
        throw new Error(response.message || 'Failed to reset preferences');
      }
      
    } catch (error: any) {
      console.error('Failed to reset all preferences:', error);
      showError('Failed to reset preferences');
      
      errorService.reportError(error, {
        component: 'PreferencesContext',
        action: 'resetAllPreferences',
      }, 'medium');
    }
  }, [showError, showSuccess, showWarning]);

  /**
   * Export preferences
   */
  const exportPreferences = useCallback(async (format: 'json' | 'csv' = 'json') => {
    try {
      const response = await preferencesAPI.exportPreferences(format);
      
      // Create download link
      const blob = new Blob([response], { 
        type: format === 'json' ? 'application/json' : 'text/csv' 
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `preferences.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      showSuccess('Preferences exported successfully');
      
    } catch (error: any) {
      console.error('Failed to export preferences:', error);
      showError('Failed to export preferences');
      
      errorService.reportError(error, {
        component: 'PreferencesContext',
        action: 'exportPreferences',
        format,
      }, 'medium');
    }
  }, [showError, showSuccess]);

  /**
   * Import preferences
   */
  const importPreferences = useCallback(async (
    importedPreferences: Partial<UserPreferences>,
    merge: boolean = false
  ) => {
    try {
      const response = await preferencesAPI.importPreferences(importedPreferences, merge);
      
      if (response.success) {
        // Reload preferences
        await loadPreferences();
        showSuccess(`Imported ${response.imported_count} preferences`);
        
        if (response.errors && response.errors.length > 0) {
          showWarning(`${response.errors.length} preferences had errors`);
        }
      } else {
        throw new Error(response.message || 'Failed to import preferences');
      }
      
    } catch (error: any) {
      console.error('Failed to import preferences:', error);
      showError('Failed to import preferences');
      
      errorService.reportError(error, {
        component: 'PreferencesContext',
        action: 'importPreferences',
        merge,
      }, 'medium');
    }
  }, [loadPreferences, showError, showSuccess, showWarning]);

  /**
   * Apply preference template
   */
  const applyTemplate = useCallback(async (templateId: number) => {
    try {
      const response = await preferencesAPI.applyTemplate(templateId);
      
      if (response.success) {
        // Reload preferences
        await loadPreferences();
        showSuccess(`Applied template: ${response.applied_count} preferences updated`);
      } else {
        throw new Error(response.message || 'Failed to apply template');
      }
      
    } catch (error: any) {
      console.error('Failed to apply template:', error);
      showError('Failed to apply preference template');
      
      errorService.reportError(error, {
        component: 'PreferencesContext',
        action: 'applyTemplate',
        templateId,
      }, 'medium');
    }
  }, [loadPreferences, showError, showSuccess]);

  /**
   * Get a preference value with fallback
   */
  const getPreference = useCallback(<T,>(
    category: keyof UserPreferences,
    key: string,
    fallback?: T
  ): T => {
    const categoryPrefs = preferences[category] as any;
    const value = categoryPrefs?.[key];
    return value !== undefined ? value : fallback;
  }, [preferences]);

  // Context value
  const contextValue: PreferencesContextType = {
    preferences,
    loading,
    error,
    updatePreference,
    updateCategoryPreferences,
    resetCategory,
    resetAllPreferences,
    exportPreferences,
    importPreferences,
    applyTemplate,
    getPreference,
    hasChanges,
    lastSyncTime,
  };

  return (
    <PreferencesContext.Provider value={contextValue}>
      {children}
    </PreferencesContext.Provider>
  );
};

// Hook for using preferences
export const usePreferences = (): PreferencesContextType => {
  const context = useContext(PreferencesContext);
  if (context === undefined) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
};

// Export types and defaults
export type { UserPreferences, AppearancePreferences, ChatPreferences, SearchPreferences, PrivacyPreferences, PerformancePreferences };
export { PreferencesContext };
export default PreferencesProvider;