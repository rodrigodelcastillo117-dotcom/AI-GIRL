// Panel esencial de Victoria (12-nov-2026). Lee /api/estado (la foto del sistema) y /api/vivo (números en vivo).
// Solo lo importante: estado, redes, vistas por día, lo que funciona, lo que sale, la tarea del día y el gasto.
const $ = (id) => document.getElementById(id);
const el = (tag, props = {}, ...hijos) => { const e = Object.assign(document.createElement(tag), props); e.append(...hijos.filter((h) => h != null)); return e; };
const NS = 'http://www.w3.org/2000/svg';
const svg = (tag, attrs = {}) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); return e; };
// Orden fijo validado (no cambiar: el color sigue a la red, nunca a su lugar en un ranking)
const REDES = [
  {k: 'tt', nombre: 'TikTok', var: '--tt'},
  {k: 'yt', nombre: 'YouTube', var: '--yt'},
  {k: 'fb', nombre: 'Facebook', var: '--fb'},
  {k: 'ig', nombre: 'Instagram', var: '--ig'},
];
const color = (r) => `var(${r.var})`;
const n0 = (n) => (n == null || Number.isNaN(n) ? '—' : Math.round(n).toLocaleString('es-MX'));
const corto = (n) => (n == null ? '—' : Math.abs(n) >= 10000 ? new Intl.NumberFormat('es-MX', {notation: 'compact', maximumFractionDigits: 1}).format(n) : n0(n));
const usd = (n) => (n == null ? '—' : `$${Number(n).toFixed(2)}`);
const hoyMx = () => new Date().toLocaleDateString('en-CA', {timeZone: 'America/Mexico_City'});
const sumarDias = (iso, d) => new Date(new Date(`${iso}T12:00:00Z`).getTime() + d * 864e5).toISOString().slice(0, 10);
const sinEmoji = (t) => String(t || '').replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}]/gu, '').trim();
let FOTO = null, VIVO = null;

async function pedir(ruta, opciones) {
  const r = await fetch(ruta, {credentials: 'same-origin', ...opciones});
  if (r.status === 401) throw Object.assign(new Error('sin acceso'), {acceso: true});
  if (!r.ok) throw new Error(`${ruta} respondió ${r.status}`);
  return r.json();
}

