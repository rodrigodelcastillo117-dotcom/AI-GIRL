"""Programa un carrusel de contenido/carruseles.json en el Instagram y el TikTok de Victoria (Publer).

Uso: python publer_carrusel.py <id> <cuando_utc> [--borrador] [--prueba]
     cuando_utc: "2026-11-03T00:45:00Z" o una hora por red: "ig=2026-11-03T14:00:00Z,tt=2026-11-03T18:30:00Z"
     python publer_carrusel.py <id> <cuando_utc|auto> --reel [--prueba]
     --borrador  lo deja como borrador en Publer (no sale): para que Rodrigo lo vea antes.
     --prueba    imprime lo que mandaría, sin llamar a Publer.
     --reel      sube carruseles/<id>/short.mp4 (el mismo video del Short de YouTube: 0 créditos) como Reel
                 solo en Instagram. El carrusel de fotos casi solo lo ven los seguidores; el Reel también
                 llega a no seguidores. "auto" elige la hora (hora_reel). Queda en carruseles.json → reel_ig,
                 fuera de la prueba de horarios (es otro formato y su hora no la eligió la prueba).

Antes: python carrusel.py <id> (las fotos en carruseles/<id>/). El short de YouTube va aparte:
carrusel_short.py y youtube.py subir.
Instagram: carrusel de hasta 10 fotos. TikTok: modo foto ("type": "photo") con música automática.
"""
import datetime
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carrusel import RAIZ, cargar  # noqa: E402
from seo import hashtags_para  # noqa: E402
from publer import _buscar_id, _primera_linea, armar_post, cuando_de, _pedir, cuentas_victoria, esperar_job, mandar, red, workspace_id, ya_programadas  # noqa: E402
from aprender import CDMX, a_utc, publicaciones  # noqa: E402


def comentario_ig(c, config):
    """Primer comentario de Instagram: el llamado del carrusel sin enlace (en Instagram solo se toca el de la bio)."""
    if c.get('enlace'):
        return f"{c['enlace']['etiqueta']}: el enlace está en mi perfil 👆"
    return config.get('primer_comentario_instagram')


def red_post(proveedor, tipo_ig, media, texto, titulo, comentario=None):
    if proveedor == 'instagram':
        return {'type': tipo_ig, 'text': texto, 'media': media, **({'firstComment': comentario} if comentario else {})}
    return {'type': 'photo', 'title': titulo[:90], 'text': texto, 'media': media,
            'details': {'privacy': 'PUBLIC_TO_EVERYONE', 'auto_add_music': True, 'comment': True}}


def cuerpo(cuenta, tipo_ig, media, texto, titulo, cuando, estado, comentario=None):
    return {'bulk': {'state': estado, 'posts': [{
        'networks': {red(cuenta): red_post(red(cuenta), tipo_ig, media, texto, titulo, comentario)},
        'accounts': [{'id': cuenta['id'], 'scheduled_at': cuando}]}]}}


def texto_reel(c, config):
    """Pie del Reel: el gancho de la portada arriba y debajo el pie del carrusel completo (sus palabras clave).
    La primera línea tiene que ser distinta a la del carrusel: con ella se reconocen en Publer al medir."""
    primera = c['portada']['titulo'].strip()
    if _primera_linea(primera) == _primera_linea(c['texto_post']):
        sys.exit(f'ERROR: el Reel de {c["id"]} empezaría igual que su carrusel; cambia portada.titulo o texto_post.')
    return primera + '\n' + c['texto_post'].strip() + '\n\n' + ' '.join(hashtags_para('instagram', c['seo'], config))


