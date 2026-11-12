"""Le quita al video de Victoria el acabado "de IA" antes de subtitularlo (paso 6 de PIPELINE.md).

Uso: python naturalizar.py entrada.mp4 salida.mp4

Rodrigo (31-oct-2026): "se ve muy AI". Lo que más delata a la IA es lo perfecto: cámara clavada,
colores saturados y piel sin textura. Esto agrega, sin tocar el audio:
- movimiento leve de mano (como celular sostenido): un recorte que se mueve 2 a 7 px con dos ondas lentas,
- grano fino que cambia en cada cuadro (sensor de celular),
- un poco menos de saturación y contraste.
Va ANTES de subtitular: los subtítulos y el título se quedan fijos encima.

1080 (Rodrigo, 12-nov-2026: "se ven en mala calidad en Instagram, no son ni 1080"): Wan entrega 720x1280 y generarlo en
1080p cuesta el doble de créditos. Aquí se escala a 1080x1920 (lanczos y un enfoque leve) ANTES de subtitular, para que
subtítulos, título y cierre se dibujen nítidos en 1080 y Instagram reciba un video 1080. No inventa detalle: un video
generado en 1080p se ve mejor; esto evita que se vea peor de lo que es.
"""
import subprocess
import sys

FILTRO = ("crop=w=iw-24:h=ih-24:x='12+5*sin(t*1.1)+2*sin(t*3.7)':y='12+4*sin(t*1.6)+2*sin(t*2.9)',"
          "scale=1080:1920:flags=lanczos,unsharp=5:5:0.5:5:5:0,"
          "eq=saturation=0.9:contrast=0.96:gamma=1.02,noise=c0s=7:c0f=t+u")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', sys.argv[1], '-vf', FILTRO, '-c:v', 'libx264', '-crf', '18',
                    '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'copy', sys.argv[2]], check=True)
    print(f'ok {sys.argv[2]}')


if __name__ == '__main__':
    main()
