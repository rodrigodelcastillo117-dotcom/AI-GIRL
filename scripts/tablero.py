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


def siguiente_video(plan, config, auditoria, ahora):
    """Cuándo sale el siguiente video y cuál: lo ya programado o, si no hay, el que toca según la
    frecuencia (config.json → dias_entre_videos) y la franja de la prueba de horarios."""
    futuros = sorted((a_mexico(v['publica_utc']), v['id']) for v in plan['videos']
                     if v['estado'] == 'programado' and v.get('publica_utc') and a_mexico(v['publica_utc']) > ahora)
    if futuros:
        cuando, vid = futuros[0]
        return cuando, f'Sale el video {vid}'
    decision = auditoria.get('decision') or {}
    fechas = [a_mexico(v['publica_utc']).date() for v in plan['videos']
              if v['estado'] in ('programado', 'publicado') and v.get('publica_utc')]
    local = ahora.astimezone(CDMX)
    dia = max(fechas) + datetime.timedelta(days=config.get('dias_entre_videos', 2)) if fechas else local.date()
    hora = decision.get('hora_siguiente') or config.get('hora_por_defecto', '18:45')
    hh, mm = (int(x) for x in hora.split(':'))
    cuando = datetime.datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=CDMX)
    if cuando <= local:
        cuando += datetime.timedelta(days=1)
    listo = next((v['id'] for v in plan['videos'] if v['estado'] == 'listo_para_publicar'), None)
    vid = listo or decision.get('video_id') or 'siguiente'
    return cuando, f'Sale el video {vid} · franja {hora} de la prueba de horarios'


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
    guardar('ejecuciones.json', json.load(open(os.path.join(RAIZ, 'contenido', 'ejecuciones.json'))))
    guardar('aprendizajes.json', json.load(open(os.path.join(RAIZ, 'contenido', 'aprendizajes.json'))))
    json.dump(auditoria, open(os.path.join(SALIDA, 'auditoria.json'), 'w'), ensure_ascii=False, indent=1)
    guardar('mejores_horas.json', [
        {'dia': d, 'hora': h, 'puntaje': (sum(puntajes[(d, h)]) / len(puntajes[(d, h)])) if (d, h) in puntajes else None}
        for d in DIAS for h in range(24)])

    ahora = datetime.datetime.now(datetime.timezone.utc)
    proxima, proxima_que = siguiente_video(plan, config, auditoria, ahora)
    perfil = os.path.join(RAIZ, 'perfil', 'foto-perfil-1080.jpg')
    foto = ''
    if os.path.exists(perfil):
        jpg = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', perfil, '-vf', 'scale=160:-2', '-q:v', '5', '-f', 'mjpeg', '-'],
                             capture_output=True).stdout
        foto = 'data:image/jpeg;base64,' + base64.b64encode(jpg).decode()
    guardar('estado.json', [{
        'canal': '@victoriatheceo',
        'frecuencia': f"Un video cada {config.get('dias_entre_videos', 2)} días · auditoría diaria {config.get('hora_auditoria', '06:37')}",
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
