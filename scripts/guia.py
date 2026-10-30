"""Arma la guía gratis "Las 30 reglas de la CEO" en PDF desde producto/guia/reglas.json.

Uso: python guia.py      → sitio/public/guia/las-30-reglas-de-la-ceo.pdf (y la vista previa en HTML)

Una regla por página (A5: se lee bien en el celular), portada con Victoria y Capital, una portada
por sección y un cierre con a dónde seguirla. Se imprime con el Chromium de Playwright.
"""
import base64
import html
import json
import os
import subprocess

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'sitio', 'public', 'guia')
FUENTES = '/usr/share/fonts/opentype/inter'


def imagen(ruta, ancho=900):
    jpg = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', ruta, '-vf', f'scale={ancho}:-2', '-q:v', '4', '-f', 'mjpeg', '-'],
                         capture_output=True, check=True).stdout
    return 'data:image/jpeg;base64,' + base64.b64encode(jpg).decode()


def main():
    datos = json.load(open(os.path.join(RAIZ, 'producto', 'guia', 'reglas.json')))
    foto = imagen(os.path.join(RAIZ, 'assets', 'cuadro-jet-final.png'))
    e = html.escape
    paginas = [f'''
<section class="pagina portada">
  <img src="{foto}" alt="Victoria y Capital">
  <div class="velo"></div>
  <div class="texto">
    <div class="marca">VICTORIA <b>THE CEO</b></div>
    <h1>{e(datos["titulo"])}</h1>
    <p>{e(datos["subtitulo"])}</p>
    <div class="gratis">Guía gratuita · @victoriatheceo</div>
  </div>
</section>
<section class="pagina intro">
  <div class="etiqueta">Antes de empezar</div>
  <h2>Treinta ideas que me hubiera gustado saber antes.</h2>
  <p>Soy Victoria. Cada regla de esta guía tiene una fuente real que puedes buscar: un libro, un estudio o una
  institución. Nada de fórmulas mágicas. Una regla por página, una acción concreta para hoy.</p>
  <p>Léela de una vez o una por día. Lo importante no es saberlas: es aplicar una esta semana.</p>
  <p class="firma">— Victoria y Capital 🐾</p>
</section>''']
    numero = 0
    for seccion in datos['secciones']:
        paginas.append(f'''
<section class="pagina divisor">
  <div class="etiqueta">Parte {datos["secciones"].index(seccion) + 1}</div>
  <h2>{e(seccion["nombre"])}</h2>
  <div class="linea"></div>
  <p>{len(seccion["reglas"])} reglas</p>
</section>''')
        for regla in seccion['reglas']:
            numero += 1
            paginas.append(f'''
<section class="pagina regla">
  <div class="numero">{numero:02d}</div>
  <div class="etiqueta">{e(seccion["nombre"])}</div>
  <h3>{e(regla["titulo"])}</h3>
  <p class="cuerpo">{e(regla["texto"])}</p>
  <div class="accion"><span>Hazlo hoy</span>{e(regla["accion"])}</div>
  <p class="fuente">Fuente: {e(regla["fuente"])}</p>
</section>''')
    avisos = ''.join(f'<li>{e(a)}</li>' for a in datos['avisos'])
    paginas.append(f'''
<section class="pagina cierre">
  <div class="etiqueta">Sigamos</div>
  <h2>Una regla nueva cada día.</h2>
  <p>Encuéntrame como <b>@victoriatheceo</b> en Instagram, TikTok y YouTube.</p>
  <p><b>El tablero de la CEO</b>: la plantilla para poner en práctica estas reglas con tus números (presupuesto, deudas, fondo de emergencia y metas, todo calculado solo).</p>
  <p><a class="enlace" href="https://victoriatheceo.vercel.app/?ref=guia#tablero">victoriatheceo.vercel.app</a></p>
  <ul class="avisos">{avisos}</ul>
</section>''')

    documento = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{e(datos["titulo"])}</title>
