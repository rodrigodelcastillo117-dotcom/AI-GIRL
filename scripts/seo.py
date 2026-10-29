"""Arma y valida los textos de publicación de un video a partir de su bloque "seo" del plan.

Uso: python seo.py <id_video> <carpeta_salida>      (sale con error si el SEO rompe una regla)
     python seo.py revisar                          (valida el SEO de todos los videos pendientes)

Escribe en la carpeta:
- titulo.txt               título para YouTube, Instagram y TikTok (reglas 10-16)
- descripcion_youtube.txt  dos primeras líneas con términos de búsqueda, 2-3 párrafos cortos,
                           máximo 2 enlaces arriba (reglas 18-20, 26)
- tags_youtube.txt         30-40 etiquetas en tres capas, máximo 480 caracteres contados como
                           YouTube (reglas 21-22)
- texto_redes.txt          pie para Instagram y TikTok: post, "enlace en mi perfil" si hay enlace,
                           3-4 hashtags fijos + 3-5 concretos (reglas 24, 27)
Las reglas numeradas están en docs/REGLAS_APRENDIDAS.md; cómo escribir el bloque, en docs/SEO.md.
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPE_TAGS = 480


def es_emoji(caracter):
    return ord(caracter) >= 0x2190 or caracter == '️'


def errores_titulo(titulo, palabra_clave, maximo):
    """Lista de reglas que rompe el título (vacía si está bien)."""
    errores = []
    if len(titulo) > maximo:
        errores.append(f'mide {len(titulo)} caracteres; máximo {maximo} (regla 13). Reescríbelo, no lo recortes (regla 16)')
    if len(titulo.strip()) < 5:
        errores.append('tiene menos de 5 caracteres (regla 6)')
    if '#' in titulo:
        errores.append('lleva # (regla 12)')
    if ':' in titulo or '|' in titulo:
        errores.append('usa ":" o "|" para encadenar palabras (regla 12)')
    if '?' in titulo or '¿' in titulo:
        errores.append('es pregunta; debe afirmar (regla 11)')
    texto = ''.join(c for c in titulo if not es_emoji(c)).strip()
    if not texto.lower().startswith(palabra_clave.lower()) and palabra_clave.lower() not in texto.lower()[:len(palabra_clave) + 12]:
        errores.append(f'no empieza con lo que se busca ("{palabra_clave}") (regla 10)')
    emojis = sum(1 for c in titulo if es_emoji(c) and c != '️')
    if emojis > 2:
        errores.append('lleva más de 2 emojis (regla 15)')
    if emojis and not es_emoji(titulo.rstrip()[-1]):
        errores.append('el emoji va al final (regla 15)')
    return errores


def costo_tag(tag):
    return len(tag) + (3 if ' ' in tag else 1)  # las etiquetas con espacios llevan comillas


def etiquetas(seo, pilar, config):
    """Tres capas en orden (genéricas, formato, concretas), pero las concretas entran primero al presupuesto."""
    concretas = [t.lower() for t in seo['tags_concretas']]
    formato = [t.lower() for t in config['tags_formato'].get(pilar, [])]
    genericas = [t.lower() for t in config['tags_genericas']]
    elegidas, usados = set(), 0
    for t in concretas + formato + genericas:
        if t not in elegidas and usados + costo_tag(t) <= TOPE_TAGS and len(elegidas) < 40:
            elegidas.add(t)
            usados += costo_tag(t)
    orden = []
    for t in genericas + formato + concretas:
        if t in elegidas and t not in orden:
            orden.append(t)
    return orden


def con_ref(enlace, red):
    return f"{enlace}{'&' if '?' in enlace else '?'}ref={red}" if enlace else ''


def textos(video, plan, config):
    seo = video.get('seo')
    if not seo:
        sys.exit(f"ERROR: el video {video['id']} no tiene bloque \"seo\" (ver docs/SEO.md)")
    errores = errores_titulo(seo['titulo'], seo['palabra_clave'], config.get('titulo_max', 45))
    if errores:
        sys.exit(f"ERROR: el título del video {video['id']} \"{seo['titulo']}\" " + '; '.join(errores))
    cierre = plan['reglas']['cierre_de_texto']
    post = '\n'.join(l for l in video['texto_post'].strip().splitlines() if not l.strip().startswith('#')).strip()
    hashtags = list(dict.fromkeys(config['hashtags_fijos'] + seo['hashtags']))
    enlaces = [e for e in (con_ref(config.get('enlace_venta'), 'yt'), con_ref(config.get('enlace_perfil'), 'yt')) if e][:2]
    descripcion = '\n\n'.join(x for x in [
        seo['descripcion_inicio'].strip(),
        '\n'.join(enlaces),
        post,
        f"Soy Victoria: un consejo de negocios, dinero y mente fuerte cada 2 días. Suscríbete.",
        ' '.join(hashtags[:3]),
        cierre,
    ] if x)[:4900]
    redes = '\n\n'.join(x for x in [
        post,
        'Enlace en mi perfil 👆' if config.get('enlace_venta') else '',
        ' '.join(hashtags[:9]),  # 3-4 fijos + 3-5 del video
        cierre,
    ] if x)
    tags = etiquetas(seo, video['pilar'], config)
    return {'titulo': seo['titulo'], 'descripcion_youtube': descripcion, 'tags_youtube': ','.join(tags), 'texto_redes': redes}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    if sys.argv[1] == 'revisar':
        malos = 0
        for v in plan['videos']:
            if v['estado'] in ('pendiente', 'listo_para_publicar'):
                try:
                    t = textos(v, plan, config)
                    print(f"OK {v['id']} ({len(t['titulo'])}) {t['titulo']} · {len(t['tags_youtube'].split(','))} etiquetas")
                except SystemExit as e:
                    malos += 1
                    print(e)
        sys.exit(1 if malos else 0)
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    video = next((v for v in plan['videos'] if v['id'] == sys.argv[1]), None)
    if not video:
        sys.exit(f'ERROR: no existe el video {sys.argv[1]}')
    os.makedirs(sys.argv[2], exist_ok=True)
    for nombre, texto in textos(video, plan, config).items():
        open(os.path.join(sys.argv[2], f'{nombre}.txt'), 'w').write(texto)
        print(f'{nombre}: {texto.splitlines()[0][:100]}')


if __name__ == '__main__':
    main()
