"""Convierte carruseles ya dibujados en video (gratis: Edge TTS + ffmpeg) y arma sus textos de YouTube.

Uso: python carrusel_video.py short <id>
         carruseles/<id>/short.mp4 (vertical, máximo 57 s) + titulo.txt, descripcion_youtube.txt,
         tags_youtube.txt para youtube.py subir.
     python carrusel_video.py largo <salida.mp4> <id> [<id>...] [--horizontal]
         Une varios carruseles en un video largo: vertical para TikTok e Instagram (más de 1 minuto),
         --horizontal (1920x1080) para un video largo de YouTube.

Cada diapositiva se queda lo que dura su "voz" más medio segundo de aire. La voz es la de Victoria,
clonada de sus videos con scripts/voz_victoria.py (corre con VOZ_PYTHON, el entorno de voz del paso 0 de
PIPELINE; Rodrigo la eligió el 31-oct-2026). --voz-edge usa es-MX-DaliaNeural de Edge TTS, la de antes,
solo si Rodrigo lo pide: sonaba "muy AI".
"""
import asyncio
import glob
import json
import os
import subprocess
import sys

import certifi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carrusel import RAIZ, cargar  # noqa: E402
from seo import cada, con_ref, errores_titulo, etiquetas, hashtags_para  # noqa: E402

VOZ = 'es-MX-DaliaNeural'
AIRE, MAXIMO_SHORT = 0.5, 57.0
AIRE_SHORT = 0.25  # menos silencio entre diapositivas: cada pausa es un momento para deslizar
NEGRO = '0x0b0b0d'
# Detrás del proxy de la nube, el certificado está en SSL_CERT_FILE; edge-tts solo mira certifi.
_ca = os.environ.get('SSL_CERT_FILE') or os.environ.get('REQUESTS_CA_BUNDLE') or '/root/.ccr/ca-bundle.crt'
if _ca and os.path.exists(_ca):
    certifi.where = lambda: _ca
import edge_tts  # noqa: E402


def duracion(ruta):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', ruta],
                       capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)['format']['duration'])


def voces_victoria(carpeta, voces):
    """vozm-XX.mp3 de las frases que falten: la dice una voz mexicana nativa (Edge TTS, es-MX-DaliaNeural) y
    voz_victoria.py la convierte al timbre de Victoria (Rodrigo, 4-nov-2026: el clon directo "se le complica México,
    aguinaldo"; "arreglemos todo, lo más real posible"). Así la pronunciación es mexicana y la voz, la de Victoria."""
    from guion_para_voz import para_voz  # nombres difíciles escritos como se dicen (config.json → pronunciacion)
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    faltan = [{'texto': para_voz(t, config), 'salida': os.path.join(carpeta, f'vozm-{i:02d}.mp3'),
               'base': os.path.join(carpeta, f'vozmx-{i:02d}.mp3')} for i, t in enumerate(voces)
              if not os.path.exists(os.path.join(carpeta, f'vozm-{i:02d}.mp3'))]
    if not faltan:
        return
    for f in faltan:
        asyncio.run(edge_tts.Communicate(f['texto'], VOZ, rate='+4%').save(f['base']))
    python = os.environ.get('VOZ_PYTHON', '/tmp/voz/bin/python')
    if not os.path.exists(python):
        sys.exit(f'ERROR: no está el entorno de voz ({python}); prepáralo con el paso 0 de docs/PIPELINE.md.')
    lista = os.path.join(carpeta, 'voces.json')
    json.dump(faltan, open(lista, 'w'), ensure_ascii=False)
    subprocess.run([python, os.path.join(RAIZ, 'scripts', 'voz_victoria.py'), lista], check=True)
    os.remove(lista)


def movimiento(segundos):
    """Short vertical que no parezca presentación (3-nov-2026: los shorts de carrusel retienen 18-29% y Victoria
    hablando 92%): la diapositiva se acerca despacio (6% en todo el tramo) y las franjas de arriba y abajo, que eran
    negras, llevan la misma diapositiva desenfocada y oscura."""
    cuadros = max(1, int(segundos * 30))
    return (f"[0:v]split[a][b];"
            f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:4,"
            f"eq=brightness=-0.28:saturation=0.8[fondo];"
            f"[b]scale=2160:2700,zoompan=z='1+0.06*on/{cuadros}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d=1:s=1080x1350:fps=30[frente];"
            f"[fondo][frente]overlay=0:285,format=yuv420p[v]")


