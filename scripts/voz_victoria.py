"""Voz de Victoria para los videos de carrusel.

DESDE EL 9-NOV-2026 (Rodrigo: "déjala para siempre"): su voz REAL de los videos clonada con MiniMax en Replicate
(config.json → voz_victoria, con_minimax). Lo de abajo (Chatterbox) queda solo como historia si voz_victoria.motor cambia.
 Desde el 4-nov-2026 cada frase la dice primero una voz mexicana nativa
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
# Muestra de su voz REAL (audio del video 18). Desde el 9-nov-2026 la usa MiniMax (con_minimax); Chatterbox solo si
# voz_victoria.motor cambia. La de antes: assets/voz-referencia.mp3.
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


def _replicate(modelo, entrada):
    """Corre un modelo de Replicate y regresa su salida (espera hasta que termine)."""
    import time
    import urllib.request
    cab = {'Authorization': f"Bearer {os.environ['REPLICATE_API_TOKEN']}", 'Content-Type': 'application/json', 'Prefer': 'wait=60'}
    req = urllib.request.Request(f'https://api.replicate.com/v1/models/{modelo}/predictions',
                                 data=json.dumps({'input': entrada}).encode(), headers=cab, method='POST')
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'Replicate {e.code}: {e.read().decode()[:300]}')
    while r.get('status') in ('starting', 'processing'):
        time.sleep(2)
        r = json.loads(urllib.request.urlopen(urllib.request.Request(r['urls']['get'], headers=cab), timeout=60).read())
    if r.get('status') != 'succeeded':
        raise RuntimeError(f"Replicate {r.get('status')}: {r.get('error')}")
    return r['output']


def clonar_de_nuevo(voz):
    """Vuelve a clonar la voz de Victoria de su muestra (por si MiniMax borró el clon) y guarda el voice_id nuevo."""
    import base64
    mp3 = os.path.join(tempfile.mkdtemp(), 'muestra.mp3')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(RAIZ, voz['muestra']), '-ac', '1', '-ar', '44100', '-b:a', '192k', mp3], check=True)
    salida = _replicate('minimax/voice-cloning', {'voice_file': 'data:audio/mpeg;base64,' + base64.b64encode(open(mp3, 'rb').read()).decode(),
                                                  'model': voz['modelo'].split('/')[-1], 'need_noise_reduction': True,
                                                  'need_volume_normalization': True})
    ruta = os.path.join(RAIZ, 'contenido', 'config.json')
    config = json.load(open(ruta))
    config['voz_victoria']['voice_id'] = salida['voice_id']
    json.dump(config, open(ruta, 'w'), ensure_ascii=False, indent=1)
    print(f"clon nuevo de la voz de Victoria: {salida['voice_id']}", flush=True)
    return salida['voice_id']


def con_minimax(frases, voz):
    """La voz de Victoria desde el 9-nov-2026: su voz REAL clonada con MiniMax (config.json → voz_victoria). Cada frase se
    revisa con faster-whisper como antes; si no sale bien en INTENTOS, error (no se cambia a otra voz)."""
    import urllib.request
    oido = WhisperModel('small', device='cpu', compute_type='int8')
    fallas = []
    for f in frases:
        mejor = None
        for intento in range(INTENTOS):
            entrada = {'text': f['texto'], 'voice_id': voz['voice_id'], 'language_boost': voz.get('language_boost', 'Spanish'),
                       'emotion': voz.get('emotion', 'auto'), 'speed': voz.get('speed', 1.0), 'sample_rate': 44100, 'bitrate': 128000}
            try:
                url = _replicate(voz['modelo'], entrada)
            except RuntimeError as e:
                if 'voice' in str(e).lower() and intento == 0:  # el clon ya no existe: se vuelve a clonar de la muestra
                    voz['voice_id'] = clonar_de_nuevo(voz)
                    continue
                raise
            crudo = f"{f['salida']}.{intento}.minimax.mp3"
            urllib.request.urlretrieve(url, crudo)
            audio_16k = librosa.load(crudo, sr=16000)[0]
            dicho = ' '.join(s.text.strip() for s in oido.transcribe(audio_16k, language='es')[0])
            nota = parecido_texto(f['texto'], dicho)
            if mejor is None or nota > mejor[0]:
                if mejor:
                    os.remove(mejor[1])
                mejor = (nota, crudo, dicho)
            else:
                os.remove(crudo)
            if nota >= 0.98:
                break
        if not mejor:
            fallas.append(f'"{f["texto"]}": MiniMax no respondió')
            continue
        nota, crudo, dicho = mejor
        print(f'{os.path.basename(f["salida"])} (voz real, MiniMax): texto {nota:.2f} | {dicho}', flush=True)
        if nota < PARECIDO_TEXTO:
            os.remove(crudo)
            fallas.append(f'"{f["texto"]}" se oyó "{dicho}" (texto {nota:.2f})')
            continue
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', crudo, '-af', 'loudnorm=I=-16:TP=-1.5', '-ar', '44100',
                        '-b:a', '160k', f['salida']], check=True)
        os.remove(crudo)
    if fallas:
        sys.exit('ERROR: estas frases no salieron bien en ' + str(INTENTOS) + ' intentos; reescríbelas y repite:\n'
                 + '\n'.join(fallas))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    frases = json.load(open(sys.argv[1]))
    voz = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json'))).get('voz_victoria') or {}
    if voz.get('motor') == 'minimax':
        if not os.environ.get('REPLICATE_API_TOKEN'):
            sys.exit('ERROR: falta REPLICATE_API_TOKEN: sin él no se puede hacer la voz de Victoria (no se usa otra voz).')
        return con_minimax(frases, voz)
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
