"""Comentario propio de Victoria en TODO lo que se publica (Rodrigo, 12-nov-2026: "comenta siempre en YouTube, shorts y
videos largos, lo mismo en Instagram siempre comentario, Facebook igual").

Uso: python3 scripts/primer_comentario.py pendientes         publicaciones de los últimos 7 días sin comentario de Victoria
     python3 scripts/primer_comentario.py yt <video_id> "texto"
     python3 scripts/primer_comentario.py ig <media_id> "texto"
     python3 scripts/primer_comentario.py fb <post_id> "texto"   (necesita pages_manage_engagement en el token de Meta)

El texto lo escribe quien corre la revisión (nunca una plantilla fija: el mismo texto en todos los posts es spam para
YouTube e Instagram): una pregunta o un dato extra sobre ESE post, en la voz de Victoria, máximo 220 caracteres.
- YouTube: puede llevar enlace de victoriatheceo.vercel.app (la guía /reglas o la calculadora del tema). Fijarlo no se
  puede por API: Rodrigo lo fija a mano (sale en el resumen diario).
- Instagram: los enlaces en comentarios no se pueden tocar: en vez de enlace, "comenta GUÍA y te la mando".
- Facebook: enlace sí.
Registro: contenido/primeros_comentarios.json.
"""
import datetime
import json
import os
import sys
import urllib.parse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REGISTRO = os.path.join(RAIZ, 'contenido', 'primeros_comentarios.json')
DIAS = 7


def registro():
    return json.load(open(REGISTRO)) if os.path.exists(REGISTRO) else []