// ---------- acceso ----------
$('formulario').addEventListener('submit', async (e) => {
  e.preventDefault();
  $('error-acceso').textContent = '';
  try {
    const r = await fetch('/api/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({clave: $('clave').value})});
    if (!r.ok) throw new Error('Clave incorrecta');
    await arrancar();
  } catch (err) { $('error-acceso').textContent = err.message; }
});
$('salir').addEventListener('click', async () => { await fetch('/api/login', {method: 'DELETE'}); location.reload(); });

async function arrancar() {
  try {
    FOTO = await pedir('/api/estado');
    VERSION.v = FOTO.version || null;
  } catch (err) {
    if (err.acceso) { $('acceso').hidden = false; $('tablero').hidden = true; $('clave').focus(); return; }
    throw err;
  }
  $('acceso').hidden = true;
  $('tablero').hidden = false;
  pintar();
  vivo();
  setInterval(vivo, 60_000);
  setInterval(foto, 2 * 60_000);
  // El celular y las pestañas de fondo congelan los relojes: al volver a la pantalla se refresca todo de inmediato.
  const alVolver = () => { if (document.visibilityState === 'visible') { vivo(); foto(); window.refrescarStats?.(); } };
  document.addEventListener('visibilitychange', alVolver);
  addEventListener('focus', alVolver);
  addEventListener('online', alVolver);
}

// Rodrigo, 13-nov-2026: "que se actualice SOLO el dashboard, siempre, siempre, siempre, sin que yo dé Command R".
// Cada 2 min vuelve a pedir la foto del sistema; si hay una versión nueva publicada (otro diseño o datos), recarga sola.
const VERSION = {v: null};
async function foto() {
  try {
    const nueva = await pedir('/api/estado');
    if (VERSION.v && nueva.version && nueva.version !== VERSION.v) return location.reload();
    VERSION.v = nueva.version || VERSION.v;
    FOTO = nueva;
    pintar();
  } catch (err) { if (err.acceso) location.reload(); }
}

async function vivo() {
  try { VIVO = await pedir('/api/vivo'); $('punto').classList.toggle('falla', Boolean(VIVO.errores?.length)); }
  catch { $('punto').classList.add('falla'); }
  pintar();
}

function pintar() {
  if (!FOTO) return;
  const e = FOTO.estado || {};
  const act = VIVO?.actualizado || e.generado_utc;
  $('actualizado').textContent = act ? `en vivo · ${new Date(act).toLocaleTimeString('es-MX', {timeZone: 'America/Mexico_City', hour: '2-digit', minute: '2-digit'})}` : '—';
  $('pie-datos').textContent = e.generado_utc ? `Datos del sistema: ${new Date(e.generado_utc).toLocaleString('es-MX', {timeZone: 'America/Mexico_City', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'})}` : '';
  estado(e.salud);
  const diario = diarioPorRed(e.serie_redes || []);
  redes(diario);
  grafica(diario.slice(-14));
  pintarTop(e.publicaciones || []);
  agenda(FOTO.calendario || []);
  tarea(FOTO.comentar_hoy, FOTO.pendientes);
  dinero(e.replicate, e.creditos_apps?.apps || {});
}

// ---------- estado ----------
function estado(salud) {
  const checks = (salud?.checks || []).filter((c) => !['Gasto', 'Créditos', 'Calendario'].includes(c.area));
  const malos = checks.filter((c) => c.estado !== 'ok').sort((a, b) => (a.estado === 'alerta' ? -1 : 1) - (b.estado === 'alerta' ? -1 : 1));
  const tono = malos.some((c) => c.estado === 'alerta') ? 'alerta' : malos.length ? 'aviso' : 'bien';
  const titulo = !salud ? 'Sin chequeo todavía' : tono === 'bien' ? 'Todo en orden' : `${malos.length} ${malos.length === 1 ? 'cosa' : 'cosas'} por atender`;
  const caja = $('estado');
  caja.replaceChildren(el('div', {className: 'estado-titulo'}, el('i', {style: `background:var(--${tono})`}), titulo));
  if (malos.length) {
    caja.append(el('ul', {}, ...malos.slice(0, 5).map((c) => el('li', {},
      el('i', {style: `background:var(--${c.estado === 'alerta' ? 'alerta' : 'aviso'})`}),
      el('span', {}, el('b', {textContent: `${c.area}. `}), c.detalle.replace(/:\s*[a-z_]+\.py.*$/i, ''))))));
  }
}

// ---------- vistas por día ----------
function diarioPorRed(serie) {
  return serie.map((d, i) => {
    const fila = {fecha: d.fecha};
    for (const r of REDES) {
      if (d[r.k] == null) continue;
      fila[r.k] = Math.max(0, d[r.k] - (i ? serie[i - 1][r.k] ?? 0 : 0));
    }
    return fila;
  }).slice(1);  // el primer día trae el acumulado de antes, no es "nuevo"
}

function suma(diario, k, desde, hasta) {
  const f = diario.filter((d) => d.fecha > desde && d.fecha <= hasta && d[k] != null);
  return f.length ? f.reduce((s, d) => s + d[k], 0) : null;
}

function redes(diario) {
  const hoy = diario.at(-1)?.fecha || hoyMx();
  const seg = VIVO?.seguidores || {};
  // Si /api/vivo aún no responde (o falla), la foto diaria de estadísticas (stats.js → ST) pone el número.
  const foto = (typeof ST !== 'undefined' && ST?.seguidores?.actual) || {};
  const seguidores = {yt: VIVO?.canal?.suscriptores ?? foto.yt, tt: seg.tt?.seguidores ?? foto.tt, ig: seg.ig?.seguidores ?? foto.ig, fb: seg.fb?.seguidores ?? foto.fb};
  const antes = {tt: seg.tt?.antes, ig: seg.ig?.antes, fb: seg.fb?.antes};
  $('redes').replaceChildren(...REDES.map((r) => {
    const ahora = suma(diario, r.k, sumarDias(hoy, -7), hoy);
    const previo = suma(diario, r.k, sumarDias(hoy, -14), sumarDias(hoy, -7));
    const cambio = ahora != null && previo ? Math.round(((ahora - previo) / previo) * 100) : null;
    const dif = seguidores[r.k] != null && antes[r.k] != null ? seguidores[r.k] - antes[r.k] : null;
    return el('div', {className: 'red', style: `--color:${color(r)}`},
      el('div', {className: 'red-nombre'}, el('i'), r.nombre),
      el('div', {className: 'red-num', textContent: corto(seguidores[r.k])}),
      el('div', {className: 'red-sub'}, r.k === 'yt' ? 'suscriptores' : 'seguidores', dif ? el('span', {className: dif > 0 ? 'sube' : 'baja', textContent: ` ${dif > 0 ? '+' : ''}${dif}`}) : null),
      el('div', {className: 'red-vistas'}, el('b', {textContent: corto(ahora)}), ' vistas',
        cambio != null ? el('span', {className: cambio >= 0 ? 'sube' : 'baja', textContent: ` ${cambio >= 0 ? '▲' : '▼'} ${Math.abs(cambio)}%`}) : null));
  }));
}

function grafica(dias) {
  const caja = $('grafica');
  $('leyenda').replaceChildren(...REDES.map((r) => el('span', {style: `--color:${color(r)}`}, el('i'), r.nombre)));
  if (dias.length < 2) { caja.replaceChildren(el('p', {className: 'vacio', textContent: 'Aparece con dos días medidos.', style: 'padding:16px'})); return; }
  const W = 680, H = 240, m = {t: 12, r: 44, b: 26, l: 40};
  const max = Math.max(10, ...dias.flatMap((d) => REDES.map((r) => d[r.k] || 0)));
  const paso = Math.pow(10, Math.floor(Math.log10(max))) * (max / Math.pow(10, Math.floor(Math.log10(max))) > 5 ? 2 : 1);
  const tope = Math.ceil(max / paso) * paso;
  const x = (i) => m.l + (i * (W - m.l - m.r)) / (dias.length - 1);
  const y = (v) => H - m.b - (v / tope) * (H - m.t - m.b);
  const s = svg('svg', {viewBox: `0 0 ${W} ${H}`});
  const eje = svg('g', {class: 'eje'});
  for (let v = 0; v <= tope; v += paso) {
    s.append(svg('line', {class: 'reja', x1: m.l, x2: W - m.r, y1: y(v), y2: y(v)}));
    const t = svg('text', {x: m.l - 8, y: y(v) + 4, 'text-anchor': 'end'}); t.textContent = corto(v); eje.append(t);
  }
  dias.forEach((d, i) => {
    if (i % Math.ceil(dias.length / 7) && i !== dias.length - 1) return;
    const t = svg('text', {x: x(i), y: H - 6, 'text-anchor': 'middle'});
    t.textContent = new Date(`${d.fecha}T12:00:00Z`).toLocaleDateString('es-MX', {day: 'numeric', month: 'short', timeZone: 'UTC'});
    eje.append(t);
  });
  s.append(eje);
  for (const r of REDES) {
    const pts = dias.map((d, i) => (d[r.k] == null ? null : [x(i), y(d[r.k])])).filter(Boolean);
    if (pts.length < 2) continue;
    s.append(svg('path', {class: 'linea', stroke: color(r), d: pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join('')}));
    const ult = pts.at(-1);
    s.append(svg('circle', {cx: ult[0], cy: ult[1], r: 4, fill: color(r), stroke: 'var(--superficie)', 'stroke-width': 2}));
  }
  const guia = svg('line', {class: 'guia', y1: m.t, y2: H - m.b, visibility: 'hidden'});
  s.append(guia);
  const zona = svg('rect', {x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: 'transparent'});
  s.append(zona);
  const tip = $('tip');
  const mover = (ev) => {
    const caja2 = s.getBoundingClientRect();
    const px = ((ev.clientX - caja2.left) / caja2.width) * W;
    const i = Math.max(0, Math.min(dias.length - 1, Math.round(((px - m.l) / (W - m.l - m.r)) * (dias.length - 1))));
    guia.setAttribute('x1', x(i)); guia.setAttribute('x2', x(i)); guia.setAttribute('visibility', 'visible');
    const d = dias[i];
    tip.replaceChildren(el('b', {textContent: new Date(`${d.fecha}T12:00:00Z`).toLocaleDateString('es-MX', {weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC'})}),
      ...REDES.filter((r) => d[r.k] != null).map((r) => el('div', {}, el('span', {}, el('i', {style: `--color:${color(r)}`}), r.nombre), el('span', {textContent: n0(d[r.k])}))));
    tip.hidden = false;
    const tx = Math.min(window.innerWidth - tip.offsetWidth - 8, ev.clientX + 14);
    tip.style.left = `${tx}px`; tip.style.top = `${ev.clientY - tip.offsetHeight - 12}px`;
  };
  zona.addEventListener('pointermove', mover);
  zona.addEventListener('pointerdown', mover);
  zona.addEventListener('pointerleave', () => { tip.hidden = true; guia.setAttribute('visibility', 'hidden'); });
  caja.replaceChildren(s);
  // tabla accesible
  $('tabla-vistas').replaceChildren(el('table', {},
    el('thead', {}, el('tr', {}, el('th', {textContent: 'Día'}), ...REDES.map((r) => el('th', {textContent: r.nombre})))),
    el('tbody', {}, ...[...dias].reverse().map((d) => el('tr', {}, el('td', {textContent: d.fecha.slice(5)}), ...REDES.map((r) => el('td', {textContent: n0(d[r.k])})))))));
}

// ---------- lo que funciona ----------
function pintarTop(pubs) {
  const vivoDe = (id) => VIVO?.porVideo?.[id];
  const filas = pubs.map((p) => {
    const g = p.ultimas_24h ? Object.values(p.ultimas_24h).reduce((a, b) => a + b, 0) : 0;
    const v = vivoDe(p.id);
    const porRed = {...p.por_red};
    if (v) for (const r of REDES) if (v[r.k]?.v != null) porRed[r.k] = Math.max(porRed[r.k] || 0, v[r.k].v);
    return {...p, gana: g, porRed, total: Object.values(porRed).reduce((a, b) => a + (b || 0), 0)};
  }).sort((a, b) => b.gana - a.gana || b.total - a.total).slice(0, 5);
  if (!filas.length) { $('top').replaceChildren(el('li', {className: 'vacio', textContent: 'Aparece con la primera medición.'})); return; }
  if ($('d-top')) $('d-top').textContent = `${sinEmoji(filas[0].titulo).slice(0, 34)}${sinEmoji(filas[0].titulo).length > 34 ? '…' : ''} +${corto(filas[0].gana)}`;
  $('top').replaceChildren(...filas.map((p, i) => el('li', {},
    el('span', {className: 'n', textContent: i + 1}),
    el('div', {}, el('div', {className: 'tipo', textContent: `${p.tipo || ''} ${p.id}`.trim()}), el('div', {className: 't', textContent: sinEmoji(p.titulo)})),
    el('div', {className: 'gana'}, `+${corto(p.gana)}`, el('small', {textContent: `${corto(p.total)} en total`})),
    el('div', {className: 'chips'}, ...REDES.filter((r) => p.porRed[r.k]).map((r) => el('span', {className: 'chip', style: `--color:${color(r)}`}, el('i'), corto(p.porRed[r.k])))))));
}

// ---------- hoy y mañana ----------
function agenda(cal) {
  const hoy = hoyMx(), manana = sumarDias(hoy, 1);
  const etiqueta = {video: 'Victoria hablando', carrusel: 'Carrusel', reel: 'Reel', facebook: 'Facebook', largo: 'Video largo', recorte: 'Short del video largo'};
  const dias = [hoy, manana].map((f) => {
    const items = cal.filter((c) => c.fecha === f).map((c) => {
      const horas = Object.values(c.horas || {}).sort();
      // 12-nov-2026: la hora de CADA red (antes solo la primera: c68 decía 13:00 y en Instagram sale a las 19:00)
      const porRed = REDES.filter((r) => c.horas?.[r.k]).sort((a, b) => c.horas[a.k].localeCompare(c.horas[b.k]))
        .map((r) => el('span', {className: 'chip', style: `--color:${color(r)}`}, el('i'), `${r.nombre} ${c.horas[r.k]}`));
      return {hora: horas[0] || '', porRed, que: `${etiqueta[c.tipo] || c.tipo} · ${sinEmoji((c.que || '').replace(/^[^«]*«/, '«').split('»')[0].replace('«', ''))}`};
    }).sort((a, b) => (a.hora || '99').localeCompare(b.hora || '99'));
    return el('div', {className: 'dia'},
      el('h3', {textContent: new Date(`${f}T12:00:00Z`).toLocaleDateString('es-MX', {weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC'})}),
      items.length ? el('ul', {}, ...items.map((x) => el('li', {}, el('span', {className: 'hora', textContent: x.hora || 'por programar'}), el('span', {className: 'que', textContent: x.que}),
        x.porRed.length ? el('div', {className: 'chips agenda-redes'}, ...x.porRed) : null)))
        : el('p', {className: 'vacio', textContent: 'La rutina de las 6:37 lo programa.'}));
  });
  $('agenda').replaceChildren(...dias);
  const nHoy = cal.filter((c) => c.fecha === hoy).length, nMan = cal.filter((c) => c.fecha === manana).length;
  if ($('d-agenda')) $('d-agenda').textContent = `hoy ${nHoy} · mañana ${nMan}`;
}

// ---------- tarea de hoy ----------
function tarea(c, pendientes) {
  // Rodrigo, 13-nov-2026: "ve cómo no se actualiza solo": al terminar Comenta hoy la sección se quedaba igual. Ahora,
  // cuando ya no queda nada de Comenta hoy, muestra lo siguiente que solo él puede hacer (contenido/pendientes_rodrigo.json).
  const vids = c?.videos || [];
  const hechos = new Set(JSON.parse(localStorage.getItem('comentados') || '[]'));
  const faltan = vids.filter((v) => !hechos.has(v.url));
  const listos = new Set(JSON.parse(localStorage.getItem('pendientes_hechos') || '[]'));
  const pend = (pendientes || []).filter((p) => !p.hecho && !listos.has(p.id));
  if (vids.length && faltan.length) {
    $('tarea-nota').textContent = `Comenta hoy · TikTok · ${vids.length - faltan.length} de ${vids.length}`;
    $('tarea').replaceChildren(...vids.map((v) => {
      const hecho = hechos.has(v.url);
      const copiar = el('button', {className: 'boton principal', type: 'button', textContent: 'Copiar'});
      copiar.onclick = async () => { await navigator.clipboard.writeText(v.comentario); copiar.textContent = 'Copiado'; setTimeout(() => (copiar.textContent = 'Copiar'), 1500); };
      const listo = el('button', {className: `boton${hecho ? ' hecho' : ''}`, type: 'button', textContent: hecho ? 'Hecho ✓' : 'Ya lo comenté'});
      listo.onclick = () => {
        const s = new Set(JSON.parse(localStorage.getItem('comentados') || '[]'));
        s.has(v.url) ? s.delete(v.url) : s.add(v.url);
        localStorage.setItem('comentados', JSON.stringify([...s]));
        tarea(c, pendientes);
      };
      return el('div', {className: 'comentario', style: hecho ? 'opacity:.55' : ''},
        el('div', {className: 'quien'}, el('b', {textContent: `@${v.autor}`}), ` · ${corto(v.vistas)} vistas`),
        el('p', {textContent: v.comentario}),
        el('div', {className: 'acciones'}, copiar, el('a', {className: 'boton', href: v.url, target: '_blank', rel: 'noopener', textContent: 'Abrir'}), listo));
    }));
    return;
  }
  const hechoHoy = vids.length ? `Comenta hoy ✓ ${vids.length} de ${vids.length}` : 'Comenta hoy: nada hoy';
  if (!pend.length) {
    $('tarea-nota').textContent = hechoHoy;
    $('tarea').replaceChildren(el('p', {className: 'vacio', textContent: 'Listo por hoy ✓ Mañana a las 6:37 llega lo nuevo.'}));
    return;
  }
  $('tarea-nota').textContent = `${hechoHoy} · siguiente: ${pend.length} pendiente${pend.length > 1 ? 's' : ''} tuyo${pend.length > 1 ? 's' : ''}`;
  $('tarea').replaceChildren(...pend.map((p) => {
    const ya = el('button', {className: 'boton principal', type: 'button', textContent: 'Ya lo hice'});
    ya.onclick = () => {
      const s = new Set(JSON.parse(localStorage.getItem('pendientes_hechos') || '[]'));
      s.add(p.id);
      localStorage.setItem('pendientes_hechos', JSON.stringify([...s]));
      tarea(c, pendientes);
    };
    return el('div', {className: 'comentario'},
      el('div', {className: 'quien'}, el('b', {textContent: 'Solo tú puedes'})),
      el('p', {textContent: p.texto}),
      el('div', {className: 'quien', textContent: p.como}),
      el('div', {className: 'acciones'}, ya));
  }));
}

// ---------- gasto y créditos ----------
function medidor(nombre, cifra, de, detalle, pct, tono) {
  return el('div', {className: 'medidor'},
    el('div', {className: 'arriba'}, el('span', {className: 'nombre', textContent: nombre})),
    el('div', {className: 'cifra'}, cifra, de ? el('small', {textContent: ` ${de}`}) : null),
    pct != null ? el('div', {className: 'barra'}, el('span', {style: `width:${Math.min(100, Math.max(2, pct))}%;${tono ? `background:var(--${tono})` : ''}`})) : null,
    el('div', {className: 'det', textContent: detalle}));
}

function dinero(rep, apps) {
  // 12-nov-2026: el gasto se lee como Rodrigo lo maneja: saldo estimado (recarga sola), presupuesto base y sus
  // autorizaciones escritas (config.json -> replicate.autorizaciones). Antes decía "$58.94 de $7" en rojo sin contexto.
  const caja = $('dinero');
  const items = [];
  const c = rep?.control;
  if (rep?.saldo_estimado_usd != null) {
    const rc = rep.recarga || {};
    const bajo = rc.umbral_usd && rep.saldo_estimado_usd <= rc.umbral_usd;
    items.push(medidor('Replicate · saldo estimado', usd(rep.saldo_estimado_usd), '',
      rc.monto_usd ? `Se recarga sola con $${rc.monto_usd} al bajar de $${rc.umbral_usd}${bajo ? ' · recarga próxima' : ''}` : 'Confirmar en replicate.com', null, null));
  }
  if (c) {
    const auts = rep.autorizaciones || [];
    const autorizado = auts.reduce((s, a) => s + (a.gastado_usd || 0), 0);
    const base = Math.max(0, c.semana_usd - autorizado);
    const ps = c.presupuesto_semanal_usd ? (base / c.presupuesto_semanal_usd) * 100 : null;
    items.push(medidor('Replicate · esta semana', usd(c.semana_usd), '',
      `${usd(autorizado)} autorizado por ti · ${usd(base)} fuera de autorizaciones (base $${c.presupuesto_semanal_usd}${ps >= 100 ? ', agotada: solo se gasta lo autorizado' : ''})`,
      ps, ps >= 100 ? 'aviso' : null));
    for (const a of auts.filter((x) => !x.cerrada && x.gastado_usd < x.tope_usd)) {
      const pct = (a.gastado_usd / a.tope_usd) * 100;
      items.push(medidor(`Autorizado · ${a.clave}`, usd(a.gastado_usd), `de $${a.tope_usd}`,
        `Quedan ${usd(a.tope_usd - a.gastado_usd)} · ${a.para.split(':')[0].replace(/\s*\([^)]*\)/g, '').trim()}`, pct, pct >= 90 ? 'aviso' : null));
    }
  }
  // Everygen, OpenArt y Higgsfield van en "Créditos de todo lo que usamos" (stats.js).
  caja.replaceChildren(...(items.length ? items : [el('p', {className: 'vacio', textContent: 'Sin datos de gasto todavía.'})]));
}

arrancar().catch((err) => { document.body.prepend(el('p', {className: 'error', style: 'padding:16px', textContent: `No pude cargar el panel: ${err.message}`})); });
