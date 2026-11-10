# Estrategia para crecer y hacerse viral (manager de redes, 9-nov-2026)

Rodrigo, 9-nov-2026: "tienes autoridad para tomar decisiones como un manager de redes sociales que contrataron para
crecer este canal, en todos lados". Este documento es el plan. La rutina diaria lo sigue junto con PERSONAJE.md.

## El diagnóstico (11 días después del arranque)

- ~500 vistas por publicación, casi cero comentarios reales, 0 suscriptores nuevos, 4 compartidos en 28 días (Muse).
- Lo que más empuja a gente nueva es que te **compartan** (Instagram) y que **comenten en la primera hora** (todas).
- En TikTok los carruseles rinden igual o mejor que los videos de Wan y cuestan 0 créditos.

## Un solo tema, muchos ángulos

Tu dinero en México. Nada de salud mental, productividad ni historias de empresas por ahora (en reserva).

## Lo que ya funcionó

- **9-nov-2026: c16 "Guarda esto: tu aguinaldo 2026 en 5 datos"**: 3,361 vistas en TikTok en 15 h, 14 compartidos
  (7 veces lo mejor anterior). Formato "Guarda esto: ___ en 5 datos" + tema de temporada + cifras con fecha. Se repite.

## Series (cada una es una promesa: "sígueme para la siguiente")

| Serie | Formato | Por qué |
|---|---|---|
| ¿Cuánto gana un ___ en México? | Carrusel con dato oficial (Data México / INEGI) + "así lo repartiría yo" | Sueldos = lo más comentado y etiquetado. Pide "comenta tu profesión" |
| Victoria reparte tu sueldo | Respuesta a un comentario real (sueldo + ciudad) | Premia al que comenta; contenido infinito |
| Victoria responde | Carrusel que contesta un comentario real, con el usuario en la portada ("@usuario preguntó…") | Premia al que comenta y enseña que aquí sí te contestan: más gente comenta |
| Capital juzga tus gastos | Memes con fotos de Capital con cara de juicio | Perros con cara de juicio = compartibles |
| Victoria vs. los consejos de tu tío | Mito/verdad con memes | Se manda al grupo de la familia |
| Mito o verdad | Quiz de 5 | Retención hasta el final y "comenta cuántas te sabías" |
| Diciembre / aguinaldo / enero | Memes + calculadoras | Temporada: lo que se busca ahora |

## Victoria responde (10-nov-2026)

- La tarea de comentarios (cada 2 h) guarda en contenido/preguntas.json los comentarios que dan para un carrusel: una
  pregunta de dinero, un sueldo, una profesión o una duda de la ley ({red, autor, texto, fecha, enlace, tipo, usado}).
- La rutina diaria toma la mejor pregunta sin usar y escribe un carrusel "Victoria responde" (datos oficiales y segunda
  revisión, como todos), que sale primero en TikTok al día siguiente (config → prioridad_carruseles).
- Privacidad: el @usuario va en la portada solo con su pregunta. Si comentó su sueldo, deudas u otro dato personal, NO se
  pone su usuario junto al dato: "Me escribieron: gano $12,000…". Nunca nombres reales, empresas ni datos de terceros.
- Cuando sale, se le contesta el comentario original: "Te contesté en un video 👉" (si la red deja).

## Ritmo

Rodrigo, 9-nov-2026: "TikTok 3 al día, YouTube 2, Instagram 2 (uno en la mañanita, otro en la tarde). El chiste es
subir lo mismo en todas las redes, no perder ningún reel, carrusel, imagen". En config → publicaciones_por_dia.

- TikTok: **3 al día**. El video de Victoria cuenta como uno; lo demás, carruseles en fotos con música recomendada.
- Instagram: **2 al día**, uno antes de las 13:00 y otro después. Reel del carrusel (o el video de Victoria ese día).
- YouTube: **3 al día** (Rodrigo, 9-nov-2026, para no atrasarse): el video de Victoria o shorts de carrusel.
- Todo carrusel pasa por las tres redes: primero TikTok (donde se prueba), luego Instagram y YouTube en este orden:
  hits, los que ya llevan 7 días esperando, los probados (temporada y vistas). La auditoría muestra la cola de cada red.
- Ojo con la cuenta: TikTok saca 3 e Instagram 2, así que Instagram se atrasa ~1 carrusel al día (YouTube va al parejo). Si la
  cola pasa de 3 días, la auditoría lo avisa: subir esa red a 3 o bajar TikTok. Los de temporada que caducan antes
  de llegar no salen (sería contenido viejo).
- Videos de Victoria (Wan): cada 3 días, solo temas fuertes. Videos de 0 créditos: "calcúlalo conmigo".
- Música: TikTok pone la de su biblioteca a los carruseles; los videos de carrusel en Instagram, Facebook y YouTube
  llevan música de fondo propia (los de Victoria no, por la sincronía de labios); martes y viernes un Reel de Instagram va con sonido de la biblioteca, subido por Rodrigo (CARRUSELES.md → Música).
