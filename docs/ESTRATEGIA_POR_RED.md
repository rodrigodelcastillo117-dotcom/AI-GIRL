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
   si no es serie, la firma fija "Soy Victoria, la CEO (personaje con IA). Sin humo, con números: sígueme y mañana te doy el siguiente dato."
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
2. **El short RESUELVE la duda por sí solo** (corregido 13-nov tras la auditoría competitiva: un short incompleto deja
   insatisfecho al que lo ve). El largo del tema es continuación opcional: "si quiere el cálculo completo, está en el
   canal", con su enlace en la descripción y en el comentario propio (y como video relacionado en Studio si la API no
   lo permite: lo hace Rodrigo).
3. **Temas en orden** (todos con dos fuentes oficiales; montos no publicados = "aún no oficial", nunca inventados):
   aguinaldo de pensionados y fechas de pago dic/ene · Pensión Bienestar 2027 "confirmado vs. rumor" · Modalidad 40 tras
   el cambio del DOF (ángulo "si ya está inscrito") · cómo revisar semanas cotizadas · pensión mínima garantizada 2027 ·
   qué pasa con la pensión/Afore al fallecer (beneficiarios) · fraudes a pensionados y "¿si mi banco quiebra?" (IPAB) ·
   Ley 73 vs Ley 97.
4. **Miniatura fija**: cara de Victoria (con etiqueta IA), 3-4 palabras en mayúsculas y una cifra o fecha. Sello
   CONFIRMADO / RUMOR / NO VERIFICADO solo cuando corresponda, con fuente y fecha (PERSONAJE.md → Identidad, regla 1). Nunca caras ni logos del gobierno (riesgo de suplantación).
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

## Reparto de temas por red (hipótesis 13-nov; se revisa el 15-dic con seguidores por 1,000 vistas)
Bio corta (todas las redes, la cambia Rodrigo a mano): "Victoria, la CEO · personaje con IA 🤖 / Sueldos, pensiones y
tu dinero en México 🇲🇽 / Sin humo. Con números." Nunca "no te vendo nada" (vendemos el Kit CEO).
Promesa del canal (descripción de YouTube y página): "el dinero que ganas, recibes, gastas y necesitas para vivir" (pensión, sueldo, derechos laborales,
bancos, deudas, decisiones de familia; todo bajo esa promesa, nada fuera).
Solo YouTube tiene dato de edad (57 % de 55+, YouTube Analytics). Facebook (4 seguidores), TikTok e Instagram NO tienen
evidencia de edad: su columna es hipótesis y se corrige con sus propios resultados.
| Tema | YouTube y Facebook | TikTok e Instagram |
|---|---|---|
| Pensión, IMSS, Afore, retiro | 40 % | 10 % (ángulo "si tus papás cobran pensión") |
| Sueldos, aguinaldo, finiquito, derechos laborales | 30 % | 50 % |
| Ahorro, deudas, cuentas del día a día | 20 % | 30 % |
| Pruebas (pareja y dinero, negocio) | 10 % | 10 % |
Nota honesta: parejas (83) y vacaciones (91) fueron UN post cada uno y de carruseles no hay retención ni impresiones;
son señal débil, no prueba de que el tema no sirva. Por eso quedan en el 10 % de pruebas, no fuera.
Se mantienen fijos temas y series 2-4 semanas; se ajustan cada semana primer segundo, duración y presentación.
Modelo de primer segundo por red (pensión hipotética de $12,000, dicho como hipotética): TikTok "Te jubilaste y
recibes $12,000 al mes. ¿Qué sacrificas primero?" · Instagram "Si tus papás viven de su pensión, vale la pena hacer
esta cuenta" · YouTube "¿Alcanza una pensión de $12,000 para vivir en México?" · Facebook "Después de toda una vida
trabajando, llega una pregunta difícil: ¿para cuánto alcanza la pensión?"

