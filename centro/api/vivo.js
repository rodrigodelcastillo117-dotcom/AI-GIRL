// Números en vivo: YouTube directo de su API y TikTok/Instagram de las estadísticas de Publer.
// Se guardan 55 segundos en memoria para no gastar cuota si varios abren el centro a la vez.
import {autorizado, leer, negar, variable} from './_comun.js';

const PUBLER = 'https://app.publer.com/api/v1';
const YT = 'https://www.googleapis.com/youtube/v3';
// Cloudflare de Publer rechaza clientes sin nombre (error 1010)
const AGENTE = 'victoria-centro/1.0 (+https://vercel.com)';
const RED_CORTA = {instagram: 'ig', tiktok: 'tt', youtube: 'yt', facebook: 'fb'};
let memoria = {hasta: 0, datos: null};

const primeraLinea = (texto) => ((texto || '').trim().split('\n')[0] || '').split(/\s+/).join(' ').toLowerCase();
const dia = (fecha) => fecha.toISOString().slice(0, 10);

async function pedir(url, opciones, nombre) {
  const r = await fetch(url, opciones);
  if (!r.ok) throw new Error(`${nombre} respondió ${r.status}`);
  return r.json();
}

async function youtube(estado, videos) {
  const faltan = ['YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN'].filter((n) => !variable(n));
  if (faltan.length) throw new Error(`faltan en Vercel: ${faltan.join(', ')}`);
  const {access_token: token} = await pedir('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: new URLSearchParams({
      client_id: variable('YOUTUBE_CLIENT_ID'), client_secret: variable('YOUTUBE_CLIENT_SECRET'),
      refresh_token: variable('YOUTUBE_REFRESH_TOKEN'), grant_type: 'refresh_token',
    }),
  }, 'Permiso de YouTube');
  const cabeceras = {headers: {Authorization: `Bearer ${token}`}};
  const canal = await pedir(`${YT}/channels?part=statistics&id=${estado.canal_youtube}`, cabeceras, 'YouTube');
  const s = canal.items?.[0]?.statistics || {};
  const porVideo = {};
  const ids = videos.filter((v) => v.youtube_id);
  for (let i = 0; i < ids.length; i += 50) {
    const lote = ids.slice(i, i + 50);
    const d = await pedir(`${YT}/videos?part=statistics,status&id=${lote.map((v) => v.youtube_id).join(',')}`, cabeceras, 'YouTube');
    for (const item of d.items || []) {
      const video = lote.find((v) => v.youtube_id === item.id);
      porVideo[video.id] = {
        v: Number(item.statistics.viewCount) || 0, l: Number(item.statistics.likeCount) || 0,
        c: Number(item.statistics.commentCount) || 0, estado: item.status.privacyStatus,
      };
    }
  }
  if (ids.length) {
    // Retención: % promedio visto de cada Short (YouTube Analytics; tarda 1 a 3 días en aparecer).
    try {
      const hoy = new Date();
      const r = await pedir('https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==MINE'
        + `&startDate=${dia(new Date(hoy.getTime() - 60 * 864e5))}&endDate=${dia(hoy)}`
        + `&metrics=averageViewPercentage&dimensions=video&filters=video==${ids.slice(0, 50).map((v) => v.youtube_id).join(',')}`, cabeceras, 'YouTube Analytics');
      for (const [idYoutube, retencion] of r.rows || []) {
        const video = ids.find((v) => v.youtube_id === idYoutube);
        if (video && porVideo[video.id]) porVideo[video.id].ret = Math.round(retencion * 10) / 10;
      }
    } catch { /* sin retención no se pierde lo demás */ }
  }
  return {suscriptores: Number(s.subscriberCount) || 0, vistas: Number(s.viewCount) || 0, porVideo};
}

async function publer(estado, videos) {
  if (!variable('PUBLER_API_KEY')) throw new Error('falta en Vercel: PUBLER_API_KEY');
  const cabeceras = {Authorization: `Bearer-API ${variable('PUBLER_API_KEY')}`, Accept: 'application/json', 'User-Agent': AGENTE};
  let ws = variable('PUBLER_WORKSPACE_ID');
  if (!ws) {
    const w = await pedir(`${PUBLER}/workspaces`, {headers: cabeceras}, 'Publer');
    ws = (Array.isArray(w) ? w : w.workspaces || w.data || [])[0]?.id;
  }
  cabeceras['Publer-Workspace-Id'] = ws;
  const cuentas = estado.cuentas_publer || {};
  const porLinea = Object.fromEntries(videos.filter((v) => v.linea).map((v) => [v.linea, v.id]));
  const porMinuto = Object.fromEntries(videos.filter((v) => v.publica_utc).map((v) => [v.publica_utc.slice(0, 16), v.id]));
  const hoy = new Date();
  const desde = new Date(hoy.getTime() - 90 * 864e5);
  const porVideo = {};
  for (let pagina = 0; pagina < 20; pagina++) {
    const r = await pedir(`${PUBLER}/analytics/post_insights?from=${dia(desde)}&to=${dia(hoy)}&page=${pagina}`, {headers: cabeceras}, 'Publer');
    const lote = r.posts || [];
    for (const p of lote) {
      const red = RED_CORTA[cuentas[p.account_id]];
      if (!red) continue;  // solo las cuentas de Victoria
      const minuto = p.scheduled_at ? new Date(p.scheduled_at).toISOString().slice(0, 16) : '';
      const video = porLinea[primeraLinea(p.text)] || porMinuto[minuto];
      if (!video) continue;
      const a = p.analytics || {};
      const destino = (porVideo[video] ||= {});
      const previo = destino[red] || {v: 0, l: 0, c: 0, s: 0, g: 0, alcance: 0};
      destino[red] = {
        v: previo.v + (Number(a.video_views) || 0), l: previo.l + (Number(a.likes) || 0),
        c: previo.c + (Number(a.comments) || 0), s: previo.s + (Number(a.shares) || 0),
        g: previo.g + (Number(a.saves) || 0), alcance: previo.alcance + (Number(a.reach) || 0),
        enlace: p.post_link || p.url || previo.enlace,
      };
    }
    if (lote.length < 10) break;
  }
  return {porVideo};
}

export default async function handler(req, res) {
  if (!autorizado(req)) return negar(res);
  res.setHeader('Cache-Control', 'private, no-store');
  if (memoria.datos && Date.now() < memoria.hasta) return res.status(200).json(memoria.datos);

  const estado = leer('estado.json')[0];
  const videos = leer('videos.json');
  const [yt, pb] = await Promise.allSettled([youtube(estado, videos), publer(estado, videos)]);
  const porVideo = {};
  for (const [fuente, resultado] of [['yt', yt], ['pb', pb]]) {
    if (resultado.status !== 'fulfilled') continue;
    for (const [id, redes] of Object.entries(resultado.value.porVideo)) {
      porVideo[id] = {...porVideo[id], ...(fuente === 'yt' ? {yt: redes} : redes)};
    }
  }
  const datos = {
    actualizado: new Date().toISOString(),
    canal: yt.status === 'fulfilled' ? {suscriptores: yt.value.suscriptores, vistas: yt.value.vistas} : null,
    porVideo,
    errores: [
      ...(yt.status === 'rejected' ? [`YouTube: ${yt.reason.message}`] : []),
      ...(pb.status === 'rejected' ? [`Publer: ${pb.reason.message}`] : []),
    ],
  };
  memoria = {hasta: Date.now() + 55_000, datos};
  res.status(200).json(datos);
}
