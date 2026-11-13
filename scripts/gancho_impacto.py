"""Gancho de impacto (Rodrigo, 13-nov-2026: "que parece que les avientan algo, corta y hablan… adaptado al fondo, a la
persona, al tema" y "hazlo con Replicate"). 1-2 s de acción en la MISMA escena donde Victoria habla, con un objeto que
ES el tema (ticket, tarjeta, sobre del SAT, billetes…) volando hacia la cámara; corte seco con golpe de sonido y entra
Victoria hablando. Reglas en docs/GANCHOS.md → "Gancho de impacto".

Uso:
  REPLICATE_AUTORIZACION=ganchos-susto python3 scripts/gancho_impacto.py generar <id> "<susto en inglés>" --veo
      anima el primer cuadro de videos/video-<id>.mp4 con seedance-1-pro (5 s, 1080p, ≈$0.75) → videos/video-<id>-gancho-crudo.mp4
      y deja una hoja de cuadros en videos/qa/<id>-gancho-cuadros.jpg para elegir el corte
  python3 scripts/gancho_impacto.py armar <id> <desde_s> <hasta_s> [<impacto_s>]   (segundo del golpe en el crudo)
      recorta el gancho, le pone el texto de pantalla y el golpe de sonido, y lo pega antes de video-<id>-FINAL.mp4
      → video-<id>-FINAL.mp4 (el original queda como video-<id>-FINAL-sin-gancho.mp4) y plan.json → gancho_impacto
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_gasto  # noqa: E402
from video_broll import pedir  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO = 'bytedance/seedance-1-pro'
# Rodrigo, 13-nov: "tiene que ser una PERSONA aventándole algo por atrás o adelante, más brusco": aquí sí entra otra
# persona (solo su brazo o de espaldas), y la acción es rápida y de golpe. Nunca objetos duros ni a la cara.
BASE = ('Photorealistic, real-life handheld footage, same red-haired woman as in the image, same face, same hair, same '
        'outfit, same place. Abrupt, fast, sudden action with real physics and motion blur. Another person may appear only as '
        'an arm or from behind, never their face. Natural hands, no morphing, no text, no logos. Elegant, never provocative. ')
FUENTE = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'


def v(*partes):
    return os.path.join(RAIZ, 'videos', *partes)


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *args], check=True)


def hoja(video, salida, n=10):
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video],
                               capture_output=True, text=True).stdout)
    ffmpeg('-i', video, '-vf', f"fps={n}/{dur},scale=216:384,drawtext=fontfile={FUENTE}:text='%{{pts\\:hms}}':x=6:y=6:"
           "fontsize=18:fontcolor=yellow:box=1:boxcolor=black", '-frames:v', str(n), '-vsync', 'vfr', salida + '-%02d.png')
    ffmpeg('-i', salida + '-%02d.png', '-vf', f'tile={n}x1', salida)
    for i in range(1, n + 1):
        os.remove(f'{salida}-{i:02d}.png')


def generar(vid, accion, modelo='seedance', foto=None):
    """modelo 'veo' (Rodrigo, 13-nov: "ya hazlo perfecto"): google/veo-3.1-fast, 4 s, 1080p, con su PROPIO sonido (el agua,
    el ladrido); mucho mejor en física y en sustos que seedance. El prompt describe el SUSTO, nunca el golpe."""
    # --foto <ruta>: la toma del gancho es OTRA composición (Rodrigo, 13-nov: persona en primer plano avienta una caja y
    # Victoria al fondo), no el primer cuadro del video hablado.
    cuadro = v('qa', f'.{vid}-primer-cuadro.jpg')
    ffmpeg('-i', foto or v(f'video-{vid}.mp4'), '-frames:v', '1', '-vf',
           'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280', '-q:v', '3', cuadro)
    imagen = 'data:image/jpeg;base64,' + base64.b64encode(open(cuadro, 'rb').read()).decode()
    os.remove(cuadro)
    replicate_gasto.freno()
    if modelo == 'veo':
        url = 'https://api.replicate.com/v1/models/google/veo-3.1-fast/predictions'
        entrada = {'image': imagen, 'prompt': accion, 'duration': 4, 'resolution': '1080p', 'aspect_ratio': '9:16',
                   'generate_audio': True,
                   'negative_prompt': 'text, captions, logos, watermark, morphing face, different woman, extra fingers, '
                                      'violence, injury, the object hitting her'}
        costo = 0.6  # ≈ $0.15/s con audio × 4 s (se toma el alto)
    elif modelo == 'kling':  # cuando el filtro de Veo bloquea la escena (E1, 13-nov: "flagged as sensitive" dos veces)
        url = 'https://api.replicate.com/v1/models/kwaivgi/kling-v2.5-turbo-pro/predictions'
        entrada = {'start_image': imagen, 'prompt': accion, 'duration': 5, 'aspect_ratio': '9:16',
                   'negative_prompt': os.environ.get('GANCHO_NEGATIVO', 'text, logos, watermark, morphing face, different woman, extra fingers, injury')}
        costo = 0.5  # no sé el precio exacto de Kling 2.5 Turbo Pro en Replicate: se anota alto
    else:
        url = f'https://api.replicate.com/v1/models/{MODELO}/predictions'
        entrada = {'image': imagen, 'prompt': BASE + accion, 'duration': 5, 'resolution': '1080p', 'aspect_ratio': '9:16',
                   'fps': 24, 'camera_fixed': True}
        costo = 0.75
    p = pedir('POST', url, {'input': entrada})
    replicate_gasto.anotar(p['id'])
    replicate_gasto.cargar(costo)
    print('replicate:', p['id'])
    while p.get('status') not in ('succeeded', 'failed', 'canceled'):
        time.sleep(8)
        p = pedir('GET', p['urls']['get'])
    if p['status'] != 'succeeded':
        sys.exit(f"ERROR: {p.get('error')}")
    crudo = v(f'video-{vid}-gancho-crudo.mp4')
    urllib.request.urlretrieve(p['output'] if isinstance(p['output'], str) else p['output'][0], crudo + '.tmp.mp4')
    audio = ['-c:a', 'aac', '-ar', '48000', '-ac', '2'] if modelo == 'veo' else ['-an']  # Kling: sin audio → golpe sintético
    ffmpeg('-i', crudo + '.tmp.mp4', '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30',
           *audio, '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', crudo)
    os.remove(crudo + '.tmp.mp4')
    hoja(crudo, v('qa', f'{vid}-gancho-cuadros.jpg'), 16)
    print('ok', crudo, '| cuadros: videos/qa/' + f'{vid}-gancho-cuadros.jpg', '| prediccion', p['id'])
    return p['id']


def tiene_audio(video):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0',
                        video], capture_output=True, text=True)
    return bool(r.stdout.strip())


def golpe(segundos, salida, en=None):
    """Silbido (ruido filtrado que sube) y golpe seco grave al final: el sonido del objeto llegando a la cámara."""
    s = max(0.4, segundos)
    ffmpeg('-f', 'lavfi', '-i', f'anoisesrc=d={s}:c=pink:a=0.6', '-f', 'lavfi', '-i', 'sine=f=55:d=0.35',
           '-filter_complex',
           f"[0]highpass=f=900,lowpass=f=6000,afade=t=in:d={s * 0.8},volume=0.55[w];"
           f"[1]afade=t=out:st=0.05:d=0.3,volume=2.2,adelay={int(((en if en is not None else s - 0.12)) * 1000)}|{int(((en if en is not None else s - 0.12)) * 1000)}[g];"
           "[w][g]amix=inputs=2:duration=longest:normalize=0,aresample=48000,pan=stereo|c0=c0|c1=c0",
           '-t', f'{s + 0.25}', '-c:a', 'aac', '-b:a', '192k', salida)


def armar(vid, desde, hasta, impacto=None):
    plan_ruta = os.path.join(RAIZ, 'contenido', 'plan.json')
    plan = json.load(open(plan_ruta))
    item = next(x for x in plan['videos'] if x['id'] == vid)
    final, sin = v(f'video-{vid}-FINAL.mp4'), v(f'video-{vid}-FINAL-sin-gancho.mp4')
    if not os.path.exists(sin):
        shutil.copy(final, sin)
    dur = hasta - desde
    palabras = (item.get('texto_pantalla') or '').upper().split()
    mitad = (len(palabras) + 1) // 2
    textfile = v(f'.{vid}-gancho-texto.txt')
    open(textfile, 'w').write(' '.join(palabras[:mitad]) + ('\n' + ' '.join(palabras[mitad:]) if len(palabras) > 3 else ''))
    clip, sonido = v(f'.{vid}-gancho-clip.mp4'), v(f'.{vid}-gancho.m4a')
    crudo = v(f'video-{vid}-gancho-crudo.mp4')
    if tiene_audio(crudo):  # Veo trae su propio sonido (agua, ladrido): ese manda, con un corte seco al final
        ffmpeg('-ss', str(desde), '-t', str(dur), '-i', crudo, '-vn', '-af', f'afade=t=out:st={max(0, dur - 0.04)}:d=0.04',
               '-c:a', 'aac', '-ar', '48000', '-ac', '2', sonido)
    else:
        golpe(dur, sonido, None if impacto is None else impacto - desde)
    # Mismo estilo que el título del video (mayúsculas, blanco sobre caja negra arriba): que no se note el pegado.
    dibujo = (f"drawtext=fontfile={FUENTE}:textfile={textfile}:fontsize=50:fontcolor=white:line_spacing=6:box=1:"
              "boxcolor=black@0.85:boxborderw=14:text_align=center:x=(w-text_w)/2:y=130" if palabras else 'null')
    ffmpeg('-ss', str(desde), '-t', str(dur), '-i', v(f'video-{vid}-gancho-crudo.mp4'), '-i', sonido,
           '-vf', dibujo, '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-r', '30', '-c:a', 'aac', '-ar', '48000', '-ac', '2', clip)
    ffmpeg('-i', clip, '-i', sin, '-filter_complex',
           '[1:v]fps=30,scale=1080:1920,setsar=1[b];[0:v]setsar=1[a];[1:a]aresample=48000,aformat=channel_layouts=stereo[ba];'
           '[a][0:a][b][ba]concat=n=2:v=1:a=1[vo][ao]', '-map', '[vo]', '-map', '[ao]', '-c:v', 'libx264', '-crf', '18',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', final)
    for f in (clip, sonido, textfile):
        if os.path.exists(f):
            os.remove(f)
    hoja(final, v('qa', f'{vid}-con-gancho-cuadros.jpg'), 12)
    item['gancho_impacto'] = {'desde_s': desde, 'hasta_s': hasta, 'archivo_sin_gancho': os.path.relpath(sin, RAIZ),
                              'prueba': 'gancho-impacto-nov26'}
    json.dump(plan, open(plan_ruta, 'w'), ensure_ascii=False, indent=1)
    print('ok', final, '| revisa videos/qa/' + f'{vid}-con-gancho-cuadros.jpg')


if __name__ == '__main__':
    if len(sys.argv) >= 4 and sys.argv[1] == 'generar':
        generar(sys.argv[2], sys.argv[3], 'veo' if '--veo' in sys.argv else 'kling' if '--kling' in sys.argv else 'seedance',
                sys.argv[sys.argv.index('--foto') + 1] if '--foto' in sys.argv else None)
    elif len(sys.argv) in (5, 6) and sys.argv[1] == 'armar':
        armar(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]) if len(sys.argv) == 6 else None)
    else:
        sys.exit(__doc__)
