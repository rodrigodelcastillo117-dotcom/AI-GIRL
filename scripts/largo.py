"""Video largo de YouTube (horizontal, 6-8 min) a partir de un guion por segmentos (Rodrigo, 12-nov-2026: "haz videos
largos de aguinaldo").

Uso:
  $VOZ_PYTHON scripts/largo.py voces <id>            1) voz de cada segmento (voz_victoria.py: la transcribe y la repite si no sale)
  python scripts/largo.py victoria <id>              2) segmentos a cámara con Replicate (video_replicate.py, 1920x1080) + qa
  python scripts/largo.py laminas <id>               3) dibuja las láminas (1920x1080, negro y dorado)
  python scripts/largo.py armar <id>                 4) une todo, capítulos, miniatura y textos para YouTube
  python scripts/largo.py todo <id>                  2, 3 y 4 seguidos (las voces van aparte: necesitan VOZ_PYTHON)

El guion vive en contenido/largos.json → [{"id", "seo", "miniatura", "foto_horizontal", "segmentos": [...]}]:
  {"tipo": "victoria", "capitulo": "..."|null, "voz": "..."}                 Victoria a cámara (gancho, transiciones, cierre)
  {"tipo": "lamina", "capitulo": ..., "titulo", "dato_grande", "puntos": [], "fuente", "voz"}   lámina narrada con su voz
  {"tipo": "grafica", ..., "barras": [{"etiqueta", "valor", "texto_valor"}], "nota", "fuente", "voz"}   barras horizontales
  {"tipo": "pasos", ..., "pasos": [{"texto", "resultado"}], "fuente", "voz"}                    la cuenta paso a paso
Rodrigo (12-nov-2026): "que sea mix de ella hablando con láminas, gráficas, fácil de entender".
Por qué la mezcla: Victoria a cámara todo el video en Replicate cuesta ~$0.045 USD por segundo (8 min ≈ $22); con ~1 min a
cámara y el resto en láminas narradas, cada largo cuesta ~$3-4 USD. Archivos en videos/largos/<id>/ (no van al repo,
salvo el final y la miniatura).
"""
import json
import os
import subprocess
import sys
import textwrap

try:  # el paso "voces" corre con VOZ_PYTHON, que no trae PIL: solo los pasos que dibujan la necesitan
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FUENTES = '/usr/share/fonts/opentype/inter/'
NEGRO, ORO, BLANCO, GRIS = (11, 11, 13), (245, 197, 66), (245, 242, 235), (150, 148, 140)
ANCHO, ALTO = 1920, 1080
PAUSA_S = 0.35  # aire después de cada segmento


def fuente(peso, tam):
    return ImageFont.truetype(os.path.join(FUENTES, f'Inter-{peso}.otf'), tam)


def cargar(vid):
    largos = json.load(open(os.path.join(RAIZ, 'contenido', 'largos.json')))
    largo = next((l for l in largos if l['id'] == vid), None)
    if not largo:
        sys.exit(f'No existe {vid} en contenido/largos.json')
    carpeta = os.path.join(RAIZ, 'videos', 'largos', vid)
    os.makedirs(carpeta, exist_ok=True)
    return largo, carpeta


def duracion(ruta):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ruta],
                                capture_output=True, text=True, check=True).stdout.strip())


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def voces(vid):
    largo, carpeta = cargar(vid)
    lista = [{'texto': s['voz'], 'salida': os.path.join(carpeta, f'voz-{i:02d}.mp3')}
             for i, s in enumerate(largo['segmentos']) if not os.path.exists(os.path.join(carpeta, f'voz-{i:02d}.mp3'))]
    if lista:
        ruta = os.path.join(carpeta, 'voces.json')
        json.dump(lista, open(ruta, 'w'), ensure_ascii=False)
        subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'voz_victoria.py'), ruta], check=True)
    total = sum(duracion(os.path.join(carpeta, f'voz-{i:02d}.mp3')) for i in range(len(largo['segmentos'])))
    print(f'ok voces {vid}: {len(largo["segmentos"])} segmentos, {total / 60:.1f} min')


