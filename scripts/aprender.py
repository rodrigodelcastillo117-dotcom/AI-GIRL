"""Cerebro de Victoria: verifica, mide, compara qué funciona y elige el siguiente video.

Uso:
  python aprender.py medir     Comprueba en cada red que los videos programados sí salieron (regla
                               34: nunca "publicado" sin verlo) y guarda en contenido/metricas.json
                               vistas, likes, comentarios y compartidos (Publer para TikTok e
                               Instagram; API de YouTube, con retención si el permiso lo incluye).
  python aprender.py auditar   Califica cada video por sus vistas a ~36 h contra la mediana del
                               canal (índice 1.0 = normal), compara tema, fondo, vestimenta, color,
                               gancho, título, día y hora, decide si hoy toca publicar, a qué hora
                               (prueba de franjas) y qué video. Escribe contenido/auditoria.json.

Reglas para no engañarse con pocos datos: un valor solo gana o pierde con al menos MIN_MUESTRAS
videos (los días de la semana, con 15: regla 29). De cada 10 videos, 7 aprovechan lo que gana y
3 exploran. Las reglas numeradas están en docs/REGLAS_APRENDIDAS.md.
"""
import datetime
import json
import os
import statistics
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CONTENIDO = os.path.join(RAIZ, 'contenido')
CDMX = datetime.timezone(datetime.timedelta(hours=-6))
DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
REDES = {'instagram': 'ig', 'tiktok': 'tt'}
MIN_MUESTRAS = 3
MIN_POR_ATRIBUTO = {'dia': 15}  # el "peor día" con menos de 15 videos es ruido (regla 29)
HORAS_CALIFICACION = 36   # se califica con la foto más cercana a 36 h (entre 20 y 60 h)
DIAS_DE_MEDICION = 14     # después de 14 días ya no se guardan fotos de ese video

FONDOS = {'jet': 'transporte', 'yate': 'transporte', 'coche': 'transporte',
          'recamara': 'casa', 'cocina': 'casa', 'sala': 'casa', 'sillon': 'casa',
          'oficina': 'negocios', 'hotel': 'negocios', 'palco_estadio': 'negocios',
          'restaurante': 'ocio', 'bar': 'ocio', 'jacuzzi': 'ocio', 'gimnasio': 'ocio', 'golf': 'ocio'}
ESTILOS = [('playa', ['traje de baño', 'bikini']), ('deportivo', ['deportivo', 'leggings', 'polo', 'visera']),
           ('casa', ['pijama']), ('noche', ['noche', 'cóctel', 'coctel', 'gala', 'terciopelo', 'satín']),
           ('ejecutivo', ['blazer', 'sastre', 'falda lápiz']), ('casual', ['suéter', 'jeans', 'lino', 'punto', 'camisero'])]
COLORES = {'blanco': 'claro', 'blanca': 'claro', 'marfil': 'claro', 'crema': 'claro', 'champaña': 'claro', 'beige': 'claro',
           'negro': 'negro', 'negra': 'negro', 'rojo': 'rojo', 'carmesí': 'rojo', 'vino': 'rojo', 'azul': 'azul',
           'verde': 'verde', 'camel': 'café', 'café': 'café', 'gris': 'gris', 'dorado': 'dorado', 'rosa': 'rosa'}
NOMBRES = {'pilar': 'El tema', 'formato': 'El formato', 'tipo_fondo': 'El tipo de fondo', 'locacion': 'El fondo', 'estilo_vestuario': 'La vestimenta',
           'color_vestuario': 'El color de ropa', 'tipo_gancho': 'El gancho', 'titulo_emoji': 'El título', 'titulo_largo': 'El largo del título',
           'titulo_tipo': 'El título', 'dia': 'El día', 'hora': 'La hora'}
NUMEROS = ['uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'veinte', 'treinta',
           'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa', 'cien', 'mil', 'por ciento']


def cargar(nombre, defecto):
    try:
        return json.load(open(os.path.join(CONTENIDO, nombre)))
    except (OSError, ValueError):
        return defecto


def guardar(nombre, datos):
    json.dump(datos, open(os.path.join(CONTENIDO, nombre), 'w'), ensure_ascii=False, indent=1)


def primera_linea(texto):
    lineas = (texto or '').strip().splitlines()
    return ' '.join(lineas[0].split()).lower() if lineas else ''


def a_utc(texto):
    return datetime.datetime.fromisoformat(texto.replace('Z', '+00:00')).astimezone(datetime.timezone.utc)


def adn(video):
    """Las características que se comparan. Si el video trae "adn" en el plan, manda ese."""
    vestuario = (video.get('vestuario') or '').lower()
    gancho = (video.get('guion') or '').split('.')[0].lower()
    color = min(((vestuario.find(p), c) for p, c in COLORES.items() if p in vestuario), default=(0, 'otro'))[1]
    estilo = next((e for e, claves in ESTILOS if any(c in vestuario for c in claves)), 'otro')
    if gancho.startswith('¿'):
        tipo = 'pregunta'
    elif any(p in gancho for p in ('error', 'estás perdiendo', 'te está costando', 'deja de ')):
        tipo = 'error'
    elif gancho.startswith(('no ', 'nunca ')) or ' no te va a ' in gancho:
        tipo = 'contradiccion'
    elif any(p in gancho for p in ('decía', 'lo llama', 'escribió', 'dijo')):
        tipo = 'cita'
    elif any(p in gancho for p in ('estudio', 'ley ', 'efecto', 'principio')):
        tipo = 'dato'
    elif 'regla' in gancho:
        tipo = 'regla'
    elif any(ch.isdigit() for ch in gancho) or any(f' {n} ' in f' {gancho} ' for n in NUMEROS):
        tipo = 'numero'
    else:
        tipo = 'consejo'
    datos = {'pilar': video.get('pilar'), 'formato': video.get('formato', 'a_camara'), 'locacion': video.get('locacion'),
             'tipo_fondo': FONDOS.get(video.get('locacion'), 'otro'), 'estilo_vestuario': estilo,
             'color_vestuario': color, 'tipo_gancho': tipo}
    titulo = (video.get('seo') or {}).get('titulo') or primera_linea(video.get('texto_post'))
    if titulo:
        largo = len(titulo)
        datos.update(titulo_emoji='con emoji' if any(ord(c) >= 0x2190 for c in titulo) else 'sin emoji',
                     titulo_largo='hasta 30' if largo <= 30 else '31 a 45' if largo <= 45 else 'más de 45',
                     titulo_tipo='pregunta' if '?' in titulo or '¿' in titulo else 'afirmación')
    if video.get('publica_utc'):
        local = a_utc(video['publica_utc']).astimezone(CDMX)
        datos.update(dia=DIAS[local.weekday()], hora=local.strftime('%H:%M'))
    datos.update(video.get('adn') or {})
    return datos


# ---------- medir ----------

def valor_publer(x):
    """Desde el 30-oct-2026 Publer manda cada métrica como {"name", "value", "tooltip"}; antes, un número."""
    if isinstance(x, dict):
        x = x.get('value')
    try:
        return int(float(x or 0))
    except (TypeError, ValueError):
        return 0


def medir_publer(videos):
    import publer
    ws = publer.workspace_id()
    cuentas = publer.CONFIG.get('cuentas_publer', {})
    # Facebook (9-nov-2026) se mide como 'fb': va en el centro y en la evolución diaria, pero no en la calificación
    # de videos (total() suma YouTube, TikTok e Instagram) ni en la prueba de horarios.
    fb = publer.CONFIG.get('facebook_victoria')
    por_linea = {primera_linea(v.get('texto_post')): v['id'] for v in videos}
    por_minuto = {v['publica_utc'][:16]: v['id'] for v in videos if v.get('publica_utc')}
    # El Reel de un carrusel (mismo video del Short) va aparte, como 'igr': sumado al carrusel inflaría su hora.
    reels = {primera_linea(v['texto_reel']): v['id'] for v in videos if v.get('texto_reel')}
    hoy = datetime.date.today()
    datos = {}
    for pagina in range(20):
        r = publer._pedir('GET', f'/analytics/post_insights?from={(hoy - datetime.timedelta(days=60)).isoformat()}'
                                 f'&to={hoy.isoformat()}&page={pagina}', ws)
        lote = r.get('posts') or []
        for p in lote:
            red = 'fb' if fb and p.get('account_id') == fb else REDES.get(cuentas.get(p.get('account_id')))
            if not red:
                continue
            minuto = a_utc(p['scheduled_at']).strftime('%Y-%m-%dT%H:%M') if p.get('scheduled_at') else ''
            video = por_linea.get(primera_linea(p.get('text'))) or (por_minuto.get(minuto) if red != 'fb' else None)
            if primera_linea(p.get('text')) in reels:
                video = reels[primera_linea(p.get('text'))]
                red = 'fb' if red == 'fb' else 'igr'  # en Facebook el Reel del carrusel es su único video
            if not video:
                continue
            a = p.get('analytics') or {}
            destino = datos.setdefault(video, {}).setdefault(red, {'v': 0, 'l': 0, 'c': 0, 's': 0})
            vistas = valor_publer(a.get('video_views'))
            destino['v'] += vistas if vistas else valor_publer(a.get('reach'))  # Publer dejó video_views vacío (30-oct-2026)
            for corto, campo in (('l', 'likes'), ('c', 'comments'), ('s', 'shares')):
                destino[corto] += valor_publer(a.get(campo))
        if len(lote) < 10:
            break
    return datos


