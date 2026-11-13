# Miniaturas, títulos, descripciones y hashtags (investigado el 12-nov-2026)

Rodrigo (12-nov): "usa Canva Pro para las miniaturas, investiga cuáles son los formatos que más funcionan… las
descripciones deben ser TOP". "Oficial" = lo dice la plataforma; "estudio" = datos de terceros; "criterio" = nuestra
regla sin datos que la prueben (se prueba comparando CTR y tiempo visto entre videos; SIN Test & Compare: Rodrigo, 13-nov).

## Miniatura de video largo (YouTube)
- **Medida** (oficial): 16:9, recomendada 3840x2160 (mínimo 640 de ancho). Exportar JPG 1920x1080 o 3840x2160;
  desde el celular, < 2 MB (escritorio admite hasta 50 MB desde oct-2025).
- **YouTube dice** (oficial): regla de tercios, letra legible, sin saturar, "lo más grande posible" para pantallas
  chicas; título y miniatura cuentan la historia JUNTOS (la miniatura no repite el título).
- **Test & Compare** (oficial): hasta 3 miniaturas (y desde dic-2025 también títulos). Gana la de más TIEMPO VISTO, no
  la de más CTR; tarda días hasta ~2 semanas. NO SE USA (Rodrigo, 13-nov): una sola miniatura por video, la mejor de
  las plantillas de abajo.
- **Datos** (estudio vidIQ, 500 videos top, jun-2026): 69 % con cara (80 % en el top 50), 56 % alto contraste,
  mediana de 5 palabras de texto, solo 1 de cada 20 con cara exagerada. 1of10 (300 mil virales 2025): en Finanzas la
  cara SÍ rinde mejor. MrBeast: boca cerrada subió su tiempo visto (anécdota).
- **Reglas comunes** (criterio): esquina inferior derecha libre (~18 % x 12 %, ahí va la duración); texto Montserrat
  Black o Anton con contorno negro 6-8 px y letra ≥ 12 % del alto; 3-5 palabras; NUNCA fondo rojo (se pierde con su pelo
  y con la interfaz). Victoria con expresión segura (boca cerrada o media sonrisa), nunca sorpresa exagerada.

### Las 3 plantillas (se elige UNA por video según el tema; sin Test & Compare desde el 13-nov)
- **A · Cifra + Victoria**: Victoria a la derecha (x 55-100 %), cara ≈ 35 % del alto, mirando a la cifra. Cifra a la
  izquierda (x 5-50 %, y 20-60 %) en amarillo #FFD400 sobre azul marino #0B1F3A (ej. "$3,519"); debajo 2-3 palabras en
  blanco (y 65-80 %).
- **B · Pierdes vs ganas**: fondo partido: izquierda gris/rojo apagado con "-$8,000", derecha verde #16A34A con
  "+$8,000"; Victoria al centro (x 35-65 %), seria, boca cerrada.
- **C · Objeto + alerta**: Victoria a la izquierda (x 0-45 %); a la derecha un objeto grande (tarjeta, recibo, estado
  de cuenta de la Afore) ≈ 40 % del ancho; un solo círculo o flecha cian #00C2D1 y máx. 3 palabras ("NO LA USES").
- **Prueba del 12-nov**: la generación con IA de Canva (generate-design) salió PEOR que nuestras miniaturas de
  largo.py (en una el perro tapaba la cara, otra sin la cifra). Se quedan las de largo.py (ya siguen la plantilla A) y
  Canva Pro se usa para variantes B y C armadas a mano por Rodrigo o editando un diseño, no generadas.
- Se arman en **Canva Pro** (cuenta de la hermana de Rodrigo, conector Canva): se sube la foto de Victoria y el
  objeto, se arma con las posiciones de arriba y se exporta JPG 1920x1080. Se guarda en `videos/miniaturas/<id>-A|B|C.jpg`.

## Portadas de Shorts, Reels y TikTok
- Shorts (oficial, desde 25-jul-2026): miniatura propia 2160x3840 (9:16) solo para canales del Programa de Socios y
  desde Studio de escritorio; sin A/B. Lo importante lejos de los bordes (área útil ~3:2 del centro).
- Instagram: la cuadrícula del perfil es **3:4 (1080x1440)** desde ene-2025: recorta ~240 px arriba y abajo del 9:16.
  Cara y 2-4 palabras en la franja central. Nuestro título de pantalla va arriba: revisar que no lo corte la cuadrícula.

## Títulos y descripciones (YouTube)
- Título (oficial): palabra clave AL INICIO (se corta), marca al final, poco MAYÚSCULAS y emoji, fiel al contenido.
  Nuestra regla: ≤ 45 caracteres, empieza con seo.palabra_clave, sin ":" ni "|" (seo.py lo revisa).
- Descripción: lo que se ve antes de "más" resume el valor y repite la palabra clave (consenso, no hay número
  oficial). Prohibido (política de spam): listas de etiquetas o frases repetidas.
- **Capítulos** en largos: el primero en 00:00, ≥ 3 marcas en orden, cada una ≥ 10 s.
- **Hashtags**: en título o descripción; YouTube muestra hasta 3 junto al título; con más de 60 los ignora todos.
  Nuestra regla: 2-3 al final de la descripción.
- **Tags**: "papel mínimo" (oficial); sirven para errores comunes ("aginaldo", "afores", "buenfin").

## Pies de Instagram y TikTok
- Instagram: **máximo 5 hashtags** (anunciado por @creators el 18-19-dic-2025). Mosseri: los hashtags no dan alcance,
  clasifican; las palabras clave van EN EL PIE (no en comentarios). Hasta 2,200 caracteres. Trial Reels: desde 1,000
  seguidores (hoy 62: bloqueado, error 2207081).
- TikTok: 4,000 caracteres; el buscador lee pie, texto en pantalla y audio: palabra clave en los primeros ~80
  caracteres. Hay reportes (no oficiales) de tope de 5 hashtags.
- Estructura (criterio): 1ª línea = gancho con la palabra clave ("Aguinaldo 2026: esto te quita el SAT"); 1-2 frases
  con términos de búsqueda; UN solo llamado; 3-5 hashtags al final; "Personaje y video creados con IA".

## Etiquetas de IA
- YouTube: declarar contenido sintético realista (casilla al subir); desde may-2026 etiqueta solo lo no declarado.
  Política de "contenido no auténtico" (jul-2025): nada de plantillas repetidas con poca variación: cada pieza con
  escena, guion y miniatura propios.
- Instagram: etiqueta "Información de IA".

## Fuentes
support.google.com/youtube/answer/72431 · /12340300 · /13861714 · /6390658 · /146402 · /2801973 · /9884579 ·
vidiq.com/blog/post/youtube-thumbnail-design-tips/ · searchenginejournal.com/do-faces-help-youtube-thumbnails-heres-what-the-data-says/563944/ ·
ppc.land/youtube-ends-2-year-wait-for-shorts-thumbnails-but-blocks-a-b-testing/ ·
kapwing.com/resources/instagrams-new-grid-layout-size-and-dimensions-2025/ ·
businesstoday.in (límite de 5 hashtags, 19-dic-2025) · blog.hootsuite.com/instagram-search ·
thenextweb.com (etiquetado automático de IA en YouTube) · ppc.land/youtube-clarifies-inauthentic-content-policy-changes/
