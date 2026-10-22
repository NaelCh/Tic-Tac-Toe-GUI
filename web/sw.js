/* No analytics, remote services or account data are cached. */
const CACHE_PREFIX = 'triliza-mobile-';
const CACHE = CACHE_PREFIX + '__CACHE_VERSION__';
const SHELL = ['./', './index.html', './style.css', './app.js', './engine.js',
  './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png',
  './icons/apple-touch-icon.png', './sounds/click.wav', './sounds/move_x.wav',
  './sounds/move_o.wav', './sounds/win.wav', './sounds/lose.wav', './sounds/draw.wav'];
self.addEventListener('install', event => {
  // A new release must not reuse a previous shell from the HTTP cache.
  const requests = SHELL.map(url => new Request(new URL(url, self.location.href), {cache: 'reload'}));
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(requests)));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys
    .filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE)
    .map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('message', event => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) return;
  if (request.mode === 'navigate') {
    // Keep HTML and scripts from the same release until the player accepts
    // the waiting worker. Fresh network HTML could require newer cached JS.
    event.respondWith(caches.open(CACHE).then(cache => cache.match('./index.html'))
      .then(cached => cached || fetch(request)));
  } else {
    event.respondWith(caches.open(CACHE).then(cache => cache.match(request))
      .then(cached => cached || fetch(request)));
  }
});
