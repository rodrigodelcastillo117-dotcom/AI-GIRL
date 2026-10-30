# Pipeline automático de Victoria

La tarea programada corre **todos los días a las 6:37 a.m.** (hora de México) dentro de la
conversación de Claude donde se armó el proyecto (ahí están las claves y el permiso de push).
Todos los días **verifica y audita**; **cada 2 días publica** un video (el 30-oct-2026 se probó diario y se regresó: los créditos del plan Plus alcanzan para cada 2 días) en Instagram, TikTok y
YouTube Shorts, en la franja que toque de la prueba de horarios. Publica directo, sin aprobación
humana. Regla principal: **si algo no pasa el control de calidad, o si el control no se pudo
hacer, NO se publica** y se registra (regla 8).

Antes de todo, lee `docs/REGLAS_APRENDIDAS.md` (34 reglas medidas en 4 canales). Se aplican
todas; cuando los datos propios digan otra cosa, mandan los propios.

## 0. Preparación

1. El repo debe estar en `/home/user/ai-girl` con permiso de escritura (`add_repo` con
   `access: "push"` para `rodrigodelcastillo117-dotcom/ai-girl`, luego `git clone`). Si `add_repo`
   no existe en la sesión, clónalo por HTTPS público y sigue: publicar no depende del push.
2. Entorno de Python para subtítulos:
   `python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q faster-whisper num2words mediapipe opencv-python-headless edge-tts pillow`
   y `apt-get install -y -q libegl1 libgles2` (MediaPipe los necesita para `qa_sync.py`).
   Con faster-whisper, decodificar el audio con ffmpeg (ver `scripts/transcribir.py`); la versión
   de PyAV del paquete no acepta rutas de archivo directo.
3. Verificar `PUBLER_API_KEY` en el entorno (`env | grep -c PUBLER_API_KEY`). Si falta: no generar
   nada, reportar y terminar.
4. `openart_account_get`: si hay menos créditos que `creditos_minimos_para_correr`
   (`contenido/config.json`), no generar nada, reportar y terminar.

## 1. Verificar, medir y auditar (todos los días)

```
python scripts/aprender.py medir     # comprueba en cada red que lo programado salió y guarda vistas
python scripts/aprender.py auditar   # qué gana, qué pierde, si hoy toca publicar, hora y video
```
- `medir` solo marca un video como `publicado` cuando lo ve publicado en Instagram, TikTok y
  YouTube (regla 34). Si algo no salió, lo dice en `contenido/verificacion.json` con el estado
  exacto: eso va al reporte. Nunca digas "publicado" sin esa comprobación.
- `auditar` escribe `contenido/auditoria.json`: `ranking` (índice de cada característica: 1.0 es
  normal, 1.2 o más gana, 0.8 o menos pierde, con al menos 3 videos; los días, con 15),
  `decision` (`toca_publicar`, `publicar_hoy`, `horarios` y `cuando` por red, `prueba_horas`, siguiente video a
  generar y `cambios_sugeridos`), `reglas_vigentes` (reglas con cifras de los datos propios) y
  `alertas`.

## 1e. Comentarios de YouTube (todos los días)

`python scripts/comentarios.py pendientes` y contestar cada uno con `responder <id> "texto"`,
siguiendo las reglas del propio script (corto, voz de Victoria, sin recomendaciones de inversión,
enlace a la calculadora o la guía si aplica; spam e insultos no se contestan). Más conversación =
más alcance. Instagram y TikTok los contesta Rodrigo en la app.

## 1a. Si hoy NO toca publicar

Sale un **carrusel** (`docs/CARRUSELES.md`): el primero en estado `listo` de
`contenido/carruseles.json` (los de temporada, si su `ventana` incluye hoy, van primero). Se publica
a la hora de cada red (`decision.cuando`): Instagram y TikTok como fotos (`publer_carrusel.py`) y YouTube como short
(`carrusel_video.py short` y `youtube.py subir`). Si no queda ninguno `listo`, escribe 5 nuevos
(reglas en `CARRUSELES.md`). Luego pasos 8 (registro), 10 (centro) y 9 (reporte de una línea). Excepción: si no hay ningún
video `listo_para_publicar`, genera uno hoy (pasos 1b a 6) y déjalo listo: así el día de publicar
ya está hecho y la franja de las 8:00 nunca se pierde.

