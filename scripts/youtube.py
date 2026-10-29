"""Sube un video de Victoria a YouTube Shorts con la API de YouTube (sin Publer, sin costo).

Lee del entorno (nunca del repo): YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN.
Comandos:

  python youtube.py canal
      Muestra el canal al que apunta el permiso.
  python youtube.py subir video.mp4 "Título" descripcion.txt "2026-10-30T02:47:00Z" [--prueba]
      Sube el video programado para esa hora (UTC). Si faltan menos de 15 minutos, lo publica
      de inmediato. --prueba imprime los metadatos sin llamar a la API.

Solo sube si el nombre del canal contiene "filtro_cuentas" de contenido/config.json.
Marca el video como contenido sintético (status.containsSyntheticMedia) por ser hecho con IA.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
API = 'https://www.googleapis.com/youtube/v3'


def _http(metodo, url, datos=None, headers=None):
    req = urllib.request.Request(url, data=datos, headers=headers or {}, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.headers, r.read().decode()
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode()[:1500]
        if 'invalid_grant' in cuerpo:
            cuerpo += ('\nEl permiso de YouTube venció o se revocó. Si la app de Google está en modo '
                       '"Testing", los permisos caducan a los 7 días: hay que pasarla a "In production" '
                       'y volver a autorizar.')
        sys.exit(f'ERROR {e.code} en {metodo} {url.split("?")[0]}: {cuerpo}')


def _variable(nombre):
    # Copiadas de un .env pueden traer comillas o espacios alrededor
    return os.environ.get(nombre, '').strip().strip('"').strip("'")


def token():
    faltan = [v for v in ('YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN') if not _variable(v)]
    if faltan:
        sys.exit('ERROR: faltan variables de entorno: ' + ', '.join(faltan))
    datos = urllib.parse.urlencode({
        'client_id': _variable('YOUTUBE_CLIENT_ID'),
        'client_secret': _variable('YOUTUBE_CLIENT_SECRET'),
        'refresh_token': _variable('YOUTUBE_REFRESH_TOKEN'),
        'grant_type': 'refresh_token',
    }).encode()
    _, cuerpo = _http('POST', 'https://oauth2.googleapis.com/token', datos,
                      {'Content-Type': 'application/x-www-form-urlencoded'})
    return json.loads(cuerpo)['access_token']


def canal(acceso):
    _, cuerpo = _http('GET', f'{API}/channels?part=snippet&mine=true', headers={'Authorization': f'Bearer {acceso}'})
    items = json.loads(cuerpo).get('items') or []
    if not items:
        sys.exit('ERROR: el permiso no tiene canal de YouTube')
    return items[0]['id'], items[0]['snippet']['title']


def metadatos(titulo, descripcion, cuando):
    publica = datetime.datetime.fromisoformat(cuando.replace('Z', '+00:00'))
    inmediato = publica - datetime.datetime.now(datetime.timezone.utc) < datetime.timedelta(minutes=15)
    estado = {'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': True}
    if inmediato:
        estado['privacyStatus'] = 'public'
    else:
        estado.update(privacyStatus='private', publishAt=cuando)  # YouTube lo hace público a esa hora
    return {
        'snippet': {'title': titulo[:100], 'description': descripcion[:4900], 'categoryId': '27',
                    'defaultLanguage': 'es', 'defaultAudioLanguage': 'es',
                    'tags': ['negocios', 'finanzas', 'mentalidad', 'victoriatheceo']},
        'status': estado,
    }


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == 'canal':
        print('Canal: %s (%s)' % canal(token())[::-1])
        return
    if sys.argv[1] != 'subir' or len(sys.argv) < 6:
        sys.exit(__doc__)
    video, titulo, archivo_desc, cuando = sys.argv[2:6]
    meta = metadatos(titulo, open(archivo_desc).read().strip(), cuando)
    if '--prueba' in sys.argv:
        print(json.dumps(meta, ensure_ascii=False, indent=1))
        return

    acceso = token()
    canal_id, nombre = canal(acceso)
    if CONFIG['filtro_cuentas'].lower() not in nombre.lower():
        sys.exit(f"ERROR: el permiso apunta al canal '{nombre}', que no es de Victoria. No subo nada.")

    contenido = open(video, 'rb').read()
    cabeceras, _ = _http(
        'POST', 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        json.dumps(meta).encode(),
        {'Authorization': f'Bearer {acceso}', 'Content-Type': 'application/json; charset=UTF-8',
         'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(len(contenido))})
    _, cuerpo = _http('PUT', cabeceras['Location'], contenido,
                      {'Authorization': f'Bearer {acceso}', 'Content-Type': 'video/mp4'})
    subido = json.loads(cuerpo)
    estado = subido.get('status', {})
    print(f"OK subido a '{nombre}': https://youtube.com/shorts/{subido['id']} "
          f"| privacidad={estado.get('privacyStatus')} publica={estado.get('publishAt', 'ya')}")


if __name__ == '__main__':
    main()
