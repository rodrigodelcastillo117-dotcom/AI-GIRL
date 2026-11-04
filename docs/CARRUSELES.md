# Carruseles (TikTok todos los días; Instagram y YouTube los días sin video)

**Regla de Rodrigo (2-nov-2026), por los datos de la primera semana:** en TikTok los carruseles en fotos llegaron
a ~500 personas cada uno y los videos a ~100; en Instagram el Reel del carrusel c03 llegó a 28 y los carruseles en
fotos a 5-9. Por eso:

| Día | TikTok | Instagram | YouTube |
|---|---|---|---|
| Con video | el video + **un carrusel en fotos** a otra hora (3 h o más) | el video | el video + **short de carrusel** a 3 h o más (prueba del 4 al 17 de noviembre) |
| Sin video | un carrusel en fotos | el carrusel en fotos **+ su video como Reel** (2 h o más después) | el short del carrusel |

- Prueba en YouTube (Rodrigo, 3-nov-2026; `config.json → prueba_youtube_carrusel_diario`): los días con video también
  sube un short de carrusel (el mejor de TikTok que no haya salido ahí). Al terminar se compara si los videos de
  Victoria perdieron vistas (antes: 600-690 por video); si bajan, se quita.
- TikTok gasta un carrusel diario: va primero el de temporada que esté en su ventana y luego el orden del archivo.
- Instagram y YouTube, los días sin video, suben **el carrusel al que mejor le fue en TikTok** (vistas medidas, 20 h
  o más después de salir ahí) que aún no hayan subido; los de temporada primero porque caducan. Si ninguno se ha
  probado en TikTok, el mismo de TikTok de hoy. TikTok funciona como laboratorio gratis para Instagram.
- `python scripts/aprender.py auditar` lo decide (`auditoria.json → decision.carruseles`, con los comandos listos)
  y avisa cuando quedan menos de 5 para TikTok: entonces se escriben 5 nuevos con datos comprobados y su segunda
  revisión, igual que siempre.

## Archivos

- `contenido/carruseles.json`: cada carrusel (portada, 3-8 datos, cierre, voces, SEO, fuente).
- `scripts/carrusel.py <id>`: dibuja `carruseles/<id>/00.png...` (1080x1350).
- `scripts/publer_carrusel.py <id> "ig=<hora>,tt=<hora>"`: lo programa en fotos en Instagram y TikTok, cada uno a
  su hora de la prueba de horarios; con una sola red (`"tt=<hora>"`) solo en esa. Guarda `publica_utc_por_red`,
  `publica_utc` y el estado `programado` en el carrusel (`--borrador` lo deja en Publer sin salir). Se niega si choca:
  Instagram, una publicación por día; TikTok, un carrusel por día y a 2 h o más del video. Instagram va como
  `"type": "photo"` con varias fotos: Publer rechaza `"carousel"` (probado 30-oct-2026).
- **Portada del Reel distinta** (Rodrigo, 4-nov-2026: en el perfil de Instagram el carrusel y su Reel se veían como
  el mismo post repetido): `carrusel.py` dibuja además `00r.png` con otra foto de Victoria (`portada.foto_reel`, la que
  lleva más tiempo sin salir), el título de SEO (o `portada.titulo_reel`) en una franja dorada abajo y la cara libre;
  `carrusel_video.py short` arma `reel.mp4`, que abre con esa portada, y `--reel` sube ese.
- `scripts/publer_carrusel.py <id> --reel auto`: el `short.mp4` del carrusel como Reel de Instagram, el día de su
  carrusel en fotos, en la franja más fuerte de ese día a 2 h o más de lo demás (guarda `reel_ig`; se mide como `igr`
  y no cuenta en la prueba de horarios). Lleva el mismo primer comentario que el carrusel.
- `scripts/carrusel_video.py short <id>`: short de máximo 57 s para YouTube, con la voz clonada de Victoria (`voz_victoria.py`: cada frase se
  transcribe y se repite si no dice lo que debe; nombres en inglés en `voz` como suenan, "Uórren Bófet") + título, descripción y
  etiquetas; después `youtube.py subir carruseles/<id>/short.mp4 "$(cat titulo.txt)" descripcion_youtube.txt <cuando> --tags tags_youtube.txt` y `youtube.py playlist <video_id> <clave>` (PIPELINE 7b).
- El video del carrusel (`short.mp4`) va a YouTube y, como Reel, a Instagram. A TikTok nunca: ahí el carrusel va en
  fotos (Rodrigo, 2-nov-2026; la regla del 31-oct de "solo YouTube" quedó atrás por los datos del Reel de c03).
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
- Si no queda foto sin usar, `carrusel.py` repite la que lleva más tiempo sin salir (nunca una de los últimos 3
  carruseles): TikTok gasta un carrusel diario y los videos dejan una foto cada 2 días. Solo si sobran créditos,
  generar una nueva con `nano-banana-2` (~20 créditos) con el prompt del paso 3 y guardarla en `assets/fotos/`.

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
3. **Cierre:** el título pide guardar o comentar; el texto lleva **a quién mandárselo** (alguien concreto) y
   **siempre la razón para seguir**: "Sígueme: cada día, un dato de dinero que sí sirve en México." (Rodrigo,
   2-nov-2026: en la primera semana los carruseles llegaron a ~1,500 personas en TikTok y los seguidores no
   subieron; nadie sigue si no le dices qué gana). La `voz` del cierre termina en "y sígueme". La guía gratis ya no
   va en la diapositiva (va en el primer comentario y en la bio): tres llamados en una diapositiva se estorban.
   Sin emoji en las diapositivas (la letra no los tiene; `carrusel.py` los quita).
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
