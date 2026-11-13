# Estrategia por red (13-nov-2026)

Rodrigo: "¿podemos mejorar todo? diferentes estrategias para cada red… adaptada a lo que sí funciona… analiza videos del
nicho, mercado… y copia, por red social". Se investigó cada red con un agente (cuentas que crecen en finanzas personales
MX/LatAm, búsqueda web + revid search_viral_videos) y se cruzó con nuestros números. Se copian FORMATOS y estructuras,
nunca guiones ni videos ajenos (Instagram y Facebook bajan el alcance del contenido no original desde 2026).

## El problema que se ataca (números del 13-nov)
- Vistas: 11,277 esta semana vs 5,188 la anterior (+117 %). Pero NO se vuelven audiencia:
  YouTube 5,016 vistas en 30 días y −1 suscriptor neto; TikTok +88 seguidores en 2 meses; Instagram 62, plano; Facebook 4.
- Métrica que manda desde hoy: **seguidores/suscriptores netos por semana y por red**, no vistas.
- Revisión de decisión: **15-dic** (ver final).

## Lo que ya nos funcionó (datos propios, metricas.json)
| Red | Gana | Pierde |
|---|---|---|
| TikTok | carruseles "Guarda esto" con datos (c16: 3,959 vistas, 14 compartidos); aguinaldo | parejas, vacaciones, opinión a cámara (O1: 84) |
| YouTube | noticia "un banco quebró" (849), Victoria opinando (O1 769), Victoria hablando de aguinaldo (~700), serie salario mínimo (516) | carruseles convertidos a short (0-15) |
| Instagram | solo Victoria hablando (20-40) | carruseles (6-10) |
| Facebook | nada (0-6) | todo |

## TikTok — convertir vistas en seguidores (red principal de volumen)
Lo que hacen las que crecen (@elsrpromotor 719k, @digittmx 537k, @samaniego2113 373k, @mr.pato.sistema 583k, @futuroenpareja):
el "sígueme" va DENTRO del contenido con una razón; series con la parte siguiente prometida; responder comentarios con
contenido ("Respuesta a @"); sketches con un villano (el SAT, el banco, el jefe) le ganan 10-100× al que habla a cámara;
fechas útiles con "guárdalo y mándalo a tu familia".
1. **YA APLICADO (código):** texto de TikTok de cada carrusel lleva la parte de la serie y "mañana la parte N: sígueme";
   si no es serie, la firma fija "Soy Victoria, una IA que no te vende nada. Sígueme y mañana te doy el siguiente dato."
   (scripts/publer_carrusel.py → firma_tiktok). Diapositivas y forma de subir: igual (Rodrigo: no cambiar el formato).
2. **Series siempre**: la cola de TikTok se arma en series de 4-8 partes (la de sueldos c78-c85 es la primera). Cada
   serie nueva que se escriba: mismo formato de carrusel de "Guarda esto" + datos.
3. **"Respuesta a @"**: TikTok no da API de comentarios. Se usan los sueldos y preguntas reales que juntan YouTube e
   Instagram (contenido/preguntas.json) para carruseles "Me preguntaron: gano $X, ¿cuánto me toca?". Si Rodrigo copia
   comentarios de TikTok a mano, entran a la misma lista.
4. **Fechas con fuente**: aguinaldo (20-dic), PTU (mayo), declaración anual (abril), cuesta de enero; cierre
   "guárdalo y mándaselo a tu familia" y la fuente oficial en la foto.
