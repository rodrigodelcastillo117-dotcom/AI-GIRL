// Acceso con contraseña (CLAVE_CENTRO) y lectura de la última foto de datos (datos/, no es público).
import crypto from 'node:crypto';
import fs from 'node:fs';

const GALLETA = 'centro';

export const variable = (nombre) => (process.env[nombre] || '').trim().replace(/^["']|["']$/g, '');

export function firma() {
  const clave = variable('CLAVE_CENTRO');
  return clave ? crypto.createHmac('sha256', clave).update('centro-victoria-v1').digest('hex') : null;
}

// Invitados: CLAVES_INVITADOS en Vercel con el formato "Carlo:su clave;Otra persona:otra clave".
// Rodrigo sigue entrando con CLAVE_CENTRO. Las claves viven solo en Vercel.
export function invitados() {
  return variable('CLAVES_INVITADOS').split(';').map((x) => x.trim()).filter(Boolean)
    .map((x) => ({nombre: x.slice(0, x.indexOf(':')).trim(), clave: x.slice(x.indexOf(':') + 1).trim()}))
    .filter((u) => u.nombre && u.clave && !u.nombre.includes('.'));
}

function firmaNombre(nombre) {
  const clave = variable('CLAVE_CENTRO');
  return clave ? crypto.createHmac('sha256', clave).update(`centro-victoria-v1:${nombre}`).digest('hex') : null;
}

export function sesion(nombre) {
  return `${Buffer.from(nombre).toString('base64url')}.${firmaNombre(nombre)}`;
}

const igual = (a, b) => Boolean(a) && Boolean(b) && a.length === b.length && crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));

// Quién entró (el nombre va firmado: no se puede cambiar). Las sesiones de antes cuentan como Rodrigo.
export function usuario(req) {
  const valor = (req.headers.cookie || '').split(';').map((x) => x.trim())
    .find((x) => x.startsWith(`${GALLETA}=`))?.slice(GALLETA.length + 1) || '';
  if (igual(valor, firma())) return 'Rodrigo';
  const [n64, f] = valor.split('.');
  if (!n64 || !f) return null;
  const nombre = Buffer.from(n64, 'base64url').toString('utf8');
  if (!igual(f, firmaNombre(nombre))) return null;
  return nombre === 'Rodrigo' || invitados().some((u) => u.nombre === nombre) ? nombre : null;  // quitar a un invitado lo saca
}

export function autorizado(req) {
  return usuario(req) != null;
}

export function galleta(valor, segundos) {
  return `${GALLETA}=${valor}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${segundos}`;
}

export function negar(res) {
  res.setHeader('Cache-Control', 'no-store');
  res.status(401).json({error: 'sin acceso'});
}

export function leer(nombre) {
  // Relativo a este archivo: en Vercel el repo vive en /var/task/centro, no en el directorio de trabajo.
  return JSON.parse(fs.readFileSync(new URL(`../datos/${nombre}`, import.meta.url), 'utf8'));
}
