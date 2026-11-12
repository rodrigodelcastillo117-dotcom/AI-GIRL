"""Video largo de YouTube (horizontal, 6-8 min) a partir de un guion por segmentos (Rodrigo, 12-nov-2026: "haz videos
largos de aguinaldo").

Uso:
  $VOZ_PYTHON scripts/largo.py voces <id>            1) voz de cada segmento (voz_victoria.py: la transcribe y la repite si no sale)
  python scripts/largo.py victoria <id>              2) segmentos a cámara con Replicate (video_replicate.py, 1920x1080) + qa
  python scripts/largo.py laminas <id>               3) dibuja las láminas (1920x1080, negro y dorado)
  python scripts/largo.py armar <id>                 4) une todo, capítulos, miniatura y textos para YouTube
  python scripts/largo.py todo <id>                  2, 3 y 4 seguidos (las voces van aparte: necesitan VOZ_PYTHON)
  python scripts/largo.py subir <id>                 5) a YouTube, programado a su publica_utc, con miniatura y lista,
                                                     y a la página de Facebook a la misma hora (publer.py --solo-facebook)

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


import hashlib
import re


def clave_voz(s):
    """Nombre del audio y de la toma de Victoria por su TEXTO (no por su posición): si se reordena o se intercala el
    guion, lo ya generado (y pagado en Replicate) se reutiliza."""
    return hashlib.sha1(s['voz'].strip().encode()).hexdigest()[:10]


def clave_visual(s):
    return hashlib.sha1(json.dumps(s, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]


def ruta_voz(carpeta, s):
    return os.path.join(carpeta, f'voz-{clave_voz(s)}.mp3')


def ruta_seg(carpeta, s):
    return os.path.join(carpeta, f"seg-{clave_voz(s) if s['tipo'] == 'victoria' else clave_visual(s)}.mp4")


def migrar(vid):
    """Pasa los archivos viejos (voz-03.mp3, seg-03.mp4: por posición) a nombres por contenido. Se corre una vez,
    con el guion tal como estaba cuando se generaron."""
    largo, carpeta = cargar(vid)
    n = 0
    for i, s in enumerate(largo['segmentos']):
        pares = [(f'voz-{i:02d}.mp3', ruta_voz(carpeta, s))]
        if s['tipo'] == 'victoria':
            pares += [(f'seg-{i:02d}.mp4', ruta_seg(carpeta, s)), (f'seg-{i:02d}-palabras.json', ruta_seg(carpeta, s).replace('.mp4', '-palabras.json'))]
        for viejo, nuevo in pares:
            viejo = os.path.join(carpeta, viejo)
            if os.path.exists(viejo) and not os.path.exists(nuevo):
                os.rename(viejo, nuevo)
                n += 1
    print(f'ok migrar {vid}: {n} archivos')


def _frases(texto):
    return [f.strip() for f in re.findall(r'[^.?!¿¡]*[¿¡]?[^.?!]*[.?!]+|[^.?!]+$', texto) if f.strip()]


def intercalar(vid):
    """Victoria, lámina, Victoria, lámina (Rodrigo, 12-nov-2026: "muy orgánico, como si ella fuera real"). Donde hay
    dos visuales seguidos, la primera frase del segundo la dice Victoria a cámara y el resto se narra sobre la lámina.
    Se guarda en contenido/largos.json (una sola vez: "intercalado": true)."""
    ruta = os.path.join(RAIZ, 'contenido', 'largos.json')
    todos = json.load(open(ruta))
    largo = next(x for x in todos if x['id'] == vid)
    if largo.get('intercalado'):
        print(f'{vid} ya está intercalado')
        return
    nuevos, puentes, sin_partir = [], 0, 0
    for s in largo['segmentos']:
        if s['tipo'] != 'victoria' and nuevos and nuevos[-1]['tipo'] != 'victoria':
            frases = _frases(s['voz'])
            primera, resto = (frases[0], ' '.join(frases[1:])) if len(frases) > 1 else ('', '')
            if 4 <= len(primera.split()) <= 30 and len(resto.split()) >= 8:
                nuevos.append({'tipo': 'victoria', 'capitulo': s.get('capitulo'), 'voz': primera, 'puente': True})
                nuevos.append({**s, 'capitulo': None, 'voz': resto})
                puentes += 1
                continue
            sin_partir += 1
        nuevos.append(s)
    largo['segmentos'], largo['intercalado'] = nuevos, True
    json.dump(todos, open(ruta, 'w'), ensure_ascii=False, indent=1)
    open(ruta, 'a').write('\n')
    print(f'ok intercalar {vid}: {puentes} tomas nuevas de Victoria; {sin_partir} visuales seguidos que no se pudieron partir')


def voces(vid):
    largo, carpeta = cargar(vid)
    vistos, lista = set(), []
    for s in largo['segmentos']:
        if not os.path.exists(ruta_voz(carpeta, s)) and ruta_voz(carpeta, s) not in vistos:
            vistos.add(ruta_voz(carpeta, s))
            lista.append({'texto': s['voz'], 'salida': ruta_voz(carpeta, s)})
    if lista:
        ruta = os.path.join(carpeta, 'voces.json')
        json.dump(lista, open(ruta, 'w'), ensure_ascii=False)
        subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'voz_victoria.py'), ruta], check=True)
    total = sum(duracion(ruta_voz(carpeta, s)) for s in largo['segmentos'])
    print(f'ok voces {vid}: {len(largo["segmentos"])} segmentos, {total / 60:.1f} min')


def victoria(vid):
    import video_replicate
    largo, carpeta = cargar(vid)
    foto = os.path.join(RAIZ, largo['foto_horizontal'])
    gasto = 0
    for i, s in enumerate(largo['segmentos']):
        if s['tipo'] != 'victoria':
            continue
        salida = ruta_seg(carpeta, s)
        if os.path.exists(salida):
            continue
        r = video_replicate.generar(foto, ruta_voz(carpeta, s), salida,
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
        f, tam, rr = _renglones(d, 'Fuente: ' + s['fuente'], 'Regular', 26, ANCHO - 2 * x0 - 640, 2, 18)
        for k, r in enumerate(rr):
            d.text((x0, ALTO - 120 + k * (tam + 6) - (len(rr) - 1) * (tam + 6) / 2), r, font=f, fill=GRIS)
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


def _renglones(d, texto, peso, tam_max, ancho, max_renglones, tam_min=22):
    """Parte texto en renglones de hasta `ancho` px; si no cabe en max_renglones, achica la letra."""
    for tam in range(tam_max, tam_min - 1, -2):
        f = fuente(peso, tam)
        renglones, actual = [], ''
        for palabra in str(texto).split():
            prueba = (actual + ' ' + palabra).strip()
            if d.textlength(prueba, font=f) <= ancho or not actual:
                actual = prueba
            else:
                renglones.append(actual)
                actual = palabra
        if actual:
            renglones.append(actual)
        if len(renglones) <= max_renglones:
            return f, tam, renglones
    return f, tam, renglones[:max_renglones]


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
        f, tam, rr = _renglones(d, 'Fuente: ' + s['fuente'], 'Regular', 26, ANCHO - 2 * x0 - 640, 2, 18)
        for k, r in enumerate(rr):
            d.text((x0, ALTO - 120 + k * (tam + 6) - (len(rr) - 1) * (tam + 6) / 2), r, font=f, fill=GRIS)
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
        f, tam, rr = _renglones(d, s['nota'], 'Medium', 34, ANCHO - x_et - 150, 2, 24)
        for k, r in enumerate(rr):
            d.text((x_et, y + 20 + k * (tam + 8)), r, font=f, fill=GRIS)
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
        f, tam, rr = _renglones(d, p['texto'], 'Medium', 36, ancho_caja - 60, 4, 24)
        for r in rr:
            d.text((x + 30, yy), r, font=f, fill=BLANCO)
            yy += tam + 10
        if p.get('resultado'):
            f, tam, rr = _renglones(d, p['resultado'], 'Black', 46, ancho_caja - 60, 2, 24)
            yr = y0 + alto - 40 - len(rr) * (tam + 8)
            for r in rr:
                d.text((x + 30, yr), r, font=f, fill=ORO)
                yr += tam + 8
        if i < n - 1:
            xa = x + ancho_caja + 12
            d.polygon([(xa, y0 + alto / 2 - 18), (xa + hueco - 24, y0 + alto / 2), (xa, y0 + alto / 2 + 18)], fill=ORO)
    im.save(ruta, quality=95)


# ---- Láminas verticales para los shorts (recortes.py): mismos datos, pensadas para leerse en un celular (12-nov-2026:
# la lámina horizontal reducida a 1080 de ancho quedaba con letra de ~24 px). Lienzo 1080x1215, sin la cara (en el
# short Victoria ya sale en su cuadro).
V_ANCHO, V_ALTO, V_X = 1080, 1215, 70


def lamina_vertical(s, capitulo, ruta):
    im = Image.new('RGB', (V_ANCHO, V_ALTO), NEGRO)
    d = ImageDraw.Draw(im)
    ancho = V_ANCHO - 2 * V_X
    y = 40
    if capitulo:
        d.text((V_X, y), capitulo.upper(), font=fuente('SemiBold', 32), fill=ORO)
        d.line([(V_X, y + 50), (V_X + 90, y + 50)], fill=ORO, width=5)
        y += 80
    f, tam, rr = _renglones(d, s.get('titulo') or '', 'Black', 72, ancho, 3, 44)
    for r in rr:
        d.text((V_X, y), r, font=f, fill=BLANCO)
        y += tam + 12
    y += 24
    tipo = s.get('tipo')
    if tipo == 'grafica':
        barras = s.get('barras') or []
        maximo = max((b['valor'] for b in barras), default=1) or 1
        alto_b = 64
        for b in barras:
            fe, te, re_ = _renglones(d, b['etiqueta'], 'Medium', 40, ancho, 2, 28)
            for r in re_:
                d.text((V_X, y), r, font=fe, fill=BLANCO)
                y += te + 6
            y += 12
            valor = b.get('texto_valor') or f"{b['valor']:,}"
            fv = fuente('Black', 50)
            espacio_valor = d.textlength(valor, font=fv) + 24
            largo_px = max(10, int((ancho - espacio_valor) * b['valor'] / maximo))
            d.rounded_rectangle((V_X, y, V_X + largo_px, y + alto_b), radius=8, fill=ORO, corners=(False, True, True, False))
            d.text((V_X + largo_px + 18, y + alto_b / 2), valor, font=fv, fill=BLANCO, anchor='lm')
            y += alto_b + 30
        if s.get('nota'):
            fn_, tn, rn = _renglones(d, s['nota'], 'Medium', 34, ancho, 3, 24)
            for r in rn:
                d.text((V_X, y), r, font=fn_, fill=GRIS)
                y += tn + 8
    elif tipo == 'pasos':
        lista = (s.get('pasos') or [])[:4]
        disponible = V_ALTO - 120 - y
        alto_caja = min(250, int(disponible / max(1, len(lista))) - 18)
        for i, p_ in enumerate(lista):
            d.rounded_rectangle((V_X, y, V_X + ancho, y + alto_caja), radius=22, outline=(70, 70, 76), width=3, fill=(20, 20, 24))
            d.ellipse((V_X + 24, y + 24, V_X + 94, y + 94), fill=ORO)
            d.text((V_X + 59, y + 59), str(i + 1), font=fuente('Black', 44), fill=NEGRO, anchor='mm')
            ft, tt, rt = _renglones(d, p_['texto'], 'Medium', 38, ancho - 150, 2, 26)
            yy = y + 26
            for r in rt:
                d.text((V_X + 120, yy), r, font=ft, fill=BLANCO)
                yy += tt + 8
            if p_.get('resultado'):
                fr, tr, rr2 = _renglones(d, p_['resultado'], 'Black', 46, ancho - 150, 2, 26)
                yy = max(yy + 6, y + alto_caja - 22 - len(rr2) * (tr + 6))
                for r in rr2:
                    d.text((V_X + 120, yy), r, font=fr, fill=ORO)
                    yy += tr + 6
            y += alto_caja + 18
    else:
        if s.get('dato_grande'):
            fd, td, rd = _renglones(d, s['dato_grande'], 'Black', 130, ancho, 2, 56)
            for r in rd:
                d.text((V_X, y), r, font=fd, fill=ORO)
                y += td + 14
            y += 16
        for p_ in s.get('puntos') or []:
            fp, tp, rp = _renglones(d, p_, 'Medium', 46, ancho - 46, 3, 30)
            d.ellipse((V_X, y + tp / 2 - 9, V_X + 18, y + tp / 2 + 9), fill=ORO)
            for r in rp:
                d.text((V_X + 46, y), r, font=fp, fill=BLANCO)
                y += tp + 10
            y += 18
            if y > V_ALTO - 160:
                break
    if s.get('fuente'):
        ff_, tf, rf = _renglones(d, 'Fuente: ' + s['fuente'], 'Regular', 24, ancho, 2, 18)
        yf = V_ALTO - 40 - len(rf) * (tf + 6)
        for r in rf:
            d.text((V_X, yf), r, font=ff_, fill=GRIS)
            yf += tf + 6
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
        if os.path.exists(ruta_seg(carpeta, s)) and os.environ.get('REHACER_LAMINAS') != '1':
            continue
        png = ruta_seg(carpeta, s).replace('.mp4', '.png')
        (DIBUJOS[s['tipo']] or lamina)(s, capitulo, png, cara)
        audio = ruta_voz(carpeta, s)
        seg = duracion(audio) + PAUSA_S
        # Acercamiento muy lento (1.00 → 1.04) para que la lámina no se vea congelada.
        ffmpeg('-loop', '1', '-i', png, '-i', audio, '-filter_complex',
               f"[0:v]scale=2304:1296,zoompan=z='1+0.04*on/({seg:.2f}*30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
               f":d=1:s={ANCHO}x{ALTO}:fps=30,fade=t=in:st=0:d=0.25,format=yuv420p[v];[1:a]apad[a]",
               '-map', '[v]', '-map', '[a]', '-t', f'{seg:.3f}', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
               '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k', ruta_seg(carpeta, s))
        hechas += 1
    print(f'ok laminas {vid}: {hechas}')


def _ts(t):
    m, s = divmod(int(t), 60)
    return f'{m}:{s:02d}'


def armar(vid):
    largo, carpeta = cargar(vid)
    lista, capitulos, t = [], [], 0.0
    for i, s in enumerate(largo['segmentos']):
        seg = ruta_seg(carpeta, s)
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
    # Facebook (Rodrigo, 12-nov-2026: "a Facebook subimos todo, incluyendo videos largos"): el gancho de la descripción
    # (sus primeras líneas, con la calculadora), el aviso de IA y los hashtags.
    gancho = seo['descripcion'].strip().split('\n\n')[0]
    open(os.path.join(carpeta, 'texto_facebook.txt'), 'w').write(
        seo['titulo'] + '\n\n' + gancho + '\n\nVictoria es un personaje creado con inteligencia artificial. Información general, '
        'no asesoría financiera ni legal.\n\n' + ' '.join(seo.get('hashtags', [])))
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


def subir(vid):
    """Sube el largo a YouTube programado a su publica_utc (Rodrigo, 12-nov-2026: "que salga todo directamente"): título,
    descripción con capítulos, tags, miniatura A, categoría Educación, marcado como contenido sintético (youtube.py), y lo
    agrega a la lista de su tema. Solo si ya está armado y no se subió antes. Guarda el enlace y estado "programado"."""
    largo, carpeta = cargar(vid)
    final = os.path.join(RAIZ, 'videos', 'largos', f'{vid}-horizontal.mp4')
    if largo.get('youtube'):
        print(f'{vid} ya está en YouTube: {largo["youtube"]}')
        return
    if not os.path.exists(final) or not os.path.exists(os.path.join(carpeta, 'descripcion_youtube.txt')):
        sys.exit(f'{vid} no está armado: corre "largo.py todo {vid}" primero')
    miniatura(largo, os.path.join(RAIZ, 'videos', 'largos', f'{vid}-miniatura.jpg'))
    import datetime
    cuando = largo.get('publica_utc') or ''
    ahora = datetime.datetime.now(datetime.timezone.utc)
    if not cuando or datetime.datetime.fromisoformat(cuando.replace('Z', '+00:00')) < ahora + datetime.timedelta(minutes=15):
        cuando = (ahora + datetime.timedelta(minutes=20)).strftime('%Y-%m-%dT%H:%M:%SZ')
    salida = subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'youtube.py'), 'subir', final,
                             open(os.path.join(carpeta, 'titulo.txt')).read().strip(),
                             os.path.join(carpeta, 'descripcion_youtube.txt'), cuando,
                             '--tags', os.path.join(carpeta, 'tags_youtube.txt'),
                             '--miniatura', os.path.join(RAIZ, 'videos', 'largos', f'{vid}-miniatura.jpg'), '--largo'],
                            capture_output=True, text=True)
    print(salida.stdout[-800:], salida.stderr[-800:])
    enlace = next((x for x in salida.stdout.split() if 'youtube.com/watch' in x), '')
    if salida.returncode != 0 or not enlace:
        sys.exit(f'No se pudo subir {vid} (código {salida.returncode})')
    video_id = enlace.split('v=')[-1]
    clave = largo.get('playlist', 'aguinaldo')
    subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'youtube.py'), 'playlist', video_id, clave])
    ruta = os.path.join(RAIZ, 'contenido', 'largos.json')
    todos = json.load(open(ruta))
    for x in todos:
        if x['id'] == vid:
            x.update(youtube=enlace, estado='programado', publica_utc=cuando)
    json.dump(todos, open(ruta, 'w'), ensure_ascii=False, indent=1)
    open(ruta, 'a').write('\n')
    print(f'ok {vid} programado {cuando}: {enlace}')
    facebook(vid, cuando)


def facebook(vid, cuando=None):
    """El mismo video horizontal como video nativo en la página de Facebook de Victoria, a la hora de YouTube."""
    largo, carpeta = cargar(vid)
    if largo.get('facebook'):
        print(f'{vid} ya está en Facebook')
        return
    texto = os.path.join(carpeta, 'texto_facebook.txt')
    final = os.path.join(RAIZ, 'videos', 'largos', f'{vid}-horizontal.mp4')
    if not os.path.exists(texto):
        sys.exit(f'Falta {texto}: corre "largo.py armar {vid}"')
    cuando = cuando or largo.get('publica_utc')
    r = subprocess.run([sys.executable, os.path.join(RAIZ, 'scripts', 'publer.py'), 'publicar', final, texto, cuando,
                        largo['seo']['titulo'], '--solo-facebook'], capture_output=True, text=True)
    print(r.stdout[-600:], r.stderr[-600:])
    if r.returncode != 0:
        print(f'AVISO: Facebook no quedó programado para {vid} (código {r.returncode}); YouTube sí.')
        return
    ruta = os.path.join(RAIZ, 'contenido', 'largos.json')
    todos = json.load(open(ruta))
    for x in todos:
        if x['id'] == vid:
            x['facebook'] = {'publica_utc': cuando, 'estado': 'programado'}
    json.dump(todos, open(ruta, 'w'), ensure_ascii=False, indent=1)
    open(ruta, 'a').write('\n')
    print(f'ok {vid} en Facebook {cuando}')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('voces', 'victoria', 'laminas', 'armar', 'todo', 'subir', 'migrar', 'intercalar', 'facebook'):
        sys.exit(__doc__)
    paso, vid = sys.argv[1:]
    if paso == 'todo':
        victoria(vid)
        laminas(vid)
        armar(vid)
    else:
        globals()[paso](vid)
