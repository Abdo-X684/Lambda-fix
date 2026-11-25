// Offline shell for the crash viewer. The dump file itself never leaves the
// device and is never cached.
const CACHE = 'lambda-fix-crashview-v1';
const SHELL = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './mdmp.js',
  './analyze.js',
  './manifest.webmanifest',
  './icon.svg',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then((hit) => hit || fetch(event.request).catch(() => caches.match('./index.html'))),
  );
});
