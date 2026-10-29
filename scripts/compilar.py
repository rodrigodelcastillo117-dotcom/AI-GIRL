"""Junta cada 12 Shorts publicados en un video largo para YouTube, Instagram y TikTok.

Uso:
  python compilar.py preparar       Si hay 12 Shorts verificados como publicados que no están en un
                                    largo, crea su entrada en plan.json → largos (videos ordenados del
                                    que mejor rindió al que menos, para retener desde el segundo 0).
                                    Después Claude escribe su bloque "seo" y su "texto_post".
  python compilar.py armar <id>     Arma los archivos del largo <id> (por ejemplo L01):
      videos/largos/<id>-horizontal.mp4  1920x1080 para YouTube (horizontal = video largo; un vertical
                                         de menos de 3 min YouTube lo cuenta como Short)
      videos/largos/<id>-vertical.mp4    720x1280 para Instagram y TikTok (más de 1 min)
      videos/largos/<id>-miniatura.jpg   1280x720 para YouTube
      y guarda los capítulos (minuto de inicio de cada Short) en el plan.
  python compilar.py probar <id_video> [<id_video> ...]   Arma un largo de prueba en /tmp con esos
                                    Shorts (repetidos hasta 12), sin tocar el plan.

Sin gancho ni introducción al inicio (regla 23): el largo abre directo con el mejor Short.
"""
import json
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FUENTE = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FUENTE_LIGERA = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
POR_LARGO = 12
ORO = '0xF5C542'


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *args], check=True)


def duracion(ruta):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ruta],
                                capture_output=True, text=True, check=True).stdout)


def titulo_corto(video):
    """Título del capítulo sin emojis (ffmpeg no los dibuja), en máximo 2 renglones."""
    titulo = (video.get('seo') or {}).get('titulo') or video['guion'].split('.')[0]
    titulo = ''.join(c for c in titulo if ord(c) < 0x2190).strip()
    renglones, actual = [], ''
    for palabra in titulo.split():
        if len(actual) + len(palabra) + 1 > 22 and actual:
            renglones.append(actual)
            actual = palabra
        else:
            actual = f'{actual} {palabra}'.strip()
    renglones.append(actual)
    return titulo, '\n'.join(renglones[:3])


def texto(carpeta, nombre, contenido):
    ruta = os.path.join(carpeta, nombre)
    open(ruta, 'w').write(contenido)
    return ruta.replace(':', r'\:')


