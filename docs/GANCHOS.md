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
