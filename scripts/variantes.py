"""Variantes de lo que ya ganó: nuestro "BuzzFy" (Rodrigo, 14-nov-2026: "haz eso justamente").

Lo que hace BuzzFy (buzzfy.co, $19-39 USD al mes) y aquí sale gratis con lo que ya tenemos:
1. Toma las publicaciones que mejor funcionaron (salud.py → ganadores; aquí: 3 veces la mediana de su red y 500+ vistas).
2. Les hace versiones NUEVAS, no copias: otro gancho/título arriba y otra edición del cuadro (acercamiento, fondo
   difuminado, color) y, si se le pasa un comentario REAL, una burbuja de "respuesta a @alguien".
3. Las publica a gente que todavía no sigue a Victoria: en TikTok (casi todo lo que ve la gente ahí es "Para ti") y en
   YouTube Shorts; en Instagram solo como Trial Reel (solo a no seguidores) cuando Meta los desbloquee: Meta los niega
   a la cuenta por pocos seguidores (62 el 13-nov; ~200 según BuzzFy). `probar` lo revisa solo.
4. Las mide a los 1, 3 y 7 días. Una variante "rompe" si pasa 10,000 vistas o la mitad de las vistas del original en
   esa red; la que rompe se vuelve original y recibe sus propias variantes.

Uso:
  python scripts/variantes.py candidatos                   qué originales merecen variantes y cuántas llevan
  python scripts/variantes.py hacer <id> "<gancho>" [--edicion inicio|zoom|fondo|color] [--comentario "texto" --autor "@x"]
                                                           arma videos/variantes/<vid>/video.mp4 + textos; NO publica
  python scripts/variantes.py publicar <vid> <cuando_utc> [--redes tt,yt] [--solo-plan]
                                                           TikTok (Publer) + YouTube Shorts; Instagram solo si hay Trial
                                                           Reels. --solo-plan anota la hora y no sube nada todavía
  python scripts/variantes.py pendientes                   sube lo que está en plan y sale en 48 h o menos
  python scripts/variantes.py medir                        foto de vistas a los 1/3/7 días y marca las que rompen
  python scripts/variantes.py probar                       ¿Meta ya deja Trial Reels? (con 200+ seguidores o cada lunes)
  python scripts/variantes.py ver                          tabla de variantes y resultados

Registro: contenido/variantes.json. Reglas: config.json → variantes. Cada variante cuenta como clon ("clon_de") en
salud.py → Ganadores. Las variantes NUNCA cambian datos ni cifras del original: solo empaque (gancho, cuadro, orden).
"""
import datetime
import glob
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRO = os.path.join(RAIZ, 'contenido', 'variantes.json')
CARPETA = os.path.join(RAIZ, 'videos', 'variantes')
FUENTES = '/usr/share/fonts/opentype/inter/'
EDICIONES = ('inicio', 'zoom', 'fondo', 'color')  # en este orden se reparten entre las variantes de un original
AHORA = datetime.datetime.now(datetime.timezone.utc)


def leer(nombre, defecto):
    try:
        return json.load(open(os.path.join(RAIZ, 'contenido', nombre)))
    except (OSError, ValueError):
        return defecto


def conf():
    base = {'por_dia': {'tt': 1, 'yt': 1, 'ig_trial': 3}, 'max_por_original': 6, 'minimo_vistas': 500,
            'veces_mediana': 3, 'rompe_vistas': 10000, 'rompe_fraccion_original': 0.5, 'checkpoints_dias': [1, 3, 7],
            'ig_trial': False, 'min_seguidores_ig_trial': 200}
    base.update(leer('config.json', {}).get('variantes') or {})
    return base


def registro():
    return leer('variantes.json', [])


def guardar(filas):
    with open(REGISTRO, 'w') as f:
        json.dump(filas, f, ensure_ascii=False, indent=1)
        f.write('\n')


def sin_emoji(t):
    return ''.join(c for c in (t or '') if ord(c) < 0x2190 and c != '️').strip()


