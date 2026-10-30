# Arquitectura

## Flujo diario (tarea programada en la nube)

1. **Elegir**: siguiente pilar de la rotación (relaciones → negocio → familia → hábitos), un cuarto
   (sala, oficina, cocina, recámara, sillón) y un vestido **nunca usado** del catálogo.
2. **Guion**: una idea de un libro o estudio real, ~27 palabras (12 s), con fuente citada.
3. **Foto**: Nano Banana 2 image2image con 3 referencias: hoja maestra del personaje, hoja del
   Rottweiler y locación.
4. **Revisión de foto**: cara, pecas, perro, manos, vestido correcto. Si falla, se regenera (máximo 2
   intentos).
5. **Video**: Wan 3.0 element2video, 12 s, 720p, 9:16, con la foto, la hoja del personaje, la hoja del
   perro y la **voz de referencia fija** (`audioRole: voice_reference`).
6. **Revisión de video**: cuadros clave + que el audio diga el guion.
7. **Subtítulos**: se queman en el video con ffmpeg (la mayoría ve sin sonido).
8. **Publer**: `POST /api/v1/media/from-url` con la URL pública del video, luego el post como
   **borrador** en Instagram, TikTok y Facebook (y YouTube Shorts si se agrega).
9. **Registro**: fila en Supabase con todo lo anterior; el vestido queda marcado como usado.

Aprobación: el borrador se aprueba en Publer con un clic. Tras un mes sin fallas se puede cambiar a
publicación automática.

## Componentes

| Pieza | Herramienta |
|---|---|
| Generación de imagen y video | OpenArt (plan Plus, 12,000 créditos/mes) |
| Publicación | Publer Business (API) |
| Base de datos y dashboard | Supabase + página web |
| Orquestación | Tarea programada de Claude diaria |
| Secretos | `PUBLER_API_KEY`, `PUBLER_WORKSPACE_ID` como secretos del entorno, nunca en el repo |

## Presupuesto de créditos (plan Plus)

| Concepto | Créditos |
|---|---|
| Foto por video | 30 |
| Video 12 s Wan 3.0 720p | 480 |
| Total por video sin reintentos | ~510 |
| 15 videos/mes con 1.5x de reintentos | ~11,500 de 12,000 |

Queda casi sin margen. Si los reintentos superan 1.5x hay que comprar créditos extra o subir a Pro.
