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
  return `${VICTORIA.pago}${VICTORIA.pago.includes('?') ? '&' : '?'}src=${encodeURIComponent(src)}`;
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