def tramos(c, horizontal=False, portada=None):
    """Un MP4 por diapositiva (imagen + su voz). Regresa (rutas, segundos totales). portada: otra imagen para
    abrir (la del Reel, 00r.png)."""
    carpeta = os.path.join(RAIZ, 'carruseles', c['id'])
    hojas = sorted(glob.glob(os.path.join(carpeta, '[0-9][0-9].png')))
    if portada:
        hojas[0] = portada
    voces = [c['portada']['voz']] + [d['voz'] for d in c['diapositivas']] + [c['cierre']['voz']]
    if len(hojas) != len(voces):
        sys.exit(f'ERROR: hay {len(hojas)} diapositivas y {len(voces)} voces: corre primero carrusel.py {c["id"]}')
    marco = ('scale=864:1080,pad=1920:1080:528:0' if horizontal else 'scale=1080:1350,pad=1080:1920:0:285') + f':color={NEGRO},format=yuv420p'
    rutas, total = [], 0.0
    edge = '--voz-edge' in sys.argv
    if not edge:
        voces_victoria(carpeta, voces)
    for i, (hoja, texto) in enumerate(zip(hojas, voces)):
        audio = os.path.join(carpeta, f'{"voz" if edge else "vozm"}-{i:02d}.mp3')
        if edge and not os.path.exists(audio):
            asyncio.run(edge_tts.Communicate(texto, VOZ, rate='+5%').save(audio))
        segundos = duracion(audio) + (AIRE if horizontal else AIRE_SHORT)
        total += segundos
        tramo = os.path.join(carpeta, f'tramo-{"h" if horizontal else "v"}-{i:02d}.mp4')
        filtro = ['-vf', marco] if horizontal else ['-filter_complex', movimiento(segundos), '-map', '[v]', '-map', '1:a']
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', hoja, '-i', audio, *filtro,
                        '-af', 'apad', '-t', f'{segundos:.2f}', '-r', '30', '-c:v', 'libx264', '-preset', 'medium',
                        '-crf', '20', '-c:a', 'aac', '-ar', '44100', '-ac', '2', tramo], check=True)
        rutas.append(tramo)
    return rutas, total


def unir(rutas, salida):
    lista = salida + '.txt'
    open(lista, 'w').write(''.join(f"file '{os.path.abspath(r)}'\n" for r in rutas))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', salida], check=True)
    for r in rutas + [lista]:
        os.remove(r)


def textos_youtube(c, config):
    """Mismas reglas que los videos (docs/SEO.md): título que empieza con lo que se busca, 2 enlaces
    arriba, preguntas que la gente escribe, 5 hashtags y etiquetas en tres capas."""
    s = c['seo']
    errores = errores_titulo(s['titulo'], s['palabra_clave'], config.get('titulo_max', 45))
    if errores:
        sys.exit(f"ERROR: el título del carrusel {c['id']} \"{s['titulo']}\" " + '; '.join(errores))
    propio = c.get('enlace') or {}
    enlaces = [f'{e}: {u}' for e, u in ((propio.get('etiqueta'), con_ref(propio.get('url'), 'yt')),
                                        ('📥 Mis 30 reglas de la CEO, gratis', con_ref(config.get('enlace_venta'), 'yt')),
                                        ('📊 El tablero de la CEO, mi plantilla de dinero', con_ref(config.get('enlace_producto'), 'yt'))) if u][:2]
    post = '\n'.join(l for l in c['texto_post'].strip().splitlines() if 'enlace en mi perfil' not in l)  # en YouTube va el enlace directo
    if s['palabra_clave'].lower() not in post.split('\n')[0].lower():  # la búsqueda lee la primera línea (docs/SEO.md)
        post = s['palabra_clave'][:1].upper() + s['palabra_clave'][1:] + ': ' + post[:1].lower() + post[1:]
    descripcion = '\n\n'.join(x for x in [
        post, '\n'.join(enlaces), f"📚 Fuentes: {c['fuente']}",
        'Preguntas que responde este video:\n' + '\n'.join(f'• {q}' for q in s['preguntas']),
        f"Soy Victoria: un consejo de negocios, dinero y mente fuerte {cada(config)}. Suscríbete para no perderte el siguiente.",
        ' '.join(hashtags_para('youtube', s, config)),
        'Victoria es un personaje creado con IA.'] if x)[:4900]
    return s['titulo'], descripcion, ','.join(etiquetas(s, c.get('pilar', 'finanzas'), config))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) >= 2 and args[0] == 'short':
        c = cargar(args[1])
        rutas, total = tramos(c)
        if total > MAXIMO_SHORT:
            sys.exit(f'ERROR: el short dura {total:.1f} s; máximo {MAXIMO_SHORT}. Acorta las voces del carrusel {c["id"]}.')
        carpeta = os.path.join(RAIZ, 'carruseles', c['id'])
        unir(rutas, os.path.join(carpeta, 'short.mp4'))
        portada_reel = os.path.join(carpeta, '00r.png')
        if os.path.exists(portada_reel):  # el Reel de Instagram abre con su propia portada (otra foto y otro título)
            r, _ = tramos(c, portada=portada_reel)
            unir(r, os.path.join(carpeta, 'reel.mp4'))
            print(f'ok {carpeta}/reel.mp4 (abre con 00r.png)')
        config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
        for nombre, texto in zip(('titulo', 'descripcion_youtube', 'tags_youtube'), textos_youtube(c, config)):
            open(os.path.join(carpeta, f'{nombre}.txt'), 'w').write(texto)
        print(f'ok {carpeta}/short.mp4 ({total:.1f} s) y sus textos de YouTube')
    elif len(args) >= 3 and args[0] == 'largo':
        horizontal = '--horizontal' in sys.argv
        rutas, total = [], 0.0
        for cid in args[2:]:
            r, t = tramos(cargar(cid), horizontal)
            rutas += r
            total += t
        unir(rutas, args[1])
        print(f'ok {args[1]} ({total / 60:.1f} min, {"horizontal" if horizontal else "vertical"})')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
