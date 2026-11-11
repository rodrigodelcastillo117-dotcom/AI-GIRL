// Aviso instantáneo de Meta (webhook) para "Comenta GUÍA" (Rodrigo, 10-nov-2026: "¿y si conectamos Meta al panel de Vercel?").
// Cuando alguien comenta "guía" en un post de @victoriatheceo, Meta avisa aquí al momento y Victoria le manda el enlace por
// mensaje privado (respuesta privada: una por comentario) y le contesta en público. La revisión de cada hora
// (scripts/comentarios_ig.py guias) sigue de respaldo y se salta los comentarios que ya tienen respuesta de Victoria.
//
// Variables en Vercel (proyecto victoria-centro; nunca en el repo ni en el chat):
//   META_TOKEN         token del usuario del sistema con instagram_manage_messages e instagram_manage_comments
//   META_APP_SECRET    clave secreta de la app "Victoria Comentarios" (para comprobar que el aviso viene de Meta)
//   META_VERIFY_TOKEN  palabra cualquiera; la misma se pone en Meta → Webhooks al suscribir
// Sin esas variables la función no hace nada (responde 503) y no rompe el panel.
import crypto from 'node:crypto';
import {variable} from './_comun.js';

const GRAPH = 'https://graph.facebook.com/v22.0';
const IG = '17841478105608541'; // @victoriatheceo
const YO = 'victoriatheceo';
const SITIO = 'https://victoriatheceo.vercel.app';
const ENLACES = [['aguinaldo', '/aguinaldo'], ['fondo de emergencia', '/fondo-de-emergencia'], ['deuda', '/pagar-deudas'],
  ['50/30/20', '/regla-50-30-20'], ['presupuesto', '/regla-50-30-20']];

const normal = (t) => (t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

// Igual que scripts/comentarios_ig.py → pide_enlace (Rodrigo lo autorizó el 11-nov-2026): GUÍA en cualquier parte, o un
// comentario corto (4 palabras o menos) que pide el enlace. Las opiniones largas y los votos (MITAD, SÍ...) no reciben nada.
const PALABRAS_CORTAS = ['quiero', 'pasamelo', 'pasame', 'mandamelo', 'link', 'info', 'aguinaldo', 'calcula', 'calculadora',
  'lista', 'porfa', 'por favor', 'me interesa'];

export function pideGuia(texto) {
  const t = normal(texto);
  if (/guia/.test(t)) return true;
  const limpio = t.replace(/[^a-z0-9ñ ]/g, ' ').split(/\s+/).filter(Boolean);
  return limpio.length > 0 && limpio.length <= 4 && PALABRAS_CORTAS.some((p) => limpio.join(' ').includes(p));
}

export function enlacePara(caption) {
  const t = (caption || '').toLowerCase();
  const ruta = (ENLACES.find(([clave]) => t.includes(clave)) || [null, ''])[1];
  return `${SITIO}${ruta}?ref=ig-dm`;
}

export function firmaValida(cuerpo, cabecera, secreto) {
  if (!cabecera || !secreto) return false;
  const esperada = 'sha256=' + crypto.createHmac('sha256', secreto).update(cuerpo).digest('hex');
  const a = Buffer.from(cabecera), b = Buffer.from(esperada);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

async function leerCrudo(req) {
  if (typeof req.body === 'string') return req.body;
  if (Buffer.isBuffer(req.body)) return req.body.toString('utf8');
  const partes = [];
  for await (const p of req) partes.push(p);
  return Buffer.concat(partes).toString('utf8');
}

async function graph(metodo, ruta, token, cuerpo) {
  const r = await fetch(`${GRAPH}/${ruta}`, {
    method: metodo,
    headers: {'Authorization': `Bearer ${token}`, ...(cuerpo ? {'Content-Type': 'application/json'} : {})},
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`${r.status} ${JSON.stringify(datos).slice(0, 200)}`);
  return datos;
}

async function entregar(comentario, token) {
  const {id, text, from, media} = comentario;
  const usuario = from?.username || '';
  if (!id || usuario === YO || !pideGuia(text)) return 'ignorado';
  const caption = media?.id ? (await graph('GET', `${media.id}?fields=caption`, token).catch(() => ({}))).caption : '';
  const enlace = enlacePara(caption);
  try {
    await graph('POST', `${IG}/messages`, token, {recipient: {comment_id: id},
      message: {text: `¡Hola${usuario ? ' @' + usuario : ''}! Aquí está lo que te prometí 👇\n${enlace}\n\nSi te sirve, cuéntame en el post qué te pareció. — Victoria`}});
    await graph('POST', `${id}/replies`, token, {message: '¡Listo! Te lo mandé por mensaje 📩 Revisa tus solicitudes si no lo ves.'});
    return 'privado';
  } catch (e) {
    // Ya se mandó (la revisión de cada hora llegó antes) o Meta no dejó: la respuesta pública lleva el enlace.
    if (/already|ya se/i.test(e.message)) return 'ya entregado';
    await graph('POST', `${id}/replies`, token, {message: `¡Aquí lo tienes! 👉 ${enlace.replace('https://', '')}`}).catch(() => {});
    return 'publico';
  }
}

export default async function handler(req, res) {
  const token = variable('META_TOKEN'), secreto = variable('META_APP_SECRET'), verificar = variable('META_VERIFY_TOKEN');
  if (!token || !secreto || !verificar) return res.status(503).json({error: 'sin configurar'});
  if (req.method === 'GET') {
    const q = req.query || {};
    if (q['hub.mode'] === 'subscribe' && q['hub.verify_token'] === verificar) return res.status(200).send(q['hub.challenge']);
    return res.status(403).send('no');
  }
  if (req.method !== 'POST') return res.status(405).end();
  const crudo = await leerCrudo(req);
  if (!firmaValida(crudo, req.headers['x-hub-signature-256'], secreto)) return res.status(401).end();
  let aviso;
  try { aviso = JSON.parse(crudo); } catch { return res.status(400).end(); }
  const resultados = [];
  for (const entrada of aviso.entry || []) {
    for (const cambio of entrada.changes || []) {
      if (cambio.field === 'comments' && cambio.value) resultados.push(await entregar(cambio.value, token).catch((e) => `error ${e.message}`));
    }
  }
  console.log('meta webhook', JSON.stringify(resultados)); // queda en los registros de Vercel
  return res.status(200).json({ok: true});
}
