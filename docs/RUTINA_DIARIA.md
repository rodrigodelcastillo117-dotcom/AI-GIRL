# Rutina diaria de VictoriatheCEO (6:37, hora de México)

La tarea programada diaria solo dice "sigue docs/RUTINA_DIARIA.md". Todo lo que hace está aquí, en el repo, para que se
pueda mejorar con un commit (12-nov-2026). Lo más nuevo va primero.

## 000. VICTORIA HOY — TODOS LOS DÍAS, sin excepción (Rodrigo, 12-nov-2026: "cada día noticias relevantes de México y el
mundo… la subes a las historias de Victoria, que te mande a una página… cómo afecta al cliente. Hazlo digerible. TODOS LOS DÍAS")
1. Busca (WebSearch) lo que movió el dinero de la gente en México y el mundo en las últimas 24-48 h: inflación, tasas
   (Banxico, Fed), peso/dólar, gasolina, salarios, SAT, Profeco, bancos, fechas que importan (aguinaldo, Buen Fin...).
2. Escoge 3 a 5. Cada una con DOS fuentes que digan lo mismo (si no hay dos, no va). Cifras tal cual las da la fuente;
   haz tú las cuentas de "cómo te afecta" y compruébalas con python.
3. Escribe contenido/noticias/<AAAA-MM-DD>.json (formato en scripts/noticias.py): qué pasó / cómo te afecta / qué hacer,
   frases cortas, de tú, lenguaje neutro. "Qué hacer" = hábito (comparar, revisar, esperar), nunca un producto, banco
   o inversión. Un "dato del día" con su cuenta y un cierre de Victoria.
4. `python3 scripts/noticias.py pagina` y `python3 scripts/noticias.py historia`, commit y push.
   HISTORIA CON ENLACE (Rodrigo, 12-nov-2026: "mete el link… que le puedan picar"; eligió subirla él): la API de
   Instagram NO deja poner el sticker de enlace. Mándale a Rodrigo con SendUserFile (status proactive) la imagen
   sitio/public/historias/<fecha>.jpg con el texto: "Historia de hoy: súbela con sticker de enlace →
   https://victoriatheceo.vercel.app/hoy?ref=ig-historia". Y con send_later a las 10:00 (America/Mexico_City) el
   respaldo: "cd /home/user/ai-girl && git pull -q && python3 scripts/noticias.py publicar --si-falta" (si él ya la
   subió, no publica nada; si no, la sube sin sticker para que nunca falte).
5. Si algo falla, la página va igual y se lo dices a Rodrigo en el resumen. Nunca inventes una noticia para llenar.

## 00000. ESTRATEGIA POR RED (13-nov-2026) — leer docs/ESTRATEGIA_POR_RED.md y aplicar lo marcado "aplicar"
Resumen para la rutina (manda sobre lo de abajo si chocan; mismo volumen, mismo formato de subir carruseles):
- TikTok: la firma/serie en el texto ya sale sola (publer_carrusel.py). La cola se arma en SERIES; usa preguntas.json
  para carruseles "Me preguntaron: gano $X…". Cierre de fechas: "guárdalo y mándaselo a tu familia" + fuente.
- YouTube: en todo short/largo de pensión, aguinaldo o retiro la razón para suscribirse es "cada vez que el IMSS o el
  Bienestar cambien fechas o montos, te lo explico aquí"; los shorts que tengan largo del tema terminan con "el video
  completo está en el canal" y su enlace va en la descripción y en el comentario propio. Miniatura: cara + 3-4 palabras
  + cifra/fecha + CONFIRMADO o RUMOR.
- Instagram: el llamado único de los Reels pasa a "mándaselo a quien…"; "Comenta GUÍA" solo en 1 de cada 3.
- Facebook: sin "Comenta SÍ o NO" ni "escribe…" (Meta lo castiga): cierre "Mándaselo por WhatsApp a quien…", máximo 3
  hashtags. Si el texto de Facebook sale igual al de Instagram, quítale la línea de "Comenta…" antes de programar.
- YouTube y Facebook de pensión/retiro: Victoria habla de USTED (Rodrigo, 13-nov). TikTok e Instagram: de tú.
- LUNES: producir el largo de pensión de la semana (REPLICATE_AUTORIZACION=largo-pension, tope $20/mes) y programarlo
  el MIÉRCOLES 18:00 en YouTube y Facebook, con 2-3 shorts de avance ("el video completo está en el canal").
