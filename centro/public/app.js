// Centro de mando de Victoria: pide la última foto del sistema (/api/estado) y los números en vivo (/api/vivo) cada minuto.
const REDES = [
  {clave: 'yt', nombre: 'YouTube', corto: 'YT', color: '#ff3b55'},
  {clave: 'tt', nombre: 'TikTok', corto: 'TT', color: '#49d6ec'},
  {clave: 'ig', nombre: 'Instagram', corto: 'IG', color: '#f5c542'},
];
const ESTADOS = {pendiente: ['En cola', ''], listo_para_publicar: ['Listo', 'listo'], en_proceso: ['Generando', 'vivo'], programado: ['Programado', 'ok'], publicado: ['Publicado', 'ok'], ok: ['OK', 'ok'], fallido: ['Falló', 'mal'], omitido: ['Omitido', ''], listo: ['Listo', 'listo'], borrador: ['Borrador', ''], por_programar: ['Por programar', '']};
const NOMBRE_RED = {ig: 'Instagram', tt: 'TikTok', yt: 'YouTube'};
// Todo lo que sale: videos y carruseles (los dos se miden en vivo).
const todo = () => [...FOTO.videos, ...(FOTO.carruseles || [])];
const PILARES = {negocio: 'Negocio', finanzas: 'Finanzas', mentalidad: 'Mentalidad', vida: 'Vida', motivacion_economica: 'Motivación $'};
const DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'];
const ORO = '#f5c542', CIAN = '#49d6ec', ROJO = '#ff3b55', FONDO = '#07111a';
const MINUTO = 60_000;

