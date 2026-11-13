"""Convierte carruseles ya dibujados en video (gratis: Edge TTS + ffmpeg) y arma sus textos de YouTube.

musica <video.mp4> [pista.mp3]: le pone música de fondo bajita (assets/musica/) a un video ya terminado.

Uso: python carrusel_video.py short <id>
         carruseles/<id>/short.mp4 (vertical, máximo 57 s) + titulo.txt, descripcion_youtube.txt,
         tags_youtube.txt para youtube.py subir.
     python carrusel_video.py largo <salida.mp4> <id> [<id>...] [--horizontal]
         Une varios carruseles en un video largo: vertical para TikTok e Instagram (más de 1 minuto),
         --horizontal (1920x1080) para un video largo de YouTube.

Cada diapositiva se queda lo que dura su "voz" más medio segundo de aire. La voz es la de Victoria,
clonada de sus videos con scripts/voz_victoria.py (corre con VOZ_PYTHON, el entorno de voz del paso 0 de
PIPELINE; Rodrigo la eligió el 31-oct-2026). --voz-edge usa es-MX-DaliaNeural de Edge TTS, la de antes,
solo si Rodrigo lo pide: sonaba "muy AI".
"""
import asyncio
import glob
import json
import os
import subprocess
import sys

import certifi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carrusel import RAIZ, cargar  # noqa: E402
from seo import cada, con_ref, errores_titulo, etiquetas, hashtags_para  # noqa: E402

VOZ = 'es-MX-DaliaNeural'
AIRE, MAXIMO_SHORT = 0.5, 57.0
AIRE_SHORT = 0.25  # menos silencio entre diapositivas: cada pausa es un momento para deslizar
NEGRO = '0x0b0b0d'
# Detrás del proxy de la nube, el certificado está en SSL_CERT_FILE; edge-tts solo mira certifi.
_ca = os.environ.get('SSL_CERT_FILE') or os.environ.get('REQUESTS_CA_BUNDLE') or '/root/.ccr/ca-bundle.crt'
if _ca and os.path.exists(_ca):
    certifi.where = lambda: _ca
import edge_tts  # noqa: E402


def duracion(ruta):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', ruta],
                       capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)['format']['duration'])


def voces_victoria(carpeta, voces):
    """vozc-XX.mp3 de las frases que falten, con la voz clonada de Victoria (voz_victoria.py) y su revisión.
    Las palabras difíciles van escritas como se pronuncian (config.json → pronunciacion, guion_para_voz.py).
    Rodrigo (6-nov-2026): "no quiero voz nueva, quiero que pronuncie bien las palabras": se probó una voz mexicana
    convertida al timbre de Victoria (4-nov) y se quitó; se queda su voz y se corrige la pronunciación."""
    from guion_para_voz import para_voz
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    # Qué texto dijo cada audio (11-nov-2026: c65 reusó audios viejos después de cambiar la voz y el short duraba 65 s).
    hechas_ruta = os.path.join(carpeta, 'voces-hechas.json')
    hechas = json.load(open(hechas_ruta)) if os.path.exists(hechas_ruta) else None
    faltan = []
    for i, t in enumerate(voces):
        salida, texto = os.path.join(carpeta, f'vozc-{i:02d}.mp3'), para_voz(t, config)
        viejo = os.path.exists(salida) and hechas is not None and hechas.get(os.path.basename(salida)) not in (None, texto)
        if viejo:
            os.remove(salida)
        if not os.path.exists(salida):
            faltan.append({'texto': texto, 'salida': salida})
    if faltan:
        python = preparar_entorno_voz()
        lista = os.path.join(carpeta, 'voces.json')
        json.dump(faltan, open(lista, 'w'), ensure_ascii=False)
        subprocess.run([python, os.path.join(RAIZ, 'scripts', 'voz_victoria.py'), lista], check=True)
        os.remove(lista)
    json.dump({f'vozc-{i:02d}.mp3': para_voz(t, config) for i, t in enumerate(voces)}, open(hechas_ruta, 'w'), ensure_ascii=False)


LIBRERIAS_VOZ = {'faster_whisper': 'faster-whisper', 'num2words': 'num2words', 'librosa': 'librosa', 'numpy': 'numpy'}


