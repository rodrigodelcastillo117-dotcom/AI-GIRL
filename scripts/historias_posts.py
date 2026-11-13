"""Cada post nuevo de Instagram se anuncia en historias de Instagram y Facebook (Rodrigo, 13-nov-2026: "todos los posts,
shorts y reels, que se hagan historias, también en Facebook").

Uso: python3 scripts/historias_posts.py              publica las historias que falten (tope: config.json →
                                                     historias_de_posts.max_por_dia, cuenta las de hoy en México)
     python3 scripts/historias_posts.py --simular    solo arma las imágenes en videos/qa/ y dice qué publicaría

Cómo funciona (y por qué así):
- Toma los posts de @victoriatheceo de las últimas 30 h que aún no tienen historia (contenido/historias_posts.json).
- Arma una imagen 1080x1920 con la portada del post, su título y "míralo en mi perfil". NO vuelve a subir el video del
  Reel: los Reels con música de la biblioteca de Instagram no traen archivo por la API (media_url vacío) y esa licencia
  es del Reel, no de una historia.
- La imagen se sube primero a Facebook como foto sin publicar (así queda en una dirección pública de Meta sin
  desplegar nada), con esa foto sale la historia de Facebook y con su dirección la de Instagram.
- Límites de la API de Meta (oficial): no hay sticker de enlace ni "compartir post en tu historia" ni destacadas: eso
  solo desde la app. TikTok no tiene historias en su API.
"""
import datetime
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRO = os.path.join(RAIZ, 'contenido', 'historias_posts.json')
QA = os.path.join(RAIZ, 'videos', 'qa')
MX = ZoneInfo('America/Mexico_City')
SIN_EMOJI = re.compile('[\U0001F000-\U0001FAFF☀-➿️‍]')


def registro():
    return json.load(open(REGISTRO)) if os.path.exists(REGISTRO) else []


def guardar(filas):
    with open(REGISTRO, 'w') as f:
        json.dump(filas, f, ensure_ascii=False, indent=1)
        f.write('\n')


def nuevos(horas=30):
    import ig_reel_musica as ig
    from comentarios_ig import IG_USUARIO
    ya = {r['post'] for r in registro()}
    desde = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=horas)
    campos = 'id,timestamp,media_type,media_product_type,media_url,thumbnail_url,caption,permalink,children{media_type,media_url,thumbnail_url}'
    salida = []
    for m in ig.graph('GET', f'{IG_USUARIO}/media?fields={campos}&limit=15').get('data', []):
        cuando = datetime.datetime.fromisoformat(m['timestamp'].replace('+0000', '+00:00'))
        if cuando >= desde and m['id'] not in ya:
            salida.append(m)
    return sorted(salida, key=lambda m: m['timestamp'])


def portada(m):
    if m['media_type'] == 'IMAGE':
        return m.get('media_url')
    if m['media_type'] == 'CAROUSEL_ALBUM':
        hijo = ((m.get('children') or {}).get('data') or [{}])[0]
        return hijo.get('media_url') if hijo.get('media_type') == 'IMAGE' else hijo.get('thumbnail_url')
    return m.get('thumbnail_url') or m.get('media_url')


def titulo(m):
    linea = SIN_EMOJI.sub('', (m.get('caption') or '').strip().split('\n')[0]).strip()
    frase = re.split(r'(?<=[.!?])\s', linea, maxsplit=1)[0]
    linea = frase if len(frase) >= 25 else linea
    return linea if len(linea) <= 90 else linea[:87].rsplit(' ', 1)[0] + '…'


def armar(m):
    """Imagen de la historia (mismo estilo que la de Victoria Hoy)."""
    os.makedirs(QA, exist_ok=True)
    fondo = os.path.join(QA, f'.post-{m["id"]}.jpg')
    urllib.request.urlretrieve(portada(m), fondo)
    tipo = {'REELS': 'NUEVO REEL', 'FEED': 'NUEVO CARRUSEL' if m['media_type'] == 'CAROUSEL_ALBUM' else 'NUEVO POST'}.get(m.get('media_product_type'), 'NUEVO')
    doc = f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@600;800&family=Playfair+Display:wght@600&display=swap" rel="stylesheet">