let FOTO = null;   // /api/estado
let VIVO = null;   // /api/vivo
const $ = (id) => document.getElementById(id);
const crear = (etiqueta, props = {}, ...hijos) => { const el = Object.assign(document.createElement(etiqueta), props); el.append(...hijos); return el; };
const fmt = (n) => (n == null || Number.isNaN(n) ? '—' : Math.round(n).toLocaleString('es-MX'));
const compacto = (n) => (n == null ? '—' : Math.abs(n) >= 10000 ? new Intl.NumberFormat('es-MX', {notation: 'compact', maximumFractionDigits: 1}).format(n) : fmt(n));
const pct = (x) => (x == null ? '—' : `${Math.round(x * 100)}%`);
const mx = (iso, op = {day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'}) => (iso ? new Date(iso).toLocaleString('es-MX', {timeZone: 'America/Mexico_City', ...op}) : '');
const porFecha = (a, b) => (a.fecha_utc < b.fecha_utc ? -1 : 1);

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
      ['Enlace con Publer (TikTok · Instagram)', Boolean(vivo) && !vivo.errores?.some((x) => x.startsWith('Publer'))],
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
    setInterval(async () => { try { FOTO = await pedir('/api/estado'); dibujarTodo(); } catch { /* sigue con la foto anterior */ } }, 5 * MINUTO);
    setInterval(relojes, 1000);
    let ancho = innerWidth;
    addEventListener('resize', () => { if (Math.abs(innerWidth - ancho) > 40) { ancho = innerWidth; dibujarGraficas(); } });
  }
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
  return m;
}
const vistasDe = (v) => Object.values(medidas(v)).reduce((s, x) => s + (Number(x.v) || 0), 0);
// Un video cuenta como medido cuando ya salió (antes, YouTube reporta 0 del video programado).
const salio = (v) => Boolean(v.publica_utc) && new Date(v.publica_utc).getTime() <= Date.now();
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
  const {videos, ejecuciones} = FOTO;
  const medidos = videos.filter(medido);
  if (medidos.length < 8) {
    lista.push(['dato', `${medidos.length} de 8 videos medidos. Con 8 ya se decide la mejor hora y el mejor tema con datos, no a ojo.`]);
  } else {
    for (const [campo, nombre] of [['pilar', 'tema'], ['hora_plan', 'hora']]) {
      const g = promedioPor(campo).filter((x) => x.videos >= 2).sort((a, b) => b.promedio - a.promedio);
      if (g.length > 1) {
        const etq = (x) => (campo === 'pilar' ? PILARES[x.grupo] || x.grupo : x.grupo);
        lista.push(['idea', `Mejor ${nombre}: ${etq(g[0])} promedia ${fmt(g[0].promedio)} vistas por video contra ${fmt(g.at(-1).promedio)} de ${etq(g.at(-1))}.`]);
      }
    }
    const mejor = [...medidos].sort((a, b) => vistasDe(b) - vistasDe(a))[0];
    lista.push(['idea', `El video ${mejor.id} es el récord con ${fmt(vistasDe(mejor))} vistas: "${mejor.gancho}".`]);
  }
  const r = resumen();
  if (r.listos) lista.push(['dato', `${r.listos} video(s) ya generados esperan salir: se publican sin gastar créditos.`]);
  const fallos = ejecuciones.filter((e) => e.resultado === 'fallido').sort(porFecha);
  if (fallos.length) lista.push(['alerta', `${fallos.length} ejecución(es) no publicaron. Última: ${fallos.at(-1).detalle}`]);
  if (r.alcanzan != null) {
    lista.push(r.alcanzan < 6
      ? ['alerta', `Energía para solo ${r.alcanzan} videos. Recarga OpenArt o baja la frecuencia.`]
      : ['dato', `Energía para unos ${r.alcanzan} videos más: ${r.alcanzan * (FOTO.estado.dias_entre_videos || 2)} días al ritmo actual.`]);
  }
  if (r.cola <= 3) lista.push(['alerta', `Quedan ${r.cola} guiones en cola. Pide a Claude el siguiente plan de videos.`]);
  for (const e of VIVO?.errores || []) lista.push(['alerta', `Sin conexión en vivo con ${e}`]);
  for (const a of FOTO.auditoria?.alertas || []) lista.push([/pierde|revisar|fallaron|Recargar/.test(a) ? 'alerta' : /gana/.test(a) ? 'idea' : 'dato', a]);
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
  $('mision-cuando').textContent = sigue ? mx(sigue.utc, {weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit'}) : '—';
  contar($('m-likes'), r.likes);
  $('m-cola').textContent = fmt(r.cola);
  $('m-fallos').textContent = fmt(r.fallos);
  $('a-usados').textContent = fmt(r.usados);
  $('a-costo').textContent = fmt(r.costo);
  $('a-dias').textContent = r.alcanzan == null ? '—' : fmt(r.alcanzan * 2);

  const errores = VIVO?.errores || [];
  $('aviso').hidden = !errores.length;
  $('aviso').textContent = errores.length ? `Conexión en vivo incompleta: ${errores.join(' · ')}. Se muestran los últimos números guardados.` : '';
  $('pulso').classList.toggle('falla', errores.length > 0);
  $('pie').textContent = `YouTube en vivo · TikTok e Instagram vía Publer · última foto del sistema: ${mx(estado.generado_utc)} · créditos según la última ejecución`;

  dibujarRedes();
  dibujarLaboratorio(FOTO.auditoria || {});
  dibujarCinta(ejecuciones, aprendizajes);
  dibujarHangar(videos);
  dibujarListas(aprendizajes);
  dibujarTablas(videos, ejecuciones);
  dibujarCalendario(FOTO.calendario);
  dibujarMetas();
  dibujarRadar();
  dibujarDespegues();
  dibujarHorarios(FOTO.auditoria || {}, estado);
  dibujarCarruseles(FOTO.carruseles);
  dibujarGraficas();
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
  // YouTube en vivo por su API; Instagram y TikTok por Publer (último dato semanal).
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
  const eventos = [...ejecuciones].sort(porFecha).reverse().slice(0, 6).map((e) => `${mx(e.fecha_utc)} · ${(ESTADOS[e.resultado] || [e.resultado])[0]} · ${e.detalle}`);
  eventos.push(...aprendizajes.slice(-3).map((a) => `Lección: ${a.regla}`));
  const cinta = $('cinta');
  // Dos copias para que el desplazamiento sea continuo.
  cinta.replaceChildren(...[...eventos, ...eventos].map((t) => crear('span', {textContent: t})));
}

function dibujarHangar(videos) {
  const caja = $('hangar');
  caja.replaceChildren();
  for (const v of videos) {
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
      crear('span', {className: `chip ${clase}`, textContent: v.publica_mx && ['programado', 'publicado'].includes(v.estado) ? `${texto} · ${v.publica_mx.slice(5)}` : texto}),
      crear('p', {textContent: v.gancho}),
      crear('p', {className: 'met', textContent: extra.join(' · ')}),
      ...(linea ? [crear('p', {className: 'met', textContent: linea})] : []))));
  }
}

