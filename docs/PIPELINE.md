# Pipeline automático de Victoria

La tarea programada corre **todos los días a las 6:37 a.m.** (hora de México) dentro de la
conversación de Claude donde se armó el proyecto (ahí están las claves y el permiso de push).
Todos los días **verifica y audita**; **cada 2 días publica** un video en Instagram, TikTok y
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
   `python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q faster-whisper num2words`.
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
  `decision` (`toca_publicar`, `publicar_hoy`, `hora_siguiente`, `prueba_horas`, siguiente video a
  generar y `cambios_sugeridos`), `reglas_vigentes` (reglas con cifras de los datos propios) y
  `alertas`.

## 1a. Si hoy NO toca publicar

Solo pasos 8 (registro), 10 (centro) y 9 (reporte de una línea). Excepción: si no hay ningún
video `listo_para_publicar`, genera uno hoy (pasos 1b a 6) y déjalo listo: así el día de publicar
ya está hecho y la franja de las 8:00 nunca se pierde.

## 1b. Si hoy SÍ toca publicar

1. Publica el video `listo_para_publicar` (`decision.publicar_hoy`) a la hora
   `decision.hora_siguiente` de hoy (paso 7). Si esa hora ya pasó o faltan menos de 15 minutos,
   usa la siguiente franja de hoy de `config.json → prueba_horas.franjas`; nunca se tira un video
   (regla 31).
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
(`id`, `estado: "pendiente"`, `pilar`, `guion` de máximo 28 palabras dicho en español de México
que abre con el gancho, `subtitulos` con dígitos, `palabras_clave`, `fuente` real, `locacion`,
`vestuario` nuevo, `accion`, `hora_publicacion: "rotacion"`, `texto_post` sin hashtags y `seo`
según `docs/SEO.md`, más `ganchos_alternativos` (las otras 2 primeras frases propuestas) y
`adn: {"tipo_gancho": "cifra|contradiccion|error|nombre|regla|dato|cita|pregunta|consejo"}`).
Después corre `python scripts/seo.py revisar`: tiene que salir sin errores.

Para mover un video ya programado: `python scripts/reprogramar.py <id> <hora_utc>` (mueve YouTube
y dice qué posts de Publer hay que mover a mano: Publer no deja cambiar la hora por API y su
borrado masivo es peligroso, nunca se usa).

- **Cada dato se comprueba antes de escribirlo** (regla 7): busca la fuente con WebSearch y no
  pongas cifras, fechas ni frases atribuidas que no encuentres. El título no promete más de lo que
  dice el video.

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

## 4. Video

`wan3-0` `element2video`: `duration: 12`, `resolution: "720p"`, `aspectRatio: "9:16"`,
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

## 7. Publicar

1. `python scripts/seo.py <id> /tmp/seo-<id>` (si falla, corrige el bloque `seo` del video y
   repite): deja `titulo.txt`, `descripcion_youtube.txt`, `tags_youtube.txt` y `texto_redes.txt`.
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
botón le agrega `?src=<red>` para saber de dónde vino cada venta. Para activar la lista de correos se llena `CONFIG` en
`sitio/public/index.html`.

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
