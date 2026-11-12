"""Mete la ACCIÓN de la escena en medio de un short de Victoria hablando (Rodrigo, 12-nov-2026: "que hable, que diga
cosas, que haga acciones dependiendo del entorno").

Uso: python3 scripts/insertar_accion.py video.mp4 tiempos.json <frases> broll.mp4 salida.mp4
     <frases>: índices de tiempos.json (salida de frases_a_tiempos.py) que se tapan con la acción, p. ej. "2" o "2-3".

- La voz NO se toca (se copia tal cual): mientras se ve la acción, Victoria sigue hablando en off, como en un video real
  donde la creadora corta a lo que está haciendo. Al volver a cámara los labios siguen exactos.
- Nunca se tapan la primera ni la última frase (gancho y cierre van a cámara) y el tramo dura de 2 a 5 s. Si el clip de
  acción es más corto que el tramo, el tramo se recorta al largo del clip (nunca se alenta el clip).
- La revisión de labios (qa_labios / qa_sync) se hace ANTES, sobre el video de Replicate completo.
"""
import json
import subprocess
import sys


def duracion(ruta):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ruta],
                                capture_output=True, text=True, check=True).stdout.strip())


def main():
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    video, tiempos, frases, broll, salida = sys.argv[1:]
    t = json.load(open(tiempos))
    a, _, b = frases.partition('-')
    a, b = int(a), int(b or a)
    if a <= 0 or b >= len(t) - 1 or a > b:
        sys.exit('ERROR: la acción no puede tapar la primera ni la última frase')
    ini, fin = t[a]['start'], t[b]['end']
    fin = min(fin, ini + 5.0, ini + duracion(broll) - 0.1)
    if fin - ini < 2.0:
        sys.exit(f'ERROR: tramo de {fin - ini:.1f} s; elige frases que sumen al menos 2 s')
    largo = fin - ini
    filtro = (f'[0:v]trim=0:{ini:.3f},setpts=PTS-STARTPTS[a];'
              f'[1:v]trim=0.2:{0.2 + largo:.3f},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,'
              f'crop=1080:1920,fps=30,format=yuv420p[m];'
              f'[0:v]trim={fin:.3f},setpts=PTS-STARTPTS[c];'
              f'[a]scale=1080:1920,fps=30,format=yuv420p[a2];[c]scale=1080:1920,fps=30,format=yuv420p[c2];'
              f'[a2][m][c2]concat=n=3:v=1:a=0[v]')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', video, '-i', broll, '-filter_complex', filtro,
                    '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
                    '-shortest', salida], check=True)
    d0, d1 = duracion(video), duracion(salida)
    if abs(d0 - d1) > 0.15:
        sys.exit(f'ERROR: el largo cambió ({d0:.2f} → {d1:.2f} s); la voz quedaría fuera de tiempo')
    print(f'ok {salida}: acción de {ini:.2f} a {fin:.2f} s ({largo:.1f} s)')


if __name__ == '__main__':
    main()
