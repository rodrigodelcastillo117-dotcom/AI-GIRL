"""Cliente mínimo de la API de Publer para publicar los videos de Victoria.

Lee PUBLER_API_KEY del entorno (nunca del repo). Comandos:

  python publer.py cuentas
      Lista workspaces y cuentas conectadas.
  python publer.py publicar video.mp4 texto.txt "2026-10-30T02:47:00Z" "Título corto" [--prueba]
      Sube el video, programa el post en las cuentas de Victoria y espera el resultado.
      --prueba arma el payload y lo imprime sin llamar a la API.

Solo publica en cuentas cuyo nombre contiene FILTRO_CUENTAS (contenido/config.json), para no
publicar nunca en las cuentas de otras marcas del mismo workspace.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

BASE = 'https://app.publer.com/api/v1'
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
REDES = ('instagram', 'tiktok', 'youtube', 'facebook')


def _pedir(metodo, ruta, workspace=None, cuerpo=None, multipart=None):
    clave = os.environ.get('PUBLER_API_KEY')
    if not clave:
        sys.exit('ERROR: falta la variable de entorno PUBLER_API_KEY')
    headers = {'Authorization': f'Bearer-API {clave}', 'Accept': 'application/json'}
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


def cuentas_victoria(ws):
    todas = _lista(_pedir('GET', '/accounts', ws), 'accounts')
    filtro = CONFIG['filtro_cuentas'].lower()
    elegidas = [c for c in todas if c.get('provider') in REDES and filtro in (c.get('name') or '').lower()]
    return todas, elegidas


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


def armar_post(cuentas, media_id, texto, titulo, cuando):
    redes = {}
    for proveedor in {red(c) for c in cuentas}:
        media = [{'id': media_id, 'type': 'video'}]
        if proveedor == 'instagram':
            redes['instagram'] = {'type': 'reel', 'text': texto, 'media': media,
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
        'accounts': [{'id': c['id'], 'scheduled_at': cuando} for c in cuentas],
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

    if prueba:
        falsas = [{'id': 'ID_IG', 'provider': 'instagram'}, {'id': 'ID_TT', 'provider': 'tiktok'}]
        print(json.dumps(armar_post(falsas, 'MEDIA_ID', texto, titulo, cuando), ensure_ascii=False, indent=1))
        return

    ws = workspace_id()
    _, cuentas = cuentas_victoria(ws)
    if not cuentas:
        sys.exit(f"ERROR: no hay cuentas cuyo nombre contenga '{CONFIG['filtro_cuentas']}'. No publico nada.")
    print('Cuentas:', ', '.join(f"{red(c)}:{c.get('name')}" for c in cuentas))

    subida = _pedir('POST', '/media', ws, multipart=(os.path.basename(video), open(video, 'rb').read(), 'video/mp4'))
    media_id = subida.get('id') or (subida.get('data') or {}).get('id')
    if not media_id and subida.get('job_id'):
        media_id = _buscar_id(esperar_job(ws, subida['job_id']).get('result'))
    if not media_id:
        sys.exit(f'ERROR: la subida no regresó id de media: {json.dumps(subida)[:1500]}')
    print('Media subido:', media_id)

    r = _pedir('POST', '/posts/schedule', ws, cuerpo=armar_post(cuentas, media_id, texto, titulo, cuando))
    job = r.get('job_id') or (r.get('data') or {}).get('job_id')
    if not job:
        sys.exit(f'ERROR: Publer no regresó job_id: {json.dumps(r)[:1500]}')
    resultado = esperar_job(ws, job)
    fallas = ((resultado.get('result') or resultado).get('payload') or {}).get('failures')
    print('Resultado:', json.dumps(resultado, ensure_ascii=False)[:2000])
    if resultado.get('status') == 'failed' or fallas:
        sys.exit(f'ERROR: Publer reportó fallas: {json.dumps(fallas, ensure_ascii=False)[:1500]}')
    print(f'OK programado para {cuando} en {len(cuentas)} cuentas. job={job} media={media_id}')


if __name__ == '__main__':
    main()
