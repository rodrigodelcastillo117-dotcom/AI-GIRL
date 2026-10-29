"""Cerebro de Victoria: mide cada video, compara qué funciona y elige el siguiente.

Uso:
  python aprender.py medir     Guarda en contenido/metricas.json una foto de vistas, likes,
                               comentarios y compartidos de cada video publicado (Publer para
                               TikTok/Instagram, API de YouTube para Shorts).
  python aprender.py auditar   Califica cada video por sus vistas a ~36 h de publicado contra la
                               mediana del canal (índice 1.0 = normal), compara tema, fondo,
                               vestimenta, color, gancho, día y hora, y elige el siguiente video.
                               Escribe contenido/auditoria.json y un resumen en pantalla.

Reglas para no engañarse con pocos datos: un valor (por ejemplo "jet") solo gana o pierde con al
menos MIN_MUESTRAS videos; mientras tanto está "en prueba". De cada 10 días, 3 se usan para
explorar (probar lo menos probado) y 7 para aprovechar lo que mejor funciona.
"""
import datetime
import json
import os
import statistics
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CONTENIDO = os.path.join(RAIZ, 'contenido')
CDMX = datetime.timezone(datetime.timedelta(hours=-6))
DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
REDES = {'instagram': 'ig', 'tiktok': 'tt'}
MIN_MUESTRAS = 3
HORAS_CALIFICACION = 36   # se califica con la foto más cercana a 36 h (entre 20 y 60 h)
DIAS_DE_MEDICION = 14     # después de 14 días ya no se guardan fotos de ese video

FONDOS = {'jet': 'transporte', 'yate': 'transporte', 'coche': 'transporte',
          'recamara': 'casa', 'cocina': 'casa', 'sala': 'casa', 'sillon': 'casa',
          'oficina': 'negocios', 'hotel': 'negocios', 'palco_estadio': 'negocios',
          'restaurante': 'ocio', 'bar': 'ocio', 'jacuzzi': 'ocio', 'gimnasio': 'ocio', 'golf': 'ocio'}
ESTILOS = [('playa', ['traje de baño', 'bikini']), ('deportivo', ['deportivo', 'leggings', 'polo', 'visera']),
           ('casa', ['pijama']), ('noche', ['noche', 'cóctel', 'coctel', 'gala', 'terciopelo', 'satín']),
           ('ejecutivo', ['blazer', 'sastre', 'falda lápiz']), ('casual', ['suéter', 'jeans', 'lino', 'punto', 'camisero'])]
COLORES = {'blanco': 'claro', 'blanca': 'claro', 'marfil': 'claro', 'crema': 'claro', 'champaña': 'claro', 'beige': 'claro',
           'negro': 'negro', 'negra': 'negro', 'rojo': 'rojo', 'carmesí': 'rojo', 'vino': 'rojo', 'azul': 'azul',
           'verde': 'verde', 'camel': 'café', 'café': 'café', 'gris': 'gris', 'dorado': 'dorado', 'rosa': 'rosa'}
NOMBRES = {'pilar': 'El tema', 'tipo_fondo': 'El tipo de fondo', 'locacion': 'El fondo', 'estilo_vestuario': 'La vestimenta',
           'color_vestuario': 'El color de ropa', 'tipo_gancho': 'El gancho', 'dia': 'El día', 'hora': 'La hora'}
NUMEROS = ['uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'veinte', 'treinta',
           'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa', 'cien', 'mil', 'por ciento']


def cargar(nombre, defecto):
    try:
        return json.load(open(os.path.join(CONTENIDO, nombre)))
    except (OSError, ValueError):
        return defecto


def guardar(nombre, datos):
    json.dump(datos, open(os.path.join(CONTENIDO, nombre), 'w'), ensure_ascii=False, indent=1)


def primera_linea(texto):
    lineas = (texto or '').strip().splitlines()
    return ' '.join(lineas[0].split()).lower() if lineas else ''


def a_utc(texto):
    return datetime.datetime.fromisoformat(texto.replace('Z', '+00:00')).astimezone(datetime.timezone.utc)


