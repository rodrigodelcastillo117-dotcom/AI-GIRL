"""Cliente mínimo de la API de Publer para publicar los videos de Victoria.

Lee PUBLER_API_KEY del entorno (nunca del repo). Comandos:

  python publer.py cuentas
      Lista workspaces y cuentas conectadas.
  python publer.py publicar video.mp4 texto.txt "2026-10-30T02:47:00Z" "Título corto" [--prueba]
      Sube el video, programa el post en las cuentas de Victoria y espera el resultado.
      Omite las cuentas que ya tienen un post con la misma primera línea (programado o publicado),
      por si una ejecución anterior publicó pero no pudo guardar su estado en el repo.
      --prueba arma el payload y lo imprime sin llamar a la API.
      Desde el 9-nov-2026 lo que sale en Instagram sale también en la página de Facebook (config → facebook_victoria),
      a la hora de Instagram. --solo-facebook lo publica solo en esa página (para lo ya publicado en las otras redes).

Solo publica en las cuentas de contenido/config.json → cuentas_publer, o cuyo nombre contiene
filtro_cuentas, para no publicar nunca en las cuentas de otras marcas del mismo workspace.
"""
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = 'https://app.publer.com/api/v1'
# Cloudflare de Publer rechaza la firma por defecto de Python (error 1010); nos identificamos con nombre propio
AGENTE = 'AI-GIRL-pipeline/1.0 (+https://github.com/rodrigodelcastillo117-dotcom/AI-GIRL)'
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
# YouTube no va por Publer (costaría una cuenta extra): lo sube scripts/youtube.py con la API gratis.
REDES = ('instagram', 'tiktok')  # Facebook va aparte (facebook_victoria): como video normal, no Reel (regla 28)


