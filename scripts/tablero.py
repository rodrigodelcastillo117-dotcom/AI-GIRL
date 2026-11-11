"""Arma los datos del centro de mando de Victoria (centro/, en Vercel) en centro/datos/.

Uso: python tablero.py

- videos.json: un renglón por video del plan, con su cuadro (miniatura), su id de YouTube, la
  primera línea de su post y sus estadísticas por red (v_ vistas, l_ likes, c_ comentarios,
  s_ compartidos, g_ guardados; sufijos ig, tt, yt, fb). Las estadísticas son la última foto de
  contenido/metricas.json (scripts/aprender.py medir). El centro además las lee en
  vivo (centro/api/vivo.js); estas son la última foto por si la consulta en vivo falla.
- ejecuciones.json y aprendizajes.json: copias de contenido/.
- mejores_horas.json: rejilla día × hora de Publer (best_times); vacía (puntaje nulo) si no hay datos.
- auditoria.json: copia de contenido/auditoria.json (qué gana, qué pierde y la decisión del día).
- estado.json: un renglón con la salida del siguiente video (lo programado o lo que toca según la
  frecuencia y la prueba de horarios), la foto de perfil y datos fijos del canal.

Después se hace commit y push: Vercel vuelve a publicar el centro solo (docs/PIPELINE.md, paso 10).
"""
import base64
import datetime
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'centro', 'datos')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
DIAS_EN = {'Monday': 'lun', 'Tuesday': 'mar', 'Wednesday': 'mié', 'Thursday': 'jue', 'Friday': 'vie',
           'Saturday': 'sáb', 'Sunday': 'dom'}
REDES = {'instagram': 'ig', 'tiktok': 'tt', 'youtube': 'yt', 'facebook': 'fb'}
CAMPOS = {'v': 'video_views', 'l': 'likes', 'c': 'comments', 's': 'shares', 'g': 'saves'}
CDMX = datetime.timezone(datetime.timedelta(hours=-6))  # México no tiene horario de verano desde 2022


def comentarios_ig_reales():
    """{primera línea del pie: comentarios de OTRAS personas} en Instagram, leídos de Meta (mismo permiso que
    comentarios_ig.py; el token lo pone el proxy de la sesión). Publer cuenta también el primer comentario de Victoria
    y sus respuestas, y eso inflaba "Coment." en el centro (9-nov-2026). Sin acceso, {} y el centro usa Publer."""
    import urllib.parse, urllib.request
    url = ('https://graph.facebook.com/v21.0/17841478105608541/media?limit=100&fields='
           + urllib.parse.quote('caption,comments.limit(100){username,replies.limit(50){username}}'))
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            datos = json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001 - sin token (fuera de la sesión) o Meta caído: no rompe el tablero
        print(f'AVISO: no leí los comentarios de Instagram de Meta ({str(e)[:120]}); el centro usa los de Publer.')
        return {}
    salida = {}
    for m in datos.get('data', []):
        otros = 0
        for c in (m.get('comments') or {}).get('data', []):
            otros += c.get('username') != 'victoriatheceo'
            otros += sum(1 for x in (c.get('replies') or {}).get('data', []) if x.get('username') != 'victoriatheceo')
        salida[primera_linea(m.get('caption'))] = salida.get(primera_linea(m.get('caption')), 0) + otros
    return salida


