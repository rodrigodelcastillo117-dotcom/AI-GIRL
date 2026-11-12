"""Noticias del día de Victoria (12-nov-2026). Rodrigo: "quiero que cada día veas noticias relevantes de México y el
mundo… que te mande a una página con una newsletter, noticias, y cómo afecta al cliente. Hazlo digerible. TODOS LOS DÍAS".

Cada día la rutina (docs/RUTINA_DIARIA.md) busca las noticias, las cruza con 2 fuentes y escribe
contenido/noticias/<AAAA-MM-DD>.json:
  {"fecha", "titulo", "intro", "noticias": [{"tema": "México|Mundo|Tu bolsillo", "titulo", "que_paso", "te_afecta",
   "que_hacer", "fuentes": [{"nombre", "url"}]}], "dato", "cierre"}
Reglas: 3 a 5 noticias; nada sin 2 fuentes; cifras como las da la fuente; sin recomendar productos, bancos ni
inversiones; "qué hacer" es una acción de hábito (comparar, revisar, esperar), nunca "compra X".

Uso: python3 scripts/noticias.py pagina              → sitio/public/hoy.html (la de hoy) y noticias/<fecha>.html (archivo)
     python3 scripts/noticias.py historia [fecha]    → sitio/public/historias/<fecha>.jpg (1080x1920)
     python3 scripts/noticias.py publicar [fecha]    → la sube como historia de Instagram (necesita la imagen ya en línea)
     python3 scripts/noticias.py publicar --si-falta → solo si hoy todavía no hay historia (respaldo de las 10 a.m.)
"""
import glob
import html
import json
import os
import subprocess
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLICO = os.path.join(RAIZ, 'sitio', 'public')
SITIO = 'https://victoriatheceo.vercel.app'
e = html.escape
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']


def ediciones():
    return sorted(glob.glob(os.path.join(RAIZ, 'contenido', 'noticias', '20[0-9][0-9]-[01][0-9]-[0-3][0-9].json')))


def cargar(fecha=None):
    rutas = ediciones()
    ruta = os.path.join(RAIZ, 'contenido', 'noticias', f'{fecha}.json') if fecha else rutas[-1]
    return json.load(open(ruta))


def fecha_larga(f):
    import datetime
    d = datetime.date.fromisoformat(f)
    return f'{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}'


def entre(texto, inicio, fin):
    a = texto.index(inicio)
    return texto[a:texto.index(fin, a) + len(fin)]


