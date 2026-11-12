"""Arma de punta a punta un short de Victoria en formato escena, ya con su video de Replicate hecho
(videos/video-<id>.mp4 + videos/video-<id>-voz.mp3). Rodrigo, 12-nov-2026: "todo listo, fluido, la mejor calidad".

Uso: python3 scripts/armar_escena.py <id>

1. Revisión completa (PIPELINE paso 5) sobre el video de Replicate: Whisper (con el python de voz), qa_audio,
   qa_labios, qa_sync y hoja de 10 cuadros en videos/qa/<id>-cuadros.jpg. Si qa_labios mide (>= 4 palabras p/b/m/v y
   desfase <= 100 ms) manda qa_labios; qa_sync solo decide cuando qa_labios no puede medir (como largo.py).
2. Tiempos de subtítulos alineados por palabras (frases_a_tiempos.py).
3. Acción como pausa real (insertar_accion.py) si el plan trae "insertos": [{"frase": N, "broll": ..., "segundos": 3}].
4. naturalizar → subtitular → título (texto_pantalla o seo.titulo) → cierre (pregunta + llamado_cierre).
Sale videos/video-<id>-FINAL.mp4 y deja el resultado de la revisión en plan.json → qa. No publica.
Los cuadros los mira una persona o el agente ANTES de publicar (misma cara y pelo rojo en todo el video).
"""
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOZ_PY = os.environ.get('VOZ_PYTHON', '/tmp/voz/bin/python')


def correr(*args, py=sys.executable, salida=False):
    r = subprocess.run([py, *args], cwd=RAIZ, capture_output=True, text=True)
    if salida:
        return r
    if r.returncode != 0:
        sys.exit(f'ERROR en {args[0]}:\n{(r.stdout + r.stderr)[-1500:]}')
    return r


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    vid = sys.argv[1]
    ruta_plan = os.path.join(RAIZ, 'contenido', 'plan.json')
    plan = json.load(open(ruta_plan))
    v = next(x for x in plan['videos'] if x['id'] == vid)
    base = os.path.join('videos', f'video-{vid}')
    qa_dir = os.path.join(RAIZ, 'videos', 'qa')
    os.makedirs(qa_dir, exist_ok=True)
    pal = os.path.join(qa_dir, f'{vid}-palabras.json')
    correr('scripts/transcribir.py', base + '.mp4', pal, py=VOZ_PY)
    p = json.load(open(pal))
    while len(p) > 1 and p[-1]['end'] - p[-1]['start'] <= 0.02:  # alucinación de Whisper al final
        p.pop()
    json.dump(p, open(pal, 'w'), ensure_ascii=False)
    cfg = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    a = correr('scripts/qa_audio.py', pal, v['guion'], str(cfg.get('similitud_minima_audio', 0.85)), py=VOZ_PY, salida=True)
    if a.returncode != 0:  # Whisper small se equivoca solo (M4: "retiros", "humas"); se confirma con medium antes de tirarlo
        pal_m = os.path.join(qa_dir, f'{vid}-palabras-medium.json')
        correr('scripts/transcribir.py', base + '.mp4', pal_m, 'medium', py=VOZ_PY)
        pm = json.load(open(pal_m))
        while len(pm) > 1 and pm[-1]['end'] - pm[-1]['start'] <= 0.02:
            pm.pop()
        json.dump(pm, open(pal_m, 'w'), ensure_ascii=False)
        a2 = correr('scripts/qa_audio.py', pal_m, v['guion'], str(cfg.get('similitud_minima_audio', 0.85)), py=VOZ_PY,
                    salida=True)
        if a2.returncode == 0:
            a = a2
    l = correr('scripts/qa_labios.py', base + '.mp4', pal, salida=True)
    s = correr('scripts/qa_sync.py', base + '.mp4', os.path.join(qa_dir, f'{vid}-sync.json'), salida=True)
    ultima = lambda r: [x for x in r.stdout.strip().splitlines() if x.strip()][-1:]  # noqa: E731 (stderr = logs de TF)
    labios_mide = 'SIN MEDIR' not in l.stdout
    labios_ok = l.returncode == 0 and labios_mide
    sync_ok = s.returncode == 0
    lab_ok = labios_ok or (not labios_mide and sync_ok)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', base + '.mp4', '-vf',
                    'fps=10/' + str(max(1.0, float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                    'format=duration', '-of', 'csv=p=0', base + '.mp4'], capture_output=True, text=True, cwd=RAIZ).stdout))) +
                    ',scale=180:-2,tile=10x1', '-frames:v', '1', os.path.join(qa_dir, f'{vid}-cuadros.jpg')], cwd=RAIZ,
                   check=True)
    v['qa'] = {**(v.get('qa') or {}), 'audio': 'OK' if a.returncode == 0 else 'FALLA ' + ' '.join(ultima(a)),
               'labios': ' '.join(ultima(l)), 'sync': ' '.join(ultima(s)),
               'cuadros': f'videos/qa/{vid}-cuadros.jpg (revisar a ojo)'}
    json.dump(plan, open(ruta_plan, 'w'), ensure_ascii=False, indent=1)
    if a.returncode != 0 or not lab_ok:
        sys.exit(f"QA FALLA {vid}: {v['qa']}")
    frases = os.path.join(qa_dir, f'{vid}-frases.json')
    json.dump(v['subtitulos'], open(frases, 'w'), ensure_ascii=False)
    tiempos = os.path.join(qa_dir, f'{vid}-tiempos.json')
    correr('scripts/frases_a_tiempos.py', pal, frases, tiempos, py=VOZ_PY)
    entrada = base + '.mp4'
    for ins in v.get('insertos') or []:
        correr('scripts/insertar_accion.py', entrada, tiempos, str(ins['frase']), ins['broll'], base + '-accion.mp4',
               str(ins.get('segundos', 3)))
        entrada, tiempos = base + '-accion.mp4', base + '-accion-tiempos.json'
        break  # una sola pausa por short (más se siente editado)
    correr('scripts/naturalizar.py', entrada, base + '-nat.mp4')
    clave = ','.join(v.get('palabras_clave') or [])
    correr('scripts/subtitular.py', base + '-nat.mp4', tiempos, base + '-SUBTITULADO.mp4', clave, py=VOZ_PY)
    titulo = (v.get('texto_pantalla') or v['seo']['titulo']).split(' · ')[0]
    tmp = os.path.join(qa_dir, f'{vid}-titulo.mp4')
    correr('scripts/titulo_pantalla.py', base + '-SUBTITULADO.mp4', titulo, tmp)
    os.replace(tmp, os.path.join(RAIZ, base + '-SUBTITULADO.mp4'))
    correr('scripts/cierre_pantalla.py', base + '-SUBTITULADO.mp4', vid, base + '-FINAL.mp4')
    v['archivo'] = base + '-FINAL.mp4'
    json.dump(plan, open(ruta_plan, 'w'), ensure_ascii=False, indent=1)
    print(f'ok {base}-FINAL.mp4 | qa: {v["qa"]}')


if __name__ == '__main__':
    main()