def anotar(red, pid, cid, texto):
    r = registro()
    r.append({'red': red, 'post': pid, 'comentario': cid, 'texto': texto,
              'fecha': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')})
    json.dump(r, open(REGISTRO, 'w'), ensure_ascii=False, indent=1)


def reciente(fecha):
    t = datetime.datetime.fromisoformat(fecha.replace('Z', '+00:00').replace('+0000', '+00:00'))
    return datetime.datetime.now(datetime.timezone.utc) - t < datetime.timedelta(days=DIAS)


def pendientes_yt():
    import youtube
    a = youtube.token()
    h = {'Authorization': f'Bearer {a}'}
    canal = youtube.CONFIG['canal_youtube']
    _, r = youtube._http('GET', f'{youtube.API}/channels?part=contentDetails&id={canal}', headers=h)
    subidas = json.loads(r)['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    _, r = youtube._http('GET', f'{youtube.API}/playlistItems?part=contentDetails&maxResults=30&playlistId={subidas}', headers=h)
    ids = [x['contentDetails']['videoId'] for x in json.loads(r).get('items', [])]
    if not ids:
        return []
    _, r = youtube._http('GET', f'{youtube.API}/videos?part=snippet,status,contentDetails&id={",".join(ids)}', headers=h)
    hechos = {x['post'] for x in registro() if x['red'] == 'yt'}
    salida = []
    for v in json.loads(r).get('items', []):
        if v['status'].get('privacyStatus') != 'public' or not reciente(v['snippet']['publishedAt']) or v['id'] in hechos:
            continue
        _, c = youtube._http('GET', f'{youtube.API}/commentThreads?part=snippet&maxResults=100&videoId={v["id"]}', headers=h)
        if any(t['snippet']['topLevelComment']['snippet'].get('authorChannelId', {}).get('value') == canal for t in json.loads(c).get('items', [])):
            continue
        dur = v['contentDetails'].get('duration', '')
        salida.append({'red': 'yt', 'id': v['id'], 'tipo': 'largo' if ('M' in dur and not dur.startswith('PT0M') and dur not in ('PT1M', 'PT2M', 'PT3M')) else 'short',
                       'titulo': v['snippet']['title'], 'texto_post': v['snippet'].get('description', '')[:300],
                       'url': f'https://youtube.com/watch?v={v["id"]}'})
    return salida


def pendientes_ig():
    from comentarios_ig import IG_USUARIO, YO, _http
    campos = 'id,caption,timestamp,permalink,media_product_type,comments.limit(50){username}'
    m = _http('GET', f'{IG_USUARIO}/media?fields={urllib.parse.quote(campos)}&limit=25')
    hechos = {x['post'] for x in registro() if x['red'] == 'ig'}
    salida = []
    for p in m.get('data', []):
        if not reciente(p['timestamp']) or p['id'] in hechos:
            continue
        if any(c.get('username') == YO for c in (p.get('comments') or {}).get('data', [])):
            continue
        salida.append({'red': 'ig', 'id': p['id'], 'tipo': p.get('media_product_type', ''), 'titulo': (p.get('caption') or '').split('\n')[0][:120],
                       'texto_post': (p.get('caption') or '')[:300], 'url': p.get('permalink')})
    return salida


def token_pagina(pagina):
    """Token de la página (lo da /me/accounts con el token de usuario de Meta). Solo vive en memoria: nunca se imprime."""
    from comentarios_ig import _http
    for p in _http('GET', 'me/accounts?fields=id,access_token&limit=50').get('data', []):
        if p['id'] == pagina:
            return p['access_token']
    raise RuntimeError('el token de Meta no administra la página de Victoria')


def fb(metodo, ruta, pagina, datos=None):
    """Graph API con el token de la página (comentar como la página, no como Rodrigo)."""
    import urllib.request
    tok = token_pagina(pagina)
    if metodo == 'GET':
        url = f'https://graph.facebook.com/v21.0/{ruta}{"&" if "?" in ruta else "?"}access_token={tok}'
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(f'https://graph.facebook.com/v21.0/{ruta}', data=urllib.parse.urlencode({**(datos or {}), 'access_token': tok}).encode(), method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'ERROR {e.code} de Facebook en {ruta.split("?")[0]}: {e.read().decode()[:300]}')


def pendientes_fb():
    """Página de Facebook: solo si el token tiene permiso de páginas (pages_read_engagement)."""
    import publer
    pagina = publer.CONFIG.get('facebook_pagina_id')
    if not pagina:
        return [{'red': 'fb', 'error': 'falta config.json → facebook_pagina_id y el permiso pages_manage_engagement del token de Meta'}]
    try:
        # Lo que publica Publer en la página son videos (el borde /posts solo trae cambios de foto): se revisan los videos.
        r = fb('GET', f'{pagina}/videos?fields=id,title,description,created_time,permalink_url,comments.limit(50){{from}}&limit=25', pagina)
    except (SystemExit, RuntimeError) as e:
        return [{'red': 'fb', 'error': str(e)[:200]}]
    hechos = {x['post'] for x in registro() if x['red'] == 'fb'}
    salida = []
    for p in r.get('data', []):
        if not reciente(p['created_time']) or p['id'] in hechos:
            continue
        if any((c.get('from') or {}).get('id') == pagina for c in (p.get('comments') or {}).get('data', [])):
            continue
        texto = p.get('title') or p.get('description') or ''
        salida.append({'red': 'fb', 'id': p['id'], 'titulo': texto.split('\n')[0][:120], 'texto_post': (p.get('description') or '')[:300],
                       'url': 'https://www.facebook.com' + p['permalink_url'] if str(p.get('permalink_url', '')).startswith('/') else p.get('permalink_url')})
    return salida


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    accion = sys.argv[1]
    if accion == 'pendientes':
        todo = []
        for f in (pendientes_yt, pendientes_ig, pendientes_fb):
            try:
                todo += f()
            except (SystemExit, Exception) as e:
                todo.append({'red': f.__name__[-2:], 'error': str(e)[:200]})
        print(json.dumps(todo, ensure_ascii=False, indent=1))
        return
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    pid, texto = sys.argv[2], sys.argv[3].strip()
    if len(texto) > 300:
        sys.exit('Máximo 300 caracteres')
    if accion == 'yt':
        import youtube
        cid = youtube.comentar(youtube.token(), pid, texto)
    elif accion == 'ig':
        from comentarios_ig import _http
        cid = _http('POST', f'{pid}/comments', {'message': texto}).get('id')
    elif accion == 'fb':
        import publer
        try:
            cid = fb('POST', f'{pid}/comments', publer.CONFIG['facebook_pagina_id'], {'message': texto}).get('id')
        except RuntimeError as e:
            if '(#200)' in str(e):  # video que no es publicación (sin comentarios posibles): se anota para no reintentarlo
                anotar('fb', pid, None, 'no admite comentarios')
                sys.exit(f'{pid}: Facebook no deja comentar ahí (no es una publicación); anotado para no reintentar')
            raise
    else:
        sys.exit(__doc__)
    anotar(accion, pid, cid, texto)
    print('ok', accion, pid, cid)


if __name__ == '__main__':
    main()