## 1b. Si hoy SÍ toca publicar

1. Publica el video `listo_para_publicar` (`decision.publicar_hoy`) a la hora de **cada red**
   (`decision.cuando`, paso 7). **Prueba de horarios por red:** Instagram, TikTok y YouTube salen a
   horas distintas y cada red rota por sus propias 5 franjas (`config.json → prueba_horas.franjas_por_red`,
   sacadas de las gráficas de engagement por red que mandó Rodrigo; entre las menos probadas va primero
   la más fuerte para ese día, `prueba_horas.orden_por_dia`) hasta tener 4
   publicaciones en cada una; `aprender.py auditar` compara cada red por franja y por día de la semana
   (videos y carruseles, cada formato contra su propia mediana) y fija la ganadora de cada red
   (`prueba_horas.ganadoras`), que se usa 4 de cada 5 veces. Publer:
   `publer.py publicar ... "ig=<decision.cuando.ig>,tt=<decision.cuando.tt>" ...`; YouTube:
   `youtube.py subir ... <decision.cuando.yt>`. Guarda en el plan `publica_utc_por_red`
   (`{"ig", "tt", "yt"}`) y `publica_utc` = la más tarde de las tres. Nunca se tira un video (regla 31).
2. Si no había video listo, genera el de `decision.video_id` (pasos 2 a 6) y publícalo hoy.
3. Después genera el siguiente (`decision.video_id`) y déjalo como `listo_para_publicar`: así
   siempre hay uno en reserva.

Al generar un video:
- Aplica `decision.cambios_sugeridos` (fondo, vestimenta, gancho o título que ganan), las
  `reglas_vigentes` y cada `regla` de `contenido/aprendizajes.json`, sin cambiar la idea ni la
  fuente. Si cambias el gancho, actualiza `subtitulos`, `palabras_clave`, `texto_post` y `seo`.
- El guion abre con el gancho en el segundo 0, sin saludo ni introducción (regla 23).
- Confirma que el `vestuario` no se repite en ningún otro video.
- Anota en el video `"decision"` (copia de `auditoria.decision`) y `"mejoras_aplicadas"`.

## 1d. Video largo (cada 12 Shorts publicados)

Solo los días que NO toca publicar Short, para no encimar:
1. `python scripts/compilar.py preparar`: si hay 12 Shorts verificados como `publicado` que aún no
   están en un largo, crea `L01`, `L02`... en `plan.json → largos`, ordenados del que mejor rindió
   al que menos (el largo abre directo con el mejor, sin introducción: regla 23).
2. Escribe en ese largo su `texto_post` (primera línea única, el gancho del largo) y su bloque
   `seo` con las mismas reglas que los Shorts (`docs/SEO.md`), y su `pilar` (el tema que más se
   repite en sus 12 videos).
3. `python scripts/compilar.py armar L0N` (unos 5 minutos): horizontal 1920x1080 para YouTube (un
   vertical de menos de 3 minutos YouTube lo cuenta como Short), vertical para Instagram y TikTok
   (más de 1 minuto) y miniatura. Revisa 3 cuadros de cada uno (regla 8).
4. `python scripts/seo.py L0N /tmp/seo-L0N`: la descripción ya lleva los capítulos (0:00 ...).
5. Publica hoy a la hora `config.json → hora_largo`: YouTube con `youtube.py subir
   videos/largos/L0N-horizontal.mp4 "$(cat /tmp/seo-L0N/titulo.txt)" /tmp/seo-L0N/descripcion_youtube.txt
   <hora_utc> --tags /tmp/seo-L0N/tags_youtube.txt --miniatura videos/largos/L0N-miniatura.jpg --largo`;
   Instagram y TikTok con `publer.py publicar videos/largos/L0N-vertical.mp4 /tmp/seo-L0N/texto_redes.txt
   <hora_utc> "$(cat /tmp/seo-L0N/titulo.txt)"`.
6. Registra en el largo `estado: "programado"`, `publica_utc` y `publicacion.youtube` (el enlace
   /watch). `medir` lo verifica al día siguiente. Los archivos de `videos/largos/` no van al repo:
   se vuelven a armar con `compilar.py armar` cuando hagan falta.

