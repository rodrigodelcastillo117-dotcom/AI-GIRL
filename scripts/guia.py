"""Arma la guía gratis "Las 30 reglas de la CEO" en PDF desde producto/guia/reglas.json.

Uso: python guia.py      → sitio/public/guia/las-30-reglas-de-la-ceo.pdf

v2 (12-nov-2026). Rodrigo: "mejora las reglas, hazlo que valga 231 pesos… hazlo increíble". Lo mismo que trae un
producto de pago, en el negro y oro de la página (Playfair Display + Inter):
- portada, cómo usarla e índice con número de página;
- una regla por página (A5, se lee en el celular) con su fuente, "Hazlo hoy" y un ejercicio "Tu turno" para escribir;
- Parte 5 "Tu tablero en papel": presupuesto 50/30/20, fondo de emergencia, deudas, días de trabajo y primer capital
  (solo fórmulas y espacios para llenar: ningún dato nuevo que verificar);
- el reto de 30 días (una regla por día), las 7 calculadoras gratis con enlace y el cierre con la plantilla.
Se imprime con el Chromium de Playwright (las fuentes llegan de Google Fonts).
"""
import base64
import html
import json
import os
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'sitio', 'public', 'guia')
SITIO = 'https://victoriatheceo.vercel.app'
e = html.escape

# Ejercicio de cada regla (solo preguntas para el lector: no agrega datos).
TU_TURNO = {
    'Págate primero': ['Cobro el día:', 'Mi 10% es: $', 'Lo aparto en:'],
    'La regla 50/30/20': ['Mi ingreso neto: $', '50% necesidades: $', '30% deseos: $', '20% ahorro y deudas: $'],
    'Fondo de emergencia primero': ['Mis gastos fijos al mes: $', '× 3 = $', 'Lo junto en (meses):'],
    'Automatiza el ahorro': ['Transferencia automática de $', 'El día:', 'A la cuenta:'],
    'La regla del 72': ['Tasa de mi ahorro: ____ %', '72 ÷ tasa = ____ años para duplicarse'],
    'El tiempo pesa más que el monto': ['Empiezo este mes con: $', 'Cada mes voy a sumar: $'],
    'La riqueza es lo que no ves': ['Mi próxima compra grande:', '¿Para quién es en realidad?'],
    'Los primeros 100 mil son los más difíciles': ['Mi primer capital: $', 'Fecha límite:', 'Necesito apartar al mes: $'],
    'Paga el total de la tarjeta': ['Saldo de mi tarjeta: $', 'Pago mínimo: $', 'Meses pagando solo el mínimo:'],
    'Bola de nieve o avalancha': ['Deuda más chica:', 'Deuda con la tasa más alta:', 'Mi método:'],
    'Cuidado con la inflación de tu estilo de vida': ['Mi próximo aumento: $', 'La mitad que ahorro: $'],
    'El efecto Diderot': ['Lo que quiero comprar:', 'Lo que después voy a querer cambiar:'],
    'Regla número 1: no pierdas dinero': ['¿Dónde está mi dinero hoy?', 'Lo explico en una frase:'],
    'Tu círculo de competencia': ['1.', '2.', '3.'],
    'No pongas todo en un solo lugar': ['Mis fuentes de ingreso:', 'Dónde guardo mi ahorro:'],
    'Perder duele el doble': ['Antes de entrar, salgo si:', 'Mi límite de pérdida: $'],
    'Lo que ya gastaste no vuelve': ['Lo que mantengo solo por lo gastado:', 'Si empezara hoy, ¿lo haría?'],
    'Todo tiene un costo de oportunidad': ['Mi decisión:', 'Lo que dejo al elegirla:'],
    'El primer número manda': ['Mi próxima negociación:', 'Mi número:'],
    'Minimiza arrepentimientos, no riesgos': ['La decisión que pospongo:', 'A los 80, ¿me arrepentiría de no hacerlo?'],
    'El 20% que importa': ['Mis 3 clientes o actividades que más dejan:', '1.', '2.', '3.'],
    'Vende tu porqué': ['Mi porqué en 15 palabras:', ''],
    'La ley de Parkinson': ['Proyecto:', 'Tiempo que le daría:', 'La mitad:'],
    'La regla de los 2 minutos': ['☐', '☐', '☐'],
    'Trágate el sapo': ['El sapo de mañana:'],
    'Mejora 1% cada día': ['Mi hábito:', 'El 1% de mañana:'],
    'Lo pendiente no te deja dormir': ['Mi pendiente más grande:', 'El siguiente paso:'],
    'Escribe lo que te preocupa': ['Lo que me preocupa:', 'Lo que sí depende de mí:'],
    'El suspiro cíclico': ['☐ Lo probé hoy', 'Cómo me sentí:'],
    'Las relaciones son la inversión': ['A quién llamo hoy:', '☐ Lo hice'],
}

