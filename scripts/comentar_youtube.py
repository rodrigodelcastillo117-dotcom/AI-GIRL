"""Victoria comenta en videos ajenos de YouTube (Rodrigo, 10-nov-2026: "¿es imposible que tú hagas eso en YouTube?").

TikTok e Instagram no dejan comentar en publicaciones ajenas por API (Instagram solo donde mencionan a la cuenta); YouTube
sí: commentThreads.insert con el permiso youtube.force-ssl que ya tiene el canal de Victoria. Es lo mismo que "Comenta
hoy" de TikTok, pero lo hace la rutina sola.

Uso: python comentar_youtube.py buscar                      videos de finanzas en México de los últimos 3 días
     python comentar_youtube.py comentar <video_id> "texto"  comenta como el canal de Victoria (máximo 3 al día)
     python comentar_youtube.py hoy                          lo que ya se comentó hoy

Reglas (para no caer en el filtro de spam de YouTube ni quemar el canal):
- Máximo 3 comentarios al día, nunca dos en el mismo canal el mismo día, nunca dos veces en el mismo video.
- Comentario específico a ESE video (que se note que lo vio: usa la transcripción o la descripción), con un dato mexicano
  comprobado o una opinión de Victoria; sin enlaces, sin "sígueme", sin "visita mi canal", sin consejos de inversión,
  nunca el mismo texto dos veces. Máximo 300 caracteres.
- Solo videos en español de finanzas personales, trabajo, pareja y dinero, o noticias de dinero. Nunca de menores, de
  política partidista, de tragedias o de odio.
Registro: contenido/comentarios_youtube_ajenos.json.
"""
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from youtube import API, _http, canal, comentar, token  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRO = os.path.join(RAIZ, 'contenido', 'comentarios_youtube_ajenos.json')
MAXIMO_DIA = 3
BUSQUEDAS = ['aguinaldo 2026', 'finanzas personales México', 'tarjeta de crédito México', 'salario mínimo México 2026',
             'dinero en pareja', 'Buen Fin 2026', 'ahorro México', 'impuestos SAT México']
TEMAS = ('aguinaldo', 'dinero', 'ahorr', 'tarjeta', 'crédito', 'credito', 'salario', 'buen fin', 'deuda', 'impuesto', 'sat ',
         'finanzas', 'quincena', 'nómina', 'nomina', 'afore', 'banco', 'pareja', 'sueldo', 'precio', 'oferta', 'inversi')
NO_ES = ('ã', 'ç', 'õ', 'você', 'salário', 'aposentad')  # portugués


def _get(acceso, ruta):
    _, cuerpo = _http('GET', f'{API}/{ruta}', headers={'Authorization': f'Bearer {acceso}'})
    return json.loads(cuerpo)


def registro():
    return json.load(open(REGISTRO)) if os.path.exists(REGISTRO) else []


def hoy_mx():
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=6)).date().isoformat()


def buscar(acceso):
    desde = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')
    propio = canal(acceso)
    ya = {r['video_id'] for r in registro()}
    vistos, ids = set(), []
    for q in BUSQUEDAS:
        r = _get(acceso, 'search?part=snippet&type=video&maxResults=10&order=viewCount&regionCode=MX&relevanceLanguage=es'
                         f'&publishedAfter={desde}&q={urllib.parse.quote(q)}')
        for it in r.get('items', []):
            v = it['id']['videoId']
            if v not in vistos and v not in ya and it['snippet']['channelId'] != propio:
                vistos.add(v)
                ids.append(v)
    salida = []
    for i in range(0, len(ids), 50):
        r = _get(acceso, f'videos?part=snippet,statistics&id={",".join(ids[i:i + 50])}')
        for v in r.get('items', []):
            e = v.get('statistics', {})
            if 'commentCount' not in e:
                continue  # comentarios apagados
            sn = v['snippet']
            idioma = (sn.get('defaultAudioLanguage') or sn.get('defaultLanguage') or 'es').lower()
            texto = (sn['title'] + ' ' + sn.get('description', '')).lower()
            if not idioma.startswith('es') or any(x in texto for x in NO_ES) or not any(t in texto for t in TEMAS):
                continue  # otro idioma u otro tema
            salida.append({'video_id': v['id'], 'url': f'https://youtube.com/watch?v={v["id"]}',
                           'canal': v['snippet']['channelTitle'], 'canal_id': v['snippet']['channelId'],
                           'titulo': v['snippet']['title'], 'publicado': v['snippet']['publishedAt'][:10],
                           'vistas': int(e.get('viewCount', 0)), 'comentarios': int(e.get('commentCount', 0)),
                           'descripcion': v['snippet'].get('description', '')[:400]})
    return sorted(salida, key=lambda x: -x['vistas'])[:20]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    acceso = token()
    if sys.argv[1] == 'buscar':
        print(json.dumps(buscar(acceso), ensure_ascii=False, indent=1))
    elif sys.argv[1] == 'hoy':
        print(json.dumps([r for r in registro() if r['fecha'] == hoy_mx()], ensure_ascii=False, indent=1))
    elif sys.argv[1] == 'comentar' and len(sys.argv) == 4:
        video_id, texto = sys.argv[2], sys.argv[3].strip()
        hechos = registro()
        de_hoy = [r for r in hechos if r['fecha'] == hoy_mx()]
        if len(de_hoy) >= MAXIMO_DIA:
            sys.exit(f'NO: ya van {MAXIMO_DIA} comentarios hoy (máximo diario).')
        if any(r['video_id'] == video_id for r in hechos):
            sys.exit('NO: ya se comentó en ese video.')
        if any(r['texto'] == texto for r in hechos):
            sys.exit('NO: ese texto ya se usó; escribe uno específico para este video.')
        if len(texto) > 300 or 'http' in texto.lower() or 'sígueme' in texto.lower() or 'mi canal' in texto.lower():
            sys.exit('NO: máximo 300 caracteres, sin enlaces, sin "sígueme" ni "mi canal".')
        v = _get(acceso, f'videos?part=snippet&id={video_id}')['items'][0]['snippet']
        if v['channelId'] == canal(acceso):
            sys.exit('NO: ese video es del canal de Victoria.')
        if any(r['canal_id'] == v['channelId'] for r in de_hoy):
            sys.exit('NO: hoy ya se comentó en ese canal.')
        cid = comentar(acceso, video_id, texto)
        hechos.append({'fecha': hoy_mx(), 'video_id': video_id, 'canal': v['channelTitle'], 'canal_id': v['channelId'],
                       'titulo': v['title'], 'texto': texto, 'comentario_id': cid})
        json.dump(hechos, open(REGISTRO, 'w'), ensure_ascii=False, indent=1)
        print(f'ok: comentado en "{v["title"]}" de {v["channelTitle"]} ({cid}).')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