- Facebook recibe lo de Instagram y además los shorts de YouTube, con el enlace directo (ahí sí se toca).
- Facebook (página "Victoria the CEO", desde el 9-nov-2026): todo lo de Instagram sale también ahí, a la misma hora,
  sin hacer nada aparte. Lo que ya había salido antes en las otras redes se subió del 9 al 13-nov, dos por día.

## Reglas para que se comparta

1. Portada con postura o con una cifra que duele, nunca un título de folleto.
2. Una persona concreta en el "Mándaselo a…" (tu primo, el grupo de la familia, tu pareja).
3. Pregunta de una palabra o un número al final; "Te contesto a todos" y se cumple.
4. Humor con Capital en cada pieza; el chiste es sobre la práctica, nunca sobre la gente.
5. Victoria siempre visible: portada, cara en cada diapositiva, cierre.

## Qué se mide (cada lunes en el reporte)

- Compartidos y guardados por pieza (Instagram, capturas de Rodrigo), comentarios reales, seguidores nuevos por red.
- Vistas de TikTok a ~48 h por tipo de portada (auditoría: postura / si / dato / meme / mito).
- Lo que gana se repite; lo que pierde dos semanas seguidas se deja.
- **Bitácora de cambios** (contenido/cambios.json, sale en el centro → "Mejora día a día"): cada vez que cambie el ritmo,
  un formato, una serie o la estrategia, se agrega una línea {fecha, cambio, por_que, vigilar: yt|tt|ig|fb|todas}. El centro
  compara solo las vistas por día de 3 días antes contra 3 días después. Lo que no mejora en una semana se revisa.

## Muse (la IA de Meta) como asesora de Instagram y Facebook

Rodrigo, 9-nov-2026. Muse ve lo que Claude no (alcance, guardados, de dónde llega la gente, qué empuja Meta). No se conecta
por API (pagar dos veces y dos managers dando órdenes): una vez por semana Rodrigo copia el reporte del centro
("Mejora día a día" → "Copiar reporte para Muse"), lo pega en Muse y le pasa a Claude lo que conteste. Claude decide qué
se aplica, lo programa y lo apunta en contenido/cambios.json para medir si funcionó. Una sola cabeza al mando.

## Lo que solo Rodrigo puede hacer (y más pesa)

