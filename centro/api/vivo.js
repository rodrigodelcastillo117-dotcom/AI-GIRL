// Números en vivo: YouTube directo de su API y TikTok/Instagram de las estadísticas de Publer.
// Se guardan 55 segundos en memoria para no gastar cuota si varios abren el centro a la vez.
import {autorizado, leer, negar, variable} from './_comun.js';

const PUBLER = 'https://app.publer.com/api/v1';
const YT = 'https://www.googleapis.com/youtube/v3';
// Cloudflare de Publer rechaza clientes sin nombre (error 1010)
const AGENTE = 'victoria-centro/1.0 (+https://vercel.com)';
const RED_CORTA = {instagram: 'ig', tiktok: 'tt', youtube: 'yt', facebook: 'fb'};
let memoria = {hasta: 0, datos: null};
// Publer contesta a veces en 0.3 s y a veces en más de 10 s, y sus estadísticas no cambian cada
// minuto: se guarda 10 min y, si falla, se usa lo último bueno (hasta 6 h) sin alarmar.
let ultimoPubler = {hasta: 0, valido: 0, datos: null, cuando: null};
// Instagram directo (API oficial, sin esperar las 24 h de Publer): cada 5 min para no pasar el límite
// de llamadas por hora de Instagram.
const IG = 'https://graph.instagram.com/v26.0';
const IG_METRICAS = 'views,reach,saved,shares';  // "views" puede tardar hasta 48 h (doc de Meta)
let ultimoInstagram = {hasta: 0, datos: null, cuando: null, error: null};

const primeraLinea = (texto) => ((texto || '').trim().split('\n')[0] || '').split(/\s+/).join(' ').toLowerCase();
const dia = (fecha) => fecha.toISOString().slice(0, 10);

async function pedir(url, opciones, nombre, espera = 8000) {
  // Cada llamada tiene su límite: una red lenta no puede tumbar todo el centro (Vercel corta a los 60 s).
  const r = await fetch(url, {...opciones, signal: AbortSignal.timeout(espera)});
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

// Desde el 30-oct-2026 Publer manda cada métrica como {name, value}; antes, un número. Sin video_views, las vistas salen de reach.
const num = (x) => Number(x && typeof x === 'object' ? x.value : x) || 0;

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
  // Solo desde el primer video de Victoria: los cientos de posts viejos de la cuenta no son suyos
  // y leerlos de 10 en 10 pasaba de los 30 s que da Vercel.
  const fechas = videos.filter((v) => v.publica_utc).map((v) => new Date(v.publica_utc).getTime());
  if (!fechas.length) return {porVideo: {}};
  const hoy = new Date();
  const desde = new Date(Math.max(Math.min(...fechas) - 2 * 864e5, hoy.getTime() - 90 * 864e5));
  const hasta = new Date(hoy.getTime() + 864e5);
  const limite = Date.now() + 20_000;
  const porVideo = {};
  for (let pagina = 0; pagina < 30; pagina++) {
    if (Date.now() > limite) throw new Error('Publer tardó demasiado; se muestran los números guardados');
    const inicio = Date.now();
    const url = `${PUBLER}/analytics/post_insights?from=${dia(desde)}&to=${dia(hasta)}&page=${pagina}`;
    const r = await pedir(url, {headers: cabeceras}, 'Publer', 18_000)
      .catch(() => pedir(url, {headers: cabeceras}, 'Publer', 18_000));  // un reintento
    console.log(`publer pagina ${pagina}: ${(r.posts || []).length} posts en ${Date.now() - inicio} ms`);
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
        v: previo.v + (num(a.video_views) || num(a.reach)), l: previo.l + num(a.likes),
        c: previo.c + num(a.comments), s: previo.s + num(a.shares),
        g: previo.g + num(a.saves), alcance: previo.alcance + num(a.reach),
        enlace: p.post_link || p.url || previo.enlace,
      };
    }
    if (lote.length < 10) break;
  }
  // Publer tarda horas en tener estadísticas de un post nuevo; mientras, se marca como publicado
  // (con su enlace) para que el centro no enseñe un 0 que parece real.
  const filtros = new URLSearchParams([['state', 'published'], ['from', dia(desde)], ['to', dia(hasta)],
    ...Object.keys(cuentas).map((c) => ['account_ids[]', c])]);
  const publicados = await pedir(`${PUBLER}/posts?${filtros}`, {headers: cabeceras}, 'Publer', 12_000).catch(() => ({posts: []}));
  for (const p of publicados.posts || []) {
    const red = RED_CORTA[cuentas[p.account_id]];
    const video = red && porLinea[primeraLinea(p.text)];
    if (!video) continue;
    const destino = (porVideo[video] ||= {});
    destino[red] ||= {pendiente: true, enlace: p.post_link || p.url};
  }
  return {porVideo};
}

