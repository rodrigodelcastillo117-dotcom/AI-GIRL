"""Arma el banner de YouTube (2560x1440) con texto dentro de la franja segura.

Uso: python banner_youtube.py foto.png salida.jpg [x_texto]

La franja visible en todos los dispositivos mide 1546x423 px centrada.
Genera también salida-guia.jpg con la franja marcada para revisarla.
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 2560, 1440
SAFE = ((W - 1546) // 2, (H - 423) // 2, (W + 1546) // 2, (H + 423) // 2)
FUENTES = '/usr/share/fonts/opentype/inter/'
DORADO = (230, 180, 60)

foto, salida = sys.argv[1], sys.argv[2]
x_texto = int(sys.argv[3]) if len(sys.argv) > 3 else 1430

img = Image.open(foto).convert('RGB')
escala = max(W / img.width, H / img.height)
img = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
izq, arr = (img.width - W) // 2, (img.height - H) // 2
img = img.crop((izq, arr, izq + W, arr + H))

# Degradado oscuro desde la zona del texto hacia la derecha, para que se lea sobre fondos claros
degradado = Image.new('L', (W, H), 0)
inicio = x_texto - 260
for x in range(inicio, W):
    degradado.paste(min(150, int(150 * (x - inicio) / 420)), (x, 0, x + 1, H))
img.paste(Image.new('RGB', (W, H), (12, 10, 8)), (0, 0), degradado)

titulo = ImageFont.truetype(FUENTES + 'InterDisplay-SemiBold.otf', 112)
subtitulo = ImageFont.truetype(FUENTES + 'InterDisplay-Medium.otf', 50)
linea3 = ImageFont.truetype(FUENTES + 'Inter-Medium.otf', 34)

lineas = [
    ('VICTORIA', titulo, (255, 255, 255), 12),
    ('THE CEO', subtitulo, DORADO, 22),
    ('Negocio · Dinero · Mente fuerte', linea3, (255, 255, 255), 2),
    ('Nuevo video cada día', linea3, DORADO, 2),
]
alturas = [f.getbbox(t)[3] for t, f, _, _ in lineas]
separacion = 26
total = sum(alturas) + separacion * (len(lineas) - 1)
y = (H - total) // 2

# Sombra suave para que el texto se lea sobre cualquier fondo
sombra = Image.new('L', (W, H), 0)
ds = ImageDraw.Draw(sombra)
yy = y
for (t, f, _, esp), alto in zip(lineas, alturas):
    ds.text((x_texto, yy), t, font=f, fill=200)
    yy += alto + separacion
sombra = sombra.filter(ImageFilter.GaussianBlur(14))
img.paste(Image.new('RGB', (W, H), (0, 0, 0)), (0, 0), sombra.point(lambda v: int(v * 0.55)))

d = ImageDraw.Draw(img)
for (t, f, color, esp), alto in zip(lineas, alturas):
    d.text((x_texto, y), t, font=f, fill=color)
    y += alto + separacion
fin_texto = max(x_texto + f.getbbox(t)[2] for t, f, _, _ in lineas)

img.save(salida, quality=93)

guia = img.copy()
dg = ImageDraw.Draw(guia)
dg.rectangle(SAFE, outline=(0, 160, 255), width=6)
guia.resize((1280, 720)).save(salida.rsplit('.', 1)[0] + '-guia.jpg', quality=85)
print('ok', salida, '| franja segura x', SAFE[0], '-', SAFE[2], '| texto termina en x', fin_texto,
      '(dentro)' if fin_texto <= SAFE[2] else '(SE SALE)')
