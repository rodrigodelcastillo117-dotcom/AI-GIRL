"""Dibuja las diapositivas de un carrusel de contenido/carruseles.json (Instagram y TikTok).

Uso: python carrusel.py <id> [carpeta]        (por defecto carruseles/<id>/: 00.png, 01.png...)

1080x1350 (4:5): lo más alto que Instagram acepta en carrusel; TikTok lo enseña igual.
- Portada: foto de Victoria, etiqueta en dorado, el gancho grande y la leyenda de IA.
- Datos: número, título y texto; lo que va después de una línea en blanco es la fuente (chico).
- Cierre: fondo dorado con la llamada a guardar, mandar y seguir.
Portada: "foto": "auto" toma la foto de Victoria más nueva de assets/fotos/ que ningún otro
carrusel haya usado (cada video deja ahí su foto base, PIPELINE paso 3) y la anota en el JSON.
Si no queda ninguna sin usar, sale con error: hay que generar una (CARRUSELES.md).
Datos: "fondo": "auto" toma de assets/fondos/ el lugar de lujo menos usado (yate, jet, palco...),
desenfocado y oscurecido para que el texto se lea; cada carrusel estrena fondo.
Una diapositiva puede llevar "imagen": "wikimedia:<búsqueda>" (foto real con licencia libre, la
primera opción porque hace más creíble el dato) o "ia:<descripción>" (Flux Schnell en Replicate,
de pago, solo si no hay foto real). Si ninguna da algo, la diapositiva sale solo con texto.
"""
import glob
import html
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANCHO, ALTO, MARGEN = 1080, 1350, 80
NEGRO, ORO, CREMA, TENUE = (11, 11, 13), (245, 197, 66), (243, 237, 226), (163, 155, 141)  # como el sitio
FUENTES = '/usr/share/fonts/opentype/inter/Inter-{}.otf'
AGENTE = 'VictoriaTheCEO/1.0 (https://victoriatheceo.vercel.app)'
LICENCIAS_LIBRES = ('cc0', 'cc by', 'public domain', 'dominio público', 'pd')


def letra(peso, tam):
    return ImageFont.truetype(FUENTES.format(peso), tam)


def renglones(texto, fuente, ancho, d):
    salida = []
    for parrafo in texto.split('\n'):
        actual = ''
        for palabra in parrafo.split():
            prueba = f'{actual} {palabra}'.strip()
            if d.textlength(prueba, font=fuente) <= ancho:
                actual = prueba
            else:
                salida.append(actual)
                actual = palabra
        salida.append(actual)
    return salida


def acomodar(texto, peso, tam, minimo, ancho, alto, d, interlineado=1.18):
    """El tamaño más grande (de tam a minimo) en el que el texto cabe en la caja."""
    while True:
        f = letra(peso, tam)
        lineas = renglones(texto, f, ancho, d)
        if len(lineas) * tam * interlineado <= alto or tam <= minimo:
            return f, lineas, int(tam * interlineado)
        tam -= 2


def escribir(d, xy, lineas, fuente, salto, color):
    x, y = xy
    for linea in lineas:
        d.text((x, y), linea, font=fuente, fill=color)
        y += salto
    return y


def pie(d, n, total, color=TENUE):
    f = letra('SemiBold', 26)
    d.text((MARGEN, ALTO - 70), '@victoriatheceo', font=f, fill=color)
    marca = f'{n}/{total}'
    d.text((ANCHO - MARGEN - d.textlength(marca, font=f), ALTO - 70), marca, font=f, fill=color)


def recortar(foto, ancho, alto, arriba=0.06):
    """Llena la caja sin deformar; recorta cerca de arriba para no cortar la cara."""
    escala = max(ancho / foto.width, alto / foto.height)
    foto = foto.resize((int(foto.width * escala + 0.5), int(foto.height * escala + 0.5)), Image.LANCZOS)
    x = (foto.width - ancho) // 2
    y = min(int(foto.height * arriba), foto.height - alto)
    return foto.crop((x, y, x + ancho, y + alto))


def elegir_fondo(c, todos):
    usos = {}
    for x in todos:
        if x['id'] != c['id'] and x.get('fondo', 'auto') != 'auto':
            usos[x['fondo']] = usos.get(x['fondo'], 0) + 1
    fondos = sorted(os.path.relpath(f, RAIZ) for f in glob.glob(os.path.join(RAIZ, 'assets', 'fondos', '*.jpg')))
    return min(fondos, key=lambda f: (usos.get(f, 0), f)) if fondos else None


def lienzo_oscuro(c):
    if not c.get('fondo'):
        return Image.new('RGB', (ANCHO, ALTO), NEGRO)
    foto = recortar(Image.open(os.path.join(RAIZ, c['fondo'])).convert('RGB'), ANCHO, ALTO, arriba=0.2)
    foto = foto.filter(ImageFilter.GaussianBlur(7))
    return Image.blend(foto, Image.new('RGB', (ANCHO, ALTO), NEGRO), 0.8)


