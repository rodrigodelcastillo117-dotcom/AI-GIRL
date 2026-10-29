import json, sys, re, subprocess

video, palabras_json, salida = sys.argv[1], sys.argv[2], sys.argv[3]
clave = set(a.lower() for a in sys.argv[4].split(',')) if len(sys.argv) > 4 else set()
words = json.load(open(palabras_json))

def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"

# Grupos de máximo 3 palabras; se corta en puntuación
grupos, actual = [], []
for w in words:
    actual.append(w)
    if len(actual) == 3 or re.search(r'[.,:;!?]$', w['w']):
        grupos.append(actual); actual = []
if actual:
    grupos.append(actual)

def limpia(t):
    return re.sub(r'[.,:;!?]+$', '', t)

lineas = []
for i, g in enumerate(grupos):
    ini = g[0]['start']
    fin = grupos[i + 1][0]['start'] if i + 1 < len(grupos) else g[-1]['end'] + 0.3
    partes = []
    for w in g:
        t = limpia(w['w'])
        partes.append(r'{\c&H3CB4E6&}' + t + r'{\c&HFFFFFF&}' if limpia(w['w']).lower() in clave else t)
    lineas.append(f"Dialogue: 0,{ts(ini)},{ts(fin)},Sub,,0,0,0,,{' '.join(partes)}")

ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter SemiBold,54,&H00FFFFFF,&H00FFFFFF,&H64000000,&H80000000,0,0,0,0,100,100,0.5,0,1,2.2,1.5,2,60,60,330,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(lineas) + "\n"
ass_path = salida.rsplit('.', 1)[0] + '.ass'
open(ass_path, 'w').write(ass)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', video, '-vf', f"ass={ass_path}",
                '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'copy', salida], check=True)
print('ok', salida, len(grupos), 'lineas')
