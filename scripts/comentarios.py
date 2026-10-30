"""Comentarios de YouTube sin contestar, y la respuesta de Victoria (la API sí deja responder; fijar no).

Uso: python comentarios.py pendientes                 comentarios de otros sin respuesta del canal
     python comentarios.py responder <id> "texto"     responde como el canal

Contestar rápido mueve el algoritmo (más conversación = más alcance). Instagram y TikTok se
contestan a mano en la app: sus APIs no están conectadas aquí.
Reglas de la respuesta (las escribe quien corre la rutina, nunca una plantilla fija):
- Corta (1-2 frases), en la voz de Victoria, en español de México, y que invite a seguir hablando.
- Nunca una recomendación de inversión concreta, ni consejo médico o legal personal (regla del canal).
- Si preguntan algo que se responde con una calculadora o la guía, se da el enlace de victoriatheceo.vercel.app.
- Si preguntan si es real: es un personaje creado con IA, y se dice sin rodeos.
- Spam, insultos o ventas: no se contestan.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from youtube import API, CONFIG, _http, token  # noqa: E402


def pendientes(acceso):
    canal = CONFIG['canal_youtube']
    _, r = _http('GET', f'{API}/commentThreads?part=snippet,replies&allThreadsRelatedToChannelId={canal}'
                        '&maxResults=100&order=time&textFormat=plainText', headers={'Authorization': f'Bearer {acceso}'})
    salida = []
    for hilo in json.loads(r).get('items', []):
        arriba = hilo['snippet']['topLevelComment']['snippet']
        if arriba.get('authorChannelId', {}).get('value') == canal:
            continue  # el comentario con enlace del propio canal
        respuestas = (hilo.get('replies') or {}).get('comments', [])
        if any(x['snippet'].get('authorChannelId', {}).get('value') == canal for x in respuestas):
            continue
        salida.append({'id': hilo['snippet']['topLevelComment']['id'], 'video': hilo['snippet'].get('videoId'),
                       'autor': arriba.get('authorDisplayName'), 'fecha': arriba.get('publishedAt'),
                       'texto': arriba.get('textDisplay')})
    return salida


def responder(acceso, padre, texto):
    cuerpo = {'snippet': {'parentId': padre, 'textOriginal': texto}}
    _, r = _http('POST', f'{API}/comments?part=snippet', json.dumps(cuerpo).encode(),
                 {'Authorization': f'Bearer {acceso}', 'Content-Type': 'application/json; charset=UTF-8'})
    return json.loads(r)['id']


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    acceso = token()
    if sys.argv[1] == 'pendientes':
        print(json.dumps(pendientes(acceso), ensure_ascii=False, indent=1))
    elif sys.argv[1] == 'responder' and len(sys.argv) == 4:
        print('ok', responder(acceso, sys.argv[2], sys.argv[3]))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
