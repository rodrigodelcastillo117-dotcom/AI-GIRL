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
    por_linea = {primera_linea(v.get('texto_post')): v['id'] for v in videos}
    por_minuto = {v['publica_utc'][:16]: v['id'] for v in videos if v.get('publica_utc')}
    hoy = datetime.date.today()
    datos = {}
    for pagina in range(20):
        r = publer._pedir('GET', f'/analytics/post_insights?from={(hoy - datetime.timedelta(days=60)).isoformat()}'
                                 f'&to={hoy.isoformat()}&page={pagina}', ws)
        lote = r.get('posts') or []
        for p in lote:
            red = REDES.get(cuentas.get(p.get('account_id')))
            if not red:
                continue
            minuto = a_utc(p['scheduled_at']).strftime('%Y-%m-%dT%H:%M') if p.get('scheduled_at') else ''
            video = por_linea.get(primera_linea(p.get('text'))) or por_minuto.get(minuto)
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
    propias |= {primera_linea(c.get('texto_post')) for c in cargar('carruseles.json', {'carruseles': []})['carruseles']}
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
    for c in cargar('carruseles.json', {'carruseles': []})['carruseles']:  # los carruseles también se miden
        if c.get('publica_utc') and a_utc(c['publica_utc']) <= ahora and (ahora - a_utc(c['publica_utc'])).days <= DIAS_DE_MEDICION:
            videos.append({'id': c['id'], 'texto_post': c['texto_post'], 'publica_utc': c['publica_utc'],
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
            if r in conteo and t.strftime('%H:%M') in conteo[r]:
                conteo[r][t.strftime('%H:%M')] += 1
    a_hora = lambda f: datetime.datetime.combine(fecha, datetime.time.fromisoformat(f), tzinfo=CDMX)
    elegidas, cuando = {}, {}
    for i, r in enumerate(CORTAS):
        franjas = franjas_de(r, config)
        libres = [f for f in franjas if a_hora(f) > ahora + datetime.timedelta(minutes=20)] or franjas[-1:]
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
                filas.append((r, tipo, t.strftime('%H:%M'), DIAS_SEMANA[t.weekday()], f[r]['v']))
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
    s = round(len(video['guion'].split()) / config.get('palabras_por_segundo', 2.33) + 0.4)
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
    por_mes = 30 // config.get('dias_entre_videos', 2)
    siguientes = [v for v in plan['videos'] if v['estado'] == 'pendiente'][:por_mes]
    gasto = sum(creditos(v, config) for v in siguientes)
    tope = int(config.get('creditos_al_mes', 12000) * (1 - config.get('reserva_reintentos', 0.15)))
    if gasto > tope:
        lista.append(f'Los próximos {len(siguientes)} videos piden {gasto} créditos y el tope del mes es {tope} '
                     '(deja 15% para reintentos): acortar los guiones más largos.')
    pps = config.get('palabras_por_segundo', 2.33)
    for v in plan['videos']:
        if v['estado'] == 'pendiente' and len(v['guion'].split()) > segundos(v, config) * pps + 1:
            lista.append(f'El guion del video {v["id"]} no cabe en {segundos(v, config)} s '
                         f'({len(v["guion"].split())} palabras; máximo {int(segundos(v, config) * pps)}).')
    orden = sorted(ejecuciones, key=lambda e: e['fecha_utc'])
    if orden:
        generados = [e for e in orden if e['tipo'] == 'generar' and e.get('creditos_usados')]
        costo = statistics.mean(e['creditos_usados'] for e in generados) if generados else 540
        alcanzan = int(orden[-1]['creditos_restantes'] // costo)
        if alcanzan < 7:
            dias = alcanzan * config.get('dias_entre_videos', 2)
            lista.append(f'Créditos para {alcanzan} videos (unos {dias} días al ritmo actual). Recargar OpenArt.')
    fallas = [e for e in orden[-5:] if e['resultado'] == 'fallido']
    if len(fallas) >= 2:
        lista.append(f'{len(fallas)} de las últimas 5 ejecuciones fallaron: revisar antes de gastar más créditos.')
    if hoy.weekday() == 0 and any(v['estado'] == 'publicado' for v in plan['videos']):
        lista.append('Es lunes: pedir a Rodrigo capturas de las estadísticas de Instagram y TikTok de la semana '
                     '(sus números por API no son fiables, regla 33).')
    return lista


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
    siguiente = next((v for v in plan['videos'] if v['id'] == d.get('video_id')), None)
    if siguiente:
        d['segundos'], d['creditos'] = segundos(siguiente, config), creditos(siguiente, config)
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
    print('Siguiente a generar:', d['por_que'], f"({d['segundos']} s, {d['creditos']} créditos)" if d.get('segundos') else '')
    for c in d.get('cambios_sugeridos', []):
        print(f"  Cambiar {c['atributo']}: {c['de']} → {c['a']} ({c['por_que']})")
    for r in resultado['reglas_vigentes']:
        print('Regla:', r)
    for a in resultado['alertas']:
        print('Alerta:', a)


if __name__ == '__main__':
    {'medir': medir, 'auditar': auditar}.get(sys.argv[1] if len(sys.argv) > 1 else '', lambda: sys.exit(__doc__))()
