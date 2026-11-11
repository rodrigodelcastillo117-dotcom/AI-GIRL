"""Comentarios de Instagram sin contestar, y la respuesta de Victoria (9-nov-2026).

Uso: python comentarios_ig.py pendientes                 comentarios de otros sin respuesta de @victoriatheceo
     python comentarios_ig.py responder <id> "texto"     responde como @victoriatheceo
     python comentarios_ig.py privado <id> "texto"       le manda un mensaje privado a quien comentó
     python comentarios_ig.py mensajes                   mensajes privados sin respuesta (últimas 23 h)
     python comentarios_ig.py contestar <para> "texto"   contesta ese mensaje privado como Victoria
     python comentarios_ig.py guias                      a quien comentó GUÍA le manda el enlace por mensaje

El token (app "Victoria Comentarios" de Meta, usuario del sistema, no caduca) NO está en el repo ni en una variable:
lo pone el proxy de la sesión en cada petición a graph.facebook.com (secreto de red del entorno). Por eso aquí no se
manda ningún encabezado de autorización.
Las reglas de la respuesta son las mismas de comentarios.py (YouTube) y docs/PERSONAJE.md:
- Corta (1-2 frases), en la voz de Victoria, español de México, que invite a seguir hablando.
- Nunca recomendación de inversión concreta ni consejo médico o legal personal.
- Si dan su sueldo: su aguinaldo mínimo (sueldo / 30 × 15, "con el año completo") y cómo lo repartiría Victoria (50/30/20,
  como opinión suya). Si dan su profesión: "la reviso en un próximo carrusel".
- Si preguntan si es real: es un personaje creado con IA.
- Spam, insultos o ventas: no se contestan.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

GRAPH = 'https://graph.facebook.com/v21.0'
IG_USUARIO = '17841478105608541'  # @victoriatheceo (Instagram business, comprobado el 9-nov-2026)
YO = 'victoriatheceo'


def _http(metodo, ruta, datos=None):
    cuerpo = urllib.parse.urlencode(datos).encode() if datos else None
    req = urllib.request.Request(f'{GRAPH}/{ruta}', data=cuerpo, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f'ERROR {e.code} en {metodo} {ruta.split("?")[0]}: {e.read().decode()[:300]}')


def pendientes(publicaciones=25):
    campos = ('id,caption,permalink,timestamp,comments.limit(50){id,text,username,timestamp,'
              'replies.limit(50){username}}')
    media = _http('GET', f'{IG_USUARIO}/media?fields={urllib.parse.quote(campos)}&limit={publicaciones}')
    salida = []
    for m in media.get('data', []):
        for c in (m.get('comments') or {}).get('data', []):
            if c.get('username') == YO:
                continue  # el primer comentario que pone Publer, o una respuesta nuestra suelta
            if any(r.get('username') == YO for r in (c.get('replies') or {}).get('data', [])):
                continue
            salida.append({'id': c['id'], 'post': m.get('permalink'), 'autor': c.get('username'),
                           'fecha': c.get('timestamp'), 'texto': c.get('text'),
                           'post_inicio': (m.get('caption') or '').split('\n')[0][:80]})
    return salida


def responder(comentario, texto):
    return _http('POST', f'{comentario}/replies', {'message': texto}).get('id')


def privado(comentario, texto):
    """Mensaje privado a quien dejó el comentario (respuesta privada de Instagram; solo una por comentario y dentro de
    7 días). Para "Comenta GUÍA y te la mando por mensaje" (10-nov-2026)."""
    cuerpo = json.dumps({'recipient': {'comment_id': comentario}, 'message': {'text': texto}}).encode()
    req = urllib.request.Request(f'{GRAPH}/{IG_USUARIO}/messages', data=cuerpo, method='POST',
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode()).get('message_id')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'ERROR {e.code} al mandar el mensaje privado: {e.read().decode()[:300]}')


SITIO = 'https://victoriatheceo.vercel.app'
ENLACES = [('aguinaldo', '/aguinaldo'), ('fondo de emergencia', '/fondo-de-emergencia'), ('deuda', '/pagar-deudas'),
           ('50/30/20', '/regla-50-30-20'), ('presupuesto', '/regla-50-30-20')]
REGISTRO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'contenido', 'guias_ig.json')


def enlace_para(texto_post):
    t = (texto_post or '').lower()
    ruta = next((r for clave, r in ENLACES if clave in t), '')
    return f'{SITIO}{ruta}?ref=ig-dm'


def guias():
    """Quien comentó GUÍA recibe el enlace por mensaje privado y una respuesta pública corta (suma otro comentario y le
    avisa que revise sus mensajes). Si Meta no deja mandar el privado, la respuesta pública lleva el enlace."""
    hechos = json.load(open(REGISTRO)) if os.path.exists(REGISTRO) else []
    ya = {h['comentario'] for h in hechos}
    campos = 'id,caption,comments.limit(50){id,text,username,timestamp,replies.limit(20){username}}'
    media = _http('GET', f'{IG_USUARIO}/media?fields={urllib.parse.quote(campos)}&limit=25')
    for m in media.get('data', []):
        for c in (m.get('comments') or {}).get('data', []):
            texto = (c.get('text') or '').lower().replace('í', 'i')
            if c.get('username') == YO or c['id'] in ya or 'guia' not in texto:
                continue
            if any(r.get('username') == YO for r in (c.get('replies') or {}).get('data', [])):
                continue  # ya lo contestó el aviso instantáneo (centro/api/meta.js)
            enlace, nombre = enlace_para(m.get('caption')), c.get('username') or ''
            try:
                mid = privado(c['id'], f'¡Hola{" @" + nombre if nombre else ""}! Aquí está lo que te prometí 👇\n{enlace}\n\n'
                                       'Si te sirve, cuéntame en el post qué te pareció. — Victoria')
                publica, via = responder(c['id'], '¡Listo! Te lo mandé por mensaje 📩 Revisa tus solicitudes si no lo ves.'), 'privado'
            except RuntimeError as e:
                print(e)
                mid, via = None, 'publico'
                publica = responder(c['id'], f'¡Aquí lo tienes! 👉 {enlace.replace("https://", "")}')
            hechos.append({'comentario': c['id'], 'autor': nombre, 'enlace': enlace, 'via': via, 'mensaje': mid,
                           'respuesta': publica, 'fecha': c.get('timestamp')})
            print(f'ok {via}: @{nombre} → {enlace}')
    json.dump(hechos, open(REGISTRO, 'w'), ensure_ascii=False, indent=1)
    print(f'{len(hechos)} guía(s) entregadas en total.')


def mensajes_pendientes():
    """Mensajes privados de otras personas cuyo último mensaje no tiene respuesta de Victoria, dentro de las 24 h en que
    Meta deja contestar (10-nov-2026). Victoria solo contesta a quien le escribió primero."""
    import datetime
    campos = 'id,updated_time,participants,messages.limit(10){id,from,message,created_time}'
    datos = _http('GET', f'{IG_USUARIO}/conversations?platform=instagram&fields={urllib.parse.quote(campos)}&limit=50')
    ahora = datetime.datetime.now(datetime.timezone.utc)
    salida = []
    for c in datos.get('data', []):
        ms = (c.get('messages') or {}).get('data', [])
        if not ms or (ms[0].get('from') or {}).get('username') == YO:
            continue
        cuando = datetime.datetime.strptime(ms[0]['created_time'][:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc)
        if (ahora - cuando).total_seconds() > 23 * 3600:
            continue
        sin_contestar = []
        for m in ms:
            if (m.get('from') or {}).get('username') == YO:
                break
            sin_contestar.append(m.get('message') or '[foto, audio o publicación compartida]')
        salida.append({'para': ms[0]['from']['id'], 'autor': ms[0]['from'].get('username'), 'fecha': ms[0]['created_time'],
                       'mensajes': list(reversed(sin_contestar))})
    return salida


def contestar_mensaje(para, texto):
    cuerpo = json.dumps({'recipient': {'id': para}, 'message': {'text': texto}}).encode()
    req = urllib.request.Request(f'{GRAPH}/{IG_USUARIO}/messages', data=cuerpo, method='POST',
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode()).get('message_id')
    except urllib.error.HTTPError as e:
        sys.exit(f'ERROR {e.code} al contestar el mensaje: {e.read().decode()[:300]}')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == 'pendientes':
        print(json.dumps(pendientes(), ensure_ascii=False, indent=1))
    elif sys.argv[1] == 'responder' and len(sys.argv) == 4:
        print('ok', responder(sys.argv[2], sys.argv[3]))
    elif sys.argv[1] == 'privado' and len(sys.argv) == 4:
        print('ok', privado(sys.argv[2], sys.argv[3]))
    elif sys.argv[1] == 'guias':
        guias()
    elif sys.argv[1] == 'mensajes':
        print(json.dumps(mensajes_pendientes(), ensure_ascii=False, indent=1))
    elif sys.argv[1] == 'contestar' and len(sys.argv) == 4:
        print('ok', contestar_mensaje(sys.argv[2], sys.argv[3]))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