async function instagram(videos) {
  const token = variable('INSTAGRAM_TOKEN');
  if (!token) return null;  // sin token se sigue con Publer
  const leerIG = (ruta) => pedir(`${IG}${ruta}${ruta.includes('?') ? '&' : '?'}access_token=${encodeURIComponent(token)}`, {}, 'Instagram', 10_000);
  const yo = await leerIG('/me?fields=user_id,username').catch(() => {
    throw new Error('el permiso (INSTAGRAM_TOKEN) no sirve o ya venció: genera uno nuevo en Meta y cámbialo en Vercel');
  });
  const cuenta = yo.data?.[0] || yo;  // la doc muestra la respuesta dentro de "data"
  // Con el login de Instagram la API no da el texto del post: cada reel se reconoce por su hora de
  // publicación (Publer publica a la hora programada, con 1 o 2 minutos de diferencia).
  const fechas = videos.filter((v) => v.publica_utc).map((v) => ({id: v.id, t: new Date(v.publica_utc).getTime()}));
  if (!fechas.length) return {porVideo: {}, cuenta: cuenta.username};
  const desde = Math.floor((Math.min(...fechas.map((f) => f.t)) - 2 * 864e5) / 1000);
  const campos = 'id,timestamp,permalink,like_count,comments_count,media_type';
  const lista = await leerIG(`/${cuenta.user_id || cuenta.id}/media?fields=${campos}&since=${desde}&limit=50`);
  const medios = await Promise.all((lista.data || []).map((m) => (m.timestamp ? m : leerIG(`/${m.id}?fields=${campos}`))));
  const porVideo = {};
  await Promise.all(medios.map(async (m) => {
    const t = new Date(m.timestamp).getTime();
    const video = fechas.find((f) => Math.abs(f.t - t) <= 20 * 60_000)?.id;
    if (!video) return;
    const fila = {v: null, l: Number(m.like_count) || 0, c: Number(m.comments_count) || 0, s: 0, g: 0, alcance: 0, enlace: m.permalink, directo: true};
    for (const metricas of [IG_METRICAS, 'reach,saved,shares']) {  // si "views" no existe, al menos lo demás
      try {
        const r = await leerIG(`/${m.id}/insights?metric=${metricas}`);
        const valor = (nombre) => r.data?.find((x) => x.name === nombre)?.values?.[0]?.value;
        if (valor('views') != null) fila.v = Number(valor('views'));
        Object.assign(fila, {s: Number(valor('shares')) || 0, g: Number(valor('saved')) || 0, alcance: Number(valor('reach')) || 0});
        delete fila.sinInsights;
        break;
      } catch (e) { fila.sinInsights = e.message; }
    }
    porVideo[video] = fila;
  }));
  return {porVideo, cuenta: cuenta.username};
}

let ultimosSeguidores = {hasta: 0, datos: null};

// Seguidores de Instagram y TikTok (Publer, gráfica "followers": último valor semanal). Cada 30 min.
async function seguidores(estado) {
  if (Date.now() < ultimosSeguidores.hasta) return ultimosSeguidores.datos;
  const clave = variable('PUBLER_API_KEY');
  if (!clave) return null;
  const cabeceras = {Authorization: `Bearer-API ${clave}`, Accept: 'application/json', 'User-Agent': AGENTE,
                     'Publer-Workspace-Id': variable('PUBLER_WORKSPACE_ID')};
  const hoy = new Date();
  const desde = new Date(hoy.getTime() - 21 * 864e5);
  const datos = {};
  await Promise.all(Object.entries(estado.cuentas_publer || {}).map(async ([id, red]) => {
    const corto = {instagram: 'ig', tiktok: 'tt'}[red];
    if (!corto) return;
    try {
      const extra = corto === 'ig' ? '&chart_ids[]=countries&chart_ids[]=ages' : '';  // audiencia: solo Instagram la da
      const r = await pedir(`${PUBLER}/analytics/${id}/chart_data?chart_ids[]=followers${extra}&from=${dia(desde)}&to=${dia(hoy)}`, {headers: cabeceras}, 'Publer', 10_000);
      const serie = r.current?.followers || [];
      const ultimo = serie.at(-1)?.last_value;
      if (ultimo != null) datos[corto] = {seguidores: ultimo, antes: serie.length > 1 ? serie[0].last_value : null, serie: serie.map((x) => x.last_value)};
      if (corto === 'ig') datos.audiencia = {paises: r.current?.countries ?? null, edades: r.current?.ages?.data ?? r.current?.ages ?? null};
    } catch (e) {
      console.log(`seguidores ${red} falló: ${e.message}`);
    }
  }));
  ultimosSeguidores = {hasta: Date.now() + 30 * 60_000, datos};
  return datos;
}

