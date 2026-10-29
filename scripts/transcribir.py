import sys, json, subprocess
import numpy as np
from faster_whisper import WhisperModel
raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', sys.argv[1], '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
m = WhisperModel('small', device='cpu', compute_type='int8')
segs, info = m.transcribe(audio, language='es', word_timestamps=True)
words = [{'w': w.word.strip(), 'start': round(w.start, 2), 'end': round(w.end, 2)} for s in segs for w in s.words]
print(' '.join(x['w'] for x in words))
json.dump(words, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print('palabras:', len(words), '| primera:', words[0] if words else None, '| ultima:', words[-1] if words else None)