def correr(*cmd):
    r = subprocess.run(list(cmd), capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'ERROR en {os.path.basename(str(cmd[1]))}: {(r.stderr or r.stdout)[-600:]}')
    return r.stdout


# ---------- qué merece variantes ----------

def originales():
    """{id: datos} de videos del plan y carruseles (y variantes que rompieron, que se tratan como originales)."""
    salida = {}
    for v in leer('plan.json', {}).get('videos', []):
        salida[v['id']] = {'tipo': 'video', 'd': v}
    for c in leer('carruseles.json', {}).get('carruseles', []):
        salida[c['id']] = {'tipo': 'carrusel', 'd': c}
    for x in registro():
        if x.get('rompio'):
            salida[x['id']] = {'tipo': 'variante', 'd': x}
    return salida


def vistas_publicadas():
    try:
        return json.load(open(os.path.join(RAIZ, 'centro', 'datos', 'estado.json')))[0].get('publicaciones') or []
    except (OSError, ValueError, IndexError, KeyError):
        return []


def candidatos():
    c = conf()
    pubs = vistas_publicadas()
    hechas = {}
    for x in registro():
        hechas[x['original']] = hechas.get(x['original'], 0) + 1
    salida = []
    for red in ('tt', 'yt', 'ig'):
        valores = [p['por_red'][red] for p in pubs if p['por_red'].get(red)]
        if len(valores) < 5:
            continue
        mediana = statistics.median(valores)
        for p in pubs:
            v = p['por_red'].get(red) or 0
            if v >= max(c['minimo_vistas'], c['veces_mediana'] * mediana):
                salida.append({'id': p['id'], 'red': red, 'vistas': v, 'mediana': round(mediana), 'titulo': p['titulo'],
                               'hechas': hechas.get(p['id'], 0)})
    for x in registro():  # las variantes que rompieron también se reciclan (BuzzFy: "new versions of their own")
        if x.get('rompio'):
            salida.append({'id': x['id'], 'red': x['rompio']['red'], 'vistas': x['rompio']['vistas'], 'mediana': None,
                           'titulo': x['gancho'], 'hechas': hechas.get(x['id'], 0)})
    mejor = {}
    for s in sorted(salida, key=lambda s: -s['vistas']):
        mejor.setdefault(s['id'], s)
    return [s for s in mejor.values() if s['hechas'] < c['max_por_original']]


# ---------- hacer la variante ----------

def fuente(original):
    """(video limpio o None, subtítulos .ass o None, video final con audio).
    Videos del plan: el limpio es -sinc.mp4 (sin subtítulos ni título) y los subtítulos se vuelven a quemar DESPUÉS de la
    edición del cuadro (así no se achican ni se cortan); si no hay -sinc, el -SUBTITULADO de armar_escena.py (ese no trae
    título). Ojo: en los videos a_camara de antes del 12-nov el -SUBTITULADO ya trae el título viejo quemado.
    Carruseles y variantes que rompieron: su video final, y el gancho nuevo va en una tarjeta encima."""
    o = originales().get(original)
    if not o:
        sys.exit(f'ERROR: no encuentro {original} en plan.json, carruseles.json ni en variantes que rompieron.')
    if o['tipo'] == 'variante':
        return None, None, os.path.join(RAIZ, o['d']['archivo'])
    if o['tipo'] == 'video':
        final = os.path.join(RAIZ, o['d'].get('archivo') or f'videos/video-{original}-FINAL.mp4')
        sinc, ass = final.replace('-FINAL.mp4', '-sinc.mp4'), final.replace('-FINAL.mp4', '-SUBTITULADO.ass')
        if os.path.exists(sinc) and os.path.exists(ass):
            return sinc, ass, final
        sub = final.replace('-FINAL.mp4', '-SUBTITULADO.mp4')
        if os.path.exists(sub) and not os.path.exists(sinc):
            return sub, None, final
        sys.exit(f'ERROR: {original} no tiene video limpio (-sinc.mp4 + -SUBTITULADO.ass); no hago una variante con el título viejo encima.')
    carpeta = os.path.join(RAIZ, 'carruseles', original)
    for n in ('reel-texto-musica.mp4', 'short.mp4', 'reel.mp4'):
        if os.path.exists(os.path.join(carpeta, n)):
            return None, None, os.path.join(carpeta, n)
    sys.exit(f'ERROR: {original} no tiene video (carruseles/{original}/short.mp4).')