def preparar_entorno_voz():
    """El entorno de voz se repara solo (11-nov-2026: el 10-nov perdió faster-whisper y num2words y fallaron 3 shorts).
    Si no existe, lo crea; si le falta una librería, la instala; y comprueba que importe antes de seguir."""
    python = os.environ.get('VOZ_PYTHON', '/tmp/voz/bin/python')
    if not os.path.exists(python):
        base = os.path.dirname(os.path.dirname(python))
        print(f'Entorno de voz no existe: lo creo en {base}')
        subprocess.run([sys.executable, '-m', 'venv', base], check=True)
    prueba = lambda m: subprocess.run([python, '-c', f'import {m}'], capture_output=True).returncode == 0
    faltan = [paquete for modulo, paquete in LIBRERIAS_VOZ.items() if not prueba(modulo)]
    if faltan:
        print('Entorno de voz incompleto, instalo:', ', '.join(faltan))
        subprocess.run([python, '-m', 'pip', 'install', '-q', *faltan], check=True)
        malos = [m for m in LIBRERIAS_VOZ if not prueba(m)]
        if malos:
            sys.exit(f'ERROR: el entorno de voz sigue sin {", ".join(malos)} después de instalar; revisa la red o pip.')
    return python


def movimiento(segundos):
    """Short vertical que no parezca presentación (3-nov-2026: los shorts de carrusel retienen 18-29% y Victoria
    hablando 92%): la diapositiva se acerca despacio (6% en todo el tramo) y las franjas de arriba y abajo, que eran
    negras, llevan la misma diapositiva desenfocada y oscura."""
    cuadros = max(1, int(segundos * 30))
    return (f"[0:v]split[a][b];"
            f"[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:4,"
            f"eq=brightness=-0.28:saturation=0.8[fondo];"
            f"[b]scale=2160:2700,zoompan=z='1+0.06*on/{cuadros}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d=1:s=1080x1350:fps=30[frente];"
            f"[fondo][frente]overlay=0:285,format=yuv420p[v]")


def tramos(c, horizontal=False, portada=None):
    """Un MP4 por diapositiva (imagen + su voz). Regresa (rutas, segundos totales). portada: otra imagen para
    abrir (la del Reel, 00r.png)."""
    carpeta = os.path.join(RAIZ, 'carruseles', c['id'])
    hojas = sorted(glob.glob(os.path.join(carpeta, '[0-9][0-9].png')))
    if portada:
        hojas[0] = portada
    voces = [c['portada']['voz']] + [d['voz'] for d in c['diapositivas']] + [c['cierre']['voz']]
    if len(hojas) != len(voces):
        sys.exit(f'ERROR: hay {len(hojas)} diapositivas y {len(voces)} voces: corre primero carrusel.py {c["id"]}')
    marco = ('scale=864:1080,pad=1920:1080:528:0' if horizontal else 'scale=1080:1350,pad=1080:1920:0:285') + f':color={NEGRO},format=yuv420p'
    rutas, total = [], 0.0
    edge = '--voz-edge' in sys.argv
    if not edge:
        voces_victoria(carpeta, voces)
    for i, (hoja, texto) in enumerate(zip(hojas, voces)):
        audio = os.path.join(carpeta, f'{"voz" if edge else "vozc"}-{i:02d}.mp3')
        if edge and not os.path.exists(audio):
            asyncio.run(edge_tts.Communicate(texto, VOZ, rate='+5%').save(audio))
        segundos = duracion(audio) + (AIRE if horizontal else AIRE_SHORT)
        total += segundos
        tramo = os.path.join(carpeta, f'tramo-{"h" if horizontal else "v"}-{i:02d}.mp4')
        filtro = ['-vf', marco] if horizontal else ['-filter_complex', movimiento(segundos), '-map', '[v]', '-map', '1:a']
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', hoja, '-i', audio, *filtro,
                        '-af', 'apad', '-t', f'{segundos:.2f}', '-r', '30', '-c:v', 'libx264', '-preset', 'medium',
                        '-crf', '20', '-c:a', 'aac', '-ar', '44100', '-ac', '2', tramo], check=True)
        rutas.append(tramo)
    return rutas, total


def unir(rutas, salida, musica=None):
    lista = salida + '.txt'
    open(lista, 'w').write(''.join(f"file '{os.path.abspath(r)}'\n" for r in rutas))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lista, '-c', 'copy', salida], check=True)
    for r in rutas + [lista]:
        os.remove(r)
    if musica:
        con_musica(salida, musica)