def elegir_foto(c, todos):
    usadas = {x['portada']['foto'] for x in todos if x['id'] != c['id']}
    fotos = sorted(glob.glob(os.path.join(RAIZ, 'assets', 'fotos', '*.jpg')), key=os.path.getmtime, reverse=True)
    libre = next((f for f in fotos if os.path.relpath(f, RAIZ) not in usadas), None)
    if not libre:
        sys.exit('ERROR: no queda foto de Victoria sin usar en assets/fotos: genera una (docs/CARRUSELES.md)')
    return os.path.relpath(libre, RAIZ)


def portada(c, total):
    p = c['portada']
    lienzo = recortar(Image.open(os.path.join(RAIZ, p['foto'])).convert('RGB'), ANCHO, ALTO)
    sombra = Image.new('L', (1, ALTO))
    for y in range(ALTO):
        sombra.putpixel((0, y), int(max(0, min(1, (y - 560) / 420)) * 240))
    lienzo.paste(Image.new('RGB', (ANCHO, ALTO), NEGRO), (0, 0), sombra.resize((ANCHO, ALTO)))
    d = ImageDraw.Draw(lienzo)
    f, lineas, salto = acomodar(p['titulo'].upper(), 'Black', 84, 56, ANCHO - 2 * MARGEN, 330, d, 1.08)
    y = ALTO - 170 - len(lineas) * salto
    d.text((MARGEN, y - 62), p['etiqueta'].upper(), font=letra('Bold', 34), fill=ORO)
    escribir(d, (MARGEN, y), lineas, f, salto, CREMA)
    d.text((MARGEN, ALTO - 112), 'Victoria es un personaje creado con IA', font=letra('Medium', 22), fill=TENUE)
    f = letra('Bold', 28)
    d.text((ANCHO - MARGEN - d.textlength('DESLIZA →', font=f), ALTO - 70), 'DESLIZA →', font=f, fill=ORO)
    d.text((MARGEN, ALTO - 70), '@victoriatheceo', font=letra('SemiBold', 26), fill=CREMA)
    return lienzo


def de_wikimedia(consulta):
    """Primera foto con licencia libre en Wikimedia Commons, con su crédito."""
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({
        'action': 'query', 'format': 'json', 'generator': 'search', 'gsrnamespace': 6, 'gsrlimit': 8,
        'gsrsearch': f'{consulta} filetype:bitmap', 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|mime',
        'iiurlwidth': 1080})
    datos = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': AGENTE}), timeout=30))
    for pagina in sorted((datos.get('query') or {}).get('pages', {}).values(), key=lambda p: p.get('index', 99)):
        info = pagina['imageinfo'][0]
        meta = {k: html.unescape(re.sub('<[^>]+>', '', v.get('value', ''))).strip() for k, v in info['extmetadata'].items()}
        licencia = meta.get('LicenseShortName', '')
        if meta.get('NonFree') == 'true' or not licencia.lower().startswith(LICENCIAS_LIBRES):
            continue
        if info.get('mime') not in ('image/jpeg', 'image/png'):
            continue
        foto = urllib.request.urlopen(urllib.request.Request(info['thumburl'], headers={'User-Agent': AGENTE}), timeout=60).read()
        return Image.open(io.BytesIO(foto)).convert('RGB'), f"Foto: {meta.get('Artist', 'Wikimedia Commons')[:60]} · {licencia} · Wikimedia Commons"
    return None


def de_replicate(descripcion):
    token = os.environ.get('REPLICATE_API_TOKEN') or os.environ.get('REPLICATE_API_KEY')
    if not token:
        return None
    cuerpo = json.dumps({'input': {'prompt': f'{descripcion}. Photographic, natural light. No text, no letters, no logos.',
                                   'aspect_ratio': '16:9', 'output_format': 'png'}}).encode()
    req = urllib.request.Request('https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions',
                                 data=cuerpo, method='POST', headers={'Authorization': f'Bearer {token}',
                                                                      'Content-Type': 'application/json', 'Prefer': 'wait'})
    salida = json.load(urllib.request.urlopen(req, timeout=120)).get('output') or []
    if not salida:
        return None
    foto = urllib.request.urlopen(salida[0] if isinstance(salida, list) else salida, timeout=60).read()
    return Image.open(io.BytesIO(foto)).convert('RGB'), 'Imagen ilustrativa creada con IA'


def imagen(spec, guardada):
    """La imagen de una diapositiva. Se guarda en assets/imagenes para no pagarla dos veces y para
    volver a armar el carrusel (o el video largo) igual."""
    if os.path.exists(guardada):
        return Image.open(guardada).convert('RGB'), open(guardada + '.txt').read().strip()
    tipo, _, consulta = spec.partition(':')
    for fuente in ((de_wikimedia, de_replicate) if tipo == 'wikimedia' else (de_replicate,) if tipo == 'ia' else ()):
        try:
            r = fuente(consulta)
            if r:
                os.makedirs(os.path.dirname(guardada), exist_ok=True)
                r[0].save(guardada, quality=88)
                open(guardada + '.txt', 'w').write(r[1])
                return r
        except Exception as e:  # una fuente caída no detiene el carrusel: se prueba la siguiente
            print(f'AVISO: {fuente.__name__} falló para "{consulta}": {e}')
    return None