const ATRIBUTOS = {pilar: 'Tema', tipo_fondo: 'Tipo de fondo', locacion: 'Fondo', estilo_vestuario: 'Vestimenta',
  color_vestuario: 'Color de ropa', tipo_gancho: 'Tipo de gancho', titulo_emoji: 'Emoji en el título',
  titulo_largo: 'Largo del título', titulo_tipo: 'Título: afirma o pregunta', dia: 'Día', hora: 'Hora'};
const MODOS = {aprovechar: 'Aprovechar', explorar: 'Explorar', 'sin guiones': 'Sin guiones'};

function dibujarLaboratorio(a) {
  const caja = $('decision');
  const d = a.decision;
  const texto = crear('div');
  if (!d) {
    texto.append(crear('p', {textContent: 'No hay guiones pendientes: el sistema escribe 10 nuevos en la siguiente ejecución.'}));
  } else {
    texto.append(crear('p', {textContent: `${d.toca_publicar ? 'Hoy toca publicar' : 'Hoy no toca publicar'} (${d.motivo}). Siguiente a generar: ${d.por_que}`}));
    if (d.horarios) texto.append(crear('p', {className: 'nota', textContent: `Hoy cada red a su hora: ${Object.entries(d.horarios).map(([r, h]) => `${NOMBRE_RED[r]} ${h}`).join(' · ')}.`}));
    if (a.reglas_vigentes?.length) texto.append(crear('ul', {}, ...a.reglas_vigentes.map((r) => crear('li', {textContent: r}))));
    if (d.cambios_sugeridos?.length) {
      texto.append(crear('ul', {}, ...d.cambios_sugeridos.map((c) => crear('li', {textContent: `${ATRIBUTOS[c.atributo] || c.atributo}: ${c.de} → ${c.a} (${c.por_que})`}))));
    }
  }
  texto.append(crear('p', {className: 'nota', textContent: `${a.videos_calificados || 0} videos calificados${a.base_vistas_36h ? ` · lo normal: ${fmt(a.base_vistas_36h)} vistas a 36 h` : ''}${a.fecha_utc ? ` · auditoría del ${mx(a.fecha_utc)}` : ''}`}));
  const modo = d?.modo || 'aprovechar';
  caja.replaceChildren(crear('div', {className: `modo ${modo}`}, MODOS[modo] || modo, crear('small', {textContent: d?.video_id ? `video ${d.video_id}` : 'sin video'})), texto);

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
      lista.append(crear('div', {className: 'fila'}, crear('span', {textContent: PILARES[f.valor] || f.valor.replace('_', ' ')}), barra, crear('em', {textContent: `${f.indice.toFixed(2)} · ${f.n} v`})));
    }
    lab.append(crear('article', {className: 'panel'}, crear('div', {className: 'codigo', textContent: `LAB · ${atributo}`}), crear('h2', {textContent: ATRIBUTOS[atributo] || atributo}), lista));
  }
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
  $('lecciones').replaceChildren(...recientes.slice(0, 6).map((a) => elemento(a.tipo, tipos[a.tipo] || a.tipo, a.regla, `${a.origen}: ${a.aprendizaje}`)),
    ...(recientes.length > 6 ? [crear('li', {className: 'mas', textContent: `+${recientes.length - 6} lecciones más guardadas en el sistema`})] : []));
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
  const secciones = [...document.querySelectorAll('main .seccion')];
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
const NOTA_META = {tt: {1000: 'enlace en la bio', 10000: 'TikTok empieza a pagar'}, ig: {10000: 'marcas y colaboraciones'}};
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

