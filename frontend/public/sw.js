// Enhanced Service Worker for RAG Chatbot PWA
// Version 2.0 - Advanced offline functionality with data synchronization
const CACHE_VERSION = '2.0.0';
const CACHE_NAME = `rag-chatbot-static-v${CACHE_VERSION}`;
const API_CACHE_NAME = `rag-chatbot-api-v${CACHE_VERSION}`;
const RUNTIME_CACHE_NAME = `rag-chatbot-runtime-v${CACHE_VERSION}`;
const OFFLINE_QUEUE_NAME = `rag-chatbot-offline-v${CACHE_VERSION}`;

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/favicon.svg',
  '/pwa-192x192.png',
  '/pwa-512x512.png',
  '/offline.html'
];

// API endpoints with caching strategies
const API_CACHE_CONFIG = {
  // Cache-first with network fallback (long-lived data)
  'cache-first': [
    '/api/auth/profile',
    '/api/documents',
  ],
  // Network-first with cache fallback (dynamic data)
  'network-first': [
    '/api/contexts',
    '/api/chat/sessions',
    '/api/chat/history',
    '/api/upload/status',
  ],
  // Network-only (sensitive operations)
  'network-only': [
    '/api/auth/login',
    '/api/auth/logout',
    '/api/auth/refresh',
    '/api/upload',
  ],
  // Stale-while-revalidate (frequently accessed)
  'stale-while-revalidate': [
    '/api/user/preferences',
  ]
};

// Cache duration settings (in milliseconds)
const CACHE_DURATIONS = {
  static: 7 * 24 * 60 * 60 * 1000,      // 7 days
  api: 30 * 60 * 1000,                   // 30 minutes
  runtime: 24 * 60 * 60 * 1000,          // 24 hours
  offline: Infinity,                     // Never expire
};

// Advanced cache utilities
class CacheManager {
  static async isExpired(response, duration) {
    if (!response) return true;
    if (duration === Infinity) return false;
    
    const cachedTime = response.headers.get('sw-cached-at');
    if (!cachedTime) return true;
    
    return (Date.now() - parseInt(cachedTime)) > duration;
  }
  
  static async addToCache(cacheName, request, response) {
    const cache = await caches.open(cacheName);
    const responseClone = response.clone();
    
    // Add timestamp header
    const modifiedResponse = new Response(responseClone.body, {
      status: responseClone.status,
      statusText: responseClone.statusText,
      headers: {
        ...Object.fromEntries(responseClone.headers),
        'sw-cached-at': Date.now().toString(),
      }
    });
    
    await cache.put(request, modifiedResponse);
    return response;
  }
  
  static getCacheStrategy(url) {
    const pathname = new URL(url).pathname;
    
    for (const [strategy, patterns] of Object.entries(API_CACHE_CONFIG)) {
      if (patterns.some(pattern => pathname.startsWith(pattern))) {
        return strategy;
      }
    }
    
    return 'network-first'; // Default strategy
  }
  
  static async cleanExpiredCache(cacheName, duration) {
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();
    
    const cleanupPromises = requests.map(async (request) => {
      const response = await cache.match(request);
      if (await this.isExpired(response, duration)) {
        await cache.delete(request);
        console.log(`🧹 Cleaned expired cache entry: ${request.url}`);
      }
    });
    
    await Promise.all(cleanupPromises);
  }
}

// Enhanced install event with comprehensive caching
self.addEventListener('install', (event) => {
  console.log(`🔄 Service Worker v${CACHE_VERSION} installing...`);
  
  event.waitUntil(
    Promise.all([
      // Cache static assets
      caches.open(CACHE_NAME).then((cache) => {
        console.log('📦 Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      }),
      
      // Initialize other caches
      caches.open(API_CACHE_NAME),
      caches.open(RUNTIME_CACHE_NAME),
      caches.open(OFFLINE_QUEUE_NAME),
      
      // Initialize IndexedDB for offline queue
      initializeOfflineStorage(),
    ]).then(() => {
      console.log('✅ Service Worker installation complete');
      return self.skipWaiting();
    })
  );
});

// Enhanced activate event with comprehensive cleanup
self.addEventListener('activate', (event) => {
  console.log(`🚀 Service Worker v${CACHE_VERSION} activating...`);
  
  const currentCaches = [CACHE_NAME, API_CACHE_NAME, RUNTIME_CACHE_NAME, OFFLINE_QUEUE_NAME];
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (!currentCaches.includes(cacheName)) {
              console.log('🗑️ Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Clean expired entries from current caches
      CacheManager.cleanExpiredCache(API_CACHE_NAME, CACHE_DURATIONS.api),
      CacheManager.cleanExpiredCache(RUNTIME_CACHE_NAME, CACHE_DURATIONS.runtime),
      
      // Setup periodic cleanup
      setupPeriodicCleanup(),
      
    ]).then(() => {
      console.log('✅ Service Worker activation complete');
      // Take control of all clients immediately
      return self.clients.claim();
    })
  );
});

// Enhanced fetch event with multiple caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests (except for offline queue processing)
  if (request.method !== 'GET') {
    if (request.method === 'POST' && !navigator.onLine) {
      event.respondWith(handleOfflineRequest(request));
    }
    return;
  }

  // Handle API requests with strategy-based caching
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequestWithStrategy(request));
    return;
  }

  // Handle static assets with cache-first strategy
  event.respondWith(handleStaticRequest(request));
});

