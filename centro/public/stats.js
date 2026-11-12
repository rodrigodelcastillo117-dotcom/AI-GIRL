// Estadísticas del panel (12-nov-2026). Lee /api/estadisticas (scripts/estadisticas.py). Usa los ayudantes de
// panel.js ($, el, svg, REDES, color, n0, corto, usd, sinEmoji): se carga después de él.
// Rodrigo: "lo que no es ESENCIAL, SIEMPRE CERRADO": las secciones plegadas cargan cerradas y su línea de título dice el
// dato principal. Con pocas publicaciones medidas, cada "mejor" lleva su n y no se corona nada con n < 2.
let ST = null;
const RED_DE = Object.fromEntries(REDES.map((r) => [r.k, r]));
const pct = (n) => (n == null ? '—' : `${n > 0 ? '+' : ''}${n}%`);
const firmado = (n) => (n == null ? '—' : `${n > 0 ? '+' : ''}${n0(n)}`);
const fechaCorta = (f) => new Date(`${f}T12:00:00Z`).toLocaleDateString('es-MX', {day: 'numeric', month: 'short', timeZone: 'UTC'});
const PAISES = {MX: 'México', US: 'Estados Unidos', AR: 'Argentina', ES: 'España', CO: 'Colombia', PE: 'Perú', CL: 'Chile', GT: 'Guatemala', EC: 'Ecuador', VE: 'Venezuela'};

async function estadisticas() {
  try {
    const r = await fetch('/api/estadisticas', {credentials: 'same-origin'});
    if (!r.ok) return;
    ST = await r.json();
  } catch { return; }
  if (!ST || !ST.generado_utc) return;
  for (const f of [kpis, seguidores, horas, temas, comparativas, youtube, dinero2, creditos, tablaPubs]) {
    try { f(); } catch (e) { console.error(f.name, e); }
  }
}

// ---------- piezas ----------
function tooltip(objetivo, filas) {
  const tip = $('tip');
  const mostrar = (ev) => {
    tip.replaceChildren(...filas());
    tip.hidden = false;
    const x = Math.min(window.innerWidth - tip.offsetWidth - 8, ev.clientX + 14);
    tip.style.left = `${Math.max(8, x)}px`; tip.style.top = `${Math.max(8, ev.clientY - tip.offsetHeight - 12)}px`;
  };
  objetivo.addEventListener('pointermove', mostrar);
  objetivo.addEventListener('pointerdown', mostrar);
  objetivo.addEventListener('pointerleave', () => { tip.hidden = true; });
}

