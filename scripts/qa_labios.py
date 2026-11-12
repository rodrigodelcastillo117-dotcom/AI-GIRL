"""¿Los labios van con la voz? Se mide en los cierres de labios (Rodrigo, 12-nov-2026: "se desfasan los labios con el
sonido").

Uso: python qa_labios.py video.mp4 palabras.json      (palabras.json sale de transcribir.py; sale con 1 si no pasa)

Por qué este y no el desfase de qa_sync.py: qa_sync compara cuánto abre la boca contra el volumen de la voz, y la boca se
abre ANTES del sonido (uno se prepara para hablar). Por eso siempre marcaba "boca 300-400 ms adelante" aunque el video
estuviera bien, y corregirlo con tpad dejó los labios 225-291 ms TARDE en los videos 40, O1 y O2 (12-nov-2026: los
originales de Wan medían -39 ms aquí; los corregidos, +225 a +291 ms).

Aquí: en las palabras que empiezan con p, b, m o v los labios TIENEN que cerrarse al empezar. Para cada desfase posible
(-600 a +600 ms) se mide qué tan abierta está la boca en esos instantes (0 = lo más cerrado de los 0.4 s alrededor, 1 = lo
más abierto). El desfase real es el que deja la boca más cerrada. Desfase positivo = la boca va TARDE (después de la voz).

Pasa si: el mejor desfase está entre -MAX_MS y +MAX_MS y, sin corregir nada, la apertura media es APERTURA_MAX o menos.
Con menos de MIN_PALABRAS palabras con p/b/m/v no se puede medir: se dice y no se aprueba ni se reprueba por esto.
Nunca se corrige un video con tpad para que pase: si falla, se genera otra vez.
"""
import json
import sys

import numpy as np

import qa_sync

MAX_MS = 100
APERTURA_MAX = 0.35
MIN_PALABRAS = 4
BILABIALES = ('p', 'b', 'm', 'v')


def medir(video, palabras):
    boca, fps = qa_sync.boca_por_cuadro(video)
    b = np.array([x if x is not None else np.nan for x in boca], float)
    b = np.where(np.isnan(b), np.nanmedian(b), b)
    bil = [w for w in palabras if w['w'].lower().lstrip('¿¡"\'(').startswith(BILABIALES)]
    ventana = int(0.4 * fps)

    def apertura(t):
        i = int(round(t * fps))
        if i < 0 or i >= len(b):
            return np.nan
        seg = b[max(0, i - ventana):min(len(b), i + ventana + 1)]
        rango = seg.max() - seg.min()
        return (b[i] - seg.min()) / rango if rango > 0 else np.nan

    def media(lista, d_ms):
        valores = [apertura(w['start'] + 0.03 + d_ms / 1000) for w in lista]
        return float(np.nanmean(valores)) if valores else float('nan')

    desfases = range(-600, 601, 33)
    puntajes = sorted((media(bil, d), d) for d in desfases)
    tramos = []
    if bil:
        fin = max(w['end'] for w in palabras)
        for k in range(3):
            sub = [w for w in bil if k * fin / 3 <= w['start'] < (k + 1) * fin / 3]
            if len(sub) >= 2:
                mejor = min((media(sub, d), d) for d in desfases)
                tramos.append({'desde_s': round(k * fin / 3, 1), 'palabras': len(sub), 'mejor_desfase_ms': mejor[1],
                               'apertura_sin_corregir': round(media(sub, 0), 2)})
    return {
        'palabras_bilabiales': len(bil),
        'mejor_desfase_ms': puntajes[0][1] if bil else None,
        'apertura_en_mejor': round(puntajes[0][0], 2) if bil else None,
        'apertura_sin_corregir': round(media(bil, 0), 2) if bil else None,
        'tramos': tramos,
    }


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    r = medir(sys.argv[1], json.load(open(sys.argv[2])))
    print(json.dumps(r, ensure_ascii=False))
    if r['palabras_bilabiales'] < MIN_PALABRAS:
        print(f'LABIOS SIN MEDIR: solo {r["palabras_bilabiales"]} palabras con p/b/m/v (mínimo {MIN_PALABRAS})')
        return
    fallas = []
    if abs(r['mejor_desfase_ms']) > MAX_MS:
        lado = 'tarde' if r['mejor_desfase_ms'] > 0 else 'adelante'
        fallas.append(f'los labios van {abs(r["mejor_desfase_ms"])} ms {lado}')
    if r['apertura_sin_corregir'] > APERTURA_MAX:
        fallas.append(f'en p/b/m/v la boca está abierta ({r["apertura_sin_corregir"]}, máximo {APERTURA_MAX})')
    if fallas:
        print('LABIOS FALLA: ' + '; '.join(fallas))
        sys.exit(1)
    print('LABIOS OK')


if __name__ == '__main__':
    main()
