// Centro de mando de Victoria: pide la última foto del sistema (/api/estado) y los números en vivo (/api/vivo) cada minuto.
const REDES = [
  {clave: 'yt', nombre: 'YouTube', corto: 'YT', color: '#ff3b55'},
  {clave: 'tt', nombre: 'TikTok', corto: 'TT', color: '#facc15'},
  {clave: 'ig', nombre: 'Instagram', corto: 'IG', color: '#a855f7'},
  {clave: 'fb', nombre: 'Facebook', corto: 'FB', color: '#1877f2'},  // página "Victoria the CEO" desde el 9-nov-2026
];
const ESTADOS = {pendiente: ['En cola', ''], reserva: ['En reserva', ''], listo_para_publicar: ['Listo', 'listo'], en_proceso: ['Generando', 'vivo'], programado: ['Programado', 'ok'], publicado: ['Publicado', 'ok'], ok: ['OK', 'ok'], fallido: ['Falló', 'mal'], omitido: ['Omitido', ''], listo: ['Listo', 'listo'], borrador: ['Borrador', ''], por_programar: ['Por programar', ''], produciendo: ['Produciendo', 'vivo']};
const NOMBRE_RED = {ig: 'Instagram', tt: 'TikTok', yt: 'YouTube', fb: 'Facebook'};
// Todo lo que sale: videos y carruseles (los dos se miden en vivo).
const todo = () => [...FOTO.videos, ...(FOTO.carruseles || [])];
const PILARES = {negocio: 'Negocio', finanzas: 'Finanzas', mentalidad: 'Mentalidad', vida: 'Vida', motivacion_economica: 'Motivación $', empresas: 'Empresas'};
const DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'];
const ORO = '#f5c542', CIAN = '#49d6ec', ROJO = '#ff3b55', FONDO = '#07111a';
const MINUTO = 60_000;

