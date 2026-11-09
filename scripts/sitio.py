"""Arma las calculadoras gratis de la página de Victoria (sitio/public/<slug>.html) y el sitemap.

Uso: python scripts/sitio.py

Cada calculadora es una entrada desde Google y desde los videos ("calcula tu aguinaldo gratis:
enlace en mi perfil"), y termina en la plantilla de paga. Lo común (cabecera, menú de herramientas,
bloque de venta, compartir por WhatsApp, pie) sale de aquí; lo propio de cada una está en HERRAMIENTAS.
Toda cifra legal o fiscal lleva su fuente en la página (regla 7) y se revisa cada año (UMA, LFT).
"""
import calendar
import html
import json
import os

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLICO = os.path.join(RAIZ, 'sitio', 'public')
DOMINIO = 'https://victoriatheceo.vercel.app'

# UMA diaria 2026: INEGI, comunicado 1/26 (DOF 9-ene-2026), vigente desde el 1-feb-2026.
UMA_DIARIA = 117.31
TOPE_EXENTO_AGUINALDO = round(30 * UMA_DIARIA, 2)
# Conasami, salarios mínimos 2026 (DOF 9-dic-2025): general y zona libre de la frontera norte.
SALARIO_MINIMO_2026 = 315.04
SALARIO_MINIMO_FRONTERA_2026 = 440.87
FUENTE_CONASAMI = ('Conasami, salarios mínimos 2026 (DOF 9-dic-2025)', 'https://www.gob.mx/conasami')  # LISR art. 93, fr. XIV: 30 días -> $3,519.30

FUENTE_LFT = ('Ley Federal del Trabajo, artículo 87 (Cámara de Diputados)', 'https://www.diputados.gob.mx/LeyesBiblio/pdf/LFT.pdf')
FUENTE_LISR = ('Ley del Impuesto sobre la Renta, artículo 93, fracción XIV (Cámara de Diputados)', 'https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf')
FUENTE_UMA = ('INEGI, valor de la UMA 2026: $117.31 diarios (comunicado 1/26)', 'https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/uma/uma2026.pdf')

# Finiquito (revisado 9-nov-2026 contra la LFT vigente, última reforma DOF 14-05-2026). Tope de la prima de
# antigüedad: doble del salario mínimo de la zona (arts. 162 fr. II, 485 y 486).
TOPE_PRIMA_ANTIGUEDAD = round(2 * SALARIO_MINIMO_2026, 2)
TOPE_PRIMA_ANTIGUEDAD_FRONTERA = round(2 * SALARIO_MINIMO_FRONTERA_2026, 2)
FUENTE_LFT_FINIQUITO = ('Ley Federal del Trabajo, artículos 33, 47 a 52, 76, 79, 80, 87, 89, 162, 485, 486 y 516 a 518 (Cámara de Diputados)',
                        'https://www.diputados.gob.mx/LeyesBiblio/pdf/LFT.pdf')
FUENTE_DOF_SALARIOS = ('DOF 9-dic-2025: Resolución de la Conasami que fija los salarios mínimos 2026',
                       'https://dof.gob.mx/nota_detalle.php?codigo=5775534&fecha=09/12/2025')
FUENTE_PROFEDET_DESPIDO = ('PROFEDET: ¿Qué hacer si te despiden?',
                           'https://www.gob.mx/profedet/articulos/que-hacer-si-te-despiden-profedet-defiende-tus-derechos-laborales?idiom=es')
FUENTE_PROFEDET_VACACIONES = ('PROFEDET: tabla de días de vacaciones (art. 76)',
                              'https://www.gob.mx/profedet/articulos/la-ley-federal-del-trabajo-es-tu-aliada-en-tu-derecho-a-recibir-vacaciones?idiom=es')

