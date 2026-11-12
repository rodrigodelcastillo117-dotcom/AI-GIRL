"""Reel de texto en pantalla con clips de Victoria (Rodrigo, 12-nov-2026: "sácale jugo total a Everygen").

Convierte un carrusel YA VERIFICADO en un video vertical de ~15-20 s: Victoria y Capital en movimiento (clips sin voz
de assets/broll/, hechos con los créditos de Everygen/OpenArt) y encima el gancho, los datos y el cierre del carrusel en
letra grande. No usa Replicate ni voz: es otro formato para el mismo contenido (TODO SE ADAPTA) y suma volumen.

Uso: python scripts/reel_texto.py <id_carrusel> [--clips a.mp4,b.mp4]
Salida en carruseles/<id>/:
  reel-texto.mp4          sin audio: Instagram (ig_reel_musica.py <id> --video reel-texto.mp4 le pone música en tendencia)
  reel-texto-musica.mp4   con música de fondo de assets/musica/: TikTok, YouTube Shorts y Facebook (publer.py)
Cada tarjeta lleva su propio fondo: fotos dinámicas (assets/fotos/dinamica-*) con movimiento lento o clips de assets/broll/,\nsiempre lo menos usado (assets/broll/uso.json) para que Victoria casi no se repita.
"""
import glob
import json
import os
import random
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = '/usr/share/fonts/opentype/inter/'
ORO, BLANCO = (245, 197, 66), (255, 255, 255)
ANCHO, ALTO, MARGEN = 1080, 1920, 80
SEG_GANCHO, SEG_DATO, SEG_CIERRE = 2.6, 2.8, 2.6


def fuente(peso, tam):
    return ImageFont.truetype(os.path.join(FUENTES, f'Inter-{peso}.otf'), tam)


def sin_emoji(t):
    return re.sub(r'[\U0001F000-\U0001FAFF☀-➿️‍]', '', t or '').strip()


def renglones(d, texto, f, ancho):
    out, linea = [], ''
    for p in texto.split():
        prueba = (linea + ' ' + p).strip()
        if d.textlength(prueba, font=f) <= ancho or not linea:
            linea = prueba
        else:
            out.append(linea)
            linea = p
    return out + ([linea] if linea else [])


def tarjeta(titulo, linea, ruta, etiqueta=None, grande=False):
    """PNG transparente 1080x1920: degradado oscuro abajo y el texto en la zona segura (encima de la interfaz de la app)."""
    im = Image.new('RGBA', (ANCHO, ALTO), (0, 0, 0, 0))
    grad = Image.new('L', (1, ALTO))
    for y in range(ALTO):
        grad.putpixel((0, y), int(225 * max(0, (y - 820) / (ALTO - 820)) ** 0.8))
    sombra = Image.new('RGBA', (ANCHO, ALTO), (0, 0, 0, 255))
    sombra.putalpha(grad.resize((ANCHO, ALTO)))
    im.alpha_composite(sombra)
    d = ImageDraw.Draw(im)
    ancho = ANCHO - 2 * MARGEN
    tam = 96 if grande else 78
    while True:
        ft = fuente('Black', tam)
        rt = renglones(d, titulo, ft, ancho)
        if len(rt) <= 4 or tam <= 52:
            break
        tam -= 6
    fl = fuente('SemiBold', 44)
    rl = renglones(d, linea, fl, ancho)[:4] if linea else []
    alto_txt = len(rt) * (tam + 14) + (24 + len(rl) * 58 if rl else 0) + (70 if etiqueta else 0)
    y = 1560 - alto_txt  # termina arriba de ~1560: libre de la barra y el texto de TikTok/Instagram
    if etiqueta:
        d.text((MARGEN, y), etiqueta.upper(), font=fuente('Bold', 36), fill=ORO)
        d.line([(MARGEN, y + 52), (MARGEN + 100, y + 52)], fill=ORO, width=6)
        y += 70
    for r in rt:
        d.text((MARGEN, y), r, font=ft, fill=BLANCO, stroke_width=3, stroke_fill=(0, 0, 0))
        y += tam + 14
    if rl:
        y += 24
        for r in rl:
            d.text((MARGEN, y), r, font=fl, fill=ORO, stroke_width=2, stroke_fill=(0, 0, 0))
            y += 58
    d.text((ANCHO - MARGEN, 1840), '@victoriatheceo · personaje creado con IA', font=fuente('Medium', 26),
           fill=(255, 255, 255, 170), anchor='rs')
    im.save(ruta)