def victoria(vid):
    import video_replicate
    largo, carpeta = cargar(vid)
    foto = os.path.join(RAIZ, largo['foto_horizontal'])
    gasto = 0
    for i, s in enumerate(largo['segmentos']):
        if s['tipo'] != 'victoria':
            continue
        salida = os.path.join(carpeta, f'seg-{i:02d}.mp4')
        if os.path.exists(salida):
            continue
        r = video_replicate.generar(foto, os.path.join(carpeta, f'voz-{i:02d}.mp3'), salida,
                                    largo.get('movimiento', video_replicate.MOVIMIENTO), tamano=f'{ANCHO}:{ALTO}')
        gasto += r['costo_usd']
        # Labios: transcribir.py corre con VOZ_PYTHON; qa_labios con el python del sistema.
        palabras = salida.replace('.mp4', '-palabras.json')
        voz_py = os.environ.get('VOZ_PYTHON', '/tmp/voz/bin/python')
        subprocess.run([voz_py, os.path.join(RAIZ, 'scripts', 'transcribir.py'), salida, palabras], check=True,
                       capture_output=True)
        qa = subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'qa_labios.py'), salida, palabras],
                            capture_output=True, text=True, cwd=os.path.join(RAIZ, 'scripts'))
        print(f'seg {i:02d}:', (qa.stdout.strip().splitlines() or ['?'])[-1])
        if qa.returncode != 0:
            os.rename(salida, salida.replace('.mp4', '-FALLA.mp4'))
            print(f'  seg {i:02d} no pasó labios: se vuelve a generar en la siguiente corrida (máximo 2 intentos)')
    print(f'ok victoria {vid}: ~${gasto:.2f} USD en Replicate')


def _foto_circular(ruta, tam, centro=(0.635, 0.21), lado_frac=0.36):
    """Círculo con la cara de Victoria. centro = (x, y) de la cara en fracción de la foto; largos.json → "cara" lo cambia."""
    im = Image.open(ruta).convert('RGB')
    w, h = im.size
    lado = int(h * lado_frac)
    x, y = int(w * centro[0] - lado / 2), int(h * centro[1] - lado / 2)
    x, y = max(0, min(w - lado, x)), max(0, min(h - lado, y))
    im = im.crop((x, y, x + lado, y + lado)).resize((tam, tam), Image.LANCZOS)
    mascara = Image.new('L', (tam, tam), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, tam, tam), fill=255)
    return im, mascara


