import crypto from 'node:crypto';
import {galleta, invitados, sesion, variable} from './_comun.js';

const resumen = (texto) => crypto.createHash('sha256').update(texto).digest();

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'DELETE') {
    res.setHeader('Set-Cookie', galleta('', 0));
    return res.status(204).end();
  }
  if (req.method !== 'POST') return res.status(405).end();
  const esperada = variable('CLAVE_CENTRO');
  const clave = String(req.body?.clave || '');
  const personas = esperada ? [{nombre: 'Rodrigo', clave: esperada}, ...invitados()] : [];
  const quien = personas.find((p) => crypto.timingSafeEqual(resumen(clave), resumen(p.clave)));
  if (!quien) {
    await new Promise((listo) => setTimeout(listo, 900));  // frena a quien adivina
    return res.status(401).json({error: esperada ? 'clave incorrecta' : 'falta CLAVE_CENTRO en Vercel'});
  }
  res.setHeader('Set-Cookie', galleta(sesion(quien.nombre), 60 * 60 * 24 * 30));
  res.status(200).json({ok: true, nombre: quien.nombre});
}