## 1c. Escribir guiones nuevos (cuando quedan menos de 5)

Lee `docs/GUIONES_VIRALES.md`: cada guion cumple su lista de 10 puntos. Escribe 10 videos nuevos
al final de `plan.json → videos`, con todos los campos de los demás
(`id`, `estado: "pendiente"`, `pilar`, `duracion` en segundos según el tema y `guion` que cabe en ella (segundos × 2.33
palabras, tabla en `GUIONES_VIRALES.md`) dicho en español de México que abre con el gancho, `subtitulos` con dígitos, `palabras_clave`, `fuente` real, `locacion`,
`vestuario` nuevo, `accion`, `hora_publicacion: "rotacion"`, `texto_post` sin hashtags y `seo`
según `docs/SEO.md`, más `ganchos_alternativos` (las otras 2 primeras frases propuestas) y
`adn: {"tipo_gancho": "cifra|contradiccion|error|nombre|regla|dato|cita|pregunta|consejo|historia|mito"}`).
Cada video lleva `texto_pantalla` (gancho visual, ver `GANCHOS.md`). y `pregunta_comentarios`
(una pregunta concreta que la gente quiera contestar; va en el pie de las 3 redes).
Si es capítulo de una serie, `formato: "serie"` y `serie: {"nombre", "numero"}`: `aprender.py`
la mete un video sí y uno no, en orden.
Después corre `python scripts/seo.py revisar`: tiene que salir sin errores.

Para mover un video ya programado: `python scripts/reprogramar.py <id> <hora_utc>` (mueve YouTube
y dice qué posts de Publer hay que mover a mano: Publer no deja cambiar la hora por API y su
borrado masivo es peligroso, nunca se usa).

- **Cada dato se comprueba antes de escribirlo** (regla 7): busca la fuente con WebSearch y no
  pongas cifras, fechas ni frases atribuidas que no encuentres. El título no promete más de lo que
  dice el video.

- **Temporadas** (aguinaldo, cuesta de enero, regreso a clases, PTU, declaración anual): videos con
  `"ventana": {"desde", "hasta"}` y `"llamado"` (`config.json → llamados`: su calculadora gratis va
  primero en la descripción, el pie y el comentario). `aprender.py` los publica primero cuando abre su
  ventana y nunca fuera de ella. Escríbelos con un mes de anticipación.
- 3 de 10 adaptan un tema o estructura que esté funcionando (`docs/INSPIRACION.md`,
  `contenido/referencias.json`; los lunes se actualiza con `search_viral_videos`). Nunca se copia texto.
- 2 de 10 son **entrevista** (ver "Formato entrevista" en el paso 3), casi siempre de emprendimiento.
- 3 de 10 son **videos puente** hacia la plantilla (`"puente_producto": true`, ver
  `docs/GUIONES_VIRALES.md → Monetizar`).
- 6 de 10 con lo que gana en `auditoria.ranking` (tema, tipo de fondo, vestimenta, gancho) y 4
  probando cosas nuevas o poco probadas: así el sistema no se queda atorado en un solo estilo.
- Locaciones: las de `assets/manifest.json` o nuevas descritas en `locaciones_nuevas`.
- Finanzas: principios generales, nunca recomendar una inversión concreta. Salud mental:
  bienestar, nunca consejo clínico.

## 2. Locación

- `assets/manifest.json` tiene las locaciones ya generadas (`cuartos`, `locaciones_lujo`,
  `locaciones_nuevas_generadas`). Si la del video no existe, generarla una vez con
  `nano-banana-2` `text2image`, 9:16, 2K, usando la descripción de `plan.json → locaciones_nuevas`,
  "photorealistic, empty, no people, no logos, no text, no watermark, camera at chest height with
  open space in the center for a person and a large dog". Revisarla, guardarla en
  `assets/loc-<clave>.png` y registrarla en el manifest bajo `locaciones_nuevas_generadas`.

## 3. Foto base

Al aprobarla, guarda una copia en `assets/fotos/video-<id>-<locacion>.jpg` (1200 px de ancho, JPG
calidad 88; bajar el PNG con `curl -A Mozilla/5.0`, la CDN rechaza otros clientes): es la portada
de un carrusel, así cada carrusel estrena foto de Victoria sin gastar créditos.