def subtitulos_sin_cierre(ass, duracion, salida):
    """Los subtítulos del original sin los que caen en el cierre (cierre_pantalla.py va en esa misma franja)."""
    from cierre_pantalla import SEGUNDOS
    corte = duracion - SEGUNDOS

    def seg(t):
        h, m, s = t.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)

    def ts(t):
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        return f'{int(h)}:{int(m):02d}:{s:05.2f}'
    lineas = []
    for linea in open(ass).read().split('\n'):
        if linea.startswith('Dialogue:'):
            partes = linea.split(',', 9)
            ini, fin = seg(partes[1]), seg(partes[2])
            if ini >= corte - 0.4:
                continue
            partes[2] = ts(min(fin, corte))
            linea = ','.join(partes)
        lineas.append(linea)
    open(salida, 'w').write('\n'.join(lineas))


def medidas(video):
    r = json.loads(correr('ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height:format=duration', '-of', 'json', video))
    return r['streams'][0]['width'], r['streams'][0]['height'], float(r['format']['duration'])


def filtro_edicion(edicion, w, h):
    if edicion == 'zoom':  # acercamiento: el cuadro se siente otro sin cortar la cara
        return f'crop=iw/1.1:ih/1.1,scale={w}:{h},eq=saturation=1.08'
    if edicion == 'fondo':  # el video más chico sobre su propio fondo difuminado
        return (f'split[a][b];[a]scale={w}:{h},boxblur=30:5,eq=brightness=-0.22[bg];'
                f'[b]scale={int(w * 0.86) // 2 * 2}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2')
    if edicion == 'color':
        return 'eq=contrast=1.06:saturation=1.18:gamma=0.97,vignette=PI/5'
    return 'null'  # inicio: el cuadro igual, solo cambia el gancho


def tarjeta_gancho(gancho, w, h, ruta, video, dur):
    """Para carruseles (el gancho es su primera tarjeta): tarjeta OPACA con el gancho nuevo encima de los 2.4 s primeros
    (si se transparenta se lee el gancho viejo debajo). Fondo: un cuadro de en medio del mismo video, difuminado y
    oscuro. Mismo estilo de reel_texto.py (Inter, oro)."""
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
    cuadro = ruta + '.fondo.jpg'
    correr('ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{dur * 0.45:.2f}', '-i', video, '-frames:v', '1', cuadro)
    img = Image.open(cuadro).convert('RGB').resize((w, h)).filter(ImageFilter.GaussianBlur(28))
    img = ImageEnhance.Brightness(img).enhance(0.32).convert('RGBA')
    os.remove(cuadro)
    d = ImageDraw.Draw(img)
    tam = int(w * 0.085)
    f = ImageFont.truetype(os.path.join(FUENTES, 'Inter-Black.otf'), tam)
    renglones = textwrap.wrap(sin_emoji(gancho).upper(), width=16)[:5]
    alto = len(renglones) * int(tam * 1.18)
    y = (h - alto) // 2
    for r in renglones:
        ancho = d.textlength(r, font=f)
        d.text(((w - ancho) / 2, y), r, font=f, fill=(245, 197, 66))
        y += int(tam * 1.18)
    chica = ImageFont.truetype(os.path.join(FUENTES, 'Inter-SemiBold.otf'), int(w * 0.028))
    nota = 'Victoria · personaje creado con IA'
    d.text(((w - d.textlength(nota, font=chica)) / 2, h - int(h * 0.08)), nota, font=chica, fill=(244, 239, 230, 170))
    img.save(ruta)


