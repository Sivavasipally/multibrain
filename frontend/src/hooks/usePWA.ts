import { useState, useEffect } from 'react';

interface PWAInstallPrompt extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface PWAState {
  isOnline: boolean;
  isInstallable: boolean;
  isInstalled: boolean;
  installPrompt: PWAInstallPrompt | null;
}

export const usePWA = () => {
  const [pwaState, setPWAState] = useState<PWAState>({
    isOnline: navigator.onLine,
    isInstallable: false,
    isInstalled: false,
    installPrompt: null,
  });

  useEffect(() => {
    // Check if app is already installed
    const isInstalled = window.matchMedia('(display-mode: standalone)').matches ||
                       (window.navigator as any).standalone ||
                       document.referrer.includes('android-app://');
    
    setPWAState(prev => ({ ...prev, isInstalled }));

    // Handle online/offline status
    const handleOnline = () => setPWAState(prev => ({ ...prev, isOnline: true }));
    const handleOffline = () => setPWAState(prev => ({ ...prev, isOnline: false }));

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Handle install prompt
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      const installPrompt = e as PWAInstallPrompt;
      setPWAState(prev => ({
        ...prev,
        isInstallable: true,
        installPrompt,
      }));
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Handle app installed
    const handleAppInstalled = () => {
      setPWAState(prev => ({
        ...prev,
        isInstalled: true,
        isInstallable: false,
        installPrompt: null,
      }));
    };

    window.addEventListener('appinstalled', handleAppInstalled);

    // Service Worker message handling
    const handleSWMessage = (event: MessageEvent) => {
      if (event.data && event.data.type) {
        switch (event.data.type) {
          case 'SW_UPDATE_AVAILABLE':
            // Handle service worker update
            console.log('Service worker update available');
            break;
          case 'MESSAGE_SYNCED':
            // Handle offline message sync
            console.log('Offline message synced:', event.data.messageId);
            break;
          default:
            break;
        }
      }
    };

    navigator.serviceWorker?.addEventListener('message', handleSWMessage);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
      navigator.serviceWorker?.removeEventListener('message', handleSWMessage);
    };
  }, []);

  const installApp = async () => {
    if (!pwaState.installPrompt) return false;

    try {
      await pwaState.installPrompt.prompt();
      const choiceResult = await pwaState.installPrompt.userChoice;
      
      if (choiceResult.outcome === 'accepted') {
        setPWAState(prev => ({
          ...prev,
          isInstallable: false,
          installPrompt: null,
        }));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error installing PWA:', error);
      return false;
    }
  };

  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission === 'denied') {
      return false;
    }

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  };

  const showNotification = (title: string, options?: NotificationOptions) => {
    if (Notification.permission === 'granted') {
      return new Notification(title, {
        icon: '/pwa-192x192.png',
        badge: '/badge-72x72.png',
        ...options,
      });
    }
    return null;
  };

  const registerBackgroundSync = async (tag: string) => {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await (registration as any).sync.register(tag);
        return true;
      } catch (error) {
        console.error('Background sync registration failed:', error);
        return false;
      }
    }
    return false;
  };

  const updateServiceWorker = async () => {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.update();
        return true;
      } catch (error) {
        console.error('Service worker update failed:', error);
        return false;
      }
    }
    return false;
  };

  const getNetworkStatus = () => {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      return {
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData,
      };
    }
    return null;
  };

  const shareContent = async (shareData: ShareData) => {
    if (navigator.share) {
      try {
        await navigator.share(shareData);
        return true;
      } catch (error) {
        console.error('Error sharing:', error);
        return false;
      }
    }
    return false;
  };

  const addToHomeScreen = () => {
    // For iOS Safari
    if ((navigator as any).standalone === false) {
      return {
        isIOS: true,
        message: 'To install this app, tap the share button and then "Add to Home Screen"',
      };
    }
    return null;
  };

  return {
    ...pwaState,
    installApp,
    requestNotificationPermission,
    showNotification,
    registerBackgroundSync,
    updateServiceWorker,
    getNetworkStatus,
    shareContent,
    addToHomeScreen,
  };
};