`nano-banana-2` `image2image`, 9:16, 2K, `visualReferences` en este orden:
hoja maestra de Victoria (`manifest.personaje.maestra`), Rottweiler (`manifest.perro`), locación.

Prompt:
```
Photorealistic vertical frame for a talking-to-camera video. The red-haired woman of Image 1
(EXACT identity: same face, vivid green eyes, long copper-red wavy hair, red lipstick, subtle light
freckles across nose and cheeks) in the location of Image 3 (same place, same light). She wears
<vestuario en inglés>. <accion en inglés>. The Rottweiler of Image 2 (same dog, same markings,
black leather collar with gold plate) is fully visible next to her. Medium shot, her face large
and sharp in the upper half, the dog's whole head visible. She looks straight into the lens with
a confident, magnetic expression. Elegant and classy, photorealistic, natural skin and fur
texture, no text, no logos, no watermark.
```

Revisar la imagen (descargarla y verla): cara de Victoria (pelirroja, pecas, ojos verdes), Capital
completo, vestuario correcto, manos y patas sin deformaciones. Si falla, repetir una vez.

### Formato entrevista (`"formato": "entrevista"` en el plan)

Victoria contesta una pregunta como en un clip de podcast: no sale ni se oye el entrevistador; la
pregunta va escrita en pantalla (`pregunta_pantalla`). Locación `estudio_entrevista`. En el prompt de
la foto base cambia la mirada y el encuadre:
```
... in the interview studio of Image 3 (same place, same light), seated in the velvet armchair, body
angled three-quarters, looking slightly off-camera to her right as if answering an interviewer who is
not in frame. A professional podcast microphone on a boom arm in front of her, not covering her face.
The Rottweiler of Image 2 lies at her feet, fully visible. Medium shot, cinematic studio lighting:
warm key light, soft fill, rim light on her hair, warm bokeh in the background. Calm, confident,
expert expression. Elegant and classy, photorealistic, no text, no logos, no watermark.
```
Y en el del video, en lugar de "She looks straight into the lens and speaks to the viewer":
```
She answers someone just off-camera to her right (the interviewer is never visible or audible),
eyes mostly on that person with brief natural glances, relaxed conversational hand gestures, ...
```
Victoria nunca cuenta anécdotas personales inventadas como si fueran reales: responde con una regla y
un caso real con fuente (regla 7).

## 4. Video

`wan3-0` `element2video`: `duration` = `decision.segundos` de `aprender.py auditar` (la `duracion`
del video en el plan, 10 a 25 s según el tema; ver `GUIONES_VIRALES.md`), `resolution: "720p"`, `aspectRatio: "9:16"`,
`audio: true`, `promptExtend: false`, `mode: "standard"`.
`visualReferences`: foto base, hoja maestra, Rottweiler y la voz
(`manifest.voz`, `type: "audio"`, `audioRole: "voice_reference"`).

Prompt:
```
Talking-to-camera vertical video in the scene of the first reference image (same place, same
outfit, same light). The woman is EXACTLY the red-haired woman of the second reference image:
identical face, vivid green eyes, long copper-red wavy hair, red lipstick, subtle light freckles.
The Rottweiler of the third reference image (same markings, black leather collar with gold plate)
stays next to her and FULLY INSIDE THE FRAME for the entire video. Medium shot. Static camera
with only a very slow, subtle lateral drift; NO zoom in, NO push-in. She looks straight into the
lens and speaks to the viewer in natural Mexican Spanish, confident, warm and magnetic, with clear
accurate lip sync and the same voice as the audio reference. She says exactly: "<guion>"
Soft room ambience, no music. Photorealistic, cinematic, elegant, no text on screen, no
subtitles, no logos.
```

Esperar con `sleep` en segundo plano (tarda 10-15 min) y consultar `openart_creation_get`.

## 5. Control de calidad (obligatorio)

1. Descargar el MP4.
2. Transcribir: `scripts/transcribir.py video.mp4 palabras.json` (modelo `small`, español).
3. `scripts/qa_audio.py palabras.json "<guion>" <similitud_minima_audio>` debe salir con 0.
3b. **Labios en sincronía:** `scripts/qa_sync.py video.mp4 sync.json` debe salir con 0. Mide la
   apertura de la boca cuadro por cuadro contra la fuerza de la voz y rechaza el video si la voz va
   atrasada o adelantada, si hay más de 1 s de voz con la boca quieta o de boca moviéndose sin voz.
   Detecta desfases de toda la pista (probado: 150 ms antes y 250 ms tarde los rechaza); no juzga
   si cada sílaba tiene la forma de boca exacta: eso se ve en la hoja de cuadros del punto 4.
