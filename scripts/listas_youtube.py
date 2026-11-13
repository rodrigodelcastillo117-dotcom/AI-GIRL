"""Listas de reproducción del canal por TEMA y por FORMATO (Rodrigo, 13-nov-2026: "¿puedes hacer playlists en YouTube? de
shorts, videos largos y así"). Cada video entra a su lista de tema (youtube.clave_playlist o por título) y además a la de
formato (largos > 3 min, si no shorts) y a las de serie (Victoria verifica, No me pagaron el aguinaldo).

Uso: python3 scripts/listas_youtube.py ver                    cómo quedaría cada video (no gasta cuota de escritura)
     python3 scripts/listas_youtube.py llenar [clave …]        mete los videos del canal a sus listas (50 unidades cada uno)
     python3 scripts/listas_youtube.py video <video_id>        un solo video (lo llama youtube.py playlist al subir)
Cuota: YouTube da 10,000 unidades al día; cada video agregado cuesta 50. llenar se detiene si YouTube responde quotaExceeded.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import youtube as yt  # noqa: E402

REGLAS = [  # (clave, palabras en el título, minúsculas y sin acentos)
    ('pension', ('pension', 'afore', 'imss', 'issste', 'retiro', 'jubil', 'modalidad 40', 'semanas cotizadas', 'bienestar')),
    ('verifica', ('rumor', 'verificad', 'verdad o', 'es falso')),
    ('no_me_pagaron', ('no me pagaron',)),
    ('sueldo', ('salario minimo', 'recibo de nomina', 'vacaciones', 'finiquito', 'liquidacion', 'sueldo y renta')),
    ('buenfin', ('buen fin',)),
    ('aguinaldo', ('aguinaldo',)),
    ('negocios', ('negocio', 'pareto', 'clientes', 'emprend')),
]


def plano(t):
    import unicodedata
    return unicodedata.normalize('NFKD', t.lower()).encode('ascii', 'ignore').decode()


def claves(titulo, segundos):
    t = plano(titulo)
    salida = ['largos' if segundos > 180 else 'shorts']
    salida += [k for k, palabras in REGLAS if any(p in t for p in palabras)]
    if not any(k in salida for k in ('pension', 'sueldo', 'buenfin', 'aguinaldo', 'negocios', 'no_me_pagaron')):
        salida.append('finanzas')
    return salida


def videos(ids=None):
    h = {'Authorization': f'Bearer {yt.token()}'}
    if ids is None:
        _, r = yt._http('GET', f'{yt.API}/channels?part=contentDetails&mine=true', headers=h)
        sube = json.loads(r)['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        ids, tok = [], ''
        while True:
            _, r = yt._http('GET', f'{yt.API}/playlistItems?part=contentDetails&maxResults=50&playlistId={sube}'
                            + (f'&pageToken={tok}' if tok else ''), headers=h)
            d = json.loads(r)
            ids += [i['contentDetails']['videoId'] for i in d['items']]
            tok = d.get('nextPageToken')
            if not tok:
                break
    salida = []
    for i in range(0, len(ids), 50):
        _, r = yt._http('GET', f'{yt.API}/videos?part=snippet,contentDetails&id={",".join(ids[i:i + 50])}', headers=h)
        for v in json.loads(r)['items']:
            m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', v['contentDetails']['duration'])
            seg = int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + int(m[3] or 0)
            salida.append({'id': v['id'], 'titulo': v['snippet']['title'], 'seg': seg})
    return salida


def llenar(lista_videos, solo=None):
    acceso = yt.token()
    hechos = 0
    for v in reversed(lista_videos):  # del más viejo al más nuevo: la lista queda en orden
        for k in claves(v['titulo'], v['seg']):
            if solo and k not in solo:
                continue
            try:
                yt.a_playlist(acceso, v['id'], k)
                hechos += 1
            except SystemExit as e:
                if 'quota' in str(e).lower():
                    sys.exit(f'Cuota de YouTube agotada después de {hechos} altas; sigue mañana con: llenar {" ".join(solo or [])}')
                print('error', v['id'], k, str(e)[:120])
    print('ok altas revisadas:', hechos)


if __name__ == '__main__':
    accion = sys.argv[1] if len(sys.argv) > 1 else ''
    if accion == 'ver':
        for v in videos():
            print(v['seg'], '|', v['titulo'][:60], '→', ', '.join(claves(v['titulo'], v['seg'])))
    elif accion == 'llenar':
        llenar(videos(), sys.argv[2:] or None)
    elif accion == 'video' and len(sys.argv) == 3:
        llenar(videos([sys.argv[2]]))
    else:
        sys.exit(__doc__)