HERRAMIENTAS = [
    {
        'slug': 'aguinaldo',
        'menu': 'Aguinaldo 2026', 'menu_nota': 'Cuánto te toca y cuánto paga ISR',
        'titulo': 'Calculadora de aguinaldo 2026: cuánto te toca y cuánto paga ISR',
        'descripcion': ('Calcula gratis tu aguinaldo 2026 según la Ley Federal del Trabajo: mínimo 15 días, parte '
                        f'proporcional y cuánto queda libre de ISR (${TOPE_EXENTO_AGUINALDO:,.2f}). Con un plan para no gastártelo en enero.'),
        'h1': 'Calcula tu <span>aguinaldo 2026</span>',
        'lema': ('Por ley son mínimo 15 días de salario, pagados antes del 20 de diciembre. Pon tus datos y te digo cuánto '
                 'te toca, cuánto está libre de impuestos y cómo repartirlo para que sí te sirva.'),
        'formulario': '''
      <label>Sueldo mensual bruto <small>(antes de impuestos, como dice tu recibo)</small>
        <input id="sueldo" inputmode="decimal" placeholder="15,000" value="15000"></label>
      <label>Días de aguinaldo <small>(la ley da mínimo 15; si tu empresa da más, pon los tuyos)</small>
        <input id="dias" inputmode="numeric" value="15"></label>
      <div class="fila">
        <label>Fecha de ingreso <small>(solo si entraste en 2026)</small>
          <input id="ingreso" type="date" min="2026-01-01" max="2026-12-31"></label>
        <label>Fecha de salida <small>(solo si ya no trabajas ahí)</small>
          <input id="salida" type="date" min="2026-01-01" max="2026-12-31"></label>
      </div>''',
        'resultado': '''
      <div class="etiqueta">Tu aguinaldo</div>
      <div class="cifra" id="total">$0</div>
      <ul class="desglose">
        <li>Salario diario <span class="letra-chica">(sueldo ÷ 30)</span><b id="diario"></b></li>
        <li>Días trabajados en 2026<b id="trabajados"></b></li>
        <li>Libre de ISR<b id="exento"></b></li>
        <li>Parte que paga ISR<b id="gravado"></b></li>
      </ul>
      <p class="nota" id="nota"></p>
      <h3>Mi plan para que no se te vaya en enero</h3>
      <p class="nota">Es mi regla, no una ley: primero lo que te cobra intereses o tu colchón, luego tus metas y al
        final el gusto, sin culpa. Cambia los porcentajes si quieres.</p>
      <div class="fila" style="grid-template-columns: repeat(3, 1fr); align-items: end">
        <label>Deudas/fondo % <input id="p1" inputmode="numeric" value="50"></label>
        <label>Metas % <input id="p2" inputmode="numeric" value="30"></label>
        <label>Gusto % <input id="p3" inputmode="numeric" value="20"></label>
      </div>
      <div class="barras" id="plan"></div>''',
        'script': f'''
const TOPE = {TOPE_EXENTO_AGUINALDO};
const DIA = 864e5;
function calcular() {{
  const sueldo = numero('sueldo'), dias = numero('dias');
  const inicio = document.getElementById('ingreso').value ? new Date(document.getElementById('ingreso').value) : new Date('2026-01-01');
  const fin = document.getElementById('salida').value ? new Date(document.getElementById('salida').value) : new Date('2026-12-31');
  const trabajados = Math.max(0, Math.min(365, Math.round((fin - inicio) / DIA) + 1));
  const diario = sueldo / 30;
  const total = diario * dias * trabajados / 365;
  const exento = Math.min(total, TOPE);
  const gravado = Math.max(0, total - TOPE);
  document.getElementById('total').textContent = pesos(total, 2);
  document.getElementById('diario').textContent = pesos(diario, 2);
  document.getElementById('trabajados').textContent = trabajados === 365 ? '365 (todo el año)' : String(trabajados);
  document.getElementById('exento').textContent = pesos(exento, 2);
  document.getElementById('gravado').textContent = pesos(gravado, 2);
  document.getElementById('nota').textContent = gravado > 0
    ? `Los primeros ${{pesos(TOPE, 2)}} no pagan ISR. Los ${{pesos(gravado, 2)}} restantes sí: tu empresa te retiene el impuesto y cuánto depende de tu sueldo, así que en tu cuenta te llegará algo menos que el total.`
    : 'Todo tu aguinaldo queda libre de ISR: es menor a 30 UMA (' + pesos(TOPE, 2) + ' en 2026).';
  const partes = [['Deudas o fondo de emergencia', numero('p1'), 'a'], ['Metas', numero('p2'), 'b'], ['Gusto', numero('p3'), 'c']];
  const suma = partes.reduce((s, p) => s + p[1], 0) || 1;
  document.getElementById('plan').replaceChildren(...partes.map(([nombre, pct, clase]) => crear('div', {{}},
    crear('span', {{textContent: `${{nombre}}: ${{pesos(total * pct / suma)}}`}}),
    crear('i', {{className: clase, style: `width:${{Math.round(100 * pct / suma)}}%`}}))));
}}
alCambiar('calculadora', calcular);''',
        'venta_titulo': 'Ya sabes cuánto te toca. Ahora que sí te rinda.',
        'venta_texto': ('El tablero de la CEO es mi plantilla para decidir a dónde va cada peso: tu aguinaldo, tus deudas, '
                        'tu fondo de emergencia y tus metas, todo calculado solo en Excel o Google Sheets.'),
        'faq': [
            ('¿Cuándo me tienen que pagar el aguinaldo?', 'Antes del 20 de diciembre. Lo dice el artículo 87 de la Ley Federal del Trabajo.'),
            ('¿Cuántos días me tocan?', 'Por lo menos 15 días de salario. Muchas empresas dan más: si es tu caso, cambia el número de días.'),
            ('¿Y si no trabajé todo el año o ya renuncié?', 'Te toca la parte proporcional al tiempo que trabajaste, aunque ya no estés en la empresa cuando se paga (artículo 87 de la Ley Federal del Trabajo).'),
            ('¿El aguinaldo paga impuestos?', f'Hasta el equivalente a 30 días queda libre de ISR (artículo 93, fracción XIV de la Ley del ISR). Se calcula con la UMA: 30 × $117.31 = ${TOPE_EXENTO_AGUINALDO:,.2f} en 2026. Lo que pase de eso sí paga ISR y tu empresa te lo retiene.'),
            ('¿Cómo sacan mi salario diario?', 'Aquí dividimos tu sueldo mensual entre 30, que es lo más común. Tu recibo puede usar otro cálculo; si no te cuadra, pregúntale a tu área de nómina.'),
            ('¿Y si trabajo para el gobierno?', 'Puede aplicarte otra ley con más días de aguinaldo. Pon tus días en el campo y el cálculo se ajusta.'),
            ('¿Y si no me pagan?', 'Puedes pedir asesoría gratuita en la Procuraduría Federal de la Defensa del Trabajo (PROFEDET).'),
            ('¿Cuánto aguinaldo me toca si gano 10 mil pesos al mes?', 'Con los 15 días de ley y el año completo: $10,000 ÷ 30 × 15 = $5,000 brutos. Los primeros $3,519.30 no pagan ISR.'),
            ('¿Cuánto aguinaldo me toca con el salario mínimo?', 'En 2026 el salario mínimo general es de $315.04 diarios: 15 días son $4,725.60. En la frontera norte, $440.87 diarios: $6,613.05.'),
        ],
        'fuentes': [FUENTE_LFT, FUENTE_LISR, FUENTE_UMA, FUENTE_CONASAMI],
        'compartir': 'Calcula cuánto te toca de aguinaldo y cuánto paga ISR, gratis:',
    },
    {
        'slug': 'finiquito',
        'menu': 'Finiquito y liquidación', 'menu_nota': 'Cuánto te toca si renuncias o te corren',
        'titulo': 'Calculadora de finiquito y liquidación 2026: cuánto te toca si renuncias o te despiden',
        'descripcion': ('Calcula gratis tu finiquito o liquidación 2026 según la Ley Federal del Trabajo: aguinaldo, vacaciones '
                        'y prima vacacional proporcionales, 3 meses de indemnización y prima de antigüedad, con el artículo de cada concepto.'),
        'h1': 'Calcula tu <span>finiquito y liquidación</span>',
        'lema': ('Lo que la ley te da no es un favor de tu patrón. Renuncies o te corran, hay dinero que ya es tuyo. '
                 'Pon tus datos y te digo cuánto, concepto por concepto y con el artículo para que lo pidas.'),
        'formulario': '''
      <label>¿Por qué terminó tu trabajo?
        <select id="motivo">
          <option value="renuncia">Renuncié</option>
          <option value="injustificado">Me despidieron sin causa</option>
          <option value="justificado">Me despidieron con causa</option>
        </select></label>
      <div class="fila">
        <label>Tu salario <small>(bruto, como dice tu recibo)</small>
          <input id="salario" inputmode="decimal" value="15000"></label>
        <label>¿Al mes o al día?
          <select id="periodo"><option value="mensual">al mes</option><option value="diario">al día</option></select></label>
      </div>
      <div class="fila">
        <label>Fecha de ingreso <input id="ingreso" type="date" value="2022-11-01"></label>
        <label>Fecha de salida <small>(tu último día)</small><input id="salida" type="date"></label>
      </div>
      <div class="fila">
        <label>¿Eres de planta? <small>(permanente)</small>
          <select id="planta"><option value="si">Sí</option><option value="no">No</option></select></label>
        <label>Zona <small>(para el tope de la prima de antigüedad)</small>
          <select id="zona"><option value="general">Resto del país</option><option value="frontera">Frontera norte</option></select></label>
      </div>
      <div class="fila">
        <label>Días de aguinaldo <small>(la ley da mínimo 15)</small><input id="dias_aguinaldo" inputmode="numeric" value="15"></label>
        <label>Prima vacacional % <small>(mínimo 25)</small><input id="prima" inputmode="decimal" value="25"></label>
      </div>
      <div class="fila">
        <label>Vacaciones que ya tomaste de este año de servicio <small>(días adelantados del año que va corriendo; si no, 0)</small>
          <input id="tomadas" inputmode="decimal" value="0"></label>
        <label>Vacaciones de años ya cumplidos que no tomaste <small>(días)</small>
          <input id="pendientes" inputmode="decimal" value="0"></label>
      </div>
      <label>Días trabajados que no te han pagado <small>(opcional: tu última quincena o semana)</small>
        <input id="sin_pagar" inputmode="decimal" value="0"></label>''',
        'resultado': '''
      <div class="etiqueta" id="titulo_total">Tu finiquito</div>
      <div class="cifra" id="total">$0</div>
      <p class="nota" id="resumen"></p>
      <ul class="desglose" id="conceptos"></ul>
      <div id="puede"></div>
      <p class="nota" id="notas"></p>
      <p class="nota"><b>Es una estimación, no asesoría legal.</b> No calcula ISR: tu patrón puede retenerte impuesto y lo que te
        llegue será menos. Usa tu salario diario (mensual ÷ 30, art. 89); para indemnizaciones la ley toma el salario con tus
        prestaciones (arts. 84 y 89), así que lo real puede ser más. Revisa tu caso gratis en la PROFEDET (079 o 800 911 7877)
        o con un abogado laboral antes de firmar.</p>''',
        'script': (f'const SM = {{general: {SALARIO_MINIMO_2026}, frontera: {SALARIO_MINIMO_FRONTERA_2026}}};\n' + '''
const DIA = 864e5;
const $ = (id) => document.getElementById(id);
const fecha = (id) => { const v = $(id).value; if (!v) return null; const [a, m, d] = v.split('-').map(Number); return Date.UTC(a, m - 1, d); };
const aniversario = (inicio, n) => { const f = new Date(inicio); return Date.UTC(f.getUTCFullYear() + n, f.getUTCMonth(), f.getUTCDate()); };
// Art. 76 (reforma DOF 27-12-2022): 12, 14, 16, 18, 20 y desde el sexto año +2 cada cinco.
const diasVacaciones = (ano) => ano < 1 ? 0 : ano <= 5 ? 10 + 2 * ano : 22 + 2 * Math.floor((ano - 6) / 5);
const dias = (n) => `${n.toLocaleString('es-MX', {maximumFractionDigits: 2})} ${n === 1 ? 'día' : 'días'}`;
const anosTexto = (n) => `${n} ${n === 1 ? 'año' : 'años'}`;
if (!$('salida').value) { const h = new Date(); $('salida').value = new Date(h - h.getTimezoneOffset() * 6e4).toISOString().slice(0, 10); }

function calcular() {
  const motivo = $('motivo').value, planta = $('planta').value === 'si';
  const diario = $('periodo').value === 'mensual' ? numero('salario') / 30 : numero('salario');
  const ingreso = fecha('ingreso'), salida = fecha('salida');
  const lista = $('conceptos'), puede = $('puede');
  if (ingreso === null || salida === null || salida < ingreso || diario <= 0) {
    $('total').textContent = pesos(0, 2);
    $('resumen').textContent = 'Pon tu salario y tus fechas de ingreso y salida (la salida no puede ser antes del ingreso).';
    lista.replaceChildren(); puede.replaceChildren(); $('notas').textContent = '';
    return;
  }
  // Antigüedad: años completos cumplidos al terminar tu último día y días del año que iba corriendo.
  const fin = salida + DIA;
  let anos = 0;
  while (anos < 80 && aniversario(ingreso, anos + 1) <= fin) anos++;
  const resto = Math.round((fin - aniversario(ingreso, anos)) / DIA);
  // Si saliste justo al cumplir el año, ese año completo de vacaciones se debe; si no, la parte proporcional (art. 79).
  const anoVac = resto === 0 ? anos : anos + 1;
  const fraccion = resto === 0 ? 1 : resto / 365;
  const desdeAguinaldo = Math.max(ingreso, Date.UTC(new Date(salida).getUTCFullYear(), 0, 1));
  const diasAno = Math.min(365, Math.round((fin - desdeAguinaldo) / DIA));

  const conceptos = [];
  const agregar = (nombre, articulo, detalle, monto) => conceptos.push({nombre, articulo, detalle, monto});
  const sinPagar = Math.max(0, numero('sin_pagar'));
  if (sinPagar > 0) agregar('Días trabajados sin pagar', 'art. 82', `${dias(sinPagar)} × ${pesos(diario, 2)}`, sinPagar * diario);
  const diasAg = Math.max(0, numero('dias_aguinaldo'));
  agregar('Aguinaldo proporcional', 'art. 87', `${dias(diasAg)} × ${diasAno}/365 de este año`, diario * diasAg * diasAno / 365);
  const diasVacAno = diasVacaciones(anoVac);
  const vacDias = Math.max(0, diasVacAno * fraccion - Math.max(0, numero('tomadas'))) + Math.max(0, numero('pendientes'));
  const vacaciones = vacDias * diario;
  agregar('Vacaciones', 'arts. 76 y 79', `${dias(Math.round(vacDias * 100) / 100)} (año ${anoVac} de servicio: ${diasVacAno} días${resto ? ` × ${resto}/365` : ''})`, vacaciones);
  const pct = Math.max(0, numero('prima'));
  agregar('Prima vacacional', 'art. 80', `${pct}% de tus vacaciones`, vacaciones * pct / 100);
  const finiquito = conceptos.reduce((s, c) => s + c.monto, 0);

  const notas = [];
  if (diasAg < 15) notas.push('Pusiste menos de 15 días de aguinaldo: la ley da mínimo 15 (art. 87).');
  if (pct < 25) notas.push('Pusiste menos de 25% de prima vacacional: la ley da mínimo 25% (art. 80).');
  if (new Date(salida).getUTCFullYear() < 2026) notas.push('Saliste antes de 2026: aquí usamos el salario mínimo 2026 para el tope de la prima de antigüedad, y antes de 2023 las vacaciones eran menos días. Revisa tu caso en la PROFEDET.');
  const sm = SM[$('zona').value];
  const base = Math.min(Math.max(diario, sm), 2 * sm);
  const baseTexto = diario > 2 * sm ? `${pesos(base, 2)} (tope: 2 salarios mínimos)` : diario < sm ? `${pesos(base, 2)} (no menos del salario mínimo)` : pesos(base, 2);
  let liquidacion = 0;
  if (!planta) notas.push('Prima de antigüedad: no aparece porque la ley solo la da a trabajadores de planta (art. 162).');
  else if (motivo === 'renuncia' && anos < 15) notas.push(`Prima de antigüedad: si renuncias, solo te toca con 15 años o más de servicio (art. 162, fr. III). Llevas ${anosTexto(anos)}.`);
  else if (anos > 0 || resto > 0) {
    if (anos > 0) {
      agregar('Prima de antigüedad', 'arts. 162, 485 y 486', `12 días × ${anosTexto(anos)} × ${baseTexto}`, 12 * anos * base);
      liquidacion += 12 * anos * base;
    }
    if (resto > 0) notas.push(`Prima de antigüedad: la ley dice "por cada año de servicios", así que aquí solo contamos tus ${anosTexto(anos)} completos. Pregunta en la PROFEDET si te reconocen la parte del año incompleto (${resto} días): serían unos ${pesos(12 * resto / 365 * base, 2)} más.`);
  }
  if (motivo === 'injustificado') {
    agregar('Indemnización: 3 meses de salario', 'art. 48', `90 días × ${pesos(diario, 2)}`, 90 * diario);
    liquidacion += 90 * diario;
    // Con menos de un año (art. 49, fr. I) el patrón puede no reinstalarte pagando el art. 50: mostramos la parte proporcional.
    const veinte = anos > 0 ? 20 * anos * diario : 20 * resto / 365 * diario;
    const veinteDetalle = anos > 0 ? `20 días × ${anosTexto(anos)} completos` : `parte proporcional de ${dias(resto)}`;
    const veinteResto = anos === 0
      ? ` Con menos de un año de servicio, el patrón puede no regresarte pagando esta indemnización (art. 49, fr. I). La ley habla de "cada uno de los años", así que esta cifra es la parte proporcional: confírmala en la PROFEDET.`
      : resto > 0 ? ` Por los ${dias(resto)} del año que iba corriendo serían unos ${pesos(20 * resto / 365 * diario, 2)} más; pregunta en la PROFEDET si te los reconocen.` : '';
    puede.replaceChildren(
      crear('h3', {textContent: 'Puede aplicar (no está sumado)'}),
      crear('ul', {className: 'desglose'}, crear('li', {},
        crear('span', {}, '20 días por año de servicio ', crear('span', {className: 'letra-chica', textContent: `(art. 50, fr. II · ${veinteDetalle})`})),
        crear('b', {textContent: pesos(veinte, 2)}))),
      crear('p', {className: 'nota', textContent: 'Si te despiden sin causa, la ley te deja elegir: que te regresen a tu trabajo o los 3 meses (art. 48). Los 20 días por año se pagan además cuando el patrón queda libre de regresarte (art. 49: si tenías menos de un año, eras de confianza, trabajo del hogar, eventual, o el Tribunal decide que el trato directo ya no es posible) o cuando tú te vas por culpa del patrón (arts. 51 y 52). Si había contrato por tiempo determinado, se calcula distinto (art. 50, fr. I). Si llegas a juicio y el patrón no prueba la causa, también se pagan salarios vencidos de hasta 12 meses (art. 48): no están aquí.' + veinteResto}));
  } else puede.replaceChildren();
  if (motivo === 'justificado') notas.push('Aunque el despido sea justificado, lo que ya ganaste se paga. El patrón debe darte un aviso por escrito con la causa y la fecha; si no te lo da, se presume que el despido fue injustificado (art. 47).');

  const total = finiquito + liquidacion;
  $('titulo_total').textContent = motivo === 'injustificado' ? 'Tu liquidación' : 'Tu finiquito';
  $('total').textContent = pesos(total, 2);
  $('resumen').textContent = `Salario diario: ${pesos(diario, 2)}. Antigüedad: ${anosTexto(anos)}${resto ? ` y ${dias(resto)}` : ''}.` +
    (motivo === 'injustificado' ? ` Finiquito ${pesos(finiquito, 2)} + ${liquidacion > 90 * diario + 0.005 ? 'indemnización y prima de antigüedad' : 'indemnización'} ${pesos(liquidacion, 2)}.` : '');
  lista.replaceChildren(...conceptos.map((c) => crear('li', {},
    crear('span', {}, `${c.nombre} `, crear('span', {className: 'letra-chica', textContent: `(${c.articulo} · ${c.detalle})`})),
    crear('b', {textContent: pesos(c.monto, 2)}))),
    crear('li', {}, crear('span', {}, crear('b', {textContent: 'Total'})), crear('b', {textContent: pesos(total, 2)})));
  notas.push('El aguinaldo cuenta desde el 1 de enero (o tu ingreso, si entraste este año) y supone que los de años pasados ya te los pagaron.');
  $('notas').textContent = notas.join(' ');
}
alCambiar('calculadora', calcular);'''),
        'venta_titulo': 'Con tu finiquito en la mano, que no se te vaya en un mes.',
        'venta_texto': ('Entre un trabajo y otro, ese dinero es tu colchón. El tablero de la CEO te ayuda a estirarlo: presupuesto, '
                        'fondo de emergencia y deudas, todo calculado solo en Excel o Google Sheets.'),
        'faq': [
            ('¿Cuánto me toca de finiquito si renuncio?',
             'Lo que ya ganaste: los días trabajados que no te han pagado, la parte proporcional de tu aguinaldo (art. 87), tus '
             'vacaciones no tomadas y las proporcionales del año que iba corriendo (arts. 76 y 79) con su prima vacacional de mínimo '
             '25% (art. 80). Si eres de planta y tienes 15 años o más, también la prima de antigüedad: 12 días por año (art. 162). '
             'Por renunciar no hay indemnización.'),
            ('¿Qué es la liquidación y en qué se diferencia del finiquito?',
             'El finiquito es lo que ya ganaste y te toca siempre, renuncies o te corran. La liquidación es el finiquito más la '
             'indemnización por despido injustificado: 3 meses de salario (art. 48) y, si eres de planta, la prima de antigüedad de '
             '12 días por año (art. 162). En algunos casos se suman 20 días por año (arts. 49, 50 y 52).'),
            ('¿Me pueden obligar a firmar mi renuncia?',
             'No. La PROFEDET lo dice claro: no firmes una carta de renuncia ni hojas en blanco; nadie te puede presionar a renunciar. '
             'Además, la ley anula cualquier renuncia a tus salarios, indemnizaciones y prestaciones, y todo convenio o liquidación '
             'debe ser por escrito, con el desglose de lo que te pagan, y ratificarse ante el Centro de Conciliación o el Tribunal (art. 33).'),
            ('¿Cuánto tiempo tengo para reclamar?',
             'Si te despidieron, 2 meses contados desde el día siguiente a tu despido (art. 518). El plazo se suspende cuando presentas '
             'tu solicitud en el Centro de Conciliación. Para lo demás (aguinaldo, vacaciones, salarios) la regla general es 1 año '
             '(art. 516). Si te quieres ir por culpa del patrón, tienes 1 mes (art. 517).'),
            ('¿Cuándo me toca la prima de antigüedad?',
             f'Solo si eres de planta. Son 12 días de salario por año, con tu salario topado al doble del mínimo: '
             f'${TOPE_PRIMA_ANTIGUEDAD:,.2f} diarios en 2026 (${TOPE_PRIMA_ANTIGUEDAD_FRONTERA:,.2f} en la frontera norte). '
             'Si renuncias, necesitas 15 años o más. Si te despiden, te toca sin importar los años y aunque el despido sea justificado '
             '(art. 162, fr. III).'),
            ('¿Cuándo me pagan los 20 días por año?',
             'No en todo despido. Si te corren sin causa puedes pedir que te regresen o 3 meses de salario (art. 48). Los 20 días por '
             'año (art. 50) se suman cuando el patrón queda libre de regresarte (art. 49: menos de un año de antigüedad, trabajadores '
             'de confianza, del hogar, eventuales, entre otros) o cuando tú te separas por una falta del patrón, como bajarte el sueldo '
             'o no pagarte (arts. 51 y 52).'),
            ('Si me despidieron con causa, ¿me pagan algo?',
             'Sí: tu finiquito (lo que ya ganaste) y, si eres de planta, la prima de antigüedad. Lo que no te toca es la indemnización '
             'de 3 meses. Ojo: el patrón debe darte un aviso por escrito con la causa; si no lo hace, se presume que el despido fue '
             'injustificado (art. 47).'),
            ('¿Dónde me asesoran gratis?',
             'En la PROFEDET (Procuraduría Federal de la Defensa del Trabajo): llama al 079 o al 800 911 7877. Todos sus servicios son '
             'gratuitos; nadie te puede cobrar por la asesoría.'),
        ],
        'fuentes': [FUENTE_LFT_FINIQUITO, FUENTE_DOF_SALARIOS, FUENTE_PROFEDET_DESPIDO, FUENTE_PROFEDET_VACACIONES],
        'compartir': 'Calcula tu finiquito o liquidación, gratis y con el artículo de cada concepto:',
    },
    {
        'slug': 'interes-compuesto',
        'menu': 'Interés compuesto', 'menu_nota': 'Cuánto crece tu ahorro con el tiempo',
        'titulo': 'Calculadora de interés compuesto: cuánto crece tu ahorro mes a mes',
        'descripcion': ('Calcula gratis cuánto crece tu dinero con interés compuesto: monto inicial, ahorro mensual, tasa y '
                        'años. Incluye la regla del 72 para saber en cuánto tiempo se duplica.'),
        'h1': 'Calculadora de <span>interés compuesto</span>',
        'lema': 'El dinero que ahorras gana intereses, y esos intereses ganan intereses. Mira cuánto crece lo tuyo con el tiempo.',
        'formulario': '''
      <div class="fila">
        <label>Monto inicial <input id="inicial" inputmode="decimal" value="0"></label>
        <label>Ahorro cada mes <input id="mensual" inputmode="decimal" value="1000"></label>
      </div>
      <div class="fila">
        <label>Tasa anual % <small>(fija, de ejemplo)</small><input id="tasa" inputmode="decimal" value="8"></label>
        <label>Años <input id="anos" inputmode="numeric" value="20"></label>
      </div>''',
        'resultado': '''
      <div class="etiqueta">Al final tendrías</div>
      <div class="cifra" id="total">$0</div>
      <ul class="desglose">
        <li>Lo que pusiste tú<b id="puesto"></b></li>
        <li>Lo que ganó en intereses<b id="intereses"></b></li>
        <li>Se duplica cada <span class="letra-chica">(regla del 72)</span><b id="duplica"></b></li>
      </ul>
      <table><thead><tr><th>Año</th><th class="num">Pusiste</th><th class="num">Tendrías</th></tr></thead><tbody id="tabla"></tbody></table>
      <p class="nota">Ejemplo con tasa fija y capitalización mensual, sin inflación, comisiones ni impuestos. Es educativo:
        no es una recomendación de inversión y ninguna tasa está garantizada.</p>''',
        'script': '''
function valorFuturo(inicial, mensual, tasa, meses) {
  const r = tasa / 100 / 12;
  if (!r) return inicial + mensual * meses;
  const f = Math.pow(1 + r, meses);
  return inicial * f + mensual * (f - 1) / r;
}
function calcular() {
  const inicial = numero('inicial'), mensual = numero('mensual'), tasa = numero('tasa');
  const anos = Math.max(0, Math.min(60, Math.round(numero('anos'))));
  const total = valorFuturo(inicial, mensual, tasa, anos * 12);
  const puesto = inicial + mensual * anos * 12;
  document.getElementById('total').textContent = pesos(total);
  document.getElementById('puesto').textContent = pesos(puesto);
  document.getElementById('intereses').textContent = pesos(total - puesto);
  document.getElementById('duplica').textContent = tasa > 0 ? `${(72 / tasa).toFixed(1)} años` : '—';
  const hitos = [...new Set([1, 5, 10, 15, 20, 25, 30, 40, 50, 60].filter((a) => a < anos).concat(anos))].filter((a) => a > 0);
  document.getElementById('tabla').replaceChildren(...hitos.map((a) => crear('tr', {},
    crear('td', {textContent: String(a)}), crear('td', {className: 'num', textContent: pesos(inicial + mensual * a * 12)}),
    crear('td', {className: 'num', textContent: pesos(valorFuturo(inicial, mensual, tasa, a * 12))}))));
}
alCambiar('calculadora', calcular);''',
        'venta_titulo': 'Haz este cálculo con tus metas reales.',
        'venta_texto': ('En El tablero de la CEO tienes el interés compuesto, la regla del 72 y cuánto apartar al mes para cada '
                        'meta, junto con tu presupuesto, tus deudas y tu fondo de emergencia.'),
        'faq': [
            ('¿Qué es el interés compuesto?', 'Es ganar intereses sobre los intereses que ya ganaste. Al principio se nota poco; con los años, la mayor parte de lo que tienes viene de los intereses.'),
            ('¿Qué es la regla del 72?', 'Divide 72 entre la tasa anual y sabrás en cuántos años se duplica tu dinero, más o menos. Al 8% anual: unos 9 años. La describió Luca Pacioli en 1494.'),
            ('¿Qué tasa pongo?', 'La que te dé hoy tu instrumento de ahorro. Las tasas cambian y ninguna está garantizada: úsala como ejemplo, no como promesa.'),
        ],
        'fuentes': [],
        'compartir': 'Mira cuánto crece tu ahorro con interés compuesto:',
    },
    {
        'slug': 'regla-50-30-20',
        'menu': 'Regla 50/30/20', 'menu_nota': 'Tu sueldo en tres partes',
        'titulo': 'Calculadora regla 50/30/20: divide tu sueldo en necesidades, deseos y ahorro',
        'descripcion': ('Calcula gratis tu presupuesto con la regla 50/30/20: cuánto va a necesidades, a deseos y a ahorro y '
                        'deudas, y compáralo con lo que gastas hoy.'),
        'h1': 'Tu sueldo con la <span>regla 50/30/20</span>',
        'lema': 'La mitad para lo necesario, 30% para lo que quieres y 20% para ahorrar y salir de deudas. Pon tu ingreso y mira cómo queda.',
        'formulario': '''
      <label>Ingreso mensual neto <small>(lo que te llega después de impuestos)</small>
        <input id="ingreso" inputmode="decimal" value="15000"></label>
      <p class="nota">Opcional: lo que gastas hoy, para comparar.</p>
      <div class="fila" style="grid-template-columns: repeat(3, 1fr); align-items: end">
        <label>Necesidades <input id="g1" inputmode="decimal" placeholder="0"></label>
        <label>Deseos <input id="g2" inputmode="decimal" placeholder="0"></label>
        <label>Ahorro y deudas <input id="g3" inputmode="decimal" placeholder="0"></label>
      </div>''',
        'resultado': '''
      <div class="etiqueta">Así se reparte tu ingreso</div>
      <ul class="desglose" id="reparto"></ul>
      <p class="nota" id="nota"></p>''',
        'script': '''
function calcular() {
  const ingreso = numero('ingreso');
  const partes = [['Necesidades (50%)', 0.5, 'g1'], ['Deseos (30%)', 0.3, 'g2'], ['Ahorro y deudas (20%)', 0.2, 'g3']];
  const comparar = partes.some(([, , id]) => numero(id) > 0);
  document.getElementById('reparto').replaceChildren(...partes.map(([nombre, pct, id]) => {
    const meta = ingreso * pct, real = numero(id);
    const fila = crear('li', {}, crear('span', {textContent: nombre}), crear('b', {textContent: pesos(meta)}));
    if (comparar) {
      const dif = real - meta;
      const ahorro = id === 'g3';
      const bien = ahorro ? dif >= 0 : dif <= 0;
      fila.append(crear('span', {className: bien ? 'bien' : 'aviso', textContent: dif === 0 ? ' justo' : ` ${dif > 0 ? '+' : '−'}${pesos(Math.abs(dif))}`}));
    }
    return fila;
  }));
  document.getElementById('nota').textContent = comparar
    ? 'En verde vas bien; en rojo te pasas (o, en ahorro, te falta). Es un punto de partida: ajústalo a tu vida.'
    : 'Necesidades: vivienda, comida, transporte, servicios, salud y los pagos mínimos de tus deudas. Deseos: lo demás. El 20% es para ahorrar y para pagar deudas de más.';
}
alCambiar('calculadora', calcular);''',
        'venta_titulo': 'Lleva tu 50/30/20 mes a mes.',
        'venta_texto': ('El tablero de la CEO trae el presupuesto 50/30/20 que se calcula solo, te dice cuánto te sobra o te falta '
                        'y lo conecta con tu ahorro, tus deudas y tus metas.'),
        'faq': [
            ('¿De dónde sale la regla 50/30/20?', 'La propusieron Elizabeth Warren y Amelia Warren Tyagi en su libro All Your Worth (2005).'),
            ('¿Los pagos de mis deudas van en necesidades?', 'Los pagos mínimos, sí. Lo que abones de más para salir antes va en el 20%.'),
            ('¿Y si mis necesidades pasan del 50%?', 'Pasa mucho. Es un punto de partida: empieza por ahorrar algo fijo cada mes aunque sea menos del 20% y ve ajustando.'),
        ],
        'fuentes': [],
        'compartir': 'Divide tu sueldo con la regla 50/30/20, gratis:',
    },
    {
        'slug': 'fondo-de-emergencia',
        'menu': 'Fondo de emergencia', 'menu_nota': 'Cuánto necesitas y cuándo llegas',
        'titulo': 'Calculadora de fondo de emergencia: cuánto necesitas y en cuánto tiempo llegas',
        'descripcion': ('Calcula gratis tu fondo de emergencia de 3 a 6 meses de gastos fijos, cuánto te falta y en cuántos meses '
                        'lo completas ahorrando cada mes.'),
        'h1': 'Tu <span>fondo de emergencia</span>',
        'lema': 'De 3 a 6 meses de tus gastos fijos, guardados para cuando algo se rompe. Mira cuánto necesitas y cuándo llegas.',
        'formulario': '''
      <label>Gastos fijos al mes <small>(vivienda, comida, salud, transporte, servicios y deudas)</small>
        <input id="gastos" inputmode="decimal" value="12000"></label>
      <div class="fila">
        <label>Meses de colchón <select id="meses"><option>3</option><option>4</option><option>5</option><option selected>6</option></select></label>
        <label>Ya tienes ahorrado <input id="tienes" inputmode="decimal" value="0"></label>
      </div>
      <label>Puedes ahorrar al mes <input id="mensual" inputmode="decimal" value="1500"></label>''',
        'resultado': '''
      <div class="etiqueta">Tu meta</div>
      <div class="cifra" id="meta">$0</div>
      <ul class="desglose">
        <li>Te falta<b id="falta"></b></li>
        <li>Avance<b id="avance"></b></li>
        <li>Llegas en<b id="tiempo"></b></li>
      </ul>
      <div class="barras"><div><i id="barra" style="width:0%"></i></div></div>
      <p class="nota">Guárdalo donde lo puedas sacar rápido y sin perder dinero: no es para invertir en algo riesgoso.</p>''',
        'script': '''
function calcular() {
  const meta = numero('gastos') * Number(document.getElementById('meses').value);
  const tienes = numero('tienes'), mensual = numero('mensual');
  const falta = Math.max(0, meta - tienes);
  const avance = meta ? Math.min(100, 100 * tienes / meta) : 0;
  document.getElementById('meta').textContent = pesos(meta);
  document.getElementById('falta').textContent = pesos(falta);
  document.getElementById('avance').textContent = `${avance.toFixed(0)}%`;
  document.getElementById('barra').style.width = `${avance}%`;
  let tiempo = '¡Ya llegaste!';
  if (falta > 0) {
    if (mensual <= 0) tiempo = 'Pon cuánto puedes ahorrar';
    else {
      const meses = Math.ceil(falta / mensual);
      const fecha = new Date(); fecha.setMonth(fecha.getMonth() + meses);
      tiempo = `${meses} meses (${fecha.toLocaleDateString('es-MX', {month: 'long', year: 'numeric'})})`;
    }
  }
  document.getElementById('tiempo').textContent = tiempo;
}
alCambiar('calculadora', calcular);''',
        'venta_titulo': 'Sigue tu avance cada mes.',
        'venta_texto': ('El tablero de la CEO lleva tu fondo de emergencia con meta, avance y meses para llegar, junto con tu '
                        'presupuesto, tus deudas y tus metas.'),
        'faq': [
            ('¿Cuántos meses necesito?', 'La CONDUSEF recomienda de 3 a 6 meses de tus gastos. Si tu ingreso es variable o mantienes a alguien, apunta a 6.'),
            ('¿Primero el fondo o primero invertir?', 'Primero el fondo. Sin colchón, cualquier emergencia te obliga a endeudarte o a vender en mal momento.'),
            ('¿Qué cuenta como gasto fijo?', 'Lo que pagas sí o sí cada mes: vivienda, comida, salud, transporte, servicios y los pagos de tus deudas.'),
        ],
        'fuentes': [],
        'compartir': 'Calcula cuánto necesitas de fondo de emergencia:',
    },
    {
        'slug': 'pagar-deudas',
        'menu': 'Salir de deudas', 'menu_nota': 'Bola de nieve o avalancha',
        'titulo': 'Calculadora para salir de deudas: método bola de nieve o avalancha',
        'descripcion': ('Calcula gratis en cuántos meses sales de tus deudas y cuánto pagas de intereses con el método bola de '
                        'nieve o el de avalancha. Te dice qué deuda pagar primero.'),
        'h1': 'Sal de tus <span>deudas</span>',
        'lema': 'Pon tus deudas y lo que puedes abonar de más cada mes. Te digo en qué orden pagarlas, cuándo terminas y cuánto te ahorras.',
        'formulario': '''
      <div id="deudas"></div>
      <button type="button" class="boton secundario" id="agregar">+ Agregar otra deuda</button>
      <label>Puedes abonar de más cada mes <small>(además de los pagos mínimos)</small>
        <input id="extra" inputmode="decimal" value="1000"></label>''',
        'resultado': '''
      <div class="etiqueta">Tu plan</div>
      <div id="plan"></div>
      <p class="nota">Usa la tasa de interés anual de tu estado de cuenta. Es una simulación con pagos fijos y sin cargos
        nuevos: tu banco puede calcular distinto.</p>''',
        'script': '''
const EJEMPLO = [['Tarjeta A', 18000, 60, 900], ['Tarjeta B', 6000, 45, 300], ['Préstamo', 25000, 30, 1200]];
const caja = document.getElementById('deudas');
function fila(datos = ['', '', '', '']) {
  if (caja.children.length >= 8) return;
  const n = caja.children.length + 1;
  const campos = [['Nombre', 'text', `Deuda ${n}`], ['Saldo', 'decimal', '0'], ['Tasa anual %', 'decimal', '0'], ['Pago mínimo', 'decimal', '0']];
  caja.append(crear('div', {className: 'deuda'}, ...campos.map(([nombre, tipo, ph], i) =>
    crear('label', {}, nombre, crear('input', {type: 'text', inputMode: tipo === 'text' ? 'text' : 'decimal', placeholder: ph, value: datos[i] ?? ''})))));
}
EJEMPLO.forEach(fila);
document.getElementById('agregar').addEventListener('click', () => { fila(); calcular(); });
const valor = (texto) => { const v = parseFloat(String(texto).replace(/[,\\s$%]/g, '')); return Number.isFinite(v) ? v : 0; };
function leerDeudas() {
  return [...caja.children].map((d, i) => {
    const c = d.querySelectorAll('input');
    return {nombre: c[0].value.trim() || `Deuda ${i + 1}`, saldo: valor(c[1].value), tasa: valor(c[2].value), minimo: valor(c[3].value)};
  }).filter((d) => d.saldo > 0);
}
function simular(deudas, extra, orden) {
  const ds = deudas.map((d) => ({...d})).sort(orden);
  const presupuesto = ds.reduce((s, d) => s + d.minimo, 0) + extra;
  let meses = 0, intereses = 0;
  const liquidadas = [];
  while (ds.some((d) => d.saldo > 0.005) && meses < 600) {
    meses++;
    for (const d of ds) if (d.saldo > 0) { const i = d.saldo * d.tasa / 1200; d.saldo += i; intereses += i; }
    let disponible = presupuesto;
    for (const d of ds) if (d.saldo > 0) { const p = Math.min(d.minimo, d.saldo); d.saldo -= p; disponible -= p; }
    for (const d of ds) if (d.saldo > 0 && disponible > 0) { const p = Math.min(disponible, d.saldo); d.saldo -= p; disponible -= p; }
    for (const d of ds) if (d.saldo <= 0.005 && !liquidadas.find((x) => x.nombre === d.nombre)) { d.saldo = 0; liquidadas.push({nombre: d.nombre, mes: meses}); }
  }
  return {meses, intereses, liquidadas, termina: meses < 600};
}
const enMeses = (m) => m >= 12 ? `${m} meses (${(m / 12).toFixed(1)} años)` : `${m} meses`;
function bloque(titulo, r, explica) {
  return crear('div', {className: 'tarjeta', style: 'margin-top:12px'},
    crear('h3', {textContent: titulo, style: 'margin-top:0'}), crear('p', {className: 'nota', textContent: explica, style: 'margin-top:0'}),
    crear('ul', {className: 'desglose'},
      crear('li', {}, 'Sin deudas en', crear('b', {textContent: r.termina ? enMeses(r.meses) : 'más de 50 años'})),
      crear('li', {}, 'Intereses que pagas', crear('b', {textContent: pesos(r.intereses)})),
      crear('li', {}, 'Orden', crear('b', {textContent: r.liquidadas.map((x) => x.nombre).join(' → ') || '—'}))));
}
function calcular() {
  const deudas = leerDeudas(), extra = numero('extra');
  const plan = document.getElementById('plan');
  if (!deudas.length) return plan.replaceChildren(crear('p', {className: 'nota', textContent: 'Pon al menos una deuda con saldo.'}));
  const bola = simular(deudas, extra, (a, b) => a.saldo - b.saldo);
  const avalancha = simular(deudas, extra, (a, b) => b.tasa - a.tasa);
  const ahorro = bola.intereses - avalancha.intereses;
  const resumen = !avalancha.termina
    ? crear('p', {className: 'aviso', textContent: 'Con estos pagos tus deudas casi no bajan: los intereses se comen lo que abonas. Sube lo que pagas de más o pide reestructurar.'})
    : crear('p', {className: 'bien', textContent: ahorro > 1
        ? `Avalancha te ahorra ${pesos(ahorro)} en intereses. Bola de nieve te da la primera victoria en ${bola.liquidadas[0]?.mes ?? '—'} meses.`
        : `Con tus deudas los dos métodos cuestan casi lo mismo: elige el que te motive más.`});
  plan.replaceChildren(resumen,
    bloque('Avalancha', avalancha, 'Primero la de la tasa más alta: es la que menos intereses te cobra en total.'),
    bloque('Bola de nieve', bola, 'Primero la más chica: la liquidas rápido y esa victoria te mantiene motivada.'));
}
alCambiar('calculadora', calcular);''',
        'venta_titulo': 'Lleva tu plan de deudas al día.',
        'venta_texto': ('El tablero de la CEO ordena tus deudas con bola de nieve o avalancha, te dice cuánto te cuestan en '
                        'intereses al mes y lo conecta con tu presupuesto y tu fondo de emergencia.'),
        'faq': [
            ('¿Qué es el método bola de nieve?', 'Pagas el mínimo en todas y lo extra va a la deuda más chica. Cuando la liquidas, lo que pagabas ahí se suma a la siguiente. Lo popularizó Dave Ramsey.'),
            ('¿Qué es el método avalancha?', 'Igual, pero lo extra va primero a la deuda con la tasa de interés más alta. Matemáticamente es el que menos intereses te cobra.'),
            ('¿Cuál me conviene?', 'Si te cuesta mantener el plan, bola de nieve: las victorias rápidas motivan. Si quieres pagar lo menos posible, avalancha.'),
        ],
        'fuentes': [],
        'compartir': 'Calcula en cuántos meses sales de tus deudas:',
    },
]

