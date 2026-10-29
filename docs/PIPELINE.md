# Pipeline automático: un video de Victoria

Lo ejecuta la tarea programada cada 2 días. Publica directo, sin aprobación humana. Por eso la
regla principal es: **si algo no pasa el control de calidad, NO se publica** y se registra el fallo.

## 0. Preparación

1. El repo debe estar en `/home/user/ai-girl` con permiso de escritura (`add_repo` con
   `access: "push"` para `rodrigodelcastillo117-dotcom/ai-girl`, luego `git clone`).
2. Entorno de Python para subtítulos:
   `python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q faster-whisper num2words`.
   Con faster-whisper, decodificar el audio con ffmpeg (ver `scripts/transcribir.py`); la versión
   de PyAV del paquete no acepta rutas de archivo directo.
3. Verificar `PUBLER_API_KEY` en el entorno (`env | grep -c PUBLER_API_KEY`). Si falta: no generar
   nada, reportar y terminar.
4. `openart_account_get`: si hay menos créditos que `creditos_minimos_para_correr`
   (`contenido/config.json`), no generar nada, reportar y terminar.

## 1. Elegir el video

- El primero de `contenido/plan.json` con `"estado": "pendiente"`.
- Confirmar que su `vestuario` no aparece en ningún video con otro estado. Si se repite, cambiarlo
  por uno nuevo acorde a la locación y anotarlo en el plan.
- Si no quedan pendientes: no generar nada; reportar que hay que escribir más guiones.

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
  Solo publica en cuentas cuyo nombre contiene `filtro_cuentas`. Si la API responde algo
  inesperado, consultar https://publer.com/docs, corregir `scripts/publer.py`, volver a intentar
  una vez y dejar la corrección en el commit.

## 8. Registro

En `plan.json`, en el video: `"estado": "programado"`, `"publica_utc"`, `"archivo"`,
`"openart": {"foto": id, "video": id}`, `"creditos"` usados, `"qa"` (similitud y notas).
Copiar el MP4 final a `videos/`. Commit y push a `main`.

## 9. Reporte final

Resumen corto: qué video, hora de publicación, cuentas, créditos usados y restantes, y cualquier
problema. Es lo que le llega a Rodrigo como notificación.