def hora_reel(c, todos, plan, config, ahora):
    """El día del carrusel en Instagram (si ya no da o ya hay otro Reel de carrusel, el siguiente), en la
    franja de Instagram más fuerte para ese día (orden_por_dia) a 2 h o más de cualquier otro post."""
    ocupadas = [h['ig'] for _, h in publicaciones(plan, todos) if 'ig' in h]
    reels = [a_utc(x['reel_ig']['publica_utc']).astimezone(CDMX) for x in todos
             if x['id'] != c['id'] and (x.get('reel_ig') or {}).get('publica_utc')]
    prueba = config.get('prueba_horas') or {}
    dia = a_utc((c.get('publica_utc_por_red') or {}).get('ig') or c['publica_utc']).astimezone(CDMX).date()
    for d in (dia + datetime.timedelta(days=i) for i in range(4)):
        if any(t.date() == d for t in reels):
            continue
        orden = ((prueba.get('orden_por_dia') or {}).get('ig') or {}).get(str(d.weekday())) or prueba['franjas_por_red']['ig']
        for f in orden:
            t = datetime.datetime.combine(d, datetime.time.fromisoformat(f), tzinfo=CDMX)
            if t > ahora + datetime.timedelta(minutes=20) and all(abs(t - o) >= datetime.timedelta(hours=2) for o in ocupadas + reels):
                return t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    sys.exit(f'ERROR: no encontré hora libre para el Reel de {c["id"]} en 4 días; pásala a mano.')


def reel(c, cuando, config):
    """Programa el Reel de Instagram del carrusel y lo guarda en carruseles.json → reel_ig."""
    video = os.path.join(RAIZ, 'carruseles', c['id'], 'short.mp4')
    if not os.path.exists(video):
        sys.exit(f'ERROR: falta {video}: corre primero carrusel_video.py short {c["id"]}')
    ruta = os.path.join(RAIZ, 'contenido', 'carruseles.json')
    datos = json.load(open(ruta))
    yo = next(x for x in datos['carruseles'] if x['id'] == c['id'])
    if (yo.get('reel_ig') or {}).get('publica_utc'):
        print(f'OMITIDO: el Reel de {c["id"]} ya está en carruseles.json ({yo["reel_ig"]["publica_utc"]}).')
        return
    if cuando == 'auto':
        plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
        cuando = hora_reel(yo, datos['carruseles'], plan, config, datetime.datetime.now(datetime.timezone.utc))
    texto = texto_reel(c, config)
    if '--prueba' in sys.argv:
        print(json.dumps(armar_post([{'id': 'ID_IG', 'provider': 'instagram'}], 'MEDIA_ID', texto, c['titulo_post'], cuando),
                         ensure_ascii=False, indent=1))
        return
    ws = workspace_id()
    _, cuentas = cuentas_victoria(ws)
    cuentas = [x for x in cuentas if red(x) == 'instagram']
    if not cuentas:
        sys.exit('ERROR: no encontré el Instagram de Victoria en Publer. No publico nada.')
    if ya_programadas(ws, cuentas, texto):
        print('OMITIDO: este Reel ya está programado o publicado en Instagram.')
        return
    subida = _pedir('POST', '/media', ws, multipart=(f'{c["id"]}-reel.mp4', open(video, 'rb').read(), 'video/mp4'))
    media_id = subida.get('id') or (subida.get('data') or {}).get('id')
    if not media_id and subida.get('job_id'):
        media_id = _buscar_id(esperar_job(ws, subida['job_id']).get('result'))
    if not media_id:
        sys.exit(f'ERROR: la subida del video no regresó id: {json.dumps(subida)[:500]}')
    motivo = mandar(ws, armar_post(cuentas, media_id, texto, c['titulo_post'], cuando, comentario_ig(c, config)))
    if motivo:  # si Publer no acepta el primer comentario, sale sin él
        print(f'AVISO: Publer rechazó el Reel con primer comentario ({motivo[:200]}); lo mando sin comentario.')
        motivo = mandar(ws, armar_post(cuentas, media_id, texto, c['titulo_post'], cuando))
    if motivo:
        sys.exit(f'ERROR: Publer reportó falla en el Reel: {motivo}')
    yo['reel_ig'] = {'publica_utc': cuando, 'texto': texto, 'video': f'carruseles/{c["id"]}/short.mp4'}
    json.dump(datos, open(ruta, 'w'), ensure_ascii=False, indent=1)
    print(f'OK Reel de Instagram programado para {cuando}.')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        sys.exit(__doc__)
    c, cuando = cargar(args[0]), args[1]
    if '--reel' in sys.argv:
        reel(c, cuando, json.load(open(os.path.join(RAIZ, 'contenido', 'config.json'))))
        return
    estado = 'draft' if '--borrador' in sys.argv else 'scheduled'
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