def dato(diapo, n, total, c):
    cid = c['id']
    lienzo = lienzo_oscuro(c)
    d = ImageDraw.Draw(lienzo)
    d.text((MARGEN, 70), f'{n - 1:02d}', font=letra('Black', 120), fill=ORO)
    d.rectangle((MARGEN, 235, MARGEN + 90, 241), fill=ORO)
    foto = imagen(diapo['imagen'], os.path.join(RAIZ, 'assets', 'imagenes', f'{cid}-{n - 1:02d}.jpg')) if diapo.get('imagen') else None
    abajo = ALTO - 130 - (500 if foto else 0)
    ancho = ANCHO - 2 * MARGEN
    cuerpo, *fuentes = diapo['texto'].split('\n\n')
    ft, lt, st = acomodar(diapo['titulo'], 'Black', 92, 52, ancho, 330, d, 1.1)
    fc, lc, sc = acomodar(cuerpo, 'Medium', 62, 36, ancho, abajo - 290 - len(lt) * st - 150, d, 1.3)
    fuente = acomodar('\n'.join(fuentes), 'Medium', 30, 22, ancho, 90, d, 1.3) if fuentes else None
    alto_bloque = len(lt) * st + 36 + len(lc) * sc + (24 + len(fuente[1]) * fuente[2] if fuente else 0)
    y = max(290, 290 + (abajo - 290 - alto_bloque) // 2)  # el bloque va centrado en el espacio libre
    y = escribir(d, (MARGEN, y), lt, ft, st, CREMA) + 36
    y = escribir(d, (MARGEN, y), lc, fc, sc, CREMA) + 24
    if fuente:
        escribir(d, (MARGEN, y), fuente[1], fuente[0], fuente[2], TENUE)
    if foto:
        caja = recortar(foto[0], ANCHO - 2 * MARGEN, 420, arriba=0.2)
        lienzo.paste(caja, (MARGEN, ALTO - 130 - 470))
        d.text((MARGEN, ALTO - 130 - 40), foto[1][:90], font=letra('Medium', 20), fill=TENUE)
    pie(d, n, total)
    return lienzo


def cierre(c, n, total):
    lienzo = Image.new('RGB', (ANCHO, ALTO), ORO)
    d = ImageDraw.Draw(lienzo)
    ancho = ANCHO - 2 * MARGEN
    ft, lt, st = acomodar(c['cierre']['titulo'], 'Black', 96, 56, ancho, 560, d, 1.08)
    fc, lc, sc = acomodar(c['cierre']['texto'], 'Medium', 50, 32, ancho, 360, d, 1.35)
    y = (ALTO - (len(lt) * st + 60 + len(lc) * sc)) // 2
    y = escribir(d, (MARGEN, y), lt, ft, st, NEGRO) + 60
    escribir(d, (MARGEN, y), lc, fc, sc, NEGRO)
    pie(d, n, total, NEGRO)
    return lienzo


def dibujar(c, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    total = len(c['diapositivas']) + 2
    hojas = [portada(c, total)] + [dato(x, i + 2, total, c) for i, x in enumerate(c['diapositivas'])] + [cierre(c, total, total)]
    rutas = []
    for i, hoja in enumerate(hojas):
        rutas.append(os.path.join(carpeta, f'{i:02d}.png'))
        hoja.save(rutas[-1], optimize=True)
    return rutas


def cargar(id_carrusel):
    ruta = os.path.join(RAIZ, 'contenido', 'carruseles.json')
    datos = json.load(open(ruta))
    c = next((x for x in datos['carruseles'] if x['id'] == id_carrusel), None)
    if not c:
        sys.exit(f'ERROR: no existe el carrusel {id_carrusel}')
    cambio = False
    if c['portada']['foto'] == 'auto':
        c['portada']['foto'], cambio = elegir_foto(c, datos['carruseles']), True
    if c.get('fondo', 'auto') == 'auto':
        c['fondo'], cambio = elegir_fondo(c, datos['carruseles']), True
    if cambio:
        json.dump(datos, open(ruta, 'w'), ensure_ascii=False, indent=1)
        open(ruta, 'a').write('\n')
    if len(c['diapositivas']) + 2 > 10:
        sys.exit('ERROR: Instagram acepta máximo 10 fotos por carrusel (portada + 8 datos + cierre)')
    return c


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    c = cargar(sys.argv[1])
    for ruta in dibujar(c, sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, 'carruseles', c['id'])):
        print(ruta)


if __name__ == '__main__':
    main()