def lamina(s, capitulo, ruta, cara):
    im = Image.new('RGB', (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(im)
    for y in range(ALTO):  # degradado leve hacia el centro
        tono = int(6 * (1 - abs(y - ALTO / 2) / (ALTO / 2)))
        d.line([(0, y), (ANCHO, y)], fill=(NEGRO[0] + tono, NEGRO[1] + tono, NEGRO[2] + tono + 2))
    x0, y = 150, 120
    if capitulo:
        d.text((x0, y), capitulo.upper(), font=fuente('SemiBold', 30), fill=ORO)
        d.line([(x0, y + 50), (x0 + 90, y + 50)], fill=ORO, width=4)
    y += 90
    for renglon in textwrap.wrap(s.get('titulo') or '', 30)[:2]:
        d.text((x0, y), renglon, font=fuente('Black', 74), fill=BLANCO)
        y += 92
    if s.get('dato_grande'):
        y += 20
        tam = 150 if len(s['dato_grande']) <= 12 else 100 if len(s['dato_grande']) <= 20 else 72
        d.text((x0, y), s['dato_grande'], font=fuente('Black', tam), fill=ORO)
        y += int(tam * 1.25)
    y += 25
    for p in s.get('puntos') or []:
        renglones = textwrap.wrap(p, 52)[:2]
        d.ellipse((x0, y + 18, x0 + 14, y + 32), fill=ORO)
        for r in renglones:
            d.text((x0 + 40, y), r, font=fuente('Medium', 42), fill=BLANCO)
            y += 56
        y += 18
        if y > ALTO - 170:
            break
    if s.get('fuente'):
        d.text((x0, ALTO - 110), 'Fuente: ' + s['fuente'], font=fuente('Regular', 26), fill=GRIS)
    # Victoria en un círculo, arriba a la derecha, y la firma abajo a la derecha.
    foto, mascara = cara
    borde = Image.new('RGB', (foto.width + 12, foto.height + 12), ORO)
    m2 = Image.new('L', borde.size, 0)
    ImageDraw.Draw(m2).ellipse((0, 0, borde.width, borde.height), fill=255)
    im.paste(borde, (ANCHO - 150 - borde.width, 110), m2)
    im.paste(foto, (ANCHO - 150 - borde.width + 6, 116), mascara)
    d.text((ANCHO - 150, ALTO - 110), '@victoriatheceo · personaje creado con IA', font=fuente('Regular', 26), fill=GRIS,
           anchor='ra')
    im.save(ruta, quality=95)


def _base(capitulo, s, cara):
    """Fondo, capítulo, título, fuente, Victoria en círculo y firma: lo común a lámina, gráfica y pasos."""
    im = Image.new('RGB', (ANCHO, ALTO), NEGRO)
    d = ImageDraw.Draw(im)
    for y in range(ALTO):
        tono = int(6 * (1 - abs(y - ALTO / 2) / (ALTO / 2)))
        d.line([(0, y), (ANCHO, y)], fill=(NEGRO[0] + tono, NEGRO[1] + tono, NEGRO[2] + tono + 2))
    x0, y = 150, 120
    if capitulo:
        d.text((x0, y), capitulo.upper(), font=fuente('SemiBold', 30), fill=ORO)
        d.line([(x0, y + 50), (x0 + 90, y + 50)], fill=ORO, width=4)
    y += 90
    for renglon in textwrap.wrap(s.get('titulo') or '', 34)[:2]:
        d.text((x0, y), renglon, font=fuente('Black', 66), fill=BLANCO)
        y += 82
    if s.get('fuente'):
        d.text((x0, ALTO - 110), 'Fuente: ' + s['fuente'], font=fuente('Regular', 26), fill=GRIS)
    foto, mascara = cara
    borde = Image.new('RGB', (foto.width + 12, foto.height + 12), ORO)
    m2 = Image.new('L', borde.size, 0)
    ImageDraw.Draw(m2).ellipse((0, 0, borde.width, borde.height), fill=255)
    im.paste(borde, (ANCHO - 150 - borde.width, 110), m2)
    im.paste(foto, (ANCHO - 150 - borde.width + 6, 116), mascara)
    d.text((ANCHO - 150, ALTO - 110), '@victoriatheceo · personaje creado con IA', font=fuente('Regular', 26), fill=GRIS,
           anchor='ra')
    return im, d, y


def grafica(s, capitulo, ruta, cara):
    """Barras horizontales de una sola serie (magnitud): una tonalidad (dorado), extremo redondeado anclado a la base,
    2 px de aire entre barras, cifra directa al final de cada barra en tinta de texto (no en el color de la barra),
    eje discreto. Guía: skill dataviz (una serie = sin leyenda; el título la nombra)."""
    im, d, y = _base(capitulo, s, cara)
    barras = s.get('barras') or []
    x_et, x_bar, x_max = 150, 760, ANCHO - 330
    alto_barra = min(105, int((ALTO - 300 - y) / max(1, len(barras))) - 30)
    maximo = max((b['valor'] for b in barras), default=1) or 1
    y = max(y + 60, 430)
    d.line([(x_bar, y - 20), (x_bar, y + len(barras) * (alto_barra + 26))], fill=(60, 60, 64), width=2)  # base
    for b in barras:
        largo_px = max(8, int((x_max - x_bar) * b['valor'] / maximo))
        d.rounded_rectangle((x_bar, y, x_bar + largo_px, y + alto_barra), radius=6, fill=ORO,
                            corners=(False, True, True, False))
        d.rectangle((x_bar, y, x_bar + 6, y + alto_barra), fill=ORO)
        etiqueta = textwrap.wrap(b['etiqueta'], 30)[:2]
        ye = y + alto_barra / 2 - len(etiqueta) * 22
        for r in etiqueta:
            d.text((x_et, ye), r, font=fuente('Medium', 40), fill=BLANCO)
            ye += 44
        valor = b.get('texto_valor') or f"{b['valor']:,}"
        f = fuente('Bold', 48)
        if x_bar + largo_px + 20 + d.textlength(valor, font=f) < ANCHO - 120:
            d.text((x_bar + largo_px + 20, y + alto_barra / 2), valor, font=f, fill=BLANCO, anchor='lm')
        else:
            d.text((x_bar + largo_px - 20, y + alto_barra / 2), valor, font=f, fill=NEGRO, anchor='rm')
        y += alto_barra + 30
    if s.get('nota'):
        d.text((x_et, y + 20), s['nota'], font=fuente('Medium', 34), fill=GRIS)
    im.save(ruta, quality=95)


def pasos(s, capitulo, ruta, cara):
    """La cuenta paso a paso: cajas numeradas de izquierda a derecha con flechas, y el resultado de cada paso abajo."""
    im, d, y = _base(capitulo, s, cara)
    lista = (s.get('pasos') or [])[:4]
    n = max(1, len(lista))
    margen, hueco = 150, 70
    ancho_caja = int((ANCHO - 2 * margen - (n - 1) * hueco) / n)
    y0, alto = max(y + 70, 440), 430
    for i, p in enumerate(lista):
        x = margen + i * (ancho_caja + hueco)
        d.rounded_rectangle((x, y0, x + ancho_caja, y0 + alto), radius=24, outline=(70, 70, 76), width=3,
                            fill=(20, 20, 24))
        d.ellipse((x + 30, y0 + 30, x + 100, y0 + 100), fill=ORO)
        d.text((x + 65, y0 + 65), str(i + 1), font=fuente('Black', 44), fill=NEGRO, anchor='mm')
        yy = y0 + 130
        ancho_txt = max(12, int(ancho_caja / 21))
        for r in textwrap.wrap(p['texto'], ancho_txt)[:4]:
            d.text((x + 30, yy), r, font=fuente('Medium', 36), fill=BLANCO)
            yy += 46
        if p.get('resultado'):
            f = fuente('Black', 46 if len(p['resultado']) <= 18 else 36)
            for r in textwrap.wrap(p['resultado'], max(10, int(ancho_caja / 25)))[:2]:
                d.text((x + 30, y0 + alto - 120 + (0 if len(p['resultado']) <= 18 else -10)), r, font=f, fill=ORO)
                break
        if i < n - 1:
            xa = x + ancho_caja + 12
            d.polygon([(xa, y0 + alto / 2 - 18), (xa + hueco - 24, y0 + alto / 2), (xa, y0 + alto / 2 + 18)], fill=ORO)
    im.save(ruta, quality=95)


DIBUJOS = {'lamina': None, 'grafica': grafica, 'pasos': pasos}


def laminas(vid):
    largo, carpeta = cargar(vid)
    cara = _foto_circular(os.path.join(RAIZ, largo['foto_horizontal']), 260, *largo.get('cara', []))
    capitulo = None
    hechas = 0
    for i, s in enumerate(largo['segmentos']):
        capitulo = s.get('capitulo') or capitulo
        if s['tipo'] not in DIBUJOS:
            continue
        png = os.path.join(carpeta, f'lamina-{i:02d}.png')
        (DIBUJOS[s['tipo']] or lamina)(s, capitulo, png, cara)
        audio = os.path.join(carpeta, f'voz-{i:02d}.mp3')
        seg = duracion(audio) + PAUSA_S
        # Acercamiento muy lento (1.00 → 1.04) para que la lámina no se vea congelada.
        ffmpeg('-loop', '1', '-i', png, '-i', audio, '-filter_complex',
               f"[0:v]scale=2304:1296,zoompan=z='1+0.04*on/({seg:.2f}*30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
               f":d=1:s={ANCHO}x{ALTO}:fps=30,fade=t=in:st=0:d=0.25,format=yuv420p[v];[1:a]apad[a]",
               '-map', '[v]', '-map', '[a]', '-t', f'{seg:.3f}', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
               '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k', os.path.join(carpeta, f'seg-{i:02d}.mp4'))
        hechas += 1
    print(f'ok laminas {vid}: {hechas}')


def _ts(t):
    m, s = divmod(int(t), 60)
    return f'{m}:{s:02d}'


def armar(vid):
    largo, carpeta = cargar(vid)
    lista, capitulos, t = [], [], 0.0
    for i, s in enumerate(largo['segmentos']):
        seg = os.path.join(carpeta, f'seg-{i:02d}.mp4')
        if not os.path.exists(seg):
            sys.exit(f'Falta {seg} (¿no pasó labios? corre "victoria" otra vez)')
        norm = os.path.join(carpeta, f'norm-{i:02d}.mp4')
        pausa = PAUSA_S if s['tipo'] == 'victoria' else 0
        ffmpeg('-i', seg, '-vf', f'scale={ANCHO}:{ALTO},fps=30,format=yuv420p,tpad=stop_mode=clone:stop_duration={pausa}',
               '-af', f'aresample=44100,apad=pad_dur={pausa}', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
               '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k', norm)
        if s.get('capitulo'):
            capitulos.append((t, s['capitulo']))
        t += duracion(norm)
        lista.append(norm)
    orden = os.path.join(carpeta, 'orden.txt')
    open(orden, 'w').write(''.join(f"file '{x}'\n" for x in lista))
    final = os.path.join(RAIZ, 'videos', 'largos', f'{vid}-horizontal.mp4')
    ffmpeg('-f', 'concat', '-safe', '0', '-i', orden, '-c', 'copy', '-movflags', '+faststart', final)
    if not capitulos or capitulos[0][0] > 0:
        capitulos.insert(0, (0, 'Intro'))
    caps = '\n'.join(f'{_ts(a)} {b}' for a, b in capitulos)
    seo = largo['seo']
    # Las 2 primeras líneas son lo único que se ve sin abrir la descripción: ahí va el gancho y la calculadora
    # (seo.descripcion ya empieza con ellos); luego capítulos, fuentes y, al final, los hashtags (los 3 primeros salen
    # arriba del título).
    descripcion = seo['descripcion'].strip().replace('\n\n', '\n\nCapítulos:\n' + caps + '\n\n', 1) + (
        '\n\nVictoria es un personaje creado con inteligencia artificial. Información general, no asesoría financiera ni legal.'
        '\n\n' + ' '.join(seo.get('hashtags', [])))
    open(os.path.join(carpeta, 'titulo.txt'), 'w').write(seo['titulo'])
    open(os.path.join(carpeta, 'descripcion_youtube.txt'), 'w').write(descripcion)
    open(os.path.join(carpeta, 'tags_youtube.txt'), 'w').write(','.join(seo.get('tags', [])))
    miniatura(largo, os.path.join(RAIZ, 'videos', 'largos', f'{vid}-miniatura.jpg'))
    print(f'ok {final} | {duracion(final) / 60:.1f} min | {len(capitulos)} capítulos\n{caps}')


def miniatura(largo, ruta):
    """Miniatura 1280x720 hecha para el clic (Rodrigo, 12-nov-2026: "una miniatura mega super TOP"):
    Victoria con emoción fuerte a la derecha (foto propia, largos.json → miniatura.foto, con la mitad izquierda vacía),
    a la izquierda una línea chica arriba, una cifra o frase GIGANTE y una banda de color con 2-3 palabras. Máximo ~6
    palabras en total; contorno negro grueso para que se lea en celular; foto con más contraste y una viñeta."""
    from PIL import ImageEnhance
    m = largo.get('miniatura', {})
    foto = Image.open(os.path.join(RAIZ, m.get('foto') or largo['foto_horizontal'])).convert('RGB').resize((1280, 720))
    foto = ImageEnhance.Contrast(ImageEnhance.Color(foto).enhance(1.18)).enhance(1.08)
    sombra = Image.new('RGB', (1280, 720), NEGRO)
    degradado = Image.linear_gradient('L').rotate(-90).resize((1280, 720))
    im = Image.composite(sombra, foto, degradado.point(lambda v: max(0, min(170, int((v - 120) * 1.6)))))
    d = ImageDraw.Draw(im)
    colores = {'oro': ORO, 'rojo': (226, 45, 45), 'blanco': BLANCO, 'verde': (32, 190, 120), 'turquesa': (40, 200, 200)}
    MAX_X = m.get('max_x', 640)  # hasta dónde puede llegar el texto sin tocar a Victoria

    def ajustar(texto, peso, maximo, renglones_max):
        for tam in range(maximo, 40, -4):
            f = fuente(peso, tam)
            renglones, actual = [], ''
            for palabra in texto.split():
                prueba = (actual + ' ' + palabra).strip()
                if d.textlength(prueba, font=f) <= MAX_X - 50 or not actual:
                    actual = prueba
                else:
                    renglones.append(actual)
                    actual = palabra
            renglones.append(actual)
            if len(renglones) <= renglones_max and all(d.textlength(r, font=f) <= MAX_X - 50 for r in renglones):
                return f, tam, renglones
        return f, tam, renglones

    bloques = []
    if m.get('superior'):
        bloques.append(('sup',) + ajustar(m['superior'].upper(), 'Black', 52, 1))
    bloques.append(('grande',) + ajustar(m['grande'].upper(), 'Black', 190, 2))
    if m.get('banda'):
        bloques.append(('banda',) + ajustar(m['banda'].upper(), 'Black', 64, 1))
    alto_total = sum(tam * 1.05 * len(r) + 28 for _, f, tam, r in bloques)
    y = (720 - alto_total) / 2
    for tipo, f, tam, renglones in bloques:
        for r in renglones:
            if tipo == 'banda':
                ancho = d.textlength(r, font=f)
                color = colores.get(m.get('color_banda', 'rojo'), (226, 45, 45))
                d.rounded_rectangle((44, y - 6, 44 + ancho + 36, y + tam * 1.12), radius=12, fill=color)
                d.text((62, y), r, font=f, fill=NEGRO if color in (ORO, BLANCO, (32, 190, 120), (40, 200, 200)) else BLANCO)
            else:
                color = colores.get(m.get('color_grande', 'oro'), ORO) if tipo == 'grande' else BLANCO
                d.text((50, y + 6), r, font=f, fill=(0, 0, 0))  # sombra
                d.text((44, y), r, font=f, fill=color, stroke_width=max(4, tam // 22), stroke_fill=NEGRO)
            y += tam * 1.05
        y += 28
    im.save(ruta, quality=92)


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('voces', 'victoria', 'laminas', 'armar', 'todo'):
        sys.exit(__doc__)
    paso, vid = sys.argv[1:]
    if paso == 'todo':
        victoria(vid)
        laminas(vid)
        armar(vid)
    else:
        globals()[paso](vid)
