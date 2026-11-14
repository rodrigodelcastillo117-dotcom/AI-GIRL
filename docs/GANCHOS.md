# Ganchos de Victoria (los primeros 2 segundos)

En 12 segundos, el gancho decide todo: si la primera frase no detiene el dedo, nada de lo demás se
ve. Se dice en el segundo 0, sin saludo, y el título fijo en pantalla (`scripts/titulo_pantalla.py`)
lo refuerza para quien ve sin sonido.

## Reglas

1. **Máximo 10 palabras** en la primera frase. Se entiende sin contexto.
2. **Habla de "tú"**, de una cifra concreta o de un nombre que la gente conoce.
3. **Abre una pregunta en la cabeza** que el resto del video cierra (punto 4 de `GUIONES_VIRALES.md`).
4. **Nunca promete más que el dato** (regla 7). Un gancho exagerado sube las vistas del primer
   segundo y tumba la retención; el algoritmo castiga lo segundo.
5. **Prohibido:** "hola", "hoy te voy a contar", "¿sabías que…?", "esto te va a volar la cabeza",
   y cualquier frase que no diga nada concreto.
6. **Prueba final:** leída sola, ¿haría que alguien deje de deslizar? ¿Se la mandarías a alguien?
   Si alguna respuesta es no, se reescribe.

## Fórmulas que usamos (con ejemplos del plan)

| Fórmula | Ejemplo |
|---|---|
| Cifra que sorprende | "La mitad de lo que gana Costco no viene de lo que vende." |
| Contradicción | "Si ahorras lo que te sobra, casi nunca vas a ahorrar." |
| El error de quien ve | "El pago mínimo de tu tarjeta es una trampa." |
| "Si tú…" (se reconoce) | "Si ganas 15 mil al mes, tu aguinaldo mínimo es de 7,500." |
| Nombre + giro | "Warren Buffett tiene dos reglas para invertir, y son la misma." |
| Historia en una línea | "Blockbuster pudo comprar Netflix por 50 millones y se rio." |
| Promesa corta y concreta | "Una división te dice cuándo se duplica tu dinero." |
| "Antes de X, haz esto" | "Antes de revisar el celular, haz esto." |
| Dolor + causa | "Si no puedes dormir pensando en pendientes, es por esto." |
| Pareja y dinero | "Las peleas por dinero predicen el divorcio más que otras peleas." |

## Gancho en pantalla (`texto_pantalla`)

La mayoría desliza sin sonido: lo primero que lee es el texto fijo de arriba
(`scripts/titulo_pantalla.py`). No es el título de SEO ("Escritura expresiva de 15 minutos" describe;
no detiene a nadie). Es un gancho visual de máximo 3 renglones de 22 letras que abre una pregunta y
no da la respuesta: "Lo que de verdad te roba energía", "La trampa del pago mínimo", "¿Cuánto
aguinaldo te toca?". En las series lleva el número: "Así empezaron #1: Airbnb casi quiebra".
`seo.py revisar` no deja pasar un video sin él.

## Plantillas de internet: cuáles sirven a Victoria

Las listas de "hooks instantáneos" están hechas para creadores humanos que cuentan su historia.
Victoria es un personaje de IA y no inventa anécdotas (regla de `PIPELINE.md`), así que:

- **Sirven tal cual, hablándole a "tú":** "Si estás haciendo ___, haz esto en su lugar" ·
  "Probablemente estás haciendo ___ mal" · "Por qué tu ___ no está funcionando" · "El mito sobre
  ___ que mantiene estancada a la mayoría" · "Todo el mundo complica ___" · "Lo que está arruinando
  tu ___ en silencio". El hueco siempre se llena con algo concreto (una cifra, un nombre, una cosa
  que la persona hace), nunca con "esto".
- **Sirven en tercera persona, con un caso real con fuente** (serie "Así empezaron"): "Todos le
  dijeron que no iba a funcionar…" → "Más de cien inversionistas le dijeron que no a Canva" ·
  "Casi renunció a ___" → "Airbnb casi quiebra y se salvó vendiendo cereal" · "Probé 3
  estrategias" → solo si un estudio real las comparó.
