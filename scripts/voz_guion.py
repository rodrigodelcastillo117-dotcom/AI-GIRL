"""Audio completo del guion de un video, con la voz clonada de Victoria (MiniMax, voz_victoria.py), para video_replicate.py.

Uso: $VOZ_PYTHON scripts/voz_guion.py <id> salida.mp3

Desde el 12-nov-2026 los videos de Victoria hablando se hacen con Replicate (foto + audio): el audio sale de aquí, así que
la voz es exactamente la de sus carruseles. Parte el guion del plan en frases (. ? !), cada frase pasa por
voz_victoria.py (la transcribe y la repite si no sale bien), y se unen con PAUSA_S de silencio. Se quita el silencio del
inicio para que la primera palabra empiece antes de 0.4 s (regla 23, gancho en el segundo 0).
"""
import json
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAUSA_S = 0.18


def frases_de(guion):
    partes = re.findall(r'[^.?!¿¡]*[¿¡]?[^.?!]*[.?!]+|[^.?!]+$', guion)
    return [p.strip() for p in partes if p.strip()]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    vid, salida = sys.argv[1], os.path.abspath(sys.argv[2])
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    video = next(v for v in plan['videos'] if v['id'] == vid)
    frases = frases_de(video['guion'])
    tmp = tempfile.mkdtemp(prefix=f'voz-{vid}-')
    lista = [{'texto': f, 'salida': os.path.join(tmp, f'f{i:02d}.mp3')} for i, f in enumerate(frases)]
    json.dump(lista, open(os.path.join(tmp, 'lista.json'), 'w'), ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'voz_victoria.py'), os.path.join(tmp, 'lista.json')],
                   check=True)
    silencio = os.path.join(tmp, 'pausa.mp3')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono', '-t', str(PAUSA_S),
                    '-b:a', '160k', silencio], check=True)
    orden = os.path.join(tmp, 'orden.txt')
    with open(orden, 'w') as o:
        for i, f in enumerate(lista):
            if i:
                o.write(f"file '{silencio}'\n")
            o.write(f"file '{f['salida']}'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', orden,
                    '-af', 'aresample=44100,silenceremove=start_periods=1:start_threshold=-45dB,loudnorm=I=-16:TP=-1.5',
                    '-ac', '1', '-ar', '44100', '-b:a', '192k', salida], check=True)
    dur = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', salida],
                         capture_output=True, text=True).stdout.strip()
    print(f'ok {salida} | {len(frases)} frases | {float(dur):.1f} s')


if __name__ == '__main__':
    main()