def medir_youtube(videos):
    import youtube
    ids = {(v.get('publicacion') or {}).get('youtube', '').rstrip('/').split('/')[-1]: v['id'] for v in videos}
    ids.pop('', None)
    if not ids:
        return {}
    acceso = youtube.token()
    _, cuerpo = youtube._http('GET', f"{youtube.API}/videos?part=statistics&id={','.join(list(ids)[:50])}",
                              headers={'Authorization': f'Bearer {acceso}'})
    datos = {}
    for item in json.loads(cuerpo).get('items') or []:
        s = item['statistics']
        datos[ids[item['id']]] = {'yt': {'v': int(s.get('viewCount', 0)), 'l': int(s.get('likeCount', 0)),
                                         'c': int(s.get('commentCount', 0)), 's': 0}}
    return datos


def verificar_publer(videos):
    """{video_id: {red: {'estado', 'enlace'}}} de los posts de Victoria en Publer."""
    import urllib.parse
    import publer
    ws = publer.workspace_id()
    cuentas = publer.CONFIG.get('cuentas_publer', {})
    por_linea = {primera_linea(v.get('texto_post')): v['id'] for v in videos}
    hoy = datetime.date.today()
    filtros = [('state', 'all'), ('from', (hoy - datetime.timedelta(days=DIAS_DE_MEDICION + 2)).isoformat()),
               ('to', (hoy + datetime.timedelta(days=1)).isoformat())] + [('account_ids[]', c) for c in cuentas]
    datos = {}
    for pagina in range(20):
        r = publer._pedir('GET', '/posts?' + urllib.parse.urlencode(filtros + [('page', pagina)]), ws)
        for p in r.get('posts') or []:
            red = REDES.get(cuentas.get(p.get('account_id')))
            video = por_linea.get(primera_linea(p.get('text')))
            if red and video:
                datos.setdefault(video, {})[red] = {'estado': p.get('state') or '', 'enlace': p.get('post_link') or ''}
        if pagina + 1 >= (r.get('total_pages') or 0):
            break
    return datos


def verificar_youtube(videos):
    import youtube
    ids = {(v.get('publicacion') or {}).get('youtube', '').rstrip('/').split('/')[-1]: v['id'] for v in videos}
    ids.pop('', None)
    if not ids:
        return {}
    acceso = youtube.token()
    _, cuerpo = youtube._http('GET', f"{youtube.API}/videos?part=status&id={','.join(list(ids)[:50])}",
                              headers={'Authorization': f'Bearer {acceso}'})
    largos = {v['id'] for v in videos if v.get('capitulos')}
    return {ids[i['id']]: {'yt': {'estado': i['status'].get('privacyStatus', ''),
                                  'enlace': f"https://youtube.com/{'watch?v=' if ids[i['id']] in largos else 'shorts/'}{i['id']}"}}
            for i in json.loads(cuerpo).get('items') or []}


def retencion_youtube(videos):
    """% promedio visto de cada Short (YouTube Analytics). Necesita el permiso yt-analytics.readonly."""
    import youtube
    ids = {(v.get('publicacion') or {}).get('youtube', '').rstrip('/').split('/')[-1]: v['id'] for v in videos}
    ids.pop('', None)
    if not ids:
        return {}
    acceso = youtube.token()
    hoy = datetime.date.today()
    url = ('https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==MINE'
           f"&startDate={(hoy - datetime.timedelta(days=30)).isoformat()}&endDate={hoy.isoformat()}"
           '&metrics=views,averageViewPercentage,averageViewDuration&dimensions=video'
           f"&filters=video=={','.join(list(ids)[:50])}")
    _, cuerpo = youtube._http('GET', url, headers={'Authorization': f'Bearer {acceso}'})
    filas = json.loads(cuerpo).get('rows') or []
    return {ids[f[0]]: {'ret': round(f[2], 1), 'seg': round(f[3], 1)} for f in filas if f[0] in ids}


def ajenos(plan):
    """Posts publicados en las cuentas de Victoria en los últimos 3 días que no son del plan."""
    import urllib.parse
    import publer
    ws = publer.workspace_id()
    cuentas = publer.CONFIG.get('cuentas_publer', {})
    propias = {primera_linea(v.get('texto_post')) for v in plan['videos'] + plan.get('largos', [])}
    for c in cargar('carruseles.json', {'carruseles': []})['carruseles']:
        propias |= {primera_linea(c.get('texto_post')), primera_linea((c.get('reel_ig') or {}).get('texto'))}
    hoy = datetime.date.today()
    filtros = [('state', 'published'), ('from', (hoy - datetime.timedelta(days=3)).isoformat()),
               ('to', (hoy + datetime.timedelta(days=1)).isoformat())] + [('account_ids[]', c) for c in cuentas]
    r = publer._pedir('GET', '/posts?' + urllib.parse.urlencode(filtros), ws)
    return [f"Post AJENO publicado en {cuentas.get(p.get('account_id'))} el {str(p.get('scheduled_at'))[:16]}: "
            f"\"{(p.get('text') or '').strip().splitlines()[0][:60] if (p.get('text') or '').strip() else ''}\" ({p.get('post_link')})"
            for p in r.get('posts') or [] if primera_linea(p.get('text')) not in propias]


def comentar_enlace(video, plan, avisos):
    """Primer comentario con el enlace de la guía en el video de YouTube recién verificado (regla 25)."""
    config = cargar('config.json', {})
    publicacion = video.setdefault('publicacion', {})
    if not config.get('enlace_venta') or publicacion.get('comentario_youtube') or not publicacion.get('youtube'):
        return
    import seo
    import youtube
    try:
        texto = seo.textos(video, plan, config)['comentario_youtube']
        id_yt = publicacion['youtube'].rstrip('/').split('/')[-1].split('=')[-1]
        publicacion['comentario_youtube'] = youtube.comentar(youtube.token(), id_yt, texto)
    except SystemExit as e:
        avisos.append(f"No pude dejar el comentario con enlace en el video {video['id']}: {str(e)[:200]}")


def verificar(plan, ahora, avisos):
    """Marca "publicado" solo lo que se ve publicado en la red; avisa de lo que no salió (regla 34)."""
    programados = [v for v in plan['videos'] + plan.get('largos', []) if v.get('estado') == 'programado' and v.get('publica_utc')
                   and a_utc(v['publica_utc']) + datetime.timedelta(minutes=30) <= ahora]
    if not programados:
        return []
    estados = {}
    for nombre, funcion in (('Publer', verificar_publer), ('YouTube', verificar_youtube)):
        try:
            for vid, redes in funcion(programados).items():
                estados.setdefault(vid, {}).update(redes)
        except SystemExit as e:
            avisos.append(f'No pude verificar en {nombre}: {e}')
            return []  # sin verificación completa no se afirma nada
    problemas = []
    for v in programados:
        redes = estados.get(v['id'], {})
        faltan = []
        for red, nombre in (('ig', 'Instagram'), ('tt', 'TikTok'), ('yt', 'YouTube')):
            dato = redes.get(red)
            salio = dato and (dato['estado'] == 'public' if red == 'yt' else dato['estado'].startswith('published'))
            if not salio:
                faltan.append(f"{nombre} ({dato['estado'] if dato else 'no encontrado'})")
        if faltan:
            problemas.append(f"El video {v['id']} no aparece publicado en: {', '.join(faltan)}.")
        else:
            v['estado'] = 'publicado'
            v.setdefault('publicacion', {}).update({r: d['enlace'] for r, d in redes.items() if d.get('enlace')})
            comentar_enlace(v, plan, avisos)
    guardar('plan.json', plan)
    return problemas