let FOTO = null;   // /api/estado
let VIVO = null;   // /api/vivo
let AGENDA = null; // /api/agenda: lo programado y lo publicado en cada red, en vivo
const $ = (id) => document.getElementById(id);
const crear = (etiqueta, props = {}, ...hijos) => { const el = Object.assign(document.createElement(etiqueta), props); el.append(...hijos); return el; };
const fmt = (n) => (n == null || Number.isNaN(n) ? '—' : Math.round(n).toLocaleString('es-MX'));
const compacto = (n) => (n == null ? '—' : Math.abs(n) >= 10000 ? new Intl.NumberFormat('es-MX', {notation: 'compact', maximumFractionDigits: 1}).format(n) : fmt(n));
const pct = (x) => (x == null ? '—' : `${Math.round(x * 100)}%`);
const mx = (iso, op = {day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'}) => (iso ? new Date(iso).toLocaleString('es-MX', {timeZone: 'America/Mexico_City', ...op}) : '');
const porFecha = (a, b) => (a.fecha_utc < b.fecha_utc ? -1 : 1);
// Texto para Rodrigo, no para máquinas (11-nov-2026): "2026-11-08" → "8 nov", "1 video" / "2 videos", títulos en vez de números.
const fechaCorta = (iso) => new Date(`${String(iso).slice(0, 10)}T12:00:00`).toLocaleDateString('es-MX', {day: 'numeric', month: 'short'}).replace('.', '');
const sinIso = (t) => String(t || '').replace(/\b(\d{4}-\d{2}-\d{2})(?:[T ][\d:.]+Z?)?\b/g, (_, d) => fechaCorta(d));
const plural = (n, uno, varios) => `${fmt(n)} ${n === 1 ? uno : varios}`;
const recortar = (t, n) => { t = String(t || '').trim(); return t.length <= n ? t : `${t.slice(0, n).replace(/[\s,;:.(¿¡—-]+\S*$/, '')}…`; };
const hoyMx = () => new Date().toLocaleDateString('en-CA', {timeZone: 'America/Mexico_City'});
function titulo(id, n = 42) {
  const p = todo().find((x) => String(x.id) === String(id));
  const t = p && (p.titulo || p.titulo_post || p.gancho || String(p.tema || '').replace(/_/g, ' '));
  return t ? `«${recortar(t, n)}»` : `${String(id).startsWith('c') ? 'carrusel' : 'video'} ${id}`;
}

// ---------- acceso ----------
async function pedir(ruta, opciones) {
  const r = await fetch(ruta, {credentials: 'same-origin', ...opciones});
  if (r.status === 401) throw Object.assign(new Error('sin acceso'), {acceso: true});
  if (!r.ok) throw new Error(`${ruta} respondió ${r.status}`);
  return r.json();
}

function mostrar(id) {
  for (const s of ['acceso', 'arranque', 'tablero']) $(s).hidden = s !== id;
}

$('formulario').addEventListener('submit', async (e) => {
  e.preventDefault();
  const boton = e.target.querySelector('button');
  boton.disabled = true;
  $('error-acceso').textContent = '';
  try {
    const r = await fetch('/api/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({clave: $('clave').value})});
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || 'clave incorrecta');
    await arrancar(true);
  } catch (err) {
    $('error-acceso').textContent = err.message === 'clave incorrecta' ? 'Clave incorrecta' : err.message;
  } finally {
    boton.disabled = false;
  }
});

$('salir').addEventListener('click', async () => {
  await fetch('/api/login', {method: 'DELETE'});
  location.reload();
});

async function consola(lineas) {
  mostrar('arranque');
  const pre = $('consola');
  pre.textContent = '';
  const rapido = matchMedia('(prefers-reduced-motion: reduce)').matches;
  for (const [texto, ok] of lineas) {
    pre.append(`> ${texto} `);
    await new Promise((listo) => setTimeout(listo, rapido ? 0 : 170));
    pre.append(crear('b', {textContent: ok ? '[ OK ]' : ''}), '\n');
  }
  await new Promise((listo) => setTimeout(listo, rapido ? 0 : 350));
}

async function arrancar(conAnimacion) {
  // El tablero sale con la última foto; lo en vivo se suma cuando llega (Publer puede tardar).
  const vivoEnCamino = pedir('/api/vivo').catch((err) => ({errores: [err.message], porVideo: {}}));
  const foto = await pedir('/api/estado');
  const vivo = await Promise.race([vivoEnCamino, new Promise((listo) => setTimeout(() => listo(null), 4000))]);
  FOTO = foto;
  VIVO = vivo;
  if (!vivo) vivoEnCamino.then((v) => { if (!VIVO) { VIVO = v; dibujarTodo(); } });
  if (conAnimacion) {
    await consola([
      ['Autenticando operador', true],
      ['Enlace con YouTube', Boolean(vivo) && !vivo.errores?.some((x) => x.startsWith('YouTube'))],
      ['Enlace con Publer (TikTok · Instagram · Facebook)', Boolean(vivo) && !vivo.errores?.some((x) => x.startsWith('Publer'))],
      [`Cargando ${foto.videos.length} videos del plan`, true],
      [`Reactor de créditos: ${fmt(resumen().restantes)}`, true],
      ['Centro de mando en línea', true],
    ]);
  }
  mostrar('tablero');
  dibujarTodo();
  if (!arrancar.hecho) {
    arrancar.hecho = true;
    armarNavegacion();
    avatar3d();
    setInterval(refrescarVivo, MINUTO);
    refrescarAgenda();
    setInterval(refrescarAgenda, MINUTO);
    setInterval(async () => {
      try {
        const nueva = await pedir('/api/estado');
        if (nueva.version && FOTO.version && nueva.version !== FOTO.version) return location.reload();  // diseño nuevo publicado
        FOTO = nueva;
        dibujarTodo();
      } catch { /* sigue con la foto anterior */ }
    }, 2 * MINUTO);
    setInterval(relojes, 1000);
    let ancho = innerWidth;
    addEventListener('resize', () => { if (Math.abs(innerWidth - ancho) > 40) { ancho = innerWidth; dibujarGraficas(); } });
  }
}

async function refrescarAgenda() {
  try {
    const r = await pedir('/api/agenda');
    if (r.agenda) { AGENDA = r.agenda; dibujarDespegues(); dibujarCalendario(FOTO.calendario); }
  } catch { /* se queda la última agenda o la de la foto */ }
}

async function refrescarVivo() {
  try {
    VIVO = await pedir('/api/vivo');
  } catch (err) {
    if (err.acceso) return location.reload();
    VIVO = {...(VIVO || {}), errores: [err.message]};
  }
  dibujarTodo();
}

// ---------- datos ----------
function medidas(v) {
  // Primero lo que llega en vivo; si no, la última foto que guardó el sistema.
  const vivo = VIVO?.porVideo?.[v.id] || {};
  const m = {};
  for (const {clave} of REDES) {
    if (vivo[clave]) m[clave] = vivo[clave];
    else if (v[`v_${clave}`] != null) m[clave] = {v: v[`v_${clave}`], l: v[`l_${clave}`], c: v[`c_${clave}`], s: v[`s_${clave}`], g: v[`g_${clave}`], ret: v[`r_${clave}`]};
  }
  // Comentarios de Instagram: solo los de otras personas (Publer cuenta también los de Victoria). Los lee la rutina de Meta.
  if (m.ig && v.c_ig_reales != null) m.ig = {...m.ig, c: v.c_ig_reales};
  if (m.yt && v.c_yt_reales != null) m.yt = {...m.yt, c: v.c_yt_reales};  // igual en YouTube: sin las respuestas del canal
  return m;
}
const vistasDe = (v) => Object.values(medidas(v)).reduce((s, x) => s + (Number(x.v) || 0), 0);
// Un video cuenta como medido cuando ya salió (antes, YouTube reporta 0 del video programado).
// Ya salió en al menos una red (antes esperaba a la última: un carrusel en TikTok no contaba hasta su short de la noche).
const salio = (v) => [v.publica_utc, ...Object.values(v.publica_utc_por_red || {})].some((t) => t && new Date(t).getTime() <= Date.now());
const medido = (v) => salio(v) && Object.keys(medidas(v)).length > 0;

function resumen() {
  const {videos, ejecuciones, aprendizajes} = FOTO;
  const orden = [...ejecuciones].sort(porFecha);
  const ultima = orden.at(-1);
  const generados = ejecuciones.filter((e) => e.tipo === 'generar' && Number(e.creditos_usados) > 0);
  const costo = generados.length ? generados.reduce((s, e) => s + Number(e.creditos_usados), 0) / generados.length : null;
  const restantes = ultima ? Number(ultima.creditos_restantes) : null;
  const usados = ejecuciones.reduce((s, e) => s + (Number(e.creditos_usados) || 0), 0);
  const alcanzan = restantes != null && costo ? Math.floor(restantes / costo) : null;
  const calidades = videos.map((v) => Number(v.qa_similitud)).filter((q) => q > 0);
  let likes = 0;
  for (const v of todo().filter(salio)) for (const x of Object.values(medidas(v))) likes += Number(x.l) || 0;
  return {
    publicados: todo().filter((v) => ['programado', 'publicado'].includes(v.estado)).length,
    listos: videos.filter((v) => v.estado === 'listo_para_publicar').length,
    cola: videos.filter((v) => v.estado === 'pendiente').length,
    fallos: ejecuciones.filter((e) => e.resultado === 'fallido').length,
    vistas: todo().filter(salio).reduce((s, v) => s + vistasDe(v), 0),
    likes,
    calidad: calidades.length ? calidades.reduce((s, q) => s + q, 0) / calidades.length : null,
    lecciones: aprendizajes.length,
    restantes, usados, costo, alcanzan,
    iniciales: restantes != null ? restantes + usados : null,
  };
}

function promedioPor(campo) {
  const g = new Map();
  for (const v of FOTO.videos) {
    if (!medido(v) || !v[campo]) continue;
    const x = g.get(v[campo]) || {grupo: v[campo], videos: 0, total: 0};
    x.videos += 1;
    x.total += vistasDe(v);
    g.set(v[campo], x);
  }
  return [...g.values()].map((x) => ({...x, promedio: x.total / x.videos}));
}

function mejoras() {
  const lista = [];
  const {ejecuciones} = FOTO;
  const medidos = todo().filter(medido);  // videos y carruseles (11-nov-2026: contaba solo los videos y decía "6 de 8")
  if (medidos.length < 8) {
    lista.push(['dato', `${medidos.length} de 8 publicaciones medidas. Con 8 ya se decide la mejor hora y el mejor tema con datos, no a ojo.`]);
  } else {
    for (const [campo, nombre] of [['pilar', 'tema'], ['hora_plan', 'hora']]) {
      const g = promedioPor(campo).filter((x) => x.videos >= 2).sort((a, b) => b.promedio - a.promedio);
      if (g.length > 1) {
        const etq = (x) => (campo === 'pilar' ? PILARES[x.grupo] || x.grupo : x.grupo);
        lista.push(['idea', `Mejor ${nombre}: ${etq(g[0])} promedia ${fmt(g[0].promedio)} vistas por video contra ${fmt(g.at(-1).promedio)} de ${etq(g.at(-1))}.`]);
      }
    }
    const mejor = [...medidos].sort((a, b) => vistasDe(b) - vistasDe(a))[0];
    lista.push(['idea', `${String(mejor.id).startsWith('c') ? 'El carrusel' : 'El video'} ${mejor.id} es el récord con ${fmt(vistasDe(mejor))} vistas: "${mejor.gancho || mejor.titulo || ''}".`]);
  }
  const r = resumen();
  if (r.listos) lista.push(['dato', `${r.listos === 1 ? '1 video ya generado espera' : `${r.listos} videos ya generados esperan`} salir: se publican sin gastar créditos.`]);
  // Solo las fallas de los últimos 7 días (11-nov-2026: seguía saliendo una del 31-oct ya resuelta).
  const hace7 = Date.now() - 7 * 86400000;
  const fallos = ejecuciones.filter((e) => e.resultado === 'fallido' && new Date(e.fecha_utc).getTime() > hace7).sort(porFecha);
  if (fallos.length) lista.push(['alerta', `${fallos.length} ejecución(es) no publicaron esta semana. Última: ${fallos.at(-1).detalle}`]);
  if (r.alcanzan != null) {
    lista.push(r.alcanzan < 6
      ? ['alerta', `Energía para solo ${r.alcanzan} videos. Recarga OpenArt o baja la frecuencia.`]
      : ['dato', `Energía para unos ${r.alcanzan} videos más: ${r.alcanzan * (FOTO.estado.dias_entre_videos || 2)} días al ritmo actual.`]);
  }
  if (r.cola <= 3) lista.push(['alerta', `Quedan ${r.cola} guiones en cola. Pide a Claude el siguiente plan de videos.`]);
  for (const e of VIVO?.errores || []) lista.push(['alerta', `Sin conexión en vivo con ${e}`]);
  for (const a of (FOTO.auditoria?.alertas || []).filter((x) => !(r.alcanzan != null && /^Créditos para/.test(x)))) lista.push([/pierde|revisar|fallaron|Recargar/.test(a) ? 'alerta' : /gana/.test(a) ? 'idea' : 'dato', a]);
  return lista;
}

// ---------- dibujo ----------
function dibujarTodo() {
  const r = resumen();
  const {estado, videos, ejecuciones, aprendizajes} = FOTO;
  if (estado.foto_perfil && !$('foto').firstChild) $('foto').append(crear('img', {src: estado.foto_perfil, alt: 'Victoria y Capital'}));
  $('l-publicados').textContent = fmt(r.publicados);
  $('l-listos').textContent = `${fmt(r.listos)} ${r.listos === 1 ? 'video listo' : 'videos listos'}`;
  $('l-alcanzan').textContent = fmt(r.alcanzan);
  contar($('vistas-totales'), r.vistas);
  const sigue = proxima();
  $('mision-que').textContent = sigue?.que || '—';
  $('minimo-calidad').textContent = pct(estado.similitud_minima);
  $('mision-cuando').textContent = sigue ? mx(sigue.utc, {weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit'}) : '—';
  contar($('m-subs'), VIVO?.canal?.suscriptores);
  contar($('m-likes'), r.likes);
  $('m-calidad').textContent = pct(r.calidad);
  $('m-cola').textContent = fmt(r.cola);
  $('m-fallos').textContent = fmt(r.fallos);
  if ($('m-fallos-sub')) $('m-fallos-sub').textContent = r.fallos === 1 ? 'vez que no se publicó' : 'veces que no se publicó';
  $('m-lecciones').textContent = fmt(r.lecciones);
  $('a-usados').textContent = fmt(r.usados);
  $('a-costo').textContent = fmt(r.costo);
  $('a-dias').textContent = r.alcanzan == null ? '—' : fmt(r.alcanzan * 2);
  pintarReplicate();

  const errores = VIVO?.errores || [];
  $('aviso').hidden = !errores.length;
  $('aviso').textContent = errores.length ? `Conexión en vivo incompleta: ${errores.join(' · ')}. Se muestran los últimos números guardados.` : '';
  $('pulso').classList.toggle('falla', errores.length > 0);
  $('pie').textContent = `YouTube en vivo · TikTok, Instagram y Facebook vía Publer · última foto del sistema: ${mx(estado.generado_utc)} · créditos según la última ejecución`;

  dibujarRedes();
  dibujarLaboratorio(FOTO.auditoria || {});
  dibujarCinta(ejecuciones, aprendizajes);
  dibujarHangar(videos);
  dibujarListas(aprendizajes);
  dibujarTablas(videos, ejecuciones);
  dibujarCalendario(FOTO.calendario);
  dibujarLargos(FOTO.largos);
  dibujarSalud(estado.salud);
  dibujarPublicaciones();
  dibujarMetas();
  dibujarDespegues();
  dibujarAudiencia();
  dibujarVentas();
  dibujarConexiones();
  dibujarHorarios(FOTO.auditoria || {}, estado);
  dibujarCarruseles(FOTO.carruseles);
  dibujarGraficas();
  dibujarComentarHoy();
  relojes();
}

function contar(el, destino) {
  // Odómetro: anima del valor anterior al nuevo.
  if (destino == null) { el.textContent = '—'; return; }
  const desde = Number(el.dataset.valor) || 0;
  el.dataset.valor = destino;
  if (desde === destino || matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = fmt(destino); return; }
  if (el.dataset.visto) {  // cambió en vivo (no es la primera carga): destello para que se note qué se movió
    el.classList.remove('cambio');
    void el.offsetWidth;
    el.classList.add('cambio');
  }
  el.dataset.visto = '1';
  const inicio = performance.now();
  const paso = (t) => {
    const k = Math.min(1, (t - inicio) / 1200);
    el.textContent = fmt(desde + (destino - desde) * (1 - (1 - k) ** 3));
    if (k < 1) requestAnimationFrame(paso);
  };
  requestAnimationFrame(paso);
}

// Siguiente salida: la primera de la foto que aún no pasa (si ya salió, la que sigue).
function proxima() {
  const e = FOTO.estado;
  const lista = e.proximas?.length ? e.proximas : (e.proxima_ejecucion_utc ? [{utc: e.proxima_ejecucion_utc, que: e.proxima_que}] : []);
  return lista.find((x) => new Date(x.utc).getTime() > Date.now()) || lista.at(-1) || null;
}

function relojes() {
  if (!FOTO) return;
  tictac();
  $('reloj').textContent = `CDMX ${new Date().toLocaleTimeString('es-MX', {timeZone: 'America/Mexico_City', hour: '2-digit', minute: '2-digit', second: '2-digit'})}`;
  const segs = VIVO?.actualizado ? Math.max(0, Math.round((Date.now() - new Date(VIVO.actualizado)) / 1000)) : null;
  $('hace').textContent = segs == null ? '—' : segs < 60 ? `hace ${segs} s` : `hace ${Math.round(segs / 60)} min`;
  const objetivo = proxima() ? new Date(proxima().utc).getTime() : null;
  const cuenta = $('cuenta');
  if (!objetivo) { cuenta.textContent = '—'; return; }
  let s = Math.max(0, Math.floor((objetivo - Date.now()) / 1000));
  const partes = [['días', Math.floor(s / 86400)], ['hrs', Math.floor((s %= 86400) / 3600)], ['min', Math.floor((s %= 3600) / 60)], ['seg', s % 60]];
  cuenta.replaceChildren(...partes.map(([etq, n]) => crear('span', {}, crear('b', {textContent: String(n).padStart(2, '0')}), crear('small', {textContent: etq}))));
}

function retencionPromedio() {
  const valores = FOTO.videos.filter(salio).map((v) => medidas(v).yt?.ret).filter((x) => x != null);
  return valores.length ? `${(valores.reduce((s, x) => s + x, 0) / valores.length).toFixed(1)}%` : '—';
}

function seguidoresDe(clave) {
  // YouTube en vivo por su API; Instagram, TikTok y Facebook por Publer (último dato semanal).
  const n = clave === 'yt' ? VIVO?.canal?.suscriptores : VIVO?.seguidores?.[clave]?.seguidores;
  const antes = VIVO?.seguidores?.[clave]?.antes;
  const cambio = n != null && antes != null && n !== antes ? ` (${n > antes ? '+' : ''}${fmt(n - antes)} en 3 semanas)` : '';
  return crear('p', {className: 'seguidores', textContent: n == null ? 'Seguidores: —' : `${fmt(n)} ${clave === 'yt' ? 'suscriptores' : 'seguidores'}${cambio}`});
}

function dibujarRedes() {
  const caja = $('redes');
  caja.replaceChildren();
  for (const red of REDES) {
    let v = 0, l = 0, c = 0, s = 0, hay = false, enCamino = false, sinVistas = false;
    for (const video of todo().filter(salio)) {
      const m = medidas(video)[red.clave];
      if (!m) continue;
      if (m.pendiente) { enCamino = true; continue; }
      hay = true;
      if (m.v == null) sinVistas = true;  // Instagram directo: likes y comentarios ya, vistas con retraso
      v += Number(m.v) || 0; l += Number(m.l) || 0; c += Number(m.c) || 0; s += (Number(m.s) || 0) + (Number(m.g) || 0);
    }
    const directo = red.clave === 'ig' && Boolean(VIVO?.instagram_actualizado);
    const enVivo = red.clave === 'yt' ? Boolean(VIVO?.canal) : directo || (Boolean(VIVO) && !(VIVO.errores || []).some((e) => e.startsWith('Publer')));
    const tarjeta = crear('article', {className: 'red'});
    tarjeta.style.setProperty('--acento', red.color);
    const valor = crear('div', {className: 'vistas'});
    const numero = crear('span', {textContent: hay && !(sinVistas && !v) ? fmt(v) : enCamino || sinVistas ? '—' : '0'});
    valor.append(numero, crear('small', {textContent: !hay && enCamino ? 'publicado · Publer manda las cifras en unas horas'
      : sinVistas && !v ? 'vistas: Instagram las entrega con retraso' : 'vistas'}));
    tarjeta.append(
      crear('header', {}, crear('h3', {textContent: red.nombre}), crear('span', {className: `etiqueta-vivo${enVivo ? '' : ' foto'}`, textContent: enVivo ? '● en vivo' : 'última foto'})),
      valor,
      seguidoresDe(red.clave),
      crear('dl', {}, ...[['Likes', l], ['Coment.', c], [red.clave === 'yt' ? 'Retención' : 'Compart.', red.clave === 'yt' ? retencionPromedio() : s], ['Por post', hay ? v / Math.max(1, todo().filter((x) => salio(x) && medidas(x)[red.clave]).length) : 0]]
        .map(([dt, dd]) => crear('div', {}, crear('dt', {textContent: dt}), crear('dd', {textContent: typeof dd === 'string' ? dd : compacto(dd)})))),
    );
    caja.append(tarjeta);
  }
}

function dibujarCinta(ejecuciones, aprendizajes) {
  // Resumen corto y sin jerga (11-nov-2026: la cinta mostraba "voz_victoria cargaba Chatterbox"); el detalle completo
  // sigue en la tabla de ejecuciones. Si una ejecución vieja no trae resumen, se corta la primera frase del detalle.
  const corto = (e) => e.resumen || String(e.detalle || e.nota || '').split(/[.:;(]/)[0].slice(0, 90);
  const eventos = [...ejecuciones].sort(porFecha).reverse().slice(0, 6).map((e) => `${mx(e.fecha_utc)} · ${(ESTADOS[e.resultado] || [e.resultado])[0]} · ${corto(e)}`);
  eventos.push(...aprendizajes.slice(-3).filter((a) => a.tipo !== 'tecnico').map((a) => recortar(`Lección: ${a.aprendizaje || a.regla}`.replace(/\b[cC]\d{2}\s+(?=["'«“])/g, ''), 160)));  // sin "c16" delante de un título
  const cinta = $('cinta');
  // Dos copias para que el desplazamiento sea continuo.
  cinta.replaceChildren(...[...eventos, ...eventos].map((t) => crear('span', {textContent: t})));
}

function dibujarHangar(videos) {
  const caja = $('hangar');
  caja.replaceChildren();
  // Primero lo que viene (listo o programado sin salir), luego lo más reciente; lo que falta generar al final (11-nov-2026:
  // abría con los videos 01 y 02 de octubre).
  const rango = (v) => (!salio(v) && ['programado', 'listo_para_publicar', 'en_proceso'].includes(v.estado) ? 0 : salio(v) ? 1 : 2);
  const turno = [FOTO.auditoria?.decision?.publicar_hoy, ...(FOTO.estado.prioridad_publicar || [])].filter(Boolean);
  const lugar = (v) => (turno.includes(v.id) ? turno.indexOf(v.id) : turno.length);
  const orden = [...videos].sort((a, b) => rango(a) - rango(b) || (rango(a) === 0 ? lugar(a) - lugar(b) : 0) || (rango(a) === 1 ? String(b.publica_utc || '').localeCompare(String(a.publica_utc || '')) : 0));
  for (const v of orden) {
    const poster = crear('div', {className: 'poster'});
    poster.append(v.miniatura ? crear('img', {src: v.miniatura, alt: `Video ${v.id}`, loading: 'lazy'}) : crear('em', {textContent: `${(v.locacion || '').replace('_', ' ')} · por generar`}));
    poster.append(crear('span', {className: 'num', textContent: v.id}));
    if (medido(v)) poster.append(crear('span', {className: 'ojo', textContent: `▶ ${compacto(vistasDe(v))}`}));
    const [texto, clase] = ESTADOS[v.estado] || [v.estado, ''];
    const m = medidas(v);
    const linea = !salio(v) ? '' : [...REDES.filter((r) => m[r.clave]).map((r) => (m[r.clave].pendiente ? `${r.corto} ✓` : `${r.corto} ${compacto(m[r.clave].v)}`)),
      ...(m.yt?.ret != null ? [`visto ${m.yt.ret}%`] : [])].join(' · ');
    const extra = [PILARES[v.pilar] || v.pilar];
    if (Number(v.qa_similitud) > 0) extra.push(`calidad ${pct(Number(v.qa_similitud))}`);
    caja.append(crear('div', {className: 'tarjeta'}, poster, crear('div', {className: 'info'},
      crear('span', {className: `chip ${clase}`, textContent: v.publica_mx && ['programado', 'publicado'].includes(v.estado) ? `${texto} · ${fechaCorta(v.publica_mx)}` : texto}),
      crear('p', {textContent: v.titulo || v.gancho}),
      crear('p', {className: 'met', textContent: extra.join(' · ')}),
      ...(linea ? [crear('p', {className: 'met', textContent: linea})] : []))));
  }
}

const ATRIBUTOS = {pilar: 'Tema', tipo_fondo: 'Tipo de fondo', locacion: 'Fondo', estilo_vestuario: 'Vestimenta',
  color_vestuario: 'Color de ropa', tipo_gancho: 'Tipo de gancho', titulo_emoji: 'Emoji en el título',
  titulo_largo: 'Largo del título', titulo_tipo: 'Título: afirma o pregunta', dia: 'Día', hora: 'Hora'};
const MODOS = {aprovechar: 'Aprovechar', explorar: 'Explorar', prioridad: 'Prioridad', 'sin guiones': 'Sin guiones'};
const VALORES = {numero: 'Número', dato: 'Dato', pregunta: 'Pregunta', contradiccion: 'Contradicción', historia: 'Historia', afirma: 'Afirma'};

function dibujarLaboratorio(a) {
  const caja = $('decision');
  const d = a.decision;
  const texto = crear('div');
  if (!d) {
    texto.append(crear('p', {textContent: 'No hay guiones pendientes: el sistema escribe 10 nuevos en la siguiente ejecución.'}));
  } else {
    // Sin nombres de archivos ni claves internas en el texto para Rodrigo (11-nov-2026: salía "(config.json → prioridad_videos)").
    const llano = (t) => String(t || '').replace(/\s*\((?:config\.json|contenido\/)[^)]*\)/g, '').replace(/config\.json\s*→\s*\w+/g, 'la configuración');
    const motivo = sinIso(llano(d.motivo)).replace(/^el último/, 'el último video');
    texto.append(crear('p', {textContent: d.toca_publicar && d.publicar_hoy ? `Hoy sale el video ${titulo(d.publicar_hoy, 60)} (${motivo}).`
      : d.toca_publicar ? `Hoy toca video (${motivo}), pero no hay uno listo.` : `Hoy no sale video: ${motivo}.`}));
    const cs = d.carruseles || {};
    const tts = (cs.tiktoks || (cs.tiktok ? [cs.tiktok] : [])).map((x) => titulo(x.id, 70));
    if (tts.length) texto.append(crear('p', {className: 'nota', textContent: `Carruseles de hoy en TikTok: ${tts.join(', ')}.`}));
    if (d.video_id) texto.append(crear('p', {className: 'nota', textContent: `Lo siguiente que se genera: el video ${titulo(d.video_id, 50)}${d.modo === 'prioridad' ? ', que tiene prioridad' : ` (${llano(d.por_que).replace(/\.$/, '')})`}.`}));
    if (d.horarios) texto.append(crear('p', {className: 'nota', textContent: `Hoy cada red a su hora: ${Object.entries(d.horarios).map(([r, h]) => `${NOMBRE_RED[r]} ${h}`).join(' · ')}.`}));
    if (a.reglas_vigentes?.length) texto.append(crear('ul', {}, ...a.reglas_vigentes.map((r) => crear('li', {textContent: r}))));
    if (d.cambios_sugeridos?.length) {
      texto.append(crear('ul', {}, ...d.cambios_sugeridos.map((c) => crear('li', {textContent: `${ATRIBUTOS[c.atributo] || c.atributo}: ${c.de} → ${c.a} (${c.por_que})`}))));
    }
  }
  texto.append(crear('p', {className: 'nota', textContent: `${a.videos_calificados || 0} videos calificados${a.base_vistas_36h ? ` · lo normal: ${fmt(a.base_vistas_36h)} vistas a 36 h` : ''}${a.fecha_utc ? ` · auditoría del ${mx(a.fecha_utc)}` : ''}`}));
  const modo = d?.modo || 'aprovechar';
  // El recuadro grande dice lo de HOY (11-nov-2026: decía "Prioridad · video 40" el día que salía O1).
  const sale = d?.toca_publicar && d?.publicar_hoy;
  caja.replaceChildren(crear('div', {className: `modo ${sale ? 'aprovechar' : modo}`}, sale ? 'Hoy sale' : (MODOS[modo] || modo),
    crear('small', {textContent: sale ? `video ${d.publicar_hoy}` : d?.video_id ? `siguiente: video ${d.video_id}` : 'sin video'})), texto);

  const lab = $('laboratorio');
  lab.replaceChildren();
  const ranking = a.ranking || {};
  if (!Object.keys(ranking).length) {
    lab.append(crear('article', {className: 'panel ancho'}, crear('p', {className: 'vacio', textContent: 'Aquí aparece qué tema, fondo, vestimenta, color, gancho y día funcionan mejor. Se llena 36 horas después de que salga el primer video y se vuelve confiable con 6 o más.'})));
    return;
  }
  for (const [atributo, filas] of Object.entries(ranking)) {
    const tope = Math.max(2, ...filas.map((f) => f.indice));
    const lista = crear('div', {className: 'atributo'});
    for (const f of filas) {
      const barra = crear('div', {className: `barra-ind ${f.estado === 'gana' ? 'gana' : f.estado === 'pierde' ? 'pierde' : ''}`});
      const relleno = crear('i');
      relleno.style.width = `${Math.min(100, (f.indice / tope) * 100)}%`;
      const uno = crear('b');
      uno.style.left = `${(1 / tope) * 100}%`;
      barra.append(relleno, uno);
      barra.title = `${f.estado} · ${f.n} videos · interacción ${pct(f.engagement)}`;
      lista.append(crear('div', {className: 'fila'}, crear('span', {textContent: PILARES[f.valor] || VALORES[f.valor] || f.valor.replace(/_/g, ' ')}), barra, crear('em', {textContent: `${f.indice.toFixed(2)} · ${f.n} vid.`})));
    }
    const tarjeta = crear('article', {className: 'panel'}, crear('div', {className: 'codigo', textContent: `LAB · ${atributo.replace(/_/g, ' ')}`}), crear('h2', {textContent: ATRIBUTOS[atributo] || atributo}), lista);
    // A la vista solo lo que más decide (11-nov-2026: eran 14 tarjetas, casi todas con 1 video); el resto en "Ver las demás".
    if (['pilar', 'tipo_gancho', 'hora'].includes(atributo)) lab.append(tarjeta);
    else (lab.querySelector('.lab-mas .lab-rejilla') || lab.appendChild(crear('details', {className: 'lab-mas panel ancho'},
      crear('summary', {textContent: 'Ver las demás variables (fondo, ropa, color, título, día)'}), crear('div', {className: 'lab-rejilla'}))).querySelector('.lab-rejilla')).append(tarjeta);
  }
  const mas = lab.querySelector('.lab-mas');
  if (mas) lab.append(mas);  // siempre al final
}

function elemento(clase, etiqueta, texto, detalle) {
  const cuerpo = crear('span', {}, texto);
  if (detalle) cuerpo.append(crear('i', {textContent: detalle}));
  return crear('li', {className: clase}, crear('small', {textContent: etiqueta}), cuerpo);
}

function dibujarListas(aprendizajes) {
  const etiquetas = {dato: 'Dato', alerta: 'Alerta', idea: 'Mejora'};
  $('mejoras').replaceChildren(...mejoras().map(([tipo, texto]) => elemento(tipo, etiquetas[tipo], texto)));
  const tipos = {tecnico: 'Técnica', contenido: 'Contenido', publicacion: 'Publicar'};
  const recientes = [...aprendizajes].sort((a, b) => (a.fecha_utc < b.fecha_utc ? 1 : -1));
  $('lecciones').replaceChildren(...recientes.map((a) => elemento(a.tipo, tipos[a.tipo] || a.tipo, a.regla, `${a.origen}: ${a.aprendizaje}`)));
}

const celda = (texto, clase = '') => crear('td', {className: clase, textContent: texto ?? ''});
const chip = (estado) => { const [t, c] = ESTADOS[estado] || [estado, '']; return crear('td', {}, crear('span', {className: `chip ${c}`, textContent: t})); };

function dibujarTablas(videos, ejecuciones) {
  $('t-plan').replaceChildren(...videos.map((v) => crear('tr', {}, celda(v.id), chip(v.estado), celda(PILARES[v.pilar] || v.pilar), celda((v.locacion || '').replace('_', ' ')),
    celda(v.gancho), celda(v.publica_mx), celda(medido(v) ? fmt(vistasDe(v)) : '', 'n'), celda(Number(v.qa_similitud) > 0 ? pct(Number(v.qa_similitud)) : '', 'n'), celda(v.creditos == null ? '' : fmt(v.creditos), 'n'))));
  $('t-bitacora').replaceChildren(...[...ejecuciones].sort(porFecha).reverse().map((e) => crear('tr', {}, celda(mx(e.fecha_utc)), celda(e.tipo), celda(e.video_id), chip(e.resultado),
    celda(e.detalle), celda(fmt(Number(e.creditos_usados) || 0), 'n'), celda(fmt(Number(e.creditos_restantes) || 0), 'n'))));
}

// ---------- navegación y efectos ----------
function armarNavegacion() {
  // Una pastilla por sección, tomada de la propia página; marca en cuál vas.
  // solo las visibles: la vista esencial oculta lo .extra (12-nov-2026)
  const secciones = [...document.querySelectorAll('main .seccion')].filter((s) => getComputedStyle(s).display !== 'none');
  const nav = $('navegacion');
  const botones = secciones.map((sec, i) => {
    sec.id ||= `seccion-${i + 1}`;
    const nombre = [...sec.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join('').trim();
    return crear('a', {href: `#${sec.id}`, textContent: nombre, className: 'pastilla'});
  });
  nav.replaceChildren(...botones);
  const activo = new IntersectionObserver((entradas) => {
    for (const e of entradas) {
      if (!e.isIntersecting) continue;
      const i = secciones.indexOf(e.target);
      botones.forEach((b, j) => b.classList.toggle('activa', j === i));
      botones[i]?.scrollIntoView({block: 'nearest', inline: 'center'});
    }
  }, {rootMargin: '-20% 0px -70% 0px'});
  secciones.forEach((s) => activo.observe(s));
}

function avatar3d() {
  // El avatar se inclina con el mouse (solo con mouse y si el sistema no pide menos movimiento).
  const heroe = document.querySelector('.heroe');
  const avatar = document.querySelector('.heroe .avatar');
  if (!heroe || !avatar || !matchMedia('(pointer: fine)').matches || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  heroe.addEventListener('pointermove', (e) => {
    const r = heroe.getBoundingClientRect();
    avatar.style.setProperty('--rx', `${((e.clientY - r.top) / r.height - 0.5) * -14}deg`);
    avatar.style.setProperty('--ry', `${((e.clientX - r.left) / r.width - 0.5) * 18}deg`);
  });
  heroe.addEventListener('pointerleave', () => { avatar.style.setProperty('--rx', '0deg'); avatar.style.setProperty('--ry', '0deg'); });
}

// ---------- centro de operaciones (todo con datos reales) ----------
const METAS = [1000, 10000, 100000, 1000000];
const NOTA_META = {tt: {1000: 'enlace en la bio', 10000: 'empieza a pagar'}, ig: {10000: 'marcas'}, yt: {1000: 'empieza a pagar'}};
const SVG = 'http://www.w3.org/2000/svg';
const svgEl = (etiqueta, attrs = {}, ...hijos) => { const el = document.createElementNS(SVG, etiqueta); for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v); el.append(...hijos); return el; };

function seguidoresReales(clave) {
  return clave === 'yt' ? VIVO?.canal?.suscriptores : VIVO?.seguidores?.[clave]?.seguidores;
}

function dibujarMetas() {
  $('metas').replaceChildren(...REDES.map((red) => {
    const n = seguidoresReales(red.clave);
    const meta = METAS.find((m) => (n ?? 0) < m) || METAS.at(-1);
    const previa = METAS[METAS.indexOf(meta) - 1] || 0;
    const avance = n == null ? 0 : Math.max(0, Math.min(1, (n - previa) / (meta - previa)));
    const largo = 2 * Math.PI * 46;
    const svg = svgEl('svg', {viewBox: '0 0 120 120', 'aria-hidden': 'true'},
      svgEl('circle', {cx: 60, cy: 60, r: 54, class: 'marcas'}),
      svgEl('circle', {cx: 60, cy: 60, r: 46, class: 'pista'}),
      svgEl('circle', {cx: 60, cy: 60, r: 46, class: 'avance', stroke: red.color, color: red.color,
        'stroke-dasharray': `${largo * avance} ${largo}`, transform: 'rotate(-90 60 60)'}));
    const nota = NOTA_META[red.clave]?.[meta];
    return crear('div', {className: 'meta'}, svg,
      crear('div', {className: 'nucleo'}, crear('b', {textContent: n == null ? '—' : compacto(n)}), crear('small', {textContent: `${Math.round(avance * 100)}%`})),
      crear('span', {className: 'rotulo', textContent: red.nombre}),
      crear('span', {className: 'detalle', textContent: n == null ? 'conectando…' : `meta ${compacto(meta)}${nota ? ` · ${nota}` : ''}`}));
  }));
}

function dibujarAudiencia() {
  // Solo lo que manda Instagram; si no manda nada, se dice por qué (nunca se rellena).
  const a = VIVO?.seguidores?.audiencia;
  const caja = $('audiencia');
  const filas = (lista) => lista.map(([nombre, valor]) => ({nombre: String(nombre), valor: Number(valor) || 0})).filter((f) => f.valor > 0).sort((x, y) => y.valor - x.valor).slice(0, 8);
  const paises = filas(Array.isArray(a?.paises) ? a.paises.map((p) => [p.country || p.name || p.label || p.key, p.value ?? p.count ?? p.percentage]) : Object.entries(a?.paises || {}));
  const edades = filas(Object.entries(Array.isArray(a?.edades) ? {} : a?.edades || {}));
  if (!paises.length && !edades.length) {
    const ig = VIVO?.seguidores?.ig?.seguidores;
    caja.replaceChildren(crear('p', {className: 'vacio', textContent: a === undefined || !VIVO
      ? 'Conectando con Publer…'
      : `Instagram todavía no manda países ni edades: los da a partir de 100 seguidores${ig != null ? ` (hoy ${fmt(ig)})` : ''}. Aparecen aquí solos cuando lleguen.`}));
    return;
  }
  const bloque = (titulo, lista) => {
    const tope = Math.max(...lista.map((f) => f.valor));
    return crear('div', {className: 'atributo'}, crear('h3', {textContent: titulo}), ...lista.map((f) => {
      const barra = crear('div', {className: 'barra-ind'});
      const relleno = crear('i');
      relleno.style.width = `${(f.valor / tope) * 100}%`;
      barra.append(relleno);
      return crear('div', {className: 'fila'}, crear('span', {textContent: f.nombre}), barra, crear('em', {textContent: fmt(f.valor)}));
    }));
  };
  caja.replaceChildren(...(paises.length ? [bloque('Países', paises)] : []), ...(edades.length ? [bloque('Edades', edades)] : []));
}

const NOMBRE_ORIGEN = {yt: 'YouTube', tt: 'TikTok', ig: 'Instagram', guia: 'Guía gratis', directo: 'Directo a la página', otro: 'Otro enlace', sin_origen: 'Sin origen'};
const COLOR_ORIGEN = {yt: '#ff3b55', tt: '#facc15', ig: '#a855f7', guia: '#49d6ec', directo: '#7f97a8', otro: '#7f97a8', sin_origen: '#34495a'};

// Una conexión que solo Rodrigo puede hacer (las claves viven en Vercel, nunca en el chat ni en el repo): qué falta y
// un botón directo a la página donde se agregan (11-nov-2026: antes era una frase sin camino).
const VARIABLES_VERCEL = 'https://vercel.com/rodrigos-eurotrip/victoria-centro/settings/environment-variables';
function pendiente(texto, nombres, deDonde) {
  return crear('div', {className: 'pendiente'},
    crear('p', {className: 'vacio', textContent: texto}),
    crear('ol', {className: 'pasos'},
      crear('li', {textContent: 'Toca el botón: abre las variables del proyecto victoria-centro en Vercel.'}),
      crear('li', {}, 'Agrega ', ...nombres.flatMap((n, i) => [i ? (i === nombres.length - 1 ? ' y ' : ', ') : '', crear('code', {textContent: n})]), `. ${deDonde}`),
      crear('li', {textContent: 'En Deployments, el último → Redeploy. Listo: se conecta solo.'})),
    crear('a', {className: 'boton', href: VARIABLES_VERCEL, target: '_blank', rel: 'noopener', textContent: 'Abrir variables en Vercel'}));
}

function dibujarConexiones() {
  const caja = $('conexiones');
  if (!caja) return;
  const c = VIVO?.conexiones;
  caja.hidden = !c || c.meta;
  if (caja.hidden) return;
  caja.replaceChildren(crear('div', {className: 'codigo', textContent: 'CNX-01 · TE TOCA A TI'}), crear('h2', {textContent: 'GUÍA al instante'}),
    pendiente('Hoy Victoria contesta "GUÍA" en Instagram cada hora. Conectando Meta lo contesta en segundos, cuando la persona todavía está viendo el post.',
      ['META_TOKEN', 'META_APP_SECRET', 'META_VERIFY_TOKEN'].filter((n) => !c.faltan || c.faltan.includes(n)), 'Si no sabes de dónde sacarlas en Meta, pídele los pasos a Claude (botón de arriba).'));
}

function dibujarVentas() {
  // Solo ventas reales de Hotmart. Si no está conectado o falla, se dice tal cual.
  const v = VIVO?.ventas;
  const caja = $('ventas');
  if (!VIVO) { caja.replaceChildren(crear('p', {className: 'vacio', textContent: 'Conectando con Hotmart…'})); return; }
  if (!v || v.conectado === false) {
    caja.replaceChildren(pendiente('Hotmart sin conectar: aquí salen las ventas de El Tablero de la CEO, por red, en cuanto lo conectes.',
      ['HOTMART_CLIENT_ID', 'HOTMART_CLIENT_SECRET'], 'Las dos salen de Hotmart → Herramientas → Credenciales.'));
    return;
  }
  if (v.error) { caja.replaceChildren(crear('p', {className: 'vacio', textContent: `Hotmart no respondió: ${v.error}`})); return; }
  const dinero = (n) => `$${Math.round(n).toLocaleString('es-MX')}${v.moneda ? ` ${v.moneda}` : ''}`;
  const filas = Object.entries(v.porRed || {}).sort((a, b) => b[1].ingresos - a[1].ingresos);
  const tope = Math.max(1, ...filas.map(([, x]) => x.ingresos));
  caja.replaceChildren(
    crear('div', {className: 'ventas-cifras'},
      crear('div', {}, crear('b', {textContent: fmt(v.ventas)}), crear('small', {textContent: v.ventas === 1 ? 'venta' : 'ventas'})),
      crear('div', {}, crear('b', {textContent: dinero(v.ingresos)}), crear('small', {textContent: 'cobrado'}))),
    filas.length ? crear('div', {className: 'atributo'}, ...filas.map(([red, x]) => {
      const barra = crear('div', {className: 'barra-ind'});
      const relleno = crear('i');
      relleno.style.width = `${(x.ingresos / tope) * 100}%`;
      relleno.style.background = COLOR_ORIGEN[red] || '#7f97a8';
      barra.append(relleno);
      return crear('div', {className: 'fila'}, crear('span', {textContent: NOMBRE_ORIGEN[red] || red}), barra, crear('em', {textContent: `${fmt(x.ventas)} · ${dinero(x.ingresos)}`}));
    })) : crear('p', {className: 'vacio', textContent: 'Todavía no hay ventas aprobadas en los últimos 90 días. Aparecen aquí solas en cuanto llegue la primera.'}),
    ...(v.otros ? [crear('p', {className: 'nota', textContent: `No cuentan aquí ${fmt(v.otros)} ${v.otros === 1 ? 'venta' : 'ventas'} de tus otros productos de Hotmart; este panel es solo de Victoria.`})] : []),
    ...(v.ultimas?.length ? [crear('ol', {className: 'lista'}, ...v.ultimas.map((u) => elemento('dato', NOMBRE_ORIGEN[u.red] || u.red, dinero(u.valor), u.fecha ? mx(new Date(u.fecha).toISOString()) : '')))] : []));
}

// Lo que la rutina de las 6:37 va a programar hoy, según la auditoría de la madrugada (11-nov-2026: antes de la rutina
// TikTok e Instagram decían "—" y YouTube enseñaba el video largo de mañana aunque O1 salía hoy a las 10:00).
// Solo cuenta si la auditoría es de hoy y la rutina de hoy todavía no corre; ya programado, manda lo real.
function planDeHoy(clave) {
  const a = FOTO.auditoria || {}, d = a.decision || {};
  const dia = (iso) => (iso ? new Date(iso).toLocaleDateString('en-CA', {timeZone: 'America/Mexico_City'}) : '');
  if (dia(a.fecha_utc) !== hoyMx() || (FOTO.ejecuciones || []).some((e) => dia(e.fecha_utc) === hoyMx())) return [];
  const c = d.carruseles || {}, xs = [];
  if (d.toca_publicar && d.publicar_hoy && d.cuando?.[clave]) xs.push({t: Date.parse(d.cuando[clave]), id: d.publicar_hoy});
  if (clave === 'tt') for (const x of c.tiktoks || (c.tiktok ? [c.tiktok] : [])) xs.push({t: Date.parse(x.cuando), id: x.id});
  if (clave === 'ig' && c.instagram?.cuando_ig) xs.push({t: Date.parse(c.instagram.cuando_ig), id: c.instagram.id});
  if (clave === 'yt' && c.youtube?.cuando_yt) xs.push({t: Date.parse(c.youtube.cuando_yt), id: c.youtube.id});
  return xs.filter((x) => x.t > Date.now()).map((x) => ({t: x.t, plan: true, p: {id: x.id}}));
}

// "hoy 10:00 a.m.", "mañana 9:00 a.m." o "vie 13 nov, 9:00 a.m.": corto para que el título quepa en la tarjeta.
function cuandoCorto(t) {
  const iso = new Date(t).toISOString();
  const dia = new Date(t).toLocaleDateString('en-CA', {timeZone: 'America/Mexico_City'});
  const manana = new Date(Date.parse(`${hoyMx()}T12:00:00`) + 86400000).toISOString().slice(0, 10);
  const hora = mx(iso, {hour: 'numeric', minute: '2-digit'});
  return dia === hoyMx() ? `hoy ${hora}` : dia === manana ? `mañana ${hora}` : mx(iso, {weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit'});
}

function siguientePorRed(clave) {
  const temprano = (lista) => lista.filter(Boolean).sort((a, b) => a.t - b.t)[0] || null;
  if (AGENDA) {  // en vivo de Publer y YouTube
    const prox = AGENDA.find((x) => x.red === clave && !x.publicado && x.t > Date.now());
    return temprano([prox && {t: prox.t, p: {id: prox.id, texto: prox.texto}}, ...planDeHoy(clave)]);
  }
  let mejor = temprano(planDeHoy(clave));
  for (const p of todo()) {
    if (p.estado !== 'programado') continue;
    const t = new Date((p.publica_utc_por_red || {})[clave] || p.publica_utc || 0).getTime();
    if (t > Date.now() && (!mejor || t < mejor.t)) mejor = {t, p};
  }
  return mejor;
}

function dibujarDespegues() {
  $('despegues').replaceChildren(...REDES.map((red) => {
    const sig = siguientePorRed(red.clave);
    const cuenta = crear('b', {className: 'cuenta-red', textContent: '—'});
    if (sig) cuenta.dataset.t = String(sig.t);
    const fila = crear('div', {className: 'despegue'}, crear('span', {className: 'red-nombre', textContent: red.nombre}), cuenta,
      crear('small', {textContent: sig ? `${cuandoCorto(sig.t)}${sig.plan ? ' (plan)' : ''} · ${sig.p.id ? titulo(sig.p.id, 48) : `«${recortar(sig.p.texto, 48)}»`}` : (() => {
        // La rutina programa a las 6:37 (hora de México): antes de esa hora es "hoy a las 6:37"; después, "mañana" (11-nov-2026).
        const [h, m] = new Date().toLocaleTimeString('en-GB', {timeZone: 'America/Mexico_City', hour: '2-digit', minute: '2-digit'}).split(':').map(Number);
        return `La rutina lo programa ${h * 60 + m < 6 * 60 + 37 ? 'hoy' : 'mañana'} a las 6:37`;
      })()}));
    fila.style.setProperty('--acento', red.color);
    return fila;
  }));
  tictac();
}

function tictac() {
  for (const el of document.querySelectorAll('.cuenta-red[data-t]')) {
    let s = Math.max(0, Math.floor((Number(el.dataset.t) - Date.now()) / 1000));
    const d = Math.floor(s / 86400), h = Math.floor((s %= 86400) / 3600), m = Math.floor((s %= 3600) / 60);
    el.textContent = `${d ? `${d}d ` : ''}${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  }
}

function horasEnVivo(f) {
  // La hora real de cada red (Publer y YouTube en vivo) manda sobre la de la última foto: si algo se movió o salió
  // antes, el calendario lo enseña al minuto. "✓" = ya salió.
  const horas = {...f.horas};
  for (const x of AGENDA || []) {
    const fecha = new Date(x.t).toLocaleDateString('en-CA', {timeZone: 'America/Mexico_City'});
    if (!x.id || x.id !== f.id || fecha !== f.fecha) continue;
    horas[x.red] = new Date(x.t).toLocaleTimeString('es-MX', {timeZone: 'America/Mexico_City', hour: '2-digit', minute: '2-digit', hour12: false})
      + (x.publicado ? ' ✓' : '');
  }
  return horas;
}

function dibujarCalendario(filas = []) {
  const hoy = new Date().toLocaleDateString('en-CA', {timeZone: 'America/Mexico_City'});
  $('t-calendario').replaceChildren(...filas.map((f) => {
    const horas = horasEnVivo(f);
    const vivo = [...(FOTO.carruseles || []), ...FOTO.videos].find((x) => x.id === f.id);
    const vistas = vivo && salio(vivo) && medido(vivo) ? fmt(vistasDe(vivo)) : '';
    return crear('tr', {className: f.fecha === hoy ? 'hoy' : ''},
      celda(new Date(`${f.fecha}T12:00:00`).toLocaleDateString('es-MX', {weekday: 'short', day: 'numeric', month: 'short'})),
      celda({carrusel: 'Carrusel', reel: 'Reel IG', facebook: 'Facebook', largo: 'Video largo'}[f.tipo] || 'Video'), celda(f.que),
      celda(horas.ig || '—', 'n'), celda(horas.tt || '—', 'n'), celda(horas.yt || '—', 'n'), celda(horas.fb || '—', 'n'), chip(f.estado), celda(vistas, 'n'));
  }));
}

function dibujarHorarios(a, estado) {
  const d = a.decision || {};
  const datos = a.horarios_por_red || {};
  const minimo = estado.prueba_horas?.min_por_franja || 4;
  $('horarios-red').replaceChildren(...['ig', 'tt', 'yt'].map((r) => {
    const info = datos[r] || {franjas: {}, dias: {}};
    const conteo = (d.conteo_horas || {})[r] || {};
    const franjas = estado.prueba_horas?.franjas_por_red?.[r] || estado.prueba_horas?.franjas || Object.keys(conteo);
    const filas = franjas.map((f) => {
      const x = (info.franjas || {})[f];
      return crear('tr', {className: info.ganadora === f ? 'gana' : ''}, celda(f), celda(`${conteo[f] ?? 0}/${minimo}`, 'n'), celda(x ? `${x.indice.toFixed(2)} (${x.n})` : '—', 'n'));
    });
    const dias = Object.entries(info.dias || {}).sort((p, q) => q[1].indice - p[1].indice).map(([dia, x]) => `${dia} ${x.indice.toFixed(2)}`).join(' · ');
    return crear('div', {className: 'red-horas'},
      crear('h3', {textContent: `${NOMBRE_RED[r]} · ${info.ganadora ? `gana ${info.ganadora}` : 'en prueba'}`}),
      crear('table', {}, crear('thead', {}, crear('tr', {}, crear('th', {textContent: 'Hora'}), crear('th', {className: 'n', textContent: 'Publicadas'}), crear('th', {className: 'n', textContent: 'Índice'}))), crear('tbody', {}, ...filas)),
      crear('p', {className: 'nota', textContent: `${d.horarios?.[r] ? `Hoy toca ${d.horarios[r]}. ` : ''}${dias ? `Mejor día: ${dias}` : 'Los días se comparan cuando haya publicaciones medidas.'}`}));
  }));
}

function dibujarCarruseles(lista = []) {
  // Lo que viene primero (en el orden de la rutina), luego lo más reciente (11-nov-2026: abría con c01 de octubre, el tema
  // salía sin acentos y el gancho largo hacía filas altísimas en el celular).
  const prio = FOTO.estado.prioridad_carruseles || [];
  const rango = (c) => (!salio(c) && ['listo', 'programado'].includes(c.estado) ? 0 : salio(c) ? 1 : 2);
  const lugar = (c) => (prio.includes(c.id) ? prio.indexOf(c.id) : prio.length);
  const ultimo = (c) => Object.values(c.horas || {}).sort().pop() || '';
  const orden = [...lista].sort((a, b) => rango(a) - rango(b) || (rango(a) === 0 ? lugar(a) - lugar(b) : ultimo(b).localeCompare(ultimo(a))));
  const nombres = {tt: 'TT', ig: 'IG', yt: 'YT', fb: 'FB'};
  $('t-carruseles').replaceChildren(...orden.map((c) => {
    const horas = Object.entries(c.horas || {}).sort((p, q) => p[1].localeCompare(q[1]))
      .map(([r, h]) => `${nombres[r] || r} ${fechaCorta(h)} ${h.slice(11, 16)}`).join(' · ');
    const m = medidas(c);
    const red = (clave) => celda(salio(c) && m[clave] ? fmt(m[clave].v) : '', 'n');
    return crear('tr', {}, celda(c.id), chip(c.estado), celda(c.titulo || String(c.tema || '').replace(/_/g, ' ')), celda(horas || '—'),
      red('ig'), red('tt'), red('yt'), red('fb'), celda(salio(c) && medido(c) ? fmt(vistasDe(c)) : '', 'n'));
  }));
}

// ---------- gráficas ----------
function globo(caja) {
  const g = crear('div', {className: 'globo', hidden: true});
  caja.append(g);
  return {
    ver(e, titulo, valor) {
      g.replaceChildren(crear('span', {textContent: `${titulo}  `}), valor);
      g.hidden = false;
      const r = caja.getBoundingClientRect();
      g.style.left = `${Math.min(Math.max(e.clientX - r.left + 12, 0), Math.max(r.width - g.offsetWidth, 0))}px`;
      g.style.top = `${Math.max(e.clientY - r.top - 36, 0)}px`;
    },
    ocultar() { g.hidden = true; },
  };
}

// Replicate (12-nov-2026): videos de Victoria y su voz. No hay saldo por API: es el saldo que Rodrigo leyó en su cuenta
// menos lo gastado desde entonces (scripts/replicate_gasto.py), separado en Victoria y el otro canal que usa la cuenta.
function pintarReplicate() {
  const rep = FOTO?.estado?.replicate;
  if (!$('rep-saldo')) return;
  const usd = (n) => (n == null ? '—' : `$${Number(n).toFixed(2)}`);
  $('rep-saldo').textContent = usd(rep?.saldo_estimado_usd);
  $('rep-saldo').style.color = rep?.saldo_estimado_usd != null && rep.saldo_estimado_usd < 5 ? ROJO : '';
  $('rep-victoria').textContent = usd(rep?.gastado_7_dias?.victoria);
  $('rep-otro').textContent = usd(rep?.gastado_7_dias?.otro);
  if (rep) {
    const base = `Saldo base ${usd(rep.saldo_base_usd)} (${String(rep.fecha_base_utc).slice(0, 10)}) menos lo gastado desde entonces.`;
    const toma = rep.costo_promedio_toma_usd != null ? ` Cada toma de Victoria a cámara: ~${usd(rep.costo_promedio_toma_usd)}.` : '';
    const falta = rep.incompleto ? ` Hay modelos sin precio conocido (${Object.keys(rep.sin_precio || {}).join(', ')}): el saldo puede ser menor.` : '';
    $('rep-nota').textContent = base + toma + falta;
  }
  if (window.d3 && $('g-replicate')) barras($('g-replicate'), (rep?.por_dia || []).map((d) => ({k: d.dia.slice(5), v: d.victoria + d.otro})), {color: ORO, formato: usd});
}

// Vistas POR PUBLICACIÓN y POR RED, con lo ganado en las últimas 24 h (Rodrigo, 12-nov-2026: "las vistas son totales,
// no por día ni por video ni por red"). Datos de la medición diaria (estado.publicaciones); se ordena tocando la columna.
let ORDEN_PUB = 'total', VER_TODAS_PUB = false;
function dibujarPublicaciones() {
  const cuerpo = $('t-publicaciones');
  if (!cuerpo) return;
  const lista = [...(FOTO.estado?.publicaciones || [])];
  const valor = (x) => (ORDEN_PUB === 'total' ? x.total : ORDEN_PUB === '24h' ? (x.ultimas_24h ? Object.values(x.ultimas_24h).reduce((a, b) => a + b, 0) : -1)
    : ORDEN_PUB === 'dia' ? x.por_dia : x.por_red[ORDEN_PUB] ?? -1);
  lista.sort((a, b) => valor(b) - valor(a));
  const mejor = Object.fromEntries(['tt', 'ig', 'yt', 'fb'].map((r) => [r, Math.max(0, ...lista.map((x) => x.por_red[r] || 0))]));
  const visibles = VER_TODAS_PUB ? lista : lista.slice(0, 10);
  cuerpo.replaceChildren(...visibles.map((x) => {
    const d24 = x.ultimas_24h ? Object.values(x.ultimas_24h).reduce((a, b) => a + b, 0) : null;
    const celda = (r) => {
      const v = x.por_red[r];
      const td = crear('td', {className: 'n', textContent: v == null ? '·' : compacto(v)});
      if (v && v === mejor[r]) td.style.color = ORO;
      const g = x.ultimas_24h?.[r];
      if (g) td.append(crear('small', {textContent: ` +${compacto(g)}`, style: 'color:#3ddc84;display:block'}));
      return td;
    };
    return crear('tr', {},
      crear('td', {}, crear('small', {className: 'nota', textContent: `${x.tipo} ${x.id} · `}), crear('span', {textContent: x.titulo})),
      celda('tt'), celda('ig'), celda('yt'), celda('fb'),
      crear('td', {className: 'n', textContent: compacto(x.total), style: 'font-weight:700'}),
      crear('td', {className: 'n', textContent: d24 == null ? '—' : `+${compacto(d24)}`, style: d24 ? 'color:#3ddc84' : ''}),
      crear('td', {className: 'n', textContent: compacto(x.por_dia)}));
  }));
  if (lista.length > 10) {
    const boton = crear('button', {type: 'button', className: 'resp-copiar', textContent: VER_TODAS_PUB ? 'Ver solo las 10 primeras' : `Ver las ${lista.length}`});
    boton.onclick = () => { VER_TODAS_PUB = !VER_TODAS_PUB; dibujarPublicaciones(); };
    cuerpo.append(crear('tr', {}, crear('td', {colSpan: 8, style: 'text-align:center'}, boton)));
  }
  const hora = FOTO.estado?.publicaciones?.[0]?.medido_utc;
  if ($('pub-nota') && hora) $('pub-nota').textContent = `Medido ${mx(hora)}. En verde: lo que ganó en las últimas 24 h. En dorado: la mejor de cada red. Toca una columna para ordenar.`;
}
document.addEventListener('click', (e) => {
  const th = e.target.closest('th[data-orden]');
  if (!th) return;
  ORDEN_PUB = th.dataset.orden;
  dibujarPublicaciones();
});

// Salud del sistema (12-nov-2026, Rodrigo: "déjame todo fluyendo, sin errores"): scripts/salud.py en la rutina diaria.
// Llaves, saldo de Replicate, huecos del calendario, largos y recortes pendientes. Alertas primero.
function dibujarSalud(salud) {
  const caja = $('salud');
  if (!caja) return;
  const checks = salud?.checks || [];
  if (!checks.length) { caja.replaceChildren(crear('p', {className: 'nota', textContent: 'Todavía no hay chequeo de salud: lo corre la rutina diaria.'})); return; }
  const color = {ok: '#3ddc84', aviso: ORO, alerta: ROJO};
  const nombre = {ok: 'Todo fluye', aviso: 'Atender hoy', alerta: 'Algo se cae'};
  const orden = (c) => ['alerta', 'aviso', 'ok'].indexOf(c.estado);
  const fila = (c) => crear('li', {style: 'margin:6px 0;list-style:none'},
    crear('span', {textContent: '● ', style: `color:${color[c.estado]}`}),
    crear('b', {textContent: `${c.area}: `}), crear('span', {textContent: c.detalle}));
  // Lo que falla, a la vista; lo que está bien, plegado (el panel debe ser corto).
  // El gasto siempre a la vista (12-nov-2026, Rodrigo: "control para no sorprenderme con el gasto").
  const malos = [...checks].filter((c) => c.estado !== 'ok' || c.area === 'Gasto').sort((a, b) => orden(a) - orden(b));
  const buenos = checks.filter((c) => c.estado === 'ok' && c.area !== 'Gasto');
  const filas = [...malos.map(fila)];
  if (buenos.length) filas.push(crear('li', {style: 'list-style:none;margin-top:8px'}, crear('details', {},
    crear('summary', {textContent: `✓ ${buenos.length} cosas en orden (toca para ver)`, style: 'cursor:pointer;color:#3ddc84'}),
    crear('ul', {style: 'padding:0;margin:6px 0 0'}, ...buenos.map(fila)))));
  caja.replaceChildren(crear('article', {className: 'panel', style: 'grid-column:1/-1'},
    crear('div', {className: 'codigo', textContent: 'SYS-00'}),
    crear('h2', {textContent: nombre[salud.estado] || 'Salud', style: `color:${color[salud.estado] || ''}`}),
    crear('p', {className: 'nota', textContent: `Último chequeo: ${mx(salud.generado_utc)}`}),
    crear('ul', {style: 'padding:0;margin:0'}, ...filas)));
}

// Videos largos de YouTube (12-nov-2026, Rodrigo: "quiero TODO en el dashboard"): miniaturas A y B, estado, cuándo sale,
// duración, capítulos y enlace.
function dibujarLargos(lista = []) {
  const caja = $('largos');
  if (!caja) return;
  if (!lista.length) { caja.replaceChildren(crear('p', {className: 'nota', textContent: 'Todavía no hay videos largos.'})); return; }
  caja.replaceChildren(...lista.map((l) => {
    const cuando = l.publica_utc ? new Date(l.publica_utc).toLocaleString('es-MX', {timeZone: 'America/Mexico_City', weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'}) : 'sin fecha';
    const minis = (l.miniaturas || []).map((src, i) => crear('figure', {className: 'mini-largo'},
      crear('img', {src, alt: `Miniatura ${i ? 'B' : 'A'} de ${l.titulo}`, loading: 'lazy', style: 'width:100%;border-radius:10px;display:block'}),
      crear('figcaption', {className: 'nota', textContent: i ? 'Miniatura B (para comparar en YouTube Studio)' : 'Miniatura A (la que se sube)'})));
    const datos = [
      `Sale: ${cuando} (YouTube)`,
      l.duracion_min ? `Duración: ${l.duracion_min} min` : `En producción: ${l.segmentos} partes, ${l.tomas_victoria} de Victoria a cámara`,
      l.capitulos?.length ? `${l.capitulos.length} capítulos` : '',
    ].filter(Boolean);
    return crear('article', {className: 'panel'},
      crear('div', {className: 'codigo', textContent: l.id}),
      crear('h2', {textContent: l.titulo}),
      crear('p', {}, crear('span', {className: `chip ${(ESTADOS[l.estado] || [])[1] || ''}`, textContent: (ESTADOS[l.estado] || [l.estado])[0]})),
      ...minis,
      ...datos.map((t) => crear('p', {className: 'nota', textContent: t})),
      ...(l.capitulos?.length ? [crear('details', {}, crear('summary', {textContent: 'Capítulos'}), ...l.capitulos.map((c) => crear('p', {className: 'nota', textContent: c})))] : []),
      ...(l.youtube ? [crear('p', {}, crear('a', {href: l.youtube, target: '_blank', rel: 'noopener', textContent: 'Ver en YouTube →'}))] : []));
  }));
}

function dibujarGraficas() {
  if (!window.d3 || !FOTO) return;
  const r = resumen();
  reactor($('g-reactor'), r);
  const ej = [...FOTO.ejecuciones].sort(porFecha).map((e, i) => ({...e, n: e.video_id ? `v${e.video_id}` : `#${i + 1}`}));
  saldo($('g-saldo'), ej, r);
  barras($('g-gasto'), ej.map((e) => ({k: e.n, v: Number(e.creditos_usados) || 0})), {color: ORO});
  barras($('g-calidad'), FOTO.videos.filter((v) => Number(v.qa_similitud) > 0).map((v) => ({k: `v${v.id}`, v: Number(v.qa_similitud)})), {color: CIAN, formato: pct, linea: FOTO.estado.similitud_minima});
  const medidos = todo().filter(medido);
  $('vacio-vistas').hidden = medidos.length > 0;
  apiladas($('g-vistas'), medidos);
  calor($('g-calor'), FOTO.mejores_horas);
  dibujarMejora();
  // Tema y día: promedio de vistas POR RED (una barra por red, lado a lado), con videos y carruseles (Rodrigo, 9-nov-2026:
  // "¿no debería ser en la misma gráfica por red social?"). Antes sumaba las redes y solo contaba los videos de Victoria.
  for (const [campo, id, vacio, nombres, orden] of [['pilar', 'g-pilar', 'vacio-pilar', PILARES, null], ['dia', 'g-dia', 'vacio-dia', {}, DIAS]]) {
    const grupos = promedioPorRed(campo);
    if (orden) grupos.sort((a, b) => orden.indexOf(a.grupo) - orden.indexOf(b.grupo));
    $(vacio).hidden = grupos.length > 0;
    agrupadas($(id), grupos.map((g) => ({...g, k: nombres[g.grupo] || g.grupo})));
  }
  for (const caja of document.querySelectorAll('.leyenda-redes')) {
    caja.replaceChildren(...REDES.map((r) => crear('span', {}, Object.assign(crear('i'), {style: `background:${r.color}`}), r.nombre)));
  }
}

const DIA_EN = {Mon: 'lun', Tue: 'mar', Wed: 'mié', Thu: 'jue', Fri: 'vie', Sat: 'sáb', Sun: 'dom'};
function diaEnRed(x, clave) {
  // El día (México) en que salió en esa red: su hora propia por red, el Reel de Instagram del carrusel, o la general.
  let t = x.publica_utc_por_red?.[clave] || x.publica_utc;
  if (clave === 'ig' && x.reel_ig) t = `${x.reel_ig.replace(' ', 'T')}:00-06:00`;
  if (!t) return null;
  return DIA_EN[new Date(t).toLocaleString('en-US', {timeZone: 'America/Mexico_City', weekday: 'short'})] || null;
}

function promedioPorRed(campo) {
  const g = new Map();
  for (const x of todo().filter(salio)) {
    const m = medidas(x);
    for (const {clave} of REDES) {
      const v = Number(m[clave]?.v);
      if (!m[clave] || m[clave].pendiente || !Number.isFinite(v)) continue;
      const hora = x.publica_utc_por_red?.[clave];
      if (hora && new Date(hora).getTime() > Date.now()) continue;  // programado en esa red: su 0 no cuenta
      const grupo = campo === 'dia' ? diaEnRed(x, clave) : (x[campo] || 'finanzas');
      if (!grupo) continue;
      const fila = g.get(grupo) || {grupo, suma: {}, n: {}};
      fila.suma[clave] = (fila.suma[clave] || 0) + v;
      fila.n[clave] = (fila.n[clave] || 0) + 1;
      g.set(grupo, fila);
    }
  }
  return [...g.values()].map((f) => ({grupo: f.grupo, n: f.n,
    valores: Object.fromEntries(Object.keys(f.suma).map((c) => [c, f.suma[c] / f.n[c]]))}));
}

function agrupadas(caja, grupos, alto = 190) {
  if (!grupos.length) { caja.replaceChildren(); return; }
  const {ancho, svg} = lienzo(caja, alto);
  const tip = globo(caja);
  const m = {t: 18, r: 6, b: 28, l: 6};
  const claves = REDES.map((r) => r.clave);
  const x0 = d3.scaleBand(grupos.map((d, i) => i), [m.l, ancho - m.r]).padding(0.22);
  const x1 = d3.scaleBand(claves, [0, x0.bandwidth()]).padding(0.12);
  const maximo = d3.max(grupos, (d) => d3.max(claves, (c) => d.valores[c] || 0)) || 1;
  const y = d3.scaleLinear([0, maximo], [alto - m.b, m.t]).nice();
  svg.append('g').attr('class', 'guia').selectAll('line').data(y.ticks(4)).join('line').attr('x1', m.l).attr('x2', ancho - m.r).attr('y1', y).attr('y2', y);
  grupos.forEach((d, i) => {
    const g = svg.append('g').attr('transform', `translate(${x0(i)},0)`);
    for (const red of REDES) {
      const v = d.valores[red.clave];
      if (v == null) continue;
      g.append('rect').attr('x', x1(red.clave)).attr('width', x1.bandwidth()).attr('y', y(v)).attr('height', y(0) - y(v))
        .attr('fill', red.color).attr('fill-opacity', 0.85)
        .on('pointermove', (e) => tip.ver(e, `${d.k} · ${red.nombre}`, `${compacto(v)} vistas promedio (${d.n[red.clave]} publicaciones)`))
        .on('pointerleave', () => tip.ocultar());
      if (x1.bandwidth() >= 16) g.append('text').attr('text-anchor', 'middle').attr('x', x1(red.clave) + x1.bandwidth() / 2).attr('y', y(v) - 4)
        .style('fill', '#e9f6fb').style('font-size', '9px').text(compacto(v));
    }
  });
  eje(svg, x0, alto, m, grupos.map((d) => d.k));
}

// ---------- mejora día a día (Rodrigo, 9-nov-2026: "el chiste es mejorar día a día") ----------
function diarioPorRed() {
  // De vistas acumuladas por día (la medición de cada mañana) a vistas NUEVAS de cada día, por red.
  const serie = FOTO.estado?.serie_redes || [];
  return serie.map((d, i) => {
    const fila = {fecha: d.fecha};
    for (const {clave} of REDES) {
      if (d[clave] == null) continue;
      const antes = i ? serie[i - 1][clave] ?? 0 : 0;
      fila[clave] = Math.max(0, d[clave] - antes);
    }
    return fila;
  });
}

function sumaDias(diario, clave, desde, hasta) {
  const filas = diario.filter((d) => d.fecha > desde && d.fecha <= hasta && d[clave] != null);
  return filas.length ? {total: filas.reduce((s, d) => s + d[clave], 0), dias: filas.length} : null;
}

const diasAntes = (fecha, n) => new Date(new Date(`${fecha}T12:00:00Z`).getTime() - n * 864e5).toISOString().slice(0, 10);

function dibujarMejora() {
  const diario = diarioPorRed();
  if (!diario.length) return;
  const hoy = diario.at(-1).fecha;
  $('mejora-semana').replaceChildren(...REDES.map((red) => {
    const ahora = sumaDias(diario, red.clave, diasAntes(hoy, 7), hoy);
    const antes = sumaDias(diario, red.clave, diasAntes(hoy, 14), diasAntes(hoy, 7));
    let flecha = 'midiendo', clase = '';
    if (ahora && antes && antes.dias >= 3 && antes.total > 0) {
      const cambio = (ahora.total - antes.total) / antes.total;
      flecha = `${cambio >= 0 ? '▲' : '▼'} ${Math.abs(Math.round(cambio * 100))}%`;
      clase = cambio >= 0 ? 'sube' : 'baja';
    }
    const caja = crear('div', {className: 'kpi-mejora'}, crear('span', {className: 'red-nombre', textContent: red.nombre}),
      crear('b', {textContent: ahora ? compacto(ahora.total) : '—'}), crear('small', {className: clase, textContent: !ahora ? 'empieza a medirse con su primer post'
        : flecha === 'midiendo' ? 'aún sin semana anterior para comparar' : `${flecha} vs semana anterior`}));
    caja.style.setProperty('--acento', red.color);
    return caja;
  }));
  lineasDiarias($('g-diario'), diario);
  prepararMuse();
  if ($('texto-muse')) $('texto-muse').textContent = reporteMuse();
  const cambios = [...(FOTO.cambios || [])].sort((a, b) => (a.fecha < b.fecha ? 1 : -1));
  const hoyMx = new Date().toLocaleDateString('en-CA', {timeZone: 'America/Mexico_City'});
  const filasBitacora = cambios.map((c) => {
    const redes = c.vigilar === 'todas' ? REDES.map((r) => r.clave) : [c.vigilar];
    const promedio = (desde, hasta) => {
      const partes = redes.map((r) => sumaDias(diario, r, desde, hasta)).filter(Boolean);
      return partes.length ? partes.reduce((s, x) => s + x.total / x.dias, 0) : null;
    };
    const antes = promedio(diasAntes(c.fecha, 4), diasAntes(c.fecha, 1));
    const despues = promedio(diasAntes(c.fecha, 0), diasAntes(c.fecha, -3));
    const dias = diario.filter((d) => d.fecha >= c.fecha).length;
    let resultado = c.fecha > hoyMx ? 'programado: aún no empieza' : `midiendo · ${Math.max(1, 3 - dias) === 1 ? 'falta 1 día' : `faltan ${Math.max(1, 3 - dias)} días`}`, clase = '';
    if (dias >= 3 && antes != null && despues != null && antes > 0) {
      const x = (despues - antes) / antes;
      resultado = `${fmt(antes)} → ${fmt(despues)} vistas/día (${x >= 0 ? '▲' : '▼'} ${Math.abs(Math.round(x * 100))}%)`;
      clase = x >= 0 ? 'sube' : 'baja';
    }
    const red = c.vigilar === 'todas' ? 'todas las redes' : NOMBRE_RED[c.vigilar] || c.vigilar;
    return crear('div', {className: 'cambio-fila'},
      crear('span', {className: 'cambio-fecha', textContent: new Date(`${c.fecha}T12:00:00`).toLocaleDateString('es-MX', {day: 'numeric', month: 'short'})}),
      crear('div', {}, crear('b', {textContent: c.cambio}), crear('small', {textContent: `${c.por_que} · se mide en ${red}`})),
      crear('span', {className: `cambio-resultado ${clase}`, textContent: resultado}));
  });
  // Solo los 6 más recientes a la vista; el resto en "Ver los anteriores" (11-nov-2026: eran 30 renglones seguidos).
  const resto = filasBitacora.slice(6);
  $('bitacora').replaceChildren(...filasBitacora.slice(0, 6), ...(resto.length
    ? [crear('details', {className: 'bitacora-mas'}, crear('summary', {textContent: `Ver los ${resto.length} cambios anteriores`}), ...resto)] : []));
}

// ---------- reporte para Muse (Rodrigo, 9-nov-2026: Muse ve lo de Instagram y Facebook que Claude no; Claude ejecuta y mide) ----------
function reporteMuse() {
  const diario = diarioPorRed();
  const hoy = diario.at(-1)?.fecha || new Date().toISOString().slice(0, 10);
  const desde = diasAntes(hoy, 7);
  const lineas = [];
  lineas.push('Hola Muse. Soy el manager (Claude) de @victoriatheceo en Instagram y de la página de Facebook "Victoria the CEO".');
  lineas.push('Victoria es un personaje creado con IA (y así se declara) que habla de dinero en México: aguinaldo, deudas, ahorro, derechos laborales, dinero en pareja.');
  lineas.push(`Ritmo: ${FOTO.estado?.frecuencia || ''}.`);
  lineas.push('', `VISTAS NUEVAS, últimos 7 días contra los 7 anteriores (hasta ${hoy}):`);
  for (const red of REDES) {
    const a = sumaDias(diario, red.clave, desde, hoy);
    const b = sumaDias(diario, red.clave, diasAntes(hoy, 14), desde);
    lineas.push(`- ${red.nombre}: ${a ? fmt(a.total) : 'sin datos'}${b && b.total ? ` (antes ${fmt(b.total)})` : ''}`);
  }
  const hora = (x, clave) => x.publica_utc_por_red?.[clave] || (clave === 'ig' && x.reel_ig ? `${x.reel_ig.replace(' ', 'T')}:00-06:00` : null);
  for (const [clave, nombre] of [['ig', 'INSTAGRAM'], ['fb', 'FACEBOOK']]) {
    const posts = todo().filter((x) => { const t = hora(x, clave); return t && t.slice(0, 10) > desde && new Date(t) <= Date.now(); })
      .sort((a, b) => (hora(a, clave) < hora(b, clave) ? -1 : 1));
    lineas.push('', `${nombre}, lo que salió en la semana (fecha y hora de México · vistas · likes · comentarios de otras personas · compartidos):`);
    if (!posts.length) lineas.push('- nada medido todavía');
    for (const x of posts) {
      const m = medidas(x)[clave] || {};
      const t = new Date(hora(x, clave)).toLocaleString('es-MX', {timeZone: 'America/Mexico_City', weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'});
      lineas.push(`- ${t} · "${String(x.id).startsWith('c') ? x.gancho : x.titulo || x.gancho}" (${String(x.id).startsWith('c') ? 'Reel de carrusel' : 'video de Victoria'}) · ${m.v ?? '—'} · ${m.l ?? '—'} · ${m.c ?? '—'} · ${m.s ?? '—'}`);
    }
  }
  const tt = todo().filter((x) => salio(x) && medidas(x).tt).sort((a, b) => (medidas(b).tt.v || 0) - (medidas(a).tt.v || 0)).slice(0, 3);
  lineas.push('', 'Lo que mejor funciona en TikTok (para que compares):');
  for (const x of tt) lineas.push(`- "${x.gancho}": ${fmt(medidas(x).tt.v)} vistas`);
  const cambios = (FOTO.cambios || []).filter((c) => c.fecha > diasAntes(hoy, 10));
  if (cambios.length) {
    lineas.push('', 'Lo que cambiamos estos días:');
    for (const c of cambios) lineas.push(`- ${c.fecha}: ${c.cambio}`);
  }
  lineas.push('', 'Preguntas:',
    '1. Con lo que tú ves en Instagram y Facebook (alcance, de dónde llega la gente, guardados, compartidos, retención), ¿qué está frenando a la cuenta?',
    '2. ¿Qué 3 cambios concretos harías esta semana en Instagram y en Facebook (horario, duración, portada, primeros 3 segundos, texto, audio, formato)?',
    '3. ¿Qué tema o formato de los que subimos tiene más potencial en Meta y por qué?',
    'Respóndeme en viñetas cortas y con números cuando los tengas.');
  return lineas.join('\n');
}

function prepararMuse() {
  const boton = $('copiar-muse');
  if (!boton || boton.dataset.listo) return;
  boton.dataset.listo = '1';
  boton.addEventListener('click', async () => {
    const texto = reporteMuse();
    $('texto-muse').textContent = texto;
    try { await navigator.clipboard.writeText(texto); } catch (e) {
      const t = document.createElement('textarea'); t.value = texto; document.body.appendChild(t); t.select();
      try { document.execCommand('copy'); } catch (e2) { /* sin portapapeles: queda en "Ver el reporte" */ } t.remove();
    }
    const antes = boton.textContent; boton.textContent = 'Copiado: pégalo en Muse'; setTimeout(() => { boton.textContent = antes; }, 2500);
  });
}

function lineasDiarias(caja, diario, alto = 200) {
  if (!window.d3 || !diario.length) { caja.replaceChildren(); return; }
  const {ancho, svg} = lienzo(caja, alto);
  const tip = globo(caja);
  const m = {t: 16, r: 10, b: 26, l: 34};
  const x = d3.scalePoint(diario.map((d) => d.fecha), [m.l, ancho - m.r]);
  const y = d3.scaleLinear([0, d3.max(diario, (d) => d3.max(REDES, (r) => d[r.clave] || 0)) || 1], [alto - m.b, m.t]).nice();
  svg.append('g').attr('class', 'guia').selectAll('line').data(y.ticks(4)).join('line').attr('x1', m.l).attr('x2', ancho - m.r).attr('y1', y).attr('y2', y);
  svg.append('g').selectAll('text').data(y.ticks(4)).join('text').attr('x', m.l - 4).attr('y', (d) => y(d) + 3).attr('text-anchor', 'end').style('fill', '#7f97a6').style('font-size', '9px').text(compacto);
  for (const red of REDES) {
    const puntos = diario.filter((d) => d[red.clave] != null);
    if (!puntos.length) continue;
    svg.append('path').datum(puntos).attr('fill', 'none').attr('stroke', red.color).attr('stroke-width', 2)
      .attr('d', d3.line().x((d) => x(d.fecha)).y((d) => y(d[red.clave])));
    svg.append('g').selectAll('circle').data(puntos).join('circle').attr('r', 3).attr('cx', (d) => x(d.fecha)).attr('cy', (d) => y(d[red.clave])).attr('fill', red.color)
      .on('pointermove', (e, d) => tip.ver(e, `${red.nombre} · ${new Date(`${d.fecha}T12:00:00`).toLocaleDateString('es-MX', {weekday: 'short', day: 'numeric', month: 'short'})}`, `${fmt(d[red.clave])} vistas nuevas`))
      .on('pointerleave', () => tip.ocultar());
  }
  const cada = Math.max(1, Math.ceil(diario.length / 8));
  svg.append('g').selectAll('text').data(diario.filter((d, i) => i % cada === 0 || i === diario.length - 1)).join('text')
    .attr('x', (d) => x(d.fecha)).attr('y', alto - 8).attr('text-anchor', 'middle').style('fill', '#7f97a6').style('font-size', '9px')
    .text((d) => new Date(`${d.fecha}T12:00:00`).toLocaleDateString('es-MX', {day: 'numeric', month: 'short'}));
}

function lienzo(caja, alto, minimo = 0) {
  caja.replaceChildren();
  const ancho = Math.max(caja.clientWidth, 260, minimo);
  const svg = d3.select(caja).append('svg').attr('viewBox', `0 0 ${ancho} ${alto}`);
  // Si no cabe (muchas barras en el celular), la gráfica se desliza de lado en vez de encimar etiquetas (11-nov-2026).
  caja.classList.toggle('desliza-x', ancho > caja.clientWidth);
  if (ancho > caja.clientWidth) svg.style('width', `${ancho}px`).style('max-width', 'none');
  return {ancho, svg};
}

function reactor(caja, r) {
  if (r.restantes == null) { caja.replaceChildren(); return; }
  const {ancho, svg} = lienzo(caja, 240);
  const radio = Math.min(ancho / 2 - 14, 108);
  const g = svg.append('g').attr('transform', `translate(${ancho / 2},120)`);
  const lleno = r.restantes / (r.iniciales || 12000);
  const color = lleno < 0.25 ? ROJO : ORO;
  const arco = d3.arc().innerRadius(radio - 16).outerRadius(radio).padAngle(0.025);
  d3.range(52).forEach((i) => {
    const encendido = i / 52 < lleno;
    g.append('path').attr('d', arco({startAngle: (i / 52) * 2 * Math.PI, endAngle: ((i + 1) / 52) * 2 * Math.PI}))
      .attr('fill', encendido ? color : '#13202b').style('filter', encendido ? `drop-shadow(0 0 4px ${color})` : null);
  });
  g.append('circle').attr('r', radio - 24).attr('fill', 'none').attr('stroke', CIAN).attr('stroke-opacity', 0.35).attr('stroke-dasharray', '2 5');
  g.append('circle').attr('r', radio - 34).attr('fill', 'rgba(73,214,236,.06)').attr('stroke', CIAN).attr('stroke-opacity', 0.5);
  g.append('text').attr('class', 'pct').attr('text-anchor', 'middle').attr('y', -radio / 4.2).text(`${Math.round(lleno * 100)}%`);
  g.append('text').attr('class', 'num').attr('text-anchor', 'middle').attr('y', radio / 9).style('font-size', `${Math.round(radio / 3.6)}px`).text(fmt(r.restantes));
  g.append('text').attr('class', 'cap').attr('text-anchor', 'middle').attr('y', radio / 3.1).text('CRÉDITOS');
}

function eje(svg, escala, alto, m, etiquetas) {
  const ejeX = d3.axisBottom(escala).tickSize(0).tickPadding(10);
  if (etiquetas) ejeX.tickFormat((i) => etiquetas[i]);
  svg.append('g').attr('transform', `translate(0,${alto - m.b})`).call(ejeX)
    .call((g) => g.select('.domain').attr('stroke', 'rgba(73,214,236,.3)')).attr('font-size', null).attr('font-family', null);
}

function barras(caja, filas, {color, formato = fmt, alto = 200, linea = null}) {
  if (!filas.length) { caja.replaceChildren(); return; }
  const {ancho, svg} = lienzo(caja, alto);
  const tip = globo(caja);
  const m = {t: 22, r: 10, b: 28, l: 10};
  filas = filas.map((d, i) => ({...d, i}));
  const x = d3.scaleBand(filas.map((d) => d.i), [m.l, ancho - m.r]).padding(0.38);
  const y = d3.scaleLinear([0, Math.max(d3.max(filas, (d) => d.v) || 1, linea || 0)], [alto - m.b, m.t]).nice();
  svg.append('g').attr('class', 'guia').selectAll('line').data(y.ticks(4)).join('line').attr('x1', m.l).attr('x2', ancho - m.r).attr('y1', y).attr('y2', y);
  const id = `gr${Math.random().toString(36).slice(2, 8)}`;
  const grad = svg.append('defs').append('linearGradient').attr('id', id).attr('x1', 0).attr('x2', 0).attr('y1', 0).attr('y2', 1);
  grad.append('stop').attr('offset', 0).style('stop-color', color);
  grad.append('stop').attr('offset', 1).style('stop-color', color).style('stop-opacity', 0.2);
  const w = Math.min(x.bandwidth(), 42);
  svg.append('g').selectAll('rect').data(filas).join('rect')
    .attr('x', (d) => x(d.i) + (x.bandwidth() - w) / 2).attr('width', w).attr('y', (d) => y(d.v)).attr('height', (d) => y(0) - y(d.v))
    .attr('fill', `url(#${id})`).attr('stroke', color).attr('stroke-opacity', 0.8)
    .on('pointermove', (e, d) => tip.ver(e, d.k, formato(d.v))).on('pointerleave', () => tip.ocultar());
  svg.append('g').selectAll('text').data(filas).join('text').attr('text-anchor', 'middle').attr('x', (d) => x(d.i) + x.bandwidth() / 2).attr('y', (d) => y(d.v) - 6)
    .style('fill', '#e9f6fb').text((d) => formato(d.v));
  if (linea != null) {
    svg.append('line').attr('x1', m.l).attr('x2', ancho - m.r).attr('y1', y(linea)).attr('y2', y(linea)).attr('stroke', ROJO).attr('stroke-dasharray', '4 4');
    svg.append('text').attr('x', ancho - m.r).attr('y', y(linea) - 5).attr('text-anchor', 'end').style('fill', ROJO).text(`mínimo ${formato(linea)}`);
  }
  eje(svg, x, alto, m, filas.map((d) => d.k));
}

function apiladas(caja, videos) {
  if (!videos.length) { caja.replaceChildren(); return; }
  const alto = 220;
  const {ancho, svg} = lienzo(caja, alto, videos.length * 36 + 20);
  const tip = globo(caja);
  const m = {t: 22, r: 10, b: 28, l: 10};
  const filas = videos.map((v) => { const md = medidas(v); return {k: String(v.id).startsWith('c') ? String(v.id) : `v${v.id}`, ...Object.fromEntries(REDES.map((r) => [r.clave, Number(md[r.clave]?.v) || 0]))}; });
  const pilas = d3.stack().keys(REDES.map((r) => r.clave))(filas);
  const x = d3.scaleBand(filas.map((d) => d.k), [m.l, ancho - m.r]).padding(0.38);
  const y = d3.scaleLinear([0, d3.max(filas, (d) => REDES.reduce((s, r) => s + d[r.clave], 0)) || 1], [alto - m.b, m.t]).nice();
  svg.append('g').attr('class', 'guia').selectAll('line').data(y.ticks(4)).join('line').attr('x1', m.l).attr('x2', ancho - m.r).attr('y1', y).attr('y2', y);
  const w = Math.min(x.bandwidth(), 42);
  pilas.forEach((capa, i) => {
    svg.append('g').selectAll('rect').data(capa).join('rect')
      .attr('x', (d) => x(d.data.k) + (x.bandwidth() - w) / 2).attr('width', w).attr('y', (d) => y(d[1])).attr('height', (d) => Math.max(0, y(d[0]) - y(d[1])))
      .attr('fill', REDES[i].color).attr('fill-opacity', 0.85)
      .on('pointermove', (e, d) => tip.ver(e, `${d.data.k} · ${REDES[i].nombre}`, `${fmt(d.data[REDES[i].clave])} vistas`)).on('pointerleave', () => tip.ocultar());
  });
  svg.append('g').selectAll('text').data(filas).join('text').attr('text-anchor', 'middle').attr('x', (d) => x(d.k) + x.bandwidth() / 2)
    .attr('y', (d) => y(REDES.reduce((s, r) => s + d[r.clave], 0)) - 6).style('fill', '#e9f6fb').text((d) => compacto(REDES.reduce((s, r) => s + d[r.clave], 0)));
  eje(svg, x, alto, m);
}

function saldo(caja, ej, r) {
  if (!ej.length) { caja.replaceChildren(); return; }
  const alto = 210;
  const {ancho, svg} = lienzo(caja, alto);
  const tip = globo(caja);
  const m = {t: 24, r: 54, b: 28, l: 12};
  const puntos = [{k: 'inicio', v: r.iniciales, detalle: 'Saldo inicial'}, ...ej.map((e) => ({k: e.n, v: Number(e.creditos_restantes), detalle: e.detalle}))].map((d, i) => ({...d, n: i}));
  const x = d3.scalePoint(puntos.map((d) => d.n), [m.l + 8, ancho - m.r]);
  const y = d3.scaleLinear([0, d3.max(puntos, (d) => d.v)], [alto - m.b, m.t]).nice();
  svg.append('g').attr('class', 'guia').selectAll('line').data(y.ticks(4)).join('line').attr('x1', m.l).attr('x2', ancho - m.r).attr('y1', y).attr('y2', y);
  const id = `sa${Math.random().toString(36).slice(2, 8)}`;
  const grad = svg.append('defs').append('linearGradient').attr('id', id).attr('x1', 0).attr('x2', 0).attr('y1', 0).attr('y2', 1);
  [[0, 0.28], [0.5, 0.08], [1, 0]].forEach(([o, a]) => grad.append('stop').attr('offset', o).style('stop-color', CIAN).style('stop-opacity', a));
  svg.append('path').datum(puntos).attr('fill', `url(#${id})`).attr('d', d3.area().x((d) => x(d.n)).y0(y(0)).y1((d) => y(d.v)));
  svg.append('path').datum(puntos).attr('fill', 'none').attr('stroke', CIAN).attr('stroke-width', 2).style('filter', `drop-shadow(0 0 4px ${CIAN})`).attr('d', d3.line().x((d) => x(d.n)).y((d) => y(d.v)));
  svg.append('g').selectAll('circle').data(puntos).join('circle').attr('cx', (d) => x(d.n)).attr('cy', (d) => y(d.v)).attr('r', 4).attr('fill', FONDO).attr('stroke', CIAN).attr('stroke-width', 2)
    .on('pointermove', (e, d) => tip.ver(e, d.detalle, `${fmt(d.v)} créditos`)).on('pointerleave', () => tip.ocultar());
  const ultimo = puntos.at(-1);
  svg.append('text').attr('x', x(ultimo.n) + 8).attr('y', y(ultimo.v) + 4).style('fill', CIAN).text(compacto(ultimo.v));
  eje(svg, x, alto, m, puntos.map((d) => d.k));
}

function calor(caja, horas) {
  const celdas = horas.map((d) => ({dia: d.dia, hora: Number(d.hora), p: d.puntaje == null || d.puntaje === '' ? null : Number(d.puntaje)}));
  const vacio = celdas.every((c) => c.p == null);
  $('vacio-horas').hidden = !vacio;
  if (vacio) { caja.replaceChildren(); return; }
  const m = {t: 6, r: 6, b: 24, l: 36};
  const ancho = Math.max(caja.clientWidth, 300);
  const lado = (ancho - m.l - m.r) / 24;
  const alto = m.t + m.b + lado * 7;
  const {svg} = lienzo(caja, alto);
  const tip = globo(caja);
  const tope = d3.max(celdas, (d) => d.p || 0) || 1;
  const mejor = celdas.reduce((a, b) => ((b.p || 0) > (a.p || 0) ? b : a));
  svg.append('g').selectAll('rect').data(celdas).join('rect')
    .attr('x', (d) => m.l + d.hora * lado + 1).attr('y', (d) => m.t + DIAS.indexOf(d.dia) * lado + 1).attr('width', lado - 2).attr('height', lado - 2)
    .attr('fill', (d) => (d.p == null ? '#0a151e' : d3.interpolateRgb('#0d1c27', ORO)(d.p / tope)))
    .attr('stroke', (d) => (d === mejor ? '#fff' : 'none'))
    .on('pointermove', (e, d) => tip.ver(e, `${d.dia} ${String(d.hora).padStart(2, '0')}:00`, d.p == null ? 'sin datos' : `puntaje ${d.p.toFixed(1)}`)).on('pointerleave', () => tip.ocultar());
  svg.append('g').selectAll('text').data(DIAS).join('text').attr('x', m.l - 6).attr('y', (d, i) => m.t + i * lado + lado / 2 + 4).attr('text-anchor', 'end').text((d) => d);
  svg.append('g').selectAll('text').data([0, 6, 12, 18, 23]).join('text').attr('x', (d) => m.l + d * lado + lado / 2).attr('y', alto - 6).attr('text-anchor', 'middle').text((d) => `${d}h`);
}

// ---------- fondo de partículas ----------
(function particulas() {
  const c = $('particulas');
  const ctx = c.getContext('2d');
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  let puntos = [];
  const medir = () => {
    c.width = innerWidth * devicePixelRatio;
    c.height = innerHeight * devicePixelRatio;
    puntos = Array.from({length: Math.min(70, Math.round(innerWidth / 18))}, () => ({x: Math.random() * c.width, y: Math.random() * c.height, v: 0.15 + Math.random() * 0.45, r: Math.random() * 1.6 + 0.4}));
  };
  medir();
  addEventListener('resize', medir);
  const cuadro = () => {
    ctx.clearRect(0, 0, c.width, c.height);
    for (const p of puntos) {
      p.y -= p.v * devicePixelRatio;
      if (p.y < 0) { p.y = c.height; p.x = Math.random() * c.width; }
      ctx.fillStyle = p.r > 1.5 ? 'rgba(245,197,66,.55)' : 'rgba(73,214,236,.45)';
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * devicePixelRatio, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(cuadro);
  };
  requestAnimationFrame(cuadro);
})();

// ---------- inicio ----------
addEventListener('load', () => {
  arrancar(false).catch((err) => {
    mostrar('acceso');
    if (!err.acceso) $('error-acceso').textContent = err.message;
    $('clave').focus();
  });
});

// "Comenta hoy" (Rodrigo, 10-nov-2026): TikTok no deja comentar en videos ajenos por API y automatizarlo con un navegador
// arriesga la cuenta; la rutina de la mañana deja aquí 3-5 videos frescos de cuentas grandes con el comentario ya escrito
// en la voz de Victoria. Rodrigo copia, abre, pega y marca. Lo marcado se recuerda solo en este celular.
async function copiarTexto(texto) {
  try { await navigator.clipboard.writeText(texto); return true; } catch (e) {
    const t = document.createElement('textarea'); t.value = texto; document.body.appendChild(t); t.select();
    let ok = false; try { ok = document.execCommand('copy'); } catch (e2) { /* sin portapapeles */ } t.remove(); return ok;
  }
}

function dibujarComentarHoy() {
  const caja = $('comentar-hoy');
  if (!caja) return;
  const datos = FOTO.comentar_hoy || {};
  const lista = datos.videos || [];
  const clave = `comentados-${datos.fecha || ''}`;
  let hechos = [];
  try { hechos = JSON.parse(localStorage.getItem(clave) || '[]'); } catch (e) { hechos = []; }
  const guardar = () => { try { localStorage.setItem(clave, JSON.stringify(hechos)); } catch (e) { /* sin memoria local */ } };
  const resumen = $('comentar-resumen');
  const pintarResumen = () => {
    if (resumen) resumen.textContent = lista.length ? `${hechos.length} de ${lista.length} hechos · ${datos.fecha === hoyMx() ? 'lista de hoy' : `lista del ${fechaCorta(datos.fecha)}; la nueva llega a las 6:37`}` : 'la rutina de la mañana deja la lista';
  };
  pintarResumen();
  if (!lista.length) { caja.replaceChildren(crear('p', {className: 'nota', textContent: 'Todavía no hay lista de hoy.'})); return; }
  caja.replaceChildren(...lista.map((v) => {
    const tarjeta = crear('div', {className: `comentar${hechos.includes(v.url) ? ' hecho' : ''}`});
    const copiar = crear('button', {type: 'button', className: 'boton', textContent: '1 · Copiar'});
    const abrir = crear('a', {className: 'boton', href: v.url, target: '_blank', rel: 'noopener', textContent: '2 · Abrir y pegar'});
    const marcar = crear('button', {type: 'button', className: 'boton tenue'});
    const pintarMarca = () => { marcar.textContent = tarjeta.classList.contains('hecho') ? '✓ Hecho' : '3 · Ya lo comenté'; };
    pintarMarca();
    copiar.addEventListener('click', async () => { copiar.textContent = (await copiarTexto(v.comentario)) ? 'Copiado ✓' : 'Mantén presionado el texto'; });
    marcar.addEventListener('click', () => {
      hechos = hechos.includes(v.url) ? hechos.filter((u) => u !== v.url) : [...hechos, v.url];
      guardar(); tarjeta.classList.toggle('hecho'); pintarMarca(); pintarResumen();
    });
    tarjeta.append(
      crear('div', {className: 'cab'}, crear('strong', {textContent: `@${v.autor}`}), crear('small', {textContent: ` · ${fmt(v.vistas)} vistas · ${v.tema}`})),
      crear('p', {className: 'texto', textContent: v.comentario}),
      crear('p', {className: 'nota', textContent: v.por_que || ''}),
      crear('div', {className: 'acciones'}, copiar, abrir, marcar));
    return tarjeta;
  }));
}
