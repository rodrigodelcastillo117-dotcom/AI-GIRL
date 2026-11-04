"""Cambia la voz de un video de Victoria por la voz nueva (mexicana nativa convertida a Victoria), frase por frase,
cada una ajustada al tiempo exacto en que sus labios la dicen. 0 créditos.

Uso (python del sistema): python doblar.py video.mp4 palabras.json <id del plan> salida.mp4

Rodrigo (4-nov-2026): "hay que mejorar muchísimo la voz, se le complica México, aguinaldo" y "arreglemos todo, lo
más real posible". Wan 3.0 genera la voz junto con la imagen y a veces la pronuncia mal ("Mese sin intereses").
1. Las frases salen de `subtitulos` del plan; su inicio y fin, de palabras.json (transcripción de la voz de Wan).
2. Cada frase la dice Edge es-MX (pronunciación mexicana) y voz_victoria.py la pasa al timbre de Victoria.
3. Cada frase se estira o encoge (atempo, entre 0.8x y 1.25x) para durar lo mismo que en el video y se pone en su
   lugar; el resto queda en silencio con el ruido de cuarto del original muy bajo.
Después se pasa por qa_audio y qa_sync como cualquier video (PIPELINE paso 5): si la boca no cuadra, no se usa.
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carrusel_video import VOZ, duracion, edge_tts  # noqa: E402  (trae el certificado del proxy)
import asyncio  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tramos_de(frases, palabras):
    """(texto, inicio, fin) de cada frase, alineando sus palabras en orden con la transcripción."""
    salida, i = [], 0
    for frase in frases:
        n = len(frase.split())
        bloque = palabras[i:i + n] or palabras[-1:]
        salida.append((frase, bloque[0]['start'], bloque[-1]['end']))
        i += n
    return salida


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    video, ruta_palabras, vid, salida = sys.argv[1:]
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    v = next(x for x in plan['videos'] if x['id'] == vid)
    palabras = json.load(open(ruta_palabras))
    tramos = tramos_de(v['subtitulos'], palabras)
    tmp = tempfile.mkdtemp()
    lista = [{'texto': t, 'salida': os.path.join(tmp, f'f{i:02d}.mp3'), 'base': os.path.join(tmp, f'b{i:02d}.mp3')}
             for i, (t, _, _) in enumerate(tramos)]
    for f in lista:
        asyncio.run(edge_tts.Communicate(f['texto'], VOZ, rate='+4%').save(f['base']))
    python = os.environ.get('VOZ_PYTHON', '/home/user/voz/venv/bin/python')
    json.dump(lista, open(os.path.join(tmp, 'lista.json'), 'w'), ensure_ascii=False)
    subprocess.run([python, os.path.join(RAIZ, 'scripts', 'voz_victoria.py'), os.path.join(tmp, 'lista.json')], check=True)
    entradas, filtros = ['-i', video], []
    for i, ((_, inicio, fin), f) in enumerate(zip(tramos, lista)):
        largo = max(0.3, fin - inicio)
        tempo = min(1.25, max(0.8, duracion(f['salida']) / largo))
        entradas += ['-i', f['salida']]
        filtros.append(f'[{i + 1}:a]silenceremove=start_periods=1:start_threshold=-45dB,atempo={tempo:.3f},'
                       f'adelay={int(inicio * 1000)}|{int(inicio * 1000)}[f{i}]')
    filtros.append('[0:a]volume=0.06[fondo]')  # ruido de cuarto del original, muy bajo
    filtros.append(''.join(f'[f{i}]' for i in range(len(lista))) + f'[fondo]amix=inputs={len(lista) + 1}:normalize=0,'
                   'loudnorm=I=-16:TP=-1.5[a]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *entradas, '-filter_complex', ';'.join(filtros), '-map', '0:v',
                    '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', salida], check=True)
    print('ok', salida, f'({len(tramos)} frases)')


if __name__ == '__main__':
    main()