# Tarjeta que sale al compartir el enlace (WhatsApp, Facebook, X): título grande + Victoria.
VISTA_PREVIA = {
    'aguinaldo': ('Calcula tu aguinaldo 2026', 'Cuánto te toca y cuánto paga ISR'),
    'finiquito': ('Calcula tu finiquito 2026', 'Renuncia o despido: cuánto te toca'),
    'interes-compuesto': ('Cuánto crece tu ahorro', 'Calculadora de interés compuesto'),
    'regla-50-30-20': ('Tu sueldo en 50/30/20', 'Necesidades, deseos y ahorro'),
    'fondo-de-emergencia': ('Tu fondo de emergencia', 'Cuánto necesitas y cuándo llegas'),
    'pagar-deudas': ('Sal de tus deudas', 'Bola de nieve o avalancha'),
}
FUENTES_INTER = '/usr/share/fonts/opentype/inter'


def extra_aguinaldo():
    """Ejemplos por sueldo (9-nov-2026): la gente busca "aguinaldo si gano 10 mil"; Google premia la respuesta directa."""
    filas = ''
    for sueldo in (8000, 10000, 12000, 15000, 20000, 25000, 30000):
        ag = sueldo / 30 * 15
        exento = min(ag, TOPE_EXENTO_AGUINALDO)
        filas += (f'<tr><td>${sueldo:,.0f}</td><td>${ag:,.0f}</td><td>${exento:,.0f}</td>'
                  f'<td>${ag - exento:,.0f}</td></tr>')
    sm = SALARIO_MINIMO_2026 * 15
    smf = SALARIO_MINIMO_FRONTERA_2026 * 15
    return f"""
    <section class="ejemplos">
      <div class="etiqueta">Ejemplos 2026</div>
      <h2>¿Cuánto aguinaldo me toca si gano…?</h2>
      <p class="lema" style="margin:0">Brutos, con los 15 días mínimos de ley, todo el año trabajado y sueldo mensual entre 30 (cifras redondeadas).
      La parte gravada paga ISR según tu tabla; tu empresa te lo retiene.</p>
      <div class="tabla"><table>
        <thead><tr><th>Sueldo/mes</th><th>Aguinaldo</th><th>Sin ISR</th><th>Con ISR</th></tr></thead>
        <tbody>{filas}</tbody>
      </table></div>
      <h3>Con el salario mínimo</h3>
      <p>Salario mínimo general 2026: ${SALARIO_MINIMO_2026:,.2f} diarios × 15 = <b>${sm:,.2f}</b>. En la zona libre de la
      frontera norte: ${SALARIO_MINIMO_FRONTERA_2026:,.2f} × 15 = <b>${smf:,.2f}</b>.</p>
      <h3>Si no trabajaste todo el año</h3>
      <p>Se paga la parte proporcional: aguinaldo × días trabajados ÷ 365. Ejemplo: $15,000 al mes y 200 días trabajados:
      $7,500 × 200 ÷ 365 = <b>${7500 * 200 / 365:,.2f}</b>. Te toca aunque ya no trabajes ahí.</p>
      <h3>Cómo se calcula, paso a paso</h3>
      <p>1. Salario diario = sueldo mensual ÷ 30. 2. Aguinaldo = salario diario × 15 (o los días que dé tu empresa).
      3. Si no completaste el año, multiplica por días trabajados ÷ 365. 4. Los primeros ${TOPE_EXENTO_AGUINALDO:,.2f}
      (30 UMA) no pagan ISR.</p>
    </section>
"""


