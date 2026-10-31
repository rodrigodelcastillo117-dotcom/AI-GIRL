"""Le quita al video de Victoria el acabado "de IA" antes de subtitularlo (paso 6 de PIPELINE.md).

Uso: python naturalizar.py entrada.mp4 salida.mp4

Rodrigo (31-oct-2026): "se ve muy AI". Lo que más delata a la IA es lo perfecto: cámara clavada,
colores saturados y piel sin textura. Esto agrega, sin tocar el audio:
- movimiento leve de mano (como celular sostenido): un recorte que se mueve 2 a 7 px con dos ondas lentas,
- grano fino que cambia en cada cuadro (sensor de celular),
- un poco menos de saturación y contraste.
Va ANTES de subtitular: los subtítulos y el título se quedan fijos encima.
"""
import subprocess
import sys

FILTRO = ("crop=w=iw-24:h=ih-24:x='12+5*sin(t*1.1)+2*sin(t*3.7)':y='12+4*sin(t*1.6)+2*sin(t*2.9)',"
          "scale=iw+24:ih+24,eq=saturation=0.9:contrast=0.96:gamma=1.02,noise=c0s=8:c0f=t+u")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', sys.argv[1], '-vf', FILTRO, '-c:v', 'libx264', '-crf', '18',
                    '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'copy', sys.argv[2]], check=True)
    print(f'ok {sys.argv[2]}')


if __name__ == '__main__':
    main()
