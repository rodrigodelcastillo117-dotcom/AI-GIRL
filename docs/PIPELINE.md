# Pipeline automático: un video de Victoria

Lo ejecuta la tarea programada cada 2 días, dentro de la conversación de Claude donde se armó
el proyecto (ahí tiene las claves y permiso de push). Publica directo, sin aprobación humana. Por eso la
regla principal es: **si algo no pasa el control de calidad, NO se publica** y se registra el fallo.

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

## 1. Elegir el video

- **Si hay un video con `"estado": "listo_para_publicar"`**, ese es el de esta ejecución: ya está
  generado, revisado y subtitulado (`archivo`). No generes nada: ve directo al paso 7 con su
  archivo y su `hora_publicacion`, y después a los pasos 8 a 10.
- Salta los videos que aparezcan en `config.json → ejecuciones_unicas`: los publica otra tarea.
- Si no, el primero de `contenido/plan.json` con `"estado": "pendiente"`.
- Confirmar que su `vestuario` no aparece en ningún video con otro estado. Si se repite, cambiarlo
  por uno nuevo acorde a la locación y anotarlo en el plan.
- Si no quedan pendientes: no generar nada; reportar que hay que escribir más guiones.

## 1b. Mejora continua (antes de generar)

Cada video debe salir mejor que el anterior. Antes de generar:

1. Lee `contenido/aprendizajes.json`: cada `regla` técnica se aplica a los prompts de los pasos 3 y
   4 de esta ejecución (composición, cámara, referencias).
2. Lee las métricas de `centro/datos/videos.json` (columnas `v_*`, `l_*`, `c_*`, `s_*`, `g_*`).
   Con 8 o más videos medidos:
   - Si un pilar o una hora promedia claramente más vistas (al menos 30% más con 2+ videos), mueve
     al frente los pendientes de ese pilar y usa esa hora en los que digan "a definir".
   - Reescribe el gancho (primera frase) del guion de este video al estilo de los 3 videos con más
     vistas, sin cambiar la idea ni la fuente, máximo 28 palabras. Actualiza también sus
     `subtitulos` y `palabras_clave`.
3. Anota en el video, campo `"mejoras_aplicadas"`, qué reglas o cambios usaste.



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
5. Si falla cualquier punto: un solo reintento del video (paso 4). Si vuelve a fallar: marcar el
   video `"estado": "fallido"` con el motivo en `"qa"`, hacer commit y push, y terminar SIN publicar.
6. **Aprendizaje:** si algo falló o salió notablemente mejor que antes, agrega un renglón a
   `contenido/aprendizajes.json` (`fecha_utc`, `origen`, `tipo`: tecnico, contenido o publicacion,
   `aprendizaje`, `regla` concreta para la próxima vez). No repitas una regla que ya existe.

## 6. Subtítulos

```
python scripts/frases_a_tiempos.py palabras.json frases.json tiempos.json   # frases = "subtitulos" del plan
python scripts/subtitular.py video.mp4 tiempos.json videos/video-<id>-SUBTITULADO.mp4 "<palabras_clave separadas por coma>"
```
Revisar 3 cuadros del video subtitulado: texto legible y sin tapar la cara.

## 7. Publicar en Publer

- Texto: `texto_post` + línea en blanco + `reglas.cierre_de_texto`.
- Hora: `hora_publicacion` del video en `America/Mexico_City` (si dice "a definir", usar
  `hora_por_defecto` de `config.json`), convertida a UTC en formato ISO
  (`2026-10-30T02:47:00Z`). Si faltan menos de 15 minutos, usar ahora + 15 minutos.
- Título: la primera línea de `texto_post` sin emojis, máximo 90 caracteres.
- `python scripts/publer.py publicar <video> <texto.txt> <hora_utc> "<título>"`.
  Solo publica en las cuentas de `config.json → cuentas_publer` (o cuyo nombre contiene
  `filtro_cuentas`); YouTube solo en `canal_youtube`. La de Instagram se llamaba "Nadie Te lo
  Explicó" y el canal de YouTube también: Publer y la API pueden seguir dando ese nombre. Si la API responde algo
  inesperado, consultar https://publer.com/docs, corregir `scripts/publer.py`, volver a intentar
  una vez y dejar la corrección en el commit.
- **Duplicados:** `publer.py` omite las cuentas que ya tienen un post con la misma primera línea y
  `youtube.py` no sube un video si el canal ya tiene uno con el mismo título (pasa si una ejecución
  anterior publicó pero no pudo guardar en el repo). Si responden `OMITIDO`, el video ya estaba
  programado: regístralo como `programado` y no lo vuelvas a subir.
- **YouTube Shorts va aparte, sin Publer:** si existen `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` y
  `YOUTUBE_REFRESH_TOKEN` en el entorno, `python scripts/youtube.py subir <video> "<título>"
  <texto.txt> <hora_utc>` con el mismo texto y la misma hora. Si no existen, se omite YouTube y se
  menciona en el reporte. Si responde `invalid_grant`, el permiso venció: reportarlo (no se arregla
  solo).

## 8. Registro

En `plan.json`, en el video: `"estado": "programado"`, `"publica_utc"`, `"archivo"`,
`"publicacion": {"youtube": "<enlace del Short>"}` (el centro lo usa para leer sus vistas),
`"openart": {"foto": id, "video": id}`, `"creditos"` usados, `"qa"` (`{"similitud": 0.9x, "notas": ...}`).
Copiar el MP4 final a `videos/`.

Agrega un renglón a `contenido/ejecuciones.json`: `fecha_utc`, `tipo` (generar o publicar),
`video_id`, `resultado` (programado, fallido u omitido), `detalle` en una frase,
`creditos_usados` y `creditos_restantes` (de `openart_account_get` al terminar).

Commit y push a `main`. Si el push falla, dilo en el reporte: lo publicado ya quedó publicado.

## 10. Centro de mando (Vercel, proyecto `victoria-centro`)

1. `python scripts/tablero.py` (con `PUBLER_API_KEY` en el entorno lee las estadísticas de Publer).
   Genera en `centro/datos/`: `videos.json`, `ejecuciones.json`, `aprendizajes.json`,
   `mejores_horas.json` y `estado.json`.
2. Inclúyelos en el commit del paso 8. Al hacer push a `main`, Vercel vuelve a publicar el centro
   solo. Las vistas en vivo no dependen de esto: el centro las pide cada minuto a YouTube y Publer
   (`centro/api/vivo.js`); estos archivos son la última foto (plan, créditos, bitácora, lecciones).

## 9. Reporte final (después del paso 10)

Resumen corto: qué video, hora de publicación, cuentas, créditos usados y restantes, y cualquier
problema. Es lo que le llega a Rodrigo como notificación.
