// Servidor local para revisar el panel con las funciones reales (11-nov-2026). Uso: CLAVE_CENTRO=prueba node servidor_local.mjs 4173
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import url from 'node:url';
const raiz = path.dirname(url.fileURLToPath(import.meta.url));
const tipos = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml'};
http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  res.status = (c) => { res.statusCode = c; return res; };
  res.json = (o) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(o)); };
  res.send = (o) => res.end(typeof o === 'string' ? o : JSON.stringify(o));
  if (u.pathname.startsWith('/api/')) {
    const nombre = u.pathname.slice(5).replace(/\/$/, '');
    const archivo = path.join(raiz, 'api', nombre + '.js');
    if (!fs.existsSync(archivo)) return res.status(404).end();
    let cuerpo = ''; for await (const p of req) cuerpo += p;
    try { req.body = cuerpo ? JSON.parse(cuerpo) : undefined; } catch { req.body = cuerpo; }
    req.query = Object.fromEntries(u.searchParams);
    const m = await import(archivo);
    try { await m.default(req, res); } catch (e) { console.error('API', nombre, e); res.statusCode = 500; res.end(String(e)); }
    return;
  }
  let f = path.join(raiz, 'public', u.pathname === '/' ? 'index.html' : u.pathname);
  if (!fs.existsSync(f) && fs.existsSync(f + '.html')) f += '.html';
  if (!fs.existsSync(f)) return res.status(404).end('404');
  res.setHeader('Content-Type', tipos[path.extname(f)] || 'application/octet-stream');
  fs.createReadStream(f).pipe(res);
}).listen(Number(process.argv[2] || 4173));