def primera_frase(texto):
    """La línea de apoyo: la primera frase del texto de la diapositiva, sin la fuente (va en el texto del post)."""
    t = sin_emoji(texto.split('\n\n')[0].replace('\n', ' '))
    m = re.match(r'(.+?[.!?])(\s|$)', t)
    corta = (m.group(1) if m else t).rstrip(':').strip()
    return corta if len(corta) <= 110 else corta[:107].rsplit(' ', 1)[0] + '…'


def tarjetas_de(c):
    p, cierre = c.get('portada') or {}, c.get('cierre') or {}
    lista = [(sin_emoji(p.get('titulo') or c.get('titulo_post', '')), '', p.get('etiqueta'), True, SEG_GANCHO)]
    for i, d in enumerate(c.get('diapositivas') or [], start=1):
        lista.append((f"{i}. {sin_emoji(d.get('titulo', ''))}", primera_frase(d.get('texto', '')), None, False, SEG_DATO))
    lista.append((sin_emoji(cierre.get('titulo', 'Guárdalo.')), 'Sígueme: un dato de dinero que sí sirve, cada día.', None, True, SEG_CIERRE))
    return lista


def ff(*args):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *args], check=True)


def duracion(ruta):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ruta],
                                capture_output=True, text=True, check=True).stdout)


USO = os.path.join(RAIZ, 'assets', 'broll', 'uso.json')
MOVS = [  # movimiento lento distinto para cada foto (Rodrigo, 12-nov-2026: "sé dinámico")
    "z='min(1.0+0.0010*on,1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
    "z='max(1.18-0.0010*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
    "z='1.12':x='(iw-iw/zoom)*on/{n}':y='ih/2-(ih/zoom/2)'",
    "z='1.12':x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-(ih/zoom/2)'",
    "z='min(1.0+0.0008*on,1.15)':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*0.25'",
]


def biblioteca():
    """Fotos dinámicas (assets/fotos/dinamica-*) y clips (assets/broll/*.mp4), de lo menos usado a lo más usado."""
    try:
        uso = json.load(open(USO))
    except (OSError, ValueError):
        uso = {}
    clips = glob.glob(os.path.join(RAIZ, 'assets', 'broll', '*.mp4'))
    # Si la escena ya tiene movimiento real (assets/broll/<escena>-mov-N.mp4), la foto fija se deja de usar.
    con_mov = {os.path.basename(c).split('-mov-')[0] for c in clips if '-mov-' in c}
    fotos = [f for f in glob.glob(os.path.join(RAIZ, 'assets', 'fotos', 'dinamica-*.png')) +
             glob.glob(os.path.join(RAIZ, 'assets', 'fotos', 'dinamica-*.jpg'))
             if os.path.splitext(os.path.basename(f))[0][len('dinamica-'):] not in con_mov]
    todo = sorted(clips + fotos)
    return sorted(todo, key=lambda r: (uso.get(os.path.relpath(r, RAIZ), 0), random.random())), uso


def tramo(fuente, seg, salida, k):
    n = int(seg * 30) + 1
    if fuente.endswith('.mp4'):
        largo = duracion(fuente)
        ini = max(0.0, min(largo - seg, 0.6))
        lento = ''
        if largo < seg:  # clip corto (p. ej. yate, 2.4 s): cámara lenta hasta 1.6x y, si aún falta, se sostiene el último cuadro
            factor = min(seg / largo, 1.6)
            lento = f'setpts={factor:.3f}*PTS,tpad=stop_mode=clone:stop_duration={max(0.0, seg - largo * factor) + 0.1:.2f},'
        ff('-ss', f'{ini:.2f}', '-i', fuente, '-t', f'{seg:.2f}', '-vf',
           lento + 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30', '-an', '-c:v', 'libx264',
           '-crf', '18', '-pix_fmt', 'yuv420p', salida)
    else:
        mov = MOVS[k % len(MOVS)].replace('{n}', str(n))
        ff('-loop', '1', '-i', fuente, '-vf', f"scale=2160:-2,crop=2160:3840,zoompan={mov}:d={n}:s=1080x1920:fps=30",
           '-t', f'{seg:.2f}', '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', salida)