def adn(video):
    """Las características que se comparan. Si el video trae "adn" en el plan, manda ese."""
    vestuario = (video.get('vestuario') or '').lower()
    gancho = (video.get('guion') or '').split('.')[0].lower()
    color = min(((vestuario.find(p), c) for p, c in COLORES.items() if p in vestuario), default=(0, 'otro'))[1]
    estilo = next((e for e, claves in ESTILOS if any(c in vestuario for c in claves)), 'otro')
    if gancho.startswith('¿'):
        tipo = 'pregunta'
    elif any(p in gancho for p in ('decía', 'lo llama', 'escribió', 'dijo')):
        tipo = 'cita'
    elif any(p in gancho for p in ('estudio', 'ley ', 'efecto', 'principio')):
        tipo = 'dato'
    elif 'regla' in gancho:
        tipo = 'regla'
    elif any(ch.isdigit() for ch in gancho) or any(f' {n} ' in f' {gancho} ' for n in NUMEROS):
        tipo = 'numero'
    else:
        tipo = 'consejo'
    datos = {'pilar': video.get('pilar'), 'locacion': video.get('locacion'),
             'tipo_fondo': FONDOS.get(video.get('locacion'), 'otro'), 'estilo_vestuario': estilo,
             'color_vestuario': color, 'tipo_gancho': tipo}
    if video.get('publica_utc'):
        local = a_utc(video['publica_utc']).astimezone(CDMX)
        datos.update(dia=DIAS[local.weekday()], hora=local.strftime('%H:%M'))
    datos.update(video.get('adn') or {})
    return datos


# ---------- medir ----------

def medir_publer(videos):
    import publer
    ws = publer.workspace_id()
    cuentas = publer.CONFIG.get('cuentas_publer', {})
    por_linea = {primera_linea(v.get('texto_post')): v['id'] for v in videos}
    por_minuto = {v['publica_utc'][:16]: v['id'] for v in videos if v.get('publica_utc')}
    hoy = datetime.date.today()
    datos = {}
    for pagina in range(20):
        r = publer._pedir('GET', f'/analytics/post_insights?from={(hoy - datetime.timedelta(days=60)).isoformat()}'
                                 f'&to={hoy.isoformat()}&page={pagina}', ws)
        lote = r.get('posts') or []
        for p in lote:
            red = REDES.get(cuentas.get(p.get('account_id')))
            if not red:
                continue
            minuto = a_utc(p['scheduled_at']).strftime('%Y-%m-%dT%H:%M') if p.get('scheduled_at') else ''
            video = por_linea.get(primera_linea(p.get('text'))) or por_minuto.get(minuto)
            if not video:
                continue
            a = p.get('analytics') or {}
            destino = datos.setdefault(video, {}).setdefault(red, {'v': 0, 'l': 0, 'c': 0, 's': 0})
            for corto, campo in (('v', 'video_views'), ('l', 'likes'), ('c', 'comments'), ('s', 'shares')):
                destino[corto] += int(a.get(campo) or 0)
        if len(lote) < 10:
            break
    return datos


def medir_youtube(videos):
    import youtube
    ids = {(v.get('publicacion') or {}).get('youtube', '').rstrip('/').split('/')[-1]: v['id'] for v in videos}
    ids.pop('', None)
    if not ids:
        return {}
    acceso = youtube.token()
    _, cuerpo = youtube._http('GET', f"{youtube.API}/videos?part=statistics&id={','.join(list(ids)[:50])}",
                              headers={'Authorization': f'Bearer {acceso}'})
    datos = {}
    for item in json.loads(cuerpo).get('items') or []:
        s = item['statistics']
        datos[ids[item['id']]] = {'yt': {'v': int(s.get('viewCount', 0)), 'l': int(s.get('likeCount', 0)),
                                         'c': int(s.get('commentCount', 0)), 's': 0}}
    return datos


def medir():
    plan = cargar('plan.json', {'videos': []})
    ahora = datetime.datetime.now(datetime.timezone.utc)
    videos = [v for v in plan['videos'] if v.get('publica_utc') and a_utc(v['publica_utc']) <= ahora
              and (ahora - a_utc(v['publica_utc'])).days <= DIAS_DE_MEDICION]
    if not videos:
        print('medir: todavía no hay videos publicados que medir')
        return
    juntos, avisos = {}, []
    for nombre, funcion in (('Publer', medir_publer), ('YouTube', medir_youtube)):
        try:
            for vid, redes in funcion(videos).items():
                juntos.setdefault(vid, {}).update(redes)
        except SystemExit as e:  # los scripts de Publer y YouTube salen con SystemExit si algo falla
            avisos.append(f'{nombre}: {e}')
    historial = cargar('metricas.json', [])
    for v in videos:
        horas = round((ahora - a_utc(v['publica_utc'])).total_seconds() / 3600, 1)
        historial.append({'fecha_utc': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'), 'video_id': v['id'], 'horas': horas,
                          **juntos.get(v['id'], {})})
    guardar('metricas.json', historial)
    for a in avisos:
        print('AVISO medir:', a)
    print(f'medir: {len(videos)} videos medidos')


