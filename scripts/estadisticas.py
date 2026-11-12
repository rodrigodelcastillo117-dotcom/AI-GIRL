"""Estadísticas del panel (Rodrigo, 12-nov-2026: "quiero ver las vistas diarias, seguidores ganados diarios, créditos de
todo lo que usamos, dinero gastado, stats, mejores días, horas, mejores temas, comparativas. Lo más pro que puedas").

Uso: python3 scripts/estadisticas.py        → centro/datos/estadisticas.json (lo llama tablero.py; también solo)

Fuentes (todo real, nada estimado salvo lo que dice "estimado"):
- Vistas por día y red: estado.json → serie_redes (acumulado de la medición diaria) → diferencia día a día.
- YouTube por día: YouTube Analytics (vistas, suscriptores ganados/perdidos, minutos, likes, compartidos, fuentes
  de tráfico). YouTube Analytics llega con ~2-3 días de atraso.
- Seguidores: contenido/seguidores.json, una foto por día que guarda este script (Publer para TikTok, Instagram y
  Facebook; YouTube Data API para suscriptores). Antes del 12-nov solo hay el dato semanal de Publer.
- Por publicación: contenido/metricas.json (última medición) + hora de salida de plan.json / carruseles.json.
- Gasto: Replicate (predicciones de los últimos 35 días, por día y modelo) + autorizaciones de config.json.
- Créditos: contenido/creditos.json (Everygen, OpenArt, Higgsfield) + saldo estimado de Replicate.
Con pocas publicaciones (≈25 medidas al 12-nov) los "mejores días/horas/temas" son señal débil: cada cifra lleva su n.
"""
import datetime
import json
import os
import statistics
import sys
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CDMX = ZoneInfo('America/Mexico_City')
REDES = ('tt', 'yt', 'ig', 'fb')
DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
AHORA = datetime.datetime.now(datetime.timezone.utc)

# Temas: palabras en el tema o el título → grupo que Rodrigo reconoce.
TEMAS = [
    ('Aguinaldo', ('aguinaldo',)),
    ('Buen Fin', ('buen_fin', 'buen fin', 'buenfin', 'ofertas')),
    ('Tarjeta y deudas', ('tarjeta', 'meses sin intereses', 'deuda', 'buro', 'buró', 'credito', 'crédito')),
    ('Sueldo y salario mínimo', ('salario', 'sueldo', 'nomina', 'nómina', 'quincena', 'alcanza')),
    ('Derechos laborales', ('finiquito', 'liquidacion', 'liquidación', 'vacaciones', 'te corren')),
    ('Afore y retiro', ('afore', 'retiro', 'pension', 'pensión')),
    ('Bancos y ahorro', ('banco', 'ipab', 'ahorro', 'cetes', 'inversion', 'inversión')),
    ('Gastos y hábitos', ('gastos', 'hormiga', 'habitos', 'hábitos', 'pareja', 'mitad', 'presupuesto')),
    ('Negocio y mentalidad', ('negocio', 'pareto', 'netflix', 'blockbuster', 'reglas', '1%', 'motivacion', 'motivación', 'lecciones')),
]


def leer(ruta, defecto):
    try:
        return json.load(open(os.path.join(RAIZ, ruta)))
    except (OSError, ValueError):
        return defecto


def utc(t):
    return datetime.datetime.fromisoformat(t.replace('Z', '+00:00'))


def tema_de(*textos):
    t = ' '.join(str(x or '') for x in textos).lower()
    return next((nombre for nombre, claves in TEMAS if any(k in t for k in claves)), 'Otros')


def mediana(xs):
    return round(statistics.median(xs)) if xs else None


def promedio(xs):
    return round(sum(xs) / len(xs)) if xs else None