def dias_vacaciones(ano):
    """Art. 76 LFT (reforma DOF 27-12-2022): 12, 14, 16, 18, 20 y desde el sexto año +2 cada cinco."""
    return 0 if ano < 1 else 10 + 2 * ano if ano <= 5 else 22 + 2 * ((ano - 6) // 5)


def calcula_finiquito(mensual, ingreso, salida, motivo, planta=True, zona_sm=SALARIO_MINIMO_2026):
    """La misma cuenta que hace la calculadora en JS (15 días de aguinaldo, prima vacacional 25%, sin vacaciones pendientes)."""
    from datetime import date, timedelta
    diario = mensual / 30
    fin = salida + timedelta(days=1)
    # Como en el JS: quien entró un 29 de febrero cumple el 1 de marzo en años no bisiestos.
    aniversario = lambda n: (date(ingreso.year + n, 3, 1) if (ingreso.month, ingreso.day) == (2, 29) and not calendar.isleap(ingreso.year + n)
                             else date(ingreso.year + n, ingreso.month, ingreso.day))
    anos = 0
    while aniversario(anos + 1) <= fin:
        anos += 1
    resto = (fin - aniversario(anos)).days
    ano_vac, fraccion = (anos, 1) if resto == 0 else (anos + 1, resto / 365)
    dias_ano = min(365, (fin - max(ingreso, date(salida.year, 1, 1))).days)
    r = {'diario': diario, 'anos': anos, 'resto': resto, 'dias_ano': dias_ano, 'ano_vac': ano_vac,
         'aguinaldo': diario * 15 * dias_ano / 365, 'dias_vac': dias_vacaciones(ano_vac) * fraccion}
    r['vacaciones'] = r['dias_vac'] * diario
    r['prima_vac'] = r['vacaciones'] * 0.25
    r['finiquito'] = r['aguinaldo'] + r['vacaciones'] + r['prima_vac']
    base = min(max(diario, zona_sm), 2 * zona_sm)
    paga_prima = planta and (motivo != 'renuncia' or anos >= 15)
    r['prima_antiguedad'] = 12 * anos * base if paga_prima else 0
    r['indemnizacion'] = 90 * diario if motivo == 'injustificado' else 0
    r['veinte_dias'] = 20 * anos * diario if motivo == 'injustificado' else 0
    r['total'] = r['finiquito'] + r['prima_antiguedad'] + r['indemnizacion']
    return r


def extra_finiquito():
    """Tres casos resueltos (9-nov-2026): la gente busca "cuánto me toca de finiquito si renuncio" con su caso."""
    from datetime import date
    p = lambda n: f'${n:,.2f}'
    a = calcula_finiquito(15000, date(2025, 8, 1), date(2026, 10, 31), 'renuncia')
    b = calcula_finiquito(15000, date(2022, 11, 1), date(2026, 10, 31), 'injustificado')
    c = calcula_finiquito(25000, date(2010, 7, 1), date(2026, 9, 30), 'renuncia')
    tabla = ''.join(f'<tr><td>{rango}</td><td>{d} días</td></tr>' for rango, d in (
        ('1 año', 12), ('2 años', 14), ('3 años', 16), ('4 años', 18), ('5 años', 20), ('6 a 10 años', 22),
        ('11 a 15 años', 24), ('16 a 20 años', 26), ('21 a 25 años', 28), ('26 a 30 años', 30)))
    return f"""
    <section class="ejemplos">
      <div class="etiqueta">Ejemplos 2026</div>
      <h2>¿Cuánto me toca de finiquito? Tres casos resueltos</h2>
      <p class="lema" style="margin:0">Brutos, antes de ISR, con sueldo mensual entre 30, 15 días de aguinaldo, prima vacacional de 25%
      y sin vacaciones pendientes de años anteriores.</p>
      <h3>1. Renuncias con 1 año y 3 meses y ganas $15,000 al mes</h3>
      <p>Entraste el 1-ago-2025 y tu último día es el 31-oct-2026. Salario diario: $500.
      Aguinaldo: $500 × 15 × {a['dias_ano']}/365 = {p(a['aguinaldo'])}.
      Vacaciones: vas en tu año 2, que da 14 días; llevas {a['resto']} días de ese año: 14 × {a['resto']}/365 = {a['dias_vac']:.2f} días
      = {p(a['vacaciones'])}. Prima vacacional: {p(a['prima_vac'])}. Sin prima de antigüedad (al renunciar se necesitan 15 años).
      Si todavía no tomabas los 12 días de tu primer año (los ganaste el 1-ago-2026 y tenías 6 meses para disfrutarlos, art. 81),
      súmalos: 12 × $500 + 25% = {p(12 * a['diario'] * 1.25)}, y el finiquito sube a {p(a['total'] + 12 * a['diario'] * 1.25)}.
      <b>Finiquito: {p(a['total'])}</b>.</p>
      <h3>2. Te despiden sin causa con 4 años y ganas $15,000 al mes</h3>
      <p>Del 1-nov-2022 al 31-oct-2026, de planta. Finiquito: aguinaldo {p(b['aguinaldo'])} + vacaciones del año 4 (18 días)
      {p(b['vacaciones'])} + prima vacacional {p(b['prima_vac'])} = {p(b['finiquito'])}. Indemnización: 3 meses = {p(b['indemnizacion'])}
      (art. 48). Prima de antigüedad: 12 × 4 × $500 = {p(b['prima_antiguedad'])} (art. 162). <b>Liquidación: {p(b['total'])}</b>.
      Si el patrón queda libre de regresarte o te vas por su culpa (arts. 49 y 52), se suman 20 días × 4 años = {p(b['veinte_dias'])}.</p>
      <h3>3. Renuncias con 16 años de planta y ganas $25,000 al mes</h3>
      <p>Del 1-jul-2010 al 30-sep-2026. Salario diario: $833.33. Aguinaldo: {p(c['aguinaldo'])}. Vacaciones: año 17 (26 días) ×
      {c['resto']}/365 = {p(c['vacaciones'])} + prima vacacional {p(c['prima_vac'])}. Como tienes más de 15 años, sí hay prima de
      antigüedad, pero con el salario topado al doble del mínimo ({p(TOPE_PRIMA_ANTIGUEDAD)}): 12 × 16 × {p(TOPE_PRIMA_ANTIGUEDAD)} =
      {p(c['prima_antiguedad'])}. <b>Finiquito: {p(c['total'])}</b>. Si no tomaste las vacaciones de tu año 16, súmalas.</p>
      <h3>Días de vacaciones por año de servicio (art. 76)</h3>
      <div class="tabla"><table>
        <thead><tr><th>Antigüedad</th><th>Vacaciones</th></tr></thead>
        <tbody>{tabla}</tbody>
      </table></div>
    </section>
"""


def vista_previa(slug, titulo, subtitulo):
    ancho, alto, foto_ancho = 1200, 630, 470
    lienzo = Image.new('RGB', (ancho, alto), (11, 11, 13))
    foto = Image.open(os.path.join(PUBLICO, 'img', 'victoria.jpg')).convert('RGB')
    recorte_alto = round(foto.width * alto / foto_ancho)
    foto = foto.crop((0, 120, foto.width, 120 + recorte_alto)).resize((foto_ancho, alto))
    lienzo.paste(foto, (0, 0))
    sombra = Image.new('L', (160, 1))
    sombra.putdata([round(255 * i / 159) for i in range(160)])
    lienzo.paste((11, 11, 13), (foto_ancho - 160, 0, foto_ancho, alto), sombra.resize((160, alto)))
    d = ImageDraw.Draw(lienzo)
    fuente = lambda nombre, tam: ImageFont.truetype(f'{FUENTES_INTER}/Inter-{nombre}.otf', tam)
    x, oro, crema = foto_ancho + 20, (245, 197, 66), (243, 237, 226)
    d.text((x, 92), 'CALCULADORA GRATIS', font=fuente('SemiBold', 24), fill=oro)
    # El título se parte en renglones que quepan en el panel
    grande, renglones, actual = fuente('Black', 72), [], ''
    for palabra in titulo.split():
        prueba = f'{actual} {palabra}'.strip()
        if d.textlength(prueba, font=grande) > ancho - x - 50 and actual:
            renglones.append(actual)
            actual = palabra
        else:
            actual = prueba
    renglones.append(actual)
    y = 140
    for r in renglones:
        d.text((x, y), r, font=grande, fill=crema)
        y += 84
    d.text((x, y + 18), subtitulo, font=fuente('Regular', 32), fill=(217, 210, 197))
    d.text((x, alto - 92), 'VICTORIA', font=fuente('SemiBold', 26), fill=crema)
    d.text((x + d.textlength('VICTORIA ', font=fuente('SemiBold', 26)), alto - 92), 'THE CEO', font=fuente('SemiBold', 26), fill=oro)
    d.text((x, alto - 56), 'victoriatheceo.vercel.app', font=fuente('Regular', 24), fill=(163, 155, 141))
    lienzo.save(os.path.join(PUBLICO, 'img', f'og-{slug}.jpg'), quality=86, optimize=True)


PLANTILLA = '''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titulo}</title>
  <meta name="description" content="{descripcion}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{titulo}">
  <meta property="og:description" content="{descripcion}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{dominio}/img/og-{slug}.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#0b0b0d">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230b0b0d'/%3E%3Ctext x='16' y='22' font-size='16' font-family='Arial' font-weight='700' fill='%23f5c542' text-anchor='middle'%3EV%3C/text%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/herramientas.css">
  <script type="application/ld+json">{datos_estructurados}</script>
  <script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
  <div class="envoltura">
    <nav class="barra"><a class="marca" href="/">VICTORIA <b>THE CEO</b></a><a class="otra" href="#herramientas">Más calculadoras</a></nav>
    <header>
      <div class="etiqueta">Calculadora gratis</div>
      <h1>{h1}</h1>
      <p class="lema">{lema}</p>
    </header>
    <div class="tarjeta">
      <form id="calculadora" novalidate>{formulario}
      </form>
      <div class="resultado" aria-live="polite">{resultado}
      </div>
      <a class="boton secundario" id="whatsapp" target="_blank" rel="noopener">Mándaselo a alguien por WhatsApp</a>
    </div>
{extra}
    <section>
      <div class="venta">
        <img src="/img/tablero.jpg" alt="El tablero de la CEO: plantilla de finanzas personales en Excel" loading="lazy" width="900" height="900">
        <div class="etiqueta">Para hacerlo completo</div>
        <h2>{venta_titulo}</h2>
        <p class="lema" style="margin:0">{venta_texto}</p>
        <ul><li>Presupuesto 50/30/20</li><li>Fondo de emergencia con meta y avance</li><li>Deudas: bola de nieve y avalancha</li><li>Interés compuesto y metas</li></ul>
        <div id="venta"></div>
      </div>
    </section>

    <section class="faq">
      <h2>Preguntas frecuentes</h2>{faq}
    </section>

    <section id="herramientas">
      <div class="etiqueta">Más calculadoras gratis</div>
      <h2>Herramientas de Victoria</h2>
      <div class="herramientas">{menu}</div>
    </section>
{fuentes}
    <footer>
      Hecho por Victoria The CEO (<a href="/">victoriatheceo</a>). Victoria es un personaje creado con inteligencia artificial.
      Herramienta educativa: no es asesoría financiera, fiscal, legal ni de inversión. Revisa tu caso con un profesional.
    </footer>
  </div>
  <script src="/comun.js"></script>
  <script>
{script}
bloqueVenta(document.getElementById('venta'), '{slug}');
document.getElementById('whatsapp').href = 'https://wa.me/?text=' + encodeURIComponent('{compartir} {url}?ref=wa');
  </script>
</body>
</html>
'''


def e(texto):
    return html.escape(texto, quote=True)


def menu(actual=None):
    enlaces = []
    for h in HERRAMIENTAS:
        clase = ' class="actual"' if h['slug'] == actual else ''
        enlaces.append(f'<a href="/{h["slug"]}"{clase}>{e(h["menu"])}<small>{e(h["menu_nota"])}</small></a>')
    return ''.join(enlaces)


EXTRAS = {'aguinaldo': extra_aguinaldo, 'finiquito': extra_finiquito}


def pagina(h):
    url = f'{DOMINIO}/{h["slug"]}'
    datos = [
        {'@context': 'https://schema.org', '@type': 'WebApplication', 'name': h['titulo'], 'url': url,
         'applicationCategory': 'FinanceApplication', 'operatingSystem': 'Web', 'inLanguage': 'es-MX',
         'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'MXN'}},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': p, 'acceptedAnswer': {'@type': 'Answer', 'text': r}} for p, r in h['faq']]},
    ]
    faq = ''.join(f'\n      <h3>{e(p)}</h3>\n      <p>{e(r)}</p>' for p, r in h['faq'])
    fuentes = ''
    if h['fuentes']:
        fuentes = ('\n    <section><div class="etiqueta">Fuentes</div><ul class="fuentes">'
                   + ''.join(f'<li><a href="{u}" rel="noopener" target="_blank">{e(t)}</a></li>' for t, u in h['fuentes'])
                   + '</ul></section>\n')
    return PLANTILLA.format(
        titulo=e(h['titulo']), descripcion=e(h['descripcion']), url=url, dominio=DOMINIO, h1=h['h1'], lema=e(h['lema']),
        formulario=h['formulario'], resultado=h['resultado'], venta_titulo=e(h['venta_titulo']), venta_texto=e(h['venta_texto']),
        faq=faq, extra=EXTRAS.get(h['slug'], lambda: '')(), menu=menu(h['slug']), fuentes=fuentes, script=h['script'], slug=h['slug'], compartir=h['compartir'],
        datos_estructurados=json.dumps(datos, ensure_ascii=False).replace('</', '<\\/'))


