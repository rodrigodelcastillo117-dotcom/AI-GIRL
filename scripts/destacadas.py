"""Lista nocturna de destacadas (Rodrigo, 13-nov-2026: "agrega la lista nocturna"). La API de Instagram no deja crear
destacadas ni agregarles historias; esto le dice a Rodrigo qué historia de hoy va a qué destacada para que solo toque
"Destacar" (30 segundos). Portadas: assets/destacadas/.

Uso: python3 scripts/destacadas.py     imprime la lista de las historias vivas (últimas 24 h) con su destacada
"""
import datetime
import json
import os
import sys
import unicodedata
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MX = ZoneInfo('America/Mexico_City')
# Orden = prioridad cuando un título toca dos temas. "hoy" es la de Victoria Hoy (noticias).
DESTACADAS = [
    ('Verifica', ('rumor', 'verifica', 'falso', 'verdad', 'whatsapp')),
    ('Pensión', ('pension', 'imss', 'afore', 'ley 73', 'ley 97', 'modalidad 40', 'bienestar', 'jubil', 'retiro', 'issste')),
    ('Aguinaldo', ('aguinaldo',)),
    ('Sueldo', ('sueldo', 'salario', 'nomina', 'te alcanza', 'finiquito', 'liquidacion', 'vacaciones', 'isr', 'prima')),
    ('Guía', ('guia', 'reglas', 'calculadora', 'buen fin', 'tarjeta', 'deuda', 'ahorro', 'presupuesto', 'pareja')),
]


def plano(t):
    return unicodedata.normalize('NFKD', (t or '').lower()).encode('ascii', 'ignore').decode()


def destacada_de(titulo):
    t = plano(titulo)
    for nombre, claves in DESTACADAS:
        if any(c in t for c in claves):
            return nombre
    return 'Guía'


def leer(ruta):
    try:
        return json.load(open(os.path.join(RAIZ, ruta)))
    except (OSError, ValueError):
        return []


def main():
    import ig_reel_musica as ig
    from comentarios_ig import IG_USUARIO
    vivas = ig.graph('GET', f'{IG_USUARIO}/stories?fields=id,timestamp&limit=100').get('data', [])
    if not vivas:
        print('Destacadas: hoy no hay historias vivas.')
        return
    # Qué es cada historia: las de posts (historias_posts.json) y las de Victoria Hoy (noticias/historias.json)
    que = {r['ig']: (r.get('titulo') or '', None) for r in leer('contenido/historias_posts.json') if r.get('ig')}
    for r in leer('contenido/noticias/historias.json'):
        if r.get('ig_media_id'):
            que[r['ig_media_id']] = ('Victoria Hoy', 'Hoy')
    lineas, mano = [], []
    for h in sorted(vivas, key=lambda h: h['timestamp']):
        cuando = datetime.datetime.fromisoformat(h['timestamp'].replace('+0000', '+00:00')).astimezone(MX)
        hora = ('' if cuando.date() == datetime.datetime.now(MX).date() else 'ayer ') + cuando.strftime('%H:%M')
        titulo, fija = que.get(h['id'], ('(subida a mano)', None))
        destino = fija or (destacada_de(titulo) if titulo != '(subida a mano)' else 'la que corresponda')
        if titulo == '(subida a mano)':
            mano.append(hora)
            continue
        lineas.append(f'- {hora} · {titulo[:60]} → **{destino}**')
    print('Destacadas de hoy (abre la historia → Destacar → elige):')
    print('\n'.join(lineas) or '- (ninguna historia automática hoy)')
    if mano:  # las que sube Rodrigo a mano: no sé qué son; se resumen en una línea en vez de 20 renglones
        print(f'- Además {len(mano)} historias que subiste tú ({mano[0]}–{mano[-1]}): agrégalas tú a la que corresponda.')


if __name__ == '__main__':
    main()