# ---------- vistas por día ----------
def vistas_por_dia(estado):
    serie = estado.get('serie_redes') or []
    filas = []
    for i in range(1, len(serie)):
        d, a = serie[i], serie[i - 1]
        fila = {'fecha': d['fecha']}
        for r in REDES:
            if d.get(r) is not None:
                fila[r] = max(0, d[r] - (a.get(r) or 0))
        fila['total'] = sum(fila.get(r, 0) for r in REDES)
        filas.append(fila)
    pubs = {x['fecha']: x['v'] for x in estado.get('serie_publicaciones') or []}
    prev = 0
    for f in filas:  # cuántas publicaciones nuevas salieron ese día (serie_publicaciones es acumulada)
        acum = pubs.get(f['fecha'])
        if acum is not None:
            f['publicaciones'] = max(0, acum - prev) if prev else None
            prev = acum
    return filas


# ---------- YouTube Analytics ----------
def youtube_analytics():
    import youtube
    acceso = youtube.token()
    hoy = datetime.date.today()
    base = f"https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==MINE&startDate={(hoy - datetime.timedelta(days=45)).isoformat()}&endDate={hoy.isoformat()}"

    def reporte(extra):
        _, cuerpo = youtube._http('GET', base + extra, headers={'Authorization': f'Bearer {acceso}'})
        return json.loads(cuerpo).get('rows') or []

    dias = [{'fecha': r[0], 'vistas': r[1], 'subs_ganados': r[2], 'subs_perdidos': r[3], 'minutos': r[4],
             'likes': max(0, r[5]), 'comentarios': r[6], 'compartidos': r[7]}
            for r in reporte('&metrics=views,subscribersGained,subscribersLost,estimatedMinutesWatched,likes,comments,shares&dimensions=day&sort=day')]
    nombres = {'SHORTS': 'Feed de Shorts', 'YT_SEARCH': 'Búsqueda de YouTube', 'YT_CHANNEL': 'Tu canal', 'SUBSCRIBER': 'Suscriptores',
               'NOTIFICATION': 'Notificaciones', 'PLAYLIST': 'Listas', 'RELATED_VIDEO': 'Videos sugeridos', 'EXT_URL': 'Enlaces externos',
               'YT_OTHER_PAGE': 'Otras páginas de YouTube', 'BROWSE': 'Inicio', 'NO_LINK_OTHER': 'Directo u otro'}
    fuentes = [{'fuente': nombres.get(r[0], r[0].title()), 'vistas': r[1]} for r in reporte('&metrics=views&dimensions=insightTrafficSourceType&sort=-views') if r[1]]
    try:
        paises = [{'pais': r[0], 'vistas': r[1]} for r in reporte('&metrics=views&dimensions=country&sort=-views&maxResults=6')]
    except SystemExit:
        paises = []
    try:
        edades = [{'edad': r[0].replace('age', '').replace('-', '–'), 'genero': r[1], 'pct': round(r[2], 1)}
                  for r in reporte('&metrics=viewerPercentage&dimensions=ageGroup,gender&sort=ageGroup')]
    except SystemExit:
        edades = []
    return {'dias': dias, 'fuentes': fuentes, 'paises': paises, 'edades': edades,
            'nota': 'YouTube Analytics llega con 2-3 días de atraso.'}