# ---------- auditar ----------

def total(foto, campo='v'):
    return sum((foto.get(r) or {}).get(campo, 0) for r in ('yt', 'tt', 'ig'))


def calificar(plan, historial):
    """{video_id: {vistas_36h, engagement}} con la foto más cercana a 36 h."""
    notas = {}
    for v in plan['videos']:
        fotos = [f for f in historial if f['video_id'] == v['id'] and 20 <= f['horas'] <= 60]
        if not fotos:
            continue
        foto = min(fotos, key=lambda f: abs(f['horas'] - HORAS_CALIFICACION))
        vistas = total(foto)
        interaccion = total(foto, 'l') + total(foto, 'c') + total(foto, 's')
        notas[v['id']] = {'vistas_36h': vistas, 'engagement': round(interaccion / vistas, 4) if vistas else 0,
                          'horas': foto['horas']}
    return notas


def comparar(plan, notas):
    base = statistics.median([n['vistas_36h'] for n in notas.values()]) if notas else 0
    for n in notas.values():
        n['indice'] = round(n['vistas_36h'] / base, 2) if base else 0
    grupos = {}
    for v in plan['videos']:
        if v['id'] not in notas:
            continue
        for atributo, valor in adn(v).items():
            grupos.setdefault(atributo, {}).setdefault(valor, []).append(notas[v['id']])
    ranking = {}
    for atributo, valores in grupos.items():
        filas = []
        for valor, lista in valores.items():
            indice = round(statistics.mean(x['indice'] for x in lista), 2)
            estado = 'en prueba'
            if len(lista) >= MIN_MUESTRAS:
                estado = 'gana' if indice >= 1.2 else 'pierde' if indice <= 0.8 else 'normal'
            filas.append({'valor': valor, 'n': len(lista), 'indice': indice, 'estado': estado,
                          'engagement': round(statistics.mean(x['engagement'] for x in lista), 4)})
        ranking[atributo] = sorted(filas, key=lambda f: -f['indice'])
    return base, ranking


def decidir(plan, ranking, hoy, config):
    dia = next((f for f in ranking.get('dia', []) if f['valor'] == DIAS[hoy.weekday()]), None)
    if config.get('saltar_dias_que_pierden') and dia and dia['estado'] == 'pierde' and dia['n'] >= MIN_MUESTRAS + 1:
        return {'video_id': None, 'modo': 'saltar', 'esperado': dia['indice'],
                'por_que': f'Los {dia["valor"]} pierden (índice {dia["indice"]} en {dia["n"]} videos): hoy no se publica y se ahorran créditos.',
                'cambios_sugeridos': []}
    pendientes = [v for v in plan['videos'] if v['estado'] == 'pendiente']
    if not pendientes:
        return None
    valores = {a: {f['valor']: f for f in filas} for a, filas in ranking.items()}
    publicados = [v for v in plan['videos'] if v['estado'] in ('programado', 'publicado')]
    ultimo_pilar = publicados[-1]['pilar'] if publicados else None
    explorar = hoy.timetuple().tm_yday % 10 < 3
    candidatos = []
    for orden, v in enumerate(pendientes):
        rasgos = {k: x for k, x in adn(v).items() if k not in ('dia', 'hora')}
        conocidos = [valores.get(a, {}).get(x) for a, x in rasgos.items()]
        firmes = [c['indice'] for c in conocidos if c and c['n'] >= MIN_MUESTRAS]
        esperado = statistics.mean(firmes) if firmes else 1.0
        if v['pilar'] == ultimo_pilar:
            esperado *= 0.9  # no repetir tema dos días seguidos sin razón
        nuevos = sum(1 for c in conocidos if not c or c['n'] < MIN_MUESTRAS)
        candidatos.append((v, round(esperado, 2), nuevos, orden))
    if explorar:
        v, esperado, nuevos, _ = max(candidatos, key=lambda c: (c[2], -c[3]))
        por_que = f'Día de exploración: el video {v["id"]} prueba {nuevos} características con pocos datos.'
    else:
        v, esperado, nuevos, _ = max(candidatos, key=lambda c: (c[1], -c[3]))
        por_que = f'Día de aprovechar: el video {v["id"]} tiene el mejor índice esperado ({esperado}).'
    cambios = []
    rasgos = adn(v)
    for atributo in ('tipo_fondo', 'locacion', 'estilo_vestuario', 'tipo_gancho'):
        actual = valores.get(atributo, {}).get(rasgos[atributo])
        mejor = next((f for f in ranking.get(atributo, []) if f['estado'] == 'gana'), None)
        if actual and actual['estado'] == 'pierde' and mejor:
            cambios.append({'atributo': atributo, 'de': rasgos[atributo], 'a': mejor['valor'],
                            'por_que': f'{rasgos[atributo]} promedia {actual["indice"]} y {mejor["valor"]} {mejor["indice"]}'})
    return {'video_id': v['id'], 'modo': 'explorar' if explorar else 'aprovechar', 'esperado': esperado,
            'por_que': por_que, 'cambios_sugeridos': cambios}