def burbuja_respuesta(texto, autor, w, h, ruta):
    """Sticker de "respuesta a un comentario" con un comentario REAL (nunca inventado)."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    chica = ImageFont.truetype(os.path.join(FUENTES, 'Inter-SemiBold.otf'), int(w * 0.03))
    f = ImageFont.truetype(os.path.join(FUENTES, 'Inter-Bold.otf'), int(w * 0.04))
    renglones = textwrap.wrap(sin_emoji(texto), width=30)[:3]
    caja_w, caja_h = int(w * 0.78), int(w * 0.07) + len(renglones) * int(w * 0.052)
    x, y = (w - caja_w) // 2, int(h * 0.20)
    d.rounded_rectangle((x, y, x + caja_w, y + caja_h), radius=int(w * 0.03), fill=(255, 255, 255, 245))
    d.text((x + 24, y + 14), f'Respuesta a {autor}', font=chica, fill=(110, 110, 110))
    yy = y + int(w * 0.06)
    for r in renglones:
        d.text((x + 24, yy), r, font=f, fill=(17, 17, 17))
        yy += int(w * 0.052)
    img.save(ruta)


def siguiente_edicion(original):
    usadas = [x['edicion'] for x in registro() if x['original'] == original]
    return min(EDICIONES, key=lambda e: (usadas.count(e), EDICIONES.index(e)))


def textos(original, gancho, carpeta):
    """titulo.txt, descripcion_youtube.txt, tags_youtube.txt, texto_tiktok.txt con el gancho nuevo arriba."""
    o = originales()[original]
    d = o['d']
    if o['tipo'] == 'video':
        tmp = tempfile.mkdtemp()
        correr(sys.executable, os.path.join(RAIZ, 'scripts', 'seo.py'), original, tmp)
        base = {n: open(os.path.join(tmp, n)).read().strip() for n in os.listdir(tmp) if n.endswith('.txt')}
        shutil.rmtree(tmp)
        clave = (d.get('seo') or {}).get('palabra_clave', '')
    elif o['tipo'] == 'carrusel':
        cc = os.path.join(RAIZ, 'carruseles', original)
        base = {n: open(os.path.join(cc, n)).read().strip() for n in ('descripcion_youtube.txt', 'tags_youtube.txt')
                if os.path.exists(os.path.join(cc, n))}
        etiquetas = []
        for t in list((d.get('seo') or {}).get('hashtags') or []) + ['#victoriatheceo', '#mexico', '#finanzas', '#educacionfinanciera', '#dinero']:
            if t.lower() not in [e.lower() for e in etiquetas]:
                etiquetas.append(t)
        base['texto_tiktok.txt'] = f"{d.get('texto_post', '')}\n\n{' '.join(etiquetas[:8])}\n\nPersonaje y video creados con IA."
        clave = (d.get('seo') or {}).get('palabra_clave', '')
    else:  # variante que rompió: sus propios textos
        cc = os.path.join(RAIZ, os.path.dirname(d['archivo']))
        base = {n: open(os.path.join(cc, n)).read().strip() for n in os.listdir(cc) if n.endswith('.txt')}
        clave = d.get('palabra_clave', '')
    limpio = sin_emoji(gancho)
    titulo = limpio if not clave or clave.lower() in limpio.lower() else f'{limpio} | {clave}'
    salida = {
        'titulo.txt': titulo[:95],
        'descripcion_youtube.txt': f"{limpio}\n{base.get('descripcion_youtube.txt', '')}".strip(),
        'tags_youtube.txt': base.get('tags_youtube.txt', ''),
        # La primera línea distinta: Publer no la toma por repetida y medir la encuentra por esa línea
        'texto_tiktok.txt': f"{gancho}\n\n{base.get('texto_tiktok.txt', '')}".strip(),
    }
    for n, t in salida.items():
        open(os.path.join(carpeta, n), 'w').write(t + '\n')
    return titulo, clave


def hacer(original, gancho, edicion=None, comentario=None, autor=None):
    limpio, ass, final = fuente(original)
    filas = registro()
    if any(sin_emoji(x['gancho']).lower() == sin_emoji(gancho).lower() for x in filas if x['original'] == original):
        sys.exit('ERROR: ese gancho ya se usó en otra variante de este original; escribe otro.')
    n = sum(1 for x in filas if x['original'] == original) + 1
    vid = f'{original}-v{n}'
    edicion = edicion or siguiente_edicion(original)
    carpeta = os.path.join(CARPETA, vid)
    os.makedirs(carpeta, exist_ok=True)
    w, h, dur = medidas(limpio or final)
    paso = os.path.join(carpeta, '.paso.mp4')
    entradas, filtro = ['-i', limpio or final], f'[0:v]{filtro_edicion(edicion, w, h)}[v0]'
    ultimo = 'v0'
    if ass:  # subtítulos encima de la edición, a tamaño normal
        subs = os.path.join(carpeta, '.subs.ass')
        subtitulos_sin_cierre(ass, dur, subs)
        filtro += f';[v0]ass={subs}[vs]'
        ultimo = 'vs'
    if not limpio:  # carrusel o variante: el gancho nuevo va en una tarjeta encima de los primeros 2.4 s
        png = os.path.join(carpeta, '.gancho.png')
        tarjeta_gancho(gancho, w, h, png, limpio or final, dur)
        entradas += ['-i', png]
        filtro += f";[{ultimo}][1:v]overlay=0:0:enable='lt(t,2.4)'[v1]"
        ultimo = 'v1'
    if comentario and autor:
        png = os.path.join(carpeta, '.respuesta.png')
        burbuja_respuesta(comentario, autor, w, h, png)
        entradas += ['-i', png]
        k = len(entradas) // 2 - 1
        filtro += f";[{ultimo}][{k}:v]overlay=0:0[v9]"
        ultimo = 'v9'
    correr('ffmpeg', '-loglevel', 'error', '-y', *entradas, '-filter_complex', filtro, '-map', f'[{ultimo}]',
           '-an', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', paso)
    if limpio:  # videos del plan: título nuevo y cierre con los mismos scripts de siempre
        titulado = os.path.join(carpeta, '.titulado.mp4')
        correr(sys.executable, os.path.join(RAIZ, 'scripts', 'titulo_pantalla.py'), paso, gancho, titulado)
        os.replace(titulado, paso)
        cerrado = os.path.join(carpeta, '.cierre.mp4')
        correr(sys.executable, os.path.join(RAIZ, 'scripts', 'cierre_pantalla.py'), paso, original, cerrado)
        os.replace(cerrado, paso)
    salida = os.path.join(carpeta, 'video.mp4')
    # El audio sale del video final del original (voz + música tal cual): la sincronía no se toca
    correr('ffmpeg', '-loglevel', 'error', '-y', '-i', paso, '-i', final, '-map', '0:v:0', '-map', '1:a:0?',
           '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', salida)
    for f in glob.glob(os.path.join(carpeta, '.*')):
        os.remove(f)
    correr('ffmpeg', '-loglevel', 'error', '-y', '-ss', '0.6', '-i', salida, '-frames:v', '1', '-q:v', '3',
           os.path.join(carpeta, 'portada.jpg'))
    titulo, clave = textos(original, gancho, carpeta)
    fila = {'id': vid, 'original': original, 'clon_de': original, 'gancho': gancho, 'edicion': edicion,
            'respuesta_a': {'autor': autor, 'texto': comentario} if comentario and autor else None,
            'archivo': os.path.relpath(salida, RAIZ), 'titulo': titulo, 'palabra_clave': clave,
            'creada_utc': AHORA.strftime('%Y-%m-%dT%H:%M:%SZ'), 'estado': 'lista', 'redes': {}, 'medidas': {}}
    filas.append(fila)
    guardar(filas)
    print(f'OK {vid} ({edicion}): {fila["archivo"]} — «{gancho}». Revisa y publica con: variantes.py publicar {vid} <cuando_utc>')
    return fila


# ---------- publicar ----------

def publicar(vid, cuando, redes=('tt', 'yt')):
    filas = registro()
    x = next((f for f in filas if f['id'] == vid), None)
    if not x:
        sys.exit(f'ERROR: no existe la variante {vid}.')
    carpeta = os.path.join(RAIZ, os.path.dirname(x['archivo']))
    video = os.path.join(RAIZ, x['archivo'])
    c = conf()
    hechas = []
    x.setdefault('plan', {}).update({r: cuando for r in redes if r not in x['redes']})
    if 'tt' in redes and 'tt' not in x['redes']:
        salida = correr(sys.executable, os.path.join(RAIZ, 'scripts', 'publer.py'), 'publicar', video,
                        os.path.join(carpeta, 'texto_tiktok.txt'), cuando, x['titulo'][:90], '--solo-tiktok')
        if 'OK tiktok' in salida or 'OMITIDO' in salida or 'Ya estaba' in salida:
            x['redes']['tt'] = {'publica_utc': cuando, 'via': 'publer'}
            hechas.append('TikTok')
        print(salida.strip()[-300:])
    if 'yt' in redes and 'yt' not in x['redes']:
        r = subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'youtube.py'), 'subir', video, x['titulo'],
                            os.path.join(carpeta, 'descripcion_youtube.txt'), cuando, '--tags',
                            os.path.join(carpeta, 'tags_youtube.txt'), '--miniatura', os.path.join(carpeta, 'portada.jpg')],
                           capture_output=True, text=True)
        texto = (r.stdout + r.stderr).strip()
        print(texto[-400:])
        enlace = next((p for p in texto.split() if 'youtube.com/shorts/' in p), None)
        if enlace:
            x['redes']['yt'] = {'publica_utc': cuando, 'enlace': enlace, 'video_id': enlace.rstrip('/').split('/')[-1]}
            hechas.append('YouTube')
        elif 'CUOTA_RESERVADA' in texto:
            print(f'YouTube sin cuota hoy: queda en plan y "variantes.py pendientes" lo sube mañana.')
    if c.get('ig_trial') and 'ig' not in x['redes']:
        try:
            x['redes']['ig'] = trial_reel(x, video)
            hechas.append('Instagram (Trial Reel)')
        except SystemExit as e:
            print('Instagram Trial Reel no salió:', str(e)[:300])
    if x['redes']:
        x['estado'] = 'programada'
    guardar(filas)
    print(f'{vid}: {", ".join(hechas) or "nada nuevo"}')


def trial_reel(x, video, solo_probar=False):
    """Reel de prueba de Instagram: solo a no seguidores; si le va bien Instagram lo pasa al perfil (SS_PERFORMANCE)."""
    import time
    import ig_reel_musica as ig
    url = ig.subir_medio(video, f"{x['id']}-trial-{int(time.time())}.mp4")
    texto = open(os.path.join(RAIZ, os.path.dirname(x['archivo']), 'texto_tiktok.txt')).read().strip()
    datos = {'media_type': 'REELS', 'video_url': url, 'caption': texto[:2200],
             'trial_params': json.dumps({'graduation_strategy': 'SS_PERFORMANCE'})}
    contenedor = ig.graph('POST', f'{ig.IG}/media', datos)['id']  # aquí es donde Meta dice "no alcanza el mínimo"
    if solo_probar:
        return {'contenedor': contenedor}
    for _ in range(60):
        estado = ig.graph('GET', f'{contenedor}?fields=status_code,status')
        if estado.get('status_code') == 'FINISHED':
            break
        if estado.get('status_code') in ('ERROR', 'EXPIRED'):
            sys.exit(f"Instagram no aceptó el video: {estado.get('status')}")
        time.sleep(5)
    media = ig.graph('POST', f'{ig.IG}/media_publish', {'creation_id': contenedor})['id']
    return {'publica_utc': AHORA.strftime('%Y-%m-%dT%H:%M:%SZ'), 'ig_media_id': media, 'trial': True}


def probar():
    """¿Ya hay Trial Reels? Arma un contenedor de prueba (no se publica; Meta lo borra solo en 24 h)."""
    import ig_reel_musica as ig
    c = conf()
    seguidores = ig.graph('GET', f'{ig.IG}?fields=followers_count').get('followers_count', 0)
    lunes = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-6))).weekday() == 0
    if seguidores < c['min_seguidores_ig_trial'] and not lunes and '--forzar' not in sys.argv:
        print(f'Trial Reels: {seguidores} seguidores en Instagram; se prueba al llegar a {c["min_seguidores_ig_trial"]} (o el lunes).')
        return
    x = next((f for f in reversed(registro())), None)
    if not x:
        print('Trial Reels: no hay variante con qué probar todavía.')
        return
    try:
        trial_reel(x, os.path.join(RAIZ, x['archivo']), solo_probar=True)
    except SystemExit as e:
        print(f'Trial Reels: todavía NO ({seguidores} seguidores). Meta: {str(e)[:220]}')
        return
    ruta = os.path.join(RAIZ, 'contenido', 'config.json')
    config = json.load(open(ruta))
    config.setdefault('variantes', {})['ig_trial'] = True
    config['variantes']['_ig_trial'] = f'Meta aceptó Trial Reels el {AHORA.date()} con {seguidores} seguidores (variantes.py probar).'
    with open(ruta, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'Trial Reels: ¡SÍ! ({seguidores} seguidores). Prendido config.variantes.ig_trial: las variantes salen también en Instagram.')


def pendientes():
    """Lo programado que falta subir (YouTube se sube hasta 48 h antes por la cuota; TikTok va por Publer)."""
    limite = AHORA + datetime.timedelta(hours=48)
    for x in registro():
        faltan = {r: t for r, t in (x.get('plan') or {}).items() if r not in x['redes']
                  and datetime.datetime.fromisoformat(t.replace('Z', '+00:00')) <= limite}
        for cuando in sorted(set(faltan.values())):
            redes = tuple(r for r, t in faltan.items() if t == cuando)
            # si la hora ya pasó, sale en cuanto se pueda (YouTube publica de inmediato con menos de 15 min)
            if datetime.datetime.fromisoformat(cuando.replace('Z', '+00:00')) < AHORA:
                cuando = (AHORA + datetime.timedelta(minutes=20)).strftime('%Y-%m-%dT%H:%M:%SZ')
            print(f"pendiente {x['id']} → {', '.join(redes)} {cuando}")
            publicar(x['id'], cuando, redes)


# ---------- medir ----------

def medir():
    c = conf()
    filas = registro()
    vivas = [x for x in filas if x.get('redes')]
    if not vivas:
        print('medir variantes: ninguna publicada todavía')
        return
    vistas = {}
    ids = {x['redes']['yt']['video_id']: x['id'] for x in vivas if (x['redes'].get('yt') or {}).get('video_id')}
    if ids:
        import youtube
        try:
            _, cuerpo = youtube._http('GET', f"{youtube.API}/videos?part=statistics&id={','.join(ids)}",
                                      headers={'Authorization': f'Bearer {youtube.token()}'})
            for it in json.loads(cuerpo).get('items') or []:
                vistas.setdefault(ids[it['id']], {})['yt'] = int(it['statistics'].get('viewCount', 0))
        except SystemExit as e:
            print('AVISO YouTube:', str(e)[:200])
    if any('tt' in x['redes'] for x in vivas):
        try:
            import publer
            from aprender import valor_publer
            ws = publer.workspace_id()
            cuentas = publer.CONFIG.get('cuentas_publer', {})
            por_linea = {open(os.path.join(RAIZ, os.path.dirname(x['archivo']), 'texto_tiktok.txt')).read().split('\n')[0].strip(): x['id']
                         for x in vivas if 'tt' in x['redes']}
            hoy = datetime.date.today()
            for pagina in range(10):
                r = publer._pedir('GET', f'/analytics/post_insights?from={(hoy - datetime.timedelta(days=30)).isoformat()}'
                                         f'&to={hoy.isoformat()}&page={pagina}', ws)
                lote = r.get('posts') or []
                for p in lote:
                    if cuentas.get(p.get('account_id')) != 'tiktok':
                        continue
                    vid = por_linea.get((p.get('text') or '').split('\n')[0].strip())
                    if vid:
                        a = p.get('analytics') or {}
                        vistas.setdefault(vid, {})['tt'] = valor_publer(a.get('video_views')) or valor_publer(a.get('reach'))
                if len(lote) < 10:
                    break
        except SystemExit as e:
            print('AVISO Publer:', str(e)[:200])
    pubs = {p['id']: p['por_red'] for p in vistas_publicadas()}
    for x in vivas:
        for red, v in (vistas.get(x['id']) or {}).items():
            sale = datetime.datetime.fromisoformat(x['redes'][red]['publica_utc'].replace('Z', '+00:00'))
            dias = (AHORA - sale).total_seconds() / 86400
            if dias < 0:
                continue
            x['redes'][red]['vistas'] = v
            for cp in c['checkpoints_dias']:
                if dias >= cp:
                    x['medidas'].setdefault(red, {}).setdefault(f'd{cp}', v)  # la primera foto pasado el día cuenta
            base = (pubs.get(x['original']) or {}).get(red) or 0
            if not x.get('rompio') and (v >= c['rompe_vistas'] or (base and v >= c['rompe_fraccion_original'] * base and v >= c['minimo_vistas'])):
                x['rompio'] = {'red': red, 'vistas': v, 'original': base, 'fecha_utc': AHORA.strftime('%Y-%m-%dT%H:%M:%SZ')}
                print(f"ROMPIÓ {x['id']} en {red}: {v:,} vistas (original {base:,}) → recibe sus propias variantes")
    guardar(filas)
    ver()


def ver():
    filas = registro()
    if not filas:
        print('Sin variantes todavía.')
        return
    for x in filas:
        redes = ' · '.join(f"{r} {d.get('vistas', '-')}" for r, d in x.get('redes', {}).items()) or 'sin publicar'
        marca = ' ★ ROMPIÓ' if x.get('rompio') else ''
        print(f"{x['id']:10s} {x['edicion']:7s} {x['estado']:10s} {redes}{marca} — {x['gancho'][:60]}")


def main():
    a = [x for x in sys.argv[1:]]
    if not a:
        sys.exit(__doc__)
    def opcion(nombre):
        return a[a.index(nombre) + 1] if nombre in a else None
    if a[0] == 'candidatos':
        for s in candidatos():
            print(f"{s['id']:6s} {s['red']} {s['vistas']:>6,} vistas (mediana {s['mediana']}) · {s['hechas']} variantes — {s['titulo'][:55]}")
    elif a[0] == 'hacer' and len(a) >= 3:
        hacer(a[1], a[2], opcion('--edicion'), opcion('--comentario'), opcion('--autor'))
    elif a[0] == 'publicar' and len(a) >= 3:
        redes = tuple((opcion('--redes') or 'tt,yt').split(','))
        if '--solo-plan' in a:  # anota la hora sin subir nada (lo sube "pendientes" cuando falten 48 h o menos)
            filas = registro()
            x = next(f for f in filas if f['id'] == a[1])
            x.setdefault('plan', {}).update({r: a[2] for r in redes})
            guardar(filas)
            print(f"{a[1]} en plan: {', '.join(redes)} {a[2]}")
        else:
            publicar(a[1], a[2], redes)
    elif a[0] == 'pendientes':
        pendientes()
    elif a[0] == 'medir':
        medir()
    elif a[0] == 'probar':
        probar()
    elif a[0] == 'ver':
        ver()
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
