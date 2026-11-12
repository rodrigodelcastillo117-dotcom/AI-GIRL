"""Mete la ACCIÓN de la escena en un short de Victoria hablando, como una PAUSA real (Rodrigo, 12-nov-2026: "el chiste
es que si toma café, no hable, o sea hacerlo REALISTA").

Uso: python3 scripts/insertar_accion.py video.mp4 tiempos.json <frase> broll.mp4 salida.mp4 [segundos]
     <frase>: índice de tiempos.json (salida de frases_a_tiempos.py); la acción entra JUSTO DESPUÉS de esa frase.
     [segundos]: cuánto dura la acción (2 a 4 s; por omisión 3).

- Victoria termina la frase, se calla y hace la acción (toma el café, prueba la salsa…) con el sonido real de la
  escena (assets/broll/sonido/<clip>.m4a, de sonido_broll.py); luego vuelve a cámara y sigue hablando. Mientras hace la
  acción NO se oye su voz (antes la voz seguía y se le veía la boca cerrada: parecía doblaje).
- El video hablando no se toca: las dos partes son cortes limpios del mismo video, así que los labios siguen exactos
  (la revisión de labios se hace ANTES, sobre el video completo de Replicate).
- El corte cae a la mitad del silencio entre esa frase y la siguiente. Nunca después de la última frase (el cierre va a
  cámara). El short dura lo que el original + la acción.
"""
import json
import os
import subprocess
import sys


def duracion(ruta):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ruta],
                                capture_output=True, text=True, check=True).stdout.strip())


def main():
    if len(sys.argv) not in (6, 7):
        sys.exit(__doc__)
    video, tiempos, frase, broll, salida = sys.argv[1:6]
    seg = float(sys.argv[6]) if len(sys.argv) == 7 else 3.0
    t = json.load(open(tiempos))
    i = int(frase)
    if i < 0 or i >= len(t) - 1:
        sys.exit('ERROR: la acción va después de una frase que no sea la última')
    seg = max(2.0, min(seg, 4.0, duracion(broll) - 0.3))
    # Corte en el silencio: la frase i termina donde arranca la i+1; se corta 0.12 s antes para no comerse la palabra.
    corte = max(t[i]['start'] + 0.3, t[i + 1]['start'] - 0.12)
    sonido = os.path.join(os.path.dirname(os.path.abspath(broll)), 'sonido',
                          os.path.splitext(os.path.basename(broll))[0] + '.m4a')
    entradas = ['-i', video, '-i', broll]
    if os.path.exists(sonido):
        entradas += ['-i', sonido]
        amb = f'[2:a]atrim=0.2:{0.2 + seg:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.15,afade=t=out:st={seg - 0.2:.3f}:d=0.2,aresample=48000,aformat=channel_layouts=stereo[am];'
    else:  # sin sonido de la escena: silencio (nunca la voz encima)
        print('AVISO: sin sonido de la escena; corre sonido_broll.py para que se oiga el ambiente')
        entradas += ['-f', 'lavfi', '-t', f'{seg:.3f}', '-i', 'anullsrc=r=48000:cl=stereo']
        amb = '[2:a]asetpts=PTS-STARTPTS[am];'
    v = '1080:1920,fps=30,format=yuv420p,setsar=1'
    filtro = (f'[0:v]trim=0:{corte:.3f},setpts=PTS-STARTPTS,scale={v}[va];'
              f'[0:a]atrim=0:{corte:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={corte - 0.06:.3f}:d=0.06,aresample=48000,aformat=channel_layouts=stereo[aa];'
              f'[1:v]trim=0.2:{0.2 + seg:.3f},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p,setsar=1[vm];'
              + amb +
              f'[0:v]trim={corte:.3f},setpts=PTS-STARTPTS,scale={v}[vc];'
              f'[0:a]atrim={corte:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.06,aresample=48000,aformat=channel_layouts=stereo[ac];'
              '[va][aa][vm][am][vc][ac]concat=n=3:v=1:a=1[v][a]')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *entradas, '-filter_complex', filtro, '-map', '[v]', '-map', '[a]',
                    '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', salida],
                   check=True)
    d0, d1 = duracion(video), duracion(salida)
    if abs(d1 - (d0 + seg)) > 0.2:
        sys.exit(f'ERROR: largo inesperado ({d0:.2f} + {seg:.1f} → {d1:.2f} s)')
    # tiempos desplazados para los subtítulos: lo que va después del corte se recorre "seg" segundos
    nuevos = [dict(x, start=round(x['start'] + (seg if x['start'] >= corte else 0), 2),
                   end=round(x['end'] + (seg if x['end'] > corte else 0), 2)) for x in t]
    nuevos[i]['end'] = round(corte, 2)  # durante la acción no hay subtítulo
    json.dump(nuevos, open(os.path.splitext(salida)[0] + '-tiempos.json', 'w'), ensure_ascii=False, indent=1)
    print(f'ok {salida}: calla en {corte:.2f} s, acción {seg:.1f} s, sigue hablando; {d1:.1f} s en total')


if __name__ == '__main__':
    main()