def comentarios_yt_reales():
    """{id de YouTube: comentarios de OTRAS personas}. El conteo público de YouTube incluye las respuestas del canal
    (las que deja Claude cada día) y el comentario con enlace: eso inflaba "Coment." (9-nov-2026)."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from youtube import API, CONFIG as CFG_YT, _http, token
        acceso, canal = token(), CFG_YT['canal_youtube']
        salida, pagina = {}, ''
        for _ in range(10):
            _, r = _http('GET', f'{API}/commentThreads?part=snippet,replies&allThreadsRelatedToChannelId={canal}&maxResults=100'
                                + (f'&pageToken={pagina}' if pagina else ''), headers={'Authorization': f'Bearer {acceso}'})
            r = json.loads(r)
            for hilo in r.get('items', []):
                vid = hilo['snippet'].get('videoId')
                autores = [hilo['snippet']['topLevelComment']['snippet']] + [x['snippet'] for x in (hilo.get('replies') or {}).get('comments', [])]
                salida[vid] = salida.get(vid, 0) + sum(1 for a in autores if (a.get('authorChannelId') or {}).get('value') != canal)
            pagina = r.get('nextPageToken')
            if not pagina:
                break
        return salida
    except Exception as e:  # noqa: BLE001 - sin credenciales de YouTube: el centro usa el conteo público
        print(f'AVISO: no leí los comentarios de YouTube ({str(e)[:120]}); el centro usa el conteo público.')
        return {}


def guardar(nombre, filas):
    os.makedirs(SALIDA, exist_ok=True)
    json.dump(filas, open(os.path.join(SALIDA, nombre), 'w'), ensure_ascii=False, indent=1)
    print(f'{nombre}: {len(filas)} renglones')


def a_mexico(utc):
    if not utc:
        return None
    return datetime.datetime.fromisoformat(utc.replace('Z', '+00:00')).astimezone(CDMX)


def miniatura(ruta, segundo=3.0, ancho=180):
    """Un cuadro del video como JPEG en data URL, para no publicar los videos en el centro."""
    if not ruta or not os.path.exists(ruta):
        return ''
    jpg = subprocess.run(['ffmpeg', '-loglevel', 'error', '-ss', str(segundo), '-i', ruta, '-frames:v', '1',
                          '-vf', f'scale={ancho}:-2', '-q:v', '6', '-f', 'mjpeg', '-'],
                         capture_output=True).stdout
    return 'data:image/jpeg;base64,' + base64.b64encode(jpg).decode() if jpg else ''


def metricas_anteriores():
    try:
        previas = json.load(open(os.path.join(SALIDA, 'videos.json')))
    except (OSError, ValueError):
        return {}
    return {f['id']: {k: v for k, v in f.items() if k[:2] in ('v_', 'l_', 'c_', 's_', 'g_')} for f in previas}


def cargar_carruseles():
    try:
        return json.load(open(os.path.join(RAIZ, 'contenido', 'carruseles.json')))['carruseles']
    except (OSError, ValueError, KeyError):
        return []


def metricas_historial():
    """{video_id: {v_ig: n, ...}} con la foto más reciente de contenido/metricas.json (scripts/aprender.py medir)."""
    try:
        historial = json.load(open(os.path.join(RAIZ, 'contenido', 'metricas.json')))
    except (OSError, ValueError):
        return {}
    ultima = {}
    for foto in historial:
        ultima[foto['video_id']] = foto  # el historial está en orden de fecha
    por_video = {}
    for vid, foto in ultima.items():
        for red in ('yt', 'tt', 'ig', 'fb'):
            for corto in ('v', 'l', 'c', 's'):
                if red in foto or (red == 'ig' and 'igr' in foto):
                    por_video.setdefault(vid, {})[f'{corto}_{red}'] = de_red(foto, red, corto)
        if (foto.get('yt') or {}).get('ret') is not None:
            por_video.setdefault(vid, {})['r_yt'] = foto['yt']['ret']  # % promedio visto en YouTube
    return por_video


def mejores_horas_publer():
    """Rejilla día × hora de Publer (best_times), promediada entre las cuentas de Victoria."""
    import publer
    ws = publer.workspace_id()
    _, victoria = publer.cuentas_victoria(ws)
    hoy = datetime.date.today()
    puntajes = {}
    for c in victoria:
        r = publer._pedir('GET', f"/analytics/{c['id']}/best_times?from={(hoy - datetime.timedelta(days=30)).isoformat()}&to={hoy.isoformat()}", ws)
        for dia, horas in (r or {}).items():
            for hora, puntaje in enumerate(horas or []):
                clave = (DIAS_EN.get(dia, dia), hora)
                puntajes.setdefault(clave, []).append(puntaje or 0)
    return puntajes


def primera_linea(texto):
    lineas = (texto or '').strip().splitlines()
    return ' '.join(lineas[0].split()).lower() if lineas else ''


def youtube_id(enlace):
    return (enlace or '').rstrip('/').split('/')[-1].split('=')[-1] if enlace else ''


def workspace_publer():
    if not os.environ.get('PUBLER_API_KEY'):
        return ''
    try:
        import publer
        return publer.workspace_id()
    except SystemExit:
        return ''


NOMBRES_RED = {'ig': 'Instagram', 'tt': 'TikTok', 'yt': 'YouTube', 'fb': 'Facebook'}
INICIO_FB = '2026-11-09'  # desde aquí lo que sale en Instagram sale también en Facebook, a la misma hora


def de_red(foto, red, corto='v'):
    """Número de una red en una medición. En el centro, Instagram de un carrusel suma su Reel ('igr', que
    aprender.py mide aparte para que no cuente en la prueba de horarios)."""
    total = (foto.get(red) or {}).get(corto, 0) or 0
    return total + ((foto.get('igr') or {}).get(corto, 0) or 0 if red == 'ig' else 0)


def horas_por_red(item):
    """{red: hora México} de un video o carrusel programado (una hora por red desde la prueba por red). Facebook: su
    hora propia (item['facebook'], lo atrasado) o, desde INICIO_FB, la de Instagram de los videos."""
    por_red = dict(item.get('publica_utc_por_red') or ({r: item['publica_utc'] for r in NOMBRES_RED} if item.get('publica_utc') else {}))
    if (item.get('facebook') or {}).get('publica_utc') and not str(item['id']).startswith('c'):
        por_red['fb'] = item['facebook']['publica_utc']
    elif not str(item['id']).startswith('c') and por_red.get('ig', '') >= INICIO_FB + 'T12':
        por_red['fb'] = por_red['ig']
    return {r: a_mexico(t) for r, t in por_red.items()}


def corto(t, n=48):
    t = ' '.join(str(t or '').split())
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0].rstrip(',.;:¿¡') + '…'


def nombre(item):
    """Cómo lo lee Rodrigo: su título, no su número (11-nov-2026: "Sale el video 17" no decía nada)."""
    tipo = 'carrusel' if str(item.get('id', '')).startswith('c') else 'video'
    texto = ((item.get('seo') or {}).get('titulo') or item.get('titulo_post') or item.get('texto_pantalla')
             or str(item.get('tema', '')).replace('_', ' '))
    return f"{tipo} «{corto(texto)}»" if texto else f"{tipo} {item.get('id', '')}".strip()


def que_sale(item):
    return f"Sale el {nombre(item)}"


def calendario(plan, carruseles, config, auditoria, ahora, dias=10):
    """Lo que sale cada día: lo ya programado con su hora en cada red y, los días sin programar, lo que
    toca con el ritmo de config → publicaciones_por_dia."""
    local = ahora.astimezone(CDMX).date()
    programado = {}  # {día: {id: (item, {red: hora})}}: cada red en el día en que sale (un carrusel puede salir
    for x in plan['videos'] + carruseles:  # en TikTok un día y en Instagram y YouTube otro, regla del 2-nov)
        if x.get('estado') in ('programado', 'publicado'):
            for r, h in horas_por_red(x).items():
                programado.setdefault(h.date(), {}).setdefault(x['id'], (x, {}))[1][r] = h
    programado = {dia: list(items.values()) for dia, items in programado.items()}
    fechas_video = sorted(min(horas_por_red(v).values()).date() for v in plan['videos']
                          if v.get('estado') in ('programado', 'publicado') and horas_por_red(v))
    cada = config.get('dias_entre_videos', 2)
    ultimo = fechas_video[-1] if fechas_video else local
    listos = [c for c in carruseles if c.get('estado') == 'listo']
    # Todos los listos en orden (11-nov-2026: tras O1 el 14-nov decía "lo elige el laboratorio" con O2 ya listo).
    orden_pub = config.get('prioridad_publicar', [])
    videos_listos = sorted((v['id'] for v in plan['videos'] if v['estado'] == 'listo_para_publicar'),
                           key=lambda i: orden_pub.index(i) if i in orden_pub else len(orden_pub))
    por_id = {v['id']: v for v in plan['videos']}
    prioridad = config.get('prioridad_carruseles', [])
    filas = []
    for i in range(dias):
        dia = local + datetime.timedelta(days=i)
        hechos = programado.get(dia, [])
        # El Reel de Instagram de un carrusel va en su propia fila y no ocupa el día (sigue tocando video o carrusel).
        for c in carruseles:
            reel = (c.get('reel_ig') or {}).get('publica_utc')
            fb = (c.get('facebook') or {}).get('publica_utc')
            horas = {}
            if reel and a_mexico(reel).date() == dia:
                horas['ig'] = a_mexico(reel).strftime('%H:%M')
            if fb and a_mexico(fb).date() == dia:
                horas['fb'] = a_mexico(fb).strftime('%H:%M')
            if horas:
                que = (f"Reel del {nombre(c)} (el mismo video del Short)" if 'ig' in horas
                       else f"Video del {nombre(c)} en Facebook (ya salió en las otras redes)")
                filas.append({'fecha': dia.isoformat(), 'tipo': 'reel' if 'ig' in horas else 'facebook', 'id': c['id'], 'estado': 'programado',
                              'que': que, 'horas': horas})
        if hechos:
            for x, horas in hechos:
                que = que_sale(x) + (' en Facebook (ya salió en las otras redes)' if set(horas) == {'fb'} else '')
                solo_fb = set(horas) == {'fb'}  # un video que ese día solo sale en Facebook va como fila de Facebook
                filas.append({'fecha': dia.isoformat(), 'tipo': 'facebook' if solo_fb else 'carrusel' if str(x['id']).startswith('c') else 'video',
                              'id': x['id'], 'que': que, 'estado': x['estado'],
                              'horas': {r: h.strftime('%H:%M') for r, h in horas.items()}})
        # Hoy cuenta como pronóstico solo mientras la rutina de la mañana no ha programado nada en TikTok
        # (11-nov-2026: a las 4 a.m. el calendario de hoy salía vacío aunque hoy salen O1 y dos carruseles).
        if dia < local or (dia == local and any('tt' in h for _, h in hechos)):
            continue  # antes de hoy, u hoy ya programado: solo lo que de verdad está programado
        # Días por venir: lo que toca con el ritmo de config → publicaciones_por_dia (TikTok 3 al día, el video cuenta).
        en_tt = sum(1 for x, h in hechos if 'tt' in h)
        video_ya = any(not str(x['id']).startswith('c') and 'tt' in h for x, h in hechos)
        es_video = video_ya or ((dia - ultimo).days % cada == 0 and dia > ultimo)
        if es_video and not video_ya:
            vid = videos_listos.pop(0) if videos_listos else None
            filas.append({'fecha': dia.isoformat(), 'tipo': 'video', 'id': vid or '', 'estado': 'por_programar', 'horas': {},
                          'que': f'{"V" + nombre(por_id.get(vid, {"id": vid}))[1:]} (ya generado) · TikTok, Instagram, Facebook y YouTube' if vid
                          else 'Video (lo elige el laboratorio el día anterior)'})
            en_tt += 1
        cupo = (config.get('publicaciones_por_dia') or {}).get('tt', 1)
        for _ in range(max(0, cupo - en_tt)):
            # los de temporada solo dentro de su ventana; los de temporada en ventana van primero
            validos = [c for c in listos if not c.get('ventana') or c['ventana']['desde'] <= dia.isoformat() <= c['ventana']['hasta']]
            # Igual que la rutina (aprender.py): config → prioridad_carruseles primero, hasta prioridad_por_dia al día;
            # luego la temporada (11-nov-2026: el calendario anunciaba c22 el 12-nov y la rutina iba a sacar c27 y c67).
            ya_prio = sum(1 for f in filas if f['fecha'] == dia.isoformat() and f['id'] in prioridad)
            con_prio = sorted((x for x in validos if x['id'] in prioridad), key=lambda x: prioridad.index(x['id']))
            c = (con_prio[0] if con_prio and ya_prio < config.get('prioridad_por_dia', len(prioridad))
                 else next((x for x in validos if x.get('ventana')), validos[0] if validos else None))
            if c:
                listos.remove(c)
            titulo = 'C' + nombre(c)[1:] if c else 'Carrusel nuevo (se escribe)'
            filas.append({'fecha': dia.isoformat(), 'tipo': 'carrusel', 'id': c['id'] if c else '', 'estado': 'por_programar',
                          'horas': {}, 'que': titulo + ' · TikTok primero; luego Reel en Instagram y Facebook y short en YouTube'})
    return filas


def siguiente_listo(plan, config):
    """El siguiente video listo, en el mismo orden que la rutina: config.json → prioridad_publicar primero (11-nov-2026)."""
    listos = [v['id'] for v in plan['videos'] if v['estado'] == 'listo_para_publicar']
    orden = config.get('prioridad_publicar', [])
    listos.sort(key=lambda i: orden.index(i) if i in orden else len(orden))
    return listos[0] if listos else None


def siguiente_video(plan, config, auditoria, ahora):
    """Cuándo sale el siguiente video y cuál: lo ya programado o, si no hay, el que toca según la
    frecuencia (config.json → dias_entre_videos) y la franja de la prueba de horarios."""
    carruseles = cargar_carruseles()
    futuros = []
    for x in plan['videos'] + carruseles:
        if x.get('estado') == 'programado':
            horas = [h for h in horas_por_red(x).values() if h > ahora]
            if horas:
                futuros.append((min(horas), x))
    hay_video = any(not str(x['id']).startswith('c') for _, x in futuros)
    if futuros:
        cuando, x = min(futuros, key=lambda f: f[0])
        detalle = ' · '.join(f"{NOMBRES_RED[r]} {h.strftime('%H:%M')}" for r, h in sorted(horas_por_red(x).items()))
        if hay_video or cuando.date() <= (ahora.astimezone(CDMX).date()):
            return cuando, f'{que_sale(x)} ({detalle})'
        programado = (cuando, f'{que_sale(x)} ({detalle})')
    else:
        programado = None
    decision = auditoria.get('decision') or {}
    fechas = [a_mexico(v['publica_utc']).date() for v in plan['videos']
              if v['estado'] in ('programado', 'publicado') and v.get('publica_utc')]
    local = ahora.astimezone(CDMX)
    dia = max(fechas) + datetime.timedelta(days=config.get('dias_entre_videos', 2)) if fechas else local.date()
    hora = min((decision.get('horarios') or {}).values(), default=None) or config.get('hora_por_defecto', '18:45')
    hh, mm = (int(x) for x in hora.split(':'))
    cuando = datetime.datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=CDMX)
    if cuando <= local:
        cuando += datetime.timedelta(days=1)
    listo = siguiente_listo(plan, config)
    vid = listo or decision.get('video_id') or 'siguiente'
    item = next((v for v in plan['videos'] if v['id'] == vid), None)
    estimado = (cuando, f"Sale el {nombre(item) if item else 'siguiente video'} · cada red a su mejor hora")
    return min([estimado] + ([programado] if programado else []), key=lambda e: e[0])


def series_reales(plan, carruseles):
    """Vistas totales y publicaciones acumuladas por día (México), solo de lo medido y lo programado."""
    try:
        historial = json.load(open(os.path.join(RAIZ, 'contenido', 'metricas.json')))
    except (OSError, ValueError):
        historial = []
    por_dia, ultimas, por_red, medidas = {}, {}, {}, set()
    for foto in sorted(historial, key=lambda f: f['fecha_utc']):
        ultimas[foto['video_id']] = {r: de_red(foto, r) for r in ('yt', 'tt', 'ig', 'fb')}
        medidas |= {r for r in ('yt', 'tt', 'ig', 'fb') if r in foto or (r == 'ig' and 'igr' in foto)}
        dia = a_mexico(foto['fecha_utc']).date().isoformat()
        por_dia[dia] = sum(sum(x.values()) for x in ultimas.values())
        # una red entra a la serie desde el día en que se midió por primera vez (Facebook no aparece en 0 antes de existir)
        por_red[dia] = {r: sum(x[r] for x in ultimas.values()) for r in ('yt', 'tt', 'ig', 'fb') if r in medidas}
    fechas = sorted(min(horas_por_red(x).values()).date().isoformat() for x in plan['videos'] + carruseles
                    if x.get('estado') in ('programado', 'publicado') and horas_por_red(x))
    hoy = datetime.datetime.now(CDMX).date().isoformat()
    publicadas = {}
    for i, f in enumerate(fechas):
        if f <= hoy:
            publicadas[f] = i + 1
    return ([{'fecha': f, 'v': v} for f, v in sorted(por_dia.items())],
            [{'fecha': f, 'v': v} for f, v in sorted(publicadas.items())],
            [{'fecha': f, **v} for f, v in sorted(por_red.items())])


def main():
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    try:
        auditoria = json.load(open(os.path.join(RAIZ, 'contenido', 'auditoria.json')))
    except (OSError, ValueError):
        auditoria = {'videos_calificados': 0, 'ranking': {}, 'decision': None, 'alertas': [], 'notas': {}}
    anteriores = metricas_anteriores()
    filas = []
    for v in plan['videos']:
        local = a_mexico(v.get('publica_utc'))
        qa = v.get('qa')
        fila = {
            # .get: los videos "calcúlalo conmigo" (C1, 9-nov-2026) no traen guion de Wan ni locación
            'id': v['id'], 'estado': v['estado'], 'pilar': v.get('pilar', ''), 'locacion': v.get('locacion', ''),
            'fuente': v.get('fuente', ''), 'gancho': (v.get('guion') or v.get('titulo') or v.get('texto_post') or '').split('.')[0][:90],
            'hora_plan': v.get('hora_publicacion', ''),
            'publica_mx': local.strftime('%Y-%m-%d %H:%M') if local else '',
            'dia': DIAS[local.weekday()] if local else '',
            'qa_similitud': qa.get('similitud') if isinstance(qa, dict) else None,
            'creditos': v.get('creditos') if isinstance(v.get('creditos'), int) else None,
            'publica_utc': v.get('publica_utc', ''),
            'publica_utc_por_red': {r: h.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') for r, h in horas_por_red(v).items()},
            'miniatura': miniatura(os.path.join(RAIZ, v['archivo'])) if v.get('archivo') else '',
            'youtube_id': youtube_id((v.get('publicacion') or {}).get('youtube')),
            'linea': primera_linea(v.get('texto_post')),
            'titulo': (v.get('seo') or {}).get('titulo') or v.get('texto_pantalla') or '',
        }
        for corto in CAMPOS:
            for red in REDES.values():
                fila[f'{corto}_{red}'] = None
        fila.update(anteriores.get(v['id'], {}))
        filas.append(fila)

    por_video = metricas_historial()
    reales_ig = comentarios_ig_reales()
    reales_yt = comentarios_yt_reales()
    for f in filas:
        f.update(por_video.get(f['id'], {}))
        if f.get('linea') in reales_ig:
            f['c_ig_reales'] = reales_ig[f['linea']]
        if reales_yt and f.get('youtube_id'):
            f['c_yt_reales'] = reales_yt.get(f['youtube_id'], 0)
    puntajes = {}
    if os.environ.get('PUBLER_API_KEY'):
        try:
            puntajes = mejores_horas_publer()
        except SystemExit as e:
            print(f'AVISO: no se pudieron leer las mejores horas de Publer: {e}')

    guardar('videos.json', filas)
    carruseles = cargar_carruseles()
    guardar('carruseles.json', [{
        'id': c['id'], 'estado': c['estado'], 'tema': c.get('tema', '').replace('_', ' '), 'pilar': c.get('pilar', 'finanzas'),
        'gancho': c['portada']['titulo'], 'titulo': (c.get('seo') or {}).get('titulo', c.get('titulo_post', '')),
        'diapositivas': len(c.get('diapositivas', [])) + 2, 'fondo': os.path.basename(c.get('fondo', '') or ''),
        'portada': os.path.basename(c['portada'].get('foto', '')),
        'horas': {**{r: h.strftime('%Y-%m-%d %H:%M') for r, h in horas_por_red(c).items()},
                  **({'fb': a_mexico(c['facebook']['publica_utc']).strftime('%Y-%m-%d %H:%M')} if (c.get('facebook') or {}).get('publica_utc') else {})},
        'youtube_id': youtube_id(c.get('youtube')), 'publica_utc': c.get('publica_utc', ''),
        'linea': primera_linea(c.get('texto_post')), 'tipo': 'carrusel',
        'linea_reel': primera_linea((c.get('reel_ig') or {}).get('texto')),
        'reel_ig': a_mexico(c['reel_ig']['publica_utc']).strftime('%Y-%m-%d %H:%M') if (c.get('reel_ig') or {}).get('publica_utc') else '',
        'publica_utc_por_red': {**(c.get('publica_utc_por_red') or {}),
                                **({'fb': c['facebook']['publica_utc']} if (c.get('facebook') or {}).get('publica_utc') else {})},
        **por_video.get(c['id'], {}),
        **({'c_yt_reales': reales_yt.get(youtube_id(c.get('youtube')), 0)} if reales_yt and youtube_id(c.get('youtube')) else {}),
        **({'c_ig_reales': sum(reales_ig.get(l, 0) for l in {primera_linea(c.get('texto_post')), primera_linea((c.get('reel_ig') or {}).get('texto'))} if l)}
           if any(l in reales_ig for l in (primera_linea(c.get('texto_post')), primera_linea((c.get('reel_ig') or {}).get('texto')))) else {}),
    } for c in carruseles])
    guardar('calendario.json', calendario(plan, carruseles, config, auditoria, datetime.datetime.now(datetime.timezone.utc)))
    guardar('ejecuciones.json', json.load(open(os.path.join(RAIZ, 'contenido', 'ejecuciones.json'))))
    try:  # bitácora de cambios (Rodrigo, 9-nov-2026: "el chiste es mejorar día a día"): qué se cambió y cuándo
        guardar('cambios.json', json.load(open(os.path.join(RAIZ, 'contenido', 'cambios.json'))))
    except (OSError, ValueError):
        guardar('cambios.json', [])
    try:  # Comenta hoy (10-nov-2026): videos ajenos para que Rodrigo comente como Victoria en TikTok
        guardar('comentar_hoy.json', json.load(open(os.path.join(RAIZ, 'contenido', 'comentar_hoy.json'))))
    except (OSError, ValueError):
        guardar('comentar_hoy.json', {})
    guardar('aprendizajes.json', json.load(open(os.path.join(RAIZ, 'contenido', 'aprendizajes.json'))))
    json.dump(auditoria, open(os.path.join(SALIDA, 'auditoria.json'), 'w'), ensure_ascii=False, indent=1)
    guardar('mejores_horas.json', [
        {'dia': d, 'hora': h, 'puntaje': (sum(puntajes[(d, h)]) / len(puntajes[(d, h)])) if (d, h) in puntajes else None}
        for d in DIAS for h in range(24)])

    ahora = datetime.datetime.now(datetime.timezone.utc)
    proxima, proxima_que = siguiente_video(plan, config, auditoria, ahora)
    # El que sigue después: el centro lo usa cuando el primero ya salió y la foto aún no se rehace
    # (la foto se regenera en la ejecución diaria; sin esto el contador se quedaba en 00:00:00).
    proximas = [(proxima, proxima_que)]
    if proxima:
        # Para el que sigue, se cuenta el primero como ya salido (11-nov-2026: repetía "Sale el video O1" dos veces).
        import copy
        plan_despues = copy.deepcopy(plan)
        lid = siguiente_listo(plan, config)
        for v in plan_despues['videos']:
            if lid and v['id'] == lid and nombre(v) in proxima_que:
                iso = proxima.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                v.update({'estado': 'publicado', 'publica_utc': iso, 'publica_utc_por_red': {'tt': iso}})
        proximas.append(siguiente_video(plan_despues, config, auditoria, proxima + datetime.timedelta(minutes=1)))
    perfil = os.path.join(RAIZ, 'perfil', 'foto-perfil-1080.jpg')
    foto = ''
    if os.path.exists(perfil):
        jpg = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', perfil, '-vf', 'scale=160:-2', '-q:v', '5', '-f', 'mjpeg', '-'],
                             capture_output=True).stdout
        foto = 'data:image/jpeg;base64,' + base64.b64encode(jpg).decode()
    guardar('estado.json', [{
        'canal': '@victoriatheceo',
        'frecuencia': (lambda r: f"Al día: TikTok {r.get('tt', 1)} · Instagram {r.get('ig', 1)} (mañana y tarde) · YouTube "
                       f"{r.get('yt', 1)} · Facebook: lo de Instagram y los shorts de YouTube · video de Victoria cada {config.get('dias_entre_videos', 2)} días"
                       f" · auditoría diaria {config.get('hora_auditoria', '06:37')}")(config.get('publicaciones_por_dia') or {}),
        'dias_entre_videos': config.get('dias_entre_videos', 2),
        'proxima_ejecucion_utc': proxima.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if proxima else '',
        'proxima_que': proxima_que if proxima else '',
        'prioridad_publicar': config.get('prioridad_publicar', []),
        'prioridad_carruseles': config.get('prioridad_carruseles', []),
        'proximas': [{'utc': c.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'que': q} for c, q in proximas if c],
        'generado_utc': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'creditos_plan_mes': 12000,
        'similitud_minima': config.get('similitud_minima_audio'),
        # Facebook solo para el centro (números en vivo y agenda); medir sigue con Instagram y TikTok.
        'cuentas_publer': {**config.get('cuentas_publer', {}),
                           **({config['facebook_victoria']: 'facebook'} if config.get('facebook_victoria') else {})},
        'publer_workspace': workspace_publer(),  # el centro no lo vuelve a pedir: Publer tarda hasta 20 s en darlo
        'canal_youtube': config.get('canal_youtube', ''),
        'prueba_horas': config.get('prueba_horas', {}),
        'productos_hotmart': config.get('productos_hotmart', {}),
        'serie_vistas': series_reales(plan, cargar_carruseles())[0],
        'serie_publicaciones': series_reales(plan, cargar_carruseles())[1],
        'serie_redes': series_reales(plan, cargar_carruseles())[2],
        'foto_perfil': foto,
    }])


if __name__ == '__main__':
    main()
