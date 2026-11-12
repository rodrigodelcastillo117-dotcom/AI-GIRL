"""Serie "Tu sueldo, tu aguinaldo" (12-nov-2026): clona el formato ganador c01/c16 (una cifra en pesos de TU sueldo +
aguinaldo + "guárdalo"; c16 hizo 3,903 vistas en TikTok contra ~200 de mediana) con un sueldo distinto por carrusel.

Uso: /tmp/voz/bin/python scripts/serie_sueldos.py <id_inicial> <sueldo_mensual|minimo|frontera> [...]
     p. ej. scripts/serie_sueldos.py c78 8000 10000 minimo
Cuentas con Decimal (redondeo a centavos, mitad hacia arriba). Datos ya verificados el 12-nov-2026 (segundo agente):
- LFT art. 87: mínimo 15 días de salario, antes del 20 de diciembre (en 2026 cae en domingo: a más tardar el sábado 19).
- LISR art. 93 fracc. XIV: exento hasta 30 UMA; UMA diaria 2026 $117.31 (INEGI, vigente desde 1-feb-2026) → $3,519.30.
- Salario mínimo 2026: general $315.04 diarios, zona libre de la frontera norte $440.87 (CONASAMI, DOF dic-2025).
Cada carrusel sale "listo" con la revisión hecha por cálculo (las cuentas se comprueban aquí mismo).
"""
import json
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

from num2words import num2words

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UMA = Decimal('117.31')
EXENTO = (UMA * 30).quantize(Decimal('0.01'))
MINIMOS = {'minimo': ('el salario mínimo', Decimal('315.04')), 'frontera': ('el mínimo de la frontera norte', Decimal('440.87'))}


def pesos(x):
    x = Decimal(x).quantize(Decimal('0.01'), ROUND_HALF_UP)
    return f'${x:,.2f}'.replace('.00', '') if x == x.to_integral() else f'${x:,.2f}'


def dicho(x):
    return num2words(int(Decimal(x).quantize(Decimal('1'), ROUND_HALF_UP)), lang='es')


