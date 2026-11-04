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
comparar = difflib.SequenceMatcher(None, dicho.split(), esperado.split())
similitud = comparar.ratio()
print(f'similitud={similitud:.2f} (mínimo {minimo})')
print('dicho:   ', dicho)
print('esperado:', esperado)
# Rodrigo (4-nov-2026): "se le complica México, aguinaldo". La similitud sola dejó pasar una frase inventada (0.86 y
# 0.91) y palabras mal dichas: se revisa también que no haya 2+ palabras de más seguidas y que cada palabra clave
# del guion (5+ letras: aguinaldo, méxico, intereses...) se entienda tal cual.
d, e = dicho.split(), esperado.split()
fallas = []
for op, i1, i2, j1, j2 in comparar.get_opcodes():
    if op in ('delete', 'replace') and i2 - i1 >= 2 and i2 - i1 > (j2 - j1) + 1:
        fallas.append(f'dijo de más: "{" ".join(d[i1:i2])}"')
for palabra in sorted({x for x in e if len(x) >= 5} - set(d)):
    if palabra.endswith('s') and palabra[:-1] in d:  # "meses sin" se oye "mese sin": las dos s se juntan al hablar
        continue
    fallas.append(f'no se entiende "{palabra}"')
for f in fallas:
    print('FALLA:', f)
sys.exit(0 if similitud >= minimo and not fallas else 1)
