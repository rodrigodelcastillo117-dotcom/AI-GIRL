"""Voz de Victoria para los videos de carrusel. Desde el 4-nov-2026 cada frase la dice primero una voz mexicana nativa
(Edge es-MX, la arma carrusel_video.py en "base") y aquí se convierte al timbre de Victoria con ChatterboxVC: el clon
directo pronunciaba mal "México" y "aguinaldo". Si la convertida no pasa la revisión, se usa el clon directo, que clona la voz de sus videos
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
# Rodrigo, 9-nov-2026 ("más femenina, que vaya con la cara de Victoria"), eligió la "E": se clona la voz de sus videos
# recientes (audio del video 18, voz cálida e íntima) y se dice más suave. La de antes: assets/voz-referencia.mp3.
REFERENCIA = os.path.join(RAIZ, 'assets', 'voz-referencia-intima.wav')
ESTILO = {'exaggeration': 0.4, 'cfg_weight': 0.35}  # más suave y pausada (tono medio ~244 Hz contra 217 de antes)
INTENTOS = 3
PARECIDO_TEXTO, PARECIDO_VOZ, PARECIDO_VOZ_MX = 0.85, 0.80, 0.82  # la convertida midió 0.88 el 4-nov; en las pruebas del 31-oct: frases buenas 0.93-1.0 y voz 0.90-0.95


def normal(texto):
    """Minúsculas, sin acentos ni signos y con los números en letra (Whisper escribe "regla 1")."""
    texto = texto.lower().replace('%', ' por ciento ').replace('$', ' ')
    texto = re.sub(r'(\d)[.,](\d{3})', r'\1\2', texto)  # "4.500" y "4,500" son cuatro mil quinientos
    texto = re.sub(r'\d+', lambda m: ' ' + num2words(int(m.group()), lang='es') + ' ', texto)
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-zñ ]', ' ', texto).split()


def parecido_texto(esperado, oido):
    """Parecido 0-1; vale 0 si dijo 2+ palabras de más seguidas ("... que nadie te explica. Un deat") o si una palabra
    de 4+ letras del texto no se oye ("Soma" por "Suma"): pasó con 0.90-0.92 el 5-nov-2026."""
    e, o = normal(esperado), normal(oido)
    comparar = difflib.SequenceMatcher(None, o, e)
    for op, i1, i2, j1, j2 in comparar.get_opcodes():
        if op in ('delete', 'replace') and i2 - i1 >= 2 and i2 - i1 > (j2 - j1) + 1:
            return 0.0
    for palabra in {x for x in e if len(x) >= 4} - set(o):
        if not (palabra.endswith('s') and palabra[:-1] in o):
            return min(comparar.ratio(), PARECIDO_TEXTO - 0.01)
    return comparar.ratio()


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

    vc = None
    fallas = []
    for f in frases:
        if f.get('base'):  # voz mexicana nativa convertida al timbre de Victoria (4-nov-2026)
            if vc is None:
                from chatterbox.vc import ChatterboxVC
                vc = ChatterboxVC.from_pretrained(device='cpu')
            wav = vc.generate(f['base'], target_voice_path=referencia)
            audio_16k = librosa.resample(wav.squeeze(0).numpy(), orig_sr=vc.sr, target_sr=16000)
            dicho = ' '.join(s.text.strip() for s in oido.transcribe(audio_16k, language='es')[0])
            texto_ok, voz_ok = parecido_texto(f['texto'], dicho), float(np.dot(voz_victoria, huella(audio_16k)))
            print(f'{os.path.basename(f["salida"])} (mexicana convertida): texto {texto_ok:.2f}, voz {voz_ok:.2f} | {dicho}', flush=True)
            if texto_ok >= PARECIDO_TEXTO and voz_ok >= PARECIDO_VOZ_MX:
                crudo = f['salida'] + '.wav'
                torchaudio.save(crudo, wav, vc.sr)
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', crudo, '-af', 'loudnorm=I=-16:TP=-1.5', '-ar', '44100',
                                '-b:a', '160k', f['salida']], check=True)
                os.remove(crudo)
                continue
            print('  no pasó: se hace con el clon directo', flush=True)
        mejor = None
        for intento in range(INTENTOS):
            torch.manual_seed(1000 + intento)
            wav = modelo.generate(f['texto'], language_id='es', audio_prompt_path=referencia, **ESTILO)
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
