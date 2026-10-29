# SEO de Victoria: títulos, palabras clave, tags y hashtags

Lo escribe Claude al crear cada guion (paso 1c de `docs/PIPELINE.md`) en el bloque `"seo"` del
video en `contenido/plan.json`. `scripts/seo.py` lo convierte en los textos que se publican.

## Lo que más pesa (en orden)

1. **Los primeros 2 segundos del video** (el gancho dicho y el subtítulo). En Shorts, Reels y
   TikTok el algoritmo reparte por retención, no por título. Ningún SEO salva un gancho flojo.
2. **Lo que se dice y se lee**: TikTok e Instagram transcriben el audio y leen el texto en
   pantalla para su buscador. La palabra clave debe decirse en el guion y salir en los subtítulos.
3. **Título y descripción de YouTube**: YouTube sí se busca. La palabra clave va al inicio.
4. **Caption de Instagram y TikTok**: la primera línea con la palabra clave; los hashtags ayudan poco.
5. **Tags de YouTube**: YouTube dice que casi no influyen (sirven para errores de escritura).
   Se ponen, pero no se pierde tiempo en ellos.

## Reglas del bloque "seo"

- `palabra_clave`: lo que una persona escribiría en el buscador ("regla del 72", "ley de
  Parkinson", "cómo ahorrar dinero"). Una sola, en minúsculas salvo nombres propios.
- `titulo_youtube`: **empieza con la palabra clave**, luego dos puntos y la promesa. Máximo 70
  caracteres (`seo.py` agrega " #Shorts"). Sin mayúsculas sostenidas ni clickbait que el video
  no cumpla. Ejemplo: "Regla del 72: cuánto tarda tu dinero en duplicarse".
- `tags_youtube`: 8 a 12, de la más específica a la más general, siempre con la palabra clave,
  variantes sin acentos, el autor o el libro si lo hay y "victoria the ceo".
- `hashtags_youtube`: 3, el primero `#Shorts`; los otros dos del tema. YouTube los muestra
  arriba del título.
- `texto_post` (Instagram y TikTok): primera línea = el gancho con la palabra clave; segunda =
  la acción; la fuente con 📚; aviso educativo en finanzas (⚠️) o de bienestar en salud mental
  (💛); **3 a 5 hashtags**: 2 del tema, 1 de la palabra clave si existe como hashtag y
  `#victoriatheceo`.

## Lo que el sistema aprende del SEO

`scripts/aprender.py` compara el `tipo_gancho` (pregunta, número, regla, dato, cita, consejo),
que es también la primera línea del título. Si un tipo gana, los guiones nuevos lo usan más.
