"""Entrena UNA vez el modelo de identidad de Victoria (LoRA de FLUX en Replicate) para que su cara salga siempre igual
(Rodrigo, 13-nov-2026: "déjalo perfecto, siempre, siempre siempre igual"; autorización `lora-victoria`, tope $5).

Uso: REPLICATE_AUTORIZACION=lora-victoria python3 scripts/entrenar_lora.py <carpeta_con_fotos> [--pasos 1000]
     REPLICATE_AUTORIZACION=lora-victoria python3 scripts/entrenar_lora.py --estado <id_entrenamiento>

Las fotos (15-25, revisadas contra la hoja maestra: assets/personaje-hoja-v4-pecas.png) se suben a Replicate como zip;
el modelo queda privado en <cuenta>/victoria-ceo-lora y se activa con la palabra VICTORIACEO en el prompt.
El costo real (segundos de H100) se anota en la autorización al terminar.
"""
import json
import os
import subprocess
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_gasto  # noqa: E402
from video_broll import RAIZ, pedir  # noqa: E402

API = 'https://api.replicate.com/v1'
ENTRENADOR = 'ostris/flux-dev-lora-trainer'
MODELO = 'victoria-ceo-lora'
PALABRA = 'VICTORIACEO'
USD_POR_SEGUNDO_H100 = 0.001528  # precio publicado de Replicate para H100 (revisar si cambia)


def subir_zip(carpeta):
    ruta = os.path.join(carpeta, '..', 'victoria-lora.zip')
    with zipfile.ZipFile(ruta, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(carpeta)):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                z.write(os.path.join(carpeta, f), f)
    r = subprocess.run(['curl', '-s', '-H', f"Authorization: Bearer {os.environ['REPLICATE_API_TOKEN']}",
                        '-F', f'content=@{ruta};type=application/zip', f'{API}/files'],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)['urls']['get']


def estado(tid):
    t = pedir('GET', f'{API}/trainings/{tid}')
    seg = (t.get('metrics') or {}).get('predict_time')
    print(t['status'], '| segundos:', seg, '| salida:', (t.get('output') or {}).get('version'))
    return t, seg


def main():
    if '--estado' in sys.argv:
        tid = sys.argv[sys.argv.index('--estado') + 1]
        t, seg = estado(tid)
        if t['status'] == 'succeeded' and seg:
            replicate_gasto.cargar(round(seg * USD_POR_SEGUNDO_H100, 2))
        return
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    replicate_gasto.freno()  # lo caro: respeta el tope de la autorización
    carpeta = sys.argv[1]
    pasos = int(sys.argv[sys.argv.index('--pasos') + 1]) if '--pasos' in sys.argv else 1000
    cuenta = pedir('GET', f'{API}/account')['username']
    try:
        pedir('POST', f'{API}/models', {'owner': cuenta, 'name': MODELO, 'visibility': 'private', 'hardware': 'gpu-t4',
                                        'description': 'Identidad de Victoria The CEO (personaje creado con IA)'})
    except SystemExit as e:  # ya existe
        print('modelo:', str(e)[:80])
    version = pedir('GET', f'{API}/models/{ENTRENADOR}')['latest_version']['id']
    url = subir_zip(carpeta)
    t = pedir('POST', f'{API}/models/{ENTRENADOR}/versions/{version}/trainings', {
        'destination': f'{cuenta}/{MODELO}',
        'input': {'input_images': url, 'trigger_word': PALABRA, 'steps': pasos, 'lora_rank': 16,
                  'learning_rate': 0.0004, 'batch_size': 1, 'resolution': '512,768,1024', 'autocaption': True,
                  'autocaption_prefix': f'a photo of {PALABRA}, a red-haired woman,'}})
    replicate_gasto.anotar(t['id'])
    print('entrenando', t['id'], '→', f'{cuenta}/{MODELO}')
    while t['status'] not in ('succeeded', 'failed', 'canceled'):
        time.sleep(30)
        t, seg = estado(t['id'])
    if t['status'] != 'succeeded':
        sys.exit(f"ERROR: {t.get('error')}")
    seg = (t.get('metrics') or {}).get('predict_time') or 0
    replicate_gasto.cargar(round(seg * USD_POR_SEGUNDO_H100, 2))
    conf = os.path.join(RAIZ, 'contenido', 'config.json')
    c = json.load(open(conf))
    c.setdefault('replicate', {})['lora_victoria'] = {'version': t['output']['version'], 'palabra': PALABRA,
                                                      'entrenamiento': t['id'], 'pasos': pasos, 'oficial': False}
    json.dump(c, open(conf, 'w'), ensure_ascii=False, indent=1)
    print('ok', t['output']['version'], f'| ${seg * USD_POR_SEGUNDO_H100:.2f}')


if __name__ == '__main__':
    main()
