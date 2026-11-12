"""Chequeo diario de que TODO fluye (Rodrigo, 12-nov-2026: "déjame todo fluyendo, sin errores, y usando todo").

Uso: python scripts/salud.py            imprime el reporte y escribe contenido/salud.json (lo lee el panel)
     python scripts/salud.py --sin-red  sin probar las llaves contra cada servicio (más rápido)

Revisa, sin imprimir nunca una clave:
  1. Llaves: YouTube, Publer, Replicate y Meta (Instagram y Facebook) responden.
  2. Saldo estimado de Replicate (contenido/replicate.json): menos de $10 no alcanza para un video largo.
  3. Calendario de los próximos 3 días por red contra config.json → publicaciones_por_dia (huecos).
  4. Videos largos que salen en 3 días o menos y no están subidos; largos subidos sin recortes;
     recortes listos sin horario; cosas cuya hora ya pasó y no quedaron programadas.
  5. Cola: carruseles listos (días de TikTok que alcanzan) y videos de Victoria listos.
Estados: ok · aviso (atender hoy) · alerta (algo se va a caer o ya se cayó).
"""
import datetime
import json
import os
import sys
import urllib.request
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
MX = ZoneInfo('America/Mexico_City')
AHORA = datetime.datetime.now(datetime.timezone.utc)
REDES = {'tt': 'TikTok', 'ig': 'Instagram', 'yt': 'YouTube', 'fb': 'Facebook'}


def leer(nombre, defecto):
    try:
        return json.load(open(os.path.join(RAIZ, 'contenido', nombre)))
    except (OSError, ValueError):
        return defecto


def fecha(texto):
    try:
        return datetime.datetime.fromisoformat(str(texto).replace('Z', '+00:00'))
    except ValueError:
        return None


checks = []


def anotar(area, estado, detalle):
    checks.append({'area': area, 'estado': estado, 'detalle': detalle})


def probar(nombre, funcion):
    try:
        funcion()
        anotar('Llaves', 'ok', f'{nombre} responde')
    except SystemExit as e:
        anotar('Llaves', 'alerta', f'{nombre} no responde: {str(e)[:160]}')
    except Exception as e:  # noqa: BLE001 (cualquier falla de red o de llave se reporta, no se esconde)
        anotar('Llaves', 'alerta', f'{nombre} no responde: {type(e).__name__} {str(e)[:160]}')


def llaves():
    import youtube
    import publer
    probar('YouTube', youtube.token)
    probar('Publer', publer.workspace_id)

    def replicate():
        req = urllib.request.Request('https://api.replicate.com/v1/account', headers={
            'Authorization': f"Bearer {os.environ['REPLICATE_API_TOKEN']}", 'User-Agent': 'victoria-pipeline/1.0'})
        urllib.request.urlopen(req, timeout=30).read()
    probar('Replicate', replicate)

    def meta():
        # El proxy de la sesión pone el token de la app "Victoria Comentarios" en graph.facebook.com.
        urllib.request.urlopen('https://graph.facebook.com/v22.0/me?fields=id', timeout=30).read()
    probar('Meta (Instagram y Facebook)', meta)


def saldo():
    rep = leer('replicate.json', {})
    s = rep.get('saldo_estimado_usd')
    if s is None:
        anotar('Replicate', 'aviso', 'Sin saldo estimado: corre scripts/replicate_gasto.py')
    elif s < 10:
        anotar('Replicate', 'alerta', f'Saldo estimado ${s:.2f}: no alcanza para un video largo (~$6-7). Rodrigo debe recargar.')
    elif s < 15:
        anotar('Replicate', 'aviso', f'Saldo estimado ${s:.2f}: alcanza para ~1 video largo más.')
    else:
        anotar('Replicate', 'ok', f'Saldo estimado ${s:.2f}')


