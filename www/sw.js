// Offline-Unterstützung für die Webseite (iPhone „Zum Home-Bildschirm“ und Android-Browser).
// Neueste Version aus dem Netz, bei fehlender Verbindung die zuletzt gespeicherte.
const CACHE = 'tellerflamme-v1';
const CORE = ['./', 'index.html', 'manifest.webmanifest', 'icon.svg', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || u.pathname.endsWith('version.json') || u.pathname.endsWith('update.zip')) return;
  e.respondWith(fetch(e.request).then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; }).catch(() => caches.match(e.request).then(m => m || caches.match('index.html'))));
});
