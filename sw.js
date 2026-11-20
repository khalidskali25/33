/* عامل خدمة مواكبة — تحديث متحكَّم فيه:
   - يعمل التطبيق دائما بالنسخة المحفوظة على الجهاز (حتى دون اتصال).
   - عند نشر نسخة جديدة، تُنزَّل في الخلفية وتبقى «في الانتظار» ولا تُطبَّق تلقائيا.
   - يظهر للمستعمل إشعار بالتحديث وما فيه، ولا يُطبَّق إلا بعد ضغطه «تحديث الآن». */
const VERSION='1.16.1';
const CACHE='mouakaba-'+VERSION;
const ASSETS=['./','./index.html','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png','./icons/maskable-512.png','./icons/apple-180.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS.map(u=>new Request(u,{cache:'reload'})))));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE&&k.startsWith('mouakaba-')).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('message',e=>{if(e.data==='skip')self.skipWaiting();});
self.addEventListener('fetch',e=>{const r=e.request,u=new URL(r.url);if(r.method!=='GET'||u.origin!==location.origin)return;
 if(u.pathname.endsWith('/version.json'))return; /* ملاحظات الإصدار: من الشبكة دائما */
 e.respondWith((async()=>{const c=await caches.open(CACHE);const m=await c.match(r,{ignoreSearch:true})||(r.mode==='navigate'?await c.match('./index.html'):null);if(m)return m;
  try{const res=await fetch(r);if(res&&res.ok)c.put(r,res.clone());return res;}catch(err){return Response.error();}})());});
