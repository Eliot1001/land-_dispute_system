// Service Worker for Land Dispute Management System
// Enables offline support, caching, and PWA functionality

const CACHE_NAME = 'land-dispute-v1';
const urlsToCache = [
  '/',
  '/static/css/dashboard.css',
  '/static/css/case.css',
  '/static/css/submitcase.css',
  '/static/images/logo-192x192.png',
  '/static/images/logo-512x512.png',
  '/static/manifest.json'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('✓ Service Worker: Opened cache');
        return cache.addAll(urlsToCache).catch((err) => {
          console.warn('⚠ Service Worker: Some resources failed to cache', err);
        });
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('✓ Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached response if available
        if (response) {
          console.log('✓ Service Worker: Serving from cache:', event.request.url);
          return response;
        }

        // Try to fetch from network
        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses or non-GET requests
            if (!response || response.status !== 200 || response.type === 'error') {
              return response;
            }

            // Cache successful responses
            const responseToCache = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache);
            });

            return response;
          })
          .catch(() => {
            // Network request failed, try to return a cached response
            console.warn('✗ Service Worker: Network error, using cache fallback');
            return caches.match(event.request);
          });
      })
  );
});

// Listen for messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('✓ Service Worker registered successfully');