4. Hoja de 6 cuadros (`ffmpeg ... fps=1/2,scale=240:-1,tile=6x1`) y verla: misma cara en todos
   los cuadros, **Capital visible en todos**, sin deformaciones, sin texto raro en pantalla.
5. Gancho en el segundo 0 (regla 23): en `palabras.json` la primera palabra debe empezar antes de
   0.4 s. Si empieza después, recorta el inicio (`ffmpeg -ss <inicio-0.05> -i video.mp4 -c:v libx264
   -c:a aac recortado.mp4`) y vuelve a transcribir.
6. Si falla cualquier punto: un solo reintento del video (paso 4). Si vuelve a fallar: marcar el
   video `"estado": "fallido"` con el motivo en `"qa"`, hacer commit y push, y terminar SIN publicar.
   Si una herramienta de revisión no corre (Whisper, ffmpeg, la hoja de cuadros), eso es un fallo,
   no un aprobado (regla 8).
7. **Aprendizaje:** si algo falló o salió notablemente mejor que antes, agrega un renglón a
   `contenido/aprendizajes.json` (`fecha_utc`, `origen`, `tipo`: tecnico, contenido o publicacion,
   `aprendizaje`, `regla` concreta para la próxima vez). No repitas una regla que ya existe.

## 6. Subtítulos

```
python scripts/frases_a_tiempos.py palabras.json frases.json tiempos.json   # frases = "subtitulos" del plan
python scripts/subtitular.py video.mp4 tiempos.json videos/video-<id>-SUBTITULADO.mp4 "<palabras_clave separadas por coma>"
```
Revisar 3 cuadros del video subtitulado: texto legible y sin tapar la cara.

Título fijo arriba (quien desliza sin sonido sabe de qué trata desde el segundo 0):
```
python scripts/titulo_pantalla.py videos/video-<id>-SUBTITULADO.mp4 "$(python -c "import json;v=[v for v in json.load(open('contenido/plan.json'))['videos'] if v['id']=='<id>'][0];print(v.get('pregunta_pantalla') or v.get('texto_pantalla') or v['seo']['titulo'])")" /tmp/titulo.mp4
cp /tmp/titulo.mp4 videos/video-<id>-SUBTITULADO.mp4
```
Revisar un cuadro: el título va en la franja de arriba (techo, cielo o pared) y no tapa la cara.

## 7. Publicar

1. `python scripts/seo.py <id> /tmp/seo-<id>` (si falla, corrige el bloque `seo` del video y
   repite): deja `titulo.txt`, `descripcion_youtube.txt`, `tags_youtube.txt`, `texto_redes.txt`,
   `texto_instagram.txt` y `texto_tiktok.txt` (publer.py usa el de cada red).
2. Hora: la franja que toca (paso 1b) en `America/Mexico_City`, convertida a UTC ISO
   (`2026-10-31T00:45:00Z`).
3. Instagram y TikTok: `python scripts/publer.py publicar <video> /tmp/seo-<id>/texto_redes.txt
   <hora_utc> "$(cat /tmp/seo-<id>/titulo.txt)"`. Hace una petición por red y espera cada job
   (regla 5); solo usa las cuentas de `config.json → cuentas_publer` (la de Instagram sigue con el
   nombre viejo "Nadie Te lo Explicó" en Publer). Si la API responde algo inesperado, consulta
   https://publer.com/docs, corrige `scripts/publer.py`, reintenta una vez y deja la corrección en
   el commit.
4. YouTube Shorts (sin Publer): `python scripts/youtube.py subir <video>
   "$(cat /tmp/seo-<id>/titulo.txt)" /tmp/seo-<id>/descripcion_youtube.txt <hora_utc> --tags
   /tmp/seo-<id>/tags_youtube.txt`. Comprueba que el canal sea `UCGyza9C58eMH3VnGgkMPr1A`
   (regla 1), sube en privado con hora de publicación (regla 2) y verifica que YouTube lo tenga así.
   Si responde `invalid_grant`, el permiso venció: repórtalo.
