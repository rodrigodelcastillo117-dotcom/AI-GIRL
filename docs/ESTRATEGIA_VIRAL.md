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
**Ampliado el 11-nov-2026 (Rodrigo: "SOLO QUIERO TENER ENGAGEMENT"; autorizó "si hazlo asi"):** también recibe el enlace
quien escribe un comentario corto (4 palabras o menos) que lo pide: "quiero", "pásamelo", "info", "link", "me interesa",
"aguinaldo", "calcula". Los votos (MITAD, SÍ, NUNCA) y las opiniones largas no reciben nada. Fuera de eso sigue la regla:
nunca se manda mensaje privado a quien no lo pidió en un comentario o no escribió primero.
**Comentarios con sueldo o renta (11-nov-2026, Rodrigo: "cuando comenten de su sueldo y rentas y así, manda ese link"):**
`comentarios_ig.py guias` también detecta los comentarios con sus números ("gano 12 mil y pago 4,500 de renta"): Victoria
le contesta en público su cuenta rápida (qué % se va en renta contra el 30%) solo si los números se entienden sin duda, y
por mensaje privado le manda la calculadora https://victoriatheceo.vercel.app/te-alcanza-tu-sueldo?ref=ig-cuentas. Se
registran en contenido/guias_ig.json con tipo "cuentas": de ahí salen los casos de la parte 3 (sin nombre de nadie).
Queda anotado en contenido/guias_ig.json. Solo a quien lo pidió comentando; nunca mensajes a nadie más.

## Mensajes privados de Instagram (10-nov-2026)

Rodrigo prendió el acceso a mensajes. La rutina de comentarios corre `python3 scripts/comentarios_ig.py mensajes` y
contesta cada uno con `contestar <para> "texto"`, en la voz de Victoria y con las mismas reglas de los comentarios. Si
piden la guía o una calculadora, va el enlace con ?ref=ig-dm. Solo a quien escribió primero y dentro de las 24 h que
deja Meta. Nunca mensajes de prospección ni a quien no escribió. Si alguien pide hablar con una persona, o algo que no es
de dinero (colaboraciones, prensa, quejas), se le contesta que su mensaje pasa al equipo y se le avisa a Rodrigo en la
línea final.

## Comenta hoy (TikTok, 10-nov-2026; reglas cambiadas el 12-nov-2026)

TikTok no deja comentar en videos ajenos por API, y automatizarlo con un navegador arriesga la cuenta. Por eso la rutina
de las 6:37 arma contenido/comentar_hoy.json y Rodrigo comenta a mano desde el panel (sección "Comenta hoy").

LO QUE APRENDIMOS (12-nov-2026, Rodrigo: "de los creadores sí, pero solo eso"): los creadores le dan like y contestan
a los comentarios de Victoria, pero el público no, y nadie llega al perfil. Los comentarios eran consejos amables para el
creador ("Truco de Capital: apunta tu cuota..."). Al creador le gustan; al público no le dicen nada, no juntan likes y
se quedan abajo, donde nadie los ve. Desde hoy se escribe PARA EL PÚBLICO del video, no para el creador:
- OBJETIVO: que el comentario junte likes de otros y suba a los primeros lugares (ahí lo ven miles y algunos tocan el
  perfil). Se mide así: Rodrigo dice cuáles subieron a los de arriba.
- LLEGAR TEMPRANO: videos publicados hace menos de 24 h (mejor menos de 12 h) que ya van creciendo. Un comentario en un
  video de 3 días con 500 comentarios no lo ve nadie. 4 a 6 videos al día, no 2; si el buscador trae poco en español de
  México, haz más búsquedas (aguinaldo, quincena, renta, sueldo, tarjeta, deudas, Buen Fin, "cuánto gano", pareja y
  dinero, "me corrieron"), no bajes la vara.
- TAMAÑO: 20 mil a 1 millón de vistas, de México. Los chicos (menos de 10 mil) solo para hacer amistad con creadores,
  máximo 1 al día.
