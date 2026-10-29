"""Arma los textos de publicación de un video a partir de su bloque "seo" del plan.

Uso: python seo.py <id_video> <carpeta_salida>

Escribe en la carpeta:
- titulo_youtube.txt   palabra clave al inicio + " #Shorts" (YouTube muestra ~40 caracteres en el feed)
- descripcion_youtube.txt   primera línea con la palabra clave, el texto del post sin hashtags,
                            invitación a suscribirse, 3 hashtags (YouTube los muestra arriba del
                            título) y la aclaración de IA
- tags_youtube.txt     tags separados por coma (máximo 500 caracteres, regla de YouTube)
- texto_redes.txt      texto para Instagram y TikTok: el post con sus hashtags y la aclaración de IA
- titulo_redes.txt     primera línea del post sin emojis (título para TikTok en Publer)
Las reglas para escribir el bloque "seo" de un video nuevo están en docs/SEO.md.
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMOJIS = re.compile('[\U0001F000-\U0001FAFF☀-➿️]')


def sin_emojis(texto):
    return ' '.join(EMOJIS.sub('', texto).split())


def textos(video, reglas):
    seo = video.get('seo')
    if not seo:
        sys.exit(f"ERROR: el video {video['id']} no tiene bloque \"seo\" en el plan (ver docs/SEO.md)")
    cierre = reglas['cierre_de_texto']
    lineas = video['texto_post'].strip().splitlines()
    cuerpo = '\n'.join(l for l in lineas if not l.strip().startswith('#')).strip()
    tags, largo = [], 0
    for t in seo['tags_youtube']:
        if largo + len(t) + 1 > 480:
            break
        tags.append(t)
        largo += len(t) + 1
    return {
        'titulo_youtube': f"{seo['titulo_youtube']} #Shorts"[:100],
        'descripcion_youtube': '\n\n'.join([
            f"{seo['titulo_youtube']}.", cuerpo,
            'Un consejo nuevo de Victoria todos los días a las 6:45 p.m. Suscríbete para no perderte ninguno.',
            ' '.join(seo['hashtags_youtube'][:3]), cierre]),
        'tags_youtube': ','.join(tags),
        'texto_redes': f"{video['texto_post'].strip()}\n\n{cierre}",
        'titulo_redes': sin_emojis(lineas[0])[:90],
    }


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    video = next((v for v in plan['videos'] if v['id'] == sys.argv[1]), None)
    if not video:
        sys.exit(f'ERROR: no existe el video {sys.argv[1]}')
    os.makedirs(sys.argv[2], exist_ok=True)
    for nombre, texto in textos(video, plan['reglas']).items():
        open(os.path.join(sys.argv[2], f'{nombre}.txt'), 'w').write(texto)
        print(f'{nombre}: {texto.splitlines()[0][:90]}')


if __name__ == '__main__':
    main()
