"""Programa un carrusel de contenido/carruseles.json en el Instagram y/o el TikTok de Victoria (Publer).

Uso: python publer_carrusel.py <id> <cuando_utc> [--borrador] [--prueba] [--forzar]
     python publer_carrusel.py <id> --reel [auto|<cuando_utc>] [--prueba] [--solo-facebook]
     cuando_utc: "2026-11-03T00:45:00Z" (las dos redes) o una hora por red: "ig=...,tt=..."; con una sola red
                 ("tt=2026-11-03T21:00:00Z") se programa solo en esa red.
     --borrador  lo deja como borrador en Publer (no sale): para que Rodrigo lo vea antes.
     --prueba    imprime lo que mandaría, sin llamar a Publer.
     --forzar    lo programa aunque choque con otra publicación de ese día (ver ya_sale_ese_dia).
     --reel      sube el video del carrusel (carruseles/<id>/short.mp4, carrusel_video.py short) como Reel de
                 Instagram, el día de su carrusel en fotos y a 3 h o más de lo demás ("auto"). Con hora fija también
                 revisa el máximo del día (config → publicaciones_por_dia['ig']); --forzar lo salta.

Qué sale y dónde (Rodrigo, 2-nov-2026, con los datos de la semana: en TikTok los carruseles llegan a ~500
personas y los videos a ~100; en Instagram el Reel del carrusel c03 llegó a 28 y las fotos a 9):
- TikTok: un carrusel en fotos todos los días; el día con video, a otra hora.
- Instagram, los días sin video: el carrusel en fotos y su video como Reel. YouTube: su short (youtube.py).
Qué carrusel toca en cada red lo decide aprender.py auditar (decision.carruseles, con los comandos listos).
Antes: python carrusel.py <id> (las fotos en carruseles/<id>/). Al programar, guarda la hora de cada red en
carruseles.json (publica_utc_por_red) y lo marca "programado".
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
from publer import (facebook_victoria, _buscar_id, _pedir, _primera_linea, armar_post, comentarios, cuando_de, cuentas_victoria,  # noqa: E402
                    esperar_job, mandar, red, workspace_id, ya_programadas)
from aprender import CDMX, a_utc, publicaciones  # noqa: E402

CORTA = {'instagram': 'ig', 'tiktok': 'tt'}
RUTA = os.path.join(RAIZ, 'contenido', 'carruseles.json')


def comentario_ig(c, config):
    """Primer comentario (Instagram y TikTok): el llamado del carrusel sin enlace (ahí solo se toca el de la bio)."""
    if c.get('enlace'):
        return f"{c['enlace']['etiqueta']}: el enlace está en mi perfil 👆"
    return config.get('primer_comentario_instagram')


def redes_de(cuando):
    """Redes a programar: las dos con una sola hora; con "ig=...,tt=...", solo las que trae."""
    if '=' not in cuando:
        return ['instagram', 'tiktok']
    claves = dict(x.split('=', 1) for x in cuando.split(','))
    return [p for p, r in CORTA.items() if r in claves]


def ya_sale_ese_dia(c, cuando, todos, plan, proveedores):
    """Choques del mismo día (México). Rodrigo, 9-nov-2026: config.json → publicaciones_por_dia (TikTok 3, Instagram 2,
    YouTube 2), contando el video del día, y a 3 h o más de otra publicación de la misma red (a 2 h de un video en
    TikTok). El 30-oct salieron c02 y c03 casi juntos por no revisarlo."""
    por_dia = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json'))).get('publicaciones_por_dia') or {}
    choques = []
    for proveedor in proveedores:
        r = CORTA[proveedor]
        t = a_utc(cuando_de(cuando, proveedor)).astimezone(CDMX)
        mismos = []
        for x in todos:  # los Reels de carrusel no están en publicaciones(): van aparte en reel_ig
            hr = (x.get('reel_ig') or {}).get('publica_utc') if r == 'ig' and x['id'] != c['id'] else None
            if hr and a_utc(hr).astimezone(CDMX).date() == t.date():
                mismos.append(f"{x['id']} (Reel)")
                if abs(a_utc(hr).astimezone(CDMX) - t) < datetime.timedelta(hours=3):
                    choques.append(f"ig: Reel de {x['id']} a las {a_utc(hr).astimezone(CDMX):%H:%M} (menos de 3 h)")
        for x, h in publicaciones(plan, todos):
            if x['id'] == c['id'] or r not in h or h[r].date() != t.date():
                continue
            mismos.append(x['id'])
            cerca = datetime.timedelta(hours=3 if x['id'].startswith('c') else 2)
            if abs(h[r] - t) < cerca:
                choques.append(f"{r}: {x['id']} a las {h[r].strftime('%H:%M')} (menos de {cerca.seconds // 3600} h)")
        if len(mismos) >= por_dia.get(r, 1):
            choques.append(f"{r}: ya hay {len(mismos)} publicación(es) ese día ({', '.join(mismos)}); máximo {por_dia.get(r, 1)}")
    return choques


def red_post(proveedor, tipo_ig, media, texto, titulo):
    if proveedor == 'instagram':
        return {'type': tipo_ig, 'text': texto, 'media': media}
    return {'type': 'photo', 'title': titulo[:90], 'text': texto, 'media': media,
            'details': {'privacy': 'PUBLIC_TO_EVERYONE', 'auto_add_music': True, 'comment': True}}


def cuerpo(cuenta, tipo_ig, media, texto, titulo, cuando, estado, comentario=None):
    return {'bulk': {'state': estado, 'posts': [{
        'networks': {red(cuenta): red_post(red(cuenta), tipo_ig, media, texto, titulo)},
        'accounts': [{'id': cuenta['id'], 'scheduled_at': cuando, **comentarios(comentario)}]}]}}


def registrar(cid, horas):
    """Guarda en carruseles.json la hora de cada red programada y lo marca "programado"."""
    datos = json.load(open(RUTA))
    yo = next(x for x in datos['carruseles'] if x['id'] == cid)
    yo.setdefault('publica_utc_por_red', {}).update(horas)
    yo['publica_utc'] = max(yo['publica_utc_por_red'].values())
    if yo['estado'] == 'listo':
        yo['estado'] = 'programado'
    json.dump(datos, open(RUTA, 'w'), ensure_ascii=False, indent=1)


def texto_reel(c, config):
    """Pie del Reel: el gancho de la portada arriba y debajo el pie del carrusel completo (sus palabras clave).
    La primera línea tiene que ser distinta a la del carrusel: con ella se reconocen en Publer al medir."""
    primera = c['portada']['titulo'].strip()
    if _primera_linea(primera) == _primera_linea(c['texto_post']):
        sys.exit(f'ERROR: el Reel de {c["id"]} empezaría igual que su carrusel; cambia portada.titulo o texto_post.')
    return primera + '\n' + c['texto_post'].strip() + '\n\n' + ' '.join(hashtags_para('instagram', c['seo'], config))


def hora_reel(c, todos, plan, config, ahora):
    """El día del carrusel en Instagram (si ese día ya tiene sus config → publicaciones_por_dia['ig'], el siguiente), en
    la franja de Instagram más fuerte para ese día (orden_por_dia) a 3 h o más de cualquier otro post."""
    ocupadas = [h['ig'] for _, h in publicaciones(plan, todos) if 'ig' in h]
    reels = [a_utc(x['reel_ig']['publica_utc']).astimezone(CDMX) for x in todos
             if x['id'] != c['id'] and (x.get('reel_ig') or {}).get('publica_utc')]
    prueba = config.get('prueba_horas') or {}
    base = (c.get('publica_utc_por_red') or {}).get('ig') or c.get('publica_utc')
    dia = a_utc(base).astimezone(CDMX).date() if base else ahora.astimezone(CDMX).date()
    for d in (dia + datetime.timedelta(days=i) for i in range(4)):
        if sum(1 for t in ocupadas + reels if t.date() == d) >= (config.get('publicaciones_por_dia') or {}).get('ig', 1):
            continue
        orden = ((prueba.get('orden_por_dia') or {}).get('ig') or {}).get(str(d.weekday())) or prueba['franjas_por_red']['ig']
        for f in orden:
            t = datetime.datetime.combine(d, datetime.time.fromisoformat(f), tzinfo=CDMX)
            if t > ahora + datetime.timedelta(minutes=20) and all(abs(t - o) >= datetime.timedelta(hours=3) for o in ocupadas + reels):
                return t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    sys.exit(f'ERROR: no encontré hora libre para el Reel de {c["id"]} en 4 días; pásala a mano.')


def reel(c, cuando, config):
    """Programa el Reel de Instagram del carrusel y lo guarda en carruseles.json → reel_ig."""
    video = os.path.join(RAIZ, 'carruseles', c['id'], 'reel.mp4')  # con su propia portada (carrusel.py → 00r.png)
    if not os.path.exists(video):
        video = os.path.join(RAIZ, 'carruseles', c['id'], 'short.mp4')
    if not os.path.exists(video):
        sys.exit(f'ERROR: falta {video}: corre primero carrusel_video.py short {c["id"]}')
    datos = json.load(open(RUTA))
    yo = next(x for x in datos['carruseles'] if x['id'] == c['id'])
    # --solo-facebook: carruseles que ya salieron en las otras redes, solo a la página de Facebook (9-nov-2026)
    ya_ig = bool((yo.get('reel_ig') or {}).get('publica_utc')) or '--solo-facebook' in sys.argv
    if ya_ig and yo.get('facebook'):
        print(f'OMITIDO: el Reel de {c["id"]} ya está en Facebook ({yo["facebook"]["publica_utc"]}).')
        return
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    if cuando == 'auto':
        cuando = hora_reel(yo, datos['carruseles'], plan, config, datetime.datetime.now(datetime.timezone.utc))
    elif '--forzar' not in sys.argv and not ya_ig:
        choques = ya_sale_ese_dia(yo, cuando, datos['carruseles'], plan, ['instagram'])
        if choques:
            sys.exit(f'ERROR: el Reel choca con otra publicación de ese día ({"; ".join(choques)}). Otra hora, o --forzar.')
    texto = texto_reel(c, config)
    if '--prueba' in sys.argv:
        print(json.dumps(armar_post([{'id': 'ID_IG', 'provider': 'instagram'}], 'MEDIA_ID', texto, c['titulo_post'], cuando,
                                    comentario_ig(c, config)), ensure_ascii=False, indent=1))
        return
    ws = workspace_id()
    todas, cuentas = cuentas_victoria(ws)
    cuentas = [x for x in cuentas if red(x) == 'instagram' and not ya_ig]  # con Reel ya programado, solo falta Facebook
    if not cuentas and not ya_ig:
        sys.exit('ERROR: no encontré el Instagram de Victoria en Publer. No publico nada.')
    fb = facebook_victoria(todas)
    if fb:
        cuentas.append(fb)  # 9-nov-2026: el Reel de Instagram sale también en la página de Facebook, a la misma hora
    ya = ya_programadas(ws, cuentas, texto)
    cuentas = [x for x in cuentas if str(x['id']) not in ya]
    if not cuentas:
        print('OMITIDO: este Reel ya está programado o publicado en Instagram y Facebook.')
        return
    subida = _pedir('POST', '/media', ws, multipart=(f'{c["id"]}-reel.mp4', open(video, 'rb').read(), 'video/mp4'))
    media_id = subida.get('id') or (subida.get('data') or {}).get('id')
    if not media_id and subida.get('job_id'):
        media_id = _buscar_id(esperar_job(ws, subida['job_id']).get('result'))
    if not media_id:
        sys.exit(f'ERROR: la subida del video no regresó id: {json.dumps(subida)[:500]}')
    fallas, salieron = [], []
    for cuenta in cuentas:  # una petición por red (regla 5): si Facebook falla, Instagram no se pierde
        motivo = mandar(ws, armar_post([cuenta], media_id, texto, c['titulo_post'], cuando, comentario_ig(c, config)))
        if motivo:  # si Publer no acepta el primer comentario, sale sin él
            print(f'AVISO: Publer rechazó el {red(cuenta)} con primer comentario ({motivo[:200]}); lo mando sin comentario.')
            motivo = mandar(ws, armar_post([cuenta], media_id, texto, c['titulo_post'], cuando))
        if motivo:
            fallas.append(f'{red(cuenta)}: {motivo}')
        else:
            salieron.append(red(cuenta))
            print(f'OK {red(cuenta)} programado para {cuando}.')
    datos = json.load(open(RUTA))  # releído: la subida tarda y otro paso pudo escribir
    yo = next(x for x in datos['carruseles'] if x['id'] == c['id'])
    if 'facebook' in salieron:
        yo['facebook'] = {'publica_utc': cuando}
    if 'instagram' not in salieron:  # solo salió (o falló) Facebook: reel_ig no se toca
        json.dump(datos, open(RUTA, 'w'), ensure_ascii=False, indent=1)
        if fallas:
            sys.exit('ERROR: Publer reportó falla: ' + ' | '.join(fallas))
        return
    yo['reel_ig'] = {'publica_utc': cuando, 'texto': texto, 'video': os.path.relpath(video, RAIZ)}
    if yo['estado'] == 'listo':
        yo['estado'] = 'programado'
    json.dump(datos, open(RUTA, 'w'), ensure_ascii=False, indent=1)
    if fallas:
        sys.exit('ERROR: Publer reportó falla: ' + ' | '.join(fallas))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    if '--reel' in sys.argv and len(args) in (1, 2):
        return reel(cargar(args[0]), args[1] if len(args) == 2 else 'auto', config)
    if len(args) != 2:
        sys.exit(__doc__)
    c, cuando = cargar(args[0]), args[1]
    proveedores = redes_de(cuando)
    if not proveedores:
        sys.exit('ERROR: la hora no trae ig= ni tt=.')
    estado = 'draft' if '--borrador' in sys.argv else 'scheduled'
    if estado == 'scheduled' and '--forzar' not in sys.argv:
        todos = json.load(open(RUTA))['carruseles']
        choques = ya_sale_ese_dia(c, cuando, todos, json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json'))), proveedores)
        if choques:
            sys.exit(f'ERROR: choca con otra publicación de ese día ({"; ".join(choques)}). Elige otra hora u otro día, o usa --forzar.')
    fotos = sorted(glob.glob(os.path.join(RAIZ, 'carruseles', c['id'], '[0-9][0-9].png')))
    if len(fotos) != len(c['diapositivas']) + 2:
        sys.exit(f'ERROR: faltan fotos en carruseles/{c["id"]}: corre primero carrusel.py {c["id"]}')
    # Instagram busca por las palabras del pie y corta en 5 hashtags; TikTok, además, por las preguntas (docs/SEO.md).
    por_red = {'instagram': c['texto_post'].strip() + '\n\n' + ' '.join(hashtags_para('instagram', c['seo'], config)),
               'tiktok': '\n\n'.join([c['texto_post'].strip(), '🔎 ' + ' '.join(c['seo']['preguntas']),
                                       ' '.join(hashtags_para('tiktok', c['seo'], config))])}
    if '--prueba' in sys.argv:
        media = [{'id': f'MEDIA_{i}', 'type': 'image'} for i in range(len(fotos))]
        for p in proveedores:
            cuenta = {'id': f'ID_{CORTA[p].upper()}', 'provider': p}
            print(json.dumps(cuerpo(cuenta, 'photo', media, por_red[p], c['titulo_post'], cuando_de(cuando, p), estado,
                                    comentario_ig(c, config)), ensure_ascii=False, indent=1))
        return
    ws = workspace_id()
    _, cuentas = cuentas_victoria(ws)
    cuentas = [x for x in cuentas if red(x) in proveedores]
    if not cuentas:
        sys.exit('ERROR: no encontré las cuentas de Victoria en Publer. No publico nada.')
    repetidas = ya_programadas(ws, cuentas, por_red['instagram'])
    cuentas = [x for x in cuentas if str(x['id']) not in repetidas]
    if not cuentas:
        print('OMITIDO: este carrusel ya está programado o publicado en esas cuentas de Victoria.')
        return
    media = []
    for foto in fotos:
        subida = _pedir('POST', '/media', ws, multipart=(os.path.basename(foto), open(foto, 'rb').read(), 'image/png'))
        mid = subida.get('id') or (subida.get('data') or {}).get('id')
        if not mid:
            sys.exit(f'ERROR: la subida de {foto} no regresó id: {json.dumps(subida)[:500]}')
        media.append({'id': mid, 'type': 'image'})
    print(f'{len(media)} fotos subidas.')
    fallidas, horas = [], {}
    for cuenta in cuentas:
        # Instagram: Publer rechaza "carousel" (error interno) y acepta "photo" con varias fotos (probado 30-oct-2026).
        p, comentario = red(cuenta), comentario_ig(c, config)
        motivo = mandar(ws, cuerpo(cuenta, 'photo', media, por_red[p], c['titulo_post'], cuando_de(cuando, p), estado, comentario))
        if motivo and comentario:  # si Publer no acepta el primer comentario, sale sin él
            print(f'AVISO: Publer rechazó el carrusel con primer comentario ({motivo[:200]}); lo mando sin comentario.')
            motivo = mandar(ws, cuerpo(cuenta, 'photo', media, por_red[p], c['titulo_post'], cuando_de(cuando, p), estado))
        if motivo:
            fallidas.append(f'{p}: {motivo}')
        else:
            horas[CORTA[p]] = cuando_de(cuando, p)
            print(f'OK {p} {"borrador" if estado == "draft" else "programado para " + cuando_de(cuando, p)}.')
    if horas and estado == 'scheduled':
        registrar(c['id'], horas)
    if fallidas:
        sys.exit('ERROR: Publer reportó fallas en ' + ' | '.join(fallidas))


if __name__ == '__main__':
    main()