<style>
@font-face {{ font-family: Inter; src: url("file://{FUENTES}/Inter-Regular.otf"); font-weight: 400; }}
@font-face {{ font-family: Inter; src: url("file://{FUENTES}/Inter-SemiBold.otf"); font-weight: 600; }}
@font-face {{ font-family: Inter; src: url("file://{FUENTES}/Inter-Black.otf"); font-weight: 900; }}
@page {{ size: A5; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: Inter, sans-serif; color: #f3ede2; background: #0b0b0d; }}
.pagina {{ width: 148mm; height: 210mm; padding: 18mm 15mm; position: relative; overflow: hidden; page-break-after: always;
  background: radial-gradient(120% 80% at 100% 0%, #2a2112 0%, #0b0b0d 55%); }}
.etiqueta {{ font-size: 8.5pt; letter-spacing: .32em; text-transform: uppercase; color: #f5c542; font-weight: 600; }}
h1 {{ font-weight: 900; font-size: 30pt; line-height: 1.02; margin: 4mm 0; }}
h2 {{ font-weight: 900; font-size: 22pt; line-height: 1.1; margin: 6mm 0; }}
h3 {{ font-weight: 900; font-size: 21pt; line-height: 1.1; margin: 4mm 0 6mm; }}
p {{ font-size: 11pt; line-height: 1.55; color: #d9d2c5; }}
.portada {{ padding: 0; }}
.portada img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
.portada .velo {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(11,11,13,0) 30%, rgba(11,11,13,.92) 72%); }}
.portada .texto {{ position: absolute; left: 15mm; right: 15mm; bottom: 16mm; }}
.marca {{ font-size: 9pt; letter-spacing: .3em; font-weight: 600; }}
.marca b {{ color: #f5c542; }}
.gratis {{ display: inline-block; margin-top: 3mm; padding: 2mm 4mm; border: 1px solid #f5c542; color: #f5c542; font-size: 8.5pt; letter-spacing: .12em; text-transform: uppercase; }}
.firma {{ color: #f5c542; font-weight: 600; }}
.enlace {{ color: #f5c542; font-weight: 900; font-size: 13pt; text-decoration: none; }}
.divisor {{ display: flex; flex-direction: column; justify-content: center; }}
.divisor h2 {{ font-size: 36pt; }}
.linea {{ width: 30mm; height: 2px; background: #f5c542; }}
.numero {{ position: absolute; right: 12mm; top: 8mm; font-size: 72pt; font-weight: 900; color: rgba(245,197,66,.16); }}
.regla {{ padding-top: 34mm; }}
.cuerpo {{ font-size: 12.5pt; }}
.accion {{ margin-top: 8mm; padding: 5mm 6mm; border-left: 3px solid #f5c542; background: rgba(245,197,66,.08); font-size: 11.5pt; line-height: 1.5; }}
.accion span {{ display: block; font-size: 8pt; letter-spacing: .28em; text-transform: uppercase; color: #f5c542; font-weight: 600; margin-bottom: 2mm; }}
.fuente {{ position: absolute; left: 15mm; right: 15mm; bottom: 14mm; font-size: 8.5pt; color: #8f877a; border-top: 1px solid rgba(245,197,66,.25); padding-top: 3mm; }}
.avisos {{ margin-top: 14mm; padding-left: 4mm; font-size: 8.5pt; color: #8f877a; line-height: 1.5; }}
</style></head><body>{"".join(paginas)}</body></html>'''
    os.makedirs(SALIDA, exist_ok=True)
    ruta_html = os.path.join(SALIDA, 'vista-previa.html')
    open(ruta_html, 'w').write(documento)
    ruta_pdf = os.path.join(SALIDA, 'las-30-reglas-de-la-ceo.pdf')
    script = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"
              f"await p.goto('file://{ruta_html}',{{waitUntil:'load'}});await p.pdf({{path:'{ruta_pdf}',format:'A5',printBackground:true}});"
              "await b.close();})();")
    subprocess.run(['node', '-e', script], check=True)
    os.remove(ruta_html)  # la vista previa lleva rutas locales; el PDF es lo que se publica
    print(f'Guía lista: {ruta_pdf} ({numero} reglas, {len(paginas)} páginas, {os.path.getsize(ruta_pdf) // 1024} KB)')


if __name__ == '__main__':
    main()
