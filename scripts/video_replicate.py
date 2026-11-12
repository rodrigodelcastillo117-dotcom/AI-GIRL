"""Video de Victoria hablando con p-video-avatar en Replicate: foto + audio → video 1080p (Rodrigo, 12-nov-2026: "se ve
mejor Replicate, cámbialo"; "tenemos que generar los mejores videos").

Uso: python video_replicate.py foto.jpg audio.mp3 salida.mp4 ["cómo se mueve en el video"]

- Modelo: prunaai/p-video-avatar, 1080p, $0.045 USD por segundo de video (15 s ≈ $0.68). Usa la clave REPLICATE_API_TOKEN
  (la misma de la voz). Nunca la imprimas.
- El audio es la voz de Victoria ya hecha (voz_victoria.py, clon de MiniMax): el modelo mueve la boca con ese audio, así
  que la voz queda exacta.
- Prueba del 12-nov-2026 (video 40): sale 1088x1920 a 24 fps con ~1 s de video de más al final y los labios a tiempo
  (qa_labios: -6 ms). Aquí se recorta al largo del audio y se pasa a 1080x1920 a 30 fps. NO se le aplica tpad: el
  desfase que marcaba qa_sync era falso (ver qa_labios.py).
- Después: transcribir.py + qa_labios.py (labios), qa_sync.py (cara en todos los cuadros, boca sin voz), Capital visible,
  naturalizar, subtítulos, título y cierre, como en PIPELINE.md.
"""
import base64
import json
import mimetypes
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

MODELO = 'prunaai/p-video-avatar'
API = 'https://api.replicate.com/v1'
# Estilo (Rodrigo, 12-nov-2026: "un poquito más coqueta, sensual, nada sexoso, solo sexy entrepreneur... con elegancia"):
# segura, elegante y encantadora; coqueta en la mirada y la sonrisa, nunca en poses ni en el cuerpo.
MOVIMIENTO = ('The red-haired woman is a confident, elegant entrepreneur talking to the camera like a creator filming a phone '
              'video. Poised posture, warm charming smile, a playful knowing look and a subtle raised eyebrow now and then, '
              'graceful small hand gestures, clear mouth movements. Classy and self-assured, never provocative. Her black and '
              'tan Rottweiler stays calmly beside her the whole time. Realistic handheld phone video.')
NEGATIVO = ('subtitles, text, watermark, blurry, distorted face, extra fingers, dog disappearing, another person, '
            'provocative pose, cleavage focus, lingerie, suggestive gestures')


def _pedir(metodo, ruta, cuerpo=None):
    token = os.environ.get('REPLICATE_API_TOKEN')
    if not token:
        sys.exit('Falta REPLICATE_API_TOKEN')
    req = urllib.request.Request(API + ruta, method=metodo, data=json.dumps(cuerpo).encode() if cuerpo else None,
                                 headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                                          'User-Agent': 'victoria-pipeline/1.0'})
    for espera in (5, 15, 30, 60, None):  # la red se corta a veces (12-nov-2026: "Connection reset by peer")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429 or espera is None:
                raise
        except (OSError, urllib.error.URLError):
            if espera is None:
                raise
        print(f'  Replicate no respondió; reintento en {espera} s', flush=True)
        time.sleep(espera)


def _data_uri(ruta):
    tipo = mimetypes.guess_type(ruta)[0] or 'application/octet-stream'
    return f'data:{tipo};base64,' + base64.b64encode(open(ruta, 'rb').read()).decode()


def duracion(ruta):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ruta],
                                capture_output=True, text=True, check=True).stdout.strip())


def generar(foto, audio, salida, movimiento=MOVIMIENTO, tamano='1080:1920'):
    """tamano: '1080:1920' (vertical, Shorts/Reels) o '1920:1080' (horizontal, videos largos de YouTube)."""
    import replicate_gasto
    replicate_gasto.freno()  # tope de gasto (12-nov-2026)
    p = _pedir('POST', f'/models/{MODELO}/predictions', {'input': {
        'image': _data_uri(foto), 'audio': _data_uri(audio), 'resolution': '1080p',
        'video_prompt': movimiento, 'negative_prompt': NEGATIVO}})
    print('replicate:', p['id'], p['status'], flush=True)
    try:
        from replicate_gasto import anotar
        anotar(p['id'])  # para el panel: este gasto es de Victoria
    except Exception:
        pass
    for _ in range(120):  # hasta 10 minutos
        if p['status'] in ('succeeded', 'failed', 'canceled'):
            break
        time.sleep(5)
        p = _pedir('GET', f'/predictions/{p["id"]}')
    if p['status'] != 'succeeded':
        sys.exit(f'Replicate no lo generó: {p["status"]} {p.get("error")}')
    crudo = salida.rsplit('.', 1)[0] + '-replicate.mp4'
    url = p['output'] if isinstance(p['output'], str) else p['output'][0]
    for intento in range(4):  # 12-nov-2026: la descarga se cortó (connection reset) con el video ya pagado
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'victoria-pipeline/1.0'}),
                                        timeout=300) as r:
                open(crudo, 'wb').write(r.read())
            break
        except OSError as e:
            if intento == 3:
                sys.exit(f'No se pudo bajar el video ya pagado ({e}); bájalo de la predicción {p["id"]}')
            time.sleep(2 ** (intento + 1))
    segundos = duracion(audio)
    # Al largo del audio, 1080x1920, 30 fps; el audio se toma del archivo original (es la voz exacta).
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', crudo, '-i', audio, '-map', '0:v', '-map', '1:a',
                    '-vf', f'scale={tamano}:flags=lanczos,fps=30', '-t', f'{segundos:.3f}',
                    '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', salida], check=True)
    costo = round(0.045 * (p.get('metrics') or {}).get('video_output_duration_seconds', segundos), 2)
    try:  # si se corre con una autorización de Rodrigo, se descuenta de su tope (replicate_gasto.cargar)
        from replicate_gasto import cargar
        cargar(costo)
    except Exception:  # noqa: BLE001
        pass
    print(f'ok {salida} | {segundos:.1f} s | ~${costo} USD | crudo: {crudo}')
    return {'replicate_id': p['id'], 'costo_usd': costo, 'crudo': crudo}


if __name__ == '__main__':
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    generar(*sys.argv[1:4], *(sys.argv[4:5] or []))