5. **Duplicados:** si `publer.py` o `youtube.py` responden `OMITIDO`, el post ya existía:
   regístralo como `programado` y no lo vuelvas a subir.
6. Que Publer acepte el job no es "publicado": la confirmación llega en el `medir` del día
   siguiente (regla 34). Cuando `medir` confirma un video, deja solo el primer comentario en YouTube
   con el enlace de la guía (`config.json → comentario_youtube`, regla 25); fijarlo es manual.

Embudo de ingresos: la página pública es `config.json → enlace_venta`
(https://victoriatheceo.vercel.app, carpeta `sitio/`). Ahí está la guía gratis y la plantilla de
paga. `seo.py` pone el enlace con `?ref=yt` en la descripción de YouTube y "enlace en mi perfil"
en Instagram y TikTok; la descripción de YouTube lleva también la plantilla (`enlace_producto`, que
abre la página en `#tablero`). El pago de Hotmart ya está activo (`config.json → pago_hotmart`); el
botón le agrega `?src=<red>` para saber de dónde vino cada venta. Las calculadoras gratis (`/aguinaldo`, `/pagar-deudas`...)
se generan con `python scripts/sitio.py`. Google Search Console está verificado con
`sitio/public/google7564e845b5da9769.html`: no se borra ni se renombra, o se pierde la verificación. Para activar la lista de correos se llena `CONFIG` en
`sitio/public/index.html`.

### 7b. Lista de reproducción de YouTube

Después de cada subida a YouTube (video o short de carrusel):
`python scripts/youtube.py playlist <video_id> <clave>`, con la clave que da
`youtube.clave_playlist(video)`: el nombre de la serie, `aguinaldo`, `negocios`, `mente` o `finanzas`.
Las listas hacen que se vea uno tras otro (más tiempo en el canal) y salen en la búsqueda. Si la
lista no existe, se crea pública y su id se guarda en `config.json → playlists_youtube`.

## 8. Registro

En `plan.json`, en el video: `"estado": "programado"`, `"publica_utc"`, `"archivo"`,
`"publicacion": {"youtube": "<enlace del Short>"}` (el centro lo usa para leer sus vistas),
`"openart": {"foto": id, "video": id}`, `"creditos"` usados, `"qa"` (`{"similitud": 0.9x, "notas": ...}`).
Copiar el MP4 final a `videos/`.

Agrega un renglón a `contenido/ejecuciones.json`: `fecha_utc`, `tipo` (generar o publicar),
`video_id`, `resultado` (programado, fallido u omitido), `detalle` en una frase,
`creditos_usados` y `creditos_restantes` (de `openart_account_get` al terminar).

Incluye `contenido/metricas.json`, `contenido/verificacion.json`, `contenido/auditoria.json` y
`contenido/config.json` (la prueba de horarios guarda ahí la franja ganadora) en el commit.

Commit y push a `main`. Si el push falla, dilo en el reporte: lo publicado ya quedó publicado.

## 10. Centro de mando (Vercel, proyecto `victoria-centro`)

1. `python scripts/tablero.py` (con `PUBLER_API_KEY` en el entorno lee las estadísticas de Publer).
   Genera en `centro/datos/`: `videos.json`, `ejecuciones.json`, `aprendizajes.json`,
   `mejores_horas.json`, `estado.json` y `auditoria.json` (el laboratorio del centro).
2. Inclúyelos en el commit del paso 8. Al hacer push a `main`, Vercel vuelve a publicar el centro
   solo. Las vistas en vivo no dependen de esto: el centro las pide cada minuto a YouTube y Publer
   (`centro/api/vivo.js`); estos archivos son la última foto (plan, créditos, bitácora, lecciones).

## 9. Reporte final (después del paso 10)

Resumen corto: qué se verificó (lo que salió y lo que no, con el estado exacto), qué video se
programó y a qué hora (franja de la prueba), créditos usados y restantes, qué decidió la auditoría
(lo que gana, lo que pierde, lo que se probó) y cualquier problema. Los días sin publicación, una
o dos líneas. Los lunes, pide a Rodrigo capturas de las estadísticas de Instagram y TikTok de la
semana (regla 33). Es lo que le llega como notificación.
