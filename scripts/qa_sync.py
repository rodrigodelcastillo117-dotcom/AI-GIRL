"""Revisa que la boca de Victoria vaya en sincronía con su voz (paso 5 de PIPELINE.md).

Uso: python qa_sync.py video.mp4 [reporte.json]     (sale con 1 si no pasa)

Mide en cada cuadro qué tan abierta está la boca (puntos de los labios de MediaPipe, divididos
entre el alto de la cara) y la fuerza de la voz en ese mismo instante, y busca el desfase en el
que más se parecen las dos curvas. Pasa si:
- la cara se encuentra en al menos 80% de los cuadros,
- el mejor desfase cae en la ventana normal. Al hablar, los labios se mueven antes que el sonido:
  en los videos 01 y 02 (bien sincronizados) la boca va 67-100 ms adelante. Con la voz 300 ms
  atrasada a propósito, la medida dio -367 y -400 ms: detecta el desfase. Ventana: de 200 ms de boca
  adelantada a 50 ms de boca atrasada (la voz atrasada más de ~125 ms extra se nota, ITU-R BT.1359),
- la boca sigue a la voz al menos un poco (correlación >= CORR_MINIMA; en videos buenos 0.12-0.28),
- no hay más de 1 segundo seguido de voz con la boca quieta, ni de boca hablando sin voz.
Si una pieza no corre (modelo, ffmpeg), sale con error: eso es un fallo, no un aprobado (regla 8).
"""
import json
import os
import subprocess
import sys
import urllib.request

import cv2
import mediapipe as mp
import numpy as np

MODELO_URL = ('https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/'
              'float16/1/face_landmarker.task')
MODELO = os.path.expanduser('~/.cache/victoria/face_landmarker.task')
CORR_MINIMA = 0.10
BOCA_ADELANTE_MAX_MS, BOCA_ATRAS_MAX_MS = 200, 50
HUECO_MAX_S = 1.0


def modelo():
    if not os.path.exists(MODELO):
        os.makedirs(os.path.dirname(MODELO), exist_ok=True)
        urllib.request.urlretrieve(MODELO_URL, MODELO)
    return MODELO


def boca_por_cuadro(video):
    """Apertura de la boca en cada cuadro (None si no hay cara) y cuadros por segundo."""
    opciones = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=modelo()),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_faces=1)
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    apertura, i = [], 0
    with mp.tasks.vision.FaceLandmarker.create_from_options(opciones) as caras:
        while True:
            ok, cuadro = cap.read()
            if not ok:
                break
            imagen = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB))
            r = caras.detect_for_video(imagen, int(i * 1000 / fps))
            if r.face_landmarks:
                p = r.face_landmarks[0]
                alto = abs(p[152].y - p[10].y) or 1e-6  # barbilla a frente
                apertura.append(abs(p[14].y - p[13].y) / alto)  # labio de abajo menos labio de arriba
            else:
                apertura.append(None)
            i += 1
    cap.release()
    return apertura, fps


def voz_por_cuadro(video, n, fps):
    # first_pts=0: si el audio empieza tarde, el silencio de antes cuenta (si no, el desfase no se ve).
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vn', '-ac', '1', '-ar', '16000',
                          '-af', 'aresample=async=1:first_pts=0', '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
    paso = 16000 / fps
    return np.array([np.sqrt(np.mean(audio[int(k * paso):int((k + 1) * paso)] ** 2) or 0) for k in range(n)])


def huecos(mascara, fps):
    """Segundos de la racha más larga de cuadros en True."""
    mayor = actual = 0
    for m in mascara:
        actual = actual + 1 if m else 0
        mayor = max(mayor, actual)
    return mayor / fps


def revisar(video):
    apertura, fps = boca_por_cuadro(video)
    n = len(apertura)
    con_cara = sum(a is not None for a in apertura) / max(n, 1)
    boca = np.array([a if a is not None else np.nan for a in apertura])
    boca = np.where(np.isnan(boca), np.nanmedian(boca), boca)
    voz = voz_por_cuadro(video, n, fps)
    # La voz suena con la boca abierta: se comparan las dos curvas normalizadas.
    zb = (boca - boca.mean()) / (boca.std() or 1)
    zv = (voz - voz.mean()) / (voz.std() or 1)
    maximo = int(round(0.4 * fps))
    corr = {}
    for d in range(-maximo, maximo + 1):  # d > 0: la boca se mueve d cuadros después de la voz
        a, b = (zv[:n - d], zb[d:]) if d >= 0 else (zv[-d:], zb[:n + d])
        corr[d] = float(np.corrcoef(a, b)[0, 1])
    mejor = max(corr, key=corr.get)
    desfase_ms = round(mejor * 1000 / fps)
    hablando = voz > 0.25 * np.percentile(voz, 95)
    quieta = boca < np.percentile(boca, 20) + 0.15 * (np.percentile(boca, 90) - np.percentile(boca, 20))
    reporte = {
        'cuadros': n, 'fps': round(fps, 2), 'cara_en_cuadros': round(con_cara, 3),
        'desfase_ms': desfase_ms, 'correlacion': round(corr[mejor], 3), 'correlacion_sin_desfase': round(corr[0], 3),
        'voz_con_boca_quieta_s': round(huecos(hablando & quieta, fps), 2),
        'boca_hablando_sin_voz_s': round(huecos(~hablando & ~quieta, fps), 2),
    }
    fallas = []
    if con_cara < 0.8:
        fallas.append(f'la cara solo se encontró en {con_cara:.0%} de los cuadros')
    if not -BOCA_ADELANTE_MAX_MS <= desfase_ms <= BOCA_ATRAS_MAX_MS:
        fallas.append(f'la boca va {abs(desfase_ms)} ms {"atrás" if desfase_ms > 0 else "adelante"} de la voz')
    if corr[mejor] < CORR_MINIMA:
        fallas.append(f'la boca casi no sigue a la voz (correlación {corr[mejor]:.2f}, mínimo {CORR_MINIMA})')
    if reporte['voz_con_boca_quieta_s'] > HUECO_MAX_S:
        fallas.append(f'{reporte["voz_con_boca_quieta_s"]} s de voz con la boca quieta')
    if reporte['boca_hablando_sin_voz_s'] > HUECO_MAX_S:
        fallas.append(f'{reporte["boca_hablando_sin_voz_s"]} s de boca moviéndose sin voz')
    reporte['fallas'] = fallas
    return reporte


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    reporte = revisar(sys.argv[1])
    if len(sys.argv) > 2:
        json.dump(reporte, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(reporte, ensure_ascii=False))
    print('SINCRONÍA OK' if not reporte['fallas'] else 'SINCRONÍA FALLA: ' + '; '.join(reporte['fallas']))
    sys.exit(1 if reporte['fallas'] else 0)


if __name__ == '__main__':
    main()
