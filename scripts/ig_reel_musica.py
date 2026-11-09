"""Reel de Instagram con música de la biblioteca de Instagram, directo con la API de Meta (9-nov-2026).

Rodrigo: "tú súbelo". Publer no puede poner sonidos de la biblioteca (su ayuda lo dice); la API de Meta sí (Audio API:
GET /ig_audio y audio_configuration al crear el Reel). El token de la app "Victoria Comentarios" lo pone el proxy de la
sesión en graph.facebook.com y ya tiene instagram_content_publish. Instagram no deja programar por esta vía: la rutina
anota el Reel con --programar y deja un recordatorio (send_later) a esa hora que corre --publicar.

Uso: python ig_reel_musica.py <id> --programar <cuando_utc>   anota reel_ig (por publicar) para que cuente en el ritmo
     python ig_reel_musica.py <id> --publicar                   sube y publica ya, con música en tendencia
     python ig_reel_musica.py <id> --prueba                     prepara el Reel en Instagram pero NO lo publica
     python ig_reel_musica.py musica                            lista la música en tendencia que da Meta

El video es carruseles/<id>/reel-limpio.mp4 (la voz de Victoria sin la música de fondo propia); la canción va al 15% y la
voz al 100%. Meta pide el video en un enlace público: se sube a la rama medios-ig del repo (público) y se lee de
raw.githubusercontent.com. Facebook no va por aquí: sale con Publer (publer_carrusel.py --reel <hora> --solo-facebook).
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carrusel import RAIZ, cargar  # noqa: E402
from publer_carrusel import RUTA, comentario_ig, texto_reel  # noqa: E402

GRAPH = 'https://graph.facebook.com/v22.0'
IG = '17841478105608541'  # @victoriatheceo
RAMA = 'medios-ig'
CRUDO = 'https://raw.githubusercontent.com/rodrigodelcastillo117-dotcom/AI-GIRL'
VOLUMEN_MUSICA, VOLUMEN_VOZ = 15, 100


def graph(metodo, ruta, datos=None):
    cuerpo = urllib.parse.urlencode(datos).encode() if datos else None
    try:
        with urllib.request.urlopen(urllib.request.Request(f'{GRAPH}/{ruta}', data=cuerpo, method=metodo), timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f'ERROR {e.code} de Meta en {ruta.split("?")[0]}: {e.read().decode()[:400]}')


def musica_en_tendencia():
    return graph('GET', f'ig_audio?audio_type=music&user_id={IG}').get('audio', [])


def elegir_audio(todos):
    """La canción en tendencia que no se haya usado en los últimos 10 Reels (para no repetir)."""
    usadas = [(c.get('reel_ig') or {}).get('audio', {}).get('id') for c in todos]
    usadas = {u for u in sorted((x for x in usadas if x), key=str)[-10:]}
    lista = musica_en_tendencia()
    if not lista:
        sys.exit('ERROR: Meta no regresó música en tendencia; no se publica sin sonido (avisar a Rodrigo).')
    return next((a for a in lista if a['audio_id'] not in usadas), lista[0])


def subir_medio(ruta, nombre):
    """Deja el video en la rama medios-ig (solo ese archivo, la rama se reescribe) y regresa su enlace público."""
    tmp = tempfile.mkdtemp()
    local = None
    subprocess.run(['git', '-C', RAIZ, 'worktree', 'add', '--detach', tmp], check=True, capture_output=True)
    try:
        g = lambda *a: subprocess.run(['git', '-C', tmp, *a], check=True, capture_output=True)
        local = f'medio-{os.getpid()}-{int(time.time())}'  # rama local de un solo uso; se sube como medios-ig
        g('checkout', '--orphan', local)
        g('rm', '-rqf', '.')
        subprocess.run(['cp', ruta, os.path.join(tmp, nombre)], check=True)
        g('add', nombre)
        g('commit', '-qm', f'Medio temporal para Instagram ({nombre})')
        for intento in range(4):
            if subprocess.run(['git', '-C', tmp, 'push', '-q', '-f', 'origin', f'HEAD:refs/heads/{RAMA}'], capture_output=True).returncode == 0:
                break
            time.sleep(2 ** (intento + 1))
        else:
            sys.exit('ERROR: no pude subir el video a la rama medios-ig.')
    finally:
        subprocess.run(['git', '-C', RAIZ, 'worktree', 'remove', '--force', tmp], capture_output=True)
        subprocess.run(['git', '-C', RAIZ, 'branch', '-D', local], capture_output=True)
    url = f'{CRUDO}/{RAMA}/{nombre}'
    for _ in range(30):  # el enlace tarda unos segundos en servir el archivo nuevo
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=30) as r:
                if r.status == 200 and int(r.headers.get('content-length', 0)) == os.path.getsize(ruta):
                    return url
        except urllib.error.URLError:
            pass
        time.sleep(4)
    sys.exit(f'ERROR: el enlace público del video no respondió: {url}')


def preparar(c, config, todos):
    carpeta = os.path.join(RAIZ, 'carruseles', c['id'])
    video = next((os.path.join(carpeta, n) for n in ('reel-limpio.mp4', 'reel.mp4', 'short.mp4')
                  if os.path.exists(os.path.join(carpeta, n))), None)
    if not video:
        sys.exit(f'ERROR: falta el video de {c["id"]}: corre primero carrusel_video.py short {c["id"]}')
    audio = elegir_audio(todos)
    url = subir_medio(video, f'{c["id"]}-reel-{int(time.time())}.mp4')  # nombre único: el CDN de GitHub guarda copias viejas
    texto = texto_reel(c, config)
    contenedor = graph('POST', f'{IG}/media', {
        'media_type': 'REELS', 'video_url': url, 'caption': texto, 'share_to_feed': 'true',
        'audio_configuration': json.dumps({'audio_id': audio['audio_id'], 'audio_volume': VOLUMEN_MUSICA,
                                           'video_volume': VOLUMEN_VOZ})})['id']
    for _ in range(60):
        estado = graph('GET', f'{contenedor}?fields=status_code,status')
        if estado.get('status_code') == 'FINISHED':
            break
        if estado.get('status_code') in ('ERROR', 'EXPIRED'):
            sys.exit(f"ERROR: Instagram no aceptó el video: {estado.get('status')}")
        time.sleep(5)
    else:
        sys.exit('ERROR: Instagram tardó más de 5 minutos en procesar el video.')
    return contenedor, audio, texto, video


def guardar(cid, cambios):
    datos = json.load(open(RUTA))
    yo = next(x for x in datos['carruseles'] if x['id'] == cid)
    yo.setdefault('reel_ig', {}).update(cambios)
    if yo['estado'] == 'listo':
        yo['estado'] = 'programado'
    json.dump(datos, open(RUTA, 'w'), ensure_ascii=False, indent=1)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if args and args[0] == 'musica':
        for a in musica_en_tendencia():
            print(a['audio_id'], '|', a.get('title'), '—', a.get('display_artist'))
        return
    if not args:
        sys.exit(__doc__)
    c = cargar(args[0])
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    todos = json.load(open(RUTA))['carruseles']
    yo = next(x for x in todos if x['id'] == c['id'])
    if '--programar' in sys.argv:
        cuando = sys.argv[sys.argv.index('--programar') + 1]
        if (yo.get('reel_ig') or {}).get('ig_media_id'):
            print(f'OMITIDO: el Reel de {c["id"]} ya salió en Instagram.')
            return
        guardar(c['id'], {'publica_utc': cuando, 'texto': texto_reel(c, config), 'via': 'meta', 'estado': 'por_publicar'})
        print(f'OK Reel de {c["id"]} anotado para {cuando}: deja un recordatorio a esa hora que corra '
              f'"python scripts/ig_reel_musica.py {c["id"]} --publicar".')
        return
    if (yo.get('reel_ig') or {}).get('ig_media_id'):
        print(f'OMITIDO: el Reel de {c["id"]} ya salió en Instagram ({yo["reel_ig"]["ig_media_id"]}).')
        return
    contenedor, audio, texto, video = preparar(c, config, todos)
    if '--prueba' in sys.argv:
        print(f"PRUEBA: Reel listo en Instagram (contenedor {contenedor}) con \"{audio.get('title')}\" de "
              f"{audio.get('display_artist')}; NO se publicó.")
        return
    media = graph('POST', f'{IG}/media_publish', {'creation_id': contenedor})['id']
    comentario = comentario_ig(c, config)
    if comentario:
        graph('POST', f'{media}/comments', {'message': comentario})
    ahora = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    guardar(c['id'], {'publica_utc': ahora, 'texto': texto, 'via': 'meta', 'estado': 'publicado', 'ig_media_id': media,
                      'video': os.path.relpath(video, RAIZ),
                      'audio': {'id': audio['audio_id'], 'titulo': audio.get('title'), 'artista': audio.get('display_artist')}})
    print(f"OK Reel de {c['id']} publicado en Instagram ({media}) con \"{audio.get('title')}\" de {audio.get('display_artist')}.")


if __name__ == '__main__':
    main()