def vigilar_youtube(plan, avisos):
    """La automatización de Errores invisibles (ES DE RODRIGO; el canal antes era de ese proyecto) metió sus enlaces (erroresinvisibles.gumroad.com) en las descripciones
    y les puso el audio en inglés (30-oct-2026). Cada día: quita los enlaces que no son de Victoria, deja el idioma en
    español y lo avisa, porque significa que alguien más sigue entrando al canal."""
    import re
    import youtube
    propios = ('victoriatheceo.vercel.app',)
    ids = [(v.get('publicacion') or {}).get('youtube', '') for v in plan['videos'] + plan.get('largos', [])]
    ids += [c.get('youtube', '') for c in cargar('carruseles.json', {'carruseles': []})['carruseles']]
    ids = [i.rstrip('/').split('/')[-1].split('=')[-1] for i in ids if i]
    if not ids:
        return
    acceso = youtube.token()
    h = {'Authorization': f'Bearer {acceso}', 'Content-Type': 'application/json; charset=UTF-8'}
    for inicio in range(0, len(ids), 50):
        _, cuerpo = youtube._http('GET', f"{youtube.API}/videos?part=snippet&id={','.join(ids[inicio:inicio + 50])}", headers=h)
        for item in json.loads(cuerpo).get('items') or []:
            sn = item['snippet']
            ajenos = [u for u in re.findall(r'https?://\S+', sn.get('description', '')) if not any(d in u for d in propios)]
            if not ajenos and sn.get('defaultAudioLanguage', 'es').startswith('es'):
                continue
            lineas = [l for l in sn.get('description', '').split('\n')
                      if not any(u in l for u in ajenos) and 'Si te gustan estos datos' not in l]
            limpia = re.sub(r'\n{3,}', '\n\n', '\n'.join(lineas)).strip()
            nuevo = {'id': item['id'], 'snippet': {'title': sn['title'], 'categoryId': sn['categoryId'], 'description': limpia,
                     'tags': sn.get('tags', []), 'defaultLanguage': 'es', 'defaultAudioLanguage': 'es'}}
            youtube._http('PUT', f"{youtube.API}/videos?part=snippet", json.dumps(nuevo).encode(), h)
            avisos.append(f"Alguien cambió el video de YouTube {item['id']} (enlaces ajenos: {', '.join(ajenos) or 'ninguno'}; "
                          f"audio {sn.get('defaultAudioLanguage')}). Ya lo restauré. Fue la automatización de Errores invisibles de Rodrigo "
                          "(es suya: no preguntar), que sigue escribiendo en este canal.")
    # El perfil del canal (3-nov-2026 tenía palabras clave de psicología, idioma inglés y descripción vieja): se compara
    # con config.json → canal_youtube y se restaura si alguien lo cambió.
    config = cargar('config.json', {})
    canal = config.get('canal_youtube_perfil')
    if canal:
        _, cuerpo = youtube._http('GET', f"{youtube.API}/channels?part=brandingSettings&mine=true", headers=h)
        item = (json.loads(cuerpo).get('items') or [{}])[0]
        b = item.get('brandingSettings') or {}
        ch = b.get('channel') or {}
        if any(ch.get(k) != canal[k] for k in ('description', 'keywords', 'defaultLanguage')):
            nuevo = {'channel': {**{k: ch.get(k) for k in ('title', 'country') if ch.get(k)}, **canal}}
            if b.get('image'):
                nuevo['image'] = b['image']
            youtube._http('PUT', f"{youtube.API}/channels?part=brandingSettings",
                          json.dumps({'id': item['id'], 'brandingSettings': nuevo}).encode(), h)
            avisos.append('Alguien cambió el perfil del canal de YouTube (descripción, palabras clave o idioma). Ya lo restauré.')


def comentar_carruseles(carruseles_json, avisos):
    """Primer comentario con el enlace en el Short de cada carrusel ya público (regla 25; fijarlo es manual).
    En Shorts YouTube no deja tocar enlaces de comentarios (desde ago-2023): por eso también manda al de su canal."""
    import seo
    import youtube
    config = cargar('config.json', {})
    datos = cargar(carruseles_json, {'carruseles': []})
    pendientes = {c['youtube'].rstrip('/').split('/')[-1]: c for c in datos['carruseles']
                  if c.get('youtube') and not c.get('comentario_youtube') and config.get('enlace_venta')}
    if not pendientes:
        return
    acceso = youtube.token()
    _, cuerpo = youtube._http('GET', f"{youtube.API}/videos?part=status&id={','.join(pendientes)}",
                              headers={'Authorization': f'Bearer {acceso}'})
    for item in json.loads(cuerpo).get('items') or []:
        if item['status'].get('privacyStatus') != 'public':
            continue
        c = pendientes[item['id']]
        if c.get('enlace'):
            texto = f"{c['enlace']['etiqueta']} 👉 {seo.con_ref(c['enlace']['url'], 'yt')}"
        else:
            texto = config['comentario_youtube'].format(enlace=seo.con_ref(config['enlace_venta'], 'yt'))
        try:
            c['comentario_youtube'] = youtube.comentar(acceso, item['id'], texto + '\nSi no te deja tocarlo, está en el enlace de mi canal.')
            avisos.append(f"Fija a mano el comentario con enlace del carrusel {c['id']}: https://studio.youtube.com/video/{item['id']}/comments")
        except SystemExit as e:
            avisos.append(f"No pude dejar el comentario con enlace en el Short del carrusel {c['id']}: {str(e)[:200]}")
    guardar(carruseles_json, datos)


def sincronizar_horas_publer(carruseles_json, avisos):
    """La hora real de Instagram y TikTok es la que tiene Publer (ahí se pueden mover a mano): se copia al
    carrusel para que la prueba de horarios cuente la hora real, se haya movido o no."""
    import urllib.parse
    import publer
    datos = cargar(carruseles_json, {'carruseles': []})
    lista = [c for c in datos['carruseles'] if c.get('publica_utc_por_red') and c.get('estado') in ('programado', 'publicado')]
    if not lista:
        return
    ws = publer.workspace_id()
    cuentas = publer.CONFIG.get('cuentas_publer', {})
    hoy = datetime.date.today()
    filtros = [('state', 'all'), ('from', (hoy - datetime.timedelta(days=DIAS_DE_MEDICION)).isoformat()),
               ('to', (hoy + datetime.timedelta(days=30)).isoformat())] + [('account_ids[]', c) for c in cuentas]
    r = publer._pedir('GET', '/posts?' + urllib.parse.urlencode(filtros), ws)
    cambio = False
    for p in r.get('posts') or []:
        red = REDES.get(cuentas.get(p.get('account_id')))
        if not red or not p.get('scheduled_at') or any(x in (p.get('state') or '') for x in ('draft', 'failed', 'deleted')):
            continue
        for c in lista:
            reel = c.get('reel_ig') or {}
            if reel.get('texto') and primera_linea(reel['texto']) == primera_linea(p.get('text')):
                real = a_utc(p['scheduled_at']).strftime('%Y-%m-%dT%H:%M:%SZ')
                if reel.get('publica_utc') != real:
                    reel['publica_utc'], cambio = real, True
                continue
            if primera_linea(c.get('texto_post')) == primera_linea(p.get('text')):
                real = a_utc(p['scheduled_at']).strftime('%Y-%m-%dT%H:%M:%SZ')
                if c['publica_utc_por_red'].get(red) != real:
                    c['publica_utc_por_red'][red] = real
                    cambio = True
                if (c.get('publer_por_mover') or {}).get(red, '')[:16] == real[:16]:
                    c['publer_por_mover'].pop(red)
                    cambio = True
    for c in lista:
        if c.get('publer_por_mover') == {}:
            c.pop('publer_por_mover')
        c['publica_utc'] = max(c['publica_utc_por_red'].values())
    if cambio:
        guardar(carruseles_json, datos)


