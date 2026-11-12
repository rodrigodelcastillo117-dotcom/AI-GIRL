"""Reel de texto en pantalla con clips de Victoria (Rodrigo, 12-nov-2026: "sácale jugo total a Everygen").

Convierte un carrusel YA VERIFICADO en un video vertical de ~15-20 s: Victoria y Capital en movimiento (clips sin voz
de assets/broll/, hechos con los créditos de Everygen/OpenArt) y encima el gancho, los datos y el cierre del carrusel en
letra grande. No usa Replicate ni voz: es otro formato para el mismo contenido (TODO SE ADAPTA) y suma volumen.

Uso: python scripts/reel_texto.py <id_carrusel> [--clips a.mp4,b.mp4]
Salida en carruseles/<id>/:
  reel-texto.mp4          sin audio: Instagram (ig_reel_musica.py <id> --video reel-texto.mp4 le pone música en tendencia)
  reel-texto-musica.mp4   con música de fondo de assets/musica/: TikTok, YouTube Shorts y Facebook (publer.py)
Sin clips en assets/broll/ usa la foto de la portada con un acercamiento lento (sirve, pero el clip se ve mejor).
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


def fondo(c, clips, total, salida, tmp):
    """Clips de b-roll uno tras otro (cortes cada ~4 s) hasta cubrir el total; sin clips, la portada con acercamiento lento."""
    if not clips:
        foto = os.path.join(RAIZ, (c.get('portada') or {}).get('foto_reel') or (c.get('portada') or {}).get('foto'))
        n = int(total * 30)
        ff('-loop', '1', '-i', foto, '-vf', f"scale=1260:-2,crop=1080:1920,zoompan=z='min(zoom+0.0006,1.15)':d={n}:s=1080x1920:fps=30",
           '-t', f'{total:.2f}', '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', salida)
        return
    partes, t, k = [], 0.0, 0
    while t < total:
        clip = clips[k % len(clips)]
        largo = min(4.2, duracion(clip), total - t + 0.05)
        parte = os.path.join(tmp, f'b{k:02d}.mp4')
        ff('-i', clip, '-t', f'{largo:.2f}', '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30',
           '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', parte)
        partes.append(parte)
        t += largo
        k += 1
    lista = os.path.join(tmp, 'lista.txt')
    open(lista, 'w').write(''.join(f"file '{p}'\n" for p in partes))
    ff('-f', 'concat', '-safe', '0', '-i', lista, '-t', f'{total:.2f}', '-c', 'copy', salida)


def elegir_clips(cid, pedidos):
    if pedidos:
        return [p if os.path.isabs(p) else os.path.join(RAIZ, p) for p in pedidos]
    todos = sorted(glob.glob(os.path.join(RAIZ, 'assets', 'broll', '*.mp4')))
    random.Random(cid).shuffle(todos)  # cada carrusel con su propia mezcla, siempre la misma para el mismo id
    return todos[:5]


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
        fondo(c, elegir_clips(cid, pedidos), total, base, tmp)
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
    pistas = sorted(glob.glob(os.path.join(RAIZ, 'assets', 'musica', '*.mp3')))
    con_musica = os.path.join(carpeta, 'reel-texto-musica.mp4')
    if pistas:
        pista = pistas[sum(map(ord, cid)) % len(pistas)]
        ff('-i', sin_audio, '-i', pista, '-filter_complex', f"[1:a]volume=0.5,afade=t=out:st={total - 1.2:.2f}:d=1.2[a]",
           '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', con_musica)
    print(f'ok {cid}: {len(lista)} tarjetas, {total:.1f} s → {sin_audio}' + (f' y {con_musica}' if pistas else ''))


if __name__ == '__main__':
    main()
