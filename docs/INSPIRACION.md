# Inspiración: qué funciona en español (dinero, negocio, emprendimiento)

Datos reales, no opiniones: `contenido/referencias.json` guarda los videos virales que se estudian,
con vistas, likes, compartidos, duración, gancho y cierre. Se sacan con la herramienta
`search_viral_videos` de Revid (TikTok, Instagram y YouTube en español), que da la transcripción
completa sin entrar a las apps.

**Regla de oro: se copia la estructura, nunca el texto.** Temas, tipo de gancho, ritmo y cierre sí;
frases, guiones y cifras de otros, no. Instagram castiga el contenido no original (lo saca de
Explorar) y copiar es plagio. Toda cifra que se tome de un video ajeno se comprueba con su fuente
original antes de usarla (regla 7): muchos de estos videos dan números sin fuente.

## A quién mirar (30-oct-2026)

| Cuenta | Por qué | Lo que se toma |
|---|---|---|
| **Marta Marcilla** (@martamarcillareflexiones) | La más parecida a Victoria: mujer, dinero y mentalidad, 20 s. 4.4 M vistas y 2.25 compartidos por cada 100 vistas | Tono de "mujer que lidera", gancho de deseo ("¿Quieres tener mucho dinero?") y una acción concreta |
| **Valu Valcárcel** (@valuvalcarcel) | 12 segundos exactos, mujer, frase célebre dicha con fuerza: 1.1 M | Frases de autores (Brian Tracy) en una sola idea |
| **Borja Álvarez** (@borjaalvarez.negocios) y **Neuromark** (@neuromark.pro) | Serie numerada de ideas de negocio con caso real y cifra: 2 a 3.7 M por video | "Idea de negocio N": quién, dónde, qué hizo y cuánto gana, y cierre que invita a la siguiente |
| **Lola Vargas** (@soylolalolitass) | Dinero y pareja con postura firme: 1 M y mucho comentario | Temas de pareja y dinero que generan conversación |
| **Leonel Rossi** (@leonel.rossi1) | Lista de ejemplos concretos en 17 s: 1.8 M | Ritmo de lista ("Pon una farmacia junto a un hospital…") y pregunta final para comentar |
| **Angel Soberanis** (@angelsolev) | Personaje hecho con IA con 3.85 compartidos por cada 100 vistas | Prueba de que un personaje de IA sí se comparte cuando tiene actitud |

## Lo que se repite en los que funcionan

- **Ganchos:** deseo en pregunta ("¿Quieres tener mucho dinero?"), caso con cifra ("convirtieron un
  plátano en un negocio que factura…"), frase de actitud, postura que divide opiniones, lista de
  ejemplos concretos, frase de un autor conocido.
- **Cierres:** "Sígueme para más ideas de negocio", "Guarda este video", una pregunta para que
  comenten ("¿Lo montarías en tu ciudad?") y series numeradas que invitan a la siguiente parte.
- **Formatos:** series numeradas (la gente sigue la cuenta para ver la siguiente), entrevista
  (en la calle o en podcast) y mujer a cámara con postura firme.

## Cómo se usa

1. **Cada lunes** se buscan los videos virales de la semana con `search_viral_videos` (idioma `es`,
   más de 300 mil vistas, temas: dinero, negocio, emprendimiento, pareja y dinero, empresas) y se
   agregan los mejores a `contenido/referencias.json`.
2. Al escribir guiones nuevos (paso 1c de `PIPELINE.md`) se revisan las referencias: 3 de cada 10
   guiones adaptan un tema o una estructura que esté funcionando esa semana.
3. El laboratorio compara con los datos de Victoria; si una estructura copiada no rinde con su
   audiencia, se deja.
