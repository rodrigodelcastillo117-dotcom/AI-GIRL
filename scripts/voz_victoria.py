"""Voz de Victoria para los videos de carrusel (solo YouTube): clona la voz de sus videos
(assets/voz-referencia.mp3) con Chatterbox Multilingual de Resemble AI (licencia MIT, corre en CPU, 0 créditos).
Rodrigo eligió esta voz ("B") el 31-oct-2026 frente a la de Edge TTS, que sonaba "muy AI".

Uso, con el python del entorno de voz (PIPELINE paso 0, VOZ_PYTHON):
  $VOZ_PYTHON scripts/voz_victoria.py lista.json
  lista.json: [{"texto": "...", "salida": "carruseles/c01/vozv-00.mp3"}, ...]

El clon a veces se come o cambia una palabra, al azar ("Sin correglas" por "Cinco reglas"). Por eso cada
frase se transcribe con faster-whisper y se compara con el texto: si sale perfecta se queda; si no, se
repite con otra semilla hasta INTENTOS veces y se queda la mejor, que debe llegar a PARECIDO_TEXTO y sonar a
Victoria (PARECIDO_VOZ con su voz de referencia). Si ninguna pasa, sale con error (regla 8): se reescribe esa
frase (los nombres en inglés, como suenan: "Uórren Bófet") y se vuelve a correr.
"""
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

import librosa
import numpy as np
import torch
import torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from faster_whisper import WhisperModel
from num2words import num2words

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCIA = os.path.join(RAIZ, 'assets', 'voz-referencia.mp3')
INTENTOS = 3
PARECIDO_TEXTO, PARECIDO_VOZ = 0.85, 0.80  # en las pruebas del 31-oct: frases buenas 0.93-1.0 y voz 0.90-0.95


def normal(texto):
    """Minúsculas, sin acentos ni signos y con los números en letra (Whisper escribe "regla 1")."""
    texto = re.sub(r'\d+', lambda m: ' ' + num2words(int(m.group()), lang='es') + ' ', texto.lower())
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-zñ ]', ' ', texto).split()


def parecido_texto(esperado, oido):
    return difflib.SequenceMatcher(None, normal(esperado), normal(oido)).ratio()


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    frases = json.load(open(sys.argv[1]))
    torch.set_num_threads(os.cpu_count() or 4)
    modelo = ChatterboxMultilingualTTS.from_pretrained(device='cpu')
    oido = WhisperModel('small', device='cpu', compute_type='int8')
    referencia = os.path.join(tempfile.mkdtemp(), 'ref.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', REFERENCIA, '-ac', '1', '-ar', '24000', referencia], check=True)

    def huella(audio_16k):
        e = modelo.ve.embeds_from_wavs([audio_16k], sample_rate=16000)[0]
        return e / np.linalg.norm(e)
    voz_victoria = huella(librosa.load(referencia, sr=16000)[0])

    fallas = []
    for f in frases:
        mejor = None
        for intento in range(INTENTOS):
            torch.manual_seed(1000 + intento)
            wav = modelo.generate(f['texto'], language_id='es', audio_prompt_path=referencia)
            audio_16k = librosa.resample(wav.squeeze(0).numpy(), orig_sr=modelo.sr, target_sr=16000)
            dicho = ' '.join(s.text.strip() for s in oido.transcribe(audio_16k, language='es')[0])
            nota = (parecido_texto(f['texto'], dicho), float(np.dot(voz_victoria, huella(audio_16k))))
            if mejor is None or nota > mejor[0]:
                mejor = (nota, wav, dicho)
            if nota[0] == 1.0 and nota[1] >= PARECIDO_VOZ:
                break
        (texto_ok, voz_ok), wav, dicho = mejor
        print(f'{os.path.basename(f["salida"])}: texto {texto_ok:.2f}, voz {voz_ok:.2f} | {dicho}', flush=True)
        if texto_ok < PARECIDO_TEXTO or voz_ok < PARECIDO_VOZ:
            fallas.append(f'"{f["texto"]}" se oyó "{dicho}" (texto {texto_ok:.2f}, voz {voz_ok:.2f})')
            continue
        crudo = f['salida'] + '.wav'
        torchaudio.save(crudo, wav, modelo.sr)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', crudo, '-af', 'loudnorm=I=-16:TP=-1.5', '-ar', '44100',
                        '-b:a', '160k', f['salida']], check=True)
        os.remove(crudo)
    if fallas:
        sys.exit('ERROR: estas frases no salieron bien en ' + str(INTENTOS) + ' intentos; reescríbelas y repite:\n'
                 + '\n'.join(fallas))


if __name__ == '__main__':
    main()
