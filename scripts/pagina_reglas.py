"""Página /reglas: la guía "Las 30 reglas de la CEO" + las 7 calculadoras (12-nov-2026).

Rodrigo: "hay que mandarla a la correcta, no? quiero que se vean todas las calculadoras… hazlo increíble". Es a donde
llega quien comenta GUÍA (comentarios_ig.py y centro/api/meta.js → mensaje_para). Toma el diseño de la portada
(sitio/public/index.html: estilos, menú, calculadoras y pie) para que se vea igual y las reglas de
producto/guia/reglas.json (las mismas del PDF), así nunca se desfasan.

Uso: python3 scripts/pagina_reglas.py      → sitio/public/reglas.html (después: commit; Vercel la sirve en /reglas)
"""
import html
import json
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLICO = os.path.join(RAIZ, 'sitio', 'public')
e = html.escape


def entre(texto, inicio, fin):
    a = texto.index(inicio)
    return texto[a:texto.index(fin, a) + len(fin)]


def main():
    portada = open(os.path.join(PUBLICO, 'index.html')).read()
    datos = json.load(open(os.path.join(RAIZ, 'producto', 'guia', 'reglas.json')))
    estilos = entre(portada, '<style>', '</style>')
    herramientas = entre(portada, '<div class="herramientas">', '<!--/herramientas--></div>')
    producto = entre(portada, '<div class="producto">', '<div id="venta"></div>') + '\n        </div>\n      </div>'
    pie = entre(portada, '<footer>', '</footer>').replace('href="#guia"', 'href="/reglas"').replace('href="#tablero"', 'href="/#tablero"')
    total = sum(len(s['reglas']) for s in datos['secciones'])
    paginas = 37  # el PDF de guia.py (se corrige solo si cambia: ver abajo)
    try:
        import subprocess
        info = subprocess.run(['pdfinfo', os.path.join(PUBLICO, 'guia', 'las-30-reglas-de-la-ceo.pdf')], capture_output=True, text=True).stdout
        paginas = int(re.search(r'Pages:\s+(\d+)', info).group(1))
    except Exception:
        pass

    n = 0
    bloques = []
    for i, s in enumerate(datos['secciones'], 1):
        tarjetas = []
        for r in s['reglas']:
            n += 1
            tarjetas.append(f'''<article class="regla-g">
          <div class="num">{n:02d}</div>
          <h3>{e(r["titulo"])}</h3>
          <p>{e(r["texto"])}</p>
          <div class="hazlo"><span>Hazlo hoy</span>{e(r["accion"])}</div>
          <div class="fte">{e(r["fuente"])}</div>
        </article>''')
        bloques.append(f'''<details class="parte"{" open" if i == 1 else ""}>
        <summary><span class="parte-n">Parte {i}</span><span class="parte-t">{e(s["nombre"])}</span><span class="parte-c">{len(s["reglas"])} reglas</span></summary>
        <div class="rejilla-reglas">{"".join(tarjetas)}</div>
      </details>''')

    extra = '''
    /* /reglas (12-nov-2026) */
    .heroe-guia { padding: 64px 0 40px; background: radial-gradient(900px 500px at 85% -10%, rgba(216,178,90,.16), transparent 60%), var(--negro); }
    .heroe-guia .contenedor { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr); gap: 48px; align-items: center; }
    @media (max-width: 860px) { .heroe-guia .contenedor { grid-template-columns: 1fr; gap: 26px; } .heroe-guia .libro { order: -1; width: 62%; max-width: 260px; margin: 0 auto; } .heroe-guia { padding-top: 36px; } }
    .heroe-guia h1 { font-family: "Playfair Display", serif; font-weight: 600; font-size: clamp(2.4rem, 6vw, 4.2rem); line-height: 1.02; margin: 14px 0 16px; letter-spacing: -.01em; }
    .heroe-guia h1 em { font-style: italic; color: var(--oro-2); }
    .heroe-guia .bajada { font-size: 1.12rem; color: var(--texto); max-width: 34rem; line-height: 1.6; }
    .datos-guia { display: flex; flex-wrap: wrap; gap: 10px; margin: 22px 0 26px; }
    .datos-guia span { border: 1px solid var(--linea); border-radius: 999px; padding: 7px 14px; font-size: .86rem; color: var(--marfil); background: rgba(216,178,90,.06); }
    .datos-guia b { color: var(--oro-2); font-family: "Playfair Display", serif; font-variant-numeric: lining-nums; }
    .heroe-guia h1, .regla-g .num, .parte-t { font-variant-numeric: lining-nums; }
    .botones { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
    .boton.grande { padding: 18px 30px; font-size: 1.05rem; }
    .boton.fantasma { background: transparent; color: var(--oro-2); }
    .libro { position: relative; perspective: 1200px; }
    .libro img { width: 100%; height: auto; border-radius: 6px 14px 14px 6px; transform: rotateY(-14deg) rotateX(3deg); box-shadow: -18px 24px 60px rgba(0,0,0,.6), 0 0 0 1px rgba(216,178,90,.3), 0 0 90px rgba(216,178,90,.14); transition: transform .4s; }
    .libro:hover img { transform: rotateY(-4deg); }
    .libro::after { content: "GRATIS"; position: absolute; top: 18px; right: -10px; background: var(--oro); color: #111; font-weight: 800; letter-spacing: .2em; font-size: .78rem; padding: 8px 14px; border-radius: 999px; box-shadow: 0 8px 24px rgba(216,178,90,.35); }
    .parte { border: 1px solid var(--linea-2); border-radius: var(--radio); background: var(--negro-2); margin-bottom: 14px; overflow: hidden; }
    .parte > summary { list-style: none; cursor: pointer; display: flex; align-items: baseline; gap: 14px; padding: 22px 24px; }
    .parte > summary::-webkit-details-marker { display: none; }
    .parte > summary::after { content: "+"; margin-left: auto; color: var(--oro); font-size: 1.4rem; line-height: 1; }
    .parte[open] > summary::after { content: "−"; }
    .parte-n { font-size: .74rem; letter-spacing: .24em; text-transform: uppercase; color: var(--oro); font-weight: 600; }
    .parte-t { font-family: "Playfair Display", serif; font-size: 1.5rem; font-weight: 600; }
    .parte-c { color: var(--tenue); font-size: .86rem; }
    @media (max-width: 560px) { .parte > summary { flex-wrap: wrap; gap: 4px 12px; padding: 18px; } .parte-t { font-size: 1.25rem; } }
    .rejilla-reglas { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; padding: 0 18px 20px; }
    @media (max-width: 560px) { .rejilla-reglas { grid-template-columns: 1fr; padding: 0 12px 14px; } }
    .regla-g { position: relative; padding: 22px 20px 18px; border-radius: 14px; background: var(--panel); border: 1px solid var(--linea-2); display: flex; flex-direction: column; gap: 10px; }
    .regla-g .num { position: absolute; top: 12px; right: 16px; font-family: "Playfair Display", serif; font-size: 2.6rem; font-weight: 700; color: rgba(216,178,90,.18); line-height: 1; }
    .regla-g h3 { margin: 0; padding-right: 54px; font-family: "Playfair Display", serif; font-size: 1.25rem; font-weight: 600; line-height: 1.2; color: var(--marfil); }
    .regla-g p { margin: 0; color: var(--texto); line-height: 1.6; font-size: .96rem; }
    .hazlo { border-left: 3px solid var(--oro); background: rgba(216,178,90,.07); padding: 10px 12px; border-radius: 0 10px 10px 0; font-size: .92rem; color: var(--marfil); line-height: 1.5; }
    .hazlo span { display: block; font-size: .68rem; letter-spacing: .22em; text-transform: uppercase; color: var(--oro); font-weight: 700; margin-bottom: 3px; }
    .fte { margin-top: auto; font-size: .78rem; color: var(--tenue); border-top: 1px solid var(--linea-2); padding-top: 9px; }
    .franja-descarga { margin-top: 28px; padding: 30px; border-radius: var(--radio); border: 1px solid var(--linea); background: radial-gradient(600px 300px at 0% 0%, rgba(216,178,90,.14), transparent 60%), var(--negro-2); display: flex; gap: 20px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
    .franja-descarga h3 { margin: 0 0 4px; font-family: "Playfair Display", serif; font-size: 1.6rem; font-weight: 600; }
    .franja-descarga p { margin: 0; color: var(--tenue); }
'''
    estilos = estilos.replace('</style>', extra + '  </style>')
    guia = '/guia/las-30-reglas-de-la-ceo.pdf'
    documento = f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Las 30 reglas de la CEO · Guía gratis de dinero en México</title>
  <meta name="description" content="Descarga gratis Las 30 reglas de la CEO ({paginas} páginas): págate primero, 50/30/20, fondo de emergencia, deudas, interés compuesto y más, cada una con su fuente y una acción para hoy. Y 7 calculadoras gratis.">
  <meta property="og:title" content="Las 30 reglas de la CEO · Guía gratis">
  <meta property="og:description" content="{total} reglas de dinero con su fuente y una acción para hoy. Gratis, sin registrarte. Más 7 calculadoras gratis.">
  <meta property="og:image" content="https://victoriatheceo.vercel.app/img/guia-portada.jpg">
  <meta property="og:url" content="https://victoriatheceo.vercel.app/reglas">
  <link rel="canonical" href="https://victoriatheceo.vercel.app/reglas">
  <meta name="theme-color" content="#070707">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='16' fill='%23070707'/%3E%3Ctext x='16' y='22' font-size='17' font-family='Georgia' font-weight='700' fill='%23d8b25a' text-anchor='middle'%3EV%3C/text%3E%3C/svg%3E">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500;1,600&display=swap" rel="stylesheet">
  {estilos}
  <script>try {{ const u = new URL(location.href); const r = u.searchParams.get('ref'); if (r && !u.searchParams.has('utm_source')) {{ u.searchParams.set('utm_source', r); history.replaceState(null, '', u); }} }} catch {{}}</script>
  <script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
  <header class="menu">
    <div class="contenedor">
      <a class="logo" href="/"><i>V</i><span>Victoria <b>The CEO</b></span></a>
      <nav aria-label="Principal">
        <a href="#descargar">La guía</a>
        <a href="#calculadoras">Calculadoras</a>
        <a href="#las-30">Las {total} reglas</a>
        <a href="/#tablero">Plantilla</a>
        <a class="cta" href="{guia}" data-guia download>Descargar gratis</a>
      </nav>
    </div>
  </header>

  <main>
  <section class="heroe-guia" id="descargar">
    <div class="contenedor">
      <div>
        <span class="sello">Guía gratis · PDF de {paginas} páginas · sin registrarte</span>
        <h1>Las {total} reglas <em>de la CEO.</em></h1>
        <p class="bajada">{e(datos["subtitulo"])} Cada regla trae su fuente real, una acción para hoy y un ejercicio para escribir. Al final: tu tablero en papel y el reto de 30 días.</p>
        <div class="datos-guia"><span><b>{total}</b> reglas</span><span><b>{total}</b> acciones para hoy</span><span><b>5</b> hojas para llenar</span><span>Reto de <b>30</b> días</span><span><b>7</b> calculadoras gratis</span></div>
        <div class="botones">
          <a class="boton grande" href="{guia}" data-guia download>Descargar la guía gratis</a>
          <a class="boton fantasma" href="#las-30">Leerla aquí</a>
        </div>
      </div>
      <div class="libro"><img src="/img/guia-portada.jpg" alt="Portada de la guía Las 30 reglas de la CEO" width="700" height="994"></div>
    </div>
  </section>

  <section class="bloque" id="calculadoras">
    <div class="contenedor">
      <div class="encabezado">
        <div class="antetitulo">Gratis · sin registrarte · con fuente oficial</div>
        <h2>Tus 7 calculadoras.</h2>
        <p>Pon tus números y en segundos sabes cuánto te toca, cuánto te queda y qué hacer primero.</p>
      </div>
      {herramientas}
    </div>
  </section>

  <section class="bloque" id="las-30">
    <div class="contenedor">
      <div class="encabezado">
        <div class="antetitulo">Toda la guía, aquí mismo</div>
        <h2>Las {total} reglas.</h2>
        <p>Toca cada parte para abrirla. Si no tiene fuente, es mi opinión, y te lo digo.</p>
      </div>
      {"".join(bloques)}
      <div class="franja-descarga">
        <div><h3>Llévatela en tu celular.</h3><p>El PDF de {paginas} páginas, una regla por página, para leerla sin internet.</p></div>
        <a class="boton grande" href="{guia}" data-guia download>Descargar gratis</a>
      </div>
    </div>
  </section>

  <section class="bloque azul" id="tablero">
    <div class="contenedor">
      <div class="encabezado">
        <div class="antetitulo">Para ponerlo en práctica</div>
        <h2>El tablero de la CEO.</h2>
        <p>Las reglas, con tus números: presupuesto 50/30/20, fondo de emergencia, deudas, interés compuesto y metas, todo calculado solo.</p>
      </div>
      {producto}
    </div>
  </section>
  </main>

  {pie}

  <script src="/comun.js"></script>
  <script>
    document.querySelectorAll('[data-guia]').forEach((a) => {{ a.href = `{guia}?ref=${{encodeURIComponent(REF)}}`; }});
    bloqueVenta(document.getElementById('venta'), 'reglas');
    document.querySelector('#venta .boton').textContent = 'La quiero';
  </script>
</body>
</html>
'''
    salida = os.path.join(PUBLICO, 'reglas.html')
    open(salida, 'w').write(documento)
    print(f'ok {salida}: {total} reglas, {paginas} páginas del PDF')


if __name__ == '__main__':
    main()
