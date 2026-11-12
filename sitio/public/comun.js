// Datos y ayudas compartidas por la página y las calculadoras de Victoria.
// pago: enlace de pago de Hotmart. precio: lo que el comprador ve en México (precio + IVA).
const VICTORIA = {
  pago: 'https://pay.hotmart.com/T108246040P',
  precio: '$231.76 MXN',
  notaPrecio: 'IVA incluido · pago único',
  garantia: 'Garantía de 7 días: si no te sirve, te regresan tu dinero. Pago seguro con Hotmart: tarjeta, Mercado Pago o PayPal.',
};

// De qué red llegó la persona (?ref=yt|ig|tt|guia): viaja a Hotmart como src para saber qué vende.
const REF = (() => {
  try { return new URLSearchParams(location.search).get('ref') || 'directo'; } catch { return 'directo'; }
})();

const crear = (tag, props = {}, ...hijos) => { const el = Object.assign(document.createElement(tag), props); el.append(...hijos); return el; };

const pesos = (n, decimales = 0) => (Number.isFinite(n) ? n : 0).toLocaleString('es-MX', {
  style: 'currency', currency: 'MXN', minimumFractionDigits: decimales, maximumFractionDigits: decimales,
});

// Lee un campo numérico aceptando "15,000" o "15000.50"; vacío o inválido = 0.
const numero = (id) => {
  const valor = parseFloat(String(document.getElementById(id)?.value || '').replace(/[,\s$]/g, ''));
  return Number.isFinite(valor) ? valor : 0;
};

function enlacePago(origen) {
  const src = origen ? `${REF}-${origen}` : REF;
  // src y sck con el mismo valor: Hotmart reporta el origen en uno u otro (la API lo da como source_sck).
  return `${VICTORIA.pago}${VICTORIA.pago.includes('?') ? '&' : '?'}src=${encodeURIComponent(src)}&sck=${encodeURIComponent(src)}`;
}

// Bloque de venta de la plantilla, con el precio real y la garantía.
function bloqueVenta(contenedor, origen) {
  if (!contenedor) return;
  contenedor.replaceChildren(
    crear('div', {className: 'precio', textContent: VICTORIA.precio}),
    crear('p', {className: 'letra-chica', textContent: VICTORIA.notaPrecio}),
    crear('a', {className: 'boton', href: enlacePago(origen), textContent: 'Quiero la plantilla'}),
    crear('p', {className: 'letra-chica', textContent: VICTORIA.garantia}));
}

// Recalcula cada vez que cambia un campo del formulario.
function alCambiar(formulario, calcular) {
  const f = document.getElementById(formulario);
  f.addEventListener('input', calcular);
  f.addEventListener('change', calcular);
  f.addEventListener('submit', (e) => { e.preventDefault(); calcular(); });
  calcular();
}

// "Victoria revisa tus números" (12-nov-2026; sitio/api/diagnostico.js). Se agrega solo al final de .resultado de la
// calculadora: manda lo que la persona escribió (etiqueta: valor de cada campo) y el texto del resultado. 1 gratis al
// día; con el código del Kit CEO, sin límite (se guarda en este navegador). Solo aparece si la función está activa.
function victoriaIA(calculadora) {
  const res = document.querySelector('.resultado');
  const form = document.getElementById('calculadora');
  if (!res || !form) return;
  let codigo = '';
  try { codigo = localStorage.getItem('kit_codigo') || ''; } catch (e) {}
  const salida = crear('p', {className: 'nota', style: 'white-space: pre-line; margin-top: 10px'});
  const preo = crear('textarea', {maxLength: 300, rows: 2, placeholder: 'Opcional: qué te preocupa o qué quieres lograr',
    style: 'width:100%; padding:12px 14px; border-radius:12px; border:1px solid rgba(216,178,90,.35); background:rgba(255,255,255,.05); color:inherit; font:inherit; margin:8px 0'});
  const boton = crear('button', {type: 'button', className: 'boton', textContent: 'Victoria, revisa mis números'});
  const nota = crear('p', {className: 'letra-chica', textContent: codigo ? 'Kit CEO activo: revisiones sin límite.' : '1 revisión gratis al día · sin límite con el Kit CEO.'});
  const caja = crear('div', {hidden: true, style: 'margin-top:18px; padding:16px; border-radius:16px; border:1px solid rgba(216,178,90,.4); background:rgba(216,178,90,.06)'},
    crear('div', {className: 'etiqueta', textContent: 'Victoria revisa tus números · IA'}), preo, boton, nota, salida);
  const despues = res.querySelector('#compartir');
  despues ? res.insertBefore(caja, despues) : res.append(caja);
  fetch('/api/diagnostico').then((r) => { if (r.ok) caja.hidden = false; }).catch(() => {});
  const etiqueta = (el) => {
    const l = el.closest('label') || form.querySelector(`label[for="${el.id}"]`);
    return (l ? l.childNodes[0]?.textContent || l.textContent : el.name || el.id || '').replace(/\s+/g, ' ').trim().slice(0, 80);
  };
  boton.addEventListener('click', async () => {
    const campos = [...form.querySelectorAll('input, select')].filter((el) => el.type !== 'hidden' && el.value !== '')
      .map((el) => ({etiqueta: etiqueta(el), valor: el.type === 'checkbox' ? (el.checked ? 'sí' : 'no') : (el.tagName === 'SELECT' ? el.options[el.selectedIndex]?.text : el.value)}));
    const clon = res.cloneNode(true);
    clon.querySelectorAll('button, textarea, div[hidden], .boton').forEach((n) => n.remove());
    [...clon.children].filter((n) => n.contains(clon.querySelector('.etiqueta')) && n.textContent.includes('Victoria revisa')).forEach((n) => n.remove());
    const resultado = clon.innerText || clon.textContent;
    boton.disabled = true; salida.textContent = 'Victoria está revisando tus números… 🐾';
    try {
      const r = await fetch('/api/diagnostico', {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({calculadora, campos, resultado, preocupacion: preo.value, codigo})});
      const d = await r.json();
      salida.textContent = d.plan || d.error || 'No pude revisar tu caso ahorita.';
      if (d.codigo === false) { try { localStorage.removeItem('kit_codigo'); } catch (e) {} codigo = ''; }
      if (d.oferta) salida.append(crear('br'), crear('a', {href: enlacePago(`ia-${calculadora}`), className: 'boton', style: 'margin-top:10px', textContent: 'Quiero el Kit CEO'}),
        crear('button', {type: 'button', className: 'boton secundario', style: 'margin:10px 0 0 8px', textContent: 'Ya tengo mi código', onclick: () => {
          const c = (prompt('Escribe tu código del Kit CEO (viene en la página 2 de tu Edición CEO):') || '').trim();
          if (c) { try { localStorage.setItem('kit_codigo', c); } catch (e) {} codigo = c; nota.textContent = 'Código guardado: vuelve a pedir tu revisión.'; }
        }}));
    } catch (e) { salida.textContent = 'No pude revisar tu caso ahorita. Intenta en un momento.'; }
    boton.disabled = false;
  });
}
