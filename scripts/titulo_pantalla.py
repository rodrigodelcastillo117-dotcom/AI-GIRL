"""Pone el título del video fijo arriba, en la franja del fondo, durante todo el video.

Uso: python titulo_pantalla.py video-SUBTITULADO.mp4 "Título sin emoji" salida.mp4

Quien ve sin sonido (la mayoría al deslizar) sabe de qué trata desde el segundo 0 (regla 23).
Va en la parte de arriba del cuadro, que en los videos de Victoria es techo, cielo o pared: no tapa
la cara (que está más abajo, en el primer tercio) ni los subtítulos (abajo).
"""
import json
import subprocess
import sys
import textwrap


def duracion(video):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', video],
                       capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)['format']['duration'])


def ts(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f'{int(h)}:{int(m):02d}:{s:05.2f}'


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    video, titulo, salida = sys.argv[1:]
    texto = ''.join(c for c in titulo if ord(c) < 0x2190).strip()  # sin emojis: la fuente no los tiene
    renglones = textwrap.wrap(texto.upper(), width=22)[:3]
    salto = '\\N'  # salto de línea de ASS
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Titulo,Inter Black,46,&H00FFFFFF,&H00FFFFFF,&H50000000,&H50000000,0,0,0,0,100,100,1,0,3,14,0,8,50,50,96,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ts(0)},{ts(duracion(video) + 1)},Titulo,,0,0,0,,{salto.join(renglones)}
"""
    ruta_ass = salida.rsplit('.', 1)[0] + '-titulo.ass'
    open(ruta_ass, 'w').write(ass)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', video, '-vf', f'ass={ruta_ass}',
                    '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'copy', salida], check=True)
    print('ok', salida, '|', ' / '.join(renglones))


if __name__ == '__main__':
    main()