def fondo(c, lista, salida, tmp, pedidos=None):
    """Un fondo distinto por tarjeta (cortes al ritmo del texto). Lo menos usado primero, sin repetir dentro del Reel."""
    if pedidos:
        fuentes, uso = pedidos, None
    else:
        fuentes, uso = biblioteca()
    if not fuentes:
        p = c.get('portada') or {}
        fuentes = [os.path.join(RAIZ, p.get('foto_reel') or p.get('foto'))]
    partes = []
    for k, item in enumerate(lista):
        f = fuentes[k % len(fuentes)]
        parte = os.path.join(tmp, f'b{k:02d}.mp4')
        tramo(f, item[4], parte, k)
        partes.append(parte)
        if uso is not None:
            clave = os.path.relpath(f, RAIZ)
            uso[clave] = uso.get(clave, 0) + 1
    if uso is not None:
        os.makedirs(os.path.dirname(USO), exist_ok=True)
        json.dump(uso, open(USO, 'w'), ensure_ascii=False, indent=1)
    lst = os.path.join(tmp, 'lista.txt')
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in partes))
    ff('-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', salida)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cid = sys.argv[1]
    pedidos = sys.argv[sys.argv.index('--clips') + 1].split(',') if '--clips' in sys.argv else None
    c = next((x for x in json.load(open(os.path.join(RAIZ, 'contenido', 'carruseles.json')))['carruseles'] if x['id'] == cid), None)
    if not c:
        sys.exit(f'No existe el carrusel {cid}')
    if c.get('estado') not in ('listo', 'programado', 'publicado'):
        sys.exit(f'{cid} está en "{c.get("estado")}": solo se hacen Reels de carruseles ya verificados')
    carpeta = os.path.join(RAIZ, 'carruseles', cid)
    os.makedirs(carpeta, exist_ok=True)
    lista = tarjetas_de(c)
    total = sum(x[4] for x in lista)
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, 'fondo.mp4')
        fondo(c, lista, base, tmp, [p if os.path.isabs(p) else os.path.join(RAIZ, p) for p in pedidos] if pedidos else None)
        entradas, filtros, t, previo = ['-i', base], [], 0.0, '0:v'
        for i, (titulo, linea, etiqueta, grande, seg) in enumerate(lista):
            png = os.path.join(tmp, f't{i:02d}.png')
            tarjeta(titulo, linea, png, etiqueta, grande)
            entradas += ['-i', png]
            filtros.append(f"[{previo}][{i + 1}:v]overlay=0:0:enable='between(t,{t:.2f},{t + seg:.2f})'[v{i}]")
            previo, t = f'v{i}', t + seg
        sin_audio = os.path.join(carpeta, 'reel-texto.mp4')
        ff(*entradas, '-filter_complex', ';'.join(filtros), '-map', f'[{previo}]', '-c:v', 'libx264', '-crf', '18',
           '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '30', '-movflags', '+faststart', sin_audio)
    # Instagram rechaza un Reel sin pista de audio (error 2207082, 12-nov-2026): se le pone una pista muda; la canción
    # en tendencia la pone Instagram encima (ig_reel_musica.py --video reel-texto.mp4).
    con_mudo = sin_audio.replace('.mp4', '-tmp.mp4')
    ff('-i', sin_audio, '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100', '-map', '0:v', '-map', '1:a',
       '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest', con_mudo)
    os.replace(con_mudo, sin_audio)
    pistas = sorted(glob.glob(os.path.join(RAIZ, 'assets', 'musica', '*.mp3')))
    con_musica = os.path.join(carpeta, 'reel-texto-musica.mp4')
    if pistas:
        pista = pistas[sum(map(ord, cid)) % len(pistas)]
        ff('-i', sin_audio, '-i', pista, '-filter_complex', f"[1:a]volume=0.5,afade=t=out:st={total - 1.2:.2f}:d=1.2[a]",
           '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', con_musica)
    print(f'ok {cid}: {len(lista)} tarjetas, {total:.1f} s → {sin_audio}' + (f' y {con_musica}' if pistas else ''))


if __name__ == '__main__':
    main()
