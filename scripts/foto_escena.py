"""Foto de Victoria HABLANDO A CÁMARA dentro de una escena del repertorio dinámico, para los shorts con acción
(Rodrigo, 12-nov-2026: "shorts que duren 15-20 segundos, que hable, que diga cosas, que haga acciones dependiendo del
entorno"). Toma la foto de actividad assets/fotos/dinamica-<escena> y la hoja maestra de Victoria y pide con
google/nano-banana (Replicate, ≈$0.04) la misma mujer, mismo lugar y ropa, ahora de pecho para arriba mirando a la
lente, como creadora grabándose. Esa foto es la que p-video-avatar hace hablar (video_replicate.py); la acción de la
escena entra después en medio del short (insertar_accion.py) con el clip assets/broll/<escena>-mov-N.mp4.

Uso: REPLICATE_AUTORIZACION=shorts-escena python3 scripts/foto_escena.py <escena> "<qué hace mientras habla>" [perro]
     "perro" pide a Capital en el cuadro; solo donde un perro real estaría (DIRECCION_CREATIVA → Capital con criterio).
Sale: assets/fotos/habla-<escena>.jpg (1200 px de ancho). Después: revisar_texto_foto.py y verla.
"""
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_gasto  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRUDO = 'https://raw.githubusercontent.com/rodrigodelcastillo117-dotcom/AI-GIRL/main/'
from video_broll import pedir  # noqa: E402


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    escena, accion, perro = sys.argv[1], sys.argv[2], 'perro' in sys.argv[3:]
    foto = next(iter(sorted(glob.glob(os.path.join(RAIZ, 'assets', 'fotos', f'dinamica-{escena}.*')))), None)
    if not foto:
        sys.exit(f'No existe assets/fotos/dinamica-{escena}.*')
    man = json.load(open(os.path.join(RAIZ, 'assets', 'manifest.json')))
    refs = [man['personaje']['maestra']['url'], CRUDO + os.path.relpath(foto, RAIZ)]
    if perro:
        refs.append(man['perro']['url'])
    # Una sola vez Capital: si la foto de la escena ya lo trae, el modelo añadía un segundo perro (café, 12-nov).
    capital = ('Exactly ONE dog: the Rottweiler of Image 3 (black leather collar with gold plate), calm, partly visible at '
               'the bottom edge of the frame, nobody touching it. Never two dogs.' if perro else
               'No dog and no animals in the frame at all.')
    prompt = (
        'Candid vertical smartphone frame from a real talking-head video filmed by the creator herself. The red-haired '
        'woman of Image 1 (EXACT identity: same face, green eyes, long copper-red wavy hair, subtle freckles) in the SAME '
        'place, light and outfit as Image 2, now a MEDIUM CLOSE-UP: her head, shoulders and upper chest fill the vertical '
        'frame (never full body, never a wide shot), slightly off-center, camera at eye level and close, like a phone '
        f'propped on the table. {accion} Nothing in front of her mouth or face; both hands below the chin. She looks straight into the lens, mid-sentence, with a confident, charming half-smile. '
        f'{capital} Real place, natural light, realistic skin texture with visible pores, slight natural grain, not a '
        'studio render, no HDR. Elegant and classy, never provocative. No text, no logos, no watermark, no readable '
        'words anywhere.')
    replicate_gasto.freno(barato=True)
    p = pedir('POST', 'https://api.replicate.com/v1/models/google/nano-banana/predictions',
              {'input': {'prompt': prompt, 'image_input': refs, 'aspect_ratio': '9:16', 'output_format': 'jpg'}})
    replicate_gasto.anotar(p['id'])
    replicate_gasto.cargar(0.04)
    while p.get('status') not in ('succeeded', 'failed', 'canceled'):
        time.sleep(4)
        p = pedir('GET', p['urls']['get'])
    if p['status'] != 'succeeded':
        sys.exit(f"ERROR: {p.get('error')}")
    url = p['output'] if isinstance(p['output'], str) else p['output'][0]
    crudo = os.path.join(RAIZ, 'assets', 'fotos', f'.habla-{escena}-crudo.jpg')
    urllib.request.urlretrieve(url, crudo)
    final = os.path.join(RAIZ, 'assets', 'fotos', f'habla-{escena}.jpg')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', crudo, '-vf', 'scale=1200:-2', '-q:v', '3', final],
                   check=True)
    os.remove(crudo)
    print('ok', final, p['id'])


if __name__ == '__main__':
    main()
