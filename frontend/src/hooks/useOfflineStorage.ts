import { useState, useEffect, useCallback } from 'react';

interface OfflineMessage {
  id: string;
  sessionId: number;
  content: string;
  contextIds: number[];
  timestamp: number;
  token: string;
}

interface OfflineData {
  contexts: any[];
  sessions: any[];
  messages: OfflineMessage[];
  lastSync: number;
}

const DB_NAME = 'RAGChatbotDB';
const DB_VERSION = 1;
const STORES = {
  contexts: 'contexts',
  sessions: 'sessions',
  messages: 'messages',
  offlineMessages: 'offlineMessages',
};

export const useOfflineStorage = () => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [db, setDb] = useState<IDBDatabase | null>(null);

  // Initialize IndexedDB
  useEffect(() => {
    const initDB = async () => {
      try {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
          console.error('Failed to open IndexedDB');
        };

        request.onsuccess = () => {
          const database = request.result;
          setDb(database);
          setIsInitialized(true);
        };

        request.onupgradeneeded = (event) => {
          const database = (event.target as IDBOpenDBRequest).result;

          // Create object stores
          if (!database.objectStoreNames.contains(STORES.contexts)) {
            const contextsStore = database.createObjectStore(STORES.contexts, { keyPath: 'id' });
            contextsStore.createIndex('status', 'status', { unique: false });
          }

          if (!database.objectStoreNames.contains(STORES.sessions)) {
            const sessionsStore = database.createObjectStore(STORES.sessions, { keyPath: 'id' });
            sessionsStore.createIndex('updated_at', 'updated_at', { unique: false });
          }

          if (!database.objectStoreNames.contains(STORES.messages)) {
            const messagesStore = database.createObjectStore(STORES.messages, { keyPath: 'id' });
            messagesStore.createIndex('session_id', 'session_id', { unique: false });
          }

          if (!database.objectStoreNames.contains(STORES.offlineMessages)) {
            const offlineStore = database.createObjectStore(STORES.offlineMessages, { keyPath: 'id' });
            offlineStore.createIndex('timestamp', 'timestamp', { unique: false });
          }
        };
      } catch (error) {
        console.error('Error initializing IndexedDB:', error);
      }
    };

    initDB();
  }, []);

  // Generic function to store data
  const storeData = useCallback(async (storeName: string, data: any) => {
    if (!db) return false;

    try {
      const transaction = db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      if (Array.isArray(data)) {
        for (const item of data) {
          await store.put(item);
        }
      } else {
        await store.put(data);
      }

      return true;
    } catch (error) {
      console.error(`Error storing data in ${storeName}:`, error);
      return false;
    }
  }, [db]);

  // Generic function to get data
  const getData = useCallback(async (storeName: string, key?: any): Promise<any> => {
    if (!db) return null;

    try {
      const transaction = db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);

      if (key) {
        const request = store.get(key);
        return new Promise((resolve, reject) => {
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => reject(request.error);
        });
      } else {
        const request = store.getAll();
        return new Promise((resolve, reject) => {
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => reject(request.error);
        });
      }
    } catch (error) {
      console.error(`Error getting data from ${storeName}:`, error);
      return null;
    }
  }, [db]);

  // Store contexts offline
  const storeContexts = useCallback(async (contexts: any[]) => {
    return await storeData(STORES.contexts, contexts);
  }, [storeData]);

  // Get cached contexts
  const getCachedContexts = useCallback(async () => {
    return await getData(STORES.contexts);
  }, [getData]);

  // Store chat sessions offline
  const storeSessions = useCallback(async (sessions: any[]) => {
    return await storeData(STORES.sessions, sessions);
  }, [storeData]);

  // Get cached sessions
  const getCachedSessions = useCallback(async () => {
    return await getData(STORES.sessions);
  }, [getData]);

  // Store messages offline
  const storeMessages = useCallback(async (sessionId: number, messages: any[]) => {
    const messagesWithSessionId = messages.map(msg => ({
      ...msg,
      session_id: sessionId,
    }));
    return await storeData(STORES.messages, messagesWithSessionId);
  }, [storeData]);

  // Get cached messages for a session
  const getCachedMessages = useCallback(async (sessionId: number) => {
    if (!db) return [];

    try {
      const transaction = db.transaction([STORES.messages], 'readonly');
      const store = transaction.objectStore(STORES.messages);
      const index = store.index('session_id');
      const request = index.getAll(sessionId);

      return new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Error getting cached messages:', error);
      return [];
    }
  }, [db]);

  // Store offline message (for later sync)
  const storeOfflineMessage = useCallback(async (message: Omit<OfflineMessage, 'id'>) => {
    const offlineMessage: OfflineMessage = {
      ...message,
      id: `offline_${Date.now()}_${Math.random()}`,
    };
    return await storeData(STORES.offlineMessages, offlineMessage);
  }, [storeData]);

  // Get all offline messages
  const getOfflineMessages = useCallback(async (): Promise<OfflineMessage[]> => {
    return await getData(STORES.offlineMessages) || [];
  }, [getData]);

  // Remove offline message after successful sync
  const removeOfflineMessage = useCallback(async (messageId: string) => {
    if (!db) return false;

    try {
      const transaction = db.transaction([STORES.offlineMessages], 'readwrite');
      const store = transaction.objectStore(STORES.offlineMessages);
      await store.delete(messageId);
      return true;
    } catch (error) {
      console.error('Error removing offline message:', error);
      return false;
    }
  }, [db]);

  // Clear all cached data
  const clearCache = useCallback(async () => {
    if (!db) return false;

    try {
      const transaction = db.transaction(Object.values(STORES), 'readwrite');
      
      for (const storeName of Object.values(STORES)) {
        const store = transaction.objectStore(storeName);
        await store.clear();
      }

      return true;
    } catch (error) {
      console.error('Error clearing cache:', error);
      return false;
    }
  }, [db]);

  // Get cache size
  const getCacheSize = useCallback(async () => {
    if (!db) return 0;

    try {
      let totalSize = 0;
      const transaction = db.transaction(Object.values(STORES), 'readonly');

      for (const storeName of Object.values(STORES)) {
        const store = transaction.objectStore(storeName);
        const request = store.getAll();
        
        const data = await new Promise((resolve) => {
          request.onsuccess = () => resolve(request.result);
        });

        // Rough size calculation
        totalSize += JSON.stringify(data).length;
      }

      return totalSize;
    } catch (error) {
      console.error('Error calculating cache size:', error);
      return 0;
    }
  }, [db]);

  // Check if data exists in cache
  const hasCache = useCallback(async (storeName: string) => {
    if (!db) return false;

    try {
      const transaction = db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.count();

      return new Promise((resolve) => {
        request.onsuccess = () => resolve(request.result > 0);
        request.onerror = () => resolve(false);
      });
    } catch (error) {
      console.error(`Error checking cache for ${storeName}:`, error);
      return false;
    }
  }, [db]);

  return {
    isInitialized,
    storeContexts,
    getCachedContexts,
    storeSessions,
    getCachedSessions,
    storeMessages,
    getCachedMessages,
    storeOfflineMessage,
    getOfflineMessages,
    removeOfflineMessage,
    clearCache,
    getCacheSize,
    hasCache,
  };
};
