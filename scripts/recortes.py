"""Shorts verticales a partir de los videos largos (Rodrigo, 12-nov-2026: "podemos usar los videos largos para hacerlos
shorts? así se reutilizan esos videos y ahorramos").

Uso: python scripts/recortes.py <id del largo>          (con VOZ_PYTHON en el entorno para los subtítulos)
     python scripts/recortes.py programar             2 al día desde el día siguiente a que sale su largo
     python scripts/recortes.py publicar <id>          YouTube Shorts + Instagram + TikTok + Facebook

Cada capítulo del largo es un short (si pasa de MAX_S, se parte donde Victoria vuelve a hablar). Como los largos van
intercalados (Victoria → lámina → Victoria...), cada capítulo abre con Victoria a cámara: el gancho con cara, sin pagar
otra toma en Replicate.

Formato 1080x1920 (el de los recortes de podcast):
- fondo: la misma imagen, ampliada y desenfocada;
- arriba: el nombre del capítulo en grande y la etiqueta del tema;
- en medio: Victoria en un cuadro de 1080x1080 recortado alrededor de su cara (resolución nativa: las tomas salen en
  1920x1088, no se amplía) o la lámina a 1080x608;
- abajo: subtítulos (transcribe.py) y, al final, "Video completo en el canal".
Salida: videos/largos/<id>/shorts/<id>-cNN.mp4 y contenido/recortes.json (título, texto y tags para publicar).
"""
import json
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import largo as lg  # noqa: E402

MAX_S = 59.0
MIN_S = 20.0
CUADRO_Y, LAMINA_Y = 470, 360
ENCUADRE = [40, 1520]  # recortar() lo cambia con largos.json → encuadre_short
CIERRE_S = 2.2


