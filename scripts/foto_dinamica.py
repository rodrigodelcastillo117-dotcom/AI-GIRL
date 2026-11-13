"""Foto NUEVA del repertorio dinámico (Victoria haciendo algo en un lugar real), con google/nano-banana en Replicate
(≈$0.04). Rodrigo, 12-nov-2026: "que esté en el yate, alberca, jacuzzi, montaña de esquiar, cancha de tenis, campo de
golf, oficina, estadio, avión privado, hangar de helicóptero, un helicóptero… ubicaciones TOP del mundo".

Uso: REPLICATE_AUTORIZACION=shorts-escena python3 scripts/foto_dinamica.py <escena> "<escena completa en inglés>" [perro]
Sale: assets/fotos/dinamica-<escena>.jpg (1200 px). Después: revisar_texto_foto.py y verla.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_gasto  # noqa: E402
from video_broll import RAIZ, pedir  # noqa: E402


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    escena, que, perro = sys.argv[1], sys.argv[2], 'perro' in sys.argv[3:]
    # --mueble <ruta> (se puede repetir): fotos de un mueble real que debe salir tal cual (Rodrigo, 13-nov-2026: los
    # escritorios de Vonhaucke, su empresa). Van al repo y se pasan por su enlace público de GitHub (hacer push antes).
    muebles = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == '--mueble' and i + 1 < len(sys.argv)]
    man = json.load(open(os.path.join(RAIZ, 'assets', 'manifest.json')))
    refs = [man['personaje']['maestra']['url']] + ([man['perro']['url']] if perro else [])
    crudo_gh = 'https://raw.githubusercontent.com/rodrigodelcastillo117-dotcom/AI-GIRL/main/'
    if muebles:
        n0 = len(refs) + 1
        refs += [crudo_gh + os.path.relpath(os.path.abspath(m), RAIZ) for m in muebles]
        que += (f' The desk and chair must be EXACTLY the furniture shown in Images {n0} to {len(refs)} (same shape, '
                'materials, colors, legs and proportions), placed naturally in the room, no logo on it.')
    capital = ('Exactly ONE dog: the Rottweiler of Image 2, calm, nobody touching it.' if perro else
               'No dogs and no animals anywhere in the frame.')
    prompt = ('Candid vertical photo taken by a friend with a phone, a real moment, not posed for a studio. The red-haired '
              'woman of Image 1 (EXACT identity: same face, green eyes, long copper-red wavy hair, subtle freckles). '
              f'{que} {capital} Real place, natural light, realistic skin with visible pores, slight natural grain, no HDR, '
              'not a render. Elegant and classy, never provocative. No text, no logos, no brand names, no watermark, no '
              'readable words anywhere.')
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
    crudo = os.path.join(RAIZ, 'assets', 'fotos', f'.dinamica-{escena}-crudo.jpg')
    urllib.request.urlretrieve(url, crudo)
    final = os.path.join(RAIZ, 'assets', 'fotos', f'dinamica-{escena}.jpg')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', crudo, '-vf', 'scale=1200:-2', '-q:v', '3', final], check=True)
    os.remove(crudo)
    print('ok', final, p['id'])


if __name__ == '__main__':
    main()