// Advanced strategy-based API request handler
async function handleApiRequestWithStrategy(request) {
  const url = new URL(request.url);
  const strategy = CacheManager.getCacheStrategy(url.href);
  
  console.log(`📡 Handling ${url.pathname} with ${strategy} strategy`);
  
  switch (strategy) {
    case 'cache-first':
      return handleCacheFirst(request);
    case 'network-first':
      return handleNetworkFirst(request);
    case 'network-only':
      return handleNetworkOnly(request);
    case 'stale-while-revalidate':
      return handleStaleWhileRevalidate(request);
    default:
      return handleNetworkFirst(request);
  }
}

// Cache-first strategy: Check cache first, fallback to network
async function handleCacheFirst(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse && !await CacheManager.isExpired(cachedResponse, CACHE_DURATIONS.api)) {
    console.log('📦 Serving from cache:', request.url);
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await CacheManager.addToCache(API_CACHE_NAME, request, networkResponse.clone());
      console.log('🌐 Updated cache from network:', request.url);
    }
    return networkResponse;
  } catch (error) {
    if (cachedResponse) {
      console.log('📦 Fallback to expired cache:', request.url);
      return cachedResponse;
    }
    return createOfflineResponse('Cache-first fallback failed');
  }
}

// Network-first strategy: Try network first, fallback to cache
async function handleNetworkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await CacheManager.addToCache(API_CACHE_NAME, request, networkResponse.clone());
      console.log('🌐 Network response cached:', request.url);
    }
    return networkResponse;
  } catch (error) {
    console.log('🔌 Network failed, trying cache:', request.url);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('📦 Serving stale cache:', request.url);
      return cachedResponse;
    }
    
    return createOfflineResponse('Network and cache unavailable');
  }
}

// Network-only strategy: Always use network, no caching
async function handleNetworkOnly(request) {
  try {
    return await fetch(request);
  } catch (error) {
    console.log('🔌 Network-only request failed:', request.url);
    return createOfflineResponse('Network unavailable for sensitive operation');
  }
}

// Stale-while-revalidate strategy: Serve from cache, update in background
async function handleStaleWhileRevalidate(request) {
  const cachedResponse = await caches.match(request);
  
  // Start network request in background
  const networkPromise = fetch(request).then(async (response) => {
    if (response.ok) {
      await CacheManager.addToCache(API_CACHE_NAME, request, response.clone());
      console.log('🔄 Background cache update:', request.url);
    }
    return response;
  }).catch(() => null);
  
  // Return cached response immediately if available
  if (cachedResponse && !await CacheManager.isExpired(cachedResponse, CACHE_DURATIONS.api)) {
    console.log('⚡ Serving from cache (revalidating):', request.url);
    return cachedResponse;
  }
  
  // Wait for network if no valid cache
  const networkResponse = await networkPromise;
  if (networkResponse) {
    return networkResponse;
  }
  
  // Fallback to expired cache or offline response
  if (cachedResponse) {
    console.log('📦 Fallback to expired cache:', request.url);
    return cachedResponse;
  }
  
  return createOfflineResponse('Stale-while-revalidate fallback failed');
}