// Barras verticales (una serie o apiladas). datos: [{etq, partes: [{v, color, nombre}]}]
function barras(caja, datos, {alto = 150, formato = n0} = {}) {
  if (!datos.length) { caja.replaceChildren(el('p', {className: 'vacio', textContent: 'Sin datos todavía.', style: 'padding:12px'})); return; }
  // El ancho del dibujo sigue al de la caja: en el celular la letra no se encoge a 5 px.
  const W = Math.max(300, caja.clientWidth || (window.innerWidth < 600 ? window.innerWidth - 40 : 680)), H = alto, m = {t: 10, r: 8, b: 22, l: 40};
  const max = Math.max(1e-9, ...datos.map((d) => d.partes.reduce((s, p) => s + Math.max(0, p.v || 0), 0)));
  const min = Math.min(0, ...datos.flatMap((d) => d.partes.map((p) => p.v || 0)));
  const y = (v) => m.t + ((max - v) / (max - min || 1)) * (H - m.t - m.b);
  const paso = (W - m.l - m.r) / datos.length;
  const ancho = Math.max(2, Math.min(26, paso - 3));
  const s = svg('svg', {viewBox: `0 0 ${W} ${H}`});
  for (const v of [max, max / 2, 0]) {
    s.append(svg('line', {class: 'reja', x1: m.l, x2: W - m.r, y1: y(v), y2: y(v)}));
    const t = svg('text', {x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end', class: 'etq'}); t.textContent = formato(v); s.append(t);
  }
  if (min < 0) {
    const t = svg('text', {x: m.l - 6, y: y(min) + 4, 'text-anchor': 'end', class: 'etq'}); t.textContent = formato(min); s.append(t);
  }
  datos.forEach((d, i) => {
    const cx = m.l + paso * i + paso / 2;
    let base = 0;
    const g = svg('g');
    d.partes.forEach((p, j) => {
      const v = p.v || 0;
      if (!v) return;
      const y0 = v >= 0 ? y(base + v) : y(0), y1 = v >= 0 ? y(base) : y(v);
      const arriba = j === d.partes.length - 1 || v < 0;
      g.append(svg('rect', {x: cx - ancho / 2, y: y0 + (j ? 1 : 0), width: ancho, height: Math.max(1, y1 - y0 - (j ? 1 : 0)), rx: arriba ? Math.min(4, ancho / 2) : 0, fill: p.color}));
      if (v >= 0) base += v;
    });
    s.append(g);
    const cada = Math.ceil(datos.length / 8);
    if ((i % cada === 0 && datos.length - 1 - i >= cada) || i === datos.length - 1) {
      const t = svg('text', {x: cx, y: H - 6, 'text-anchor': 'middle', class: 'etq'}); t.textContent = d.etq; s.append(t);
    }
    const zona = svg('rect', {x: cx - paso / 2, y: m.t, width: paso, height: H - m.t - m.b, fill: 'transparent'});
    tooltip(zona, () => [el('b', {textContent: d.tip || d.etq}), ...d.partes.map((p) => el('div', {}, el('span', {}, el('i', {style: `--color:${p.color}`}), p.nombre || ''), el('span', {textContent: formato(p.v)})))]);
    s.append(zona);
  });
  caja.replaceChildren(s);
}

// Barras horizontales en HTML: filas [{etq, v, texto, color, mejor, nota}]
function hbarras(caja, filas, {color: c = 'var(--acento)'} = {}) {
  if (!filas.length) { caja.replaceChildren(el('p', {className: 'vacio', textContent: 'Sin datos todavía.'})); return; }
  const max = Math.max(1e-9, ...filas.map((f) => f.v || 0));
  caja.replaceChildren(...filas.map((f) => el('div', {className: `hb${f.mejor ? ' mejor' : ''}`},
    el('span', {className: 'hb-etq', textContent: f.etq}),
    el('span', {className: 'hb-pista'}, el('span', {className: 'hb-barra', style: `width:${Math.max(2, ((f.v || 0) / max) * 100)}%;background:${f.color || c}`})),
    el('span', {className: 'hb-val'}, f.texto ?? n0(f.v), f.nota ? el('small', {textContent: ` ${f.nota}`}) : null))));
}

function tabla(caja, cabeza, filas, {ordenable = false} = {}) {
  let orden = null;
  const pintar = () => {
    const datos = [...filas];
    if (orden) datos.sort((a, b) => ((b[orden.i]?.v ?? b[orden.i]) > (a[orden.i]?.v ?? a[orden.i]) ? 1 : -1) * orden.dir);
    const t = el('table', {className: 'tabla'},
      el('thead', {}, el('tr', {}, ...cabeza.map((h, i) => {
        const th = el('th', {textContent: h + (orden?.i === i ? (orden.dir > 0 ? ' ↓' : ' ↑') : '')});
        if (ordenable) { th.style.cursor = 'pointer'; th.onclick = () => { orden = {i, dir: orden?.i === i ? -orden.dir : 1}; pintar(); }; }
        return th;
      }))),
      el('tbody', {}, ...datos.map((f) => el('tr', {}, ...f.map((c) => (c instanceof Node ? el('td', {}, c) : el('td', {textContent: c?.t ?? c ?? '—'})))))));
    caja.replaceChildren(t);
  };
  pintar();
}

// ---------- cifras clave ----------
function kpis() {
  const sem = ST.semana_vs_semana?.total || {};
  const seg = ST.seguidores?.actual || {};
  const totalSeg = REDES.reduce((s, r) => s + (seg[r.k] || 0), 0);
  const ganados = seguidoresGanados7();
  const c = ST.gasto?.control || {};
  const t = ST.totales || {};
  const tiles = [
    ['Vistas · 7 días', corto(sem.esta), sem.cambio_pct != null ? el('span', {className: sem.cambio_pct >= 0 ? 'sube' : 'baja', textContent: `${sem.cambio_pct >= 0 ? '▲' : '▼'} ${Math.abs(sem.cambio_pct)}% vs semana anterior`}) : ''],
    ['Seguidores en total', n0(totalSeg), ganados != null ? el('span', {className: ganados >= 0 ? 'sube' : 'baja', textContent: `${firmado(ganados)} en 7 días`}) : 'ganados: se mide desde hoy'],
    ['Vistas por publicación', n0(t.mediana_por_publicacion), `mediana de ${t.publicaciones_medidas || 0} publicaciones`],
    ['Interacción', t.interaccion_mediana_pct != null ? `${t.interaccion_mediana_pct}%` : '—', 'likes + comentarios + compartidos / vistas'],
    ['Gasto · esta semana', usd(c.semana_usd), `mes ${usd(c.mes_usd)} · Replicate`],
    ['Saldo Replicate', usd(ST.gasto?.saldo_estimado_usd), 'estimado · se recarga solo'],
  ];
  $('kpis').replaceChildren(...tiles.map(([n, v, d]) => el('div', {className: 'kpi'}, el('div', {className: 'kpi-n', textContent: n}), el('div', {className: 'kpi-v', textContent: v}), el('div', {className: 'kpi-d'}, d))));
}

function seguidoresGanados7() {
  // YouTube: YouTube Analytics (diario real). TikTok/Instagram/Facebook: última semana de Publer.
  let total = 0, alguno = false;
  const yt = (ST.youtube?.dias || []).slice(-7);
  if (yt.length) { total += yt.reduce((s, d) => s + d.subs_ganados - d.subs_perdidos, 0); alguno = true; }
  for (const r of ['tt', 'ig', 'fb']) {
    const w = ST.seguidores?.semanal?.[r] || [];
    if (w.length >= 2) { total += w.at(-1).valor - w.at(-2).valor; alguno = true; }
  }
  return alguno ? total : null;
}

// ---------- seguidores ganados ----------
function seguidores() {
  const S = ST.seguidores || {};
  const diario = S.diario || [];
  const cajas = REDES.map((r) => {
    let datos = [], etiqueta = '', ganados = null;
    if (r.k === 'yt' && ST.youtube?.dias?.length) {
      const dias = ST.youtube.dias.slice(-21);
      datos = dias.map((d) => ({etq: fechaCorta(d.fecha), tip: fechaCorta(d.fecha), partes: [{v: d.subs_ganados - d.subs_perdidos, color: color(r), nombre: 'Netos'}]}));
      ganados = dias.slice(-7).reduce((s, d) => s + d.subs_ganados - d.subs_perdidos, 0);
      etiqueta = 'por día · YouTube Analytics (2-3 días de atraso)';
    } else if (diario.filter((d) => d.ganados?.[r.k] != null).length >= 7) {
      const dias = diario.filter((d) => d.ganados?.[r.k] != null).slice(-21);
      datos = dias.map((d) => ({etq: fechaCorta(d.fecha), partes: [{v: d.ganados[r.k], color: color(r), nombre: 'Ganados'}]}));
      ganados = dias.slice(-7).reduce((s, d) => s + d.ganados[r.k], 0);
      etiqueta = 'por día';
    } else {
      const w = S.semanal?.[r.k] || [];
      datos = w.slice(1).map((x, i) => ({etq: fechaCorta(x.semana), tip: `Semana del ${fechaCorta(x.semana)}`, partes: [{v: x.valor - w[i].valor, color: color(r), nombre: 'Ganados'}]}));
      ganados = w.length >= 2 ? w.at(-1).valor - w.at(-2).valor : null;
      etiqueta = 'por semana (diario desde el 12-nov)';
    }
    const caja = el('div', {className: 'mini-graf'});
    caja.style.minHeight = '1px';
    const tarjeta = el('div', {className: 'multiple', style: `--color:${color(r)}`},
      el('div', {className: 'm-cabeza'}, el('span', {className: 'red-nombre'}, el('i'), r.nombre), el('b', {className: ganados > 0 ? 'sube' : ganados < 0 ? 'baja' : '', textContent: ganados == null ? '—' : firmado(ganados)})),
      el('div', {className: 'm-nota', textContent: `${S.actual?.[r.k] != null ? n0(S.actual[r.k]) + ' en total · ' : ''}${etiqueta}`}), caja);
    tarjeta.pintar = () => barras(caja, datos, {alto: 110});
    return tarjeta;
  });
  $('seguidores').replaceChildren(...cajas);
  cajas.forEach((t) => t.pintar());  // ya en la página: miden su ancho real
}

// ---------- mejores días y horas ----------
function mejorDe(lista, clave) {
  const validos = lista.filter((x) => x.n >= 2);
  return validos.length ? validos.reduce((a, b) => (b.mediana > a.mediana ? b : a))[clave] : null;
}

function horas() {
  const M = ST.mejores?.por_red || {};
  let actual = 'tt';
  const pintar = () => {
    const d = M[actual] || {dias: [], horas: []};
    const r = RED_DE[actual];
    const mejorDia = mejorDe(d.dias, 'dia'), mejorHora = mejorDe(d.horas, 'hora');
    hbarras($('g-dias'), d.dias.map((x) => ({etq: x.dia, v: x.mediana, texto: n0(x.mediana), nota: `n=${x.n}`, mejor: x.dia === mejorDia, color: color(r)})));
    hbarras($('g-horas'), d.horas.map((x) => ({etq: `${String(x.hora).padStart(2, '0')}:00`, v: x.mediana, texto: n0(x.mediana), nota: `n=${x.n}`, mejor: x.hora === mejorHora, color: color(r)})));
    const n = d.dias.reduce((s, x) => s + x.n, 0);
    $('n-horas').textContent = `Vistas por publicación (mediana) en ${r.nombre}, solo publicaciones con 24 h o más · ${n} medidas. Marcado en oro: el mejor con al menos 2 publicaciones. ${n < 20 ? 'Con tan pocas publicaciones es señal débil: la prueba de horarios sigue corriendo.' : ''}`;
    $('pest-horas').querySelectorAll('button').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.red === actual)));
  };
  $('pest-horas').replaceChildren(...REDES.map((r) => {
    const b = el('button', {type: 'button', role: 'tab', textContent: r.nombre, className: 'pestana'});
    b.dataset.red = r.k;
    b.onclick = () => { actual = r.k; pintar(); };
    return b;
  }));
  pintar();
  const tt = M.tt || {dias: [], horas: []};
  const md = mejorDe(tt.dias, 'dia'), mh = mejorDe(tt.horas, 'hora');
  $('d-horas').textContent = md || mh != null ? `TikTok: ${md || '—'}${mh != null ? ` · ${String(mh).padStart(2, '0')}:00` : ''}` : 'falta medir';
}