# ---------- seguidores ----------
def seguidores_hoy():
    """Foto de hoy: TikTok, Instagram y Facebook (Publer) y YouTube (Data API). Se guarda en contenido/seguidores.json."""
    hoy = AHORA.astimezone(CDMX).date().isoformat()
    foto, semanal = {}, {}
    try:
        import publer
        ws = publer.workspace_id()
        desde = (AHORA - datetime.timedelta(days=60)).date().isoformat()
        for id_, red in (publer.CONFIG.get('cuentas_publer') or {}).items():
            corto = {'instagram': 'ig', 'tiktok': 'tt', 'facebook': 'fb'}.get(red)
            if not corto:
                continue
            try:
                r = publer._pedir('GET', f'/analytics/{id_}/chart_data?chart_ids[]=followers&from={desde}&to={hoy}', ws)
                serie = (r.get('current') or {}).get('followers') or []
                if serie and serie[-1].get('last_value') is not None:
                    foto[corto] = serie[-1]['last_value']
                    semanal[corto] = [{'semana': x['date'], 'valor': x['last_value']} for x in serie if x.get('last_value') is not None]
            except SystemExit as e:
                print('seguidores', red, e)
    except Exception as e:  # sin llave: no rompe
        print('publer:', e)
    try:
        import youtube
        acceso = youtube.token()
        _, cuerpo = youtube._http('GET', f'{youtube.API}/channels?part=statistics&mine=true', headers={'Authorization': f'Bearer {acceso}'})
        est = json.loads(cuerpo)['items'][0]['statistics']
        foto['yt'] = int(est['subscriberCount'])
        foto['yt_vistas_canal'] = int(est.get('viewCount', 0))
        foto['yt_videos'] = int(est.get('videoCount', 0))
    except Exception as e:
        print('youtube:', e)
    ruta = os.path.join(RAIZ, 'contenido', 'seguidores.json')
    log = leer('contenido/seguidores.json', [])
    if any(r in foto for r in REDES):
        log = [x for x in log if x['fecha'] != hoy] + [{'fecha': hoy, **foto}]
        log.sort(key=lambda x: x['fecha'])
        json.dump(log, open(ruta, 'w'), ensure_ascii=False, indent=1)
    diario = []
    for i, x in enumerate(log):
        fila = {'fecha': x['fecha'], **{r: x.get(r) for r in REDES}}
        if i:
            a = log[i - 1]
            fila['ganados'] = {r: x[r] - a[r] for r in REDES if x.get(r) is not None and a.get(r) is not None}
        diario.append(fila)
    return {'actual': {r: (log[-1].get(r) if log else None) for r in REDES}, 'diario': diario, 'semanal': semanal,
            'nota': 'Diario desde el 12-nov-2026 (foto propia de cada día). Antes, solo el dato semanal de Publer. YouTube diario sale de YouTube Analytics.'}


# ---------- publicaciones ----------
def publicaciones():
    plan = leer('contenido/plan.json', {'videos': []})
    cs = leer('contenido/carruseles.json', [])
    cs = cs if isinstance(cs, list) else cs.get('carruseles', [])
    info = {}
    for v in plan['videos']:
        info[v['id']] = {'formato': 'Victoria hablando', 'titulo': (v.get('seo') or {}).get('titulo') or v.get('texto_pantalla') or v['id'],
                         'tema': tema_de(v.get('tema'), v.get('pilar'), (v.get('seo') or {}).get('titulo'), v.get('texto_pantalla')),
                         'por_red': v.get('publica_utc_por_red') or ({r: v['publica_utc'] for r in REDES} if v.get('publica_utc') else {})}
    for c in cs:
        info[c['id']] = {'formato': 'Carrusel', 'titulo': (c.get('seo') or {}).get('titulo') or c.get('titulo_post') or c['id'],
                         'tema': tema_de(c.get('tema'), (c.get('portada') or {}).get('titulo'), (c.get('seo') or {}).get('titulo')),
                         'por_red': c.get('publica_utc_por_red') or {}}
    historial = sorted(leer('contenido/metricas.json', []), key=lambda f: f['fecha_utc'])
    ultima = {}
    for f in historial:
        ultima[f['video_id']] = f
    filas = []
    for vid, f in ultima.items():
        i = info.get(vid)
        if not i:
            continue
        redes = {}
        for r in REDES:
            m = dict(f.get(r) or {})
            if r == 'ig' and f.get('igr'):  # el Reel del carrusel cuenta en Instagram
                for k in ('v', 'l', 'c', 's'):
                    m[k] = (m.get(k) or 0) + (f['igr'].get(k) or 0)
            if not m:
                continue
            sale = i['por_red'].get(r) or (i['por_red'].get('ig') if r == 'fb' else None)
            local = utc(sale).astimezone(CDMX) if sale else None
            horas = m.get('h') or ((utc(f['fecha_utc']) - utc(sale)).total_seconds() / 3600 if sale else None)
            redes[r] = {'v': m.get('v', 0) or 0, 'l': m.get('l', 0) or 0, 'c': m.get('c', 0) or 0, 's': m.get('s', 0) or 0,
                        'dia': DIAS[local.weekday()] if local else None, 'hora': local.hour if local else None,
                        'horas': round(horas, 1) if horas is not None else None}
        if not redes:
            continue
        total = sum(x['v'] for x in redes.values())
        inter = sum(x['l'] + x['c'] + x['s'] for x in redes.values())
        filas.append({'id': vid, 'formato': i['formato'], 'tema': i['tema'], 'titulo': str(i['titulo'])[:70], 'redes': redes,
                      'total': total, 'interaccion': round(inter / total * 100, 2) if total else 0})
    return sorted(filas, key=lambda x: -x['total'])


