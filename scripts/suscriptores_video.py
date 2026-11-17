"""Qué video de YouTube trae suscriptores (Rodrigo, 17-nov-2026: "no sé si ya cancelar… no veo que funcione"; "siii" a
medir suscriptores por video). Lo demás del sistema optimiza vistas; esto mide lo que importa para seguir o pausar.

YouTube Analytics da subscribersGained/subscribersLost por video (llega con 2-3 días de atraso). TikTok e Instagram no
dan seguidores por publicación en su API: ahí solo hay seguidores netos por día (contenido/seguidores.json).

Uso: python3 scripts/suscriptores_video.py          guarda contenido/suscriptores_por_video.json y lo imprime
Cada fila: id de la pieza (video, carrusel, largo, recorte o variante), título, formato, vistas, suscriptores ganados y
perdidos, netos y netos por cada 1,000 vistas. Los cortes del proyecto (30-nov y 15-dic, config.json → cortes_victoria)
se deciden con seguidores netos; esta tabla dice QUÉ piezas los traen.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def leer(nombre, defecto):
    try:
        return json.load(open(os.path.join(RAIZ, 'contenido', nombre)))
    except (OSError, ValueError):
        return defecto


def vid_de(enlace):
    enlace = (enlace or '').rstrip('/')
    if 'watch?v=' in enlace:
        return enlace.split('watch?v=')[1].split('&')[0]
    return enlace.split('/')[-1] if 'youtube' in enlace or 'youtu.be' in enlace else ''


def piezas():
    """{video_id de YouTube: (id de la pieza, título, formato)}."""
    salida = {}
    for v in leer('plan.json', {}).get('videos', []):
        pub = v.get('publicacion') or {}
        y = vid_de(pub.get('youtube') or pub.get('yt'))
        if y:
            salida[y] = (v['id'], (v.get('seo') or {}).get('titulo') or v['id'], 'Victoria hablando')
    for c in leer('carruseles.json', {}).get('carruseles', []):
        y = vid_de(c.get('youtube'))
        if y:
            salida[y] = (c['id'], (c.get('seo') or {}).get('titulo') or c['id'], 'Carrusel en short')
    for l in leer('largos.json', []):
        y = vid_de(l.get('youtube'))
        if y:
            salida[y] = (l['id'], (l.get('seo') or {}).get('titulo') or l['id'], 'Largo')
    for r in leer('recortes.json', []):
        y = vid_de((r.get('publicado_en') or {}).get('yt'))
        if y:
            salida[y] = (r['id'], r.get('titulo') or r['id'], 'Recorte de largo')
    for x in leer('variantes.json', []):
        y = ((x.get('redes') or {}).get('yt') or {}).get('video_id')
        if y:
            salida[y] = (x['id'], x.get('gancho') or x['id'], 'Variante')
    return salida


def main():
    import youtube
    acceso = youtube.token()
    hoy = datetime.date.today()
    url = ('https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==MINE'
           f'&startDate=2026-10-01&endDate={hoy.isoformat()}'
           '&metrics=views,subscribersGained,subscribersLost&dimensions=video&sort=-subscribersGained&maxResults=200')
    _, cuerpo = youtube._http('GET', url, headers={'Authorization': f'Bearer {acceso}'})
    filas = json.loads(cuerpo).get('rows') or []
    mapa = piezas()
    tabla = []
    for vid, vistas, ganados, perdidos in filas:
        pid, titulo, formato = mapa.get(vid, (None, None, 'Sin registrar'))
        netos = ganados - perdidos
        tabla.append({'video_id': vid, 'pieza': pid, 'titulo': titulo, 'formato': formato, 'vistas': vistas,
                      'ganados': ganados, 'perdidos': perdidos, 'netos': netos,
                      'netos_por_mil': round(netos / vistas * 1000, 2) if vistas else 0})
    por_formato = {}
    for t in tabla:
        f = por_formato.setdefault(t['formato'], {'videos': 0, 'vistas': 0, 'netos': 0})
        f['videos'] += 1
        f['vistas'] += t['vistas']
        f['netos'] += t['netos']
    for f in por_formato.values():
        f['netos_por_mil'] = round(f['netos'] / f['vistas'] * 1000, 2) if f['vistas'] else 0
    salida = {'generado': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
              'nota': 'YouTube Analytics llega con 2-3 días de atraso. Solo YouTube: TikTok e Instagram no dan seguidores por publicación.',
              'total': {'videos': len(tabla), 'vistas': sum(t['vistas'] for t in tabla),
                        'ganados': sum(t['ganados'] for t in tabla), 'perdidos': sum(t['perdidos'] for t in tabla)},
              'por_formato': por_formato,
              'videos': tabla}
    with open(os.path.join(RAIZ, 'contenido', 'suscriptores_por_video.json'), 'w') as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
        f.write('\n')
    tot = salida['total']
    print(f"YouTube desde el 1-oct: {tot['videos']} videos, {tot['vistas']:,} vistas, +{tot['ganados']} −{tot['perdidos']} suscriptores")
    for k, f in sorted(por_formato.items(), key=lambda kv: -kv[1]['netos_por_mil']):
        print(f"  {k}: {f['videos']} videos, {f['vistas']:,} vistas, {f['netos']:+} netos ({f['netos_por_mil']} por cada 1,000)")
    print('Videos que trajeron suscriptores:')
    for t in [t for t in tabla if t['ganados']][:15]:
        print(f"  {t['pieza'] or t['video_id']:10s} +{t['ganados']} −{t['perdidos']} · {t['vistas']:,} vistas · {t['formato']} · {(t['titulo'] or '')[:50]}")


if __name__ == '__main__':
    main()