- MIÉRCOLES: sketch de TikTok de la semana (REPLICATE_AUTORIZACION=sketch-tiktok, tope $8/mes; ver ESTRATEGIA_POR_RED).
- Mismo tema, PRIMERA LÍNEA distinta por red (no el mismo texto de arranque en las cuatro): TikTok = conflicto
  ("Gana $X y no le alcanza: te explico"), Instagram = identificación ("Si te pasa esto con tu aguinaldo…"),
  YouTube = pregunta ("¿Cuánto le toca de aguinaldo si cobra pensión?"), Facebook = historia corta con consecuencia.
- Métrica del resumen diario: seguidores/suscriptores NETOS por red y SEGUIDORES POR CADA 1,000 VISTAS de la semana (contenido/seguidores.json), antes que vistas.

## 0000. PLAN DE CRECIMIENTO — desde el 13-nov (Rodrigo, 12-nov-2026: "aplícalo todo desde mañana y historias también
en Facebook"). Mismo volumen de siempre; esto cambia QUÉ va primero, no cuánto se publica.
1. **Historia en Facebook todos los días**: después del paso 4 de Victoria Hoy, `python3 scripts/noticias.py facebook`
   (sube la imagen del día como historia de la página; verifica con GET /{página}/stories que salga `published`).
   Sin sticker de enlace (la API no lo da): la imagen ya trae la dirección escrita.
2. **Serie "Tu sueldo, tu aguinaldo" en TikTok, una por día, primero que todo**: c78 → c85 en orden (13 al 20-nov).
   Es el primer carrusel de TikTok del día; los demás carruseles del día van después. Al acabarse, se escribe la
   siguiente serie de sueldos reales (con revisión de cifras por un segundo agente, como siempre).
3. **Cada short de YouTube termina con una razón concreta para suscribirse**, nunca un "suscríbete" pelón: en el cierre
   hablado/pantalla y en la primera línea de la descripción, p. ej. "Suscríbete: cada semana hago las cuentas de un
   sueldo real" o "Suscríbete: te aviso cuándo cae tu aguinaldo y cuánto te quitan". Una sola razón por short.
4. **YouTube prioriza a la gente de 55+** (es la que más ve el canal según YouTube Analytics): Afore, pensión, retiro,
   Ley 73 / Ley 97, finiquito, aguinaldo, ISR. Al elegir qué short o largo va a YouTube, esos temas primero; los de
   tarjeta de crédito, Buen Fin y apps van más a TikTok/IG. Pensión y Afore: cifras solo de IMSS/CONSAR/DOF, dos
   fuentes, cuentas con python.
5. **"Victoria verifica" 2 veces por semana (martes y viernes)**: toma un dato de dinero que se está moviendo en redes
   (WebSearch / tendencias.json), lo checa contra la fuente oficial y dice VERDAD / FALSO / A MEDIAS con la fuente en
   pantalla. Formato carrusel o reel de texto (no gasta Replicate). Si no hay dos fuentes oficiales, no se publica.
   Nunca nombra ni exhibe a una persona: se verifica el dato, no al que lo dijo.
6. Al medir (tablero.py / estadisticas.py), compara cada semana: suscriptores ganados por short con razón vs. antes,
   y seguidores de TikTok los días de la serie. Lo que no mueva el número en 2 semanas se cambia y se le dice a Rodrigo.

## 00. 13-NOV (Rodrigo)
- LC1 (22-nov) y LC2 (26-nov): autorizados ≈$8 (config.json → replicate.autorizaciones.largos-lc). Correr voces y
  tomas con REPLICATE_AUTORIZACION=largos-lc. Fotos de las tomas con luz de día y manos vacías.
- Miniaturas: SIN Test & Compare. Elige tú la mejor (la de largo.py; Canva solo si sale mejor) y no se lo recuerdes.
- Meta Business: Rodrigo ya aceptó el permiso (era para MUSE). Pendiente suyo: enlace de YouTube en la bio de IG.

- Panel (12-nov): tablero.py ahora corre scripts/estadisticas.py (vistas y seguidores por día, mejores días/horas/temas,
  comparativas, YouTube Analytics, dinero y créditos) y guarda una foto diaria de seguidores en contenido/seguidores.json:
  NO te saltes tablero.py ni un día, o se pierde el dato diario. Regla de Rodrigo: lo no esencial, SIEMPRE cerrado.
- Vercel gratis = 100 publicaciones al día (se acabaron el 12-nov). Junta los cambios: un push al final de la rutina.
- LC2: Rodrigo dijo "acaba el LC2" (autorización largos-lc ampliada a $10.5).

## 0. LO NUEVO DEL 12-NOV NOCHE (manda sobre lo de abajo si chocan)

