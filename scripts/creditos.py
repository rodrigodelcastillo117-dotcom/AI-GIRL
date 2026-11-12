"""Créditos de las apps de video e imagen (Rodrigo, 12-nov-2026: "mete también los créditos de Everygen al dashboard,
quiero ver, controlar y saber de todo"). Sus saldos solo se leen con los conectores (MCP) de la sesión, así que la
rutina los consulta y los anota aquí; salud.py y el panel los muestran.

Uso: python scripts/creditos.py anotar openart=199 everygen=31      (después de openart_account_get y get_credit_balance)
     python scripts/creditos.py                                     muestra lo anotado
"""
import datetime
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(RAIZ, 'contenido', 'creditos.json')
APPS = {
    'everygen': {'nombre': 'Everygen (Viewmax)', 'plan': 'Professional anual, ya pagado; termina el 26-jul-2027',
                 'mensual': 350, 'reinicia_dia': 27, 'uso': 'clips de Victoria sin voz, fotos y miniaturas',
                 'regla': 'Se pierden si no se usan: el día 23 de cada mes se gastan los que queden'},
    'openart': {'nombre': 'OpenArt', 'plan': 'Plus', 'mensual': None,
                'uso': 'respaldo de clips y fotos', 'regla': 'Cancelar al renovar si Everygen cubre todo'},
    'higgsfield': {'nombre': 'Higgsfield', 'plan': 'gratis', 'mensual': None, 'uso': 'sin uso', 'regla': '—'},
}


def leer():
    try:
        return json.load(open(RUTA))
    except (OSError, ValueError):
        return {'apps': {}}


def main():
    datos = leer()
    if len(sys.argv) > 2 and sys.argv[1] == 'anotar':
        ahora = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        for par in sys.argv[2:]:
            app, valor = par.split('=')
            info = dict(APPS.get(app, {'nombre': app}))
            anterior = (datos['apps'].get(app) or {}).get('creditos')
            info.update({'creditos': float(valor) if '.' in valor else int(valor), 'anterior': anterior, 'leido_utc': ahora})
            datos['apps'][app] = info
        datos['actualizado_utc'] = ahora
        with open(RUTA, 'w') as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
            f.write('\n')
    print(json.dumps(datos, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