def segmento(origen, n, total, video, carpeta):
    """Un Short convertido a horizontal (con marca y capítulo a los lados) y a vertical (con n/total)."""
    _, renglones = titulo_corto(video)
    marca1 = texto(carpeta, f'm1-{n}.txt', 'VICTORIA')
    marca2 = texto(carpeta, f'm2-{n}.txt', 'THE CEO')
    numero = texto(carpeta, f'n-{n}.txt', f'{n}/{total}')
    capitulo = texto(carpeta, f'c-{n}.txt', renglones)
    horizontal = os.path.join(carpeta, f'h-{n:02d}.mp4')
    vertical = os.path.join(carpeta, f'v-{n:02d}.mp4')
    filtro_h = (
        "[0:v]split=2[a][b];"
        "[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=40:2,eq=brightness=-0.28[fondo];"
        "[b]scale=-2:1080[frente];"
        "[fondo][frente]overlay=(W-w)/2:0,"
        f"drawtext=expansion=none:fontfile={FUENTE}:textfile={marca1}:fontsize=78:fontcolor=white:x=(W-608)/4-tw/2:y=H/2-90,"
        f"drawtext=expansion=none:fontfile={FUENTE}:textfile={marca2}:fontsize=58:fontcolor={ORO}:x=(W-608)/4-tw/2:y=H/2+5,"
        f"drawtext=expansion=none:fontfile={FUENTE}:textfile={numero}:fontsize=96:fontcolor={ORO}:x=W-(W-608)/4-tw/2:y=H/2-170,"
        f"drawtext=expansion=none:fontfile={FUENTE_LIGERA}:textfile={capitulo}:fontsize=44:fontcolor=white:line_spacing=12:"
        "x=W-(W-608)/4-tw/2:y=H/2-20,format=yuv420p[v]"
    )
    ffmpeg('-i', origen, '-filter_complex', filtro_h, '-map', '[v]', '-map', '0:a', '-r', '30',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '160k', horizontal)
    filtro_v = (f"scale=720:1280,drawtext=expansion=none:fontfile={FUENTE}:textfile={numero}:fontsize=40:fontcolor={ORO}:"
                "box=1:boxcolor=black@0.45:boxborderw=12:x=40:y=150,format=yuv420p")
    ffmpeg('-i', origen, '-vf', filtro_v, '-r', '30', '-c:v', 'libx264', '-preset', 'medium', '-crf', '22',
           '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '160k', vertical)
    return horizontal, vertical


def unir(partes, salida, carpeta, nombre):
    lista = os.path.join(carpeta, f'{nombre}.txt')
    open(lista, 'w').write(''.join(f"file '{p}'\n" for p in partes))
    ffmpeg('-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', '-movflags', '+faststart', salida)


def miniatura(origen, titulo, salida, carpeta):
    linea = texto(carpeta, 'mini.txt', titulo)
    filtro = (
        "[0:v]split=2[a][b];"
        "[a]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=30:2,eq=brightness=-0.35[fondo];"
        "[b]scale=-2:720[frente];[fondo][frente]overlay=W-w-60:0,"
        f"drawtext=expansion=none:fontfile={FUENTE}:textfile={linea}:fontsize=64:fontcolor=white:line_spacing=14:x=60:y=(H-th)/2,"
        f"drawbox=x=60:y=(ih/2)+150:w=180:h=10:color={ORO}:t=fill"
    )
    ffmpeg('-ss', '3', '-i', origen, '-frames:v', '1', '-filter_complex', filtro, '-q:v', '3', salida)


def armar_archivos(videos, salida_base, carpeta):
    horizontales, verticales, capitulos, inicio = [], [], [], 0.0
    for n, video in enumerate(videos, 1):
        h, v = segmento(os.path.join(RAIZ, video['archivo']), n, len(videos), video, carpeta)
        horizontales.append(h)
        verticales.append(v)
        capitulos.append({'inicio': round(inicio), 'video_id': video['id'], 'titulo': titulo_corto(video)[0]})
        inicio += duracion(h)
    unir(horizontales, f'{salida_base}-horizontal.mp4', carpeta, 'h')
    unir(verticales, f'{salida_base}-vertical.mp4', carpeta, 'v')
    return capitulos


def candidatos(plan):
    usados = {vid for largo in plan.get('largos', []) for vid in largo['videos']}
    return [v for v in plan['videos'] if v['estado'] == 'publicado' and v['id'] not in usados and v.get('archivo')]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ruta_plan = os.path.join(RAIZ, 'contenido', 'plan.json')
    plan = json.load(open(ruta_plan))
    accion = sys.argv[1]

    if accion == 'preparar':
        libres = candidatos(plan)
        if len(libres) < POR_LARGO:
            print(f'Faltan {POR_LARGO - len(libres)} Shorts publicados para el siguiente largo ({len(libres)}/{POR_LARGO}).')
            return
        try:
            notas = json.load(open(os.path.join(RAIZ, 'contenido', 'auditoria.json'))).get('notas', {})
        except (OSError, ValueError):
            notas = {}
        elegidos = sorted(libres[:POR_LARGO], key=lambda v: -(notas.get(v['id'], {}).get('indice') or 0))
        numero = len(plan.get('largos', [])) + 1
        largo = {'id': f'L{numero:02d}', 'estado': 'por_escribir_seo', 'videos': [v['id'] for v in elegidos],
                 'pilar': 'vida', 'texto_post': '', 'seo': None}
        plan.setdefault('largos', []).append(largo)
        json.dump(plan, open(ruta_plan, 'w'), ensure_ascii=False, indent=2)
        print(f"Largo {largo['id']} preparado con {', '.join(largo['videos'])}. Falta escribir su seo y texto_post.")
        return

    if accion == 'probar':
        ids = sys.argv[2:]
        base = [next(v for v in plan['videos'] if v['id'] == i) for i in ids]
        videos = [base[i % len(base)] for i in range(POR_LARGO)]
        carpeta = tempfile.mkdtemp(prefix='largo-prueba-')
        capitulos = armar_archivos(videos, os.path.join(carpeta, 'prueba'), carpeta)
        miniatura(os.path.join(RAIZ, videos[0]['archivo']), '12 reglas de dinero\nque nadie te enseñó', os.path.join(carpeta, 'prueba-miniatura.jpg'), carpeta)
        print('Prueba en', carpeta)
        print(json.dumps(capitulos[:3], ensure_ascii=False))
        return

    if accion == 'armar' and len(sys.argv) > 2:
        largo = next(l for l in plan.get('largos', []) if l['id'] == sys.argv[2])
        videos = [next(v for v in plan['videos'] if v['id'] == i) for i in largo['videos']]
        os.makedirs(os.path.join(RAIZ, 'videos', 'largos'), exist_ok=True)
        base = os.path.join(RAIZ, 'videos', 'largos', largo['id'])
        carpeta = tempfile.mkdtemp(prefix=f"largo-{largo['id']}-")
        largo['capitulos'] = armar_archivos(videos, base, carpeta)
        titulo = ((largo.get('seo') or {}).get('titulo') or 'Victoria The CEO')
        miniatura(os.path.join(RAIZ, videos[0]['archivo']), titulo_corto({'seo': {'titulo': titulo}, 'guion': ''})[1],
                  f'{base}-miniatura.jpg', carpeta)
        largo['archivo_horizontal'] = f"videos/largos/{largo['id']}-horizontal.mp4"
        largo['archivo_vertical'] = f"videos/largos/{largo['id']}-vertical.mp4"
        largo['miniatura'] = f"videos/largos/{largo['id']}-miniatura.jpg"
        largo['estado'] = 'armado'
        json.dump(plan, open(ruta_plan, 'w'), ensure_ascii=False, indent=2)
        print(f"Largo {largo['id']} armado: {duracion(base + '-horizontal.mp4'):.0f} s, {len(videos)} capítulos.")
        return
    sys.exit(__doc__)


if __name__ == '__main__':
    main()