def pagina_html(ed, archivo):
    portada = open(os.path.join(PUBLICO, 'index.html')).read()
    estilos = entre(portada, '<style>', '</style>')
    pie = entre(portada, '<footer>', '</footer>').replace('href="#guia"', 'href="/reglas"').replace('href="#tablero"', 'href="/#tablero"')
    extra = '''
    .hoy-cabeza { padding: 56px 0 26px; background: radial-gradient(800px 420px at 90% -10%, rgba(216,178,90,.15), transparent 60%), var(--negro); }
    .hoy-cabeza h1 { font-family: "Playfair Display", serif; font-weight: 600; font-size: clamp(2rem, 5.4vw, 3.6rem); line-height: 1.05; margin: 12px 0 14px; max-width: 18ch; }
    .hoy-cabeza .bajada { font-size: 1.1rem; color: var(--texto); max-width: 40rem; line-height: 1.6; }
    .fecha-hoy { font-size: .78rem; letter-spacing: .24em; text-transform: uppercase; color: var(--oro); font-weight: 600; }
    .notas { display: grid; gap: 16px; }
    .nota-n { position: relative; padding: 26px 24px 22px; border-radius: var(--radio); background: var(--negro-2); border: 1px solid var(--linea-2); }
    .nota-n .tema { display: inline-block; font-size: .7rem; letter-spacing: .2em; text-transform: uppercase; font-weight: 700; color: #111; background: var(--oro); padding: 4px 10px; border-radius: 999px; }
    .nota-n .tema.mundo { background: var(--zafiro); color: #fff; } .nota-n .tema.bolsillo { background: var(--esmeralda); color: #fff; }
    .nota-n h2 { font-family: "Playfair Display", serif; font-weight: 600; font-size: 1.55rem; line-height: 1.2; margin: 12px 0 14px; }
    .tres { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    @media (max-width: 820px) { .tres { grid-template-columns: 1fr; } }
    .tres div { padding: 14px 16px; border-radius: 14px; background: var(--panel); border: 1px solid var(--linea-2); }
    .tres span { display: block; font-size: .68rem; letter-spacing: .2em; text-transform: uppercase; font-weight: 700; margin-bottom: 6px; color: var(--tenue); }
    .tres .afecta { border-color: rgba(216,178,90,.4); background: rgba(216,178,90,.07); } .tres .afecta span { color: var(--oro); }
    .tres .hacer span { color: var(--esmeralda); }
    .tres p { margin: 0; line-height: 1.55; color: var(--marfil); font-size: .97rem; }
    .fuentes-n { margin-top: 12px; font-size: .8rem; color: var(--tenue); } .fuentes-n a { color: var(--tenue); }
    .dato { margin-top: 22px; padding: 24px; border-radius: var(--radio); border: 1px solid var(--linea); background: radial-gradient(500px 240px at 0 0, rgba(216,178,90,.14), transparent 60%), var(--negro-2); }
    .dato b { font-family: "Playfair Display", serif; font-size: 1.25rem; font-weight: 600; display: block; margin-bottom: 6px; color: var(--oro-2); }
    .archivo { display: flex; flex-wrap: wrap; gap: 8px; } .archivo a { border: 1px solid var(--linea-2); border-radius: 999px; padding: 7px 14px; font-size: .86rem; text-decoration: none; color: var(--texto); }
    .archivo a:hover { border-color: var(--oro); color: var(--oro-2); }
'''
    estilos = estilos.replace('</style>', extra + '  </style>')
    clase = {'Mundo': 'mundo', 'Tu bolsillo': 'bolsillo'}
    notas = ''.join(f'''<article class="nota-n">
        <span class="tema {clase.get(n["tema"], "")}">{e(n["tema"])}</span>
        <h2>{e(n["titulo"])}</h2>
        <div class="tres">
          <div><span>Qué pasó</span><p>{e(n["que_paso"])}</p></div>
          <div class="afecta"><span>Cómo te afecta</span><p>{e(n["te_afecta"])}</p></div>
          <div class="hacer"><span>Qué hacer</span><p>{e(n["que_hacer"])}</p></div>
        </div>
        <div class="fuentes-n">Fuentes: {" · ".join(f'<a href="{e(f["url"])}" rel="noopener" target="_blank">{e(f["nombre"])}</a>' for f in n["fuentes"])}</div>
      </article>''' for n in ed['noticias'])
    lista = ''.join(f'<a href="/noticias/{f}">{e(fecha_larga(f))}</a>' for f in reversed(archivo))
    return f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(ed["titulo"])} · Victoria Hoy</title>
  <meta name="description" content="{e(ed["intro"])} Noticias de dinero de México y el mundo, explicadas fácil, con cómo te afectan.">
  <meta property="og:title" content="{e(ed["titulo"])}">
  <meta property="og:description" content="Victoria Hoy · {e(fecha_larga(ed["fecha"]))} · noticias de dinero explicadas fácil.">
  <meta property="og:image" content="{SITIO}/historias/{ed["fecha"]}.jpg">
  <meta name="theme-color" content="#070707">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='16' fill='%23070707'/%3E%3Ctext x='16' y='22' font-size='17' font-family='Georgia' font-weight='700' fill='%23d8b25a' text-anchor='middle'%3EV%3C/text%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500&display=swap" rel="stylesheet">
  {estilos}
  <script>try {{ const u = new URL(location.href); const r = u.searchParams.get('ref'); if (r && !u.searchParams.has('utm_source')) {{ u.searchParams.set('utm_source', r); history.replaceState(null, '', u); }} }} catch {{}}</script>
  <script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
  <header class="menu">
    <div class="contenedor">
      <a class="logo" href="/"><i>V</i><span>Victoria <b>The CEO</b></span></a>
      <nav aria-label="Principal">
        <a href="/hoy">Hoy</a>
        <a href="/#calculadoras">Calculadoras</a>
        <a href="/reglas">Las 30 reglas</a>
        <a href="/#tablero">Plantilla</a>
        <a class="cta" href="/reglas">Guía gratis</a>
      </nav>
    </div>
  </header>
  <main>
  <section class="hoy-cabeza">
    <div class="contenedor">
      <div class="fecha-hoy">Victoria Hoy · {e(fecha_larga(ed["fecha"]))}</div>
      <h1>{e(ed["titulo"])}</h1>
      <p class="bajada">{e(ed["intro"])}</p>
    </div>
  </section>
  <section class="bloque" style="padding-top:10px">
    <div class="contenedor">
      <div class="notas">{notas}</div>
      <div class="dato"><b>El dato del día</b>{e(ed["dato"])}</div>
      <p style="margin-top:22px;font-family:'Playfair Display',serif;font-size:1.2rem;color:var(--marfil)">{e(ed["cierre"])} — Victoria</p>
      <p class="letra-chica">Resumen informativo con fuentes públicas; no es asesoría financiera. Victoria es un personaje creado con IA.</p>
    </div>
  </section>
  <section class="bloque">
    <div class="contenedor">
      <div class="encabezado"><div class="antetitulo">Haz tus cuentas</div><h2>Mis 7 calculadoras gratis.</h2></div>
      {entre(portada, '<div class="herramientas">', '<!--/herramientas--></div>')}
    </div>
  </section>
  <section class="bloque">
    <div class="contenedor">
      <div class="encabezado"><div class="antetitulo">Archivo</div><h2>Días anteriores.</h2></div>
      <div class="archivo">{lista}</div>
    </div>
  </section>
  </main>
  {pie}
