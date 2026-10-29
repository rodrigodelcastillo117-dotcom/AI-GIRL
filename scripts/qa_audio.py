"""Compara lo que dijo Victoria (transcripción de Whisper) con el guion del plan.

Uso: python qa_audio.py palabras.json "guion del plan" [similitud_minima]
Sale con código 1 si la similitud queda por debajo del mínimo (default 0.85).
Los números que Whisper escribe con dígitos ("80%", "37") se pasan a palabras antes de comparar.
"""
import difflib
import json
import sys

from texto import normaliza


palabras = json.load(open(sys.argv[1]))
dicho = normaliza(' '.join(p['w'] for p in palabras))
esperado = normaliza(sys.argv[2])
minimo = float(sys.argv[3]) if len(sys.argv) > 3 else 0.85
similitud = difflib.SequenceMatcher(None, dicho.split(), esperado.split()).ratio()
print(f'similitud={similitud:.2f} (mínimo {minimo})')
print('dicho:   ', dicho)
print('esperado:', esperado)
sys.exit(0 if similitud >= minimo else 1)