def calendario():
    """Publicaciones por día y red en los próximos 3 días (hora de México)."""
    config = leer('config.json', {})
    meta = config.get('publicaciones_por_dia', {'tt': 3, 'ig': 2, 'yt': 3})
    dias = [(AHORA.astimezone(MX) + datetime.timedelta(days=i)).date().isoformat() for i in range(3)]
    cuenta = {d: {r: 0 for r in REDES} for d in dias}

    def sumar(cuando, red):
        f = fecha(cuando)
        if f:
            d = f.astimezone(MX).date().isoformat()
            if d in cuenta:
                cuenta[d][red] += 1

    for c in leer('carruseles.json', {}).get('carruseles', []):
        for red, cuando in (c.get('publica_utc_por_red') or {}).items():
            sumar(cuando, red)
        if (c.get('reel_ig') or {}).get('programado_utc'):
            sumar(c['reel_ig']['programado_utc'], 'ig')
            sumar(c['reel_ig']['programado_utc'], 'fb')
    for r in leer('recortes.json', []):
        horas = r.get('publica_utc_por_red') or {}
        if r.get('estado') in ('programado', 'listo') and horas:
            for red in ('yt', 'ig', 'tt'):
                sumar(horas.get(red), red)
            sumar(horas.get('ig'), 'fb')
    for l in leer('largos.json', []):
        sumar(l.get('publica_utc'), 'yt')
        sumar(l.get('publica_utc'), 'fb')
    for v in leer('plan.json', {}).get('videos', []):
        if v.get('estado') in ('programado', 'publicado'):
            for red, cuando in (v.get('publica_utc_por_red') or {}).items():
                sumar(cuando, red)
    for i, d in enumerate(dias):
        huecos = [f"{REDES[r]} {cuenta[d][r]}/{meta[r]}" for r in ('tt', 'ig', 'yt') if cuenta[d][r] < meta.get(r, 0)]
        resumen = ', '.join(f"{REDES[r]} {cuenta[d][r]}" for r in REDES)
        if not huecos:
            anotar('Calendario', 'ok', f'{d}: {resumen}')
        else:
            # Cada día lo llena la rutina diaria de las 6:37 de ese día: un hueco de HOY es aviso; de mañana, normal.
            anotar('Calendario', 'aviso' if i == 0 else 'ok',
                   f"{d}: {resumen} · {'faltan' if i == 0 else 'la rutina de ese día llena'}: {', '.join(huecos)}")
    return cuenta


def largos_y_recortes():
    recortes = leer('recortes.json', [])
    con_recortes = {r['largo'] for r in recortes}
    for l in leer('largos.json', []):
        f = fecha(l.get('publica_utc'))
        subido = bool(l.get('youtube'))
        if f and not subido:
            horas = (f - AHORA).total_seconds() / 3600
            if horas < 0:
                anotar('Videos largos', 'alerta', f"{l['id']}: su hora ({l['publica_utc']}) ya pasó y no está en YouTube")
            elif horas < 72:
                armado = os.path.exists(os.path.join(RAIZ, 'videos', 'largos', f"{l['id']}-horizontal.mp4"))
                anotar('Videos largos', 'aviso' if horas > 12 else 'alerta',
                       f"{l['id']}: sale en {horas:.0f} h y no está subido ({'armado' if armado else 'sin armar'}): largo.py subir {l['id']}")
            else:
                anotar('Videos largos', 'ok', f"{l['id']}: sale {l['publica_utc'][:10]}, en producción")
        elif subido:
            if not l.get('facebook'):
                anotar('Videos largos', 'aviso', f"{l['id']}: en YouTube pero no en Facebook: largo.py facebook {l['id']}")
            if l['id'] not in con_recortes:
                anotar('Recortes', 'aviso', f"{l['id']}: subido sin recortes: recortes.py {l['id']}")
            else:
                anotar('Videos largos', 'ok', f"{l['id']}: YouTube y Facebook {l['publica_utc'][:10]}, con recortes")
    sin_hora = [r['id'] for r in recortes if r.get('estado') == 'listo' and not r.get('publica_utc_por_red')]
    if sin_hora:
        anotar('Recortes', 'aviso', f"{len(sin_hora)} recortes listos sin horario: recortes.py programar")
    for r in recortes:
        horas = r.get('publica_utc_por_red') or {}
        if r.get('estado') == 'listo' and horas:
            f = fecha(horas.get('yt'))
            hecho = r.get('publicado_en', {})
            faltan = [n for n, k in (('YouTube', 'yt'), ('Instagram/TikTok/Facebook', 'ig_tt_fb')) if k not in hecho]
            estado = 'alerta' if f and f < AHORA + datetime.timedelta(hours=6) else 'aviso'
            anotar('Recortes', estado, f"{r['id']}: falta subir a {', '.join(faltan)} (sale {horas.get('yt', '')[:16]}): recortes.py publicar {r['id']}")
    prog = sum(1 for r in recortes if r.get('estado') == 'programado')
    if prog:
        anotar('Recortes', 'ok', f'{prog} recortes programados en las 4 redes')