ESTILO = '''@page { size: A5; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, sans-serif; color: #f4efe6; background: #070707; font-variant-numeric: lining-nums; }
.pagina { width: 148mm; height: 210mm; padding: 17mm 14mm 16mm; position: relative; overflow: hidden; page-break-after: always;
  background: radial-gradient(130% 70% at 100% 0%, #241b0d 0%, #0b0b0c 52%, #070707 100%); }
.pagina::before { content: ""; position: absolute; inset: 7mm; border: 1px solid rgba(216,178,90,.16); border-radius: 3mm; pointer-events: none; }
.folio { position: absolute; bottom: 9.5mm; left: 0; right: 0; text-align: center; font-size: 7pt; letter-spacing: .3em; color: #8c867b; }
.etiqueta { font-size: 7.5pt; letter-spacing: .32em; text-transform: uppercase; color: #d8b25a; font-weight: 700; }
h1, h2, h3 { font-family: "Playfair Display", Georgia, serif; font-weight: 600; letter-spacing: -.005em; }
h1 { font-size: 34pt; line-height: 1.0; margin: 4mm 0 5mm; }
h1 em, h2 em { color: #f0d488; font-style: italic; }
h2 { font-size: 21pt; line-height: 1.12; margin: 5mm 0 6mm; }
h2.grande { font-size: 34pt; }
h3 { font-size: 20pt; line-height: 1.12; margin: 3mm 0 5mm; }
p { font-size: 10.5pt; line-height: 1.55; color: #d6cfc2; margin: 0 0 4mm; }
.nota { font-size: 9pt; color: #b8b1a4; }
.portada { padding: 0; }
.portada::before { display: none; }
.portada img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.portada .velo { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(7,7,7,0) 28%, rgba(7,7,7,.94) 70%); }
.portada .texto { position: absolute; left: 13mm; right: 13mm; bottom: 15mm; }
.portada p { font-size: 10pt; }
.marca { font-size: 8.5pt; letter-spacing: .32em; font-weight: 700; }
.marca b { color: #d8b25a; }
.sellos { display: flex; flex-wrap: wrap; gap: 2mm; margin-top: 4mm; }
.sellos span { border: 1px solid rgba(216,178,90,.6); color: #f0d488; font-size: 7pt; letter-spacing: .1em; text-transform: uppercase; padding: 1.5mm 3mm; border-radius: 10mm; }
.pasos { display: grid; gap: 3.5mm; margin: 6mm 0; }
.pasos div { display: grid; grid-template-columns: 9mm 1fr; gap: 3mm; align-items: center; }
.pasos b { width: 9mm; height: 9mm; border-radius: 50%; display: grid; place-items: center; background: #d8b25a; color: #111; font-weight: 800; }
.pasos span { font-size: 10pt; color: #d6cfc2; line-height: 1.45; }
.pasos strong { color: #f4efe6; }
.firma { color: #d8b25a; font-weight: 600; font-family: "Playfair Display", serif; font-style: italic; font-size: 12pt; }
.ind { display: flex; align-items: baseline; gap: 2mm; padding: 2.6mm 0; border-bottom: 1px solid rgba(255,255,255,.06); font-size: 10.5pt; }
.ind i { flex: 1; border-bottom: 1px dotted rgba(216,178,90,.35); }
.ind b { color: #d8b25a; font-family: "Playfair Display", serif; }
.divisor { display: flex; flex-direction: column; justify-content: center; }
.linea { width: 30mm; height: 2px; background: linear-gradient(90deg, #f0d488, #a8843a); margin-bottom: 5mm; }
.numero { position: absolute; right: 12mm; top: 9mm; font-family: "Playfair Display", serif; font-size: 66pt; font-weight: 700; color: rgba(216,178,90,.17); line-height: 1; }
.regla { padding-top: 27mm; }
.cuerpo { font-size: 11.5pt; }
.accion { margin-top: 4mm; padding: 4mm 5mm; border-left: 3px solid #d8b25a; background: rgba(216,178,90,.08); border-radius: 0 2mm 2mm 0; font-size: 10.5pt; line-height: 1.45; }
.accion span, .turno > span { display: block; font-size: 7pt; letter-spacing: .28em; text-transform: uppercase; color: #d8b25a; font-weight: 700; margin-bottom: 1.5mm; }
.turno { margin-top: 5mm; padding: 4mm 5mm 3mm; border: 1px dashed rgba(216,178,90,.35); border-radius: 2mm; }
.campo { display: flex; align-items: flex-end; gap: 2mm; min-height: 8mm; font-size: 9.5pt; color: #cfc8bb; }
.campo span { white-space: nowrap; }
.campo i { flex: 1; border-bottom: 1px solid rgba(244,239,230,.28); margin-bottom: 1mm; }
.hecho { margin-top: 2mm; font-size: 8.5pt; color: #8c867b; }
.fuente { position: absolute; left: 14mm; right: 14mm; bottom: 15mm; font-size: 7.5pt; color: #8c867b; border-top: 1px solid rgba(216,178,90,.22); padding-top: 2.5mm; margin: 0; }
.hojas h3 { margin-top: 2mm; }
table.hoja { width: 100%; border-collapse: collapse; margin: 3mm 0 4mm; font-size: 9pt; }
table.hoja th { text-align: left; font-size: 7pt; letter-spacing: .18em; text-transform: uppercase; color: #d8b25a; padding: 2mm 2mm; border-bottom: 1px solid rgba(216,178,90,.45); }
table.hoja td { padding: 2.6mm 2mm; border-bottom: 1px solid rgba(244,239,230,.14); color: #cfc8bb; height: 8mm; }
.reto { display: grid; grid-template-columns: 1fr 1fr; gap: 1.4mm 4mm; }
.dia { display: grid; grid-template-columns: 7mm 1fr 4mm; align-items: center; gap: 1.5mm; font-size: 7.6pt; padding: 1.2mm 0; border-bottom: 1px solid rgba(255,255,255,.06); }
.dia b { color: #d8b25a; font-family: "Playfair Display", serif; font-size: 9pt; }
.dia span { color: #d6cfc2; line-height: 1.25; }
.dia i { color: #d8b25a; font-style: normal; }
.calcs { display: grid; gap: 2.6mm; }
.calc { display: grid; padding: 3mm 4mm; border-radius: 2.5mm; border: 1px solid rgba(216,178,90,.28); background: rgba(216,178,90,.05); text-decoration: none; color: inherit; }
.calc b { font-family: "Playfair Display", serif; font-size: 11.5pt; font-weight: 600; }
.calc span { font-size: 8.5pt; color: #b8b1a4; }
.calc em { font-style: normal; font-size: 7.5pt; color: #d8b25a; margin-top: 1mm; }
.boton { display: inline-block; margin: 2mm 0 6mm; padding: 3.5mm 7mm; border-radius: 10mm; background: linear-gradient(180deg, #f0d488, #d8b25a); color: #111; font-weight: 800; text-decoration: none; font-size: 10.5pt; }
.avisos { margin-top: 8mm; padding-left: 4mm; font-size: 7.5pt; color: #8c867b; line-height: 1.5; }
'''

