/* Quay Đội — service worker: chạy offline, tự cập nhật ở lần mở sau */
const CACHE = 'quaydoi-1.0.1';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
function refresh(req, key) {
  return fetch(req).then(res => {
    if (res && res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(key || req, cp)); }
    return res;
  });
}
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET' || new URL(r.url).origin !== location.origin) return;
  if (r.mode === 'navigate') {
    e.respondWith(caches.match('./index.html').then(c => {
      const net = refresh(r, './index.html').catch(() => c);
      return c || net;
    }));
    return;
  }
  e.respondWith(caches.match(r).then(c => {
    const net = refresh(r).catch(() => c);
    return c || net;
  }));
});