1. Bio con el enlace (https://victoriatheceo.vercel.app/?ref=ig / ?ref=tt).
2. Contestar comentarios en la primera hora (panel → Respuestas rápidas) o sacar el permiso de Instagram para que lo
   haga Claude.
3. Crear la página de Facebook (kit en perfil/facebook/).
4. $300–500 MXN para empujar la pieza que mejor rinda cada semana (Claude dice cuál el viernes).

## Comenta GUÍA (Instagram, 10-nov-2026)

En Instagram el texto dice "comenta GUÍA y te lo mando por mensaje" (config.json → guia_por_mensaje_ig). La rutina de
comentarios corre primero `python3 scripts/comentarios_ig.py guias`: a cada comentario con "guía" le manda por mensaje
privado el enlace que va con el post (aguinaldo, fondo de emergencia, deudas, 50/30/20 o el sitio, con ?ref=ig-dm) y le
contesta en público "te lo mandé por mensaje". Si Meta no deja mandar el privado, la respuesta pública lleva el enlace.
Queda anotado en contenido/guias_ig.json. Solo a quien lo pidió comentando; nunca mensajes a nadie más.

## Mensajes privados de Instagram (10-nov-2026)

Rodrigo prendió el acceso a mensajes. La rutina de comentarios corre `python3 scripts/comentarios_ig.py mensajes` y
contesta cada uno con `contestar <para> "texto"`, en la voz de Victoria y con las mismas reglas de los comentarios. Si
piden la guía o una calculadora, va el enlace con ?ref=ig-dm. Solo a quien escribió primero y dentro de las 24 h que
deja Meta. Nunca mensajes de prospección ni a quien no escribió. Si alguien pide hablar con una persona, o algo que no es
de dinero (colaboraciones, prensa, quejas), se le contesta que su mensaje pasa al equipo y se le avisa a Rodrigo en la
línea final.

## Comenta hoy (TikTok, 10-nov-2026)

TikTok no deja comentar en videos ajenos por API, y automatizarlo con un navegador arriesga la cuenta. Por eso la rutina
de las 6:37 arma contenido/comentar_hoy.json y Rodrigo comenta a mano desde el panel (sección "Comenta hoy"):
- Busca con search_viral_videos (revid) videos de TikTok en español de los últimos 3 días: finanzas personales, dinero en
  pareja, aguinaldo, tarjetas, Buen Fin, bancos, SAT. Varias búsquedas, porque el buscador trae ruido (recetas, deportes).
- Elige de 3 a 5: 2-3 grandes (100 mil vistas o más, para que mucha gente vea el comentario) y 1-2 chicos de finanzas en
  México (contestan y devuelven la visita). Nunca de menores de edad, política partidista, tragedias ni videos de odio.
  Si no hay 3 que valgan la pena, pon los que haya y dilo; no rellenes.
- Comentario de máximo 150 caracteres (límite de TikTok), en la voz de Victoria, específico al video: suma un dato
  mexicano comprobado (con fuente oficial verificada con WebSearch), una opinión o una pregunta que invite a contestar.
  Nunca enlaces, "sígueme", autopromoción, consejos de inversión ni el mismo texto en dos videos.
- Formato: {"fecha", "videos": [{"url", "autor", "vistas", "comentarios", "publicado", "tema", "comentario", "por_que"}]}.

## PLAN VIGENTE 10-nov → 24-nov-2026 (congelado: no se cambia el formato hasta medirlo el 24-nov)

Diagnóstico con datos (9-nov): TikTok 15 piezas, 471 vistas promedio, 4 comentarios en total; los 2 mejores son de
AGUINALDO (c16 3,361; c01 624). Las listas genéricas ("5 reglas de Buffett", "5 lecciones de negocio") no pasan de 525.
Los videos de Victoria hablando son lo mejor en YouTube (674-701 vistas) y lo peor en TikTok. En 8 días hubo 19 cambios
de estrategia: así no se aprende nada. Desde hoy, 14 días con estas reglas, y se mide el 24-nov.

1. AGUINALDO TODOS LOS DÍAS hasta el 20-dic (fecha límite de pago): es la ola de búsqueda más grande del año en el
   nicho y la única que nos ha funcionado. Cola: config.json → prioridad_carruseles.
2. NOTICIA DE DINERO EN 24 H: cuando haya una noticia de dinero que esté en tendencia (un banco que quiebra, el salario
   mínimo 2027, la UMA, el Buen Fin, cambios del SAT), la rutina escribe ese mismo día un carrusel "¿Qué significa para
   tu bolsillo en México?", con datos de fuente oficial y segunda revisión, y lo pone primero en la cola. La primera:
   el banco que quebró en Paraguay (2-nov) → "¿Tu dinero está seguro en México?" (IPAB 400 mil UDIS por persona y banco;
   SOFIPO 25 mil UDIS; qué NO cubre el IPAB; el caso CIBanco de 2025). Verificar todo antes de publicar.
3. LA SERIE (motor de seguidores): "¿Alcanza el salario mínimo? Hago las cuentas", 5 partes (c66 es la parte 1: cuánto
   llega). Victoria es un personaje de IA: son CUENTAS con datos oficiales, nunca "lo viví" (regla de GANCHOS: nada de
   primera persona inventada). Parte 2: la renta (con las rentas y ciudades que la gente comente en la parte 1 + un dato
   oficial de INEGI); parte 3: la comida (CONEVAL, canasta alimentaria); parte 4: el transporte; parte 5: el veredicto.
   Una parte cada 2 días después de que salga la anterior en TikTok; cada portada dice "PARTE X DE 5" y cada cierre
   "sígueme para no perderte la parte X+1". Una serie con capítulos es lo que hace que la gente SIGA la cuenta.
4. EL MOTOR DE COMENTARIOS: "Dime tu sueldo y te reparto tu aguinaldo". Cada sueldo que comenten se contesta y, si da para
   contenido, se vuelve un carrusel "Reparto el aguinaldo de @usuario" (sin datos personales más allá de su usuario y su
   sueldo, que ya hizo públicos). Requiere los primeros comentarios: amigos de Rodrigo + "Comenta GUÍA" + "Comenta hoy".
5. DEBATE DE PAREJA (c27, c41, c28, c29 y la serie Socios en casa): Victoria toma postura; esos generan opiniones.
6. SE DEJA: listas genéricas sin México ni fecha (Buffett, "5 lecciones de negocio", "5 cambios"). No se escriben más.
7. YOUTUBE: los videos de Victoria hablando siguen (2-3 por semana); es donde mejor retienen.

## Comentar en YouTube (Rodrigo lo autorizó el 10-nov-2026)

YouTube sí deja comentar en videos ajenos por API (permiso youtube.force-ssl del canal). Cada día la rutina corre
`python3 scripts/comentar_youtube.py buscar`, elige hasta 3 videos de finanzas en México de los últimos 3 días (canales
distintos), lee su descripción y escribe un comentario específico de Victoria (máximo 300 caracteres, dato comprobado u
opinión marcada, sin enlaces ni "sígueme", sin repetir texto) y lo publica con `comentar_youtube.py comentar <id> "texto"`.
El script pone los candados (3 al día, un canal por día, nunca dos veces en un video). Si el sistema de permisos de la
sesión frena la publicación, NO se fuerza: ese comentario va a contenido/comentar_hoy.json (con "YouTube ·" en el tema)
para que Rodrigo lo pegue desde el canal de Victoria, y se dice en el resumen.