CALCULADORAS = [
    ('Aguinaldo 2026', 'Cuánto te toca y cuánto paga ISR', '/aguinaldo'),
    ('¿Te alcanza tu sueldo?', 'Renta, comida y lo que te queda', '/te-alcanza-tu-sueldo'),
    ('Finiquito y liquidación', 'Cuánto te toca si renuncias o te corren', '/finiquito'),
    ('Interés compuesto', 'Cuánto crece tu ahorro con el tiempo', '/interes-compuesto'),
    ('Regla 50/30/20', 'Tu sueldo en tres partes', '/regla-50-30-20'),
    ('Fondo de emergencia', 'Cuánto necesitas y cuándo llegas', '/fondo-de-emergencia'),
    ('Salir de deudas', 'Bola de nieve o avalancha', '/pagar-deudas'),
]


def imagen(ruta, ancho=1000):
    jpg = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', ruta, '-vf', f'scale={ancho}:-2', '-q:v', '3', '-f', 'mjpeg', '-'],
                         capture_output=True, check=True).stdout
    return 'data:image/jpeg;base64,' + base64.b64encode(jpg).decode()


def lineas(campos):
    return ''.join(f'<div class="campo"><span>{e(c)}</span><i></i></div>' for c in campos)


def tabla(cabeza, filas):
    return ('<table class="hoja"><tr>' + ''.join(f'<th>{e(h)}</th>' for h in cabeza) + '</tr>'
            + ''.join('<tr>' + ''.join(f'<td>{e(c)}</td>' for c in fila) + '</tr>' for fila in filas) + '</table>')


