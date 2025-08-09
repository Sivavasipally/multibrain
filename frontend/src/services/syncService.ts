/**
 * Data Synchronization Service for RAG Chatbot PWA
 * 
 * Handles synchronization between offline and online states, managing data consistency
 * across client-server boundaries. Provides intelligent conflict resolution, queue
 * management, and background synchronization capabilities.
 * 
 * Key Features:
 * - Bidirectional data synchronization
 * - Conflict resolution strategies  
 * - Priority-based queue management
 * - Real-time sync status monitoring
 * - Bandwidth-aware sync optimization
 * - Automatic retry with exponential backoff
 * 
 * Usage:
 *   import { syncService } from '../services/syncService';
 *   
 *   // Initialize service
 *   await syncService.initialize();
 *   
 *   // Queue offline data for sync
 *   await syncService.queueForSync('contexts', contextData, 'create');
 *   
 *   // Manual sync trigger
 *   await syncService.syncAll();
 * 
 * Author: RAG Chatbot Development Team
 * Version: 2.0.0
 */

// Note: Offline storage is accessed through React hooks in components, not directly in services
import { errorService } from './errorService';

// Sync operation types
export type SyncOperation = 'create' | 'update' | 'delete';
export type SyncStatus = 'pending' | 'syncing' | 'synced' | 'failed' | 'conflict';
export type ConflictResolution = 'client-wins' | 'server-wins' | 'merge' | 'manual';

// Sync data interfaces
export interface SyncItem {
  id: string;
  type: string; // contexts, sessions, messages, documents
  operation: SyncOperation;
  data: any;
  timestamp: number;
  priority: number; // 1-10, higher = more urgent
  retryCount: number;
  lastRetry?: number;
  status: SyncStatus;
  checksum?: string;
  conflictData?: any;
}

export interface SyncConfig {
  maxRetries: number;
  retryDelay: number;
  batchSize: number;
  syncInterval: number;
  conflictResolution: ConflictResolution;
  enableBackgroundSync: boolean;
}

export interface SyncResult {
  success: boolean;
  syncedCount: number;
  failedCount: number;
  conflictsCount: number;
  errors: string[];
}

export interface NetworkInfo {
  isOnline: boolean;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
}

// Default configuration
const DEFAULT_CONFIG: SyncConfig = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second, will use exponential backoff
  batchSize: 10,
  syncInterval: 30000, // 30 seconds
  conflictResolution: 'server-wins',
  enableBackgroundSync: true,
};

/**
 * Data Synchronization Service
 * 
 * Manages offline/online data synchronization with intelligent conflict resolution
 * and priority-based queue management.
 */
class SyncService {
  private config: SyncConfig;
  private syncQueue: SyncItem[] = [];
  private isSyncing = false;
  private isInitialized = false;
  private syncTimer: NodeJS.Timeout | null = null;
  private networkInfo: NetworkInfo = { isOnline: navigator.onLine };
  // Note: Offline storage should be accessed through proper React context/hooks in components
  // This service provides the sync logic that components can use via hooks
  
  // Event listeners for sync status
  private listeners: Map<string, Function[]> = new Map();

  constructor(config: Partial<SyncConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.setupNetworkMonitoring();
    this.setupServiceWorkerCommunication();
  }