// ---------- temas ----------
function temas() {
  const t = ST.mejores?.temas || [];
  const conN = t.filter((x) => x.n >= 3);
  const mejor = conN.length ? conN.reduce((a, b) => (b.mediana > a.mediana ? b : a)) : null;
  hbarras($('g-temas'), t.map((x) => ({etq: x.tema, v: x.mediana, texto: n0(x.mediana), nota: `n=${x.n}`, mejor: mejor && x.tema === mejor.tema})));
  $('d-temas').textContent = mejor ? `${mejor.tema} · ${n0(mejor.mediana)} por publicación` : '';
}

// ---------- comparativas ----------
function comparativas() {
  const s = ST.semana_vs_semana || {};
  const filas = [...REDES.map((r) => [r.nombre, r.k]), ['Total', 'total']].filter(([, k]) => s[k]).map(([n, k]) => {
    const c = s[k].cambio_pct;
    return [n, n0(s[k].esta), n0(s[k].anterior), el('span', {className: c == null ? '' : c >= 0 ? 'sube' : 'baja', textContent: c == null ? 'nuevo' : `${c >= 0 ? '▲' : '▼'} ${Math.abs(c)}%`})];
  });
  tabla($('c-semana'), ['Red', 'Esta semana', 'Anterior', 'Cambio'], filas);
  const F = ST.mejores?.formatos || {};
  tabla($('c-formato'), ['Formato', ...REDES.map((r) => r.nombre)], Object.entries(F).map(([fmt, porRed]) => [fmt, ...REDES.map((r) => (porRed[r.k] ? `${n0(porRed[r.k].mediana)} · n=${porRed[r.k].n}` : '—'))]));
  const total = REDES.reduce((a, r) => a + (s[r.k]?.esta || 0), 0);
  $('c-reparto').replaceChildren(
    el('div', {className: 'reparto'}, ...REDES.filter((r) => s[r.k]?.esta).map((r) => el('span', {style: `width:${(s[r.k].esta / total) * 100}%;background:${color(r)}`, title: `${r.nombre} ${Math.round((s[r.k].esta / total) * 100)}%`}))),
    el('div', {className: 'leyenda', style: 'margin-top:8px'}, ...REDES.filter((r) => s[r.k]?.esta).map((r) => el('span', {style: `--color:${color(r)}`}, el('i', {style: 'height:8px;width:8px'}), `${r.nombre} ${Math.round((s[r.k].esta / total) * 100)}%`))));
  // la frase que importa: qué formato rinde dónde
  const v = F['Victoria hablando'], c = F.Carrusel;
  const frase = [];
  if (v?.yt && c?.yt) frase.push(`YouTube: Victoria hablando ${(v.yt.mediana / Math.max(1, c.yt.mediana)).toFixed(1)}× un carrusel`);
  if (v?.tt && c?.tt) frase.push(`TikTok: carrusel ${(c.tt.mediana / Math.max(1, v.tt.mediana)).toFixed(1)}× Victoria`);
  $('d-comp').textContent = frase.join(' · ') || (s.total?.cambio_pct != null ? `total ${pct(s.total.cambio_pct)} vs semana anterior` : '');
}

