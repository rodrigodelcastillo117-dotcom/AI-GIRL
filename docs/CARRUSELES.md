# Carruseles (los días sin video)

Un día sale video de Victoria y al siguiente un carrusel: presencia diaria sin gastar créditos de
video. Instagram y TikTok los reciben como fotos (en finanzas los carruseles se guardan y se
comparten mucho, y TikTok empuja el modo foto); YouTube no tiene carruseles, así que ahí sale como
short con voz. El laboratorio dirá con datos si conviene más foto o video en cada red.

## Archivos

- `contenido/carruseles.json`: cada carrusel (portada, 3-8 datos, cierre, voces, SEO, fuente).
- `scripts/carrusel.py <id>`: dibuja `carruseles/<id>/00.png...` (1080x1350).
- `scripts/publer_carrusel.py <id> <cuando_utc>`: lo programa en Instagram y TikTok (`--borrador`
  lo deja en Publer sin salir). Instagram va como `"type": "photo"` con varias fotos: Publer
  rechaza `"carousel"` (probado 30-oct-2026).
- `scripts/carrusel_video.py short <id>`: short de máximo 57 s para YouTube + título, descripción y
  etiquetas; después `youtube.py subir carruseles/<id>/short.mp4 "$(cat titulo.txt)" descripcion_youtube.txt <cuando> --tags tags_youtube.txt` y `youtube.py playlist <video_id> <clave>` (PIPELINE 7b).
- `scripts/carrusel_video.py largo <salida> <id>...`: une carruseles en un video largo. Vertical
  para TikTok e Instagram (más de 1 minuto: TikTok solo paga videos de más de 1 minuto) y
  `--horizontal` para YouTube. Cada mes, los carruseles del mes en uno: "Todo lo de <tema> en 5 minutos".

Las fotos se vuelven a dibujar igual desde el JSON (las imágenes de Wikimedia o IA se guardan en
`assets/imagenes/`), así que sirven para el video largo cuando se necesite.

## Portada: siempre Victoria, siempre distinta

- `"foto": "auto"` toma la foto más nueva de `assets/fotos/` que ningún carrusel usó. Cada video
  deja ahí su foto base (PIPELINE paso 3), así que hay una nueva cada 2 días.
- Solo Victoria: pelirroja, ojos verdes, con Capital. Nunca otra mujer (hubo una rubia en OpenArt:
  no se usa).
- Si no queda foto sin usar: generar una con `nano-banana-2` (30 créditos) con el prompt del paso 3
  en una locación de lujo que no se haya usado, y guardarla en `assets/fotos/`.

## Fondo de los datos: un lugar de lujo distinto en cada carrusel

`"fondo": "auto"` toma de `assets/fondos/` el lugar menos usado (yate, jet, palco, restaurante...),
desenfocado y oscurecido para que el texto se lea. Para estrenar fondos: `nano-banana-2` 9:16 de un
lugar de lujo vacío, sin gente ni logotipos (30 créditos).

## Cómo se escribe uno

1. **Gancho de portada** con las plantillas que sí sirven a Victoria (`GANCHOS.md`): "Si haces esto
   con tu dinero, haz esto en su lugar", "El mito sobre ___", "Por qué tu ___ no funciona", o una
   cifra concreta ("Si ganas $15,000 al mes, te toca mínimo $7,500"). Nunca primera persona inventada.
2. **3 a 8 datos**, uno por diapositiva, cada uno con su fuente (regla 7). Título corto que se lee
   en 1 segundo; texto de máximo 30 palabras.
3. **Cierre** que pide guardar, mandar o comentar (lo que más mueve un carrusel) y la guía gratis.
4. **Voces** cortas: el short no pasa de 57 s (unas 130 palabras en total).
5. **SEO** como los videos (`docs/SEO.md`): `seo.palabra_clave` al inicio del título y del pie,
   `titulo` de máximo 45 caracteres, `tags_concretas`, 4 `hashtags` del tema (se suman los de marca:
   Instagram queda en 5, TikTok en 7) y 3-4 `preguntas` que la gente escribe.
6. **El día que sale**, antes de programarlo: dibujarlo y ver la hoja de diapositivas (texto cortado,
   portada sin Victoria, foto repetida). Si algo falla, se corrige; nunca se publica sin verlo.
7. **Revisión antes de `listo`**: un segundo agente compara cada dato con su fuente y lee las
   diapositivas dibujadas (texto cortado, faltas, números que no cuadran). Solo entonces `listo`.

## Música

TikTok le pone música automática al carrusel (`auto_add_music`). Los sonidos en tendencia de
Instagram y TikTok solo se pueden poner a mano desde la app: ninguna API los da. Si Rodrigo quiere
un sonido en tendencia, lo pone él al publicar desde Publer o la app.
