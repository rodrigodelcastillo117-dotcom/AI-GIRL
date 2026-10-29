"""Normalización de texto compartida por qa_audio.py y frases_a_tiempos.py."""
import re
import unicodedata

from num2words import num2words


def normaliza(texto):
    """Minúsculas, sin acentos ni puntuación, con los números escritos en palabras."""
    def numero(m):
        palabras = num2words(int(m.group(1).replace(',', '')), lang='es')
        return palabras + (' por ciento' if m.group(2) else '')
    texto = re.sub(r'(\d[\d,]*)\s*(%)?', numero, texto)
    texto = unicodedata.normalize('NFD', texto.lower())
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return ' '.join(re.sub(r'[^a-z ]', ' ', texto).split())
