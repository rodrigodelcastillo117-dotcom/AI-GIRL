"""Guion de un video tal como se le pasa a Wan 3.0 en el prompt ("She says exactly these words and nothing else"):
con las palabras difíciles escritas como se pronuncian (config.json → pronunciacion) y sin dos puntos ni punto y
coma, que hicieron que Wan inventara frases (videos 37 y 38).

Uso: python guion_para_voz.py <id>

Rodrigo (4-nov-2026): "se le complica México, aguinaldo". Solo cambia lo que se le pide decir a Wan: los
subtítulos, el pie y qa_audio usan el guion normal.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def para_voz(guion, config):
    texto = guion.replace(':', ',').replace(';', ',')
    for escrito, dicho in (config.get('pronunciacion') or {}).items():
        texto = re.sub(rf'\b{re.escape(escrito)}\b', dicho, texto)
    return texto


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    print(para_voz(next(v for v in plan['videos'] if v['id'] == sys.argv[1])['guion'], config))