def main():
    datos = json.load(open(os.path.join(RAIZ, 'producto', 'guia', 'reglas.json')))
    foto = imagen(os.path.join(RAIZ, 'assets', 'cuadro-jet-final.png'))
    total = sum(len(s['reglas']) for s in datos['secciones'])
    paginas = []  # (html, entrada del índice o None)

    def pagina(cuerpo, clase='', indice=None):
        paginas.append((f'<section class="pagina {clase}">{cuerpo}<div class="folio">{{FOLIO}}</div></section>', indice))

    paginas.append((f'''<section class="pagina portada">
  <img src="{foto}" alt="Victoria y Capital">
  <div class="velo"></div>
  <div class="texto">
    <div class="marca">VICTORIA <b>THE CEO</b></div>
    <h1>Las {total} reglas<br><em>de la CEO</em></h1>
    <p>{e(datos["subtitulo"])}</p>
    <div class="sellos"><span>{total} reglas con fuente</span><span>{total} ejercicios</span><span>Reto de 30 días</span><span>Hojas para llenar</span></div>
  </div>
</section>''', None))

    pagina(f'''<div class="etiqueta">Antes de empezar</div>
<h2>Esta guía es para usarse, no para guardarse.</h2>
<p>Soy Victoria. Cada regla tiene una fuente real que puedes buscar: un libro, un estudio o una institución. Nada de
fórmulas mágicas. Si algo es mi opinión, te lo digo.</p>
<div class="pasos">
  <div><b>1</b><span><strong>Lee una regla.</strong> Una por página. Dos minutos.</span></div>
  <div><b>2</b><span><strong>Haz la acción.</strong> Cada regla trae algo concreto para hoy.</span></div>
  <div><b>3</b><span><strong>Escribe tu turno.</strong> Imprímela o llénala en tu tablet: con tus números se te queda.</span></div>
</div>
<p>Al final tienes tu tablero en papel, el reto de 30 días y mis 7 calculadoras gratis.</p>
<p class="firma">— Victoria y Capital</p>''', 'intro')

    paginas.append(('{INDICE}', None))

    numero = 0
    for i, seccion in enumerate(datos['secciones'], 1):
        pagina(f'''<div class="etiqueta">Parte {i}</div>
<h2 class="grande">{e(seccion["nombre"])}</h2>
<div class="linea"></div>
<p>{len(seccion["reglas"])} reglas · reglas {numero + 1} a {numero + len(seccion["reglas"])}</p>''', 'divisor', f'Parte {i} · {seccion["nombre"]}')
        for regla in seccion['reglas']:
            numero += 1
            turno = TU_TURNO.get(regla['titulo'], ['Lo que voy a hacer:', 'Cuándo:'])
            pagina(f'''<div class="numero">{numero:02d}</div>
<div class="etiqueta">{e(seccion["nombre"])}</div>
<h3>{e(regla["titulo"])}</h3>
<p class="cuerpo">{e(regla["texto"])}</p>
<div class="accion"><span>Hazlo hoy</span>{e(regla["accion"])}</div>
<div class="turno"><span>Tu turno</span>{lineas(turno)}<div class="hecho">☐ Lo hice el ___ / ___</div></div>
<p class="fuente">Fuente: {e(regla["fuente"])}</p>''', 'regla')

    pagina('''<div class="etiqueta">Parte 5</div>
<h2 class="grande">Tu tablero en papel</h2>
<div class="linea"></div>
<p>Cinco hojas para poner las reglas en tus números. Solo fórmulas: tú pones los datos.</p>''', 'divisor', 'Parte 5 · Tu tablero en papel')
    pagina(f'''<div class="etiqueta">Hoja 1 · reglas 1 y 2</div><h3>Mi presupuesto 50/30/20</h3>
<p class="nota">Ingreso neto = lo que te llega después de impuestos.</p>
{tabla(['', 'Fórmula', 'Mi cantidad'], [['Ingreso neto', '', '$'], ['Necesidades', '× 0.50', '$'], ['Deseos', '× 0.30', '$'], ['Ahorro y deudas', '× 0.20', '$'], ['Págate primero', 'mínimo × 0.10', '$']])}
<p class="nota">Es un punto de partida: si tu renta se come más de la mitad, ajusta los deseos antes que el ahorro.</p>''', 'hojas')
    pagina(f'''<div class="etiqueta">Hoja 2 · regla 3</div><h3>Mi fondo de emergencia</h3>
{tabla(['Gasto fijo del mes', '$'], [['Renta o casa', ''], ['Comida', ''], ['Luz, agua, gas, internet', ''], ['Transporte', ''], ['Deudas (pagos mínimos)', ''], ['Otros', ''], ['Total al mes', '']])}
{lineas(['Meta de 3 meses (total × 3): $', 'Meta de 6 meses (total × 6): $', 'Puedo apartar al mes: $', 'Llego en (meta ÷ lo que aparto): ____ meses'])}''', 'hojas')
    pagina(f'''<div class="etiqueta">Hoja 3 · reglas 9 y 10</div><h3>Mis deudas</h3>
{tabla(['Deuda', 'Saldo', 'Tasa / CAT', 'Pago mínimo'], [['', '$', '%', '$']] * 6)}
<p class="nota"><b>Avalancha:</b> todo lo extra a la de tasa más alta (pagas menos intereses). <b>Bola de nieve:</b> todo lo extra
a la más chica (ganas impulso). En ambas, a las demás les pagas el mínimo.</p>
{lineas(['Mi método:', 'Primero ataco:'])}''', 'hojas')
    pagina(f'''<div class="etiqueta">Hoja 4 · reglas 7 y 12</div><h3>¿Cuántos días de trabajo cuesta?</h3>
<p class="nota">Sueldo diario = sueldo del mes ÷ 30. Días de trabajo = precio ÷ sueldo diario.</p>
{lineas(['Mi sueldo diario: $'])}
{tabla(['Lo que quiero', 'Precio', 'Días de trabajo'], [['', '$', ''], ['', '$', ''], ['', '$', ''], ['', '$', ''], ['', '$', '']])}
<p class="nota">Si al verlo en días ya no lo quieres tanto, te ahorraste algo más que dinero.</p>''', 'hojas')
    pagina(f'''<div class="etiqueta">Hoja 5 · reglas 6 y 8</div><h3>Mi primer capital</h3>
{lineas(['Mi meta: $', 'Fecha: ', 'Meses que faltan: ', 'Apartar al mes (meta ÷ meses): $'])}
{tabla(['Mes', 'Aparté', 'Llevo'], [[m, '$', '$'] for m in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']])}''', 'hojas')

    reto = []
    n = 0
    for s in datos['secciones']:
        for r in s['reglas']:
            n += 1
            reto.append(f'<div class="dia"><b>{n:02d}</b><span>{e(r["titulo"])}</span><i>☐</i></div>')
    pagina(f'''<div class="etiqueta">El reto</div><h3>30 días, una regla por día</h3>
<p class="nota">Lee la regla del día, haz su acción y palomea. Si te saltas un día, sigue al siguiente.</p>
<div class="reto">{"".join(reto)}</div>''', 'hojas', 'El reto de 30 días')

    tarjetas = ''.join(f'<a class="calc" href="{SITIO}{r}?ref=guia"><b>{e(t)}</b><span>{e(d)}</span><em>victoriatheceo.vercel.app{r}</em></a>'
                       for t, d, r in CALCULADORAS)
    pagina(f'''<div class="etiqueta">Gratis · sin registrarte</div><h3>Mis 7 calculadoras</h3>
<p class="nota">Toca cualquiera: abre en tu celular.</p>
<div class="calcs">{tarjetas}</div>''', 'hojas', 'Las 7 calculadoras gratis')

    avisos = ''.join(f'<li>{e(a)}</li>' for a in datos['avisos'])
    pagina(f'''<div class="etiqueta">Sigamos</div>
<h2>Las reglas ya las tienes. Ahora, tus números.</h2>
<p><b>El tablero de la CEO</b> es mi plantilla para Excel y Google Sheets: escribes en lo amarillo y se calcula solo
tu presupuesto 50/30/20, tu fondo de emergencia, el orden de tus deudas, tu interés compuesto y tus metas.</p>
<a class="boton" href="{SITIO}/?ref=guia#tablero">Ver la plantilla</a>
<p>Y una regla nueva cada dos días en <b>@victoriatheceo</b> · Instagram, TikTok y YouTube.</p>
<ul class="avisos">{avisos}</ul>''', 'cierre', 'Sigamos')

    # Folios e índice (cada sección es una página A5)
    entradas = []
    for k, (h, ind) in enumerate(paginas, 1):
        if ind:
            entradas.append((ind, k))
    indice = ''.join(f'<div class="ind"><span>{e(t)}</span><i></i><b>{p}</b></div>' for t, p in entradas)
    cuerpo = []
    for k, (h, _) in enumerate(paginas, 1):
        if h == '{INDICE}':
            h = f'<section class="pagina indice"><div class="etiqueta">Contenido</div><h2>Lo que vas a encontrar</h2>{indice}<div class="folio">{k}</div></section>'
        cuerpo.append(h.replace('{FOLIO}', str(k)))

    documento = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Las {total} reglas de la CEO</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500;1,600&display=swap" rel="stylesheet">
<style>
{ESTILO}</style></head><body>{"".join(cuerpo)}</body></html>'''
    os.makedirs(SALIDA, exist_ok=True)
    ruta_html = os.path.join(SALIDA, 'vista-previa.html')
    open(ruta_html, 'w').write(documento)
    ruta_pdf = os.path.join(SALIDA, 'las-30-reglas-de-la-ceo.pdf')
    script = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"
              f"await p.goto('file://{ruta_html}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);"
              f"await p.pdf({{path:'{ruta_pdf}',format:'A5',printBackground:true}});await b.close();}})();")
    subprocess.run(['node', '-e', script], check=True)
    os.remove(ruta_html)
    print(f'Guía lista: {ruta_pdf} ({numero} reglas, {len(cuerpo)} páginas, {os.path.getsize(ruta_pdf) // 1024} KB)')


if __name__ == '__main__':
    main()
