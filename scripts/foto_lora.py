"""Foto nueva de Victoria con SU modelo de identidad (LoRA entrenado el 13-nov-2026, oficial: la cara sale igual
siempre). Rodrigo, 13-nov-2026: "déjalo perfecto, siempre, siempre siempre igual".

Uso: REPLICATE_AUTORIZACION=<clave> python3 scripts/foto_lora.py <escena> "<escena completa en inglés>" [--vertical|--horizontal]
Sale: assets/fotos/dinamica-<escena>.jpg (1200 px). Después: compararla contra la hoja maestra y verla.

Cuándo NO usarlo: si la escena lleva un mueble o producto exacto (escritorios de Vonhaucke) o a Capital, se usa
foto_dinamica.py (nano-banana con referencias) y se revisa la cara a mano: el LoRA copia la cara, no los objetos.
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

USD_POR_SEGUNDO = 0.001528


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    escena, que = sys.argv[1], sys.argv[2]
    lora = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))['replicate']['lora_victoria']
    prompt = (f"a candid realistic photo of {lora['palabra']}, a red-haired woman with deep copper-red long wavy hair, "
              f"green eyes, subtle freckles, red lipstick, {que} Natural light, realistic skin texture, elegant and classy, "
              "never provocative, no text, no logos, no brand names, no watermark.")
    replicate_gasto.freno(barato=True)
    r = pedir('POST', 'https://api.replicate.com/v1/predictions', {
        'version': lora['version'].split(':')[1],
        'input': {'prompt': prompt, 'aspect_ratio': '16:9' if '--horizontal' in sys.argv else '9:16',
                  'output_format': 'jpg', 'lora_scale': 1, 'num_inference_steps': 28, 'guidance_scale': 3}})
    replicate_gasto.anotar(r['id'])
    while r['status'] not in ('succeeded', 'failed', 'canceled'):
        time.sleep(3)
        r = pedir('GET', r['urls']['get'])
    if r['status'] != 'succeeded':
        sys.exit(f"ERROR: {r.get('error')}")
    replicate_gasto.cargar(round(((r.get('metrics') or {}).get('predict_time') or 10) * USD_POR_SEGUNDO, 3))
    url = r['output'][0] if isinstance(r['output'], list) else r['output']
    crudo = os.path.join(RAIZ, 'assets', 'fotos', f'.dinamica-{escena}-crudo.jpg')
    urllib.request.urlretrieve(url, crudo)
    final = os.path.join(RAIZ, 'assets', 'fotos', f'dinamica-{escena}.jpg')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', crudo, '-vf', 'scale=1200:-2', '-q:v', '3', final], check=True)
    os.remove(crudo)
    print('ok', final, r['id'])


if __name__ == '__main__':
    main()