def _pedir(metodo, ruta, workspace=None, cuerpo=None, multipart=None):
    clave = os.environ.get('PUBLER_API_KEY')
    if not clave:
        sys.exit('ERROR: falta la variable de entorno PUBLER_API_KEY')
    headers = {'Authorization': f'Bearer-API {clave}', 'Accept': 'application/json', 'User-Agent': AGENTE}
    if workspace:
        headers['Publer-Workspace-Id'] = workspace
    datos = None
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode()
        headers['Content-Type'] = 'application/json'
    elif multipart is not None:
        limite = uuid.uuid4().hex
        nombre, contenido, tipo = multipart
        datos = (f'--{limite}\r\nContent-Disposition: form-data; name="file"; filename="{nombre}"\r\n'
                 f'Content-Type: {tipo}\r\n\r\n').encode() + contenido + f'\r\n--{limite}--\r\n'.encode()
        headers['Content-Type'] = f'multipart/form-data; boundary={limite}'
    req = urllib.request.Request(BASE + ruta, data=datos, headers=headers, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            texto = r.read().decode()
    except urllib.error.HTTPError as e:
        sys.exit(f'ERROR {e.code} en {metodo} {ruta}: {e.read().decode()[:1500]}')
    return json.loads(texto) if texto else {}


def _lista(respuesta, clave):
    """La documentación muestra a veces un arreglo y a veces {clave: [...]}."""
    if isinstance(respuesta, list):
        return respuesta
    return respuesta.get(clave) or respuesta.get('data') or []


def workspace_id():
    if os.environ.get('PUBLER_WORKSPACE_ID'):
        return os.environ['PUBLER_WORKSPACE_ID']
    ws = _lista(_pedir('GET', '/workspaces'), 'workspaces')
    if not ws:
        sys.exit('ERROR: la clave no tiene workspaces')
    return ws[0]['id']


def sin_perfil(texto, proveedor):
    """Mientras la bio de esa red no tenga el enlace (config.json → bio_con_enlace), "el enlace está en mi perfil" apunta a
    nada: se cambia por la dirección escrita, que se puede copiar o teclear (10-nov-2026)."""
    corta = {'instagram': 'ig', 'tiktok': 'tt'}.get(proveedor)
    if not texto or not corta or (CONFIG.get('bio_con_enlace') or {}).get(corta):
        return texto
    if corta == 'ig' and CONFIG.get('guia_por_mensaje_ig'):  # Instagram: comentar GUÍA trae el enlace por mensaje (comentarios_ig.py privado), y suma comentarios
        return re.sub(r'(el )?enlace (est[áa] )?en mi perfil\s*👆?', 'comenta GUÍA y te lo mando por mensaje 📩', texto)
    return re.sub(r'(el )?enlace (est[áa] )?en mi perfil\s*👆?', 'victoriatheceo.vercel.app', texto)


def guia_arriba(texto, comentario, proveedor):
    """Instagram con "Comenta GUÍA": la línea de la guía va también en el texto, debajo de la pregunta (la gente lee el
    texto, casi nadie el primer comentario). Rodrigo lo aprobó el 10-nov-2026."""
    if proveedor != 'instagram' or not CONFIG.get('guia_por_mensaje_ig') or not texto or 'GUÍA' in texto:
        return texto
    linea = next((l for l in (comentario or '').splitlines() if 'GUÍA' in l), None)
    if not linea:
        return texto
    lineas = texto.split('\n')
    i = 1
    while i < len(lineas) and lineas[i].strip().startswith(('💬', '👥')):
        i += 1
    return '\n'.join(lineas[:i] + [linea] + lineas[i:])


def pregunta_arriba(texto):
    """La pregunta para comentar ("💬 …") va en la segunda línea: TikTok e Instagram solo enseñan las primeras líneas
    sin tocar "más", y TikTok no acepta el primer comentario de Publer (10-nov-2026: 3,361 vistas y 0 comentarios en c16)."""
    if not texto:
        return texto
    lineas = texto.split('\n')
    # "Mándaselo a…" se vuelve "Etiqueta a…" (10-nov-2026): etiquetar cuenta como comentario y le avisa al etiquetado.
    lineas = [re.sub(r'^(\s*)📩\s*M[áa]ndaselo a\b', r'\1👥 Etiqueta a', l) for l in lineas]
    arriba = [l for l in lineas[1:] if l.strip().startswith(('💬', '👥'))]
    arriba.sort(key=lambda l: 0 if l.strip().startswith('💬') else 1)
    if not arriba:
        return '\n'.join(lineas)
    return '\n'.join([lineas[0]] + arriba + [l for l in lineas[1:] if l not in arriba])


def texto_facebook(texto, enlace=None, etiqueta=None):
    """Pie de Facebook: el de Instagram, pero ahí los enlaces sí se pueden tocar (9-nov-2026). "enlace en mi perfil"
    se cambia por el enlace directo con ?ref=fb; si no lo trae, se agrega el del carrusel o el de la página."""
    from seo import con_ref  # aquí y no arriba: seo importa de varios lados
    # Facebook castiga los textos con muchos hashtags (Meta, abr-2025): máximo 3 (config.json → max_hashtags.facebook).
    tope = CONFIG.get('max_hashtags', {}).get('facebook', 3)
    texto = '\n'.join(' '.join([w for w in l.split() if w.startswith('#')][:tope]) if l.strip().startswith('#') else l
                      for l in texto.split('\n'))
    url = con_ref(enlace or CONFIG.get('enlace_venta') or 'https://victoriatheceo.vercel.app', 'fb')
    nuevo, n = re.subn(r'enlace en mi perfil\s*👆?', url, texto)
    if n:
        return nuevo
    lineas = texto.rstrip().split('\n')
    corte = next((i for i in range(len(lineas) - 1, -1, -1) if lineas[i].strip() and not lineas[i].startswith('#')), len(lineas) - 1) + 1
    return '\n'.join(lineas[:corte] + [f"{etiqueta or '👉 Más de Victoria'}: {url}"] + lineas[corte:])


def facebook_victoria(todas):
    """La página de Facebook de Victoria (config.json → facebook_victoria, desde el 9-nov-2026), o None. Va aparte de
    cuentas_victoria para que medir y el tablero sigan solo con Instagram y TikTok."""
    fb = CONFIG.get('facebook_victoria')
    return next((c for c in todas if fb and c['id'] == fb and c.get('provider') == 'facebook'), None)


def cuentas_victoria(ws):
    todas = _lista(_pedir('GET', '/accounts', ws), 'accounts')
    filtro = CONFIG['filtro_cuentas'].lower()
    ids = CONFIG.get('cuentas_publer', {})  # la de Instagram era "Nadie Te lo Explicó" y Publer guarda el nombre viejo
    elegidas = [c for c in todas if c.get('provider') in REDES
                and (c['id'] in ids or filtro in (c.get('name') or '').lower())]
    return todas, elegidas


def _primera_linea(texto):
    lineas = (texto or '').strip().splitlines()
    return ' '.join(lineas[0].split()).lower() if lineas else ''


def ya_programadas(ws, cuentas, texto):
    """IDs de las cuentas que ya tienen un post con la misma primera línea, programado o publicado."""
    linea = _primera_linea(texto)
    hoy = datetime.date.today()
    filtros = [('state', 'all'), ('from', (hoy - datetime.timedelta(days=30)).isoformat()),
               ('to', (hoy + datetime.timedelta(days=60)).isoformat())]
    filtros += [('account_ids[]', c['id']) for c in cuentas]
    ids, pagina = set(), 0
    while True:
        r = _pedir('GET', '/posts?' + urllib.parse.urlencode(filtros + [('page', pagina)]), ws)
        for p in _lista(r, 'posts'):
            if any(x in (p.get('state') or '') for x in ('failed', 'deleted', 'draft')):
                continue
            if _primera_linea(p.get('text')) == linea:
                ids.add(str(p.get('account_id')))
        pagina += 1
        if pagina >= min(r.get('total_pages') or 0 if isinstance(r, dict) else 0, 20):
            return ids


def esperar_job(ws, job_id, intentos=60):
    for _ in range(intentos):
        r = _pedir('GET', f'/job_status/{job_id}', ws)
        datos = r.get('data', r)
        estado = datos.get('status')
        if estado in ('complete', 'completed', 'failed'):
            return datos
        time.sleep(5)
    sys.exit(f'ERROR: el job {job_id} no terminó a tiempo')


def _buscar_id(obj):
    """Primer campo "id" dentro del resultado anidado de un job de subida."""
    if isinstance(obj, dict):
        if isinstance(obj.get('id'), str):
            return obj['id']
        valores = obj.values()
    elif isinstance(obj, list):
        valores = obj
    else:
        return None
    for v in valores:
        encontrado = _buscar_id(v)
        if encontrado:
            return encontrado
    return None


def red(cuenta):
    return cuenta['provider']


def reprogramar(ws, post_id, cuando):
    """Cambia la hora de un post programado (PUT /posts/{id}/reschedule, documentado en
    publer.com/docs/posting/update-posts/unpublished-posts). Solo posts creados con esta clave y que no
    estén ya en la cola de publicación. Regresa la hora que quedó en Publer (para comprobarla)."""
    _pedir('PUT', f'/posts/{post_id}/reschedule', ws, cuerpo={'scheduled_at': cuando})
    r = _pedir('GET', f'/posts/{post_id}', ws)
    return (r.get('post') or r).get('scheduled_at')


def cuando_de(cuando, proveedor):
    """"2026-11-01T00:45:00Z" (la misma hora en todas) o "ig=...,tt=..." (una hora por red: prueba de horarios)."""
    if '=' not in cuando:
        return cuando
    # Facebook sale a la hora de Instagram (9-nov-2026).
    return dict(x.split('=', 1) for x in cuando.split(','))[{'instagram': 'ig', 'tiktok': 'tt', 'facebook': 'ig'}[proveedor]]


def mandar(ws, body):
    """None si Publer aceptó el post; si no, el motivo."""
    r = _pedir('POST', '/posts/schedule', ws, cuerpo=body)
    job = r.get('job_id') or (r.get('data') or {}).get('job_id')
    if not job:
        return f'Publer no regresó job_id ({json.dumps(r)[:300]})'
    resultado = esperar_job(ws, job)
    fallas = ((resultado.get('result') or resultado).get('payload') or {}).get('failures')
    if resultado.get('status') == 'failed' or fallas:
        return json.dumps(fallas or resultado, ensure_ascii=False)[:500]
    return None


def comentarios(texto):
    """Comentario de seguimiento que Publer publica 1 minuto después del post (Instagram y TikTok)."""
    return {'comments': [{'text': texto, 'delay': {'duration': 1, 'unit': 'Minute'}}]} if texto else {}


def armar_post(cuentas, media_id, texto, titulo, cuando, comentario=None):
    """comentario: primer comentario, como comentario de seguimiento de la cuenta (accounts[].comments con delay, docs de
    Publer). networks.instagram.firstComment lo aceptaba pero lo ignoraba (video 02, 31-oct: comments vacío). Solo se
    puede poner al crear el post: el PUT de Publer solo cambia texto y título."""
    redes = {}
    if len({red(c) for c in cuentas}) == 1:  # una red por petición (lo normal): texto y comentario sin "enlace en mi perfil"
        texto, comentario = pregunta_arriba(sin_perfil(texto, red(cuentas[0]))), sin_perfil(comentario, red(cuentas[0]))
    for proveedor in {red(c) for c in cuentas}:
        media = [{'id': media_id, 'type': 'video'}]
        if proveedor == 'instagram':
            redes['instagram'] = {'type': 'video', 'text': texto, 'media': media,
                                  'details': {'type': 'reel', 'feed': True}}
        elif proveedor == 'tiktok':
            redes['tiktok'] = {'type': 'video', 'title': titulo, 'text': texto, 'media': media,
                               'details': {'privacy': 'PUBLIC_TO_EVERYONE', 'comment': True}}
        elif proveedor == 'youtube':
            redes['youtube'] = {'type': 'short', 'title': titulo[:100], 'description': texto,
                                'privacy': 'public', 'media': media}
        elif proveedor == 'facebook':
            redes['facebook'] = {'type': 'video', 'title': titulo, 'text': texto, 'media': media}
    return {'bulk': {'state': 'scheduled', 'posts': [{
        'networks': redes,
        'accounts': [{'id': c['id'], 'scheduled_at': cuando, **comentarios(comentario)} for c in cuentas],
    }]}}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == 'cuentas':
        ws = workspace_id()
        todas, elegidas = cuentas_victoria(ws)
        print('workspace:', ws)
        for c in todas:
            marca = '  <- Victoria' if c in elegidas else ''
            print(f"  {c.get('provider'):10s} {c.get('type', ''):12s} {c.get('name')} ({c['id']}){marca}")
        return

    if sys.argv[1] != 'publicar' or len(sys.argv) < 6:
        sys.exit(__doc__)
    video, archivo_texto, cuando, titulo = sys.argv[2:6]
    prueba = '--prueba' in sys.argv
    texto = open(archivo_texto).read().strip()
    # Pie propio por red si seo.py lo dejó junto al texto (Instagram admite máximo 5 hashtags).
    carpeta = os.path.dirname(os.path.abspath(archivo_texto))
    por_red = {r: open(os.path.join(carpeta, f'texto_{r}.txt')).read().strip()
               for r in ('instagram', 'tiktok') if os.path.exists(os.path.join(carpeta, f'texto_{r}.txt'))}
    por_red['facebook'] = texto_facebook(por_red.get('instagram', texto))  # el de Instagram, con el enlace que se toca
    if len(titulo.strip()) < 5:  # Instagram pide título y TikTok mínimo 5 caracteres (regla 6)
        titulo = 'Victoria The CEO'

    if prueba:
        falsas = [{'id': 'ID_IG', 'provider': 'instagram'}, {'id': 'ID_TT', 'provider': 'tiktok'}]
        for c in falsas:
            print(json.dumps(armar_post([c], 'MEDIA_ID', por_red.get(red(c), texto), titulo, cuando_de(cuando, red(c))), ensure_ascii=False, indent=1))
        return

    ws = workspace_id()
    todas, cuentas = cuentas_victoria(ws)
    if not cuentas:
        sys.exit('ERROR: no encontré las cuentas de Victoria en Publer. No publico nada.')
    fb = facebook_victoria(todas)
    if '--solo-facebook' in sys.argv:  # 9-nov-2026: lo ya publicado en las otras redes, solo a la página nueva
        if not fb:
            sys.exit('ERROR: no encontré la página de Facebook de Victoria (config → facebook_victoria).')
        cuentas = [fb]
    elif fb and any(red(c) == 'instagram' for c in cuentas):
        cuentas.append(fb)  # lo que sale en Instagram sale también en Facebook
    print('Cuentas:', ', '.join(f"{red(c)}:{c.get('name')}" for c in cuentas))
    try:
        repetidas = ya_programadas(ws, cuentas, texto)
    except SystemExit as e:
        print(f'AVISO: no pude revisar si ya existía el post ({e}); sigo.')
        repetidas = set()
    if repetidas:
        print('Ya estaba programado o publicado en:', ', '.join(f"{red(c)}:{c.get('name')}" for c in cuentas if str(c['id']) in repetidas))
        cuentas = [c for c in cuentas if str(c['id']) not in repetidas]
        if not cuentas:
            print('OMITIDO: este post ya existe en todas las cuentas de Victoria. No subo nada.')
            return

    subida = _pedir('POST', '/media', ws, multipart=(os.path.basename(video), open(video, 'rb').read(), 'video/mp4'))
    media_id = subida.get('id') or (subida.get('data') or {}).get('id')
    if not media_id and subida.get('job_id'):
        media_id = _buscar_id(esperar_job(ws, subida['job_id']).get('result'))
    if not media_id:
        sys.exit(f'ERROR: la subida no regresó id de media: {json.dumps(subida)[:1500]}')
    print('Media subido:', media_id)

    # Una petición por red (regla 5): si una falla, las otras no se pierden y se sabe cuál fue.
    fallidas = []
    comentario = CONFIG.get('primer_comentario_instagram')
    for cuenta in cuentas:
        motivo = mandar(ws, armar_post([cuenta], media_id, por_red.get(red(cuenta), texto), titulo, cuando_de(cuando, red(cuenta)), comentario))
        if motivo and comentario:  # si Publer no acepta el comentario, el post sale sin él
            print(f'AVISO: Publer rechazó el post con primer comentario ({motivo[:200]}); lo mando sin comentario.')
            motivo = mandar(ws, armar_post([cuenta], media_id, por_red.get(red(cuenta), texto), titulo, cuando_de(cuando, red(cuenta))))
        if motivo:
            fallidas.append(f'{red(cuenta)}: {motivo}')
        else:
            print(f'OK {red(cuenta)} programado para {cuando_de(cuando, red(cuenta))}. Se confirma que salió en la siguiente medición.')
    if fallidas:
        sys.exit('ERROR: Publer reportó fallas en ' + ' | '.join(fallidas))


if __name__ == '__main__':
    main()
