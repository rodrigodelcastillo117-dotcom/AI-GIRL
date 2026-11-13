"""Pone de portada la lámina 00 (Victoria + título) a los shorts de carrusel YA subidos (Rodrigo, 13-nov-2026: "que en los
shorts siempre sea Victoria en la portada"). Los nuevos ya la llevan al subir (youtube.py → portada_carrusel).

Uso: python3 scripts/portadas_shorts.py [--prueba]     cada portada cuesta 50 unidades de cuota de YouTube
Registro: contenido/portadas_youtube.json (no repite las que ya puso).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import youtube as yt  # noqa: E402

REG = os.path.join(yt.RAIZ, 'contenido', 'portadas_youtube.json')


def main():
    hechos = json.load(open(REG)) if os.path.exists(REG) else {}
    carr = json.load(open(os.path.join(yt.RAIZ, 'contenido', 'carruseles.json')))['carruseles']
    acceso = None
    for c in carr:
        enlace = c.get('youtube') or ''
        vid = enlace.rstrip('/').split('/')[-1].split('=')[-1] if enlace else ''
        if not vid or vid in hechos:
            continue
        imagen = yt.portada_carrusel(os.path.join(yt.RAIZ, 'carruseles', c['id'], 'short.mp4'))
        if not imagen:
            continue
        if '--prueba' in sys.argv:
            print('pondría', c['id'], vid)
            continue
        acceso = acceso or yt.token()
        try:
            yt._http('POST', f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}',
                     open(imagen, 'rb').read(), {'Authorization': f'Bearer {acceso}', 'Content-Type': 'image/jpeg'})
        except SystemExit as e:
            if 'quota' in str(e).lower():
                sys.exit('Cuota de YouTube agotada; sigue mañana.')
            print('no', c['id'], vid, str(e)[:160])
            continue
        hechos[vid] = c['id']
        json.dump(hechos, open(REG, 'w'), ensure_ascii=False, indent=1)
        print('ok portada', c['id'], vid)


if __name__ == '__main__':
    main()
