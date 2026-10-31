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
NEGRO = '0x0b0b0d'
# Detrás del proxy de la nube, el certificado está en SSL_CERT_FILE; edge-tts solo mira certifi.
_ca = os.environ.get('SSL_CERT_FILE') or os.environ.get('REQUESTS_CA_BUNDLE')
if _ca and os.path.exists(_ca):
    certifi.where = lambda: _ca
import edge_tts  # noqa: E402


def duracion(ruta):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', ruta],
                       capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)['format']['duration'])


def voces_victoria(carpeta, voces):
    """vozv-XX.mp3 de las frases que falten, con la voz clonada de Victoria y su revisión (voz_victoria.py)."""
    faltan = [{'texto': t, 'salida': os.path.join(carpeta, f'vozv-{i:02d}.mp3')} for i, t in enumerate(voces)
              if not os.path.exists(os.path.join(carpeta, f'vozv-{i:02d}.mp3'))]
    if not faltan:
        return
    python = os.environ.get('VOZ_PYTHON', '/tmp/voz/bin/python')
    if not os.path.exists(python):
        sys.exit(f'ERROR: no está el entorno de voz ({python}); prepáralo con el paso 0 de docs/PIPELINE.md.')
    lista = os.path.join(carpeta, 'voces.json')
    json.dump(faltan, open(lista, 'w'), ensure_ascii=False)
    subprocess.run([python, os.path.join(RAIZ, 'scripts', 'voz_victoria.py'), lista], check=True)
    os.remove(lista)


def tramos(c, horizontal=False):
    """Un MP4 por diapositiva (imagen + su voz). Regresa (rutas, segundos totales)."""
    carpeta = os.path.join(RAIZ, 'carruseles', c['id'])
    hojas = sorted(glob.glob(os.path.join(carpeta, '[0-9][0-9].png')))
    voces = [c['portada']['voz']] + [d['voz'] for d in c['diapositivas']] + [c['cierre']['voz']]
    if len(hojas) != len(voces):
        sys.exit(f'ERROR: hay {len(hojas)} diapositivas y {len(voces)} voces: corre primero carrusel.py {c["id"]}')
    marco = ('scale=864:1080,pad=1920:1080:528:0' if horizontal else 'scale=1080:1350,pad=1080:1920:0:285') + f':color={NEGRO},format=yuv420p'
    rutas, total = [], 0.0
    edge = '--voz-edge' in sys.argv
    if not edge:
        voces_victoria(carpeta, voces)
    for i, (hoja, texto) in enumerate(zip(hojas, voces)):
        audio = os.path.join(carpeta, f'{"voz" if edge else "vozv"}-{i:02d}.mp3')
        if edge and not os.path.exists(audio):
            asyncio.run(edge_tts.Communicate(texto, VOZ, rate='+5%').save(audio))
        segundos = duracion(audio) + AIRE
        total += segundos
        tramo = os.path.join(carpeta, f'tramo-{"h" if horizontal else "v"}-{i:02d}.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', hoja, '-i', audio, '-vf', marco,
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