## Revisión semanal (domingos) — ajusta EJECUCIÓN, nunca los pilares (Rodrigo, 13-nov)
Cuatro preguntas, por red: ¿qué series dan más seguidores por cada 1,000 vistas? ¿qué primeros segundos retienen más?
¿qué temas repiten resultado (no un viral aislado)? ¿qué formato funciona en esta red? Regla: ninguna serie o formato
se declara ganador con un solo video; mínimo 3 publicaciones comparables (misma red, edad parecida). Desde el 16-nov,
además, compara piezas con y sin cada rasgo de personalidad (campo `rasgos`, PERSONAJE.md → Identidad): se conserva el
rasgo que mejore seguidores o comentarios por 1,000 vistas y se quita el que no. Temas, series y
reparto no se tocan hasta el 15-dic.

## Auditoría competitiva México (13-nov, la trajo Rodrigo) — se toma solo ejecución
- **Largo semanal de pensión = formato "Victoria resuelve":** pregunta real → regla aplicable (fuente) → ejemplo
  resuelto con supuestos explícitos → resultado y condiciones que lo cambian → lista de lo que debe revisar. 8-14 min.
- **Las cuentas se ven:** datos de entrada, operación, resultado y condiciones aparecen en pantalla mientras habla.
- **Short de 45 s (modelo):** 0-3 pregunta · 3-8 regla · 8-29 cuentas visibles · 29-39 resultado y supuestos
  (proporcional, impuestos) · 39-45 cierre. Cierre firma opcional: "Aquí hacemos cuentas, no promesas."
- **Ideas para las series existentes (sin reordenar la cola):** "¿Cuánto le corresponde de pensión con su régimen y
  semanas?" (YouTube largo) · "Si ganas $12,000, $18,000 o $25,000, ¿cuánto aguinaldo te toca?" (TikTok) · "Tres errores
  al revisar tu finiquito" (Instagram) · "¿Es cierto que habrá un pago adicional para pensionados?" (Facebook, Victoria
  verifica, solo con fuente vigente) · "¿Conviene pedir un préstamo para pagar deudas?" (Shorts) · "Victoria responde:
  ¿por qué mi nómina no coincide con mi sueldo?" (TikTok/Instagram).
- **Panel de 5 referentes para la revisión semanal** (solo mirar qué despuntó en la semana, nunca copiar afirmaciones):
  Princesa Godín (TikTok), Rafa Hurtado y Pensión a la Medida (YouTube especializado), Las Pensiones Bienestar
  (actualidad), Moris Dieck (marca multiplataforma).
- **Métricas que se suman:** errores de datos detectados y correcciones publicadas; clics al Kit CEO y ventas por red.
- **Riesgo abierto:** los datos los revisa un segundo agente de IA contra fuentes oficiales, no un experto humano. Para
  montos de pensión se recomendó a Rodrigo una revisión humana (contador o abogado laboral) del largo semanal: decisión
  suya, pendiente.

## Plan por red con fórmula propia (13-nov, lo trajo Rodrigo) — se toma solo esto
- **Expediente maestro por tema:** antes de producir un tema de pensión o derechos laborales se escribe
  contenido/expedientes/<tema>.json (pregunta, fuentes oficiales con fecha de consulta, fórmula, supuestos, ejemplos,
  preguntas frecuentes). De ahí salen el largo, los shorts, el carrusel y el post de Facebook con arranque, duración
  y cierre distintos por red. Una investigación verificada, varias piezas originales.
- **Etiqueta de IA de cada plataforma, no solo la bio:** YouTube ya se marca como sintético al subir directo
  (youtube.py → containsSyntheticMedia). Lo que sale por Publer (TikTok, Instagram, Facebook) hoy NO lleva la etiqueta
  de la plataforma: en revisión si la API de Publer la permite; si no, Rodrigo la activa a mano o se sube distinto.
- **Stories de Instagram para comunidad y Kit:** encuestas y preguntas son stickers que la API no pone; las hace
  Rodrigo a mano cuando quiera (1-2 por semana), con presentación transparente del Kit CEO.
- **NO se adopta su tabla de volumen semanal** (TikTok 3 videos + 2 carruseles, etc.): bajaría TikTok de ~21 a 5 piezas
  por semana y subiría los videos con costo; Rodrigo decidió mantener el volumen. Se revisa el 15-dic con datos.

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
