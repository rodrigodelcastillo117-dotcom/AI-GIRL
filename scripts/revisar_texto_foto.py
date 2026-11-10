"""¿La foto tiene letras? (Rodrigo, 10-nov-2026: un calendario de fondo decía "January" en la portada de c64: "que no
vuelva a pasar"). Las fotos de Victoria (assets/fotos/) no deben llevar texto legible: ni calendarios, ni letreros, ni
pantallas, ni portadas de libros. El texto del carrusel lo pone carrusel.py, no la foto.

Uso: python revisar_texto_foto.py <foto.jpg> [...]     sale con error si alguna foto tiene palabras legibles
     python revisar_texto_foto.py todas                  revisa todas las de assets/fotos/

Lee con tesseract (inglés y español) y solo cuenta palabras de 3+ letras con confianza alta: el ruido de texturas
(cortinas, plantas) sale con confianza baja. Si tesseract no está instalado: apt-get install -y tesseract-ocr
tesseract-ocr-spa (PIPELINE paso 0).
"""
import csv
import glob
import io
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIANZA = 85
PALABRA = re.compile(r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3,}$')


def palabras(foto):
    salida = subprocess.run(['tesseract', foto, '-', '-l', 'eng+spa', '--psm', '11', 'tsv'],
                            capture_output=True, text=True).stdout
    filas = csv.DictReader(io.StringIO(salida), delimiter='\t', quoting=csv.QUOTE_NONE)
    return [(f['text'], round(float(f['conf']))) for f in filas
            if f.get('text') and PALABRA.match(f['text']) and float(f.get('conf') or -1) >= CONFIANZA]


def main():
    fotos = sys.argv[1:]
    if not fotos:
        sys.exit(__doc__)
    if fotos == ['todas']:
        fotos = sorted(glob.glob(os.path.join(RAIZ, 'assets', 'fotos', '*.jpg')) + glob.glob(os.path.join(RAIZ, 'assets', 'fotos', '*.png')))
    con_texto = {}
    for foto in fotos:
        encontradas = palabras(foto)
        if encontradas:
            con_texto[foto] = encontradas
    for foto, encontradas in con_texto.items():
        print(f"TEXTO EN LA FOTO {os.path.relpath(foto, RAIZ)}: " + ', '.join(f'"{p}" ({c}%)' for p, c in encontradas))
    if con_texto:
        sys.exit('ERROR: hay fotos con letras legibles: rehazlas (o recórtalas) antes de usarlas en un carrusel o video.')
    print(f'ok: {len(fotos)} foto(s) sin texto legible.')


if __name__ == '__main__':
    main()