Rodrigo (12-nov, noche): "volumen como lo teníamos… toma en cuenta lo importante de MUSE… LA MEJOR CALIDAD, que se
muevan, animados, movimiento, videos largos, miniaturas top, tags, hashtags, todo… descripciones TOP… todo real".

**A. Shorts de Victoria hablando = formato escena** (docs/PIPELINE.md → 4b). Victoria habla a cámara en un lugar real
del repertorio; a media pieza SE CALLA y hace la acción del lugar con su sonido real (pausa de 2-3 s); luego sigue
hablando. Ambiente del lugar bajito debajo de todo. Pasos:
1. Foto hablando: `REPLICATE_AUTORIZACION=shorts-escena python3 scripts/foto_escena.py <escena> "<qué hace>" [perro]`.
   SIEMPRE con luz de día pareja en la cara (nada de atardecer, contraluz ni interiores oscuros: con eso p-video-avatar
   cambió la cara y el pelo en M2 y M4) y de pecho para arriba (si sale más abierta, recórtala 9:16 centrada en la cara
   antes de pagar). Escenas buenas para hablar: café, calle, cocina, yate de día, coche de día. Las de atardecer o
   interiores oscuros (terraza, bar, restaurante, lectura, alberca, helipuerto) solo como ACCIÓN.
2. Voz: `REPLICATE_AUTORIZACION=shorts-escena $VOZ_PYTHON scripts/voz_guion.py <id> videos/video-<id>-voz.mp3`
   (15-30 s; si pasa de 27 s, quita una frase antes de pagar el video).
3. Video: `REPLICATE_AUTORIZACION=shorts-escena python3 scripts/video_replicate.py <foto> <voz> videos/video-<id>.mp4 "<movimiento>"`
   (en el movimiento: "Her face, green eyes, freckles and copper-red hair stay exactly the same in every frame", el
   fondo con movimiento suave y la luz de día).
4. Todo lo demás de un jalón: `python3 scripts/armar_escena.py <id>` (revisión completa, pausa con acción y sonido,
   naturalizar, subtítulos, título, cierre). Luego MIRA `videos/qa/<id>-cuadros.jpg`: si en algún cuadro cambia la cara
   o el pelo deja de ser cobrizo, se tira (un solo reintento, con otra foto de día).
5. Pago: los shorts hablados salen de la autorización escrita de Rodrigo `shorts-escena` (config.json → replicate →
   autorizaciones, tope 15 USD, el freno lo respeta). Si se acaba, los demás salen como Reels de texto y se le avisa.

**B. Reglas de MUSE para Instagram y Facebook** (docs/MUSE_auditoria_2026-11-12.md):
- El gancho manda (salto de Reels 50-78 %): cada reel empieza con el número y el dinero en pantalla
  (`texto_pantalla`, p. ej. "$9,309 MÁS CARO"); las cifras largas se dicen redondeadas y la exacta va en pantalla.
- Un solo llamado por pieza: guardar O compartir, nunca los dos, nunca "link en bio". En el plan: `llamado_cierre`
  (sale en el cierre del video) y un pie con UNA línea de llamado (si seo.py pone varios, déjalo en uno).
- Pregunta de respuesta obligada en comentarios ("¿1, 2 o 3?", "Comenta SÍ o NO", "Comenta el número").
- En Instagram nunca carrusel y reel del mismo tema el mismo día (config.json → instagram_temas_del_dia).
- Reel = traer gente nueva; carrusel = que lo guarden.
- Rodrigo eligió MANTENER EL VOLUMEN (no bajar a 4 por semana): el ritmo de abajo sigue igual.
- Ya programado de MUSE: M1 Buen Fin (12-nov 12:51), M2 aguinaldo (13-nov), c77 carrusel tarjeta (16-nov), M4 Afore
  (18-nov). No los dupliques. El 19-nov hay medición contra la línea base (tarea programada aparte).

**C. Miniaturas, títulos, descripciones y hashtags** (docs/MINIATURAS_Y_SEO.md, investigado el 12-nov): seguirlo en
todo largo y en todo short (sin Test & Compare desde el 13-nov: una sola miniatura, la mejor).

**D. Sonido real**: toda escena tiene `assets/broll/sonido/<escena>-ambiente.m4a` y el sonido de su acción
`<clip>.m4a`; insertar_accion.py los usa solos. Escena nueva = `sonido_broll.py` (ambiente y acción) antes de usarla.
El clip del estudio NO sirve como pausa (ella habla en el clip).

## 1. Todo lo demás (igual que antes)

El resto de la rutina sigue en el texto de la tarea programada diaria (6:37). Si algo de aquí arriba choca con eso,
gana lo de arriba.
