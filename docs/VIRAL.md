# Cómo hacerse viral (investigación del 31-oct-2026)

Lo que cada red dice que premia, lo que eso significa para Victoria y qué se hace. Cada dato con su
fuente; donde la fuente no es la red misma, se dice. Las cifras "mágicas" (70% de retención, 3 s) son
reglas de dedo de blogs, no datos oficiales.

## Lo que premia cada red

| Red | Señales (fuente) | Qué no cuenta |
|---|---|---|
| YouTube Shorts | "Viewed vs. swiped away" (cuántos eligieron verlo en vez de deslizar) y el % que ven; cada Short se prueba con un público chico y crece o se frena según su reacción ([vidIQ](https://vidiq.com/blog/post/youtube-shorts-algorithm/), [OutlierKit](https://outlierkit.com/resources/youtube-shorts-algorithm/)). YouTube no publica pesos. | Las etiquetas pesan poco |
| Instagram Reels | Tiempo visto, likes por alcance y **envíos por alcance** (Mosseri, ene-2025; los envíos pesan algo más para no seguidores) ([Buffer](https://buffer.com/resources/instagram-algorithms/), [wiro.ae](https://wiro.ae/articles/instagram-ranking-signals-2026)). | — |
| TikTok | Cuánto ves y si lo terminas, likes, compartidos, comentarios ([TikTok Newsroom](https://newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you), [TikTok Safety](https://www.tiktok.com/safety/en/making-your-feed-for-you)). | **Los seguidores no son factor directo** (TikTok) |

## Etiqueta de IA: obligatoria y ligada al alcance

- **Instagram (31-ago-2026):** las cuentas cuyo personaje es generado con IA deben usar la etiqueta
  "AI-generated profile"; sin ella pueden perder alcance y salir de las recomendaciones. Con ella no se
  castiga ([TechCrunch](https://techcrunch.com/2026/08/31/instagram-puts-new-limits-on-undisclosed-ai-profiles/),
  [Engadget](https://www.engadget.com/2246914/instagram-will-demote-ai-generated-influencers-if-they-dont-clearly-label-their-account/)).
  Victoria es exactamente ese caso: **la etiqueta se pone en la app (Rodrigo)**.
- **TikTok:** el contenido realista hecho con IA debe llevar la etiqueta de IA; la API de publicación tiene
  `is_aigc` ([TikTok for Developers](https://developers.tiktok.com/doc/content-posting-api-reference-direct-post)).
  Los blogs dicen que lo no etiquetado puede perder alcance o borrarse; TikTok no lo confirma en lo que se encontró.
  Además, cada usuario puede pedir ver menos contenido de IA en su For You
  ([Digital Music News](https://www.digitalmusicnews.com/2025/11/21/tiktok-ai-toggle-how-to-use/)): el gancho tiene que ganar igual.
  **Publer no tiene ese campo** (revisado en su API el 31-oct: TikTok solo trae privacy, comment, duet, stitch,
  promotional, paid, auto_add_music y reminder): la etiqueta de IA de TikTok la pone Rodrigo en la app.
- **YouTube:** `containsSyntheticMedia` en cada video (ya lo pone `youtube.py`; reafirmado el 31-oct).

## Lo que ya muestran los números de Victoria (31-oct)

- YouTube: el video de Victoria hablando (01) 467 vistas; los videos de carrusel 20-27. El formato que
  funciona es Victoria a cámara.
- TikTok: 1,165 seguidores y 89 de alcance en el 01. Como los seguidores no cuentan, lo que manda es si
  la gente no desliza y lo termina.
- Instagram: 60 seguidores, alcance 6. Posible causa: la etiqueta de perfil de IA (arriba). No comprobado.

## Qué se hace (en orden de impacto)

1. **Etiquetas de IA en las 3 redes** (Instagram: perfil; TikTok: cada post; YouTube: ya). Sin esto, todo lo
   demás puede no importar en Instagram.
2. **Que no deslicen (segundo 0-1):** la primera frase sola tiene que ser una pregunta o una cifra que te toca
   a ti (`docs/GANCHOS.md`), con el título en pantalla desde el cuadro 1 (`titulo_pantalla.py`) y la voz antes
   de 0.4 s (control del paso 5).
3. **Que lo terminen y lo repitan:** la última frase engancha con la primera (cierre en bucle) o deja un hueco
   para la siguiente parte; nada de despedidas. 16-18 s para explicaciones.
4. **Que lo manden (envíos = alcance con no seguidores en Instagram):** el dato tiene que servirle a alguien
   concreto y el pie lo nombra: "mándaselo a quien renunció este año", no "a alguien que lo necesite".
5. **Series numeradas:** "Aguinaldo 1/4", "Así empezaron 3/5": la gente sigue la cuenta para ver la siguiente.
6. **Temporada:** aguinaldo (nov-dic) y cuesta de enero son demanda segura; van primero (`ventana` en el plan).
7. **Medir lo que importa:** en YouTube Studio, "Viewed vs. swiped away" de cada Short (no está en la API);
   en Instagram, envíos y tiempo visto; en TikTok, % que lo terminan.

## Lo que no mueve la aguja

Más hashtags (Instagram corta en 5), publicar más veces en Instagram con 60 seguidores, mover la hora por
corazonada, o comprar vistas (castigo y cero ventas).
