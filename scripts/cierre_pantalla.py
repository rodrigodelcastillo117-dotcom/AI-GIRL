"""Cierre en pantalla de los últimos segundos de cada video: la pregunta para comentar y la razón para seguir.

Uso: python cierre_pantalla.py video.mp4 <id del plan> salida.mp4

Rodrigo (3-nov-2026): "el chiste es generar más vistas, retención, seguidores, comentarios, todo". Desde que salió
Victoria (28-oct) YouTube no ganó ni un suscriptor y casi nadie comenta: los guiones cierran en bucle (bueno para
que lo repitan) pero nunca piden nada. Esto no toca la voz ni el bucle: solo texto encima en los últimos
SEGUNDOS, sin audio nuevo.
- Arriba, chica: la pregunta del plan (`pregunta_comentarios`), para que comenten.
- Abajo, grande y dorado: "COMENTA Y SÍGUEME", o en una serie "PARTE N+1 MAÑANA: SÍGUEME".
- Desde el 12-nov-2026 los dos van en la franja de los subtítulos (abajo, sin tapar la cara ni a Capital) y
  subtitular.py ya no pone subtítulos en estos SEGUNDOS: antes salían a media pantalla y encima del último subtítulo.
Va después de titulo_pantalla.py (PIPELINE paso 6). El audio se copia tal cual: la sincronía no cambia.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from titulo_pantalla import duracion, ts  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEGUNDOS = 2.2


def limpio(texto):
    return ''.join(c for c in texto if ord(c) < 0x2190).strip()  # sin emoji: la letra no los tiene


def textos(video):
    pregunta = limpio(video.get('pregunta_comentarios') or '')
    serie = video.get('serie') or {}
    parte = video.get('parte') or ''
    m = re.search(r'(\d+)\s*(?:de|/)\s*(\d+)', str(parte))  # "parte 2 de 4" o "2/4"
    parte = f'{m.group(1)}/{m.group(2)}' if m else ''
    if serie.get('numero') and serie.get('total') and serie['numero'] < serie['total']:
        llamado = f"PARTE {serie['numero'] + 1} MUY PRONTO: SÍGUEME"
    elif '/' in str(parte) and int(str(parte).split('/')[0]) < int(str(parte).split('/')[1]):
        llamado = f"PARTE {int(str(parte).split('/')[0]) + 1} MUY PRONTO: SÍGUEME"
    elif video.get('llamado_cierre'):  # MUSE (12-nov-2026): un solo llamado por pieza (guardar O compartir)
        llamado = limpio(video['llamado_cierre']).upper()
    else:
        llamado = 'COMENTA Y SÍGUEME'
    return pregunta, llamado


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    entrada, vid, salida = sys.argv[1:]
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    video = next((v for v in plan['videos'] if v['id'] == vid), None)
    if not video:
        sys.exit(f'ERROR: no existe el video {vid} en el plan')
    pregunta, llamado = textos(video)
    fin = duracion(entrada)
    inicio = max(0.0, fin - SEGUNDOS)
    lineas = []
    if pregunta:
        lineas.append(f"Dialogue: 0,{ts(inicio)},{ts(fin + 1)},Pregunta,,0,0,0,,{pregunta}")
    lineas.append(f"Dialogue: 0,{ts(inicio)},{ts(fin + 1)},Llamado,,0,0,0,,{llamado}")
    ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pregunta,Inter SemiBold,34,&H00FFFFFF,&H00FFFFFF,&H64000000,&H64000000,0,0,0,0,100,100,0,0,3,14,0,5,70,70,0,1
Style: Llamado,Inter Black,38,&H0042C5F5,&H0042C5F5,&H64000000,&H64000000,0,0,0,0,100,100,1,0,3,16,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + '\n'.join(l.replace(',Pregunta,,0,0,0,,', ',Pregunta,,0,0,0,,{\\pos(360,860)}')
                .replace(',Llamado,,0,0,0,,', ',Llamado,,0,0,0,,{\\pos(360,965)}') for l in lineas) + '\n'
    ruta_ass = salida.rsplit('.', 1)[0] + '-cierre.ass'
    open(ruta_ass, 'w').write(ass)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', entrada, '-vf', f'ass={ruta_ass}',
                    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'copy', salida],
                   check=True)
    print('ok', salida, '|', pregunta, '/', llamado, f'| desde {inicio:.1f} s')


if __name__ == '__main__':
    main()