def agrupar(pubs, clave, red=None, minimo_h=24):
    """Vistas por publicación agrupadas (solo las que llevan ≥ 24 h en esa red: las nuevas bajarían el promedio)."""
    grupos = {}
    for p in pubs:
        for r, m in p['redes'].items():
            if red and r != red:
                continue
            if m['horas'] is not None and m['horas'] < minimo_h:
                continue
            k = clave(p, r, m)
            if k is None:
                continue
            grupos.setdefault(k, []).append(m['v'])
    return {k: {'n': len(v), 'mediana': mediana(v), 'promedio': promedio(v), 'total': sum(v)} for k, v in grupos.items()}


def mejores(pubs):
    salida = {'por_red': {}}
    for r in REDES:
        dias = agrupar(pubs, lambda p, rr, m: m['dia'], r)
        horas = agrupar(pubs, lambda p, rr, m: m['hora'], r)
        salida['por_red'][r] = {
            'dias': [{'dia': d, **dias[d]} for d in DIAS if d in dias],
            'horas': [{'hora': h, **horas[h]} for h in sorted(horas)],
        }
    temas = agrupar(pubs, lambda p, r, m: p['tema'])
    salida['temas'] = sorted(({'tema': k, **v} for k, v in temas.items()), key=lambda x: -(x['mediana'] or 0))
    formatos = {}
    for r in REDES:
        for k, v in agrupar(pubs, lambda p, rr, m: p['formato'], r).items():
            formatos.setdefault(k, {})[r] = v
    salida['formatos'] = formatos
    return salida


# ---------- gasto ----------
def gasto():
    rep = leer('contenido/replicate.json', {})
    conf = (leer('contenido/config.json', {}).get('replicate') or {})
    por_dia, por_modelo, por_modelo_mes = {}, {}, {}
    try:
        if os.environ.get('REPLICATE_API_TOKEN'):
            import replicate_gasto as rg
            nuestros = set(open(rg.IDS).read().split()) if os.path.exists(rg.IDS) else set()
            desde = (AHORA - datetime.timedelta(days=35)).strftime('%Y-%m-%dT%H:%M:%SZ')
            mes0 = AHORA.astimezone(CDMX).replace(day=1).date().isoformat()
            for p in rg.predicciones_desde(desde):
                if p.get('status') != 'succeeded' or not rg.PRECIOS.get(p.get('model')):
                    continue
                costo = rg.PRECIOS[p['model']](p)
                quien = 'victoria' if p['id'] in nuestros else 'otro'
                dia = utc(p['created_at']).astimezone(CDMX).date().isoformat()
                fila = por_dia.setdefault(dia, {'victoria': 0.0, 'otro': 0.0})
                fila[quien] += costo
                if quien == 'victoria':
                    por_modelo[p['model']] = por_modelo.get(p['model'], 0) + costo
                    if dia >= mes0:
                        por_modelo_mes[p['model']] = por_modelo_mes.get(p['model'], 0) + costo
    except Exception as e:
        print('replicate:', e)
    nombres = {'prunaai/p-video-avatar': 'Victoria hablando (p-video-avatar)', 'bytedance/seedance-1-pro': 'Escenas con movimiento (Seedance)',
               'google/nano-banana': 'Fotos (Nano Banana)', 'zsxkib/mmaudio': 'Sonido real (MMAudio)', 'minimax/speech-02-hd': 'Voz (MiniMax)',
               'minimax/video-01': 'Video (MiniMax)', 'minimax/voice-cloning': 'Clonar voz (MiniMax)'}
    return {
        'por_dia': [{'fecha': d, **{k: round(v, 2) for k, v in x.items()}} for d, x in sorted(por_dia.items())],
        'por_modelo_mes': sorted(({'modelo': nombres.get(k, k), 'usd': round(v, 2)} for k, v in por_modelo_mes.items()), key=lambda x: -x['usd']),
        'control': rep.get('control'),
        'saldo_estimado_usd': rep.get('saldo_estimado_usd'),
        'recarga': conf.get('recarga'),
        'autorizaciones': [{'clave': k, 'para': a.get('para', ''), 'tope_usd': a.get('tope_usd', 0), 'gastado_usd': round(a.get('gastado_usd', 0), 2),
                            'cerrada': bool(a.get('cerrada'))} for k, a in (conf.get('autorizaciones') or {}).items()],
    }


