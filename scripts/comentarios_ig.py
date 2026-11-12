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
import re
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
ENLACES = [('renta', '/te-alcanza-tu-sueldo'), ('salario mínimo', '/te-alcanza-tu-sueldo'), ('aguinaldo', '/aguinaldo'), ('fondo de emergencia', '/fondo-de-emergencia'), ('deuda', '/pagar-deudas'),
           ('50/30/20', '/regla-50-30-20'), ('presupuesto', '/regla-50-30-20')]
REGISTRO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'contenido', 'guias_ig.json')


def enlace_para(texto_post):
    t = (texto_post or '').lower()
    ruta = next((r for clave, r in ENLACES if clave in t), '')
    return f'{SITIO}{ruta}?ref=ig-dm'


# 12-nov-2026, Rodrigo: "hay que mandarla a la correcta, no? quiero que se vean todas las calculadoras". Los posts dicen
# "Mis 30 reglas de la CEO… comenta GUÍA y te lo mando" y se mandaba la calculadora del tema (c70 → /aguinaldo): mal.
# Ahora GUÍA (o un post que promete las 30 reglas) recibe la página de la guía (/reglas: el PDF y las 7 calculadoras) y,
# de regalo, la calculadora del tema del post. Lo demás ("quiero", "calculadora"...) sigue con la calculadora del tema.
GUIA = f'{SITIO}/reglas?ref=ig-dm'


def mensaje_para(nombre, comentario, caption):
    """(enlace, texto del mensaje privado) para quien pidió algo en un post."""
    t = (comentario or '').lower().replace('í', 'i')
    calc = enlace_para(caption)
    hola = f'¡Hola{" @" + nombre if nombre else ""}!'
    if 'guia' in t or '30 reglas' in (caption or '').lower():
        extra = f'\n🧮 Y la calculadora del post: {calc}' if calc != f'{SITIO}?ref=ig-dm' else ''
        return GUIA, (f'{hola} Aquí están mis 30 reglas de la CEO, gratis 👇\n{GUIA}\n\n'
                      f'Ahí mismo tienes mis 7 calculadoras gratis.{extra}\n\nCuéntame en el post cuál te sirvió más. — Victoria')
    return calc, (f'{hola} Aquí está lo que te prometí 👇\n{calc}\n\n'
                  f'Y todas mis calculadoras gratis: {SITIO}/?ref=ig-dm#herramientas — Victoria')


# 11-nov-2026, Rodrigo autorizó ("si hazlo asi"): además de GUÍA, cuentan los comentarios cortos que piden el enlace
# ("quiero", "pásamelo", "info" o la palabra del tema). GUÍA cuenta en cualquier parte; las demás solo si el comentario
# tiene 4 palabras o menos, para no mandarle nada a quien está opinando ("el aguinaldo no me alcanza para nada...").
PALABRAS_CORTAS = ('quiero', 'pasamelo', 'pasame', 'mandamelo', 'link', 'info', 'aguinaldo', 'calcula', 'calculadora',
                   'lista', 'porfa', 'por favor', 'me interesa')


def pide_enlace(texto):
    t = texto.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    if 'guia' in t:
        return True
    limpio = ''.join(ch if ch.isalnum() or ch == ' ' else ' ' for ch in t).split()
    return 0 < len(limpio) <= 4 and any(p in ' '.join(limpio) for p in PALABRAS_CORTAS)


# 11-nov-2026, Rodrigo: "cuando comenten de su sueldo y rentas y así, manda ese link". Quien comenta sus números recibe
# en público su cuenta rápida (solo si los números se entienden sin duda) y por mensaje la calculadora ¿Te alcanza tu
# sueldo?. Si no se entiende cuál es el sueldo y cuál la renta, no se adivina: solo va el enlace.
CALCULADORA = f'{SITIO}/te-alcanza-tu-sueldo'


