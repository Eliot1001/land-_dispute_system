/**
 * PWA Setup Script for Land Dispute Management System
 * Handles service worker registration and PWA features
 */

// Register Service Worker
function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/service-worker.js', {
        scope: '/'
      })
      .then((registration) => {
        console.log('✓ Service Worker registered successfully:', registration);
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker is ready
              console.log('✓ Service Worker update available');
              showUpdateNotification(registration);
            }
          });
        });
      })
      .catch((error) => {
        console.warn('⚠ Service Worker registration failed:', error);
      });
    });
  } else {
    console.log('ℹ Service Workers not supported in this browser');
  }
}

// Show notification when update is available
function showUpdateNotification(registration) {
  const updatePrompt = document.createElement('div');
  updatePrompt.id = 'pwa-update-prompt';
  updatePrompt.innerHTML = `
    <div style="
      position: fixed;
      bottom: 20px;
      left: 20px;
      right: 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 16px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 9999;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <strong>✨ Update Available</strong>
          <p style="margin-top: 4px; font-size: 14px; opacity: 0.9;">
            A new version of the app is ready to use.
          </p>
        </div>
        <div style="display: flex; gap: 8px;">
          <button onclick="updateApp()" style="
            background: white;
            color: #667eea;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            font-size: 14px;
          ">Update Now</button>
          <button onclick="this.parentElement.parentElement.parentElement.remove()" style="
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
          ">Later</button>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(updatePrompt);
  
  window.updateApp = function() {
    if (registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  };
}

// Detect when app is installed
window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent the mini-infobar from appearing on mobile
  e.preventDefault();
  // Store the event for later use
  window.installPrompt = e;
  console.log('✓ Install prompt ready');
});

// Detect successful app installation
window.addEventListener('appinstalled', () => {
  console.log('✓ App installed successfully');
  // Clear the install prompt
  window.installPrompt = null;
});

// Check if app is running in standalone mode (installed)
function isAppInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true ||
         document.referrer === 'android-app://';
}

// Show install prompt if available
function showInstallPrompt() {
  if (window.installPrompt) {
    window.installPrompt.prompt();
    window.installPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('✓ User accepted the install prompt');
      } else {
        console.log('✗ User dismissed the install prompt');
      }
      window.installPrompt = null;
    });
  }
}

// Initialize PWA features
function initPWA() {
  if (isAppInstalled()) {
    console.log('✓ App is running in installed mode');
    document.documentElement.classList.add('pwa-installed');
  } else {
    console.log('ℹ App is running in browser');
  }
  
  registerServiceWorker();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPWA);
} else {
  initPWA();
}