</body>
</html>
'''


def pagina():
    archivo = [os.path.basename(r)[:-5] for r in ediciones()]
    os.makedirs(os.path.join(PUBLICO, 'noticias'), exist_ok=True)
    for f in archivo:
        open(os.path.join(PUBLICO, 'noticias', f'{f}.html'), 'w').write(pagina_html(cargar(f), archivo))
    open(os.path.join(PUBLICO, 'hoy.html'), 'w').write(pagina_html(cargar(archivo[-1]), archivo))
    print(f'ok /hoy = {archivo[-1]} · archivo: {len(archivo)} días')


def historia(fecha=None):
    """Imagen 1080x1920 para la historia: titular, las noticias en una línea cada una y a dónde ir."""
    ed = cargar(fecha)
    foto = os.path.join(PUBLICO, 'img', 'victoria.jpg')
    renglones = ''.join(f'<li><span>{e(n["tema"])}</span>{e(n["titulo"])}</li>' for n in ed['noticias'][:3])
    doc = f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800&family=Playfair+Display:ital,wght@0,600;1,600&display=swap" rel="stylesheet">
<style>
body {{ margin: 0; width: 1080px; height: 1920px; background: #070707; color: #f4efe6; font-family: Inter, sans-serif; overflow: hidden; position: relative; }}
.foto {{ position: absolute; inset: 0 0 auto 0; height: 780px; background: url("file://{foto}") center 20%/cover; }}
.foto::after {{ content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(7,7,7,.15) 40%, #070707 100%); }}
.caja {{ position: absolute; left: 70px; right: 70px; top: 560px; }}
.marca {{ font-size: 30px; letter-spacing: .3em; font-weight: 800; }} .marca b {{ color: #d8b25a; }}
.fecha {{ margin-top: 14px; font-size: 28px; letter-spacing: .18em; text-transform: uppercase; color: #d8b25a; font-weight: 700; }}
h1 {{ font-family: "Playfair Display", serif; font-weight: 600; font-size: 66px; line-height: 1.06; margin: 18px 0 28px; }}
ul {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 22px; }}
li {{ font-size: 33px; line-height: 1.25; font-weight: 600; padding: 22px 26px; border-radius: 26px; background: #141415; border: 1px solid rgba(216,178,90,.25); }}
p.mas {{ font-size: 28px; color: #d8b25a; font-weight: 700; margin: 18px 0 0; }}
li span {{ display: block; font-size: 22px; letter-spacing: .2em; text-transform: uppercase; color: #d8b25a; margin-bottom: 8px; font-weight: 800; }}
.ir {{ position: absolute; left: 70px; right: 70px; bottom: 270px; text-align: center; padding: 34px; border-radius: 60px; background: linear-gradient(180deg, #f0d488, #d8b25a); color: #111; font-size: 40px; font-weight: 800; }}
.ir small {{ display: block; font-size: 28px; font-weight: 700; margin-top: 6px; }}
</style></head><body><div class="foto"></div><div class="caja">
<div class="marca">VICTORIA <b>HOY</b></div><div class="fecha">{e(fecha_larga(ed["fecha"]))}</div>
<h1>{e(ed["titulo"])}</h1><ul>{renglones}</ul>{'<p class="mas">+ ' + str(len(ed['noticias']) - 3) + ' más en la página</p>' if len(ed['noticias']) > 3 else ''}</div>
<div class="ir">Cómo te afecta, aquí 👇<small>victoriatheceo.vercel.app/hoy</small></div></body></html>'''
    os.makedirs(os.path.join(PUBLICO, 'historias'), exist_ok=True)
    tmp = os.path.join(RAIZ, 'videos', 'qa', f'.historia-{ed["fecha"]}.html')
    open(tmp, 'w').write(doc)
    salida = os.path.join(PUBLICO, 'historias', f'{ed["fecha"]}.jpg')
    png = tmp[:-5] + '.png'
    script = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});"
              f"await p.goto('file://{tmp}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);await p.screenshot({{path:'{png}'}});await b.close();}})();")
    subprocess.run(['node', '-e', script], check=True)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', png, '-q:v', '3', salida], check=True)
    os.remove(tmp)
    os.remove(png)
    print('ok', salida)
    return salida