def alertas(plan, ranking, notas, ejecuciones, config):
    lista = []
    medidos = len(notas)
    if medidos < 6:
        lista.append(f'{medidos} videos calificados. Con 6 o más ya se ven tendencias; antes de eso todo está "en prueba".')
    for atributo, nombre in NOMBRES.items():
        for f in ranking.get(atributo, []):
            if f['estado'] in ('gana', 'pierde'):
                lista.append(f'{nombre} "{f["valor"]}" {f["estado"]}: índice {f["indice"]} en {f["n"]} videos.')
    pendientes = sum(1 for v in plan['videos'] if v['estado'] == 'pendiente')
    if pendientes < 5:
        lista.append(f'Quedan {pendientes} guiones: hay que escribir 10 nuevos hoy (paso 1c).')
    orden = sorted(ejecuciones, key=lambda e: e['fecha_utc'])
    if orden:
        generados = [e for e in orden if e['tipo'] == 'generar' and e.get('creditos_usados')]
        costo = statistics.mean(e['creditos_usados'] for e in generados) if generados else 540
        alcanzan = int(orden[-1]['creditos_restantes'] // costo)
        if alcanzan < 7:
            lista.append(f'Créditos para {alcanzan} videos: a uno diario se acaban en {alcanzan} días. Recargar OpenArt.')
    fallas = [e for e in orden[-5:] if e['resultado'] == 'fallido']
    if len(fallas) >= 2:
        lista.append(f'{len(fallas)} de las últimas 5 ejecuciones fallaron: revisar antes de gastar más créditos.')
    for vid, n in notas.items():
        if n['vistas_36h'] == 0:
            lista.append(f'El video {vid} tiene 0 vistas a {n["horas"]} h: revisar que sí se haya publicado.')
    return lista


def auditar():
    plan = cargar('plan.json', {'videos': []})
    historial = cargar('metricas.json', [])
    ejecuciones = cargar('ejecuciones.json', [])
    config = cargar('config.json', {})
    hoy = datetime.datetime.now(CDMX).date()
    notas = calificar(plan, historial)
    base, ranking = comparar(plan, notas)
    resultado = {
        'fecha_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'videos_calificados': len(notas),
        'base_vistas_36h': base,
        'notas': {vid: n for vid, n in sorted(notas.items())},
        'ranking': ranking,
        'decision': decidir(plan, ranking, hoy, config),
        'alertas': alertas(plan, ranking, notas, ejecuciones, config),
    }
    guardar('auditoria.json', resultado)
    print(f"Auditoría: {len(notas)} videos calificados, base {base} vistas a 36 h.")
    for atributo, filas in ranking.items():
        print(f'  {atributo}: ' + ', '.join(f"{f['valor']} {f['indice']} ({f['n']}, {f['estado']})" for f in filas))
    d = resultado['decision']
    print('Decisión:', d['por_que'] if d else 'no hay guiones pendientes')
    for c in (d or {}).get('cambios_sugeridos', []):
        print(f"  Cambiar {c['atributo']}: {c['de']} → {c['a']} ({c['por_que']})")
    for a in resultado['alertas']:
        print('Alerta:', a)


if __name__ == '__main__':
    {'medir': medir, 'auditar': auditar}.get(sys.argv[1] if len(sys.argv) > 1 else '', lambda: sys.exit(__doc__))()
