// Respuestas rápidas (8-nov-2026, docs/PERSONAJE.md): Victoria promete "Te contesto a todos" en cada post.
// En YouTube e Instagram contesta Claude solo (comentarios.py, comentarios_ig.py, cada 2 h); en TikTok contesta Rodrigo desde aquí (su API no deja responder).
(() => {
  const UMA_2026 = 117.31; // INEGI, vigente desde el 1-feb-2026: tope exento de ISR = 30 UMA
  const EXENTO = +(UMA_2026 * 30).toFixed(2);
  const pesos = (n) => '$' + n.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const PLANTILLAS = [
    ['DEUDA', 'Eso es de CEO. Primero la deuda más cara, casi siempre la tarjeta: cada peso que le quitas ahí te rinde más que cualquier regalo. Capital aprueba 🐾'],
    ['AHORRO', 'Así se hace. Si todavía no tienes fondo de emergencia, empieza ahí: de 3 a 6 meses de tus gastos, en una cuenta aparte. 🐾'],
    ['REGALOS / GUSTO', 'Sin culpa, pero con tope: decide la cifra antes de salir a comprar. Y si traes deuda de tarjeta, primero ella 😉'],
    ['RENUNCIA', 'Si renuncias te toca tu finiquito: días trabajados sin pagar más lo proporcional de aguinaldo, vacaciones y prima vacacional. Revísalo antes de firmar; PROFEDET te asesora gratis.'],
    ['DESPIDO', 'Si te corrieron sin causa, además del finiquito puedes reclamar 3 meses de salario (y prima de antigüedad si eras de planta). Tienes 2 meses para reclamar: PROFEDET te asesora gratis.'],
    ['SÍ / YA', '¡Eso! 🙌 Guárdalo para cuando alguien te pregunte, y mándaselo a quien todavía no lo sabe.'],
    ['NO / NUNCA', 'Hoy es buen día para empezar 😉 Guárdalo y revísalo esta semana; cualquier duda me escribes aquí.'],
    ['UN NÚMERO', 'Gracias por contarme. Con ese dato ya sabes dónde estás; el siguiente paso está en el post 🐾'],
    ['COMENTARON SU PROFESIÓN', '¡Anotada! 📝 La reviso con datos oficiales en una de las siguientes partes de la serie. Sígueme para que no te la pierdas 🐾'],
    ['TE HACEN UNA PREGUNTA', 'Muy buena pregunta. Te contesto con un post esta semana: sígueme para que no te lo pierdas.'],
    ['PIDEN DÓNDE INVERTIR', 'No doy recomendaciones de inversión: te explico cómo funciona cada cosa para que tú decidas con datos.'],
  ];

  const caja = document.getElementById('respuestas');
  if (!caja) return;

  const copiar = async (texto, boton) => {
    try { await navigator.clipboard.writeText(texto); } catch (e) {
      const t = document.createElement('textarea'); t.value = texto; document.body.appendChild(t); t.select();
      try { document.execCommand('copy'); } catch (e2) { /* sin portapapeles */ } t.remove();
    }
    const antes = boton.textContent; boton.textContent = 'Copiado'; setTimeout(() => { boton.textContent = antes; }, 1400);
  };

  const fila = (etiqueta, texto) => {
    const d = document.createElement('div'); d.className = 'resp';
    const b = document.createElement('button'); b.type = 'button'; b.className = 'resp-copiar'; b.textContent = 'Copiar';
    const e = document.createElement('div'); e.className = 'resp-etq'; e.textContent = etiqueta;
    const p = document.createElement('p'); p.textContent = texto;
    b.addEventListener('click', () => copiar(p.textContent, b));
    d.append(e, p, b); return d;
  };

  // Calculadora: "Comenta tu sueldo y te digo cuánto aguinaldo te toca".
  const calc = document.createElement('div'); calc.className = 'resp resp-calc';
  calc.innerHTML = '<div class="resp-etq">COMENTARON SU SUELDO</div>' +
    '<label>Sueldo mensual <input id="r-sueldo" inputmode="decimal" placeholder="15000"></label>' +
    '<label>Días trabajados en el año <input id="r-dias" inputmode="numeric" placeholder="365"></label>' +
    '<p id="r-texto">Escribe el sueldo que comentaron.</p>';
  const bc = document.createElement('button'); bc.type = 'button'; bc.className = 'resp-copiar'; bc.textContent = 'Copiar';
  bc.addEventListener('click', () => copiar(document.getElementById('r-texto').textContent, bc));
  calc.append(bc);
  caja.append(calc);
  const actualizar = () => {
    const s = parseFloat(String(document.getElementById('r-sueldo').value).replace(/[^\d.]/g, ''));
    let dias = parseInt(document.getElementById('r-dias').value, 10);
    if (!s) { document.getElementById('r-texto').textContent = 'Escribe el sueldo que comentaron.'; return; }
    dias = dias > 0 && dias < 365 ? dias : 365;
    const ag = (s / 30) * 15 * (dias / 365);
    const parte = dias < 365 ? ` por ${dias} días trabajados (la parte proporcional)` : '';
    document.getElementById('r-texto').textContent =
      `Con ${pesos(s)} al mes te tocan mínimo ${pesos(ag)} brutos de aguinaldo${parte}: 15 días de salario. ` +
      `Los primeros ${pesos(EXENTO)} van sin ISR. Te lo deben pagar antes del 20 de diciembre 🔖 ` +
      `Y tu sueldo, así lo repartiría yo (mi regla 50/30/20): ${pesos(s * 0.5)} a lo necesario, ${pesos(s * 0.3)} a gustos ` +
      `y ${pesos(s * 0.2)} a ahorro y deudas. Capital ya apartó lo suyo 🐾`;
  };
  calc.addEventListener('input', actualizar);

  PLANTILLAS.forEach(([e, t]) => caja.append(fila(e, t)));
})();