def _montos(t):
    """[(posición, monto)] de "12000", "12,000", "$4,500", "12 mil", "4.5k"; solo montos de 500 a 500,000."""
    salida = []
    for m in re.finditer(r'\$?\s*(\d{1,3}(?:[,.]\d{3})+|\d+(?:\.\d+)?)\s*(mil\b|k\b)?', t):
        crudo = m.group(1)
        valor = float(crudo.replace(',', '').replace('.', '')) if re.fullmatch(r'\d{1,3}(?:[,.]\d{3})+', crudo) else float(crudo)
        if m.group(2):
            valor *= 1000
        if 500 <= valor <= 500000:
            salida.append((m.start(), valor))
    return salida


def cuentas_de(texto, caption=''):
    """{'sueldo': x, 'renta': y} con lo que se entienda sin duda; None si el comentario no trae sus números."""
    t = (texto or '').lower()
    nums = _montos(t)
    if not nums:
        return None
    claves = {'sueldo': r'gano|sueldo|ingreso|cobro|salario|me pagan|quincena',
              'renta': r'renta|rento|alquiler' + ('|pago' if 'renta' in (caption or '').lower() else '')}
    hallado = {}
    for nombre, patron in claves.items():
        k = re.search(patron, t)
        if k:  # el monto más cercano a la palabra
            pos, valor = min(nums, key=lambda n: abs(n[0] - k.start()))
            hallado[nombre] = (pos, valor)
    if not hallado:
        return None
    if len(hallado) == 2 and hallado['sueldo'][0] == hallado['renta'][0]:
        return {}  # un solo número para dos cosas: no se adivina
    if 'quincena' in t and 'sueldo' in hallado and not re.search(r'al mes|mensual', t):
        hallado['sueldo'] = (hallado['sueldo'][0], hallado['sueldo'][1] * 2)
    return {k: v for k, (_, v) in hallado.items()}


def respuesta_cuentas(c):
    pesos = lambda n: f'${n:,.0f}'
    if 'sueldo' in c and 'renta' in c and c['renta'] < c['sueldo']:
        pct = round(100 * c['renta'] / c['sueldo'])
        estado = 'estás en zona sana 👌' if pct <= 30 else f'lo sano es 30% ({pesos(0.3 * c["sueldo"])})'
        return (f'Con {pesos(c["sueldo"])} de sueldo y {pesos(c["renta"])} de renta, la renta se lleva el {pct}%: {estado}. '
                'Te mandé por mensaje la calculadora para ver cuánto te queda para comer y lo demás 📩')
    return '¡Gracias por compartir tus números! Te mandé por mensaje la calculadora para que hagas tus cuentas completas 📩'


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
            if c.get('username') == YO or c['id'] in ya:
                continue
            numeros = None if pide_enlace(texto) else cuentas_de(c.get('text'), m.get('caption'))
            if numeros is None and not pide_enlace(texto):
                continue
            if any(r.get('username') == YO for r in (c.get('replies') or {}).get('data', [])):
                continue  # ya lo contestó el aviso instantáneo (centro/api/meta.js)
            nombre = c.get('username') or ''
            if numeros is not None:  # comentó su sueldo o su renta: su cuenta en público y la calculadora por mensaje
                enlace = f'{CALCULADORA}?ref=ig-cuentas'
                try:
                    mid = privado(c['id'], f'¡Hola{" @" + nombre if nombre else ""}! Aquí haces tus cuentas completas en segundos 👇\n{enlace}\n\n'
                                           'Y tu caso puede salir en la parte 3 de la serie (sin tu nombre). — Victoria')
                    publica, via = responder(c['id'], respuesta_cuentas(numeros)), 'privado'
                except RuntimeError as e:
                    print(e)
                    mid, via = None, 'publico'
                    publica = responder(c['id'], respuesta_cuentas(numeros).replace('Te mandé por mensaje la calculadora', 'Aquí la calculadora: '
                                        + enlace.replace('https://', '') + ',').replace(' 📩', ''))
                hechos.append({'comentario': c['id'], 'autor': nombre, 'enlace': enlace, 'via': via, 'mensaje': mid, 'respuesta': publica,
                               'fecha': c.get('timestamp'), 'tipo': 'cuentas', 'numeros': numeros, 'texto': c.get('text')})
                print(f'ok cuentas {via}: @{nombre} {numeros}')
                continue
            enlace, texto_privado = mensaje_para(nombre, c.get('text'), m.get('caption'))
            try:
                mid = privado(c['id'], texto_privado)
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