def subtitular(video, c):
    """Subtítulos palabra por palabra en la franja negra de abajo (10-nov-2026: los shorts de carrusel retenían 20-62% en
    YouTube y los videos de Victoria, que ya llevan subtítulos, 70-108%). De 3 en 3 palabras, la que suena en dorado. El
    texto es el escrito de la voz (sin faltas aunque el oído oiga otra cosa); el tiempo de cada palabra se reparte por su
    largo dentro de la duración de su frase."""
    carpeta = os.path.join(RAIZ, 'carruseles', c['id'])
    voces = [c['portada']['voz']] + [d['voz'] for d in c['diapositivas']] + [c['cierre']['voz']]
    ts = lambda t: f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'
    eventos, inicio = [], 0.0
    for i, texto in enumerate(voces):
        audio = os.path.join(carpeta, f'vozc-{i:02d}.mp3')
        largo = duracion(audio)
        palabras = texto.split()
        pesos = [len(p) + 2 for p in palabras]
        habla_ini, habla = inicio + 0.08, max(0.3, largo - 0.18)
        t = habla_ini
        tiempos = []
        for p, w in zip(palabras, pesos):
            d = habla * w / sum(pesos)
            tiempos.append((p, t, t + d))
            t += d
        for j in range(0, len(tiempos), 3):
            grupo = tiempos[j:j + 3]
            fin = tiempos[j + 3][1] if j + 3 < len(tiempos) else grupo[-1][2] + 0.15
            karaoke = ' '.join(r'{\k' + str(max(1, round((b - a) * 100))) + '}' + p for p, a, b in grupo)
            eventos.append(f'Dialogue: 0,{ts(grupo[0][1])},{ts(fin)},Sub,,0,0,0,,{karaoke}')
        inicio += largo + AIRE_SHORT
    ass = video + '.ass'
    open(ass, 'w').write('''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter ExtraBold,84,&H0042C5F5,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,4,2,2,50,50,95,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
''' + '\n'.join(eventos) + '\n')
    tmp = video + '.sub.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vf', f'ass={ass}', '-c:v', 'libx264', '-preset', 'medium',
                    '-crf', '20', '-c:a', 'copy', tmp], check=True)
    os.replace(tmp, video)
    os.remove(ass)


def pista_para(cid):
    """Música de fondo del carrusel (Rodrigo, 9-nov-2026: "el chiste es usar sonidos"): una de assets/musica/*.mp3, la
    misma para el mismo carrusel y rotando entre carruseles. Sin pistas en la carpeta, sin música."""
    pistas = sorted(glob.glob(os.path.join(RAIZ, 'assets', 'musica', '*.mp3')))
    if not pistas or '--sin-musica' in sys.argv:
        return None
    return pistas[sum(map(ord, cid)) % len(pistas)]