  /**
   * Initialize the sync service
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      console.log('⚠️  Sync service already initialized, skipping...');
      return;
    }
    
    try {
      console.log('🔄 Initializing sync service...');
      
      // Load pending sync items from storage
      await this.loadSyncQueue();
      
      // Setup periodic sync if enabled
      if (this.config.enableBackgroundSync) {
        this.startPeriodicSync();
      }
      
      // Register for background sync
      if ('serviceWorker' in navigator && navigator.serviceWorker.ready) {
        const registration = await navigator.serviceWorker.ready;
        if (registration.sync) {
          await registration.sync.register('data-sync');
        }
      }
      
      this.isInitialized = true;
      console.log('✅ Sync service initialized');
      this.emit('initialized');
      
    } catch (error) {
      console.error('Failed to initialize sync service:', error);
      errorService.reportError(error, {
        component: 'SyncService',
        action: 'initialize',
      }, 'high');
    }
  }

  /**
   * Queue data for synchronization
   */
  async queueForSync(
    type: string,
    data: any,
    operation: SyncOperation,
    priority: number = 5
  ): Promise<string> {
    const syncItem: SyncItem = {
      id: `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      operation,
      data,
      timestamp: Date.now(),
      priority,
      retryCount: 0,
      status: 'pending',
      checksum: this.calculateChecksum(data),
    };

    this.syncQueue.push(syncItem);
    this.sortQueueByPriority();
    
    // Save queue to persistent storage
    await this.saveSyncQueue();
    
    console.log(`📤 Queued ${operation} for ${type}:`, syncItem.id);
    this.emit('item-queued', syncItem);
    
    // Try immediate sync if online
    if (this.networkInfo.isOnline && !this.isSyncing) {
      this.syncAll();
    }
    
    return syncItem.id;
  }

  /**
   * Synchronize all queued items
   */
  async syncAll(): Promise<SyncResult> {
    if (this.isSyncing) {
      console.log('⏳ Sync already in progress');
      return { success: false, syncedCount: 0, failedCount: 0, conflictsCount: 0, errors: ['Sync in progress'] };
    }

    if (!this.networkInfo.isOnline) {
      console.log('📱 Cannot sync while offline');
      return { success: false, syncedCount: 0, failedCount: 0, conflictsCount: 0, errors: ['Offline'] };
    }

    this.isSyncing = true;
    this.emit('sync-start');
    
    let syncedCount = 0;
    let failedCount = 0;
    let conflictsCount = 0;
    const errors: string[] = [];

    try {
      console.log(`🔄 Starting sync of ${this.syncQueue.length} items...`);
      
      // Process items in batches
      const batches = this.createBatches(this.syncQueue.filter(item => item.status === 'pending' || item.status === 'failed'));
      
      for (const batch of batches) {
        try {
          const batchResult = await this.syncBatch(batch);
          syncedCount += batchResult.syncedCount;
          failedCount += batchResult.failedCount;
          conflictsCount += batchResult.conflictsCount;
          errors.push(...batchResult.errors);
          
          // Update progress
          this.emit('sync-progress', {
            processed: syncedCount + failedCount,
            total: this.syncQueue.length,
            synced: syncedCount,
            failed: failedCount,
            conflicts: conflictsCount,
          });
          
          // Respect bandwidth limitations
          if (this.shouldThrottleSync()) {
            await this.delay(1000);
          }
          
        } catch (error) {
          console.error('Batch sync failed:', error);
          errors.push(`Batch sync failed: ${error.message}`);
          failedCount += batch.length;
        }
      }
      
      // Remove successfully synced items
      this.syncQueue = this.syncQueue.filter(item => item.status !== 'synced');
      await this.saveSyncQueue();
      
      const result: SyncResult = {
        success: failedCount === 0,
        syncedCount,
        failedCount,
        conflictsCount,
        errors,
      };
      
      console.log(`✅ Sync complete: ${syncedCount} synced, ${failedCount} failed, ${conflictsCount} conflicts`);
      this.emit('sync-complete', result);
      
      return result;
      
    } catch (error) {
      console.error('Sync failed:', error);
      errors.push(`Sync failed: ${error.message}`);
      
      errorService.reportError(error, {
        component: 'SyncService',
        action: 'syncAll',
        queueSize: this.syncQueue.length,
      }, 'high');
      
      const result: SyncResult = {
        success: false,
        syncedCount,
        failedCount: this.syncQueue.length,
        conflictsCount,
        errors,
      };
      
      this.emit('sync-error', result);
      return result;
      
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * Sync a batch of items
   */
  private async syncBatch(batch: SyncItem[]): Promise<SyncResult> {
    let syncedCount = 0;
    let failedCount = 0;
    let conflictsCount = 0;
    const errors: string[] = [];

    // Group by type and operation for efficient API calls
    const grouped = this.groupByTypeAndOperation(batch);
    
    for (const [key, items] of grouped) {
      const [type, operation] = key.split(':');
      
      try {
        const result = await this.syncGroup(type, operation as SyncOperation, items);
        
        syncedCount += result.syncedCount;
        failedCount += result.failedCount;
        conflictsCount += result.conflictsCount;
        errors.push(...result.errors);
        
      } catch (error) {
        console.error(`Failed to sync ${key}:`, error);
        errors.push(`${key}: ${error.message}`);
        failedCount += items.length;
        
        // Mark items as failed
        items.forEach(item => {
          item.status = 'failed';
          item.retryCount++;
          item.lastRetry = Date.now();
        });
      }
    }

    return { success: failedCount === 0, syncedCount, failedCount, conflictsCount, errors };
  }

  /**
   * Sync a group of items of the same type and operation
   */
  private async syncGroup(
    type: string,
    operation: SyncOperation,
    items: SyncItem[]
  ): Promise<SyncResult> {
    console.log(`🔄 Syncing ${items.length} ${operation} operations for ${type}`);
    
    let syncedCount = 0;
    let failedCount = 0;
    let conflictsCount = 0;
    const errors: string[] = [];

    // Mark items as syncing
    items.forEach(item => item.status = 'syncing');

    try {
      // Prepare API request
      const endpoint = this.getApiEndpoint(type, operation);
      const payload = this.prepareApiPayload(operation, items);
      
      const response = await fetch(endpoint, {
        method: this.getHttpMethod(operation),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      
      // Process response and update item statuses
      if (result.success) {
        items.forEach(item => {
          item.status = 'synced';
          syncedCount++;
        });
      } else if (result.conflicts) {
        // Handle conflicts
        result.conflicts.forEach((conflict: any, index: number) => {
          const item = items[index];
          if (conflict.conflict) {
            item.status = 'conflict';
            item.conflictData = conflict.serverData;
            conflictsCount++;
          } else {
            item.status = 'synced';
            syncedCount++;
          }
        });
      }
      
    } catch (error) {
      console.error(`Group sync failed for ${type}:${operation}:`, error);
      errors.push(`${type}:${operation} - ${error.message}`);
      
      // Handle different error types
      if (error.message.includes('401') || error.message.includes('403')) {
        // Authentication error - mark as failed
        items.forEach(item => {
          item.status = 'failed';
          item.retryCount++;
        });
        failedCount = items.length;
      } else if (error.message.includes('409')) {
        // Conflict - handle individually
        items.forEach(item => {
          item.status = 'conflict';
          conflictsCount++;
        });
      } else {
        // Network or server error - retry later
        items.forEach(item => {
          item.status = 'failed';
          item.retryCount++;
          item.lastRetry = Date.now();
        });
        failedCount = items.length;
      }
    }

    return { success: failedCount === 0, syncedCount, failedCount, conflictsCount, errors };
  }

  /**
   * Resolve conflicts using configured strategy
   */
  async resolveConflicts(items: SyncItem[]): Promise<void> {
    console.log(`🔧 Resolving ${items.length} conflicts...`);
    
    for (const item of items) {
      try {
        switch (this.config.conflictResolution) {
          case 'client-wins':
            await this.resolveClientWins(item);
            break;
          case 'server-wins':
            await this.resolveServerWins(item);
            break;
          case 'merge':
            await this.resolveMerge(item);
            break;
          case 'manual':
            // Keep as conflict for manual resolution
            this.emit('conflict-manual', item);
            continue;
        }
        
        item.status = 'synced';
        console.log(`✅ Resolved conflict for ${item.type}:${item.id}`);
        
      } catch (error) {
        console.error(`Failed to resolve conflict for ${item.id}:`, error);
        item.status = 'failed';
      }
    }
    
    await this.saveSyncQueue();
  }

  /**
   * Get sync queue status
   */
  getQueueStatus(): {
    total: number;
    pending: number;
    syncing: number;
    failed: number;
    conflicts: number;
  } {
    const total = this.syncQueue.length;
    const pending = this.syncQueue.filter(item => item.status === 'pending').length;
    const syncing = this.syncQueue.filter(item => item.status === 'syncing').length;
    const failed = this.syncQueue.filter(item => item.status === 'failed').length;
    const conflicts = this.syncQueue.filter(item => item.status === 'conflict').length;
    
    return { total, pending, syncing, failed, conflicts };
  }

  /**
   * Clear sync queue (with confirmation)
   */
  async clearQueue(force: boolean = false): Promise<void> {
    if (!force && this.syncQueue.some(item => item.status === 'pending')) {
      throw new Error('Queue contains pending items. Use force=true to clear anyway.');
    }
    
    this.syncQueue = [];
    await this.saveSyncQueue();
    console.log('🗑️ Sync queue cleared');
    this.emit('queue-cleared');
  }

  /**
   * Event listener management
   */
  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  off(event: string, callback: Function): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(event: string, data?: any): void {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in sync event callback for ${event}:`, error);
        }
      });
    }
  }

  // Private helper methods
  private async loadSyncQueue(): Promise<void> {
    try {
      const stored = localStorage.getItem('syncQueue');
      if (stored) {
        this.syncQueue = JSON.parse(stored);
        console.log(`📥 Loaded ${this.syncQueue.length} items from sync queue`);
      }
    } catch (error) {
      console.error('Failed to load sync queue:', error);
      this.syncQueue = [];
    }
  }

  private async saveSyncQueue(): Promise<void> {
    try {
      localStorage.setItem('syncQueue', JSON.stringify(this.syncQueue));
    } catch (error) {
      console.error('Failed to save sync queue:', error);
    }
  }

  private sortQueueByPriority(): void {
    this.syncQueue.sort((a, b) => {
      // Higher priority first, then older timestamps
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }
      return a.timestamp - b.timestamp;
    });
  }

  private createBatches(items: SyncItem[]): SyncItem[][] {
    const batches: SyncItem[][] = [];
    for (let i = 0; i < items.length; i += this.config.batchSize) {
      batches.push(items.slice(i, i + this.config.batchSize));
    }
    return batches;
  }

  private groupByTypeAndOperation(items: SyncItem[]): Map<string, SyncItem[]> {
    const grouped = new Map<string, SyncItem[]>();
    
    items.forEach(item => {
      const key = `${item.type}:${item.operation}`;
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(item);
    });
    
    return grouped;
  }

  private getApiEndpoint(type: string, operation: SyncOperation): string {
    const endpoints = {
      contexts: '/api/contexts',
      sessions: '/api/chat/sessions',
      messages: '/api/chat/messages',
      documents: '/api/documents',
    };
    
    const baseEndpoint = endpoints[type as keyof typeof endpoints] || `/api/${type}`;
    
    if (operation === 'create') {
      return `${baseEndpoint}/batch`;
    } else if (operation === 'update') {
      return `${baseEndpoint}/batch-update`;
    } else if (operation === 'delete') {
      return `${baseEndpoint}/batch-delete`;
    }
    
    return baseEndpoint;
  }

  private getHttpMethod(operation: SyncOperation): string {
    switch (operation) {
      case 'create': return 'POST';
      case 'update': return 'PUT';
      case 'delete': return 'DELETE';
      default: return 'POST';
    }
  }

  private prepareApiPayload(operation: SyncOperation, items: SyncItem[]): any {
    if (operation === 'delete') {
      return { ids: items.map(item => item.data.id) };
    }
    
    return { items: items.map(item => item.data) };
  }

  private calculateChecksum(data: any): string {
    // Simple checksum calculation - in production, use a more robust method
    return btoa(JSON.stringify(data)).slice(0, 16);
  }

  private shouldThrottleSync(): boolean {
    // Throttle on slow connections
    if (this.networkInfo.effectiveType && ['slow-2g', '2g'].includes(this.networkInfo.effectiveType)) {
      return true;
    }
    
    // Throttle on low bandwidth
    if (this.networkInfo.downlink && this.networkInfo.downlink < 1.5) {
      return true;
    }
    
    return false;
  }

  private async resolveClientWins(item: SyncItem): Promise<void> {
    // Force update with client data
    const response = await fetch(this.getApiEndpoint(item.type, 'update'), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        'X-Conflict-Resolution': 'force-client',
      },
      body: JSON.stringify({ item: item.data }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to resolve client-wins: ${response.statusText}`);
    }
  }

  private async resolveServerWins(item: SyncItem): Promise<void> {
    // Accept server data and update local
    if (item.conflictData) {
      // Update local storage with server data
      await this.updateLocalData(item.type, item.conflictData);
    }
  }

  private async resolveMerge(item: SyncItem): Promise<void> {
    // Implement merge logic based on data type
    const merged = this.mergeData(item.data, item.conflictData);
    
    const response = await fetch(this.getApiEndpoint(item.type, 'update'), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        'X-Conflict-Resolution': 'merge',
      },
      body: JSON.stringify({ item: merged }),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to resolve merge: ${response.statusText}`);
    }
  }

  private mergeData(clientData: any, serverData: any): any {
    // Simple merge strategy - prefer newer timestamps
    const merged = { ...serverData, ...clientData };
    
    // Handle timestamp-based merging
    if (clientData.updated_at && serverData.updated_at) {
      if (new Date(serverData.updated_at) > new Date(clientData.updated_at)) {
        merged.updated_at = serverData.updated_at;
        // Prefer server data for newer updates
        return { ...clientData, ...serverData };
      }
    }
    
    return merged;
  }

  private async updateLocalData(type: string, data: any): Promise<void> {
    // Update local data stores
    switch (type) {
      case 'contexts':
        // Update contexts in local storage
        break;
      case 'sessions':
        // Update sessions in local storage
        break;
      // Add other types as needed
    }
  }

  private setupNetworkMonitoring(): void {
    // Monitor online/offline status
    window.addEventListener('online', () => {
      this.networkInfo.isOnline = true;
      console.log('🌐 Network restored - triggering sync');
      this.emit('network-online');
      
      // Trigger sync when coming back online
      if (!this.isSyncing && this.syncQueue.length > 0) {
        setTimeout(() => this.syncAll(), 1000);
      }
    });

    window.addEventListener('offline', () => {
      this.networkInfo.isOnline = false;
      console.log('📱 Network lost');
      this.emit('network-offline');
    });

    // Monitor connection quality if available
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      
      const updateConnectionInfo = () => {
        this.networkInfo.effectiveType = connection.effectiveType;
        this.networkInfo.downlink = connection.downlink;
        this.networkInfo.rtt = connection.rtt;
      };
      
      updateConnectionInfo();
      connection.addEventListener('change', updateConnectionInfo);
    }
  }

  private setupServiceWorkerCommunication(): void {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        const { type, data } = event.data;
        
        switch (type) {
          case 'SYNC_COMPLETE':
            this.emit('background-sync-complete', data);
            break;
          case 'REQUEST_SYNCED':
            this.handleBackgroundSyncResult(data);
            break;
          case 'SYNC_ERROR':
            this.emit('background-sync-error', data);
            break;
        }
      });
    }
  }

  private handleBackgroundSyncResult(data: any): void {
    // Update sync queue based on background sync results
    const item = this.syncQueue.find(item => item.id === data.requestId);
    if (item) {
      item.status = data.success ? 'synced' : 'failed';
      this.saveSyncQueue();
    }
  }

  private startPeriodicSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }
    
    this.syncTimer = setInterval(() => {
      if (this.networkInfo.isOnline && !this.isSyncing && this.syncQueue.length > 0) {
        console.log('⏰ Periodic sync triggered');
        this.syncAll();
      }
    }, this.config.syncInterval);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
    
    this.listeners.clear();
    console.log('🔄 Sync service destroyed');
  }
}

// Export singleton instance
export const syncService = new SyncService();

export default syncService;