5. **AUTORIZADO (Rodrigo, 13-nov): 1 sketch por semana, tope $8 al mes** (autorización `sketch-tiktok`, vence
   13-dic). 35-55 s, Victoria contra un "villano" que aparece como texto en pantalla o voz en off ("el SAT", "tu jefe y
   tu finiquito", "el pago mínimo", "el gestor que te cobra la pensión"); ella lo desarma con el dato verificado. Se
   produce con el formato escena (RUTINA → A) y REPLICATE_AUTORIZACION=sketch-tiktok. Sale el MIÉRCOLES en TikTok
   (y Reel de Instagram/Facebook si pasa QA). Si en 2 semanas no suben seguidores, se corta y se le dice a Rodrigo.

## YouTube — la audiencia es 55+ (57 %): pensión, retiro, aguinaldo de pensionados
Lo que hacen los canales que crecen (Pensión al Día MX: de 77 a 182K vistas en 3 semanas; Pensión a la Medida 179K;
Rafa Hurtado 434K; Lic. Telésforo Ávila; Espacio Curioso JCF): noticia con fecha límite ("Cambios desde el 1 de
diciembre", "Haga esto antes del 30"), 8-15 min, capítulos, fuentes en pantalla y aviso "información general";
miniatura con una cara + 3-5 palabras en mayúsculas + cifra o fecha; shorts como avance del largo ("video completo en
el canal"); listas por tema; preguntas y respuestas.
1. **Razón para suscribirse ligada a algo que se repite** (reemplaza a la genérica): en shorts y largos de pensión/
   aguinaldo: "Suscríbete: cada vez que el IMSS o el Bienestar cambien fechas o montos, te lo explico aquí". En la
   serie de sueldos sigue "cada semana hago las cuentas de un sueldo real".
2. **Shorts de YouTube = avance de un largo**: termina con "el video completo está en el canal" y el largo va en el
   comentario propio y en la descripción. 
3. **Temas en orden** (todos con dos fuentes oficiales; montos no publicados = "aún no oficial", nunca inventados):
   aguinaldo de pensionados y fechas de pago dic/ene · Pensión Bienestar 2027 "confirmado vs. rumor" · Modalidad 40 tras
   el cambio del DOF (ángulo "si ya está inscrito") · cómo revisar semanas cotizadas · pensión mínima garantizada 2027 ·
   qué pasa con la pensión/Afore al fallecer (beneficiarios) · fraudes a pensionados y "¿si mi banco quiebra?" (IPAB) ·
   Ley 73 vs Ley 97.
4. **Miniatura fija**: cara de Victoria (con etiqueta IA), 3-4 palabras en mayúsculas, una cifra o fecha y la etiqueta
   CONFIRMADO o RUMOR. Nunca caras ni logos del gobierno (riesgo de suplantación).
5. **Victoria responde** (semanal): video con 3-5 preguntas reales de comentarios (preguntas.json), en vez de lives.
6. **DECIDIDO (Rodrigo, 13-nov):** (a) **usted** en YouTube y Facebook cuando el tema es pensión o retiro (en TikTok
   e Instagram sigue de tú); (b) **1 largo de pensión por semana, tope $20 al mes** (autorización `largo-pension`,
   vence 13-dic): 8-15 min con largo.py y REPLICATE_AUTORIZACION=largo-pension, se produce el LUNES y sale el MIÉRCOLES
   18:00 en YouTube y Facebook, con 2-3 shorts de avance antes. Primero: "Aguinaldo de pensionados 2026: cuánto y
   cuándo le pagan" (IMSS Ley 73, ISSSTE, Bienestar; fechas y montos solo de fuente oficial, dos fuentes);
   (c) dejar de convertir carruseles en shorts de YouTube (0-15 vistas): se evalúa el 18-nov (tarea programada).

## Instagram — la menor prioridad hasta que repartan (62 seguidores)
Evidencia 2026 (Mosseri/Instagram): para llegar a no seguidores pesan tiempo visto, likes y sobre todo ENVÍOS por DM;
lo original gana; los Trial Reels sirven para probar ganchos con no seguidores; "comenta X y te mando" sube comentarios
pero no alcance.
1. Reels de Victoria hablando (lo único que rinde aquí) de 20-45 s, la cifra en texto grande desde el primer cuadro
   (regla de MUSE que sigue), y el llamado único pasa a ser **"mándaselo a quien…"** (envío), no guardar.
2. "Comenta GUÍA" en 1 de cada 3 publicaciones, no en todas (sirve para convertir, no para crecer).
3. Trial Reels: **no sé** si Publer los puede publicar por API; si no, Rodrigo puede marcar a mano 1 Reel al día como
   prueba desde la app. No se cambia la forma de subir los carruseles.
4. Collabs con microcuentas mexicanas (contadores, presupuesto): solo si Rodrigo consigue la cuenta; la invitación la
   manda el otro.

## Facebook — el público 55+ vive aquí
Evidencia 2026 (Meta): todo video es Reel; lo original casi duplicó vistas; se castiga lo no original, textos con
muchos hashtags y el "engagement bait" ("escribe SÍ", "comenta AMÉN").
1. Facebook recibe lo de pensión/aguinaldo de YouTube (shorts y largos) además de los Reels de Instagram, subido nativo
   por Publer (ya es así: sin marca de agua de otra red).
2. **Sin "Comenta SÍ o NO" en Facebook**: el cierre en Facebook es "Mándaselo por WhatsApp a quien cobra pensión /
   aguinaldo". Máximo 3 hashtags.
3. "Victoria verifica" (martes y viernes) es justo el formato "¿es verdad o es fraude?" que más se comparte con 55+:
   siempre con la fuente oficial en pantalla, nunca un monto no publicado.
4. Grupo "Dudas de pensión y aguinaldo — Victoria (IA)": impacto incierto; solo si Rodrigo quiere abrirlo (la API no
   crea grupos).
5. Nunca: nombres o logos que parezcan del gobierno, calendarios "tentativos" como si fueran oficiales, "ALERTA MÁXIMA".

## Contraste con el informe de ChatGPT que trajo Rodrigo (13-nov)
Se toma: (1) mismo tema, PRIMER SEGUNDO distinto por red (TikTok conflicto, Instagram identificación, YouTube pregunta,
Facebook historia); (2) "¿Quién tiene razón?" (debate de dinero) como UNA prueba dentro del sketch semanal, serie solo
si gana en seguidores; (3) métrica "seguidores por cada 1,000 vistas" por red y semana; (4) Creator Search Insights de
TikTok (lo revisa Rodrigo en la app y manda captura). No se toma: 30 % relaciones / 30 % negocios (nuestros datos:
parejas 83 vistas, vacaciones 91; YouTube es 55+ de pensión), casos "reales" que no podamos verificar (solo hipotéticos
dichos en pantalla), A/B de miniaturas (Rodrigo dijo no a Test & Compare el 13-nov).

## Qué NO se copia de la competencia
Montos de pensión no confirmados (el clickbait de "pensión para mayores de 50" es falso), caras de funcionarios en
miniaturas, mezclar información con préstamos o asesorías de pago, consejos de inversión.

## Decisión del 15-dic (pico del aguinaldo)
- Sigue igual: YouTube +100 suscriptores netos, TikTok +300 seguidores y al menos 1 venta del Kit.
- Enfocar: si solo responde YouTube 55+, se recortan TikTok e Instagram y todo va a pensión/retiro.
- Replantear: si nada se mueve aunque haya vistas, el problema es el personaje o el formato, no el volumen.

Fuentes por red: informes de los agentes del 13-nov (cuentas y URLs en el historial de la sesión): TikTok (@elsrpromotor,
@digittmx, @samaniego2113, @mr.pato.sistema, @futuroenpareja, @auromarketing_), YouTube (Pensión al Día MX, Pensiones
Mx, Rafa Hurtado, Pensión a la Medida, Telésforo Ávila, Espacio Curioso JCF, Contador Contado), Instagram (Mosseri vía
Buffer y Lindsey Gamble, about.fb.com jun-2025, PetaPixel abr-2026), Facebook (about.fb.com mar-2026, TechCrunch
jun-2025 y abr-2025).