// Handle offline POST requests by queuing them
async function handleOfflineRequest(request) {
  console.log('📱 Queuing offline request:', request.url);
  
  try {
    const requestData = {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body: await request.text(),
      timestamp: Date.now(),
    };
    
    await queueOfflineRequest(requestData);
    
    return new Response(
      JSON.stringify({
        success: true,
        message: 'Request queued for when online',
        offline: true,
        queueId: requestData.timestamp,
      }),
      {
        status: 202, // Accepted
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error) {
    console.error('Failed to queue offline request:', error);
    return createOfflineResponse('Failed to queue request');
  }
}

// Create standardized offline response
function createOfflineResponse(message) {
  return new Response(
    JSON.stringify({
      error: message,
      offline: true,
      timestamp: new Date().toISOString(),
    }),
    {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

// Enhanced static request handler with runtime caching
async function handleStaticRequest(request) {
  const url = new URL(request.url);
  
  // Try cache first for static assets
  const cachedResponse = await caches.match(request);
  if (cachedResponse && !await CacheManager.isExpired(cachedResponse, CACHE_DURATIONS.static)) {
    console.log('📦 Serving static asset from cache:', request.url);
    return cachedResponse;
  }

  // Try network
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses with appropriate cache
    if (networkResponse.ok) {
      const cacheName = STATIC_ASSETS.includes(url.pathname) ? CACHE_NAME : RUNTIME_CACHE_NAME;
      await CacheManager.addToCache(cacheName, request, networkResponse.clone());
      console.log('🌐 Cached static asset:', request.url);
    }
    
    return networkResponse;
  } catch (error) {
    console.log('🔌 Static request failed:', request.url, error);
    
    // Return expired cache if available
    if (cachedResponse) {
      console.log('📦 Serving expired static cache:', request.url);
      return cachedResponse;
    }
    
    // For navigation requests, return the cached index.html or offline page
    if (request.mode === 'navigate') {
      const cachedIndex = await caches.match('/');
      if (cachedIndex) {
        return cachedIndex;
      }
      
      // Return enhanced offline page
      return createOfflinePage();
    }
    
    // Return generic offline response for other assets
    return createOfflineResponse('Static asset unavailable offline');
  }
}

// Create enhanced offline page
function createOfflinePage() {
  return new Response(
    `<!DOCTYPE html>
    <html lang="en">
      <head>
        <title>Offline - RAG Chatbot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex; justify-content: center; align-items: center;
            min-height: 100vh; color: #333; text-align: center;
          }
          .container {
            background: white; padding: 3rem 2rem; border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 500px; margin: 1rem;
          }
          .icon { font-size: 5rem; margin-bottom: 1.5rem; }
          h1 { color: #333; margin-bottom: 1rem; font-size: 2rem; }
          p { color: #666; margin-bottom: 2rem; line-height: 1.6; }
          .actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
          button {
            background: #1976d2; color: white; border: none;
            padding: 0.875rem 1.5rem; border-radius: 8px; cursor: pointer;
            font-size: 1rem; font-weight: 500; transition: all 0.2s;
          }
          button:hover { background: #1565c0; transform: translateY(-1px); }
          button:active { transform: translateY(0); }
          .secondary { background: #f5f5f5; color: #333; }
          .secondary:hover { background: #eeeeee; }
          .status { margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; font-size: 0.875rem; }
          .online-indicator { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
          .offline { background-color: #f44336; }
          .online { background-color: #4caf50; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="icon">📱</div>
          <h1>You're Offline</h1>
          <p>Don't worry! The RAG Chatbot works offline too. Your data is cached locally and will sync when you're back online.</p>
          <div class="actions">
            <button onclick="window.location.reload()">Try Again</button>
            <button class="secondary" onclick="goHome()">Go Home</button>
          </div>
          <div class="status">
            <div>
              <span class="online-indicator offline"></span>
              <span id="status-text">Offline Mode</span>
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #999;">
              Last updated: <span id="timestamp">${new Date().toLocaleString()}</span>
            </div>
          </div>
        </div>
        
        <script>
          function goHome() { window.location.href = '/'; }
          
          // Monitor connection status
          function updateStatus() {
            const indicator = document.querySelector('.online-indicator');
            const statusText = document.getElementById('status-text');
            
            if (navigator.onLine) {
              indicator.className = 'online-indicator online';
              statusText.textContent = 'Back Online! Syncing...';
              setTimeout(() => window.location.reload(), 1000);
            }
          }
          
          // Check every 2 seconds
          setInterval(updateStatus, 2000);
          window.addEventListener('online', updateStatus);
        </script>
      </body>
    </html>`,
    {
      headers: { 'Content-Type': 'text/html' }
    }
  );
}

// Enhanced background sync with comprehensive queue processing
self.addEventListener('sync', (event) => {
  console.log('🔄 Background sync triggered:', event.tag);
  
  switch (event.tag) {
    case 'offline-requests':
      event.waitUntil(processOfflineQueue());
      break;
    case 'cache-cleanup':
      event.waitUntil(performCacheCleanup());
      break;
    case 'data-sync':
      event.waitUntil(syncOfflineData());
      break;
    default:
      console.log('Unknown sync tag:', event.tag);
  }
});

// Process all queued offline requests
async function processOfflineQueue() {
  console.log('📤 Processing offline request queue...');
  
  try {
    const queuedRequests = await getQueuedRequests();
    console.log(`Found ${queuedRequests.length} queued requests`);
    
    let processedCount = 0;
    let failedCount = 0;
    
    for (const request of queuedRequests) {
      try {
        const response = await fetch(request.url, {
          method: request.method,
          headers: request.headers,
          body: request.body,
        });
        
        if (response.ok) {
          await removeQueuedRequest(request.timestamp);
          processedCount++;
          
          // Notify client of successful sync
          notifyClients({
            type: 'REQUEST_SYNCED',
            requestId: request.timestamp,
            success: true,
          });
        } else {
          console.warn(`Request failed with status ${response.status}:`, request.url);
          failedCount++;
        }
      } catch (error) {
        console.error('Failed to process queued request:', error);
        failedCount++;
        
        // Consider removing requests that have failed too many times
        if (request.retryCount && request.retryCount > 3) {
          await removeQueuedRequest(request.timestamp);
          notifyClients({
            type: 'REQUEST_FAILED',
            requestId: request.timestamp,
            error: error.message,
          });
        } else {
          // Increment retry count
          await updateRequestRetryCount(request.timestamp);
        }
      }
    }
    
    console.log(`✅ Queue processing complete: ${processedCount} succeeded, ${failedCount} failed`);
    
    if (processedCount > 0) {
      notifyClients({
        type: 'SYNC_COMPLETE',
        processed: processedCount,
        failed: failedCount,
      });
    }
    
  } catch (error) {
    console.error('Queue processing failed:', error);
  }
}

// Sync offline data with server
async function syncOfflineData() {
  console.log('🔄 Syncing offline data...');
  
  try {
    const offlineData = await getOfflineData();
    
    if (offlineData && Object.keys(offlineData).length > 0) {
      const response = await fetch('/api/sync/offline-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await getAuthToken()}`,
        },
        body: JSON.stringify(offlineData),
      });
      
      if (response.ok) {
        await clearOfflineData();
        console.log('✅ Offline data synced successfully');
        
        notifyClients({
          type: 'DATA_SYNCED',
          success: true,
        });
      }
    }
  } catch (error) {
    console.error('Data sync failed:', error);
  }
}

// Perform comprehensive cache cleanup
async function performCacheCleanup() {
  console.log('🧹 Performing cache cleanup...');
  
  try {
    await Promise.all([
      CacheManager.cleanExpiredCache(API_CACHE_NAME, CACHE_DURATIONS.api),
      CacheManager.cleanExpiredCache(RUNTIME_CACHE_NAME, CACHE_DURATIONS.runtime),
      cleanupLargeCache(),
    ]);
    
    console.log('✅ Cache cleanup complete');
  } catch (error) {
    console.error('Cache cleanup failed:', error);
  }
}

// Clean up large cache entries to manage storage
async function cleanupLargeCache() {
  const maxCacheSize = 50 * 1024 * 1024; // 50MB limit
  
  for (const cacheName of [API_CACHE_NAME, RUNTIME_CACHE_NAME]) {
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();
    
    let totalSize = 0;
    const entriesWithSize = [];
    
    // Calculate sizes
    for (const request of requests) {
      const response = await cache.match(request);
      const size = await getResponseSize(response);
      totalSize += size;
      entriesWithSize.push({ request, size, response });
    }
    
    // If over limit, remove largest entries first
    if (totalSize > maxCacheSize) {
      entriesWithSize.sort((a, b) => b.size - a.size);
      
      let removedSize = 0;
      for (const entry of entriesWithSize) {
        await cache.delete(entry.request);
        removedSize += entry.size;
        
        if (totalSize - removedSize <= maxCacheSize) {
          break;
        }
      }
      
      console.log(`🧹 Cleaned ${removedSize} bytes from ${cacheName}`);
    }
  }
}

// Handle push notifications
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event);
  
  const options = {
    body: event.data ? event.data.text() : 'New message available',
    icon: '/pwa-192x192.png',
    badge: '/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open Chat',
        icon: '/chat-icon-96x96.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/close-icon-96x96.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('RAG Chatbot', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    // Open the chat page
    event.waitUntil(
      clients.openWindow('/chat')
    );
  } else if (event.action === 'close') {
    // Just close the notification
    return;
  } else {
    // Default action - open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// IndexedDB setup and utility functions
let db = null;

async function initializeOfflineStorage() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('RAGChatbotOfflineDB', 2);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      db = request.result;
      resolve(db);
    };
    
    request.onupgradeneeded = (event) => {
      const database = event.target.result;
      
      // Create offline requests store
      if (!database.objectStoreNames.contains('offlineRequests')) {
        const store = database.createObjectStore('offlineRequests', { keyPath: 'timestamp' });
        store.createIndex('url', 'url', { unique: false });
        store.createIndex('method', 'method', { unique: false });
      }
      
      // Create offline data store
      if (!database.objectStoreNames.contains('offlineData')) {
        database.createObjectStore('offlineData', { keyPath: 'key' });
      }
      
      // Create auth tokens store
      if (!database.objectStoreNames.contains('authTokens')) {
        database.createObjectStore('authTokens', { keyPath: 'type' });
      }
    };
  });
}