def ff(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def _dur(ruta):
    try:
        return lg.duracion(ruta) if os.path.exists(ruta) else None
    except Exception:  # se está escribiendo
        return None


def capitulos(largo):
    """[(nombre, [segmentos])] partiendo donde empieza cada capítulo; si uno pasa de MAX_S, se parte en una toma de Victoria."""
    grupos, actual, nombre = [], [], None
    for s in largo['segmentos']:
        if s.get('capitulo') and actual:
            grupos.append((nombre, actual))
            actual = []
        nombre = s.get('capitulo') or nombre
        actual.append(s)
    if actual:
        grupos.append((nombre, actual))
    _, carpeta = lg.cargar(largo['id'])
    salida = []
    for nombre, segs in grupos:
        trozo, t = [], 0.0
        for s in segs:
            d = _dur(lg.ruta_seg(carpeta, s)) or ((_dur(lg.ruta_voz(carpeta, s)) or 7.6) + 0.35)
            d += 0.3
            if trozo and t + d > MAX_S and s['tipo'] == 'victoria':
                salida.append((nombre, trozo))
                trozo, t = [], 0.0
            trozo.append(s)
            t += d
        if trozo:
            salida.append((nombre, trozo))
    # Un short no puede abrir con lámina: si el primero de un trozo no es Victoria, se une al trozo anterior.
    limpio = []
    for nombre, segs in salida:
        if limpio and segs[0]['tipo'] != 'victoria' and limpio[-1][0] == nombre:
            limpio[-1] = (nombre, limpio[-1][1] + segs)
        else:
            limpio.append((nombre, segs))
    # Los de menos de MIN_S (la intro de 2 frases, un cierre de una toma) se unen al vecino: hacia adelante, y el
    # último hacia atrás. Se queda el nombre del capítulo con más contenido (nunca "Intro" ni "Cierre").
    def seg_total(segs):
        return sum((_dur(lg.ruta_seg(carpeta, x)) or ((_dur(lg.ruta_voz(carpeta, x)) or 7.6) + 0.35)) + 0.3 for x in segs)
    cambio = True
    while cambio and len(limpio) > 1:
        cambio = False
        for i, (nombre, segs) in enumerate(limpio):
            if seg_total(segs) < MIN_S:
                j = i + 1 if i + 1 < len(limpio) else i - 1
                a, b = sorted((i, j))
                nombres = [n for n in (limpio[a][0], limpio[b][0]) if n and n.lower() not in ('intro', 'cierre')]
                limpio[a:b + 1] = [((nombres[0] if nombres else limpio[b][0]), limpio[a][1] + limpio[b][1])]
                cambio = True
                break
    # 12-nov-2026: un capítulo partido en dos daba dos shorts con el MISMO título, y youtube.py (que no sube dos veces
    # el mismo título) le pegó al segundo el enlace del primero (LB1-c03). Cada parte lleva su número.
    cuenta = {}
    for nombre, _ in limpio:
        cuenta[nombre] = cuenta.get(nombre, 0) + 1
    vistos, final = {}, []
    for nombre, segs in limpio:
        if cuenta[nombre] > 1 and nombre:
            vistos[nombre] = vistos.get(nombre, 0) + 1
            final.append((f'{nombre} (parte {vistos[nombre]})', segs))
        else:
            final.append((nombre, segs))
    return final


def tramo_vertical(origen, s, salida, cara_x, capitulo=None):
    """Un segmento del largo (1920x1080) en vertical 1080x1920 con fondo desenfocado."""
    if s['tipo'] == 'victoria':
        # 12-nov-2026: el cuadro de 1080 centrado en la cara dejaba fuera a Capital (está a la izquierda de Victoria).
        # Ahora se toma un cuadro más ancho que incluye a los dos (encuadre_short = [x0, ancho] en px del 1920 original;
        # por defecto el de la foto de podcast) y se escala a 1080 de ancho.
        x0, ancho = ENCUADRE
        filtro = (f"[0:v]split[a][b];[b]scale=-2:1920,crop=1080:1920:(iw-1080)*{cara_x:.3f}:0,boxblur=24:2,eq=brightness=-0.18[f];"
                  f"[a]crop={ancho}:ih:{x0}:0,scale=1080:-2:flags=lanczos[c];[f][c]overlay=0:{CUADRO_Y},fps=30,format=yuv420p[v]")
        ff('-i', origen, '-filter_complex', filtro, '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-crf', '18',
           '-preset', 'medium', '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k', salida)
        return
    # Lámina: la versión vertical (lg.lamina_vertical) sobre fondo negro, con el audio del segmento.
    png = salida.replace('.mp4', '.png')
    lg.lamina_vertical(s, capitulo, png)
    seg = lg.duracion(origen)
    ff('-loop', '1', '-i', png, '-i', origen, '-filter_complex',
       f"[0:v]pad=1080:1920:0:{LAMINA_Y}:color=0x0B0B0D,fps=30,fade=t=in:st=0:d=0.2,format=yuv420p[v]",
       '-map', '[v]', '-map', '1:a', '-t', f'{seg:.3f}', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
       '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k', salida)
    os.remove(png)


def ass_textos(titulo, etiqueta, palabras, duracion):
    """Título arriba todo el short, subtítulos abajo (grupos de 3 palabras) y el cierre al final."""
    def ts(t):
        h, r = divmod(max(0, t), 3600)
        m, s = divmod(r, 60)
        return f'{int(h)}:{int(m):02d}:{s:05.2f}'
    lineas = [f'Dialogue: 0,{ts(0)},{ts(duracion + 1)},Etiqueta,,0,0,0,,{etiqueta.upper()}',
              f'Dialogue: 0,{ts(0)},{ts(duracion + 1)},Titulo,,0,0,0,,{titulo}']
    corte = duracion - CIERRE_S
    grupo = []
    for i, w in enumerate(palabras):
        grupo.append(w)
        fin_grupo = len(grupo) == 3 or re.search(r'[.,:;!?]$', w['w']) or i == len(palabras) - 1
        if fin_grupo:
            ini = grupo[0]['start']
            fin = palabras[i + 1]['start'] if i + 1 < len(palabras) else grupo[-1]['end'] + 0.3
            if ini < corte - 0.15:
                texto = re.sub(r'[.,:;!]+$', '', ' '.join(x['w'] for x in grupo))
                lineas.append(f'Dialogue: 0,{ts(ini)},{ts(min(fin, corte))},Sub,,0,0,0,,{texto}')
            grupo = []
    lineas.append(f'Dialogue: 0,{ts(corte)},{ts(duracion + 1)},Cierre,,0,0,0,,VIDEO COMPLETO EN MI CANAL ▶')
    return ('[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\n'
            'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, '
            'StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
            'Style: Etiqueta,Inter Black,40,&H0042C5F5,&H0042C5F5,&H00000000,&H00000000,1,0,0,0,100,100,3,0,1,0,0,8,80,80,170,1\n'
            'Style: Titulo,Inter Black,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,3,20,0,8,70,70,235,1\n'
            'Style: Sub,Inter Black,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,80,80,230,1\n'
            'Style: Cierre,Inter Black,56,&H0042C5F5,&H0042C5F5,&H00000000,&HC8000000,1,0,0,0,100,100,1,0,3,18,0,2,70,70,250,1\n\n'
            '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n' + '\n'.join(lineas) + '\n')


def recortar(vid):
    largo, carpeta = lg.cargar(vid)
    destino = os.path.join(carpeta, 'shorts')
    os.makedirs(destino, exist_ok=True)
    cara_x = (largo.get('cara') or [0.635])[0]
    global ENCUADRE
    ENCUADRE = largo.get('encuadre_short') or [40, 1520]
    etiqueta = largo.get('etiqueta_shorts') or (largo['seo'].get('palabra_clave') or largo['id']).title()
    voz_py = os.environ.get('VOZ_PYTHON', '/tmp/voz/bin/python')
    registro = []
    for n, (nombre, segs) in enumerate(capitulos(largo), start=1):
        sid = f'{vid}-c{n:02d}'
        final = os.path.join(destino, f'{sid}.mp4')
        faltan = [s for s in segs if not _dur(lg.ruta_seg(carpeta, s))]
        if faltan:
            print(f'{sid}: faltan {len(faltan)} tomas o láminas; se salta (corre "largo.py todo {vid}" primero)')
            continue
        if os.environ.get('SOLO') and sid not in os.environ['SOLO'].split(','):
            continue
        tramos = []
        for k, s in enumerate(segs):
            t = os.path.join(destino, f'{sid}-t{k:02d}.mp4')
            tramo_vertical(lg.ruta_seg(carpeta, s), s, t, cara_x, nombre)
            tramos.append(t)
        lista = os.path.join(destino, f'{sid}.txt')
        open(lista, 'w').write(''.join(f"file '{t}'\n" for t in tramos))
        crudo = os.path.join(destino, f'{sid}-crudo.mp4')
        ff('-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', crudo)
        palabras = os.path.join(destino, f'{sid}-palabras.json')
        subprocess.run([voz_py, os.path.join(RAIZ, 'scripts', 'transcribir.py'), crudo, palabras], check=True, capture_output=True)
        dur = lg.duracion(crudo)
        titulo = nombre if nombre and nombre.lower() not in ('intro', 'cierre') else largo['seo']['titulo'].split(':')[0]
        ass = os.path.join(destino, f'{sid}.ass')
        open(ass, 'w').write(ass_textos(titulo, etiqueta, json.load(open(palabras)), dur))
        ff('-i', crudo, '-vf', f'ass={ass}', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
           '-c:a', 'copy', '-movflags', '+faststart', final)
        for t in tramos + [crudo, lista]:
            os.remove(t)
        primera = next((s['voz'] for s in segs if s['tipo'] == 'victoria'), segs[0]['voz'])
        registro.append({'id': sid, 'largo': vid, 'capitulo': nombre, 'archivo': os.path.relpath(final, RAIZ),
                         'segundos': round(dur, 1), 'titulo': f"{titulo} · {largo['seo']['titulo'].split(':')[0]}"[:95],
                         'texto': f"{primera}\n\nVideo completo en mi canal: {largo['seo']['titulo']}\n\n"
                                  f"Victoria es un personaje creado con IA. Información general, no asesoría.\n\n"
                                  + ' '.join(largo['seo'].get('hashtags', [])[:4]),
                         'tags': largo['seo'].get('tags', [])[:10], 'estado': 'listo'})
        print(f'ok {sid} | {dur:.1f} s | {titulo}', flush=True)
    ruta = os.path.join(RAIZ, 'contenido', 'recortes.json')
    todos = json.load(open(ruta)) if os.path.exists(ruta) else []
    todos = [r for r in todos if r['largo'] != vid] + registro
    json.dump(todos, open(ruta, 'w'), ensure_ascii=False, indent=1)
    open(ruta, 'a').write('\n')
    print(f'ok recortes {vid}: {len(registro)} shorts')


# ---- Publicar en TODAS las redes (Rodrigo, 12-nov-2026: "TODO SE UTILIZA, TODO SE SUBE, TODO SE ADAPTA") ----
# YouTube Shorts (youtube.py), Instagram Reel + TikTok + Facebook (publer.py: Facebook sale a la hora de Instagram).
# 2 al día, desde el día siguiente a que sale su video largo (cada short dice "Video completo en mi canal"), en horas que
# no chocan con los carruseles de la rutina (TikTok 9/13/19 h, Reels 11 y ~19 h): hora de México.
# minutos impares: Publer exige 1 minuto entre posts de la misma cuenta y los carruseles caen en :00 y :30 (12-nov-2026)
TURNOS = [{'yt': '14:00', 'ig': '15:07', 'tt': '16:04'}, {'yt': '20:30', 'ig': '21:37', 'tt': '22:19'}]


def _utc(dia, hora):
    import datetime
    from zoneinfo import ZoneInfo
    h, m = map(int, hora.split(':'))
    local = datetime.datetime.combine(dia, datetime.time(h, m), tzinfo=ZoneInfo('America/Mexico_City'))
    return local.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def programar():
    """Reparte en el calendario los recortes "listo" que aún no tienen hora: 2 al día, alternando videos largos."""
    import datetime
    from zoneinfo import ZoneInfo
    ruta = os.path.join(RAIZ, 'contenido', 'recortes.json')
    todos = json.load(open(ruta))
    largos = {l['id']: l for l in json.load(open(os.path.join(RAIZ, 'contenido', 'largos.json')))}
    ocupados = {}
    for r in todos:
        if r.get('publica_utc_por_red'):
            dia = r['publica_utc_por_red']['ig'][:10]
            ocupados[dia] = ocupados.get(dia, 0) + 1
    hoy = datetime.datetime.now(ZoneInfo('America/Mexico_City')).date()
    pendientes = [r for r in todos if r.get('estado') == 'listo' and not r.get('publica_utc_por_red')]
    # Alternar: uno de cada largo por turno (más variedad), respetando el orden de los capítulos.
    por_largo = {}
    for r in pendientes:
        por_largo.setdefault(r['largo'], []).append(r)
    orden = []
    while any(por_largo.values()):
        for k in sorted(por_largo):
            if por_largo[k]:
                orden.append(por_largo[k].pop(0))
    for r in orden:
        sale = largos.get(r['largo'], {}).get('publica_utc')
        desde = (datetime.datetime.fromisoformat(sale.replace('Z', '+00:00')).astimezone(ZoneInfo('America/Mexico_City')).date()
                 + datetime.timedelta(days=1)) if sale else hoy + datetime.timedelta(days=1)
        dia = max(desde, hoy + datetime.timedelta(days=1))
        while ocupados.get(dia.isoformat(), 0) >= len(TURNOS):
            dia += datetime.timedelta(days=1)
        turno = TURNOS[ocupados.get(dia.isoformat(), 0)]
        r['publica_utc_por_red'] = {red: _utc(dia, h) for red, h in turno.items()}
        ocupados[dia.isoformat()] = ocupados.get(dia.isoformat(), 0) + 1
        print(f"{r['id']}: {dia} (YouTube {turno['yt']}, Instagram y Facebook {turno['ig']}, TikTok {turno['tt']})")
    json.dump(todos, open(ruta, 'w'), ensure_ascii=False, indent=1)
    open(ruta, 'a').write('\n')


def publicar(sid):
    """Sube un recorte a YouTube (Short programado) y por Publer a Instagram, TikTok y Facebook."""
    ruta = os.path.join(RAIZ, 'contenido', 'recortes.json')
    todos = json.load(open(ruta))
    r = next(x for x in todos if x['id'] == sid)
    horas = r.get('publica_utc_por_red') or sys.exit(f'{sid} sin horario: corre "recortes.py programar"')
    archivo = os.path.join(RAIZ, r['archivo'])
    carpeta = os.path.dirname(archivo)
    texto = os.path.join(carpeta, f'{sid}-texto.txt')
    open(texto, 'w').write(r['texto'])
    tags = os.path.join(carpeta, f'{sid}-tags.txt')
    open(tags, 'w').write(','.join(r.get('tags', [])))
    hecho = r.setdefault('publicado_en', {})
    if 'yt' not in hecho:
        y = subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'youtube.py'), 'subir', archivo, r['titulo'], texto,
                            horas['yt'], '--tags', tags], capture_output=True, text=True)
        print(y.stdout[-400:], y.stderr[-400:])
        enlace = next((w for w in y.stdout.split() if 'youtube.com/shorts' in w), '')
        if enlace:
            hecho['yt'] = enlace
            clave = (json.load(open(os.path.join(RAIZ, 'contenido', 'largos.json'))) and
                     next((l.get('playlist', 'aguinaldo') for l in json.load(open(os.path.join(RAIZ, 'contenido', 'largos.json')))
                           if l['id'] == r['largo']), 'aguinaldo'))
            subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'youtube.py'), 'playlist', enlace.split('/')[-1], clave])
    if 'ig_tt_fb' not in hecho:
        pb = subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'publer.py'), 'publicar', archivo, texto,
                             f"ig={horas['ig']},tt={horas['tt']}", r['titulo'][:90]], capture_output=True, text=True)
        print(pb.stdout[-600:], pb.stderr[-400:])
        if pb.returncode == 0:
            hecho['ig_tt_fb'] = horas['ig']
    r['estado'] = 'programado' if {'yt', 'ig_tt_fb'} <= set(hecho) else 'listo'
    json.dump(todos, open(ruta, 'w'), ensure_ascii=False, indent=1)
    open(ruta, 'a').write('\n')
    print(f"{sid}: {r['estado']} {hecho}")


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'programar':
        programar()
    elif len(sys.argv) == 3 and sys.argv[1] == 'publicar':
        publicar(sys.argv[2])
    elif len(sys.argv) == 2:
        recortar(sys.argv[1])
    else:
        sys.exit(__doc__)
