"""Kit CEO · "Las 30 reglas de la CEO — Edición CEO" (PDF de pago, 12-nov-2026).

Rodrigo: "agrega cosas top a las 30 reglas: ejercicios, lecturas, casos, lecciones, terminología… que realmente valga
231 pesos por el contenido". La guía gratis (guia.py) se queda igual para GUÍA; esta es la versión completa del Kit:
por cada regla, la regla + Lectura a fondo + Caso real (ilustrativo) + Error común + Ejercicio paso a paso + Términos +
Para profundizar; luego 5 lecciones que unen varias reglas, el glosario de 40 términos, el tablero en papel, el reto de
30 días, las 7 calculadoras y el código para las revisiones de IA sin límite.

Contenido: producto/guia/edicion_ceo_1.json (reglas 1-15) y edicion_ceo_2.json (16-30, glosario, lecciones).
Uso: python3 scripts/edicion_ceo.py <CODIGO>   → producto/kit/edicion-ceo.pdf (NO va al sitio ni al repo: es de pago)
El código es el que Vercel tiene en KIT_CODIGOS (proyecto victoriatheceo) y desbloquea "Victoria revisa tus números".
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guia  # noqa: E402  (mismo diseño: ESTILO, imagen, lineas, tabla, TU_TURNO, CALCULADORAS)

RAIZ = guia.RAIZ
e = guia.e
EXTRA = '''
.lectura p { font-size: 10.6pt; line-height: 1.62; }
.caja-caso { margin-top: 3mm; padding: 4.5mm 5mm; border-radius: 2.5mm; background: rgba(91,132,230,.08); border: 1px solid rgba(91,132,230,.35); }
.caja-caso b { display: block; font-family: "Playfair Display", serif; font-size: 12pt; margin-bottom: 1.5mm; color: #cfdcff; }
.caja-caso p { font-size: 9.8pt; margin: 0; }
.caja-error { margin-top: 4mm; padding: 4mm 5mm; border-radius: 2.5mm; background: rgba(176,71,90,.09); border: 1px solid rgba(176,71,90,.4); }
.caja-error p { font-size: 9.8pt; margin: 0; }
.mini { display: block; font-size: 7pt; letter-spacing: .28em; text-transform: uppercase; font-weight: 700; margin-bottom: 1.5mm; color: #d8b25a; }
.caja-error .mini { color: #e58a9b; } .caja-caso .mini { color: #9db4f2; }
ol.pasos-e { margin: 2mm 0 4mm; padding-left: 5mm; font-size: 10pt; line-height: 1.5; color: #d6cfc2; }
ol.pasos-e li { margin-bottom: 1.6mm; }
.termino { margin: 0 0 2.4mm; font-size: 9.3pt; line-height: 1.45; color: #cfc8bb; }
.termino b { color: #f0d488; }
.profundiza { margin-top: 4mm; padding-top: 3mm; border-top: 1px solid rgba(216,178,90,.25); font-size: 8.8pt; color: #b8b1a4; }
.glos { columns: 2; column-gap: 6mm; }
.glos .termino { break-inside: avoid; font-size: 8.2pt; }
.codigo-kit { margin: 6mm 0; padding: 6mm; border: 2px dashed #d8b25a; border-radius: 3mm; text-align: center; }
.codigo-kit b { display: block; font-family: "Playfair Display", serif; font-size: 22pt; letter-spacing: .08em; color: #f0d488; margin-top: 2mm; }
'''


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    codigo = sys.argv[1].strip().upper()
    base = json.load(open(os.path.join(RAIZ, 'producto', 'guia', 'reglas.json')))
    p1 = json.load(open(os.path.join(RAIZ, 'producto', 'guia', 'edicion_ceo_1.json')))
    p2 = json.load(open(os.path.join(RAIZ, 'producto', 'guia', 'edicion_ceo_2.json')))
    extra = {x['n']: x for x in p1 + p2['reglas']}
    total = sum(len(s['reglas']) for s in base['secciones'])
    assert len(extra) == total, f'faltan reglas: {sorted(set(range(1, total + 1)) - set(extra))}'
    foto = guia.imagen(os.path.join(RAIZ, 'assets', 'cuadro-jet-final.png'))
    paginas = []

    def pagina(cuerpo, clase='', indice=None):
        paginas.append((f'<section class="pagina {clase}">{cuerpo}<div class="folio">{{FOLIO}}</div></section>', indice))

    paginas.append((f'''<section class="pagina portada"><img src="{foto}" alt="Victoria y Capital"><div class="velo"></div>
<div class="texto"><div class="marca">VICTORIA <b>THE CEO</b> · KIT CEO</div>
<h1>Las {total} reglas<br><em>Edición CEO</em></h1>
<p>Cada regla a fondo: lectura, caso real, el error que todos cometen, ejercicio paso a paso y los términos que tienes que dominar.</p>
<div class="sellos"><span>{total} lecturas</span><span>{total} casos</span><span>5 lecciones</span><span>Glosario de {len(p2["glosario"])} términos</span></div></div></section>''', None))

    pagina(f'''<div class="etiqueta">Tu Kit CEO</div><h2>Gracias por confiar en mí.</h2>
<p>Esta es la versión completa de mis reglas. La gratis te dice qué hacer; esta te explica por qué, cómo se ve en la vida
real y cómo hacerlo con tus números, paso a paso.</p>
<div class="codigo-kit"><span class="mini">Tu código para las revisiones de IA sin límite</span><b>{e(codigo)}</b></div>
<p class="nota">Escríbelo en cualquier calculadora de victoriatheceo.vercel.app → "Victoria, revisa mis números" → "Ya tengo mi
código". Es personal: no lo compartas.</p>
<p class="firma">— Victoria y Capital</p>''', 'intro')
    paginas.append(('{INDICE}', None))

    n = 0
    for i, s in enumerate(base['secciones'], 1):
        pagina(f'''<div class="etiqueta">Parte {i}</div><h2 class="grande">{e(s["nombre"])}</h2><div class="linea"></div>
<p>{len(s["reglas"])} reglas a fondo</p>''', 'divisor', f'Parte {i} · {s["nombre"]}')
        for r in s['reglas']:
            n += 1
            x = extra[n]
            pagina(f'''<div class="numero">{n:02d}</div><div class="etiqueta">{e(s["nombre"])}</div><h3>{e(r["titulo"])}</h3>
<p class="cuerpo">{e(r["texto"])}</p><div class="accion"><span>Hazlo hoy</span>{e(r["accion"])}</div>
<div class="turno"><span>Tu turno</span>{guia.lineas(guia.TU_TURNO.get(r["titulo"], ["Lo que voy a hacer:", "Cuándo:"]))}</div>
<p class="fuente">Fuente: {e(r["fuente"])}</p>''', 'regla')
            pagina(f'''<div class="etiqueta">Regla {n:02d} · Lectura a fondo</div><h3>{e(r["titulo"])}</h3>
<div class="lectura">{"".join(f"<p>{e(par)}</p>" for par in x["lectura"].split(chr(10)) if par.strip())}</div>''', 'hojas')
            pasos = ''.join(f'<li>{e(p)}</li>' for p in x['ejercicio'])
            terminos = ''.join(f'<p class="termino"><b>{e(t["termino"])}.</b> {e(t["definicion"])}</p>' for t in x['terminos'])
            pagina(f'''<div class="etiqueta">Regla {n:02d} · En la vida real</div>
<div class="caja-caso"><span class="mini">Caso</span><b>{e(x["caso"]["titulo"])}</b><p>{e(x["caso"]["texto"])}</p></div>
<div class="caja-error"><span class="mini">El error común</span><p>{e(x["error_comun"])}</p></div>''', 'hojas')
            pagina(f'''<div class="etiqueta">Regla {n:02d} · Ejercicio</div><h3>Hazlo con tus números</h3><ol class="pasos-e">{pasos}</ol>
<span class="mini">Términos clave</span>{terminos}
<p class="profundiza"><b>Para profundizar:</b> {e(x["para_profundizar"])}</p>''', 'hojas')

    pagina('''<div class="etiqueta">Parte 5</div><h2 class="grande">Lecciones CEO</h2><div class="linea"></div>
<p>Cinco lecciones que unen varias reglas en un plan.</p>''', 'divisor', 'Parte 5 · Lecciones CEO')
    for k, l in enumerate(p2['lecciones'], 1):
        pagina(f'''<div class="etiqueta">Lección {k}</div><h3>{e(l["titulo"])}</h3>
<div class="lectura">{"".join(f"<p>{e(par)}</p>" for par in l["texto"].split(chr(10)) if par.strip())}</div>
<div class="accion"><span>Tu acción</span>{e(l["accion"])}</div>''', 'hojas')

    glos = sorted(p2['glosario'], key=lambda t: t['termino'].lower())
    mitad = (len(glos) + 1) // 2
    for k, parte in enumerate((glos[:mitad], glos[mitad:]), 1):
        pagina(f'''<div class="etiqueta">Glosario {k}/2</div><h3>Las palabras del dinero</h3>
<div class="glos">{"".join(f'<p class="termino"><b>{e(t["termino"])}.</b> {e(t["definicion"])}</p>' for t in parte)}</div>''', 'hojas',
               'Glosario' if k == 1 else None)

    # tablero en papel, reto y calculadoras: los mismos de la guía gratis
    gratis = open(os.path.join(RAIZ, 'scripts', 'guia.py')).read()  # solo para recordar que deben coincidir
    del gratis
    tarjetas = ''.join(f'<a class="calc" href="{guia.SITIO}{r}?ref=kit"><b>{e(t)}</b><span>{e(d)}</span><em>victoriatheceo.vercel.app{r}</em></a>'
                       for t, d, r in guia.CALCULADORAS)
    pagina(f'''<div class="etiqueta">Con tu código, sin límite</div><h3>Mis 7 calculadoras + Victoria IA</h3>
<p class="nota">En cada una, "Victoria, revisa mis números" te dice qué ve, qué revisar y tu plan de 3 pasos.</p>
<div class="calcs">{tarjetas}</div>''', 'hojas', 'Las 7 calculadoras + IA')

    entradas = [(ind, k) for k, (h, ind) in enumerate(paginas, 1) if ind]
    indice = ''.join(f'<div class="ind"><span>{e(t)}</span><i></i><b>{p}</b></div>' for t, p in entradas)
    cuerpo = []
    for k, (h, _) in enumerate(paginas, 1):
        if h == '{INDICE}':
            h = f'<section class="pagina indice"><div class="etiqueta">Contenido</div><h2>Lo que vas a encontrar</h2>{indice}<div class="folio">{k}</div></section>'
        cuerpo.append(h.replace('{FOLIO}', str(k)))
    documento = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Las {total} reglas de la CEO · Edición CEO</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500;1,600&display=swap" rel="stylesheet">
<style>{guia.ESTILO}{EXTRA}</style></head><body>{"".join(cuerpo)}</body></html>'''
    salida = os.path.join(RAIZ, 'producto', 'kit')
    os.makedirs(salida, exist_ok=True)
    ruta_html = os.path.join(salida, '.vista.html')
    open(ruta_html, 'w').write(documento)
    ruta_pdf = os.path.join(salida, 'edicion-ceo.pdf')
    script = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"
              f"await p.goto('file://{ruta_html}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);"
              f"await p.pdf({{path:'{ruta_pdf}',format:'A5',printBackground:true}});await b.close();}})();")
    subprocess.run(['node', '-e', script], check=True)
    os.remove(ruta_html)
    print(f'Edición CEO lista: {ruta_pdf} ({len(cuerpo)} páginas, {os.path.getsize(ruta_pdf) // 1024} KB)')


if __name__ == '__main__':
    main()
