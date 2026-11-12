"""Todo lo demás del sistema en el panel (Rodrigo, 12-nov-2026: "conecta todo al dashboard. todo, todo, todo").

Uso: python3 scripts/sistema.py   → centro/datos/sistema.json (lo llama tablero.py; también solo)

Junta, con datos reales del momento:
- Victoria Hoy: la edición más reciente (titular, noticias, enlace) y si ya hay historia hoy en Instagram.
- Comunidad: guías entregadas (Instagram por mensaje, YouTube por respuesta), comentarios propios de Victoria, y lo que
  sigue pendiente ahora mismo (comentarios de YouTube e Instagram sin respuesta, mensajes privados).
- Instagram a fondo: estadísticas de las últimas publicaciones (vistas, alcance, likes, comentarios, guardados,
  compartidos) con el permiso instagram_manage_insights (token nuevo del 12-nov).
- Facebook: seguidores de la página.
- Página web: si cada página responde, si la IA de las calculadoras está activa y si la portada ya vende el Kit CEO.
- Automatizaciones: qué corre solo, cuándo, y el vencimiento del token de Meta (config.json → automatizaciones).
Cada bloque va en su try: si una fuente falla, ese bloque dice el error y lo demás sale igual.
"""
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SITIO = 'https://victoriatheceo.vercel.app'
AHORA = datetime.datetime.now(datetime.timezone.utc)


def leer(ruta, defecto):
    try:
        return json.load(open(os.path.join(RAIZ, ruta)))
    except (OSError, ValueError):
        return defecto


def bloque(f):
    try:
        return f()
    except (SystemExit, Exception) as e:  # una fuente caída no tumba el resto
        return {'error': str(e)[:200]}


def victoria_hoy():
    import noticias
    rutas = noticias.ediciones()
    ed = json.load(open(rutas[-1])) if rutas else None
    historias = leer('contenido/noticias/historias.json', [])
    return {'fecha': ed and ed['fecha'], 'titulo': ed and ed['titulo'], 'noticias': [n['titulo'] for n in (ed or {}).get('noticias', [])],
            'url': f'{SITIO}/hoy', 'ediciones': len(rutas), 'historia_hoy': bloque(noticias.ya_hay_historia_hoy),
            'historias_publicadas_auto': len(historias)}


def comunidad():
    import comentarios
    import comentarios_ig
    import youtube
    salida = {'guias_ig': len(leer('contenido/guias_ig.json', [])), 'guias_youtube': len(leer('contenido/guias_youtube.json', [])),
              'comentarios_propios': len([x for x in leer('contenido/primeros_comentarios.json', []) if x.get('comentario')])}
    salida['pendientes_youtube'] = bloque(lambda: len(comentarios.pendientes(youtube.token())))
    salida['pendientes_instagram'] = bloque(lambda: len(comentarios_ig.pendientes()))
    try:
        import primer_comentario
        salida['sin_comentario_propio'] = len([x for x in primer_comentario.pendientes_yt() + primer_comentario.pendientes_ig() if 'error' not in x])
    except (SystemExit, Exception) as e:
        salida['sin_comentario_propio'] = {'error': str(e)[:120]}
    return salida


def instagram():
    from comentarios_ig import IG_USUARIO, _http
    campos = 'id,caption,timestamp,media_product_type,permalink,like_count,comments_count'
    m = _http('GET', f'{IG_USUARIO}/media?fields={urllib.parse.quote(campos)}&limit=12')
    filas = []
    for p in m.get('data', []):
        fila = {'id': p['id'], 'fecha': p['timestamp'][:10], 'tipo': p.get('media_product_type', ''), 'titulo': (p.get('caption') or '').split('\n')[0][:70],
                'url': p.get('permalink'), 'likes': p.get('like_count', 0), 'comentarios': p.get('comments_count', 0)}
        metricas = 'views,reach,saved,shares' if p.get('media_product_type') in ('REELS', 'FEED') else 'reach,saved,shares'
        try:
            r = _http('GET', f'{p["id"]}/insights?metric={metricas}')
            fila.update({d['name']: d['values'][0]['value'] for d in r.get('data', [])})
        except SystemExit as e:
            fila['error'] = str(e)[:80]
        filas.append(fila)
    tot = lambda k: sum(f.get(k, 0) or 0 for f in filas)
    return {'publicaciones': filas, 'totales': {k: tot(k) for k in ('views', 'reach', 'likes', 'comentarios', 'saved', 'shares')}}


def facebook():
    import primer_comentario
    import publer
    pagina = publer.CONFIG.get('facebook_pagina_id')
    if not pagina:
        return {'error': 'falta facebook_pagina_id'}
    r = primer_comentario.fb('GET', f'{pagina}?fields=name,followers_count,fan_count', pagina)
    return {'nombre': r.get('name'), 'seguidores': r.get('followers_count'), 'me_gusta': r.get('fan_count')}


def web():
    def estado(ruta):
        try:
            with urllib.request.urlopen(urllib.request.Request(SITIO + ruta, headers={'User-Agent': 'victoria-panel'}), timeout=20) as r:
                return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            return e.code, ''
        except Exception:
            return 0, ''
    paginas = {}
    for ruta in ('/', '/reglas', '/hoy', '/aguinaldo', '/te-alcanza-tu-sueldo', '/finiquito', '/interes-compuesto', '/regla-50-30-20',
                 '/fondo-de-emergencia', '/pagar-deudas'):
        c, cuerpo = estado(ruta)
        paginas[ruta] = {'ok': c == 200, 'codigo': c, 'ia': 'victoriaIA(' in cuerpo or 'analiza mi caso' in cuerpo}
        if ruta == '/':
            kit = 'El Kit CEO' in cuerpo
    ia = estado('/api/diagnostico')[0] == 200
    guia = estado('/guia/las-30-reglas-de-la-ceo.pdf')[0] == 200
    return {'paginas': paginas, 'ia_calculadoras': ia, 'kit_en_portada': kit, 'guia_pdf': guia,
            'pendiente_de_publicar': [x for x, v in (('IA en las 7 calculadoras', ia), ('Kit CEO en la portada', kit)) if not v]}


def main():
    conf = leer('contenido/config.json', {})
    salida = {
        'generado_utc': AHORA.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'victoria_hoy': bloque(victoria_hoy),
        'comunidad': bloque(comunidad),
        'instagram': bloque(instagram),
        'facebook': bloque(facebook),
        'web': bloque(web),
        'automatizaciones': conf.get('automatizaciones', {}),
    }
    json.dump(salida, open(os.path.join(RAIZ, 'centro', 'datos', 'sistema.json'), 'w'), ensure_ascii=False)
    print('sistema.json:', {k: ('error' if isinstance(v, dict) and 'error' in v else 'ok') for k, v in salida.items() if k != 'generado_utc'})


if __name__ == '__main__':
    main()
