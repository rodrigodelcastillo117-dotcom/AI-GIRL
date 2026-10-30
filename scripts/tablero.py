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
        for red in ('yt', 'tt', 'ig'):
            for corto in ('v', 'l', 'c', 's'):
                if red in foto:
                    por_video.setdefault(vid, {})[f'{corto}_{red}'] = foto[red].get(corto, 0)
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


NOMBRES_RED = {'ig': 'Instagram', 'tt': 'TikTok', 'yt': 'YouTube'}


def horas_por_red(item):
    """{red: hora México} de un video o carrusel programado (una hora por red desde la prueba por red)."""
    por_red = item.get('publica_utc_por_red') or ({r: item['publica_utc'] for r in NOMBRES_RED} if item.get('publica_utc') else {})
    return {r: a_mexico(t) for r, t in por_red.items()}


def que_sale(item):
    if str(item['id']).startswith('c'):
        return f"Sale el carrusel {item['id']} · {item.get('tema', '').replace('_', ' ')}"
    return f"Sale el video {item['id']}"


def calendario(plan, carruseles, config, auditoria, ahora, dias=10):
    """Lo que sale cada día: lo ya programado con su hora en cada red y, los días sin programar, lo que
    toca (video y carrusel en días alternos)."""
    local = ahora.astimezone(CDMX).date()
    programado = {}
    for x in plan['videos'] + carruseles:
        if x.get('estado') in ('programado', 'publicado'):
            horas = horas_por_red(x)
            if horas:
                programado.setdefault(min(horas.values()).date(), []).append((x, horas))
    fechas_video = sorted(min(horas_por_red(v).values()).date() for v in plan['videos']
                          if v.get('estado') in ('programado', 'publicado') and horas_por_red(v))
    cada = config.get('dias_entre_videos', 2)
    ultimo = fechas_video[-1] if fechas_video else local
    listos = [c for c in carruseles if c.get('estado') == 'listo']
    video_listo = next((v['id'] for v in plan['videos'] if v['estado'] == 'listo_para_publicar'), None)
    filas = []
    for i in range(dias):
        dia = local + datetime.timedelta(days=i)
        hechos = programado.get(dia, [])
        if hechos:
            for x, horas in hechos:
                filas.append({'fecha': dia.isoformat(), 'tipo': 'carrusel' if str(x['id']).startswith('c') else 'video',
                              'id': x['id'], 'que': que_sale(x), 'estado': x['estado'],
                              'horas': {r: h.strftime('%H:%M') for r, h in horas.items()}})
            continue
        es_video = (dia - ultimo).days % cada == 0 and dia > ultimo
        if es_video:
            vid, video_listo = video_listo, None
            filas.append({'fecha': dia.isoformat(), 'tipo': 'video', 'id': vid or '', 'estado': 'por_programar', 'horas': {},
                          'que': f'Video {vid} (ya generado)' if vid else 'Video (lo elige el laboratorio el día anterior)'})
        else:
            # los de temporada solo dentro de su ventana; los de temporada en ventana van primero
            validos = [c for c in listos if not c.get('ventana') or c['ventana']['desde'] <= dia.isoformat() <= c['ventana']['hasta']]
            c = next((x for x in validos if x.get('ventana')), validos[0] if validos else None)
            if c:
                listos.remove(c)
            filas.append({'fecha': dia.isoformat(), 'tipo': 'carrusel', 'id': c['id'] if c else '', 'estado': 'por_programar',
                          'horas': {}, 'que': f"Carrusel {c['id']} · {c.get('tema', '').replace('_', ' ')}" if c else 'Carrusel nuevo (se escribe)'})
    return filas


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
    listo = next((v['id'] for v in plan['videos'] if v['estado'] == 'listo_para_publicar'), None)
    vid = listo or decision.get('video_id') or 'siguiente'
    estimado = (cuando, f'Sale el video {vid} · la hora de cada red la fija la auditoría de ese día')
    return min([estimado] + ([programado] if programado else []), key=lambda e: e[0])


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
            'id': v['id'], 'estado': v['estado'], 'pilar': v['pilar'], 'locacion': v['locacion'],
            'fuente': v.get('fuente', ''), 'gancho': v['guion'].split('.')[0][:90],
            'hora_plan': v.get('hora_publicacion', ''),
            'publica_mx': local.strftime('%Y-%m-%d %H:%M') if local else '',
            'dia': DIAS[local.weekday()] if local else '',
            'qa_similitud': qa.get('similitud') if isinstance(qa, dict) else None,
            'creditos': v.get('creditos') if isinstance(v.get('creditos'), int) else None,
            'publica_utc': v.get('publica_utc', ''),
            'publica_utc_por_red': v.get('publica_utc_por_red') or {},
            'miniatura': miniatura(os.path.join(RAIZ, v['archivo'])) if v.get('archivo') else '',
            'youtube_id': youtube_id((v.get('publicacion') or {}).get('youtube')),
            'linea': primera_linea(v.get('texto_post')),
        }
        for corto in CAMPOS:
            for red in REDES.values():
                fila[f'{corto}_{red}'] = None
        fila.update(anteriores.get(v['id'], {}))
        filas.append(fila)

    por_video = metricas_historial()
    for f in filas:
        f.update(por_video.get(f['id'], {}))
    puntajes = {}
    if os.environ.get('PUBLER_API_KEY'):
        try:
            puntajes = mejores_horas_publer()
        except SystemExit as e:
            print(f'AVISO: no se pudieron leer las mejores horas de Publer: {e}')

    guardar('videos.json', filas)
    carruseles = cargar_carruseles()
    guardar('carruseles.json', [{
        'id': c['id'], 'estado': c['estado'], 'tema': c.get('tema', '').replace('_', ' '),
        'gancho': c['portada']['titulo'], 'titulo': (c.get('seo') or {}).get('titulo', c.get('titulo_post', '')),
        'diapositivas': len(c.get('diapositivas', [])) + 2, 'fondo': os.path.basename(c.get('fondo', '') or ''),
        'portada': os.path.basename(c['portada'].get('foto', '')),
        'horas': {r: h.strftime('%Y-%m-%d %H:%M') for r, h in horas_por_red(c).items()},
        'youtube_id': youtube_id(c.get('youtube')), 'publica_utc': c.get('publica_utc', ''),
        'linea': primera_linea(c.get('texto_post')), 'tipo': 'carrusel',
        'publica_utc_por_red': c.get('publica_utc_por_red') or {},
        **por_video.get(c['id'], {}),
    } for c in carruseles])
    guardar('calendario.json', calendario(plan, carruseles, config, auditoria, datetime.datetime.now(datetime.timezone.utc)))
    guardar('ejecuciones.json', json.load(open(os.path.join(RAIZ, 'contenido', 'ejecuciones.json'))))
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
        proximas.append(siguiente_video(plan, config, auditoria, proxima + datetime.timedelta(minutes=1)))
    perfil = os.path.join(RAIZ, 'perfil', 'foto-perfil-1080.jpg')
    foto = ''
    if os.path.exists(perfil):
        jpg = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', perfil, '-vf', 'scale=160:-2', '-q:v', '5', '-f', 'mjpeg', '-'],
                             capture_output=True).stdout
        foto = 'data:image/jpeg;base64,' + base64.b64encode(jpg).decode()
    guardar('estado.json', [{
        'canal': '@victoriatheceo',
        'frecuencia': (f"Video y carrusel en días alternos: algo nuevo cada día · cada red a su hora"
                       f" · auditoría diaria {config.get('hora_auditoria', '06:37')}"),
        'dias_entre_videos': config.get('dias_entre_videos', 2),
        'proxima_ejecucion_utc': proxima.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if proxima else '',
        'proxima_que': proxima_que if proxima else '',
        'proximas': [{'utc': c.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'que': q} for c, q in proximas if c],
        'generado_utc': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'creditos_plan_mes': 12000,
        'similitud_minima': config.get('similitud_minima_audio'),
        'cuentas_publer': config.get('cuentas_publer', {}),
        'canal_youtube': config.get('canal_youtube', ''),
        'prueba_horas': config.get('prueba_horas', {}),
        'foto_perfil': foto,
    }])


if __name__ == '__main__':
    main()
