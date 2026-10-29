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
- `hashtags`: 3 a 5 concretos del video, bien escritos. `seo.py` les antepone los 4 fijos
  (`config.json → hashtags_fijos`) y los pone en el pie, nunca en el título (regla 27).

## Enlaces

Si `config.json → enlace_venta` tiene un enlace:
- Instagram y TikTok: el pie dice "Enlace en mi perfil 👆" (regla 24); el enlace va en la bio.
- YouTube: arriba de la descripción con `?ref=yt` y, cuando haya permiso para comentar, en un
  primer comentario escrito como persona (regla 25). Fijarlo es manual: la API no lo permite.
