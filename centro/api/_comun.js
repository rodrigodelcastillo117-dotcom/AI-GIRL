// Acceso con contraseña (CLAVE_CENTRO) y lectura de la última foto de datos (datos/, no es público).
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const GALLETA = 'centro';

export const variable = (nombre) => (process.env[nombre] || '').trim().replace(/^["']|["']$/g, '');

export function firma() {
  const clave = variable('CLAVE_CENTRO');
  return clave ? crypto.createHmac('sha256', clave).update('centro-victoria-v1').digest('hex') : null;
}

export function autorizado(req) {
  const esperada = firma();
  const valor = (req.headers.cookie || '').split(';').map((x) => x.trim())
    .find((x) => x.startsWith(`${GALLETA}=`))?.slice(GALLETA.length + 1) || '';
  return Boolean(esperada) && valor.length === esperada.length
    && crypto.timingSafeEqual(Buffer.from(valor), Buffer.from(esperada));
}

export function galleta(valor, segundos) {
  return `${GALLETA}=${valor}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${segundos}`;
}

export function negar(res) {
  res.setHeader('Cache-Control', 'no-store');
  res.status(401).json({error: 'sin acceso'});
}

export function leer(nombre) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'datos', nombre), 'utf8'));
}
