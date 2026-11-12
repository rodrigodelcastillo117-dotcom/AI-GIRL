// Batcueva (12-nov-2026): héroe con la foto de Victoria, reloj de CDMX, cinta de lo que sale, cuenta regresiva de la
// próxima misión y partículas. Usa los ayudantes y la foto del sistema de panel.js (FOTO, $, el, n0, sinEmoji).
(() => {
  const MX = 'America/Mexico_City';
  const ETQ = {video: 'Victoria hablando', carrusel: 'Carrusel', reel: 'Reel', facebook: 'Facebook', largo: 'Video largo', recorte: 'Short del largo', publer: 'Programado'};

  // Reloj
  const reloj = () => { const r = $('reloj'); if (r) r.textContent = `CDMX ${new Date().toLocaleTimeString('es-MX', {timeZone: MX, hour: '2-digit', minute: '2-digit', second: '2-digit'})}`; };
  reloj(); setInterval(reloj, 1000);

  // Hora de México de una fila del calendario → Date (México: UTC-6 todo el año desde 2022)
  const cuando = (fecha, hora) => new Date(`${fecha}T${hora}:00-06:00`);
  const titulo = (c) => sinEmoji((c.que || '').replace(/^[^«]*«/, '«').split('»')[0].replace('«', '')) || c.id;

  function proximas(cal) {
    const ahora = Date.now();
    const filas = [];
    for (const c of cal || []) {
      for (const [red, h] of Object.entries(c.horas || {})) {
        const t = cuando(c.fecha, h);
        if (t.getTime() > ahora) filas.push({t, red, c});
      }
    }
    return filas.sort((a, b) => a.t - b.t);
  }

  let objetivo = null;
  function cuenta() {
    const caja = $('cuenta');
    if (!caja || !objetivo) return;
    let s = Math.max(0, Math.floor((objetivo - Date.now()) / 1000));
    const partes = [['días', Math.floor(s / 86400)], ['hrs', Math.floor((s % 86400) / 3600)], ['min', Math.floor((s % 3600) / 60)], ['seg', s % 60]];
    caja.replaceChildren(...partes.map(([n, v]) => el('span', {}, el('b', {textContent: String(v).padStart(2, '0')}), el('small', {textContent: n}))));
    if (s === 0) setTimeout(pintarHeroe, 1500);
  }
  setInterval(cuenta, 1000);

  function pintarHeroe() {
    if (typeof FOTO === 'undefined' || !FOTO) return;
    const e = FOTO.estado || {};
    if (e.foto_perfil && !$('foto').firstChild) $('foto').append(el('img', {src: e.foto_perfil, alt: 'Victoria'}));
    const redes = (e.serie_redes || []).at(-1) || {};
    const total = ['tt', 'yt', 'ig', 'fb'].reduce((s, k) => s + (redes[k] || 0), 0);
    $('vistas-totales').textContent = total ? n0(total) : '—';
    const pubs = (e.serie_publicaciones || []).at(-1)?.v;
    const listosV = (FOTO.videos || []).filter((v) => v.estado === 'listo_para_publicar').length;
    const listosC = (FOTO.carruseles || []).filter((c) => c.estado === 'listo').length;
    $('lema').replaceChildren(el('b', {textContent: n0(pubs)}), ' publicaciones en redes · ', el('b', {textContent: n0(listosC)}), ' carruseles y ',
      el('b', {textContent: n0(listosV)}), ' videos listos para salir.');
    // próxima misión: lo siguiente programado (cualquier red)
    const prox = proximas(FOTO.calendario);
    if (prox.length) {
      const p = prox[0];
      objetivo = p.t.getTime();
      const mismas = prox.filter((x) => x.c === p.c).map((x) => ({tt: 'TikTok', yt: 'YouTube', ig: 'Instagram', fb: 'Facebook'})[x.red]);
      $('mision-que').textContent = `${ETQ[p.c.tipo] || p.c.tipo} · ${titulo(p.c)}`;
      $('mision-cuando').textContent = `${p.t.toLocaleString('es-MX', {timeZone: MX, weekday: 'long', hour: '2-digit', minute: '2-digit'})} · ${[...new Set(mismas)].join(', ')}`;
      cuenta();
    } else {
      $('cuenta').textContent = '—';
      $('mision-que').textContent = 'La rutina de las 6:37 programa lo siguiente';
      $('mision-cuando').textContent = '';
    }
    // cinta: lo que sale hoy y mañana, hora por hora
    const vistos = new Set();
    const items = prox.slice(0, 24).filter((x) => { const k = x.c.id + x.c.tipo + x.t.getTime(); if (vistos.has(k)) return false; vistos.add(k); return true; })
      .map((x) => el('span', {}, el('b', {textContent: x.t.toLocaleString('es-MX', {timeZone: MX, weekday: 'short', hour: '2-digit', minute: '2-digit'})}), ` · ${ETQ[x.c.tipo] || x.c.tipo} · ${titulo(x.c)}`));
    const cinta = $('cinta');
    if (items.length) cinta.replaceChildren(...items, ...items.map((n) => n.cloneNode(true)));
  }

  // Inclinación 3D de la foto con el mouse
  document.addEventListener('pointermove', (ev) => {
    const a = document.querySelector('.avatar');
    if (!a || ev.pointerType !== 'mouse') return;
    const r = a.getBoundingClientRect();
    const dx = (ev.clientX - (r.left + r.width / 2)) / window.innerWidth, dy = (ev.clientY - (r.top + r.height / 2)) / window.innerHeight;
    a.style.setProperty('--ry', `${(dx * 18).toFixed(2)}deg`); a.style.setProperty('--rx', `${(-dy * 18).toFixed(2)}deg`);
  });

  // Partículas (motas de polvo de la batcueva)
  const lienzo = $('particulas');
  if (lienzo && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const ctx = lienzo.getContext('2d');
    let W, H, motas;
    const tam = () => { W = lienzo.width = innerWidth; H = lienzo.height = innerHeight; motas = Array.from({length: Math.min(70, Math.floor(W / 18))}, () => ({x: Math.random() * W, y: Math.random() * H, r: Math.random() * 1.4 + .3, v: Math.random() * .25 + .05, o: Math.random() * .5 + .15, oro: Math.random() < .3})); };
    tam(); addEventListener('resize', tam);
    const paso = () => {
      ctx.clearRect(0, 0, W, H);
      for (const m of motas) {
        m.y -= m.v; if (m.y < -4) { m.y = H + 4; m.x = Math.random() * W; }
        ctx.beginPath(); ctx.arc(m.x, m.y, m.r, 0, 6.283);
        ctx.fillStyle = m.oro ? `rgba(245,197,66,${m.o})` : `rgba(73,214,236,${m.o})`; ctx.fill();
      }
      requestAnimationFrame(paso);
    };
    paso();
  }

  // Arranca cuando panel.js ya cargó la foto del sistema; se repinta con cada refresco.
  const espera = setInterval(() => {
    if (typeof FOTO !== 'undefined' && FOTO && !$('tablero').hidden) { clearInterval(espera); pintarHeroe(); setInterval(pintarHeroe, 60_000); }
  }, 300);
})();