async function queueOfflineRequest(requestData) {
  if (!db) await initializeOfflineStorage();
  
  const transaction = db.transaction(['offlineRequests'], 'readwrite');
  const store = transaction.objectStore('offlineRequests');
  
  const requestWithMeta = {
    ...requestData,
    retryCount: 0,
    queuedAt: Date.now(),
  };
  
  await store.add(requestWithMeta);
  console.log('📱 Request queued:', requestData.url);
}

async function getQueuedRequests() {
  if (!db) await initializeOfflineStorage();
  
  const transaction = db.transaction(['offlineRequests'], 'readonly');
  const store = transaction.objectStore('offlineRequests');
  
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

async function removeQueuedRequest(timestamp) {
  if (!db) await initializeOfflineStorage();
  
  const transaction = db.transaction(['offlineRequests'], 'readwrite');
  const store = transaction.objectStore('offlineRequests');
  
  await store.delete(timestamp);
}

async function updateRequestRetryCount(timestamp) {
  if (!db) await initializeOfflineStorage();
  
  const transaction = db.transaction(['offlineRequests'], 'readwrite');
  const store = transaction.objectStore('offlineRequests');
  
  const request = await store.get(timestamp);
  if (request) {
    request.retryCount = (request.retryCount || 0) + 1;
    await store.put(request);
  }
}

async function getOfflineData() {
  if (!db) await initializeOfflineStorage();
  
  const transaction = db.transaction(['offlineData'], 'readonly');
  const store = transaction.objectStore('offlineData');
  
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => {
      const data = {};
      request.result.forEach(item => {
        data[item.key] = item.value;
      });
      resolve(data);
    };
    request.onerror = () => reject(request.error);
  });
}

