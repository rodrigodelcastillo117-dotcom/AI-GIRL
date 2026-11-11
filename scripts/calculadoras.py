"""Qué calculadora gratis del sitio va con cada carrusel (Rodrigo, 11-nov-2026: "haz lo necesario... vamos a hacernos
virales"). En vez de posts de "mira mi página" (el algoritmo los trata como anuncio), cada carrusel útil termina en la
calculadora de su tema: quien ya se interesó por el aguinaldo llega a calcular el suyo.

Uso: from calculadoras import calculadora_para  →  ('/aguinaldo', 'Calcula tu aguinaldo') o None
     python calculadoras.py   (muestra la calculadora de cada carrusel listo)
"""
import json
import os

SITIO_CORTO = 'victoriatheceo.vercel.app'
# El orden importa: gana la primera que aparece en el tema, el título o el inicio del texto.
RUTAS = [
    (('aguinaldo',), '/aguinaldo', 'Calcula tu aguinaldo'),
    (('finiquito', 'liquidaci', 'despid', 'te corren', 'renuncia'), '/finiquito', 'Calcula tu finiquito'),
    (('deuda', 'tarjeta', 'pago mínimo', 'pago minimo', 'meses sin intereses', 'crédito', 'credito'), '/pagar-deudas',
     'Haz tu plan para salir de deudas'),
    (('fondo de emergencia', 'emergencia'), '/fondo-de-emergencia', 'Calcula tu fondo de emergencia'),
    (('renta', 'salario mínimo', 'salario minimo', 'sueldo', 'alcanza', 'canasta'), '/te-alcanza-tu-sueldo',
     '¿Te alcanza tu sueldo? Haz tus cuentas'),
    (('presupuesto', '50/30/20', 'quincena', 'gastos hormiga', 'gasto'), '/regla-50-30-20', 'Divide tu sueldo con la 50/30/20'),
    (('interés compuesto', 'interes compuesto', 'afore', 'ahorr'), '/interes-compuesto', 'Mira cuánto crece tu ahorro'),
]


def calculadora_para(c):
    """(ruta, frase) de la calculadora que va con el carrusel c, o None si ninguna aplica."""
    if c.get('calculadora') is False:
        return None
    if isinstance(c.get('calculadora'), list):  # se puede fijar a mano: ["/finiquito", "Calcula tu finiquito"]
        return tuple(c['calculadora'])
    # Manda el título; si no dice nada, el tema; y al final el inicio del texto (11-nov-2026: c53, "finiquito si te corren en
    # diciembre", se iba a la de aguinaldo porque el texto nombra el aguinaldo primero).
    titulos = ' '.join([str(c.get('titulo_post', '')), str((c.get('portada') or {}).get('titulo', ''))])
    for texto in (titulos, str(c.get('tema', '')), str(c.get('texto_post', ''))[:300]):
        texto = texto.lower().replace('_', ' ')
        for claves, ruta, frase in RUTAS:
            if any(k in texto for k in claves):
                return ruta, frase
    return None


def linea_calculadora(c):
    """La línea para el texto del post, o '' si no aplica o el texto ya trae el sitio."""
    calc = calculadora_para(c)
    if not calc or SITIO_CORTO in (c.get('texto_post') or ''):
        return ''
    return f'🧮 {calc[1]}, gratis: {SITIO_CORTO}{calc[0]}'


def texto_con_calculadora(c):
    """texto_post con la línea de su calculadora: reemplaza una línea vieja "🧮 ... en mi perfil" o se agrega al final."""
    texto, linea = (c.get('texto_post') or '').strip(), linea_calculadora(c)
    if not linea:
        return texto
    viejas = [x for x in texto.split('\n') if x.startswith('🧮') and 'perfil' in x]
    if viejas:
        return texto.replace(viejas[0], linea)
    return texto + '\n' + linea


if __name__ == '__main__':
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datos = json.load(open(os.path.join(raiz, 'contenido', 'carruseles.json')))
    for c in (datos if isinstance(datos, list) else datos['carruseles']):
        if c.get('estado') == 'listo':
            calc = calculadora_para(c)
            print(c['id'], (c.get('titulo_post') or c.get('tema'))[:50], '→', calc[0] if calc else '(ninguna)')