def cola():
    carr = leer('carruseles.json', {}).get('carruseles', [])
    listos = [c for c in carr if c.get('estado') == 'listo' and not (c.get('publica_utc_por_red') or {}).get('tt')]
    dias = len(listos) / 3
    anotar('Cola', 'alerta' if dias < 2 else 'aviso' if dias < 5 else 'ok',
           f'{len(listos)} carruseles listos para TikTok (~{dias:.0f} días a 3 por día)')
    videos = [v for v in leer('plan.json', {}).get('videos', []) if v.get('estado') == 'listo_para_publicar']
    anotar('Cola', 'ok' if videos else 'aviso', f'{len(videos)} videos de Victoria listos para publicar')


def ganadores():
    """Regla "clonar al ganador" (Rodrigo, 12-nov-2026: "el 1 me encanta"): una publicación que en alguna red saca el
    CINCO VECES la mediana de esa red (y al menos 1,000 vistas; con el doble salían videos viejos que solo acumularon) recibe 3 variantes con su misma estructura en 72 h. Las
    variantes llevan "clon_de": "<id>" en carruseles.json o plan.json."""
    import statistics
    try:
        pubs = json.load(open(os.path.join(RAIZ, 'centro', 'datos', 'estado.json')))[0].get('publicaciones') or []
    except (OSError, ValueError, IndexError, KeyError):
        return
    clones = {}
    for x in leer('carruseles.json', {}).get('carruseles', []) + leer('plan.json', {}).get('videos', []):
        if x.get('clon_de'):
            clones[x['clon_de']] = clones.get(x['clon_de'], 0) + 1
    for red in ('tt', 'ig', 'yt', 'fb'):
        valores = [p['por_red'][red] for p in pubs if p['por_red'].get(red)]
        if len(valores) < 5:
            continue
        mediana = statistics.median(valores)
        for p in pubs:
            v = p['por_red'].get(red) or 0
            if v >= max(1000, 5 * mediana):
                hechos = clones.get(p['id'], 0)
                if hechos >= 3:
                    anotar('Ganadores', 'ok', f"{p['id']} ({REDES[red]} {v:,} vs mediana {mediana:,.0f}): ya tiene {hechos} clones")
                else:
                    anotar('Ganadores', 'aviso', f"{p['id']} «{p['titulo'][:50]}» saca {v:,} en {REDES[red]} (mediana {mediana:,.0f}): "
                           f"faltan {3 - hechos} clones con su misma estructura (clon_de: \"{p['id']}\")")


def main():
    if '--sin-red' not in sys.argv:
        llaves()
    saldo()
    calendario()
    largos_y_recortes()
    cola()
    ganadores()
    peor = 'alerta' if any(c['estado'] == 'alerta' for c in checks) else 'aviso' if any(c['estado'] == 'aviso' for c in checks) else 'ok'
    salida = {'generado_utc': AHORA.strftime('%Y-%m-%dT%H:%M:%SZ'), 'estado': peor, 'checks': checks}
    with open(os.path.join(RAIZ, 'contenido', 'salud.json'), 'w') as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
        f.write('\n')
    marca = {'ok': 'OK    ', 'aviso': 'AVISO ', 'alerta': 'ALERTA'}
    for c in sorted(checks, key=lambda c: ('alerta', 'aviso', 'ok').index(c['estado'])):
        print(f"{marca[c['estado']]} {c['area']}: {c['detalle']}")
    print(f'\nEstado general: {peor.upper()}')


if __name__ == '__main__':
    main()