def ya_hay_historia_hoy():
    """True si @victoriatheceo ya tiene una historia publicada desde las 5 a.m. de hoy (hora de México): la que subió
    Rodrigo a mano con el sticker de enlace (12-nov-2026: "mete el link de cómo te afecta como link que le puedan picar")."""
    import datetime
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ig_reel_musica as ig
    from comentarios_ig import IG_USUARIO
    mx = datetime.timezone(datetime.timedelta(hours=-6))
    inicio = datetime.datetime.now(mx).replace(hour=5, minute=0, second=0, microsecond=0)
    for h in ig.graph('GET', f'{IG_USUARIO}/stories?fields=id,timestamp').get('data', []):
        if datetime.datetime.fromisoformat(h['timestamp'].replace('+0000', '+00:00')) >= inicio:
            return True
    return False


def publicar(fecha=None):
    """Historia de Instagram (API de Meta, media_type=STORIES). La API no deja poner el sticker de enlace: la imagen
    lleva la dirección escrita y Rodrigo puede añadir el sticker a mano si quiere."""
    import time
    ed = cargar(fecha)
    url = f'{SITIO}/historias/{ed["fecha"]}.jpg'
    with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=30) as r:
        if r.status != 200:
            sys.exit(f'La imagen no está en línea todavía: {url}')
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ig_reel_musica as ig
    from comentarios_ig import IG_USUARIO
    cont = ig.graph('POST', f'{IG_USUARIO}/media', {'image_url': url, 'media_type': 'STORIES'})
    for _ in range(20):
        estado = ig.graph('GET', f'{cont["id"]}?fields=status_code')
        if estado.get('status_code') == 'FINISHED':
            break
        time.sleep(3)
    pub = ig.graph('POST', f'{IG_USUARIO}/media_publish', {'creation_id': cont['id']})
    registro = os.path.join(RAIZ, 'contenido', 'noticias', 'historias.json')
    hechas = json.load(open(registro)) if os.path.exists(registro) else []
    hechas.append({'fecha': ed['fecha'], 'ig_media_id': pub.get('id'), 'imagen': url})
    json.dump(hechas, open(registro, 'w'), ensure_ascii=False, indent=1)
    print('ok historia publicada', pub.get('id'))


if __name__ == '__main__':
    accion = sys.argv[1] if len(sys.argv) > 1 else ''
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if accion == 'publicar' and '--si-falta' in sys.argv:
        if ya_hay_historia_hoy():
            print('Ya hay historia de hoy (la subió Rodrigo con el enlace): no se publica otra.')
            sys.exit(0)
        arg = None
    {'pagina': pagina, 'historia': lambda: historia(arg), 'publicar': lambda: publicar(arg)}.get(accion, lambda: sys.exit(__doc__))()
