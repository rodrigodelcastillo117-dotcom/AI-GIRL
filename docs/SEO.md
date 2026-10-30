# SEO de Victoria: títulos, descripción, etiquetas y hashtags

Lo escribe Claude al crear cada guion (paso 1c de `docs/PIPELINE.md`) en el bloque `"seo"` del
video en `contenido/plan.json`. `scripts/seo.py` lo valida y lo convierte en los textos que se
publican; si un título rompe una regla, `seo.py` falla y el título se reescribe (nunca se recorta).
Las reglas vienen de 4 canales medidos (`docs/REGLAS_APRENDIDAS.md`); cuando los datos propios
(`contenido/auditoria.json → reglas_vigentes`) digan otra cosa, mandan los propios.

## Lo que más pesa (en orden)

1. **Los primeros 3 segundos** (regla 23): el gancho dicho en el segundo 0, sin "hola" ni
   introducción. Menos de 35 % de abandono al inicio dio 934 de alcance; más de 45 %, 194.
2. **Que el título cumpla lo que promete** (regla 7): si promete más, se cae la retención.
3. **Título y primeras 2 líneas de la descripción en YouTube**, que sí se buscan.
4. **Etiquetas y hashtags**: ayudan poco, pero cuestan nada.

## El bloque "seo"

```json
"seo": {
  "palabra_clave": "regla del 72",
  "titulo": "Regla del 72 para duplicar tu dinero 📈",
  "descripcion_inicio": "Regla del 72: divide 72 entre tu tasa ... duplica tu dinero.\nInterés compuesto explicado fácil, ...",
  "tags_concretas": ["regla del 72", "cuanto tarda en duplicarse mi dinero", "..."],
  "hashtags": ["#regladel72", "#interescompuesto", "#inversion", "#dinero"]
}
```

- `palabra_clave`: lo que una persona escribe en el buscador. El título EMPIEZA con ella (regla 10).
- `titulo` (mismo para YouTube, Instagram y TikTok):
  - máximo **45 caracteres** (regla 13; se ajusta con datos propios en `config.json → titulo_max`);
  - **afirma**, nunca pregunta (regla 11: preguntas rindieron 0.45x);
  - **sin `#`, sin `:` y sin `|`** (regla 12);
  - nombra algo concreto: cifra real, persona, libro, hábito (regla 14);
  - 0, 1 o 2 emojis **al final**, pegados al hecho (regla 15). Se prueba: más o menos 2 de cada
    3 títulos con emoji, y el laboratorio compara "con emoji" contra "sin emoji";
  - ortografía perfecta con tildes y eñes (regla 16).
- `descripcion_inicio`: **2 líneas** que se lean como frase y estén llenas de lo que se busca
  (regla 18). `seo.py` agrega después los enlaces (máximo 2, regla 20, con `?ref=yt`), el texto
  del post, la invitación a suscribirse, 3 hashtags y la aclaración de IA. Máximo 4,900 caracteres.
- `tags_concretas`: lo concreto del video y sus colas largas (capa 3 de la regla 22), en
  minúsculas. `seo.py` las junta con las genéricas y las de formato del pilar
  (`config.json → tags_genericas`, `tags_formato`) en ese orden, dando prioridad a las concretas
  dentro del tope de 480 caracteres (las que llevan espacios cuentan 3 de más). Con etiquetas de
  varias palabras caben unas 23 a 26; 30 a 40 solo caben si son cortas.
- `parrafo`: 3 a 5 frases naturales que expliquen la idea con **variantes de la búsqueda**
  (sinónimos, el nombre del autor o la ley, la pregunta que la gente escribe) y solo datos de la
  `fuente`. Va en la descripción de YouTube y en los pies de Instagram y TikTok, que también se
  buscan por texto. Nunca una lista de palabras clave sueltas (YouTube lo castiga como spam).
- `preguntas`: 3 preguntas reales que alguien escribiría en el buscador y que el video responde.
  Van en YouTube ("Preguntas que responde este video") y en TikTok (línea 🔎).
- `hashtags`: 3 a 5 concretos del video, bien escritos, del más buscado al menos buscado.
  `seo.py` arma los de cada red: **YouTube 5** (los 3 primeros salen sobre el título: van los
  concretos), **Instagram 5** (límite de Instagram desde diciembre de 2025: 3 concretos +
  `#finanzaspersonales #victoriatheceo`), **TikTok 7** (más los fijos de nicho). Nunca en el título.
- Las etiquetas de YouTube ya llenan el tope de 480 caracteres; YouTube dice que pesan poco.
  Lo que más pesa es título, primeras 2 líneas, párrafo y retención.

## Enlaces

Si `config.json → enlace_venta` tiene un enlace:
- Instagram y TikTok: el pie dice "Enlace en mi perfil 👆" (regla 24); el enlace va en la bio.
- YouTube: arriba de la descripción con `?ref=yt` y, cuando haya permiso para comentar, en un
  primer comentario escrito como persona (regla 25). Fijarlo es manual: la API no lo permite.