- **Prohibidas para Victoria:** las de primera persona que inventan una vida ("Cometí este error
  durante meses", "Pensé que me quedaría estancada", "El consejo que ignoré durante años", "Nadie
  me dijo que iba a ser así de difícil", "Este ajuste en mi rutina cambió todo") y las que prometen
  de más ("disparó ___ de la noche a la mañana"): mentira y regla 4.
- **Vacías si no se llenan bien:** "Necesitas escuchar esto" y "La verdad que nadie te cuenta" no
  dicen nada (regla 5); solo pasan si lo que sigue es un dato poco conocido y comprobado.

## Lo que tiene millones de vistas en finanzas en español (revid.ai, 31-oct-2026)

Patrones, no textos (nunca copiar a otro creador). Muestra: 20 videos virales de dinero en español
(TikTok, Reels, Shorts; 1 a 11 millones de vistas).
- **Pregunta con una cifra que te toca a ti**, y la respuesta sorprende al final: "¿cuánto le
  tocaría a cada mexicano si…?" (11.2 M), "cada mexicano debe casi ___" (1.5 M). Para Victoria:
  "¿Ganas quince mil? Te tocan…", "¿Por qué tu aguinaldo llega incompleto?".
- **Lista numerada con un hueco abierto**: "5 reglas… y la última es la que casi todos se saltan"
  (1.3 M), "lo mejor viene al final" (2.9 M). El hueco obliga a ver hasta el final (retención).
- **Negar lo obvio primero**: "No es abrir un restaurante, ni seguir modas…" y luego la respuesta.
- **Mito que se cae**: "¿Sabías que ya no existe ___?" (1.1 M), siempre con fuente.
- **Series numeradas** ("PT48"): la gente sigue la cuenta para ver la siguiente parte.
- Los de estas cuentas duran 30 a 150 s; los de Victoria, 10 a 25 s por los créditos de OpenArt. Los
  videos de carrusel (gratis, voz clonada) sí pueden llegar a 57 s: ahí cabe la lista con hueco.

El laboratorio (`scripts/aprender.py`) compara las fórmulas por `adn.tipo_gancho` con las vistas a
36 h: cuando haya datos, manda lo que gane con la audiencia de Victoria, no esta tabla.

## Gancho de impacto — EN PAUSA (13-nov: v1 y v2 rechazados por Rodrigo; ver "Lo que aprendimos")

### Lo que aprendimos (13-nov)
- Veo 3.1 Fast (Capital brincando a la cámara; cubeta de agua desde arriba, corte antes de mojarla) también fue
  rechazado: "no, está malo, así no". NO se gasta más en ganchos sin un video de referencia de Rodrigo.
- Rodrigo NO quiere que le peguen: quiere el SUSTO (la amenaza) y cortar justo antes. Ejemplos suyos: un señor en una
  escalera le avienta agua desde arriba → corte → Victoria hablando; Capital brincando hacia la cámara → corte → habla.
- Animar el primer cuadro del video hablado con seedance-1-pro NO sirve: objetos que flotan, brazos que no se entienden,
  letras inventadas. El gancho tiene que ser su PROPIA toma (otro encuadre), con un modelo mejor en física.

### (versión anterior) Gancho de impacto (Rodrigo, 13-nov-2026: "que parece que les avientan algo, corta y hablan… adaptado al fondo, a la persona, al tema" · "hazlo con Replicate")

Qué es: 0.4-0.8 s de acción en la MISMA escena y con el MISMO cuadro donde Victoria va a hablar: un objeto que ES el
tema vuela hacia la cámara (o cae de golpe), silbido + golpe seco, CORTE y entra Victoria hablando. Interrumpe el
scroll en el primer medio segundo. Script: scripts/gancho_impacto.py (generar → revisar cuadros → armar).

Reglas (no negociables):
1. El objeto ES el tema. Si el susto no tiene que ver, la gente se va en el segundo 2 y el video se castiga.
2. Elegante: el impacto lo pone el dinero, no la violencia. NUNCA atropellos, golpes a personas, armas, accidentes de
   coche realistas (contenido peligroso/engañoso con IA) ni nada que la haga ver vulgar.
3. Mismo cuadro que el video hablado (generar usa el primer cuadro de videos/video-<id>.mp4): que no se note el pegado.
4. Corte ANTES de que el modelo invente texto o marcas en el objeto (pasó con E1: después de 0.7 s el ticket mostraba
   "NICII"). Se elige el corte mirando la hoja de cuadros; ideal: el objeto en su punto más grande y borroso.
5. Texto de pantalla en el segundo 0, mismo estilo que el título del video (lo pone armar).
6. Máximo 1 de cada 3 shorts hablados: si se usa diario, se gasta.
7. Costo: seedance-1-pro 5 s 1080p ≈ $0.75 con la autorización shorts-escena (el freno manda).

Catálogo escena × tema (elegir el que va con el lugar donde está Victoria):
| Escena | Tema | Objeto / acción |
|---|---|---|
| café, terraza | gastos hormiga, antojos | un ticket larguísimo del café sale volando a la cámara (E1, 13-nov) |
| oficina, escritorio Vonhaucke | SAT, ISR, declaración | un sobre del SAT cae de golpe sobre el escritorio frente a la cámara |
| home office, estados de cuenta | tarjeta, deudas, MSI | una tarjeta de crédito sale disparada hacia la cámara |
| calle, compras | Buen Fin, ofertas | una bolsa de compras / etiqueta de precio vuela a la cámara |
| cocina, casa | aguinaldo, sueldo | billetes que se escapan volando hacia la cámara |
| estudio, lectura | Afore, pensión, retiro | un estado de cuenta de la Afore cae de golpe frente a la cámara |
| terraza nevada, invierno | cuesta de enero | bola de nieve que rueda hacia la cámara |
| lobby, junta | negocios, ventas | un fajo de facturas que alguien avienta sobre la mesa |

Prueba (desde el 14-nov): 3 shorts con gancho de impacto contra 3 normales comparables (mismo formato escena, misma
red, edad parecida). Se mide: % que sigue después de 3 s (YouTube: % visto; TikTok: vistas a la misma edad) y seguidores
por cada 1,000 vistas. Nadie gana con menos de 3 contra 3 (regla de ESTRATEGIA_POR_RED). Registro: plan.json →
gancho_impacto.prueba = "gancho-impacto-nov26"; evaluación en la revisión del 26-nov.

## Formato "la teoría" (Rodrigo, 13-nov-2026, consejo de una creadora sobre Trial Reels)

Qué es: video de 5-7 s (b-roll de Victoria haciendo algo, texto en pantalla, canción en tendencia) con el gancho
"Cuando [situación de dinero], [alguien] me contó sobre [teoría] y desde entonces no volví a ver mi dinero igual", y
TODO el valor en el caption largo: qué dice la teoría, cómo se aplica con números de México, y un llamado (sígueme /
guarda / comenta). La retención sale de que el video es corto y se repite mientras leen.

Reglas propias (no del consejo original):
- La teoría tiene que ser REAL y con fuente (nada de "puede ser inventada"): regla de dos fuentes y segunda revisión.
- La anécdota es del personaje (Victoria es IA y está etiquetada); nunca se presenta como dato ni testimonio real.
- Sin guiones largos en el texto (consejo útil: se lee más humano).
- Entra en el 10 % de "pruebas" del reparto (ESTRATEGIA_POR_RED): no cambia pilares antes del 15-dic.
- Trial Reels (solo a no seguidores): el script ya los soporta (config.json → ig_reels_de_prueba), pero Meta los
  NIEGA a @victoriatheceo: "la cuenta no alcanza el mínimo de seguidores" (probado el 10-nov y el 13-nov con 62
  seguidores; Meta no dice el mínimo). Desde el 14-nov lo revisa solo scripts/variantes.py probar (200+ seguidores o
  cada lunes) y, cuando Meta acepte, las variantes de ganadores salen como Trial Reels (nuestro BuzzFy).

10 ideas (teorías reales):
1. Efecto Diderot: "Cuando me compré mi primer bolso caro, mi mentora me contó sobre el efecto Diderot…" (una compra
   jala otras; Denis Diderot y su bata nueva, ensayo de 1769).
2. Ley de Parkinson del gasto: "Cuando me subieron el sueldo y seguía sin ahorrar…" (C. Northcote Parkinson, 1960: el
   gasto sube hasta alcanzar el ingreso).
3. Efecto latte: "Cuando sentía que no me alcanzaba…" (David Bach: gastos hormiga diarios × 365).
4. Adaptación hedónica: "Cuando el coche nuevo dejó de emocionarme en un mes…" (Brickman y Campbell, 1971).
5. Contabilidad mental: "Cuando gasté todo mi aguinaldo en una semana…" (Richard Thaler, Nobel 2017: el "dinero extra"
   se gasta más fácil).
6. Págate primero: "Cuando trabajaba en mi primer empleo…" (George S. Clason, El hombre más rico de Babilonia, 1926).
7. Kakeibo: "Cuando no sabía en qué se me iba la quincena…" (Hani Motoko, 1904: libreta japonesa de 4 preguntas).
8. El experimento del malvavisco: "Cuando quería todo YA…" (Walter Mischel, Stanford: aguantar para ganar más).
9. Regla del 72: "Cuando pensé que ahorrar no servía de nada…" (72 ÷ tasa = años para duplicar; solo como cuenta, sin
   recomendar productos).
10. Método bola de nieve: "Cuando tenía tres tarjetas al tope…" (pagar primero la deuda más chica para ganar impulso).
