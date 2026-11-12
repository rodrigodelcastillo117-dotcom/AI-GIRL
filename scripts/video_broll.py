"""Escenas de Victoria con movimiento real (Rodrigo, 12-nov-2026: "haz más escenas con movimiento real, no importa el gasto
de Replicate"). Anima una foto del repertorio (assets/fotos/dinamica-*) con bytedance/seedance-1-pro en Replicate:
vertical 9:16, 1080p, 5 s, sin voz. Pasa por el freno de gasto (con la autorización de Rodrigo en config.json →
replicate.autorizaciones) y anota cada predicción en contenido/replicate_ids.txt.

Uso: REPLICATE_AUTORIZACION=broll-movimiento python3 scripts/video_broll.py <escena> "<acción en inglés>"
     (la foto es assets/fotos/dinamica-<escena>.png o .jpg; el clip queda en assets/broll/<escena>-mov-<n>.mp4)
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
MODELO = 'bytedance/seedance-1-pro'
CRUDO = 'https://raw.githubusercontent.com/rodrigodelcastillo117-dotcom/AI-GIRL/main/'
BASE = ('Photorealistic, natural and subtle real-life motion, handheld cinematic feel, shallow depth of field. The same '
        'red-haired woman as in the image, same face, same hair, same outfit, same place. Natural hands and fingers, no '
        'morphing, no extra people, no text, no logos. Elegant, never provocative. ')


def pedir(metodo, url, cuerpo=None):
    cab = {'Authorization': f"Bearer {os.environ['REPLICATE_API_TOKEN']}", 'Content-Type': 'application/json',
           'User-Agent': 'victoria-pipeline/1.0'}
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    for espera in (5, 15, 30, 60):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=datos, headers=cab, method=metodo), timeout=120) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001 (red caída o 5xx: se reintenta)
            print('reintento:', str(e)[:120])
            time.sleep(espera)
    sys.exit('ERROR: Replicate no respondió')


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    escena, accion = sys.argv[1], sys.argv[2]
    foto = next(iter(sorted(glob.glob(os.path.join(RAIZ, 'assets', 'fotos', f'dinamica-{escena}.*')))), None)
    if not foto:
        sys.exit(f'No existe assets/fotos/dinamica-{escena}.*')
    replicate_gasto.freno()
    url = CRUDO + os.path.relpath(foto, RAIZ)
    p = pedir('POST', f'https://api.replicate.com/v1/models/{MODELO}/predictions', {'input': {
        'image': url, 'prompt': BASE + accion, 'duration': 5, 'resolution': '1080p', 'aspect_ratio': '9:16',
        'fps': 24, 'camera_fixed': False}})
    replicate_gasto.anotar(p['id'])
    print('replicate:', p['id'], p.get('status'))
    while p.get('status') not in ('succeeded', 'failed', 'canceled'):
        time.sleep(8)
        p = pedir('GET', p['urls']['get'])
    if p['status'] != 'succeeded':
        sys.exit(f"ERROR: {p.get('error')}")
    salida_url = p['output'] if isinstance(p['output'], str) else p['output'][0]
    n = len(glob.glob(os.path.join(RAIZ, 'assets', 'broll', f'{escena}-mov-*.mp4'))) + 1
    crudo = os.path.join(RAIZ, 'assets', 'broll', f'.{escena}-mov-{n}-crudo.mp4')
    urllib.request.urlretrieve(salida_url, crudo)
    final = os.path.join(RAIZ, 'assets', 'broll', f'{escena}-mov-{n}.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', crudo, '-vf',
                    'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30', '-an', '-c:v', 'libx264',
                    '-crf', '18', '-pix_fmt', 'yuv420p', final], check=True)
    os.remove(crudo)
    ruta = os.path.join(RAIZ, 'assets', 'broll', 'catalogo.json')
    cat = json.load(open(ruta))
    cat['clips'].append({'archivo': os.path.basename(final), 'foto': os.path.basename(foto), 'modelo': MODELO + ' 1080p',
                         'app': 'Replicate', 'segundos': 5, 'accion': accion, 'prediccion': p['id'],
                         'nota_calidad': 'por revisar'})
    json.dump(cat, open(ruta, 'w'), ensure_ascii=False, indent=1)
    print('ok', final)


if __name__ == '__main__':
    main()
