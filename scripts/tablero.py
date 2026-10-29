"""Arma los datos del tablero de Victoria en tablero/datos/.

Uso: python tablero.py

- videos.json: un renglón por video del plan, con su cuadro (miniatura) y sus estadísticas por red
  (v_ vistas, l_ likes, c_ comentarios, s_ compartidos, g_ guardados; sufijos ig, tt, yt, fb).
  Las estadísticas vienen de la API de Publer si hay PUBLER_API_KEY; si no, se conservan las
  anteriores.
- ejecuciones.json y aprendizajes.json: copias de contenido/.
- mejores_horas.json: rejilla día × hora de Publer (best_times); vacía (puntaje nulo) si no hay datos.
- estado.json: un renglón con la próxima ejecución, la foto de perfil y datos fijos del canal.

El tablero no acepta archivos sin renglones: ninguno de estos queda vacío.
Después, la sesión que lo corre sube los archivos al tablero (docs/PIPELINE.md, paso 10).
"""
import base64
import datetime
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'tablero', 'datos')
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
    """Un cuadro del video como JPEG en data URL (el tablero solo acepta imágenes embebidas)."""
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
    por_video = {}
    for p in posts:
        red = red_de.get(p.get('account_id'))
        video = por_minuto.get((p.get('scheduled_at') or '').replace(' ', 'T')[:16])
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
        'generado_utc': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'creditos_plan_mes': 12000,
        'foto_perfil': foto,
    }])


if __name__ == '__main__':
    main()
