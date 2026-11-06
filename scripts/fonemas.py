"""Escribe los SONIDOS que dice una voz (no las palabras): distingue "a-g-i-naldo" de "a-gw-i-naldo" o "a-x-i-nado",
que Whisper no distingue. Uso: VOZ_PYTHON -I scripts/fonemas.py audio.wav ... (wav2vec2 xlsr espeak, 6-nov-2026)."""
import sys, json, librosa, torch
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC
from huggingface_hub import hf_hub_download
mid = 'facebook/wav2vec2-xlsr-53-espeak-cv-ft'
fe = Wav2Vec2FeatureExtractor.from_pretrained(mid); model = Wav2Vec2ForCTC.from_pretrained(mid)
vocab = {v: k for k, v in json.load(open(hf_hub_download(mid, 'vocab.json'))).items()}
for f in sys.argv[1:]:
    a = librosa.load(f, sr=16000)[0]
    with torch.no_grad():
        ids = model(fe(a, sampling_rate=16000, return_tensors='pt').input_values).logits.argmax(-1)[0].tolist()
    out, prev = [], None
    for i in ids:
        if i != prev and vocab.get(i) not in ('<pad>', None):
            out.append(vocab[i])
        prev = i
    print(f.split('/')[-1], '|', ' '.join(out), flush=True)