function dibujarRadar() {
  const C = 150, R = 132, DIAS_RADAR = 14;
  const sector = {yt: -90, tt: 30, ig: 150};  // 120° por red
  const svg = svgEl('svg', {viewBox: '0 0 300 300', role: 'img', 'aria-label': 'Radar de publicaciones'});
  const defs = svgEl('defs', {}, svgEl('radialGradient', {id: 'barrido-grad', cx: 0, cy: 0, r: 1, gradientUnits: 'userSpaceOnUse', gradientTransform: `translate(${C} ${C}) scale(${R})`},
    svgEl('stop', {offset: '0', 'stop-color': '#49d6ec', 'stop-opacity': '.0'}), svgEl('stop', {offset: '1', 'stop-color': '#49d6ec', 'stop-opacity': '.35'})));
  svg.append(defs);
  for (const r of [R / 3, (2 * R) / 3, R]) svg.append(svgEl('circle', {cx: C, cy: C, r, class: 'anillo'}));
  for (const red of REDES) {
    const a = ((sector[red.clave] - 60) * Math.PI) / 180;
    svg.append(svgEl('line', {x1: C, y1: C, x2: C + R * Math.cos(a), y2: C + R * Math.sin(a), class: 'eje'}));
    const m = ((sector[red.clave]) * Math.PI) / 180;
    svg.append(svgEl('text', {x: C + (R + 12) * Math.cos(m), y: C + (R + 12) * Math.sin(m) + 3, 'text-anchor': 'middle', fill: red.color}, red.corto));
  }
  const fin = (-25 * Math.PI) / 180;
  svg.append(svgEl('g', {class: 'barrido'}, svgEl('path', {d: `M${C} ${C} L${C + R} ${C} A${R} ${R} 0 0 0 ${C + R * Math.cos(fin)} ${C + R * Math.sin(fin)} Z`, fill: 'url(#barrido-grad)'})));
  const ahora = Date.now();
  const puntos = [];
  for (const p of todo().filter(salio)) {
    for (const red of REDES) {
      const m = medidas(p)[red.clave];
      if (!m || m.pendiente) continue;
      const t = new Date((p.publica_utc_por_red || {})[red.clave] || p.publica_utc).getTime();
      const dias = (ahora - t) / 864e5;
      if (!(dias >= 0 && dias <= DIAS_RADAR)) continue;
      puntos.push({p, red, v: Number(m.v) || 0, dias});
    }
  }
  const tope = Math.max(1, ...puntos.map((x) => x.v));
  for (const {p, red, v, dias} of puntos) {
    let semilla = 0;
    for (const ch of String(p.id)) semilla = (semilla * 31 + ch.charCodeAt(0)) % 997;
    const ang = ((sector[red.clave] - 50 + (semilla % 100)) * Math.PI) / 180;
    const dist = 14 + (dias / DIAS_RADAR) * (R - 18);
    const titulo = svgEl('title', {}, `${String(p.id).startsWith('c') ? 'Carrusel' : 'Video'} ${p.id} · ${red.nombre} · ${fmt(v)} vistas`);
    svg.append(svgEl('g', {class: 'blip'}, svgEl('circle', {cx: C + dist * Math.cos(ang), cy: C + dist * Math.sin(ang), r: 3 + 9 * Math.sqrt(v / tope), fill: red.color, color: red.color}), titulo));
  }
  if (!puntos.length) svg.append(svgEl('text', {x: C, y: C + 4, 'text-anchor': 'middle', class: 'vacio-radar'}, 'esperando la primera medición'));
  $('radar').replaceChildren(svg);
}

function siguientePorRed(clave) {
  let mejor = null;
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
      crear('small', {textContent: sig ? `${String(sig.p.id).startsWith('c') ? 'Carrusel' : 'Video'} ${sig.p.id} · ${mx(new Date(sig.t).toISOString(), {weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'})}` : 'Nada programado todavía: la auditoría de mañana lo programa'}));
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