def con_musica(video, pista, volumen=0.11):
    """Mete la pista bajita debajo de la voz (que manda), en bucle, con entrada y salida suaves."""
    dur = duracion(video)
    tmp = video + '.musica.mp4'
    filtro = (f'[1:a]volume={volumen},afade=t=in:d=0.6,afade=t=out:st={max(0, dur - 1.2):.2f}:d=1.2[m];'
              '[0:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-stream_loop', '-1', '-i', pista, '-filter_complex', filtro,
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-t', f'{dur:.2f}', tmp], check=True)
    os.replace(tmp, video)


def textos_youtube(c, config):
    """Mismas reglas que los videos (docs/SEO.md): título que empieza con lo que se busca, 2 enlaces
    arriba, preguntas que la gente escribe, 5 hashtags y etiquetas en tres capas."""
    s = c['seo']
    errores = errores_titulo(s['titulo'], s['palabra_clave'], config.get('titulo_max', 45))
    if errores:
        sys.exit(f"ERROR: el título del carrusel {c['id']} \"{s['titulo']}\" " + '; '.join(errores))
    propio = c.get('enlace') or {}
    enlaces = [f'{e}: {u}' for e, u in ((propio.get('etiqueta'), con_ref(propio.get('url'), f"yt-{c['id']}")),
                                        ('📥 Mis 30 reglas de la CEO, gratis', con_ref(config.get('enlace_venta'), f"yt-{c['id']}")),
                                        ('📊 El tablero de la CEO, mi plantilla de dinero', con_ref(config.get('enlace_producto'), f"yt-{c['id']}"))) if u][:2]
    post = '\n'.join(l for l in c['texto_post'].strip().splitlines() if 'enlace en mi perfil' not in l)  # en YouTube va el enlace directo
    if s['palabra_clave'].lower() not in post.split('\n')[0].lower():  # la búsqueda lee la primera línea (docs/SEO.md)
        post = s['palabra_clave'][:1].upper() + s['palabra_clave'][1:] + ': ' + post[:1].lower() + post[1:]
    from seo import sin_errores
    relacionadas = sin_errores([t for t in s.get('tags_concretas', []) if t.lower() not in s['titulo'].lower()],
                               s['titulo'] + ' ' + c['texto_post'])[:8]
    pension = any(k in (s['titulo'] + ' '.join(s.get('tags_concretas', []))).lower()
                  for k in ('pension', 'pensión', 'imss', 'afore', 'jubil', 'retiro', 'modalidad 40', 'semanas cotizadas'))
    razon = config.get('razon_suscribirse', {}).get('pension' if pension else 'otro') or \
        f"Soy Victoria: tu dinero en México, sin rodeos, {cada(config)}. Suscríbete para no perderte el siguiente."
    descripcion = '\n\n'.join(x for x in [
        s['titulo'].strip(),  # 13-nov-2026: el título en la primera línea de la descripción
        post, '\n'.join(enlaces), f"📚 Fuentes: {c['fuente']}",
        'Preguntas que responde este video:\n' + '\n'.join(f'• {q}' for q in s['preguntas']),
        razon,
        ('También te sirve si buscas: ' + ', '.join(relacionadas) + '.') if relacionadas else '',
        ' '.join(hashtags_para('youtube', s, config)),
        'Victoria es un personaje creado con IA.'] if x)[:4900]
    return s['titulo'], descripcion, ','.join(etiquetas(s, c.get('pilar', 'finanzas'), config))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) >= 2 and args[0] == 'short':
        c = cargar(args[1])
        rutas, total = tramos(c)
        if total > MAXIMO_SHORT:
            sys.exit(f'ERROR: el short dura {total:.1f} s; máximo {MAXIMO_SHORT}. Acorta las voces del carrusel {c["id"]}.')
        carpeta = os.path.join(RAIZ, 'carruseles', c['id'])
        pista = pista_para(c['id'])
        short = os.path.join(carpeta, 'short.mp4')
        unir(rutas, short)
        if '--sin-subtitulos' not in sys.argv:
            subtitular(short, c)
        if pista:
            con_musica(short, pista)
        portada_reel = os.path.join(carpeta, '00r.png')
        if os.path.exists(portada_reel):  # el Reel de Instagram abre con su propia portada (otra foto y otro título)
            r, _ = tramos(c, portada=portada_reel)
            reel = os.path.join(carpeta, 'reel.mp4')
            unir(r, reel)
            if '--sin-subtitulos' not in sys.argv:
                subtitular(reel, c)
            # Sin música, para los días en que Rodrigo lo sube con un sonido de la biblioteca de Instagram
            subprocess.run(['cp', reel, os.path.join(carpeta, 'reel-limpio.mp4')], check=True)
            if pista:
                con_musica(reel, pista)
            print(f'ok {carpeta}/reel.mp4 (abre con 00r.png)')
        config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
        for nombre, texto in zip(('titulo', 'descripcion_youtube', 'tags_youtube'), textos_youtube(c, config)):
            open(os.path.join(carpeta, f'{nombre}.txt'), 'w').write(texto)
        print(f'ok {carpeta}/short.mp4 ({total:.1f} s) y sus textos de YouTube')
    elif len(args) >= 2 and args[0] == 'musica':
        # Videos de Victoria (PIPELINE, después de cierre_pantalla.py): la música va debajo de la voz; el video no
        # se toca, así que la sincronía de labios no cambia.
        pista = args[2] if len(args) >= 3 else pista_para(os.path.basename(args[1]))
        if not pista:
            sys.exit('ERROR: no hay pistas en assets/musica/')
        con_musica(args[1], pista)
        print(f'ok {args[1]} con música de fondo ({os.path.basename(pista)})')
    elif len(args) >= 3 and args[0] == 'largo':
        horizontal = '--horizontal' in sys.argv
        rutas, total = [], 0.0
        for cid in args[2:]:
            r, t = tramos(cargar(cid), horizontal)
            rutas += r
            total += t
        unir(rutas, args[1])
        print(f'ok {args[1]} ({total / 60:.1f} min, {"horizontal" if horizontal else "vertical"})')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