def medir():
    plan = cargar('plan.json', {'videos': []})
    ahora = datetime.datetime.now(datetime.timezone.utc)
    avisos_verificacion = []
    problemas = verificar(plan, ahora, avisos_verificacion)
    try:
        problemas += ajenos(plan)
    except SystemExit as e:
        avisos_verificacion.append(f'No pude revisar posts ajenos en Publer: {e}')
    guardar('verificacion.json', {'fecha_utc': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'), 'problemas': problemas,
                                  'avisos': avisos_verificacion})
    for p in problemas + avisos_verificacion:
        print('VERIFICACIÓN:', p)
    videos = [v for v in plan['videos'] if v.get('publica_utc') and a_utc(v['publica_utc']) <= ahora
              and (ahora - a_utc(v['publica_utc'])).days <= DIAS_DE_MEDICION]
    try:
        sincronizar_horas_publer('carruseles.json', avisos_verificacion)
    except SystemExit as e:
        avisos_verificacion.append(f'No pude leer de Publer la hora real de los carruseles: {e}')
    try:
        vigilar_youtube(plan, avisos_verificacion)
    except SystemExit as e:
        avisos_verificacion.append(f'No pude revisar las descripciones de YouTube: {e}')
    try:
        comentar_carruseles('carruseles.json', avisos_verificacion)
    except SystemExit as e:
        avisos_verificacion.append(f'No pude revisar los comentarios con enlace de los carruseles: {e}')
    # Lo de arriba agrega avisos (comentarios por fijar, YouTube restaurado) después del primer guardado.
    guardar('verificacion.json', {'fecha_utc': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'), 'problemas': problemas,
                                  'avisos': avisos_verificacion})
    for c in cargar('carruseles.json', {'carruseles': []})['carruseles']:  # los carruseles también se miden
        if c.get('publica_utc') and a_utc(c['publica_utc']) <= ahora and (ahora - a_utc(c['publica_utc'])).days <= DIAS_DE_MEDICION:
            videos.append({'id': c['id'], 'texto_post': c['texto_post'], 'publica_utc': c['publica_utc'],
                           'texto_reel': (c.get('reel_ig') or {}).get('texto'),
                           'publica_utc_por_red': c.get('publica_utc_por_red'), 'publicacion': {'youtube': c.get('youtube', '')}})
    if not videos:
        print('medir: todavía no hay videos publicados que medir')
        return
    juntos, avisos = {}, []
    for nombre, funcion in (('Publer', medir_publer), ('YouTube', medir_youtube)):
        try:
            for vid, redes in funcion(videos).items():
                juntos.setdefault(vid, {}).update(redes)
        except SystemExit as e:  # los scripts de Publer y YouTube salen con SystemExit si algo falla
            avisos.append(f'{nombre}: {e}')
    try:
        for vid, ret in retencion_youtube(videos).items():
            juntos.setdefault(vid, {}).setdefault('yt', {}).update(ret)
    except SystemExit as e:
        avisos.append('Retención de YouTube no disponible (falta el permiso yt-analytics.readonly o la API de '
                      f'YouTube Analytics): {str(e)[:160]}')
    historial = cargar('metricas.json', [])
    for v in videos:
        horas = round((ahora - a_utc(v['publica_utc'])).total_seconds() / 3600, 1)
        fila = juntos.get(v['id'], {})
        for r, datos_red in fila.items():  # cada red salió a su hora (prueba de horarios por red)
            t = (v.get('publica_utc_por_red') or {}).get(r)
            if t and isinstance(datos_red, dict):
                datos_red['h'] = round((ahora - a_utc(t)).total_seconds() / 3600, 1)
        historial.append({'fecha_utc': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'), 'video_id': v['id'], 'horas': horas, **fila})
    guardar('metricas.json', historial)
    for a in avisos:
        print('AVISO medir:', a)
    print(f'medir: {len(videos)} videos medidos')


# ---------- auditar ----------

def total(foto, campo='v'):
    return sum((foto.get(r) or {}).get(campo, 0) for r in ('yt', 'tt', 'ig'))


def calificar(plan, historial):
    """{video_id: {vistas_36h, engagement, retencion}} con la foto más cercana a 36 h."""
    notas = {}
    for v in plan['videos']:
        fotos = [f for f in historial if f['video_id'] == v['id'] and 20 <= f['horas'] <= 60]
        if not fotos:
            continue
        foto = min(fotos, key=lambda f: abs(f['horas'] - HORAS_CALIFICACION))
        vistas = total(foto)
        interaccion = total(foto, 'l') + total(foto, 'c') + total(foto, 's')
        ultima_ret = next((f['yt']['ret'] for f in reversed(historial)
                           if f['video_id'] == v['id'] and (f.get('yt') or {}).get('ret') is not None), None)
        notas[v['id']] = {'vistas_36h': vistas, 'engagement': round(interaccion / vistas, 4) if vistas else 0,
                          'retencion': ultima_ret, 'horas': foto['horas']}
    return notas


def minimo(atributo, config):
    if atributo == 'hora':
        return (config.get('prueba_horas') or {}).get('min_por_franja', 5)
    return MIN_POR_ATRIBUTO.get(atributo, MIN_MUESTRAS)


def comparar(plan, notas, config):
    base = statistics.median([n['vistas_36h'] for n in notas.values()]) if notas else 0
    for n in notas.values():
        n['indice'] = round(n['vistas_36h'] / base, 2) if base else 0
    grupos = {}
    for v in plan['videos']:
        if v['id'] not in notas:
            continue
        for atributo, valor in adn(v).items():
            grupos.setdefault(atributo, {}).setdefault(valor, []).append(notas[v['id']])
    ranking = {}
    for atributo, valores in grupos.items():
        filas = []
        for valor, lista in valores.items():
            indice = round(statistics.mean(x['indice'] for x in lista), 2)
            estado = 'en prueba'
            if len(lista) >= minimo(atributo, config):
                estado = 'gana' if indice >= 1.2 else 'pierde' if indice <= 0.8 else 'normal'
            retenciones = [x['retencion'] for x in lista if x.get('retencion') is not None]
            filas.append({'valor': valor, 'n': len(lista), 'indice': indice, 'estado': estado,
                          'engagement': round(statistics.mean(x['engagement'] for x in lista), 4),
                          'retencion': round(statistics.mean(retenciones), 1) if retenciones else None})
        ranking[atributo] = sorted(filas, key=lambda f: -f['indice'])
    return base, ranking


CORTAS = ('ig', 'tt', 'yt')
DIAS_SEMANA = ('lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')


def franjas_de(red, config):
    """Horarios a probar en una red (config.json → prueba_horas.franjas_por_red; si no, los comunes)."""
    prueba = config.get('prueba_horas') or {}
    return (prueba.get('franjas_por_red') or {}).get(red) or prueba.get('franjas') or [config.get('hora_por_defecto', '18:45')]


def franja_de(t, red, config):
    """Franja de la prueba a la que pertenece una hora real: a 20 min o menos de ella (las 11:17 cuentan
    en la de las 11:00); si no cae en ninguna, la hora tal cual (no suma a la prueba)."""
    for f in franjas_de(red, config):
        h, m = map(int, f.split(':'))
        if abs(t.hour * 60 + t.minute - (h * 60 + m)) <= 20:
            return f
    return t.strftime('%H:%M')


def publicaciones(plan, carruseles):
    """Cada video o carrusel programado o publicado, con su hora (México) en cada red."""
    for x in plan['videos'] + carruseles:
        if x.get('estado') not in ('programado', 'publicado'):
            continue
        por_red = x.get('publica_utc_por_red') or ({r: x['publica_utc'] for r in CORTAS} if x.get('publica_utc') else {})
        yield x, {r: a_utc(t).astimezone(CDMX) for r, t in por_red.items()}


def horarios(plan, carruseles, config, fecha, ahora):
    """Hora de cada red para lo que sale en `fecha`. Cada red rota por las franjas hasta tener
    min_por_franja en cada una (y empieza en otra franja, así el mismo día salen a horas distintas);
    con ganadora, 4 de cada 5 publicaciones van a esa hora y 1 sigue probando."""
    prueba = config.get('prueba_horas') or {}
    minimo_f = prueba.get('min_por_franja', 4)
    ganadoras = prueba.get('ganadoras') or {}
    conteo = {r: {f: 0 for f in franjas_de(r, config)} for r in CORTAS}
    for _, horas in publicaciones(plan, carruseles):
        for r, t in horas.items():
            if r in conteo and franja_de(t, r, config) in conteo[r]:
                conteo[r][franja_de(t, r, config)] += 1
    a_hora = lambda f: datetime.datetime.combine(fecha, datetime.time.fromisoformat(f), tzinfo=CDMX)
    reels = [a_utc(c['reel_ig']['publica_utc']) for c in carruseles if (c.get('reel_ig') or {}).get('publica_utc')]
    lejos_de_reels = lambda f: all(abs(a_hora(f) - t) >= datetime.timedelta(hours=2) for t in reels)
    elegidas, cuando = {}, {}
    for i, r in enumerate(CORTAS):
        franjas = franjas_de(r, config)
        libres = [f for f in franjas if a_hora(f) > ahora + datetime.timedelta(minutes=20)
                  and (r != 'ig' or lejos_de_reels(f))] or franjas[-1:]
        if ganadoras.get(r) in libres and sum(conteo[r].values()) % 5:
            f = ganadoras[r]
        else:
            # Entre las menos probadas, primero la más fuerte para este día según los estudios (orden_por_dia).
            orden = ((prueba.get('orden_por_dia') or {}).get(r) or {}).get(str(fecha.weekday())) or []
            rango = lambda x: orden.index(x) if x in orden else len(orden) + (franjas.index(x) - 2 * i) % len(franjas)
            f = min(libres, key=lambda x: (conteo[r][x], rango(x)))
        elegidas[r] = f
        cuando[r] = a_hora(f).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    estado = ' · '.join(f"{r}: {'fija ' + ganadoras[r] if ganadoras.get(r) else 'en prueba'} ("
                        + ', '.join(f'{f} {conteo[r][f]}/{minimo_f}' for f in franjas_de(r, config)) + ')' for r in CORTAS)
    return elegidas, cuando, conteo, estado


def horas_por_red(plan, carruseles, historial, config):
    """Qué franja y qué día rinden más en cada red. Vistas a ~36 h en esa red, divididas entre la
    mediana de esa red y ese formato (video o carrusel) para no mezclarlos. Fija la ganadora de la red
    cuando todas las franjas tienen min_por_franja y la mejor rinde 20% más que la segunda."""
    filas = []
    for x, horas in publicaciones(plan, carruseles):
        tipo = 'carrusel' if x['id'].startswith('c') else 'video'
        for r, t in horas.items():
            fotos = [(f, (f.get(r) or {}).get('h') or f['horas']) for f in historial
                     if f['video_id'] == x['id'] and (f.get(r) or {}).get('v') is not None]
            fotos = [(f, h) for f, h in fotos if 20 <= h <= 60]
            if fotos:
                f, _ = min(fotos, key=lambda par: abs(par[1] - HORAS_CALIFICACION))
                filas.append((r, tipo, franja_de(t, r, config), DIAS_SEMANA[t.weekday()], f[r]['v']))
    medianas = {}
    for r, tipo, *_, v in filas:
        medianas.setdefault((r, tipo), []).append(v)
    medianas = {k: statistics.median(v) for k, v in medianas.items()}
    prueba = config.get('prueba_horas') or {}
    minimo_f = prueba.get('min_por_franja', 4)
    salida = {}
    for r in CORTAS:
        grupos = {'franjas': {}, 'dias': {}}
        for rr, tipo, franja, dia, v in filas:
            if rr == r:
                indice = v / medianas[(r, tipo)] if medianas[(r, tipo)] else 0
                grupos['franjas'].setdefault(franja, []).append(indice)
                grupos['dias'].setdefault(dia, []).append(indice)
        salida[r] = {k: {valor: {'n': len(l), 'indice': round(statistics.mean(l), 2)} for valor, l in g.items()}
                     for k, g in grupos.items()}
        orden = sorted(salida[r]['franjas'].items(), key=lambda kv: -kv[1]['indice'])
        completas = all(salida[r]['franjas'].get(f, {}).get('n', 0) >= minimo_f for f in franjas_de(r, config))
        if completas and len(orden) > 1 and orden[0][1]['indice'] >= 1.2 * max(orden[1][1]['indice'], 0.01):
            prueba.setdefault('ganadoras', {})[r] = orden[0][0]
            config['prueba_horas'] = prueba
            guardar('config.json', config)
        salida[r]['ganadora'] = (prueba.get('ganadoras') or {}).get(r)
    return salida


def toca_publicar(plan, hoy, config):
    """Un video cada dias_entre_videos días (fecha de México)."""
    fechas = [a_utc(v['publica_utc']).astimezone(CDMX).date() for v in plan['videos']
              if v['estado'] in ('programado', 'publicado') and v.get('publica_utc')]
    if not fechas:
        return True, 'todavía no hay videos programados'
    ultima = max(fechas)
    faltan = config.get('dias_entre_videos', 2) - (hoy - ultima).days
    if faltan > 0:
        return False, f"el último sale el {ultima.isoformat()}; toca publicar en {faltan} día(s)"
    return True, f"el último salió el {ultima.isoformat()}"


def segundos(video, config):
    """Segundos del video: los del plan o los que pide su guion (2.33 palabras por segundo).
    Prorrateo: las reglas cortas salen de 10-12 s y las historias que lo valen, más largas (máximo 25)."""
    if video.get('duracion'):
        return video['duracion']
    s = round(len(video['guion'].split()) / config.get('palabras_por_segundo', 2.65) + 1.0)  # +1 s de aire; si sobra más, Wan inventa
    s += 1 if video.get('formato') == 'entrevista' else 0  # la entrevista lleva pausas
    return max(config.get('segundos_minimos', 10), min(config.get('segundos_maximos', 25), s))


def creditos(video, config):
    return segundos(video, config) * config.get('creditos_por_segundo', 40) + config.get('creditos_foto', 30)


def decidir(plan, ranking, hoy, config):
    toca, motivo = toca_publicar(plan, hoy, config)
    carruseles = cargar('carruseles.json', {'carruseles': []})['carruseles']
    ahora = datetime.datetime.now(datetime.timezone.utc)
    elegidas, cuando, conteo, estado = horarios(plan, carruseles, config, hoy, ahora)
    listo = next((v for v in plan['videos'] if v['estado'] == 'listo_para_publicar'), None)
    base = {'toca_publicar': toca, 'motivo': motivo, 'hora_siguiente': elegidas['ig'], 'horarios': elegidas,
            'cuando': cuando, 'prueba_horas': estado, 'conteo_horas': conteo,
            'publicar_hoy': listo['id'] if toca and listo else None}
    # Videos de temporada ("ventana"): solo si salen dentro de sus fechas, y van primero porque caducan.
    sale = (hoy + datetime.timedelta(days=config.get('dias_entre_videos', 2))).isoformat()
    en_fecha = lambda v: not v.get('ventana') or v['ventana']['desde'] <= sale <= v['ventana']['hasta']
    pendientes = [v for v in plan['videos'] if v['estado'] == 'pendiente' and en_fecha(v)]
    temporada = [v for v in pendientes if v.get('ventana')]
    if temporada:
        v = temporada[0]
        return {**base, 'video_id': v['id'], 'modo': 'temporada', 'esperado': None, 'cambios_sugeridos': [],
                'por_que': f'Temporada: el video {v["id"]} solo sirve hasta el {v["ventana"]["hasta"]}.'}
    # Prioridad a mano (Rodrigo, 9-nov-2026: "hagamos lo mejor"): con pocos créditos, primero estos ids si siguen pendientes.
    prioridad = [v for i in config.get('prioridad_videos', []) for v in pendientes if v['id'] == i]
    if prioridad:
        v = prioridad[0]
        return {**base, 'video_id': v['id'], 'modo': 'prioridad', 'esperado': None, 'cambios_sugeridos': [],
                'por_que': f'Prioridad: el video {v["id"]} va primero (config.json → prioridad_videos).'}
    if not pendientes:
        return {**base, 'video_id': None, 'modo': 'sin guiones', 'esperado': None, 'cambios_sugeridos': [],
                'por_que': 'No hay guiones pendientes: escribir 10 nuevos (paso 1c).'}
    publicados = [v for v in plan['videos'] if v['estado'] in ('programado', 'publicado', 'listo_para_publicar')]
    # Series ("Así empezaron #N"): un capítulo cada 2 videos para que el "sígueme para la siguiente"
    # se cumpla pronto, siempre el número que sigue y sin dos capítulos seguidos.
    serie = sorted((v for v in pendientes if v.get('serie')), key=lambda v: v['serie']['numero'])
    if serie and not (publicados and publicados[-1].get('serie')):
        v = serie[0]
        return {**base, 'video_id': v['id'], 'modo': 'serie', 'esperado': None, 'cambios_sugeridos': [],
                'por_que': f'Serie: toca el capítulo {v["serie"]["numero"]} (uno cada 2 videos).'}
    pendientes = [v for v in pendientes if not v.get('serie')] or pendientes
    valores = {a: {f['valor']: f for f in filas} for a, filas in ranking.items()}
    ultimo_pilar = publicados[-1]['pilar'] if publicados else None
    explorar = len(publicados) % 10 in (2, 5, 8)  # 3 de cada 10 videos exploran
    candidatos = []
    for orden, v in enumerate(pendientes):
        rasgos = {k: x for k, x in adn(v).items() if k not in ('dia', 'hora')}
        conocidos = [valores.get(a, {}).get(x) for a, x in rasgos.items()]
        firmes = [c['indice'] for a, c in zip(rasgos, conocidos) if c and c['n'] >= minimo(a, config)]
        esperado = statistics.mean(firmes) if firmes else 1.0
        if v['pilar'] == ultimo_pilar:
            esperado *= 0.9  # no repetir tema seguido sin razón
        nuevos = sum(1 for a, c in zip(rasgos, conocidos) if not c or c['n'] < minimo(a, config))
        candidatos.append((v, round(esperado, 2), nuevos, orden))
    if explorar:
        v, esperado, nuevos, _ = max(candidatos, key=lambda c: (c[2], -c[3]))
        por_que = f'Toca explorar: el video {v["id"]} prueba {nuevos} características con pocos datos.'
    else:
        v, esperado, nuevos, _ = max(candidatos, key=lambda c: (c[1], -c[3]))
        por_que = f'Toca aprovechar: el video {v["id"]} tiene el mejor índice esperado ({esperado}).'
    cambios = []
    rasgos = adn(v)
    for atributo in ('tipo_fondo', 'locacion', 'estilo_vestuario', 'tipo_gancho', 'titulo_emoji', 'titulo_largo'):
        actual = valores.get(atributo, {}).get(rasgos.get(atributo))
        mejor = next((f for f in ranking.get(atributo, []) if f['estado'] == 'gana'), None)
        if actual and actual['estado'] == 'pierde' and mejor:
            cambios.append({'atributo': atributo, 'de': rasgos[atributo], 'a': mejor['valor'],
                            'por_que': f'{rasgos[atributo]} promedia {actual["indice"]} y {mejor["valor"]} {mejor["indice"]}'})
    return {**base, 'video_id': v['id'], 'modo': 'explorar' if explorar else 'aprovechar', 'esperado': esperado,
            'por_que': por_que, 'cambios_sugeridos': cambios}


def en_ventana(c, dia):
    v = c.get('ventana')
    return not v or v['desde'] <= dia.isoformat() <= v['hasta']


def vistas_tiktok(cid, historial):
    """Últimas vistas medidas en TikTok de un carrusel (None si todavía no hay)."""
    fotos = [f for f in historial if f['video_id'] == cid and (f.get('tt') or {}).get('v') is not None]
    return max(fotos, key=lambda f: f['fecha_utc'])['tt']['v'] if fotos else None


def franja_extra(r, fecha, ocupadas, conteo, config, ahora, separacion=3, filtro=None):
    """Segunda publicación del día en la red r: la franja menos probada (y, entre ellas, la más fuerte para ese día,
    orden_por_dia) a `separacion` horas o más de lo que ya sale. Suma a la prueba de horarios como las demás."""
    prueba = config.get('prueba_horas') or {}
    a_hora = lambda f: datetime.datetime.combine(fecha, datetime.time.fromisoformat(f), tzinfo=CDMX)
    orden = ((prueba.get('orden_por_dia') or {}).get(r) or {}).get(str(fecha.weekday())) or []
    libres = [f for f in franjas_de(r, config) if (not filtro or filtro(f)) and a_hora(f) > ahora + datetime.timedelta(minutes=20)
              and all(abs(a_hora(f) - t) >= datetime.timedelta(hours=separacion) for t in ocupadas)]
    if not libres:
        return None
    f = min(libres, key=lambda x: (conteo[r].get(x, 0), orden.index(x) if x in orden else len(orden)))
    return a_hora(f).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def decidir_carruseles(plan, carruseles, historial, config, hoy, ahora, d):
    """Qué carruseles salen hoy en cada red. Rodrigo, 9-nov-2026: "TikTok 3 al día, YouTube 2, Instagram 2 (uno en la
    mañanita, otro en la tarde). El chiste es subir lo mismo en todas las redes, no perder ningún reel ni carrusel."
    - config.json → publicaciones_por_dia por red; el video de Victoria del día cuenta como una.
    - TikTok: carruseles en fotos (temporada primero), a 3 h o más entre sí y del video.
    - Instagram: el Reel del carrusel (desde el 7-nov sin las fotos: Muse, "Reels para llegar fuera"), uno antes de
      las 13:00 y otro después. YouTube: su short.
    - Todo carrusel acaba en las tres redes. Orden para Instagram y YouTube: hits marcados por la revisión vespertina
      (config → prioridad_reel_ig), luego los que ya llevan 7 días o más en TikTok (para que no se queden atrás),
      luego los probados 20 h o más en TikTok (temporada y vistas), luego los de TikTok de hoy."""
    por_red = lambda c: c.get('publica_utc_por_red') or {}
    falta = lambda c, r: (c['estado'] in ('listo', 'programado', 'publicado') and r not in por_red(c) and en_ventana(c, hoy)
                          and not c.get('fuera_de_tema'))  # 9-nov-2026: un solo tema
    hoy_cdmx = lambda t: a_utc(t).astimezone(CDMX)
    cupos = {'tt': 1, 'ig': 1, 'yt': 1, **(config.get('publicaciones_por_dia') or {})}
    salida = {'tiktok': None, 'instagram': None, 'youtube': None, 'tiktoks': [], 'instagrams': [], 'youtubes': [], 'notas': []}

    def ya_hoy(r):
        """Horas (México) de lo que ya sale hoy en la red r: videos, carruseles, Reels y el video que se programa hoy."""
        horas = [h[r] for _, h in publicaciones(plan, carruseles) if r in h and h[r].date() == hoy]
        if r == 'ig':
            horas += [hoy_cdmx(c['reel_ig']['publica_utc']) for c in carruseles
                      if (c.get('reel_ig') or {}).get('publica_utc') and hoy_cdmx(c['reel_ig']['publica_utc']).date() == hoy]
        if d.get('publicar_hoy') and (d.get('cuando') or {}).get(r):
            t = hoy_cdmx(d['cuando'][r])
            if all(abs(t - x) > datetime.timedelta(minutes=1) for x in horas):
                horas.append(t)
        return horas

    # TikTok: los primeros que no han salido ahí (temporada primero).
    ocupadas = ya_hoy('tt')
    # config → prioridad_carruseles va primero (9-nov-2026: la serie de parejas llevaba días atorada detrás de la temporada)
    # (hasta config → prioridad_por_dia al día; los demás turnos siguen con la temporada)
    prioridad = config.get('prioridad_carruseles', [])
    base = sorted((c for c in carruseles if falta(c, 'tt')), key=lambda c: 0 if c.get('ventana') else 1)
    primero = sorted((c for c in base if c['id'] in prioridad), key=lambda c: prioridad.index(c['id']))
    primero = primero[:max(0, config.get('prioridad_por_dia', len(primero)) - sum(1 for c in carruseles if c['id'] in prioridad
                                                                                 and (por_red(c).get('tt') or '')[:10] == hoy.isoformat()))]
    pendientes_tt = primero + [c for c in base if c not in primero]
    if len(ocupadas) >= cupos['tt']:
        salida['notas'].append(f'TikTok ya tiene sus {len(ocupadas)} publicaciones de hoy.')
    while pendientes_tt and len(ocupadas) < cupos['tt']:
        cuando = franja_extra('tt', hoy, ocupadas, d['conteo_horas'], config, ahora) if ocupadas else d['cuando']['tt']
        if not cuando:
            salida['notas'].append('TikTok: ya no queda hora libre hoy a 3 h de lo demás; sigue mañana.')
            break
        salida['tiktoks'].append({'id': pendientes_tt[0]['id'], 'cuando': cuando})
        ocupadas.append(hoy_cdmx(cuando))
        pendientes_tt = pendientes_tt[1:]
    if not pendientes_tt and len(ocupadas) < cupos['tt']:
        salida['notas'].append('TikTok: no queda ningún carrusel "listo" que no haya salido ahí: escribir 5 nuevos.')
    salida['tiktok'] = salida['tiktoks'][0] if salida['tiktoks'] else None
    salida['quedan_tiktok'] = len(pendientes_tt)
    tt_de_hoy = [t['id'] for t in salida['tiktoks']]

    def cola(r, tiene):
        """Carruseles que faltan en la red r, en el orden del docstring."""
        hits = config.get('prioridad_reel_ig', [])
        lista = []
        for c in carruseles:
            if not falta(c, r) or tiene(c):
                continue
            t_tt = hoy_cdmx(por_red(c)['tt']) if 'tt' in por_red(c) else None
            if not t_tt and c['id'] not in tt_de_hoy:
                continue  # primero sale en TikTok, que es donde se prueba
            if c['id'] in hits:
                grupo = 0
            elif t_tt and t_tt <= ahora - datetime.timedelta(days=7):
                grupo = 1
            elif t_tt and t_tt <= ahora - datetime.timedelta(hours=20):
                grupo = 2
            else:
                grupo = 3
            orden = hits.index(c['id']) if grupo == 0 else 0
            lista.append(((grupo, orden, 0 if c.get('ventana') else 1, -(vistas_tiktok(c['id'], historial) or -1),
                           t_tt or ahora + datetime.timedelta(days=1)), c))
        return [c for _, c in sorted(lista, key=lambda x: x[0])]

    def por_que(c):
        v = vistas_tiktok(c['id'], historial)
        if c['id'] in config.get('prioridad_reel_ig', []):
            return f'hit en TikTok ({v} vistas): va primero (config → prioridad_reel_ig)'
        if 'tt' not in por_red(c):
            return 'sale hoy en TikTok y todavía no hay probados que falten'
        t_tt = hoy_cdmx(por_red(c)['tt'])
        if t_tt > ahora:
            return f'sale en TikTok hoy a las {t_tt:%H:%M}; no quedan probados que falten aquí'
        return f'{v if v is not None else "sin medir"} vistas en TikTok; lleva {(ahora - t_tt).days} día(s) esperando'

    # Instagram: un Reel en la mañana (antes de las 13:00) y otro en la tarde; el video del día ocupa su turno.
    tiene_ig = lambda c: (c.get('reel_ig') or {}).get('publica_utc')
    ocupadas = ya_hoy('ig')
    turnos = [('mañana', lambda f: f < '13:00'), ('tarde', lambda f: f >= '13:00')]
    libres = [(n, f) for n, f in turnos if not any(f(t.strftime('%H:%M')) for t in ocupadas)]
    candidatos = cola('ig', tiene_ig)
    if len(ocupadas) >= cupos['ig']:
        salida['notas'].append(f'Instagram ya tiene sus {len(ocupadas)} publicaciones de hoy.')
    while candidatos and len(ocupadas) < cupos['ig']:
        _, filtro = libres.pop(0) if libres else (None, None)
        cuando = franja_extra('ig', hoy, ocupadas, d['conteo_horas'], config, ahora, filtro=filtro) \
            or franja_extra('ig', hoy, ocupadas, d['conteo_horas'], config, ahora)
        if not cuando:
            salida['notas'].append('Instagram: ya no queda hora libre hoy a 3 h de lo demás.')
            break
        c = candidatos.pop(0)
        nombre = 'mañana' if hoy_cdmx(cuando).strftime('%H:%M') < '13:00' else 'tarde'
        salida['instagrams'].append({'id': c['id'], 'cuando_ig': cuando, 'turno': nombre, 'por_que': por_que(c)})
        ocupadas.append(hoy_cdmx(cuando))
    salida['quedan_instagram'] = len(candidatos)

    # YouTube: el short de los mismos de Instagram si les falta, luego la cola de YouTube.
    tiene_yt = lambda c: c.get('youtube')
    ocupadas = ya_hoy('yt')
    ids_ig = [x['id'] for x in salida['instagrams']]
    candidatos = sorted(cola('yt', tiene_yt), key=lambda c: 0 if c['id'] in ids_ig else 1)
    if len(ocupadas) >= cupos['yt']:
        salida['notas'].append(f'YouTube ya tiene sus {len(ocupadas)} publicaciones de hoy.')
    while candidatos and len(ocupadas) < cupos['yt']:
        cuando = franja_extra('yt', hoy, ocupadas, d['conteo_horas'], config, ahora)
        if not cuando:
            salida['notas'].append('YouTube: ya no queda hora libre hoy a 3 h de lo demás.')
            break
        c = candidatos.pop(0)
        salida['youtubes'].append({'id': c['id'], 'cuando_yt': cuando, 'por_que': por_que(c)})
        ocupadas.append(hoy_cdmx(cuando))
    salida['quedan_youtube'] = len(candidatos)
    salida['instagram'] = salida['instagrams'][0] if salida['instagrams'] else None
    salida['youtube'] = salida['youtubes'][0] if salida['youtubes'] else None
    for r, nombre in (('ig', 'Instagram'), ('yt', 'YouTube')):
        atras = salida[f"quedan_{'instagram' if r == 'ig' else 'youtube'}"]
        if atras > 3 * cupos[r]:
            salida['notas'].append(f'{nombre} lleva {atras} carruseles atrás de TikTok: subir {nombre} a '
                                   f'{cupos[r] + 1} al día o bajar TikTok (config → publicaciones_por_dia).')

    comandos = []
    for t in salida['tiktoks']:
        comandos.append(f"python scripts/publer_carrusel.py {t['id']} \"tt={t['cuando']}\"")
    hechos = set()
    for x in salida['instagrams'] + salida['youtubes']:
        if x['id'] not in hechos:
            comandos.append(f"python scripts/carrusel_video.py short {x['id']}")
            hechos.add(x['id'])
    biblioteca = hoy.weekday() in (config.get('sonido_biblioteca_ig') or {}).get('dias', [])
    for i, ig in enumerate(salida['instagrams']):
        # Martes y viernes el primer Reel lo sube Rodrigo con un sonido de la biblioteca (config → sonido_biblioteca_ig)
        manual = ' --manual' if biblioteca and i == 0 else ''
        ig['manual'] = bool(manual)
        comandos.append(f"python scripts/publer_carrusel.py {ig['id']} --reel {ig['cuando_ig']}{manual}")
    for yt in salida['youtubes']:
        comandos.append(f"youtube.py subir carruseles/{yt['id']}/short.mp4 ... {yt['cuando_yt']} (CARRUSELES.md)")
        if config.get('facebook_victoria') and yt['id'] not in ids_ig:
            # 9-nov-2026 (Rodrigo: "sube mucho a Facebook"): los shorts de YouTube también van a la página de Facebook;
            # los de Instagram ya van solos con su Reel.
            comandos.append(f"python scripts/publer_carrusel.py {yt['id']} --reel {yt['cuando_yt']} --solo-facebook")
    salida['comandos'] = comandos
    return salida


def reglas_vigentes(ranking, config):
    """Reglas con cifras sacadas de los datos propios, para quien escribe guiones y títulos (regla 32)."""
    reglas = []
    for atributo, nombre in NOMBRES.items():
        filas = [f for f in ranking.get(atributo, []) if f['n'] >= minimo(atributo, config)]
        if len(filas) < 2:
            continue
        mejor, peor = filas[0], filas[-1]
        if mejor['indice'] >= 1.2 * max(peor['indice'], 0.01):
            reglas.append(f'{nombre}: "{mejor["valor"]}" rinde {mejor["indice"]}x ({mejor["n"]} videos) contra '
                          f'{peor["indice"]}x de "{peor["valor"]}" ({peor["n"]} videos). Usar más "{mejor["valor"]}".')
    return reglas


def alertas(plan, ranking, notas, ejecuciones, config, hoy):
    lista = []
    vence = config.get('instagram_token_vence')  # el permiso de Instagram del centro dura 60 días
    if vence and (datetime.date.fromisoformat(vence) - hoy).days <= 7:
        lista.append(f'El permiso de Instagram del centro vence el {vence}: genera uno nuevo en Meta (Instagram > '
                     'API setup > Generate token) y cámbialo en Vercel (INSTAGRAM_TOKEN). Luego actualiza la fecha en config.json.')
    verificacion = cargar('verificacion.json', {})
    lista += verificacion.get('problemas', [])  # solo lo comprobado en cada red (regla 34)
    medidos = len(notas)
    if medidos < 6:
        lista.append(f'{medidos} videos calificados. Con 6 o más ya se ven tendencias; antes de eso todo está "en prueba".')
    for atributo, nombre in NOMBRES.items():
        for f in ranking.get(atributo, []):
            if f['estado'] in ('gana', 'pierde'):
                lista.append(f'{nombre} "{f["valor"]}" {f["estado"]}: índice {f["indice"]} en {f["n"]} videos.')
    pendientes = sum(1 for v in plan['videos'] if v['estado'] == 'pendiente')
    if pendientes < 5:
        lista.append(f'Quedan {pendientes} guiones: hay que escribir 10 nuevos (paso 1c).')
    p = presupuesto(plan, ejecuciones, config, hoy)
    if p and p['sobran'] < 0:
        lista.append(f"Créditos: hasta el {p['renovacion']} se necesitan {p['necesarios']} para {p['videos']} videos y hay "
                     f"{p['restantes']} (dejando {p['reserva']}): faltan {-p['sobran']}. Los días que no alcance, sale carrusel "
                     "(gratis) en lugar de video.")
    pps = config.get('palabras_por_segundo', 2.33)
    for v in plan['videos']:
        if v['estado'] == 'pendiente' and len(v['guion'].split()) > segundos(v, config) * pps + 1:
            lista.append(f'El guion del video {v["id"]} no cabe en {segundos(v, config)} s '
                         f'({len(v["guion"].split())} palabras; máximo {int(segundos(v, config) * pps)}).')
    orden = sorted(ejecuciones, key=lambda e: e['fecha_utc'])
    if orden:
        generados = [e for e in orden if e['tipo'] == 'generar' and e.get('creditos_usados')]
        costo = statistics.mean(e['creditos_usados'] for e in generados) if generados else 540
        ultimo = next((e['creditos_restantes'] for e in reversed(orden) if e.get('creditos_restantes') is not None), 0)
        alcanzan = int(ultimo // costo)
        if alcanzan < 7:
            dias = alcanzan * config.get('dias_entre_videos', 2)
            lista.append(f'Créditos para {alcanzan} videos (unos {dias} días al ritmo actual). Recargar OpenArt.')
    prueba = config.get('prueba_voz_intima')
    if prueba:  # Rodrigo, 7-nov-2026: voz cálida e íntima; se decide con datos
        intimos = sorted((v for v in plan['videos'] if v.get('voz') == 'intima' and v['estado'] == 'publicado'
                          and v.get('publica_utc')), key=lambda v: v['publica_utc'])
        if len(intimos) >= prueba.get('videos', 3):
            ultimo = datetime.date.fromisoformat(intimos[prueba.get('videos', 3) - 1]['publica_utc'][:10])
            if (hoy - ultimo).days >= 3:
                lista.append('Prueba de voz íntima lista para evaluar: compara ' + ', '.join(v['id'] for v in intimos)
                             + ' contra ' + ', '.join(prueba['comparar_con']) + ' (porcentaje visto, guardados, '
                             'comentarios, visitas al perfil) y decide con Rodrigo si se queda.')
        else:
            lista.append(f"Prueba de voz íntima: {len(intimos)} de {prueba.get('videos', 3)} videos publicados.")
    largo = config.get('largo_tematico')  # 9-nov-2026: video largo por tema para búsquedas de YouTube
    if largo and not largo.get('hecho') and hoy.isoformat() >= largo['desde']:
        listos = [i for i in largo['videos'] if any(v['id'] == i and v['estado'] == 'publicado' for v in plan['videos'])]
        lista.append(f"Video largo \"{largo['titulo']}\": {len(listos)} de {len(largo['videos'])} videos ya publicados "
                     f"({', '.join(listos) or 'ninguno'}). Armarlo con compilar.py probar {' '.join(listos)} cuando pase de 3 min "
                     "y subirlo como largo (PIPELINE 1d); luego poner hecho: true en config.json → largo_tematico.")
    fallas = [e for e in orden[-5:] if e['resultado'] == 'fallido']
    if len(fallas) >= 2:
        lista.append(f'{len(fallas)} de las últimas 5 ejecuciones fallaron: revisar antes de gastar más créditos.')
    if hoy.weekday() == 0 and any(v['estado'] == 'publicado' for v in plan['videos']):
        lista.append('Es lunes: pedir a Rodrigo capturas de las estadísticas de Instagram y TikTok de la semana '
                     '(sus números por API no son fiables, regla 33).')
    return lista


def presupuesto(plan, ejecuciones, config, hoy):
    """Créditos hasta la renovación de OpenArt: se gastan hasta dejar reserva_final_creditos (Rodrigo, 31-oct: "que
    quedemos con 100 al final"). Videos que faltan = uno cada dias_entre_videos hasta renovacion_creditos."""
    if not ejecuciones or not config.get('renovacion_creditos'):
        return None
    con_dato = [e for e in ejecuciones if e.get('creditos_restantes') is not None]  # 9-nov: una ejecución sin dato no rompe la auditoría
    if not con_dato:
        return None
    restantes = sorted(con_dato, key=lambda e: e['fecha_utc'])[-1]['creditos_restantes']
    renovacion = datetime.date.fromisoformat(config['renovacion_creditos'])
    while renovacion <= hoy:  # el ciclo se repite cada mes
        renovacion = (renovacion.replace(day=1) + datetime.timedelta(days=32)).replace(day=min(renovacion.day, 28))
    hechos = sum(1 for v in plan['videos'] if v['estado'] == 'listo_para_publicar')  # ya generados: no gastan
    videos = max(0, -(-(renovacion - hoy).days // config.get('dias_entre_videos', 2)) - hechos)
    pendientes = [v for v in plan['videos'] if v['estado'] == 'pendiente'][:videos]
    necesarios = sum(creditos(v, config) for v in pendientes)
    reserva = config.get('reserva_final_creditos', 100)
    return {'restantes': restantes, 'renovacion': renovacion.isoformat(), 'videos': len(pendientes),
            'necesarios': necesarios, 'reserva': reserva, 'sobran': restantes - reserva - necesarios}


def ganchos_carrusel(carruseles, historial):
    """Prueba de ganchos (Rodrigo, 8-nov-2026, docs/PERSONAJE.md): vistas de TikTok de cada carrusel cerca de las
    48 h (entre 24 y 96 h), agrupadas por portada.gancho_tipo (postura, si, dato). Gana un tipo con 3 o más
    carruseles que rinda 20% más que el segundo; ese tipo se usa en los guiones de video (que cuestan créditos)."""
    tipos = {}
    for c in carruseles:
        tomas = [f for f in historial if f['video_id'] == c['id'] and (f.get('tt') or {}).get('v') is not None
                 and 24 <= (f['tt'].get('h') or f.get('horas') or 0) <= 96]
        if not tomas:
            continue
        cerca = min(tomas, key=lambda f: abs((f['tt'].get('h') or f.get('horas')) - 48))
        tipos.setdefault((c.get('portada') or {}).get('gancho_tipo', 'dato'), []).append(cerca['tt']['v'])
    filas = sorted(({'tipo': t, 'n': len(v), 'vistas_48h': round(statistics.mean(v))} for t, v in tipos.items()),
                   key=lambda f: -f['vistas_48h'])
    con_datos = [f for f in filas if f['n'] >= 3]
    gana = con_datos[0]['tipo'] if len(con_datos) >= 2 and con_datos[0]['vistas_48h'] >= 1.2 * con_datos[1]['vistas_48h'] else None
    return {'tipos': filas, 'gana': gana}


def auditar():
    plan = cargar('plan.json', {'videos': []})
    historial = cargar('metricas.json', [])
    ejecuciones = cargar('ejecuciones.json', [])
    config = cargar('config.json', {})
    hoy = datetime.datetime.now(CDMX).date()
    notas = calificar(plan, historial)
    base, ranking = comparar(plan, notas, config)
    resultado = {
        'fecha_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'videos_calificados': len(notas),
        'base_vistas_36h': base,
        'notas': {vid: n for vid, n in sorted(notas.items())},
        'ranking': ranking,
        'decision': decidir(plan, ranking, hoy, config),
        'horarios_por_red': horas_por_red(plan, cargar('carruseles.json', {'carruseles': []})['carruseles'], historial, config),
        'reglas_vigentes': reglas_vigentes(ranking, config),
        'alertas': alertas(plan, ranking, notas, ejecuciones, config, hoy),
    }
    d = resultado['decision']
    d['carruseles'] = decidir_carruseles(plan, cargar('carruseles.json', {'carruseles': []})['carruseles'], historial,
                                         config, hoy, datetime.datetime.now(datetime.timezone.utc), d)
    al_dia = (config.get('publicaciones_por_dia') or {}).get('tt', 1)
    if d['carruseles']['quedan_tiktok'] < 5 * al_dia:  # 5 días de cola (9-nov-2026: 3 al día en TikTok)
        resultado['alertas'].append(f"Quedan {d['carruseles']['quedan_tiktok']} carruseles para TikTok (salen hasta {al_dia} "
                                    f'al día): escribir {3 * al_dia} nuevos con datos comprobados (CARRUSELES.md) y su segunda revisión.')
    siguiente = next((v for v in plan['videos'] if v['id'] == d.get('video_id')), None)
    if siguiente:
        d['segundos'], d['creditos'] = segundos(siguiente, config), creditos(siguiente, config)
    resultado['ganchos_carrusel'] = ganchos_carrusel(cargar('carruseles.json', {'carruseles': []})['carruseles'], historial)
    guardar('auditoria.json', resultado)
    print(f"Auditoría: {len(notas)} videos calificados, base {base} vistas a 36 h.")
    for atributo, filas in ranking.items():
        print(f'  {atributo}: ' + ', '.join(f"{f['valor']} {f['indice']} ({f['n']}, {f['estado']})" for f in filas))
    print(f"Hoy {'SÍ' if d['toca_publicar'] else 'NO'} toca publicar video ({d['motivo']}).")
    print('Horas de hoy por red: ' + ', '.join(f"{r} {h}" for r, h in d['horarios'].items())
          + ' · publer: ' + ','.join(f"{r}={d['cuando'][r]}" for r in ('ig', 'tt')) + f" · youtube: {d['cuando']['yt']}")
    print('Prueba de horarios:', d['prueba_horas'])
    for r, datos in resultado['horarios_por_red'].items():
        if datos['franjas']:
            print(f"  {r}: " + ', '.join(f"{f} {x['indice']} ({x['n']})" for f, x in sorted(datos['franjas'].items()))
                  + (f" · gana {datos['ganadora']}" if datos['ganadora'] else ''))
    if d.get('publicar_hoy'):
        print(f"Publicar hoy el video listo {d['publicar_hoy']}.")
    k = d['carruseles']
    if k['tiktok']:
        print('Carruseles de TikTok hoy: ' + ', '.join(f"{t['id']} a las {a_utc(t['cuando']).astimezone(CDMX):%H:%M}" for t in k['tiktoks']) + '.')
    for x in k.get('instagrams', []):
        print(f"Reel de Instagram ({x['turno']}): {x['id']} a las {a_utc(x['cuando_ig']).astimezone(CDMX):%H:%M} ({x['por_que']})"
              + (" · LO SUBE RODRIGO con un sonido de la biblioteca" if x.get('manual') else '') + '.')
    for x in k.get('youtubes', []):
        print(f"Short de YouTube: {x['id']} a las {a_utc(x['cuando_yt']).astimezone(CDMX):%H:%M} ({x['por_que']}).")
    print(f"En cola: TikTok {k.get('quedan_tiktok')}, Instagram {k.get('quedan_instagram')}, YouTube {k.get('quedan_youtube')} carruseles.")
    for n in k['notas']:
        print('Carruseles:', n)
    for c in k['comandos']:
        print('  ', c)
    g = resultado['ganchos_carrusel']
    print('Ganchos de carrusel en TikTok (vistas a ~48 h): ' + (', '.join(f"{f['tipo']} {f['vistas_48h']} ({f['n']})" for f in g['tipos']) or 'sin datos')
          + (f" · gana {g['gana']}: úsalo en los guiones de video" if g['gana'] else ' · en prueba (3+ por tipo y 20% de ventaja)'))
    print('Siguiente a generar:', d['por_que'], f"({d['segundos']} s, {d['creditos']} créditos)" if d.get('segundos') else '')
    for c in d.get('cambios_sugeridos', []):
        print(f"  Cambiar {c['atributo']}: {c['de']} → {c['a']} ({c['por_que']})")
    for r in resultado['reglas_vigentes']:
        print('Regla:', r)
    for a in resultado['alertas']:
        print('Alerta:', a)


if __name__ == '__main__':
    {'medir': medir, 'auditar': auditar}.get(sys.argv[1] if len(sys.argv) > 1 else '', lambda: sys.exit(__doc__))()
