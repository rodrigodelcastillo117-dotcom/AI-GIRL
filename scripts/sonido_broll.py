"""Sonido real para las escenas con movimiento (Rodrigo, 12-nov-2026: "el chiste es que si toma café, no hable, o sea
hacerlo REALISTA"). Mientras Victoria hace la acción NO habla: se oye la escena (la taza en el plato, la calle, el
agua). zsxkib/mmaudio en Replicate genera ese sonido sincronizado con el clip (centavos por clip) y queda guardado para
siempre en assets/broll/sonido/<clip>.m4a: se paga una vez y se reutiliza.

Uso: REPLICATE_AUTORIZACION=shorts-escena python3 scripts/sonido_broll.py <clip.mp4> "<qué se oye, en inglés>"
     (el clip debe estar ya en GitHub: se pasa su URL pública)
     python3 scripts/sonido_broll.py ambiente <escena> "<ambiente continuo, en inglés>"
     → assets/broll/sonido/<escena>-ambiente.m4a (25 s, a partir de la foto de la escena; va bajito debajo de todo el
       short: la calle con claxon lejano, el mar, el rotor del helicóptero, la pista de esquí…)
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_gasto  # noqa: E402
from video_broll import CRUDO, RAIZ, pedir  # noqa: E402

VERSION = '62871fb59889b2d7c13777f08deb3b36bdff88f7e1d53a50ad7694548a41b484'  # zsxkib/mmaudio
NEGATIVO = 'music, speech, voice, talking, singing, words, humming'


def ambiente(escena, que):
    import glob
    foto = sorted(glob.glob(os.path.join(RAIZ, 'assets', 'fotos', f'dinamica-{escena}.*')))[0]
    replicate_gasto.freno(barato=True)
    p = pedir('POST', 'https://api.replicate.com/v1/predictions', {'version': VERSION, 'input': {
        'image': CRUDO + os.path.relpath(foto, RAIZ), 'prompt': que + ', continuous and steady, realistic natural sound, no music',
        'negative_prompt': NEGATIVO + ', clear voices, loud sudden sounds', 'duration': 25}})
    replicate_gasto.anotar(p['id'])
    replicate_gasto.cargar(0.03)
    while p.get('status') not in ('succeeded', 'failed', 'canceled'):
        time.sleep(4)
        p = pedir('GET', p['urls']['get'])
    if p['status'] != 'succeeded':
        sys.exit(f"ERROR: {str(p.get('error'))[:200]}")
    url = p['output'] if isinstance(p['output'], str) else p['output'][0]
    tmp = os.path.join(RAIZ, 'assets', 'broll', 'sonido', f'.tmp-{escena}')
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    urllib.request.urlretrieve(url, tmp)
    salida = os.path.join(RAIZ, 'assets', 'broll', 'sonido', f'{escena}-ambiente.m4a')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', tmp, '-vn', '-af', 'loudnorm=I=-22:TP=-2', '-ar', '48000',
                    '-c:a', 'aac', '-b:a', '160k', salida], check=True)
    os.remove(tmp)
    print('ok', salida, p['id'])


def main():
    if len(sys.argv) == 4 and sys.argv[1] == 'ambiente':
        return ambiente(sys.argv[2], sys.argv[3])
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    clip, que = os.path.abspath(sys.argv[1]), sys.argv[2]
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', clip],
                               capture_output=True, text=True, check=True).stdout)
    replicate_gasto.freno(barato=True)
    # Modelo de la comunidad: se pide por versión (el atajo /models/.../predictions da 404).
    p = pedir('POST', 'https://api.replicate.com/v1/predictions', {'version': VERSION, 'input': {
        'video': CRUDO + os.path.relpath(clip, RAIZ), 'prompt': que + ', realistic natural sound, no music, no voices',
        'negative_prompt': NEGATIVO, 'duration': round(dur, 2)}})
    replicate_gasto.anotar(p['id'])
    replicate_gasto.cargar(0.02)
    while p.get('status') not in ('succeeded', 'failed', 'canceled'):
        time.sleep(4)
        p = pedir('GET', p['urls']['get'])
    if p['status'] != 'succeeded':
        sys.exit(f"ERROR: {p.get('error')}")
    url = p['output'] if isinstance(p['output'], str) else p['output'][0]
    os.makedirs(os.path.join(RAIZ, 'assets', 'broll', 'sonido'), exist_ok=True)
    tmp = os.path.join(RAIZ, 'assets', 'broll', 'sonido', '.tmp-' + os.path.basename(url))
    urllib.request.urlretrieve(url, tmp)
    salida = os.path.join(RAIZ, 'assets', 'broll', 'sonido', os.path.splitext(os.path.basename(clip))[0] + '.m4a')
    # Solo el audio, a -20 LUFS aprox. (ambiente, más bajo que la voz de Victoria)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', tmp, '-vn', '-af', 'loudnorm=I=-22:TP=-2', '-ar', '48000',
                    '-c:a', 'aac', '-b:a', '160k', salida], check=True)
    os.remove(tmp)
    ruta = os.path.join(RAIZ, 'assets', 'broll', 'catalogo.json')
    cat = json.load(open(ruta))
    for c in cat['clips']:
        if c.get('archivo') == os.path.basename(clip):
            c['sonido'] = os.path.relpath(salida, os.path.join(RAIZ, 'assets', 'broll'))
            c['sonido_que'] = que
    json.dump(cat, open(ruta, 'w'), ensure_ascii=False, indent=1)
    print('ok', salida, p['id'])


if __name__ == '__main__':
    main()
