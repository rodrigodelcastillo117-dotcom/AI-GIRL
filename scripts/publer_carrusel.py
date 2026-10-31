"""Programa un carrusel de contenido/carruseles.json en el Instagram y el TikTok de Victoria (Publer).

Uso: python publer_carrusel.py <id> <cuando_utc> [--borrador] [--prueba]
     cuando_utc: "2026-11-03T00:45:00Z" o una hora por red: "ig=2026-11-03T14:00:00Z,tt=2026-11-03T18:30:00Z"
     --borrador  lo deja como borrador en Publer (no sale): para que Rodrigo lo vea antes.
     --prueba    imprime lo que mandaría, sin llamar a Publer.
     --forzar    deja programarlo aunque ese día ya salga otro video o carrusel en esa red (sin esto, se niega:
                 el 30-oct salieron c02 y c03 el mismo día por no revisarlo).

Antes: python carrusel.py <id> (las fotos en carruseles/<id>/). El video del carrusel (carrusel_video.py short)
es SOLO para YouTube (youtube.py subir): Instagram y TikTok reciben los videos de Victoria o, los días sin
video, el carrusel en fotos (Rodrigo, 31-oct-2026).
Instagram: carrusel de hasta 10 fotos. TikTok: modo foto ("type": "photo") con música automática.
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carrusel import RAIZ, cargar  # noqa: E402
from seo import hashtags_para  # noqa: E402
from publer import cuando_de, _pedir, cuentas_victoria, mandar, red, workspace_id, ya_programadas  # noqa: E402
from aprender import CDMX, a_utc, publicaciones  # noqa: E402


def comentario_ig(c, config):
    """Primer comentario de Instagram: el llamado del carrusel sin enlace (en Instagram solo se toca el de la bio)."""
    if c.get('enlace'):
        return f"{c['enlace']['etiqueta']}: el enlace está en mi perfil 👆"
    return config.get('primer_comentario_instagram')


def ya_sale_ese_dia(c, cuando, todos, plan):
    """Lo que ya sale el mismo día (México) en Instagram o TikTok: un video o carrusel por día y por red
    (Rodrigo: video un día, carrusel el siguiente)."""
    choques = []
    for proveedor, r in (('instagram', 'ig'), ('tiktok', 'tt')):
        dia = a_utc(cuando_de(cuando, proveedor)).astimezone(CDMX).date()
        choques += [f"{r}: {x['id']} a las {h[r].strftime('%H:%M')}" for x, h in publicaciones(plan, todos)
                    if x['id'] != c['id'] and r in h and h[r].date() == dia]
    return choques


def red_post(proveedor, tipo_ig, media, texto, titulo, comentario=None):
    if proveedor == 'instagram':
        return {'type': tipo_ig, 'text': texto, 'media': media, **({'firstComment': comentario} if comentario else {})}
    return {'type': 'photo', 'title': titulo[:90], 'text': texto, 'media': media,
            'details': {'privacy': 'PUBLIC_TO_EVERYONE', 'auto_add_music': True, 'comment': True}}


def cuerpo(cuenta, tipo_ig, media, texto, titulo, cuando, estado, comentario=None):
    return {'bulk': {'state': estado, 'posts': [{
        'networks': {red(cuenta): red_post(red(cuenta), tipo_ig, media, texto, titulo, comentario)},
        'accounts': [{'id': cuenta['id'], 'scheduled_at': cuando}]}]}}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        sys.exit(__doc__)
    c, cuando = cargar(args[0]), args[1]
    estado = 'draft' if '--borrador' in sys.argv else 'scheduled'
    if estado == 'scheduled' and '--forzar' not in sys.argv:
        todos = json.load(open(os.path.join(RAIZ, 'contenido', 'carruseles.json')))['carruseles']
        choques = ya_sale_ese_dia(c, cuando, todos, json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json'))))
        if choques:
            sys.exit(f'ERROR: ese día ya sale otra publicación ({"; ".join(choques)}). Elige otro día o usa --forzar.')
    fotos = sorted(glob.glob(os.path.join(RAIZ, 'carruseles', c['id'], '[0-9][0-9].png')))
    if len(fotos) != len(c['diapositivas']) + 2:
        sys.exit(f'ERROR: faltan fotos en carruseles/{c["id"]}: corre primero carrusel.py {c["id"]}')
    # Instagram busca por las palabras del pie y corta en 5 hashtags; TikTok, además, por las preguntas (docs/SEO.md).
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    por_red = {'instagram': c['texto_post'].strip() + '\n\n' + ' '.join(hashtags_para('instagram', c['seo'], config)),
               'tiktok': '\n\n'.join([c['texto_post'].strip(), '🔎 ' + ' '.join(c['seo']['preguntas']),
                                       ' '.join(hashtags_para('tiktok', c['seo'], config))])}
    texto = por_red['instagram']
    if '--prueba' in sys.argv:
        falsa = [{'id': 'ID_IG', 'provider': 'instagram'}, {'id': 'ID_TT', 'provider': 'tiktok'}]
        media = [{'id': f'MEDIA_{i}', 'type': 'image'} for i in range(len(fotos))]
        for cuenta in falsa:
            print(json.dumps(cuerpo(cuenta, 'photo', media, por_red[red(cuenta)], c['titulo_post'], cuando_de(cuando, red(cuenta)), estado,
                                    comentario_ig(c, config) if red(cuenta) == 'instagram' else None), ensure_ascii=False, indent=1))
        return
    ws = workspace_id()
    _, cuentas = cuentas_victoria(ws)
    cuentas = [x for x in cuentas if red(x) in ('instagram', 'tiktok')]
    if not cuentas:
        sys.exit('ERROR: no encontré las cuentas de Victoria en Publer. No publico nada.')
    repetidas = ya_programadas(ws, cuentas, texto)
    cuentas = [x for x in cuentas if str(x['id']) not in repetidas]
    if not cuentas:
        print('OMITIDO: este carrusel ya está programado o publicado en todas las cuentas de Victoria.')
        return
    media = []
    for foto in fotos:
        subida = _pedir('POST', '/media', ws, multipart=(os.path.basename(foto), open(foto, 'rb').read(), 'image/png'))
        mid = subida.get('id') or (subida.get('data') or {}).get('id')
        if not mid:
            sys.exit(f'ERROR: la subida de {foto} no regresó id: {json.dumps(subida)[:500]}')
        media.append({'id': mid, 'type': 'image'})
    print(f'{len(media)} fotos subidas.')
    fallidas = []
    for cuenta in cuentas:
        # Instagram: Publer rechaza "carousel" (error interno) y acepta "photo" con varias fotos (probado 30-oct-2026).
        comentario = comentario_ig(c, config) if red(cuenta) == 'instagram' else None
        motivo = mandar(ws, cuerpo(cuenta, 'photo', media, por_red[red(cuenta)], c['titulo_post'], cuando_de(cuando, red(cuenta)), estado, comentario))
        if motivo and comentario:  # si Publer no acepta el primer comentario, sale sin él
            print(f'AVISO: Publer rechazó el carrusel con primer comentario ({motivo[:200]}); lo mando sin comentario.')
            motivo = mandar(ws, cuerpo(cuenta, 'photo', media, por_red[red(cuenta)], c['titulo_post'], cuando_de(cuando, red(cuenta)), estado))
        if motivo:
            fallidas.append(f'{red(cuenta)}: {motivo}')
        else:
            print(f'OK {red(cuenta)} {"borrador" if estado == "draft" else "programado para " + cuando_de(cuando, red(cuenta))}.')
    if fallidas:
        sys.exit('ERROR: Publer reportó fallas en ' + ' | '.join(fallidas))


if __name__ == '__main__':
    main()