// ---------- YouTube ----------
function youtube() {
  const Y = ST.youtube;
  if (!Y) { $('d-yt').textContent = 'sin datos'; return; }
  const dias = Y.dias.slice(-30);
  const yt = RED_DE.yt;
  barras($('y-minutos'), dias.map((d) => ({etq: fechaCorta(d.fecha), partes: [{v: d.minutos, color: color(yt), nombre: 'Minutos'}]})), {alto: 140});
  const totF = Y.fuentes.reduce((s, f) => s + f.vistas, 0) || 1;
  hbarras($('y-fuentes'), Y.fuentes.slice(0, 6).map((f) => ({etq: f.fuente, v: f.vistas, texto: `${Math.round((f.vistas / totF) * 100)}%`, color: color(yt)})));
  const totP = Y.paises.reduce((s, f) => s + f.vistas, 0) || 1;
  hbarras($('y-paises'), Y.paises.map((p) => ({etq: PAISES[p.pais] || p.pais, v: p.vistas, texto: n0(p.vistas), color: color(yt)})));
  const sexo = {male: 'hombres', female: 'mujeres', user_specified: 'otro'};
  hbarras($('y-edades'), (Y.edades || []).map((e) => ({...e, edad: e.edad.replace(/–$/, '+')})).filter((e) => e.pct >= 1).sort((a, b) => b.pct - a.pct).slice(0, 8).map((e) => ({etq: `${e.edad} · ${sexo[e.genero] || e.genero}`, v: e.pct, texto: `${e.pct}%`, color: color(yt)})));
  const min = dias.reduce((s, d) => s + d.minutos, 0), subs = dias.reduce((s, d) => s + d.subs_ganados - d.subs_perdidos, 0);
  $('d-yt').textContent = `${n0(min)} min vistos · ${firmado(subs)} suscriptores (30 días)`;
  const busq = Y.fuentes.find((f) => f.fuente.startsWith('Búsqueda'));
  $('n-yt').textContent = `${Y.nota}${busq ? ` La búsqueda trae el ${Math.round((busq.vistas / totF) * 100)}% de las vistas: los títulos con palabra clave sí sirven.` : ''}`;
}

