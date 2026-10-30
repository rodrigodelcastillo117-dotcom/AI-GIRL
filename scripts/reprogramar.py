"""Mueve un video ya programado a otra hora en Instagram, TikTok y YouTube, con su SEO actual.

Uso: python reprogramar.py <id_video> <hora_utc>     ej. python reprogramar.py 01 2026-10-29T23:45:00Z

- Publer: la hora se cambia con PUT /posts/{id}/reschedule (publer.reprogramar; el PUT normal solo cambia
  texto y título). Su borrado (DELETE /posts) borra TODOS los posts no publicados del workspace si no
  reconoce los ids, incluidas otras marcas: NUNCA se usa.
- YouTube: se actualizan hora, título, descripción y etiquetas del mismo video (sigue privado
  hasta la hora nueva) y se verifica.
- Actualiza publica_utc del video en contenido/plan.json.
Solo toca posts en estado "scheduled": lo ya publicado no se mueve.
"""
import json
import os
import sys
import tempfile
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publer  # noqa: E402
import seo  # noqa: E402
import youtube  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def posts_programados(ws, linea):
    cuentas = publer.CONFIG.get('cuentas_publer', {})
    filtros = [('state', 'scheduled')] + [('account_ids[]', c) for c in cuentas]
    r = publer._pedir('GET', '/posts?' + urllib.parse.urlencode(filtros), ws)
    return [p for p in r.get('posts') or [] if seo_linea(p.get('text')) == linea]


def seo_linea(texto):
    lineas = (texto or '').strip().splitlines()
    return ' '.join(lineas[0].split()).lower() if lineas else ''


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    vid, cuando = sys.argv[1], sys.argv[2]
    ruta_plan = os.path.join(RAIZ, 'contenido', 'plan.json')
    plan = json.load(open(ruta_plan))
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    video = next(v for v in plan['videos'] if v['id'] == vid)
    textos = seo.textos(video, plan, config)
    carpeta = tempfile.mkdtemp(prefix=f'seo-{vid}-')
    for nombre, texto in textos.items():
        open(os.path.join(carpeta, f'{nombre}.txt'), 'w').write(texto)

    # Publer: se mueven con /reschedule y se comprueba la hora que quedó
    ws = publer.workspace_id()
    cuentas = publer.CONFIG.get('cuentas_publer', {})
    import datetime
    objetivo = datetime.datetime.fromisoformat(cuando.replace('Z', '+00:00'))
    pendientes_a_mano = []
    for p in posts_programados(ws, seo_linea(video['texto_post'])):
        hora = datetime.datetime.fromisoformat(p['scheduled_at'].replace('Z', '+00:00'))
        if abs((hora - objetivo).total_seconds()) > 60:
            quedo = publer.reprogramar(ws, p['id'], cuando)
            nueva = datetime.datetime.fromisoformat(str(quedo).replace('Z', '+00:00')) if quedo else hora
            if abs((nueva - objetivo).total_seconds()) > 60:
                pendientes_a_mano.append(f"{cuentas.get(p['account_id'], p['account_id'])} (quedó en {quedo})")
            else:
                print(f"Publer: {cuentas.get(p['account_id'])} movido a {quedo}")
        else:
            print(f"Publer: {cuentas.get(p['account_id'])} ya está a la hora nueva")

    # YouTube: mismo video, hora y SEO nuevos
    enlace = (video.get('publicacion') or {}).get('youtube', '')
    if enlace:
        id_yt = enlace.rstrip('/').split('/')[-1]
        acceso = youtube.token()
        canal_id, nombre = youtube.canal(acceso)
        if canal_id != config.get('canal_youtube'):
            sys.exit(f'ERROR: el permiso es del canal {nombre} ({canal_id}); no toco YouTube.')
        meta = youtube.metadatos(textos['titulo'], textos['descripcion_youtube'], cuando,
                                 textos['tags_youtube'].split(','))
        meta['id'] = id_yt
        cabeceras = {'Authorization': f'Bearer {acceso}', 'Content-Type': 'application/json; charset=UTF-8'}
        youtube._http('PUT', f'{youtube.API}/videos?part=snippet,status', json.dumps(meta).encode(), cabeceras)
        for intento in range(6):  # YouTube tarda unos segundos en mostrar el cambio
            _, cuerpo = youtube._http('GET', f'{youtube.API}/videos?part=snippet,status&id={id_yt}',
                                      headers={'Authorization': f'Bearer {acceso}'})
            item = json.loads(cuerpo)['items'][0]
            estado = item['status']
            if estado.get('publishAt', '')[:16] == cuando[:16]:
                break
            time.sleep(5)
        if item['snippet']['title'] != textos['titulo'] or estado.get('publishAt', '')[:16] != cuando[:16]:
            sys.exit(f"ERROR: YouTube no quedó como se pidió: {item['snippet']['title']} · {estado}")
        print(f"YouTube: {enlace} · {estado.get('privacyStatus')} hasta {estado.get('publishAt')} · \"{item['snippet']['title']}\"")

    video['publica_utc'] = cuando
    json.dump(plan, open(ruta_plan, 'w'), ensure_ascii=False, indent=2)
    if pendientes_a_mano:
        print('FALTA mover a mano en el calendario de Publer: ' + ', '.join(pendientes_a_mano))
        sys.exit(2)
    print(f'OK video {vid} movido a {cuando} en las tres redes')


if __name__ == '__main__':
    main()