function dibujarCalendario(filas = []) {
  const hoy = new Date().toLocaleDateString('en-CA', {timeZone: 'America/Mexico_City'});
  $('t-calendario').replaceChildren(...filas.map((f) => {
    const vivo = [...(FOTO.carruseles || []), ...FOTO.videos].find((x) => x.id === f.id);
    const vistas = vivo && salio(vivo) && medido(vivo) ? fmt(vistasDe(vivo)) : '';
    return crear('tr', {className: f.fecha === hoy ? 'hoy' : ''},
      celda(new Date(`${f.fecha}T12:00:00`).toLocaleDateString('es-MX', {weekday: 'short', day: 'numeric', month: 'short'})),
      celda(f.tipo === 'carrusel' ? 'Carrusel' : 'Video'), celda(f.que),
      celda(f.horas.ig || '—', 'n'), celda(f.horas.tt || '—', 'n'), celda(f.horas.yt || '—', 'n'), chip(f.estado), celda(vistas, 'n'));
  }));
}

function dibujarHorarios(a, estado) {
  const d = a.decision || {};
  const datos = a.horarios_por_red || {};
  const minimo = estado.prueba_horas?.min_por_franja || 4;
  $('horarios-red').replaceChildren(...['ig', 'tt', 'yt'].map((r) => {
    const info = datos[r] || {franjas: {}, dias: {}};
    const conteo = (d.conteo_horas || {})[r] || {};
    const franjas = estado.prueba_horas?.franjas || Object.keys(conteo);
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
  $('t-carruseles').replaceChildren(...lista.map((c) => {
    const horas = Object.entries(c.horas || {}).map(([r, h]) => `${NOMBRE_RED[r]} ${h.slice(5)}`).join(' · ');
    const m = medidas(c);
    const red = (clave) => celda(salio(c) && m[clave] ? fmt(m[clave].v) : '', 'n');
    return crear('tr', {}, celda(c.id), chip(c.estado), celda(c.tema), celda(c.gancho), celda(horas || '—'),
      red('ig'), red('tt'), red('yt'), celda(salio(c) && medido(c) ? fmt(vistasDe(c)) : '', 'n'));
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

function dibujarGraficas() {
  if (!window.d3 || !FOTO) return;
  const r = resumen();
  reactor($('g-reactor'), r);
  const ej = [...FOTO.ejecuciones].sort(porFecha).map((e, i) => ({...e, n: e.video_id ? `v${e.video_id}` : `#${i + 1}`}));
  saldo($('g-saldo'), ej, r);
  barras($('g-gasto'), ej.map((e) => ({k: e.n, v: Number(e.creditos_usados) || 0})), {color: ORO});
  const medidos = todo().filter(medido);
  $('vacio-vistas').hidden = medidos.length > 0;
  apiladas($('g-vistas'), medidos);
  for (const [campo, id, vacio, color, nombres] of [['pilar', 'g-pilar', 'vacio-pilar', ORO, PILARES]]) {
    let filas = promedioPor(campo);
    if (campo === 'dia') filas.sort((a, b) => DIAS.indexOf(a.grupo) - DIAS.indexOf(b.grupo));
    if (campo === 'hora_plan' && filas.length < 2) filas = [];
    $(vacio).hidden = filas.length > 0;
    barras($(id), filas.map((x) => ({k: nombres[x.grupo] || x.grupo, v: x.promedio})), {color, formato: compacto, alto: 190});
  }
}

function lienzo(caja, alto) {
  caja.replaceChildren();
  const ancho = Math.max(caja.clientWidth, 260);
  return {ancho, svg: d3.select(caja).append('svg').attr('viewBox', `0 0 ${ancho} ${alto}`)};
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
  const {ancho, svg} = lienzo(caja, alto);
  const tip = globo(caja);
  const m = {t: 22, r: 10, b: 28, l: 10};
  const filas = videos.map((v) => { const md = medidas(v); return {k: `v${v.id}`, ...Object.fromEntries(REDES.map((r) => [r.clave, Number(md[r.clave]?.v) || 0]))}; });
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