def carrusel(cid, arg):
    if arg in MINIMOS:
        nombre, diario = MINIMOS[arg]
        mensual = (diario * 30).quantize(Decimal('0.01'))
        quien, quien_voz = f'Si ganas {nombre}', f'Si ganas {nombre}'
        etiqueta_sueldo = f'{pesos(diario)} diarios'
    else:
        mensual = Decimal(arg)
        diario = (mensual / 30).quantize(Decimal('0.01'), ROUND_HALF_UP)
        exacto = (mensual * 15 / 30).quantize(Decimal('0.01'), ROUND_HALF_UP)  # sin redondear el diario antes ($8,000 → $4,000)
        quien, quien_voz = f'Si ganas {pesos(mensual)} al mes', f'Si ganas {dicho(mensual)} pesos al mes'
        etiqueta_sueldo = f'{pesos(mensual)} al mes'
    agui = exacto if arg not in MINIMOS else (diario * 15).quantize(Decimal('0.01'), ROUND_HALF_UP)
    gravado = max(Decimal('0'), agui - EXENTO)
    assert abs(agui - diario * 15) < Decimal('0.10')
    titulo = f'{quien}, tu aguinaldo mínimo es {pesos(agui)}'
    imp = (f'De {pesos(agui)}, {pesos(EXENTO)} van libres de ISR y el impuesto se calcula solo sobre {pesos(gravado)}.'
           if gravado > 0 else f'Todo tu aguinaldo ({pesos(agui)}) queda dentro de lo exento: no paga ISR.')
    return {
        'id': cid, 'estado': 'listo', 'tema': 'aguinaldo_tu_sueldo', 'serie': 'Tu sueldo, tu aguinaldo', 'clon_de': 'c01',
        'pilar': 'finanzas', 'fondo': 'auto', 'ventana': {'desde': '2026-11-13', 'hasta': '2026-12-19'},
        'portada': {'foto': 'auto', 'etiqueta': 'AGUINALDO 2026', 'titulo': titulo,
                    'voz': f'{quien_voz}, tu aguinaldo mínimo es de {dicho(agui)} pesos. Guarda esto.', 'gancho_tipo': 'si'},
        'diapositivas': [
            {'titulo': 'La cuenta', 'texto': f'Sueldo diario × 15.\n{etiqueta_sueldo} → {pesos(diario)} diarios × 15 = {pesos(agui)} brutos.\n\nLey Federal del Trabajo, art. 87',
             'voz': 'La cuenta: tu sueldo diario por quince días.'},
            {'titulo': '¿Cuándo?', 'texto': 'Antes del 20 de diciembre. En 2026 el 20 cae en domingo: a más tardar el sábado 19.\n\nLFT art. 87',
             'voz': 'Te lo tienen que pagar antes del veinte de diciembre.'},
            {'titulo': '¿Paga ISR?', 'texto': f'{imp}\n\nLISR art. 93 fracc. XIV: 30 UMA × $117.31 (UMA 2026, INEGI)',
             'voz': 'Una parte va libre de impuestos: treinta UMAs.'},
            {'titulo': '¿Entraste o te fuiste este año?', 'texto': 'También te toca: la parte proporcional a los días que trabajaste.',
             'voz': 'Si entraste o te fuiste este año, te toca la parte proporcional.'},
            {'titulo': 'Calcula el tuyo exacto', 'texto': 'victoriatheceo.vercel.app/aguinaldo\n(enlace en mi perfil)',
             'voz': 'Calcula el tuyo exacto con el enlace de mi perfil.'}],
        'cierre': {'titulo': 'Guárdalo para diciembre.', 'texto': '¿Cuánto ganas tú? Comenta tu sueldo y te digo tu aguinaldo.',
                   'voz': 'Guárdalo para diciembre y comenta tu sueldo.'},
        'llamado_unico': 'guardar',
        'fuente': f'LFT art. 87 (15 días, antes del 20-dic); LISR art. 93 fracc. XIV (30 UMA); UMA 2026 diaria $117.31 (INEGI) → exento {pesos(EXENTO)}' +
                  ('; salario mínimo 2026 (CONASAMI): general $315.04, frontera norte $440.87' if arg in MINIMOS else ''),
        'titulo_post': titulo[:60],
        'texto_post': f'{titulo} 💰\n{etiqueta_sueldo} ÷ 30 × 15 = {pesos(agui)} brutos, y te lo deben pagar antes del 20 de diciembre (LFT art. 87).\n{imp}\n\n🔖 Guárdalo para diciembre. ¿Cuánto ganas tú? Comenta tu sueldo y te digo tu aguinaldo.\n\n#aguinaldo #aguinaldo2026 #finanzaspersonales #dinero #victoriatheceo',
        'seo': {'palabra_clave': 'aguinaldo 2026', 'titulo': (f'Aguinaldo 2026 con {nombre.replace("el ", "")} 💰' if arg in MINIMOS else f'Aguinaldo 2026 si ganas {pesos(mensual)} al mes 💰'),
                'tags_concretas': ['aguinaldo 2026', f'aguinaldo {etiqueta_sueldo}', 'cuanto me toca de aguinaldo', 'calcular aguinaldo', 'aguinaldo exento isr', 'aginaldo'],
                'hashtags': ['#aguinaldo', '#aguinaldo2026', '#finanzaspersonales', '#dinero'],
                'preguntas': [f'¿Cuánto es mi aguinaldo si gano {etiqueta_sueldo}?', '¿Cuándo pagan el aguinaldo?', '¿El aguinaldo paga ISR?']},
        'enlace': {'etiqueta': '🧮 Calcula tu aguinaldo gratis', 'url': 'https://victoriatheceo.vercel.app/aguinaldo'},
        'revision': f'12-nov-2026: cuentas con Decimal en scripts/serie_sueldos.py (diario {diario}, aguinaldo {agui}, exento {EXENTO}, gravado {gravado}); datos verificados por segundo agente el 12-nov.'}


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ruta = os.path.join(RAIZ, 'contenido', 'carruseles.json')
    cs = json.load(open(ruta))
    lista = cs if isinstance(cs, list) else cs['carruseles']
    n = int(sys.argv[1].lstrip('c'))
    ids = {x['id'] for x in lista}
    for arg in sys.argv[2:]:
        cid = f'c{n}'
        if cid in ids:
            sys.exit(f'{cid} ya existe')
        c = carrusel(cid, arg)
        lista.append(c)
        print(cid, c['portada']['titulo'], '|', c['seo']['titulo'], len(c['seo']['titulo']))
        n += 1
    json.dump(cs, open(ruta, 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
