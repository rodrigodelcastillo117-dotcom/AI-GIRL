import crypto from 'node:crypto';
import {firma, galleta, variable} from './_comun.js';

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
  if (!esperada || !crypto.timingSafeEqual(resumen(clave), resumen(esperada))) {
    await new Promise((listo) => setTimeout(listo, 900));  // frena a quien adivina
    return res.status(401).json({error: esperada ? 'clave incorrecta' : 'falta CLAVE_CENTRO en Vercel'});
  }
  res.setHeader('Set-Cookie', galleta(firma(), 60 * 60 * 24 * 30));
  res.status(200).json({ok: true});
}