async function clearOfflineData() {
  if (!db) await initializeOfflineStorage();
  
  const transaction = db.transaction(['offlineData'], 'readwrite');
  const store = transaction.objectStore('offlineData');
  
  await store.clear();
}

async function getAuthToken() {
  if (!db) await initializeOfflineStorage();
  
  const transaction = db.transaction(['authTokens'], 'readonly');
  const store = transaction.objectStore('authTokens');
  
  return new Promise((resolve) => {
    const request = store.get('access');
    request.onsuccess = () => {
      resolve(request.result?.token || null);
    };
    request.onerror = () => resolve(null);
  });
}

// Client notification helper
async function notifyClients(message) {
  const clients = await self.clients.matchAll({ includeUncontrolled: true });
  clients.forEach(client => {
    client.postMessage(message);
  });
}

// Utility functions
async function getResponseSize(response) {
  if (!response) return 0;
  
  try {
    const blob = await response.blob();
    return blob.size;
  } catch {
    return 0;
  }
}

// Setup periodic cleanup
async function setupPeriodicCleanup() {
  // Register periodic background sync for cleanup (if supported)
  if (self.registration && self.registration.periodicSync) {
    try {
      await self.registration.periodicSync.register('cache-cleanup', {
        minInterval: 24 * 60 * 60 * 1000, // 24 hours
      });
      console.log('✅ Periodic cleanup registered');
    } catch (error) {
      console.log('Periodic sync not available:', error.message);
    }
  }
}
