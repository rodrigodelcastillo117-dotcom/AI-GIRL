"""Gasto y saldo estimado de Replicate (Rodrigo, 12-nov-2026: "actualiza el dashboard para replicate. tenemos 30.68 usd.
también lo va a usar mi canal de El espacio").

Uso: python replicate_gasto.py            imprime el resumen y lo guarda en contenido/replicate.json
     python replicate_gasto.py saldo 25.40   Rodrigo dice cuánto marca replicate.com/account/billing: nueva base

Replicate no da el saldo por API (probado: /v1/billing, /balance, /credits = 404). Por eso:
- contenido/config.json → replicate = {"saldo_base_usd", "fecha_base_utc"}: el último saldo que Rodrigo leyó en su cuenta.
- Se listan las predicciones de la cuenta desde esa fecha (GET /v1/predictions) y se estima el costo de cada una con el
  precio de su modelo (PRECIOS). Saldo estimado = saldo base − todo lo gastado desde entonces (Victoria + otros).
- Lo de Victoria: los id que anotan nuestros scripts en contenido/replicate_ids.txt (anotar(id)). Lo demás de la cuenta
  (el canal de El espacio u otro) sale como "otro".
- Modelos sin precio conocido se cuentan aparte ("sin_precio") y el saldo se marca como incompleto.
"""
import datetime
import json
import os
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS = os.path.join(RAIZ, 'contenido', 'replicate_ids.txt')
SALIDA = os.path.join(RAIZ, 'contenido', 'replicate.json')
AGENTE = 'victoria-pipeline/1.0'  # Cloudflare de Replicate rechaza el User-Agent de Python (12-nov-2026)


def _costo_video(p):
    m = p.get('metrics') or {}
    seg = m.get('video_output_duration_seconds') or (m.get('billing') or {}).get('video_output_duration_seconds') or 0
    return seg * (0.045 if '1080' in str(m.get('resolution_target', '1080p')) else 0.025)


# USD. Fuentes: página del modelo en Replicate (p-video-avatar $0.045/s 1080p y $0.025/s 720p; flux-schnell $0.003 por
# imagen). MiniMax speech-02-hd en Replicate cobra por tokens y no publica la tarifa: se estima con lo que cobra MiniMax
# directo, $0.10 por 1,000 caracteres (platform.minimax.io), así que es aproximado.
PRECIOS = {
    'prunaai/p-video-avatar': _costo_video,
    'minimax/speech-02-hd': lambda p: len(str((p.get('input') or {}).get('text', ''))) / 1000 * 0.10,
    'black-forest-labs/flux-schnell': lambda p: 0.003 * max(1, int((p.get('input') or {}).get('num_outputs', 1) or 1)),
}


def anotar(prediccion_id):
    """Lo llaman nuestros scripts al crear una predicción: así se sabe qué gasto es de Victoria."""
    if prediccion_id:
        with open(IDS, 'a') as f:
            f.write(prediccion_id + '\n')


def _pedir(url):
    req = urllib.request.Request(url, headers={'Authorization': f"Bearer {os.environ['REPLICATE_API_TOKEN']}",
                                               'User-Agent': AGENTE})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def predicciones_desde(desde):
    url, todas = 'https://api.replicate.com/v1/predictions', []
    while url:
        pagina = _pedir(url)
        for p in pagina.get('results', []):
            if p.get('created_at', '') < desde:
                return todas
            todas.append(p)
        url = pagina.get('next')
    return todas


def freno(barato=False):
    """Freno duro (Rodrigo, 12-nov-2026: "me llegó otro cargo de Replicate, por favor con cuidado con los gastos").
    Todo script que crea algo en Replicate llama esto antes. Para si config.json → replicate.pausado es true o si el
    gasto de Victoria de la semana o del mes (contenido/replicate.json → control, lo calcula este script) ya llegó al
    presupuesto. No hay excepción automática: para pasar el tope Rodrigo tiene que subir el presupuesto o quitar la pausa."""
    try:
        cfg = (json.load(open(os.path.join(RAIZ, 'contenido', 'config.json'))).get('replicate') or {})
        c = (json.load(open(SALIDA)).get('control') or {}) if os.path.exists(SALIDA) else {}
    except (OSError, ValueError):
        return
    if cfg.get('pausado'):
        sys.exit('FRENO DE REPLICATE: está en pausa (config.json → replicate.pausado). No se generó nada.')
    sem, tope_s = c.get('semana_usd') or 0, cfg.get('presupuesto_semanal_usd')
    mes, tope_m = c.get('mes_usd') or 0, cfg.get('presupuesto_mensual_usd')
    # barato=True (voz de Victoria, imágenes de fondo: centavos) solo se frena en el tope del MES; lo caro (videos de
    # Victoria hablando, ~$0.045 por segundo) en el de la semana o el del mes.
    if (not barato and tope_s and sem >= tope_s) or (tope_m and mes >= tope_m):
        sys.exit(f'FRENO DE REPLICATE: Victoria ya gastó ${sem:.2f} esta semana (tope ${tope_s}) y ${mes:.2f} este mes '
                 f'(tope ${tope_m}). No se generó nada; avísale a Rodrigo.')