// ---------- dinero ----------
function dinero2() {
  const G = ST.gasto || {};
  const dias = (G.por_dia || []).slice(-30);
  barras($('g-gasto'), dias.map((d) => ({etq: fechaCorta(d.fecha), partes: [{v: d.victoria, color: 'var(--acento)', nombre: 'Victoria'}, {v: d.otro, color: 'var(--tenue)', nombre: 'El espacio'}]})), {alto: 150, formato: (v) => (!v ? '$0' : `$${Number(v).toFixed(v >= 10 ? 0 : 2)}`)});
  hbarras($('g-modelos'), (G.por_modelo_mes || []).map((m) => ({etq: m.modelo, v: m.usd, texto: usd(m.usd)})));
  const c = G.control || {};
  $('d-dinero').textContent = `semana ${usd(c.semana_usd)} · mes ${usd(c.mes_usd)} · saldo ${usd(G.saldo_estimado_usd)}`;
}

// ---------- créditos ----------
function creditos() {
  const items = (ST.creditos || []).map((a) => medidor(a.nombre, a.creditos == null ? '—' : Number.isInteger(a.creditos) ? n0(a.creditos) : String(a.creditos), a.mensual ? `de ${a.mensual} al mes` : 'créditos',
    [a.plan, a.uso].filter(Boolean).join(' · '), a.mensual ? (a.creditos / a.mensual) * 100 : null, null));
  const G = ST.gasto || {};
  items.unshift(medidor('Replicate', usd(G.saldo_estimado_usd), 'saldo estimado', 'Pago por uso · se recarga sola', null, null));
  $('creditos').replaceChildren(...items);
  $('d-creditos').textContent = (ST.creditos || []).map((a) => `${a.nombre.split(' ')[0]} ${a.creditos ?? '—'}${a.mensual ? `/${a.mensual}` : ''}`).join(' · ');
}

// ---------- todas las publicaciones ----------
function tablaPubs() {
  const P = ST.publicaciones || [];
  tabla($('t-pubs'), ['Publicación', 'Formato', 'Tema', ...REDES.map((r) => r.nombre), 'Total', 'Interacción'],
    P.map((p) => [{t: `${p.id} · ${sinEmoji(p.titulo)}`, v: p.id}, p.formato, p.tema, ...REDES.map((r) => ({t: p.redes[r.k] ? n0(p.redes[r.k].v) : '—', v: p.redes[r.k]?.v ?? -1})), {t: n0(p.total), v: p.total}, {t: `${p.interaccion}%`, v: p.interaccion}]),
    {ordenable: true});
  $('d-pubs').textContent = `${P.length} medidas · mediana ${n0(ST.totales?.mediana_por_publicacion)} vistas`;
}

// Siempre cerrado al cargar (también si el navegador restaura el estado al volver atrás).
window.addEventListener('pageshow', () => document.querySelectorAll('details.plegable').forEach((d) => { d.open = false; }));
// Arranca cuando panel.js ya mostró el tablero (después del acceso).
const espera = setInterval(() => { if (!$('tablero').hidden) { clearInterval(espera); estadisticas(); } }, 300);
