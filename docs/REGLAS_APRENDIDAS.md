# Reglas aprendidas en 4 canales reales (brief de Rodrigo, 29-oct-2026)

Medidas durante meses en otros canales. Se aplican todas en VictoriatheCEO, salvo donde abajo
dice "Aquí". Cuando los datos propios contradigan una regla, mandan los datos propios (regla 17).

## Antes de publicar (seguridad)
1. Antes de cada subida a YouTube, `channels?mine=true` y comprobar que el id es
   `UCGyza9C58eMH3VnGgkMPr1A`. Si no coincide, NO subir. *Aquí: `scripts/youtube.py` lo exige.*
2. Primera prueba en "private"; pública solo cuando esté bien. *Aquí: todo se sube privado con
   hora de publicación y se verifica después de subir.*
3. Nunca publicar con navegador automatizado ni contraseñas: solo API (96 % de acierto contra
   33-66 %; Meta bloquea cuentas que entran desde servidores).
4. Al recortar texto, no partir un emoji. *Aquí: los títulos no se recortan; si son largos, se
   reescriben.*
5. Publer: el contenido va dentro de `networks.<red>`, una petición por red, y un 200 con `job_id`
   no es publicado: consultar el job hasta que diga que salió. *Aquí: según la documentación
   actual de Publer, el estado válido para programar o publicar es `scheduled` (no existe
   `published` en `bulk.state`); se confirma que salió con la verificación de la regla 34.*
6. Nunca un título vacío: Instagram lo pide y TikTok exige mínimo 5 caracteres; tener respaldo.

## Calidad
7. Prohibido inventar cifras, datos o logros. Comprobar cada dato. Un título que promete más de lo
   que hay destroza la retención.
8. Revisar cada pieza antes de publicar; si la revisión no se pudo hacer, no se publica. Si solo
   una pieza está mal, rehacer esa.
9. Personaje consistente: siempre la misma hoja de personaje de Victoria en OpenArt.

## Título
10. Delante lo que la gente BUSCA, no el número ni la marca.
11. Afirmar, no preguntar: los títulos con pregunta rindieron 0.45x.
12. Ni `#` en el título (0.66x) ni separadores `|` o `:` para encadenar palabras clave (mediana 9
    vistas contra 19).
13. Corto: empezar con máximo 45 caracteres y ajustar con datos propios.
14. Nombrar algo concreto (cifra real, empresa, hábito, situación).
15. Uno o dos emojis al final, pegados al hecho (2.32x en un canal): probarlo con datos propios.
16. Ortografía perfecta con tildes y eñes; si acortar rompe las tildes, usar el largo.
17. Si los datos propios contradicen a la competencia, manda la audiencia propia.

## Descripción (YouTube)
18. Las dos primeras líneas son lo único visible y lo que más indexa: términos de búsqueda que se
    lean como frase.
19. Después 2 o 3 párrafos cortos con lo concreto. Máximo 4,900 caracteres.
20. Máximo DOS enlaces, arriba: el que vende y luego la tienda o el perfil.

## Etiquetas (YouTube)
21. 30 a 40 etiquetas en minúsculas; tope real 500 caracteres sumados (quedarse en 480); una
    etiqueta con espacios cuenta 3 de más. La API recorta sin avisar.
22. Tres capas en este orden: genéricas (volumen), formato e intención, lo concreto del video y
    sus colas largas. Las concretas son las que ganan.

## Instagram y TikTok
23. Pesan los 3 primeros segundos: menos de 35 % de abandono al inicio = 934 de alcance; más de
    45 % = 194. Gancho en el segundo 0, sin introducción.
24. El único enlace pulsable es el de la bio: escribir "enlace en mi perfil".
25. En YouTube, el enlace va en un primer comentario fijado, escrito como persona, con un solo
    enlace. *Aquí: la API de YouTube puede escribir el comentario (con permiso extra), pero no
    fijarlo; fijarlo es manual.*
26. `?ref=<red>` en cada enlace (yt, ig, tt).
27. Hashtags: 3 o 4 fijos de marca y nicho, bien escritos, + 3 a 5 concretos del video. En el
    pie, nunca en el título.
28. Si se conecta una página de Facebook, su Reel sale también en el Instagram enlazado: no
    mandar el mismo video dos veces a Instagram. *Aquí: no se publica en Facebook.*

## Horarios y frecuencia
29. Publicar los 7 días; el "peor día" cambia de mes a mes y con menos de 15 videos por día es
    ruido. *Aquí: Rodrigo decidió un video cada 2 días. Nunca se salta un día por "malo": el día
    solo cuenta con 15 videos o más.*
30. Una hora fija por canal; al principio medir franjas 3 o 4 semanas y quedarse con la que gane.
    *Aquí: rotación 18:45, 08:00 y 14:00 (config.json → prueba_horas) hasta tener 5 videos por
    franja.*
31. No tirar contenido producido por un horario: pasarlo a la siguiente franja o día.

## Medir y aprender
32. Medir por video vistas, retención, likes y comentarios; sacar reglas con cifras de los datos
    propios y aplicarlas a quien escribe el título.
33. Instagram y TikTok no dan métricas fiables por API: pedir capturas a Rodrigo cuando hagan falta.
34. Nunca una alarma falsa ni decir "publicado" sin comprobarlo en la red.
