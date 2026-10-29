"""Arma los datos del centro de mando de Victoria (centro/, en Vercel) en centro/datos/.

Uso: python tablero.py

- videos.json: un renglón por video del plan, con su cuadro (miniatura), su id de YouTube, la
  primera línea de su post y sus estadísticas por red (v_ vistas, l_ likes, c_ comentarios,
  s_ compartidos, g_ guardados; sufijos ig, tt, yt, fb). Las estadísticas vienen de la API de
  Publer si hay PUBLER_API_KEY; si no, se conservan las anteriores. El centro además las lee en
  vivo (centro/api/vivo.js); estas son la última foto por si la consulta en vivo falla.
- ejecuciones.json y aprendizajes.json: copias de contenido/.
- mejores_horas.json: rejilla día × hora de Publer (best_times); vacía (puntaje nulo) si no hay datos.
- estado.json: un renglón con la próxima ejecución (la tarea cada 2 días o una única de
  config.json → ejecuciones_unicas, la que llegue antes), la foto de perfil y datos fijos del canal.

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


def metricas_publer(filas):
    """{video_id: {v_ig: n, ...}} y la rejilla de mejores horas, desde Publer."""
    import publer
    ws = publer.workspace_id()
    _, victoria = publer.cuentas_victoria(ws)
    red_de = {c['id']: REDES.get(c['provider'], c['provider']) for c in victoria}
    hoy = datetime.date.today()
    desde = (hoy - datetime.timedelta(days=90)).isoformat()
    posts, pagina = [], 0
    while pagina < 30:
        r = publer._pedir('GET', f'/analytics/post_insights?from={desde}&to={hoy.isoformat()}&page={pagina}', ws)
        lote = r.get('posts') or []
        posts += lote
        if len(lote) < 10:
            break
        pagina += 1
    por_minuto = {f['publica_utc'][:16]: f['id'] for f in filas if f.get('publica_utc')}
    por_linea = {f['linea']: f['id'] for f in filas if f.get('linea')}
    por_video = {}
    for p in posts:
        red = red_de.get(p.get('account_id'))
        minuto = ''
        if p.get('scheduled_at'):
            minuto = datetime.datetime.fromisoformat(p['scheduled_at'].replace('Z', '+00:00')).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M')
        video = por_linea.get(primera_linea(p.get('text'))) or por_minuto.get(minuto)
        if not red or not video:
            continue
        a = p.get('analytics') or {}
        destino = por_video.setdefault(video, {})
        for corto, campo in CAMPOS.items():
            destino[f'{corto}_{red}'] = (destino.get(f'{corto}_{red}') or 0) + (a.get(campo) or 0)
    puntajes = {}
    for c in victoria:
        r = publer._pedir('GET', f"/analytics/{c['id']}/best_times?from={(hoy - datetime.timedelta(days=30)).isoformat()}&to={hoy.isoformat()}", ws)
        for dia, horas in (r or {}).items():
            for hora, puntaje in enumerate(horas or []):
                clave = (DIAS_EN.get(dia, dia), hora)
                puntajes.setdefault(clave, []).append(puntaje or 0)
    return por_video, puntajes


def primera_linea(texto):
    lineas = (texto or '').strip().splitlines()
    return ' '.join(lineas[0].split()).lower() if lineas else ''


def youtube_id(enlace):
    return (enlace or '').rstrip('/').split('/')[-1].split('=')[-1] if enlace else ''


def proxima_ejecucion(ahora):
    """La tarea corre los días pares del 2 al 30 a las 5:37 hora de México."""
    local = ahora.astimezone(CDMX)
    for dias in range(0, 40):
        d = (local + datetime.timedelta(days=dias)).replace(hour=5, minute=37, second=0, microsecond=0)
        if d > local and d.day % 2 == 0 and 2 <= d.day <= 30:
            return d
    return None


def main():
    plan = json.load(open(os.path.join(RAIZ, 'contenido', 'plan.json')))
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
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
            'miniatura': miniatura(os.path.join(RAIZ, v['archivo'])) if v.get('archivo') else '',
            'youtube_id': youtube_id((v.get('publicacion') or {}).get('youtube')),
            'linea': primera_linea(v.get('texto_post')),
        }
        for corto in CAMPOS:
            for red in REDES.values():
                fila[f'{corto}_{red}'] = None
        fila.update(anteriores.get(v['id'], {}))
        filas.append(fila)

    puntajes = {}
    if os.environ.get('PUBLER_API_KEY'):
        try:
            por_video, puntajes = metricas_publer(filas)
            for f in filas:
                f.update(por_video.get(f['id'], {}))
        except SystemExit as e:
            print(f'AVISO: no se pudieron leer las estadísticas de Publer: {e}')

    guardar('videos.json', filas)
    guardar('ejecuciones.json', json.load(open(os.path.join(RAIZ, 'contenido', 'ejecuciones.json'))))
    guardar('aprendizajes.json', json.load(open(os.path.join(RAIZ, 'contenido', 'aprendizajes.json'))))
    guardar('mejores_horas.json', [
        {'dia': d, 'hora': h, 'puntaje': (sum(puntajes[(d, h)]) / len(puntajes[(d, h)])) if (d, h) in puntajes else None}
        for d in DIAS for h in range(24)])

    ahora = datetime.datetime.now(datetime.timezone.utc)
    proxima = proxima_ejecucion(ahora)
    unicas = {u['video_id'] for u in config.get('ejecuciones_unicas', [])}
    listo = next((v['id'] for v in plan['videos'] if v['estado'] == 'listo_para_publicar' and v['id'] not in unicas), None)
    proxima_que = f'Publicar video {listo} (ya generado)' if listo else 'Generar y publicar el siguiente video'
    for u in config.get('ejecuciones_unicas', []):
        cuando = datetime.datetime.fromisoformat(u['utc'].replace('Z', '+00:00'))
        if ahora < cuando and (not proxima or cuando < proxima):
            proxima, proxima_que = cuando, u['que']
    perfil = os.path.join(RAIZ, 'perfil', 'foto-perfil-1080.jpg')
    foto = ''
    if os.path.exists(perfil):
        jpg = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', perfil, '-vf', 'scale=160:-2', '-q:v', '5', '-f', 'mjpeg', '-'],
                             capture_output=True).stdout
        foto = 'data:image/jpeg;base64,' + base64.b64encode(jpg).decode()
    guardar('estado.json', [{
        'canal': '@victoriatheceo',
        'frecuencia': 'Un video cada 2 días',
        'proxima_ejecucion_utc': proxima.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if proxima else '',
        'proxima_que': proxima_que if proxima else '',
        'generado_utc': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'creditos_plan_mes': 12000,
        'similitud_minima': config.get('similitud_minima_audio'),
        'cuentas_publer': config.get('cuentas_publer', {}),
        'canal_youtube': config.get('canal_youtube', ''),
        'foto_perfil': foto,
    }])


if __name__ == '__main__':
    main()