const leerSiHay = (nombre) => { try { return leer(nombre); } catch { return []; } };

export default async function handler(req, res) {
  if (!autorizado(req)) return negar(res);
  res.setHeader('Cache-Control', 'private, no-store');
  if (memoria.datos && Date.now() < memoria.hasta) return res.status(200).json(memoria.datos);

  const estado = leer('estado.json')[0];
  // Videos y carruseles: los dos se miden en vivo (YouTube por id, Publer por la primera línea del pie).
  const videos = [...leer('videos.json'), ...leerSiHay('carruseles.json')];
  const ahora = Date.now();
  const [yt, pbNuevo, igNuevo, seg] = await Promise.allSettled([
    youtube(estado, videos),
    ahora < ultimoPubler.hasta ? Promise.resolve(ultimoPubler.datos) : publer(estado, videos),
    ahora < ultimoInstagram.hasta ? Promise.resolve(ultimoInstagram.datos) : instagram(videos),
    seguidores(estado),
  ]);
  if (ahora >= ultimoInstagram.hasta) {
    ultimoInstagram = igNuevo.status === 'fulfilled'
      ? {hasta: ahora + 5 * 60_000, datos: igNuevo.value, cuando: new Date(ahora).toISOString(), error: null}
      : {...ultimoInstagram, hasta: ahora + 60_000, error: igNuevo.reason?.message};
    if (igNuevo.status === 'rejected') console.log(`instagram falló: ${igNuevo.reason?.message}`);
  }
  const ig = ultimoInstagram.datos;
  let pb = pbNuevo;
  if (pb.status === 'fulfilled' && ahora >= ultimoPubler.hasta) {
    ultimoPubler = {hasta: ahora + 10 * 60_000, valido: ahora + 6 * 3600_000, datos: pb.value, cuando: new Date(ahora).toISOString()};
  } else if (pb.status === 'rejected') {
    console.log(`publer falló: ${pb.reason?.message}`);
    if (ultimoPubler.datos && ahora < ultimoPubler.valido) pb = {status: 'fulfilled', value: ultimoPubler.datos};
  }
  const porVideo = {};
  for (const [fuente, resultado] of [['yt', yt], ['pb', pb]]) {
    if (resultado.status !== 'fulfilled') continue;
    for (const [id, redes] of Object.entries(resultado.value.porVideo)) {
      porVideo[id] = {...porVideo[id], ...(fuente === 'yt' ? {yt: redes} : redes)};
    }
  }
  for (const [id, fila] of Object.entries(ig?.porVideo || {})) porVideo[id] = {...porVideo[id], ig: fila};  // Instagram directo manda
  const datos = {
    actualizado: new Date().toISOString(),
    canal: yt.status === 'fulfilled' ? {suscriptores: yt.value.suscriptores, vistas: yt.value.vistas} : null,
    publer_actualizado: pb.status === 'fulfilled' ? ultimoPubler.cuando : null,
    instagram_actualizado: ig ? ultimoInstagram.cuando : null,
    porVideo,
    seguidores: seg.status === 'fulfilled' ? seg.value : null,
    errores: [
      ...(yt.status === 'rejected' ? [`YouTube: ${yt.reason.message}`] : []),
      ...(pb.status === 'rejected' ? [`Publer: ${pb.reason.message}`] : []),
      ...(ultimoInstagram.error ? [`Instagram: ${ultimoInstagram.error}`] : []),
    ],
  };
  memoria = {hasta: Date.now() + 55_000, datos};
  res.status(200).json(datos);
}
