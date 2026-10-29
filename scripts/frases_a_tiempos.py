"""Asigna tiempos a las frases de subtítulos del plan usando la transcripción de Whisper.

Uso: python frases_a_tiempos.py palabras_whisper.json frases.json salida.json

frases.json es la lista "subtitulos" del plan. Ambos lados se pasan a palabras habladas
("1%" -> "uno por ciento") y se alinean por oraciones (frases que terminan en . ? !). Si una
oración tiene el mismo número de palabras habladas en el plan y en el audio, cada frase arranca
exactamente en su palabra; si no, se reparte en proporción y se ajusta a la palabra más cercana.
La salida es compatible con subtitular.py (un elemento por frase, con "corte": true).
"""
import json
import re
import sys

from texto import normaliza

palabras = json.load(open(sys.argv[1]))
frases = json.load(open(sys.argv[2]))
FIN = re.compile(r'[.?!]["»”]?$')


def oraciones(items, texto):
    grupos, actual = [], []
    for it in items:
        actual.append(it)
        if FIN.search(texto(it)):
            grupos.append(actual); actual = []
    if actual:
        grupos.append(actual)
    return grupos


def habladas(audio):
    """Palabras habladas de la transcripción, cada una con el inicio de su token de Whisper."""
    return [p['start'] for p in audio for _ in normaliza(p['w']).split()] or [audio[0]['start']]


def repartir(grupo, tiempos):
    conteos = [max(1, len(normaliza(f).split())) for f in grupo]
    exacto = sum(conteos) == len(tiempos)
    salida, acumulado = [], 0
    for f, n in zip(grupo, conteos):
        if exacto:
            t = tiempos[acumulado]
        else:
            t = tiempos[min(len(tiempos) - 1, round(acumulado * len(tiempos) / sum(conteos)))]
        salida.append({'w': f, 'start': round(t, 2)})
        acumulado += n
    return salida, exacto


or_audio = oraciones(palabras, lambda p: p['w'])
or_frases = oraciones(frases, lambda f: f)
resultado, exactas = [], 0
if len(or_audio) == len(or_frases):
    for audio, grupo in zip(or_audio, or_frases):
        parte, exacto = repartir(grupo, habladas(audio))
        resultado += parte
        exactas += exacto
    modo = f'por oraciones ({exactas}/{len(or_frases)} exactas)'
else:
    resultado, _ = repartir(frases, habladas(palabras))
    modo = f'proporcional (oraciones: audio {len(or_audio)} vs plan {len(or_frases)})'

final = palabras[-1]['end'] + 0.3
for i, r in enumerate(resultado):
    r['end'] = round(resultado[i + 1]['start'] if i + 1 < len(resultado) else final, 2)
    r['corte'] = True
json.dump(resultado, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
print('ok', len(resultado), 'frases,', modo)