def resumen():
    config = json.load(open(os.path.join(RAIZ, 'contenido', 'config.json')))
    base = config.get('replicate') or {}
    desde_base = base.get('fecha_base_utc', '2026-11-12T00:00:00Z')
    # Control de gasto (Rodrigo, 12-nov-2026: "se recarga solo cuando llega a 5 usd… solo te pido control para no
    # sorprenderme con el gasto"): hoy, semana (lunes a domingo) y mes, en hora de México, contra el presupuesto.
    from zoneinfo import ZoneInfo
    mx = datetime.datetime.now(ZoneInfo('America/Mexico_City'))
    lunes = (mx - datetime.timedelta(days=mx.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    dia1 = mx.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    utc = lambda d: d.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    hoy0 = utc(mx.replace(hour=0, minute=0, second=0, microsecond=0))
    lunes0, mes0 = utc(lunes), utc(dia1)
    desde = min(desde_base, lunes0, mes0)
    periodos = {'hoy': {'victoria': 0.0, 'otro': 0.0}, 'semana': {'victoria': 0.0, 'otro': 0.0}, 'mes': {'victoria': 0.0, 'otro': 0.0}}
    nuestros = set(open(IDS).read().split()) if os.path.exists(IDS) else set()
    hace7 = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    total = {'victoria': 0.0, 'otro': 0.0}
    semana = {'victoria': 0.0, 'otro': 0.0}
    por_dia, por_modelo, sin_precio = {}, {}, {}
    videos = []
    for p in predicciones_desde(desde):
        if p.get('status') != 'succeeded':
            continue
        quien = 'victoria' if p['id'] in nuestros else 'otro'
        precio = PRECIOS.get(p.get('model'))
        if not precio:
            sin_precio[p.get('model')] = sin_precio.get(p.get('model'), 0) + 1
            continue
        costo = precio(p)
        for nombre, inicio in (('hoy', hoy0), ('semana', lunes0), ('mes', mes0)):
            if p['created_at'] >= inicio:
                periodos[nombre][quien] += costo
        if p['created_at'] < desde_base:
            continue
        total[quien] += costo
        if p['created_at'] >= hace7:
            semana[quien] += costo
        dia = p['created_at'][:10]
        por_dia.setdefault(dia, {'victoria': 0.0, 'otro': 0.0})[quien] += costo
        por_modelo[p['model']] = por_modelo.get(p['model'], 0.0) + costo
        if p.get('model') == 'prunaai/p-video-avatar' and quien == 'victoria':
            videos.append(costo)
    saldo_base = base.get('saldo_base_usd')
    import calendar
    dias_mes = calendar.monthrange(mx.year, mx.month)[1]
    pres_sem, pres_mes = base.get('presupuesto_semanal_usd'), base.get('presupuesto_mensual_usd')
    control = {
        'hoy_usd': round(periodos['hoy']['victoria'], 2),
        'semana_usd': round(periodos['semana']['victoria'], 2),
        'mes_usd': round(periodos['mes']['victoria'], 2),
        'otro_canal_semana_usd': round(periodos['semana']['otro'], 2),
        'otro_canal_mes_usd': round(periodos['mes']['otro'], 2),
        'presupuesto_semanal_usd': pres_sem, 'presupuesto_mensual_usd': pres_mes,
        'presupuesto_otro_canal_mensual_usd': base.get('presupuesto_otro_canal_mensual_usd'),
        'proyeccion_mes_usd': round(periodos['mes']['victoria'] / mx.day * dias_mes, 2),
        'semana_desde': lunes.strftime('%Y-%m-%d'),
        'recarga_automatica': base.get('recarga_automatica'),
    }
    datos = {
        'control': control,
        'saldo_base_usd': saldo_base, 'fecha_base_utc': desde_base,
        'saldo_estimado_usd': round(saldo_base - total['victoria'] - total['otro'], 2) if saldo_base is not None else None,
        'gastado_desde_base': {k: round(v, 2) for k, v in total.items()},
        'gastado_7_dias': {k: round(v, 2) for k, v in semana.items()},
        'por_dia': [{'dia': d, **{k: round(v, 2) for k, v in x.items()}} for d, x in sorted(por_dia.items())],
        'por_modelo': {k: round(v, 2) for k, v in sorted(por_modelo.items(), key=lambda kv: -kv[1])},
        'costo_promedio_toma_usd': round(sum(videos) / len(videos), 2) if videos else None,
        'sin_precio': sin_precio,
        'incompleto': bool(sin_precio),
        'generado_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'nota': 'Estimado: Replicate no da el saldo por API. Confirmar en replicate.com/account/billing.',
    }
    json.dump(datos, open(SALIDA, 'w'), ensure_ascii=False, indent=1)
    return datos


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'saldo':
        ruta = os.path.join(RAIZ, 'contenido', 'config.json')
        config = json.load(open(ruta))
        config.setdefault('replicate', {}).update({'saldo_base_usd': float(sys.argv[2]),
                               'fecha_base_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')})
        open(ruta, 'w').write(json.dumps(config, ensure_ascii=False, indent=1) + '\n')
        print('nueva base:', config['replicate'])
    print(json.dumps(resumen(), ensure_ascii=False, indent=1))
