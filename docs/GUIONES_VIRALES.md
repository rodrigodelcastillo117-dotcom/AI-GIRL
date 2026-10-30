# Guiones virales de Victoria

Meta del canal: **monetizar**. Para eso cada guion se escribe para maximizar que se vea completo,
se vuelva a ver, se guarde y se comparta. Ningún guion garantiza ser viral; lo que sí se controla
es que cada uno cumpla esta lista, y el laboratorio (`scripts/aprender.py`) dice cuáles funcionan
con datos de Victoria.

## Lista obligatoria (12 segundos, máximo 28 palabras)

1. **Gancho en el segundo 0** (regla 23, reglas y fórmulas en `docs/GANCHOS.md`): la primera frase sola, de máximo 10 palabras, tiene que detener el dedo. Formas
   que funcionan: una cifra real que sorprende ("El 1% diario te hace 37 veces mejor"), una
   contradicción ("Ahorrar no te va a hacer rico"), un error que la persona comete ("Estás
   perdiendo dinero cada vez que…"), un nombre que la gente busca (Buffett, Bezos, Harvard).
2. **Una sola idea**, aplicable hoy. Si necesita dos ideas, son dos videos.
3. **Dato real y comprobado** con fuente (regla 7). Nada inventado ni exagerado: si el gancho
   promete más que el video, la gente se va y el algoritmo lo castiga.
4. **Curiosidad que se cierra al final**: el gancho abre una pregunta en la cabeza y la última
   frase la responde. No se resuelve en la primera frase.
5. **Final que invita a volver a verlo**: la última frase conecta con la primera o deja una acción
   concreta ("Esta noche: papel, pluma y quince minutos").
6. **Algo que valga la pena guardar o mandar**: una regla, una cifra, un método. La invitación
   ("Guárdalo", "Mándaselo a quien…") va en el pie del post, no en el audio.
7. **Frases cortas**, ritmo rápido; números en dígitos en los subtítulos.
8. **Palabra clave real** en la primera frase dicha (lo que la gente busca), que también abre el
   título (docs/SEO.md).
9. **Opinión firme sin mentir**: Victoria habla con seguridad de empresaria, no con "tal vez".
10. **Tres ganchos por guion**: al escribir, propone 3 primeras frases (`ganchos_alternativos` en el
    plan) y usa la más específica y sorprendente. Las otras dos quedan para probarlas después.

11. **Que se mande**: lo que más reparte un reel a gente que no te sigue es que lo manden por
    mensaje. Cada guion tiene que ser algo que alguien le mandaría a su pareja, a su amigo o a su
    grupo de WhatsApp: útil para México, concreto y con una cifra o una regla que sirve hoy
    (aguinaldo, tarjeta, sueldo, ahorro, negocio). Las frases célebres solas se mandan poco: úsalas
    solo si la idea se aplica hoy con un ejemplo en pesos.

## Qué decide el laboratorio

El tipo de gancho (cifra, contradicción, error, nombre, regla, dato, cita), el tema, el fondo, la
vestimenta y el título se comparan por vistas a 36 h y retención de YouTube. Los guiones nuevos
usan 6 de 10 veces lo que gana y 4 de 10 prueban algo distinto (`docs/PIPELINE.md`, paso 1c).

## Monetizar (lo que hay que saber)

- **El dinero sale del embudo propio, no de las plataformas.** Página
  (`config.json → enlace_venta`) → guía gratis → plantilla de $231.76 MXN con IVA en Hotmart
  (`pago_hotmart`). Cada video empuja ahí con `?ref=` por red (reglas 20, 24, 25 y 26).
- **Videos puente (3 de cada 10 guiones nuevos):** el tema es algo que la plantilla resuelve
  (presupuesto 50/30/20, págate primero, fondo de emergencia, deudas bola de nieve o avalancha,
  interés compuesto, regla del 72, metas). El guion da la regla completa y una acción para hoy; en el
  plan llevan `"puente_producto": true` y `seo.py` cambia el llamado del pie y el comentario de
  YouTube a la plantilla. El audio no vende: el valor va completo en el video.
- **YouTube no va a pagar a Victoria** (comprobado el 29-oct-2026): desde julio de 2026 su política de
  monetización excluye los canales con "AI-generated personas" que dan información de temas
  sensibles (salud, finanzas, temas legales); su ejemplo: "AI-generated podcast hosts offering financial
  guidance". YouTube es tráfico hacia el embudo, no ingreso por anuncios. No se persiguen las metas del
  Programa de Socios. https://support.google.com/youtube/answer/1311392
- **TikTok** (Programa de Recompensas en México desde octubre de 2025): 10,000 seguidores, 100,000 vistas
  en 30 días, cuenta personal y videos originales de más de 1 minuto; los de 12 segundos no cuentan.
  No está comprobado si acepta un personaje hecho con IA.
- **Instagram** no tiene un pago general por Reels.
- **Afiliados de Hotmart:** otros pueden vender la plantilla a cambio de una comisión (se activa en
  Hotmart; no cuesta nada hasta que hay una venta).
