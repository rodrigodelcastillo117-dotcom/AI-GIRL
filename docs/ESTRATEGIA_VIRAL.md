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
