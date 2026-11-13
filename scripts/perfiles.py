"""Perfiles al 100 % (Rodrigo, 13-nov-2026: "poner bien los tags y hashtags en descripciones del canal en ajustes, dejar
la página al 100 en cada red social").

Uso: python3 scripts/perfiles.py youtube     descripción, palabras clave (≈485 de 500), país e idioma del canal
     python3 scripts/perfiles.py facebook    "acerca de", descripción y sitio web de la página
     python3 scripts/perfiles.py ver         imprime los textos (Instagram y TikTok no tienen API para la bio:
                                             los pega Rodrigo a mano)
Los textos viven en contenido/perfiles.json para cambiarlos con un commit.
"""
import json
import os
import sys
import urllib.parse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(RAIZ, 'contenido', 'perfiles.json')))


def costo_palabras(lista):
    """YouTube cuenta las palabras clave del canal separadas por espacio; las de varias palabras van entre comillas."""
    return len(' '.join(f'"{k}"' if ' ' in k else k for k in lista))


def palabras_canal():
    elegidas = []
    for k in P['youtube']['palabras_clave']:
        if costo_palabras(elegidas + [k]) <= P['youtube'].get('tope_palabras', 485):
            elegidas.append(k)
    return ' '.join(f'"{k}"' if ' ' in k else k for k in elegidas)


def youtube():
    import youtube as yt
    h = {'Authorization': f'Bearer {yt.token()}', 'Content-Type': 'application/json'}
    _, r = yt._http('GET', f'{yt.API}/channels?part=brandingSettings&mine=true', headers=h)
    canal = json.loads(r)['items'][0]
    b = canal['brandingSettings']
    b.setdefault('channel', {}).update({'description': P['youtube']['descripcion'][:1000], 'keywords': palabras_canal(),
                                        'country': 'MX', 'defaultLanguage': 'es'})
    cuerpo = json.dumps({'id': canal['id'], 'brandingSettings': {'channel': b['channel']}}).encode()
    yt._http('PUT', f'{yt.API}/channels?part=brandingSettings', cuerpo, headers=h)
    print('ok youtube | palabras clave:', len(palabras_canal()), 'caracteres | descripción:', len(P['youtube']['descripcion']))


def facebook():
    import primer_comentario as pc
    import publer
    pagina = publer.CONFIG['facebook_pagina_id']
    f = P['facebook']
    for campo, valor in (('about', f['acerca'][:255]), ('description', f['descripcion']), ('website', f['sitio'])):
        try:
            pc.fb('POST', f'{pagina}?{campo}={urllib.parse.quote(valor)}', pagina)
            print('ok facebook', campo)
        except SystemExit as e:
            print('facebook', campo, 'NO:', str(e)[:160])


def ver():
    print('YouTube palabras clave (', len(palabras_canal()), '):', palabras_canal())
    for red in ('instagram', 'tiktok'):
        print(f'\n{red.upper()} (a mano):\n{P[red]["bio"]}\n({len(P[red]["bio"])} caracteres)')


if __name__ == '__main__':
    {'youtube': youtube, 'facebook': facebook, 'ver': ver}.get(sys.argv[1] if len(sys.argv) > 1 else '', lambda: sys.exit(__doc__))()
