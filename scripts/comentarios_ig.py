"""Comentarios de Instagram sin contestar, y la respuesta de Victoria (9-nov-2026).

Uso: python comentarios_ig.py pendientes                 comentarios de otros sin respuesta de @victoriatheceo
     python comentarios_ig.py responder <id> "texto"     responde como @victoriatheceo

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


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == 'pendientes':
        print(json.dumps(pendientes(), ensure_ascii=False, indent=1))
    elif sys.argv[1] == 'responder' and len(sys.argv) == 4:
        print('ok', responder(sys.argv[2], sys.argv[3]))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