- QUÉ ESCRIBIR (uno de estos, máximo 120 caracteres, que se entienda sin ver el video):
  1. La frase que todos pensaron y nadie dijo, con humor ("Mi aguinaldo ya tiene dueño y no soy yo 🥲").
  2. Un número mexicano que sorprende y sirve, comprobado con fuente oficial ("Ojo: si te corren antes del 20 de
     diciembre, igual te toca la parte de tu aguinaldo. Art. 87 LFT.").
  3. Tomar postura clara para que la gente conteste a favor o en contra ("Prestarle a un familiar es regalar dinero con
     pasos extra. Cámbienme de opinión.").
- NUNCA: consejos dirigidos al creador ("buen video", "truco: haz esto"), enlaces, "sígueme", autopromoción, nombrar a
  Victoria o a Capital (el nombre de la cuenta ya lo dice), consejos de inversión, el mismo texto en dos videos.
- Nunca de menores de edad, política partidista, tragedias ni videos de odio.
- Formato: {"fecha", "videos": [{"url", "autor", "vistas", "comentarios", "publicado", "tema", "tipo": "frase|dato|postura",
  "comentario", "por_que"}]}.

CREADORES QUE YA CONTESTARON = la puerta más barata. Si un creador le contestó a Victoria, no es para comentarle más:
es para proponerle algo juntos (un dueto o stitch "Victoria hace las cuentas de tu video"). Rodrigo manda el mensaje a
mano; la rutina deja el texto listo en contenido/comentar_hoy.json → "colaborar": [{"autor", "mensaje"}] cuando Rodrigo
diga quién contestó.

## TODO SE UTILIZA, TODO SE SUBE, TODO SE ADAPTA (Rodrigo, 12-nov-2026)

1. **Video largo → shorts → todas las redes.** Cada video largo (contenido/largos.json, scripts/largo.py) se parte en
   shorts por capítulo con `scripts/recortes.py <id>` (Victoria en cuadro, láminas verticales, subtítulos, "Video completo
   en mi canal"). `recortes.py programar` los reparte 2 al día desde el día siguiente a que sale su largo y
   `recortes.py publicar <id>` los sube a YouTube Shorts, Instagram Reels, TikTok y Facebook.
2. **Los videos largos** van a YouTube y a la página de Facebook (video nativo, misma hora): `largo.py subir <id>`.
   TikTok e Instagram no (horizontal largo no rinde ahí). Spotify (video podcast) cuando haya 6-7 largos.
3. **Shorts y carruseles → videos largos** (la regla 2), en este orden de valor:
   (1) 3-4 carruseles del mismo tema convertidos en un largo de verdad: sus datos verificados como láminas horizontales y
   Victoria intercalada; cada carrusel es un capítulo (LC1, LC2...). (2) Recopilación de shorts de un tema con Victoria de
   anfitriona. (3) "Top 10" de un tema en cuenta regresiva. (4) Resumen semanal del domingo con los 5 shorts que más
   rindieron. (5) "Victoria responde": sus videos hablando juntos por tema, sin tomas nuevas. Nunca se recompilan los
   recortes de un largo (ese largo ya existe).
4. **Intercalar formatos cada día**: TikTok 3 carruseles de fotos + 1 recorte; YouTube Shorts 2 recortes + 1 short de
   carrusel; Instagram 1 recorte + 1 Reel de carrusel; Facebook lo de Instagram y YouTube.
5. Ciclo completo de un carrusel: TikTok (fotos) → video largo del tema (YouTube + Facebook) → recortes con Victoria en
   las 4 redes.

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

**10-nov-2026, por la tarde: YouTube RETIENE los comentarios de Victoria en canales ajenos** (moderationStatus
"heldForReview": nadie los ve hasta que el dueño del canal los aprueba; típico de canales nuevos). Por eso
`comentar_youtube.py comentar` se pausa solo mientras el último siga retenido (`comentar_youtube.py estado` lo muestra).
Si dice EN PAUSA: no comentes en YouTube ese día, ni lo mandes al panel (pegarlo a mano desde el mismo canal también
queda retenido). Se reintenta solo el día que el último salga publicado.

**Pauta (Rodrigo, 10-nov-2026): "ahorita no, pero en un futuro sí; es bueno crecer orgánicamente".** No se propone gastar
cada día; solo los viernes, como ya dice la rutina, la pieza de la semana que más convendría empujar y cuánto, para cuando
él decida. Primera prueba sugerida cuando quiera: $200 MXN, objetivo seguidores, 2 días, en el mejor "Guarda esto".

**GUÍA instantánea (11-nov-2026, código listo, falta configurar):** `centro/api/meta.js` recibe el aviso de Meta al momento
(webhook) y entrega la guía en segundos. Se activa cuando Rodrigo: (1) genera en Meta Business un token del usuario del
sistema con instagram_manage_messages e instagram_manage_comments y le asigna la página "Victoria the CEO"; (2) pone en
Vercel (proyecto victoria-centro) META_TOKEN, META_APP_SECRET y META_VERIFY_TOKEN; (3) en Meta for Developers → la app →
Webhooks → Instagram, pone la URL https://victoria-centro.vercel.app/api/meta y la misma META_VERIFY_TOKEN, y marca
"comments". La revisión de cada hora sigue de respaldo y se salta lo que ya contestó el aviso.

## Experimentos creativos (Rodrigo, 11-nov-2026: "vuélate la barda"; "si hazlo, venga")

Uno nuevo por semana, medido contra el promedio de su red; el que gane se queda. No toca la prueba congelada del PLAN
VIGENTE (formato de TikTok) porque va en espacios aparte.

1. **"Comenta y te hago las cuentas" (desde el 12-nov, serie del salario mínimo).** c67 (parte 2, la renta) cierra con
   "¿Cuánto ganas, cuánto pagas de renta y en qué ciudad? Comenta y te hago las cuentas". La **parte 3** se arma con esos
   comentarios: la rutina lee los de Instagram y YouTube (`comentarios_ig.py`, `comentarios.py pendientes`; los de TikTok
   solo si Rodrigo los pega en el panel) y elige 3 a 5 casos distintos (ciudades y sueldos variados). Cada diapositiva:
   "Me escribieron de <ciudad>: gana $X y paga $Y de renta" → lo que le queda, contra la canasta alimentaria de CONEVAL y
   el 30% de referencia de la ONU (datos oficiales con fuente y segunda revisión). **Nunca** nombre de usuario ni datos
   que identifiquen a la persona: solo ciudad y montos que ella misma escribió. **Nunca** un caso inventado: si hay menos de
   2 comentarios reales con números, la parte 3 sale como estaba planeada (la comida) y se vuelve a pedir en su cierre.
   Cierre de la parte 3: "¿Te hago las tuyas? Comenta sueldo, renta y ciudad".
2. **Fotos en el feed de Instagram (desde el 11-nov).** Además de los Reels, un carrusel en fotos al día
   (config.json → ig_fotos_feed_por_dia = 1): el carrusel de TikTok con más vistas que no haya salido en fotos en Instagram
   (`publer_carrusel.py <id> "ig=<hora>"`, a 3 h o más de lo demás, entre 18:00 y 20:00). Primero salió c16 ("Guarda
   esto", el récord) el 11-nov a las 18:30. Con sus revisiones de GUÍA a los 15 y 40 minutos, igual que los Reels.
3. **Semana del 16-nov: "Capital audita tus gastos"** (fotos; video solo si hay créditos de OpenArt).
4. **Semana del 23-nov: "¿Cuántas quincenas te cuesta…?"** con calculadora en el sitio.
5. **Semana del 30-nov: "Reacciono a consejos de dinero de internet: ¿sirven en México?"** (Victoria califica del 1 al 10).
Fuera: historias personales inventadas de Victoria, otra mujer en cuadro, política.

## "Victoria, analiza mi caso" (calculadora ¿Te alcanza tu sueldo?, 11-nov-2026)

Botón con IA en https://victoriatheceo.vercel.app/te-alcanza-tu-sueldo (`sitio/api/analiza.js`): Claude Haiku 5.5
(Rodrigo: "el modelo barato pero bueno, precio calidad") recibe las cuentas ya hechas con datos oficiales y lo que le
preocupa a la persona, y escribe un plan de 3 pasos de máximo 170 palabras. Solo presupuesto, renta, comida, deudas y ahorro;
nunca inversiones, créditos ni productos; 3 consultas por persona por hora. Variables en Vercel (proyecto victoriatheceo):
ANTHROPIC_API_KEY (la puso Rodrigo) y ANTHROPIC_WORKSPACE_ID (su clave no está asignada a un workspace). Si la calidad no
alcanza, subir a claude-sonnet-5-5. Cada análisis queda en los registros de Vercel con sus tokens para medir el costo.

## Cada carrusel termina en su calculadora (11-nov-2026, Rodrigo: "haz lo necesario... vamos a hacernos virales")

No se hacen posts de "mira mi página" (el algoritmo los trata como anuncio y bajan el promedio de la cuenta). En su lugar,
`scripts/calculadoras.py` elige la calculadora del tema de cada carrusel (por el título primero, luego el tema y el
texto) y `carrusel.py` la pone en una franja negra en la diapositiva final; `publer_carrusel.py` agrega la línea
"🧮 <calculadora>, gratis: victoriatheceo.vercel.app/<ruta>" al texto (reemplaza la vieja "en mi perfil"). Se puede fijar
a mano en el carrusel: "calculadora": ["/ruta", "Frase"] o false. Además, c69 ("Guarda esto: 7 calculadoras gratis") es el
menú para fijar en el perfil de Instagram y TikTok (lo fija Rodrigo: la API no deja).

## Lo que hace viral a las finanzas en español (investigación del 11-nov-2026)

Fuente: búsqueda de lo viral en TikTok en español, sep-nov 2026 (revid), + TikTok Newsroom y Mosseri (Instagram).
Los que pegaron: @pepsgranadosv 4.5M ("¿cuánto tiempo te tomaría comprar… con el salario mínimo de cada país?"),
@estudioribeiro 4.2M ("hay 3 reglas que todo empleador debe conocer"), @samaniego2113 2.3M y 60.5K compartidos ("ojalá
hubieras sabido esto antes… guarda este video y compártelo con tu familia"), @futuroenpareja 2M (contraste de dos parejas),
@soycharlygalleta 1.6M (noticia de banco), @samaniego2113 717K ("mucho ojo con este aviso"). Lo que fracasa: venta
disfrazada de consejo ("comenta PPR"). Nuestro único éxito (c16, 3,903 vistas y 14 compartidos) cumple el patrón.

Reglas desde hoy (todas las piezas nuevas):
1. **Gancho = público + número** en la portada o los primeros 2 s: "Si cobras por quincena: 3 reglas…", "5 rumores del
   aguinaldo que te van a mandar por WhatsApp". Nada de títulos genéricos.
2. **Pensado para mandárselo a alguien**: el cierre nombra a la persona exacta ("al grupo de la familia", "a tu roomie").
   Los compartidos/envíos son la señal que más reparte a gente que no te sigue (Mosseri; patrón de samaniego).
3. **Del momento**: fecha o noticia de esta semana (aguinaldo hasta el 20-dic, Buen Fin, salario mínimo 2027 en diciembre).
4. **Pregunta abierta al final** que cualquiera puede contestar ("¿qué rumor te llegó?").
5. **Series nuevas**: "Victoria verifica" (rumores de dinero con veredicto y artículo de la ley; 1-2 por semana cuando
   haya rumor real; c70 la estrena) y "¿Cuántos días de salario mínimo cuesta…?" (comparaciones con CONASAMI/INEGI).
6. En Instagram, con menos de 50K seguidores, el Reel (video) alcanza más que el carrusel en fotos: las fotos del feed son
   extra, nunca en lugar del Reel.
No se sabe por qué los carruseles de TikTok bajaron de 350-650 vistas (octubre) a ~90 (noviembre); TikTok dice que los
seguidores y los éxitos previos no cuentan directo. Hipótesis: los de noviembre son menos útiles para mandar. Se mide.

## Clonar al ganador (Rodrigo, 12-nov-2026: "el 1 me encanta… tenemos que seguir subiendo")

- **Ganador** = una publicación que en alguna red saca **5 veces la mediana** de esa red y al menos **1,000 vistas**. `scripts/salud.py` lo detecta solo (área "Ganadores") y lo marca como AVISO hasta que tenga sus clones.
- **Qué se hace**: en las siguientes 72 h salen **3 variantes con la MISMA estructura** (mismo formato, mismo número de diapositivas, mismo tipo de gancho y portada, mismo cierre), cambiando solo el tema por otro de la temporada. Cada una lleva `"clon_de": "<id del ganador>"` y pasa la segunda revisión de datos como cualquier carrusel. Van primero en `config.json → prioridad_carruseles`.
- **Primer caso**: c16 "Aguinaldo 2026 en 5 datos para guardar" (3,903 vistas en TikTok contra una mediana de 197) → clones de Buen Fin, finiquito e ISR del aguinaldo, "en 5 datos para guardar".
- **Si un clon también gana**, se clona el clon: la estructura que funciona se vuelve serie.
- **Volumen**: se sigue subiendo todo (largos, recortes, carruseles). El volumen da más boletos; clonar al ganador hace que cada boleto tenga mejores probabilidades. El algoritmo decide post por post por la reacción de las primeras personas, no por insistencia.

## Fuera de la caja: series para hacernos virales (Rodrigo, 12-nov-2026: "piensa fuera de la caja… vamos por todo… que los temas sean TOP")

Todo con datos comprobados en fuente oficial y segunda revisión, como siempre. Cada serie se mide; la que gane se clona (regla del ganador).

1. **"¿Cuánto cuesta REALMENTE…?"** (9/10). Lo que la gente sueña o presume, con la cuenta completa: una boda, unos XV años, un depa en la CDMX, mantener un Rottweiler al año (con Capital), un iPhone a meses con CAT, una casa con Infonavit, vivir solo con un sueldo. Curiosidad + se comparte + da para pelear en comentarios. Formato: carrusel "5 datos" (el que ganó) + Reel de texto con Victoria haciendo algo relacionado.
2. **"Hago tus cuentas"** (9/10). Victoria toma un comentario real (solo ciudad, sueldo y renta; nunca el nombre ni la cuenta de la persona) y hace sus números en pantalla: "Ganas 14 mil en Guadalajara y pagas 6 mil de renta: así quedan tus números". Premia comentar y cada video pide el siguiente. Son CUENTAS, nunca historias inventadas.
3. **Cuenta regresiva con fecha legal** (8/10). "Faltan N días para que te paguen el aguinaldo" (20-dic), luego cuesta de enero, PTU (mayo), declaración anual (abril). Una pieza al día con un dato distinto; la fecha crea urgencia y regreso diario.
4. **Ciudad contra ciudad** (8/10). "¿Te alcanza en CDMX, Monterrey o Guadalajara?" con rentas oficiales (ENIGH/INEGI). El orgullo de ciudad dispara comentarios.
5. **Mito o verdad con postura** (7/10). Desmentir frases virales de dinero ("con el aguinaldo pagas tus deudas", "el Buen Fin siempre es más barato") con el dato oficial. Postura clara, nunca contra una persona.
6. **Victoria es IA y lo usa** (7/10). "Soy IA: no me da pena decirte cuánto ganas" / "No tengo jefe, pero tú sí: esto te debe". La etiqueta de IA como gancho, no como disculpa.
7. **Capital, el que cuida el dinero** (6/10). Remates cortos de Capital en los cierres ("Capital ya revisó su recibo: puras croquetas exentas"). Mascota = marca.

Ritmo: cada día al menos una pieza de 1, 2 o 3. Formato Reel de texto (`reel_texto.py`, sin Replicate) para todo lo que no necesite que Victoria hable; los videos donde habla, solo para lo que más rinde, dentro del tope de Replicate.

## Temas: de todo, no solo aguinaldo (Rodrigo, 12-nov-2026: "que hable de muchas cosas: éxito, consejos, parejas, finanzas, explicando qué es un estado de resultados, cómo leerlo, temas virales, cómo impactan los aranceles, el T-MEC, de todo")

Pilares que rotan cada semana (todo con fuente oficial y segunda revisión; opiniones marcadas como opinión; nunca recomendaciones de inversión):
1. **Dinero personal** (lo que ya funciona): aguinaldo, sueldo, renta, deudas, tarjetas, ahorro, Afore.
2. **Negocios explicados fácil**: qué es un estado de resultados y cómo leerlo, balance general, flujo de efectivo, margen, punto de equilibrio, cómo cobrar, facturar, RESICO.
3. **Economía que te pega**: aranceles y cómo suben precios, el T-MEC y su revisión, el tipo de cambio, la inflación, tasas de Banxico, el salario mínimo. Siempre con la noticia oficial del día y qué significa para tu bolsillo.
4. **Éxito y mentalidad con números**: hábitos de dinero, negociar sueldo, pedir aumento, emprender sin quebrar.
5. **Parejas y dinero**: quién paga, cuentas en pareja, bodas, divorcio y bienes.
6. **Temas virales**: lo que esté en tendencia esa semana con un ángulo de dinero.
