# Pipeline automático: un video de Victoria al día

Lo ejecuta la tarea programada **todos los días a las 6:37 a.m.** (hora de México), dentro de la
conversación de Claude donde se armó el proyecto (ahí tiene las claves y permiso de push). El
video sale **a las 6:45 p.m.** del mismo día en Instagram, TikTok y YouTube Shorts. Publica
directo, sin aprobación humana. Por eso la regla principal es: **si algo no pasa el control de
calidad, NO se publica** y se registra el fallo.

Cada ejecución también **audita**: mide los videos ya publicados, compara qué funciona y qué no
(tema, fondo, vestimenta, color, gancho, día y hora) y elige el siguiente video con esos datos.

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

## 1. Medir y auditar (siempre, aunque hoy no se publique)

```
python scripts/aprender.py medir     # foto de vistas de cada video publicado → contenido/metricas.json
python scripts/aprender.py auditar   # qué gana y qué pierde, y el siguiente video → contenido/auditoria.json
```
Lee el resumen y `contenido/auditoria.json` (`ranking`, `decision`, `alertas`). Cada video se
califica por sus vistas a ~36 h contra la mediana del canal (índice 1.0 = normal; 1.2 o más gana;
0.8 o menos pierde, con al menos 3 videos). Nada se da por bueno o malo con menos datos.

## 1a. Un video por día

- Si en `plan.json` ya hay un video `programado` para hoy (fecha de México), hoy no se publica
  otro: termina con los pasos 8, 10 y 9 (registrar la auditoría y actualizar el centro).
- Si `auditoria.decision.modo` es `saltar` (el día de hoy pierde de forma consistente), tampoco se
  publica: se ahorran créditos. Dilo en el reporte.

## 1b. Elegir y mejorar el video

- **Si hay un video `listo_para_publicar`**, ese es el de hoy (ya generado y revisado): ve directo
  al paso 7 con su `archivo`, y después a los pasos 8, 10 y 9.
- Si no, el de `auditoria.decision.video_id`. Aplica sus `cambios_sugeridos`: cambia la locación
  por una del tipo que gana, el estilo de vestimenta por el que gana (con una prenda nueva, nunca
  repetida) o reescribe la primera frase con el tipo de gancho que gana, sin cambiar la idea ni la
  fuente, máximo 28 palabras (y entonces actualiza `subtitulos`, `palabras_clave`, `texto_post` y
  `seo`).
- Aplica cada `regla` técnica de `contenido/aprendizajes.json` a los prompts de los pasos 3 y 4.
- Confirma que su `vestuario` no aparece en ningún otro video. Si se repite, cámbialo.
- Anota en el video `"decision"` (copia de `auditoria.decision`) y `"mejoras_aplicadas"` (qué
  cambiaste y por qué). Así el centro y la siguiente auditoría saben qué se probó.

## 1c. Escribir guiones nuevos (cuando quedan menos de 5)

Escribe 10 videos nuevos al final de `plan.json → videos`, con todos los campos de los demás
(`id`, `estado: "pendiente"`, `pilar`, `guion` de máximo 28 palabras dicho en español de México,
`subtitulos` con dígitos, `palabras_clave`, `fuente` real y verificable, `locacion`, `vestuario`
nuevo, `accion`, `hora_publicacion: "18:45"`, `texto_post` y `seo` según `docs/SEO.md`).

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

## 7. Publicar

- Textos: `python scripts/seo.py <id> /tmp/seo-<id>` arma `texto_redes.txt` (Instagram y
  TikTok), `titulo_redes.txt`, `titulo_youtube.txt`, `descripcion_youtube.txt` y
  `tags_youtube.txt` desde el bloque `seo` del video (reglas en `docs/SEO.md`). Si el video no
  tiene `seo`, escríbelo primero.
- Hora: `hora_publicacion` del video (18:45) en `America/Mexico_City`, convertida a UTC en formato
  ISO (`2026-10-31T00:45:00Z`). Si faltan menos de 15 minutos, usar ahora + 15 minutos.
- `python scripts/publer.py publicar <video> /tmp/seo-<id>/texto_redes.txt <hora_utc> "<titulo_redes>"`.
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
  `YOUTUBE_REFRESH_TOKEN` en el entorno, `python scripts/youtube.py subir <video>
  "<titulo_youtube>" /tmp/seo-<id>/descripcion_youtube.txt <hora_utc> --tags
  /tmp/seo-<id>/tags_youtube.txt` a la misma hora. Si no existen, se omite YouTube y se
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

Incluye `contenido/metricas.json` y `contenido/auditoria.json` en el commit.

Commit y push a `main`. Si el push falla, dilo en el reporte: lo publicado ya quedó publicado.

## 10. Centro de mando (Vercel, proyecto `victoria-centro`)

1. `python scripts/tablero.py` (con `PUBLER_API_KEY` en el entorno lee las estadísticas de Publer).
   Genera en `centro/datos/`: `videos.json`, `ejecuciones.json`, `aprendizajes.json`,
   `mejores_horas.json`, `estado.json` y `auditoria.json` (el laboratorio del centro).
2. Inclúyelos en el commit del paso 8. Al hacer push a `main`, Vercel vuelve a publicar el centro
   solo. Las vistas en vivo no dependen de esto: el centro las pide cada minuto a YouTube y Publer
   (`centro/api/vivo.js`); estos archivos son la última foto (plan, créditos, bitácora, lecciones).

## 9. Reporte final (después del paso 10)

Resumen corto: qué video, hora de publicación, cuentas, créditos usados y restantes, qué decidió
la auditoría y por qué (lo que gana, lo que pierde, lo que se probó hoy) y cualquier problema. Es
lo que le llega a Rodrigo como notificación.