def main():
    for h in HERRAMIENTAS:
        vista_previa(h['slug'], *VISTA_PREVIA[h['slug']])
        ruta = os.path.join(PUBLICO, f'{h["slug"]}.html')
        open(ruta, 'w').write(pagina(h))
        print(f'{h["slug"]}.html ({os.path.getsize(ruta) // 1024} KB)')
    urls = [DOMINIO + '/'] + [f'{DOMINIO}/{h["slug"]}' for h in HERRAMIENTAS]
    open(os.path.join(PUBLICO, 'sitemap.xml'), 'w').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    # URLs limpias (/aguinaldo) con rewrites y no con cleanUrls: cleanUrls redirige todo .html, también
    # el archivo de verificación de Google Search Console, y Google lo pide sin redirección.
    ruta_vercel = os.path.join(RAIZ, 'sitio', 'vercel.json')
    vercel = json.load(open(ruta_vercel))
    vercel['rewrites'] = [{'source': f'/{h["slug"]}', 'destination': f'/{h["slug"]}.html'} for h in HERRAMIENTAS]
    open(ruta_vercel, 'w').write(json.dumps(vercel, ensure_ascii=False, indent=2) + '\n')
    open(os.path.join(PUBLICO, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {DOMINIO}/sitemap.xml\n')
    # La portada lleva el mismo menú, en HTML fijo para que Google siga los enlaces.
    portada = os.path.join(PUBLICO, 'index.html')
    texto = open(portada).read()
    inicio, fin = '<!--herramientas-->', '<!--/herramientas-->'
    if inicio in texto:
        texto = texto[:texto.index(inicio) + len(inicio)] + menu() + texto[texto.index(fin):]
        open(portada, 'w').write(texto)
    print(f'sitemap.xml ({len(urls)} páginas) y robots.txt')


if __name__ == '__main__':
    main()