<style>
body {{ margin: 0; width: 1080px; height: 1920px; background: #070707; color: #f4efe6; font-family: Inter, sans-serif; overflow: hidden; position: relative; }}
.borroso {{ position: absolute; inset: -60px; background: url("file://{fondo}") center/cover; filter: blur(40px) brightness(.35); }}
.chip {{ position: absolute; top: 170px; left: 0; right: 0; text-align: center; }}
.chip span {{ display: inline-block; padding: 14px 30px; border-radius: 40px; background: #d8b25a; color: #111; font-weight: 800; font-size: 30px; letter-spacing: .2em; }}
.post {{ position: absolute; top: 280px; left: 110px; width: 860px; height: 1075px; border-radius: 36px; background: url("file://{fondo}") center/cover; box-shadow: 0 30px 80px rgba(0,0,0,.6); border: 2px solid rgba(216,178,90,.5); }}
h1 {{ position: absolute; top: 1400px; left: 90px; right: 90px; margin: 0; text-align: center; font-family: "Playfair Display", serif; font-weight: 600; font-size: 54px; line-height: 1.12; }}
.ir {{ position: absolute; left: 150px; right: 150px; bottom: 170px; text-align: center; padding: 28px; border-radius: 60px; background: linear-gradient(180deg, #f0d488, #d8b25a); color: #111; font-size: 36px; font-weight: 800; }}
.ir small {{ display: block; font-size: 26px; font-weight: 600; margin-top: 4px; }}
.ia {{ position: absolute; bottom: 90px; left: 0; right: 0; text-align: center; font-size: 22px; color: rgba(244,239,230,.6); letter-spacing: .08em; }}
</style></head><body><div class="borroso"></div><div class="chip"><span>{tipo}</span></div><div class="post"></div>
<h1>{html.escape(titulo(m))}</h1><div class="ir">Míralo completo en mi perfil<small>@victoriatheceo</small></div>
<div class="ia">Victoria · personaje creado con IA</div></body></html>'''
    tmp = os.path.join(QA, f'.historia-post-{m["id"]}.html')
    open(tmp, 'w').write(doc)
    png, salida = tmp[:-5] + '.png', os.path.join(QA, f'historia-post-{m["id"]}.jpg')
    script = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});"
              f"await p.goto('file://{tmp}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);await p.screenshot({{path:'{png}'}});await b.close();}})();")
    subprocess.run(['node', '-e', script], check=True)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', png, '-q:v', '3', salida], check=True)
    for f in (tmp, png, fondo):
        os.remove(f)
    return salida


def foto_facebook(jpg, pagina):
    """Sube la imagen a la página como foto sin publicar; devuelve (id, dirección pública de Meta)."""
    import primer_comentario as pc
    tok = pc.token_pagina(pagina)
    r = subprocess.run(['curl', '-s', '-F', f'source=@{jpg};type=image/jpeg', '-F', 'published=false', '-F', f'access_token={tok}',
                        f'https://graph.facebook.com/v21.0/{pagina}/photos'], capture_output=True, text=True, check=True)
    foto = json.loads(r.stdout)
    if 'id' not in foto:
        raise RuntimeError(f"Facebook no aceptó la foto: {str(foto.get('error', foto))[:200]}")
    imgs = pc.fb('GET', f'{foto["id"]}?fields=images', pagina).get('images') or []
    return foto['id'], max(imgs, key=lambda i: i.get('width', 0))['source']


def publicar(m, jpg):
    import ig_reel_musica as ig
    import primer_comentario as pc
    import publer
    from comentarios_ig import IG_USUARIO
    pagina = publer.CONFIG['facebook_pagina_id']
    fila = {'post': m['id'], 'permalink': m.get('permalink'), 'titulo': titulo(m),
            'fecha_mx': datetime.datetime.now(MX).date().isoformat()}
    foto_id, url = foto_facebook(jpg, pagina)
    try:
        h = pc.fb('POST', f'{pagina}/photo_stories', pagina, {'photo_id': foto_id})
        fila['fb'] = h.get('post_id') or h.get('id')
    except RuntimeError as e:
        fila['fb_error'] = str(e)[:200]
    try:
        cont = ig.graph('POST', f'{IG_USUARIO}/media', {'image_url': url, 'media_type': 'STORIES'})
        for _ in range(20):
            if ig.graph('GET', f'{cont["id"]}?fields=status_code').get('status_code') == 'FINISHED':
                break
            time.sleep(3)
        fila['ig'] = ig.graph('POST', f'{IG_USUARIO}/media_publish', {'creation_id': cont['id']}).get('id')
    except (SystemExit, RuntimeError) as e:
        fila['ig_error'] = str(e)[:200]
    return fila


def main():
    simular = '--simular' in sys.argv
    conf = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json'))).get('historias_de_posts', {})
    tope = int(conf.get('max_por_dia', 3))
    filas = registro()
    hoy = datetime.datetime.now(MX).date().isoformat()
    quedan = tope - sum(1 for f in filas if f.get('fecha_mx') == hoy and (f.get('ig') or f.get('fb')))
    pendientes = nuevos()
    if not pendientes:
        print('ok: no hay posts nuevos sin historia')
        return
    for m in pendientes[-max(quedan, 0):] if quedan > 0 else []:  # si hay más que el tope, los más recientes
        if not portada(m):
            print('sin portada por la API, se salta:', m['id'])
            continue
        jpg = armar(m)
        if simular:
            print('simulado:', titulo(m), '→', jpg)
            continue
        fila = publicar(m, jpg)
        filas.append(fila)
        guardar(filas)
        print('ok historia', fila['titulo'][:50], '| ig', fila.get('ig') or fila.get('ig_error'), '| fb', fila.get('fb') or fila.get('fb_error'))
    if quedan <= 0:
        print(f'tope del día alcanzado ({tope}); quedan {len(pendientes)} posts para mañana si siguen dentro de 30 h')


if __name__ == '__main__':
    main()