# ---------- comparativas ----------
def semana_vs_semana(dias):
    if not dias:
        return {}
    ult = dias[-1]['fecha']
    hoy = datetime.date.fromisoformat(ult)
    rango = lambda a, b: [d for d in dias if (hoy - datetime.timedelta(days=b)).isoformat() < d['fecha'] <= (hoy - datetime.timedelta(days=a)).isoformat()]
    esta, antes = rango(0, 7), rango(7, 14)
    salida = {}
    for r in REDES + ('total',):
        a, b = sum(d.get(r) or 0 for d in esta), sum(d.get(r) or 0 for d in antes)
        salida[r] = {'esta': a, 'anterior': b, 'cambio_pct': round((a - b) / b * 100) if b else None}
    return salida


def main():
    estado = (leer('centro/datos/estado.json', [{}]) or [{}])[0]
    dias = vistas_por_dia(estado)
    try:
        yt = youtube_analytics()
    except Exception as e:
        print('youtube analytics:', e)
        yt = None
    pubs = publicaciones()
    creditos = leer('contenido/creditos.json', {}).get('apps') or {}
    salida = {
        'generado_utc': AHORA.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'vistas_dia': dias,
        'semana_vs_semana': semana_vs_semana(dias),
        'youtube': yt,
        'seguidores': seguidores_hoy(),
        'publicaciones': pubs,
        'mejores': mejores(pubs),
        'gasto': gasto(),
        'creditos': [{'clave': k, 'nombre': a.get('nombre', k), 'plan': a.get('plan'), 'creditos': a.get('creditos'),
                      'mensual': a.get('mensual'), 'regla': a.get('regla'), 'uso': a.get('uso')} for k, a in creditos.items()],
        'mejores_horas_estudio': leer('centro/datos/mejores_horas.json', []),
        'totales': {
            'vistas': sum(d['total'] for d in dias) + sum((estado.get('serie_redes') or [{}])[0].get(r) or 0 for r in REDES),
            'publicaciones_medidas': len(pubs),
            'mediana_por_publicacion': mediana([p['total'] for p in pubs]),
            'interaccion_mediana_pct': round(statistics.median([p['interaccion'] for p in pubs]), 2) if pubs else None,
        },
    }
    json.dump(salida, open(os.path.join(RAIZ, 'centro', 'datos', 'estadisticas.json'), 'w'), ensure_ascii=False)
    print('estadisticas.json:', len(dias), 'días ·', len(pubs), 'publicaciones ·',
          'YouTube', 'sí' if yt else 'no', '· seguidores', salida['seguidores']['actual'])


if __name__ == '__main__':
    main()
