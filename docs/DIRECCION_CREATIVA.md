# Dirección creativa v2

## Personaje

Empresaria y dueña de empresas, enorme en negocios. Es un **personaje ficticio creado con IA** y se
presenta así: la bio y cada post lo dicen. Nunca se afirma que es una persona real con empresas reales.

## Pilares (rotan en este orden)

1. Ideas de negocio
2. Consejos de vida
3. Motivación económica
4. Salud mental: bienestar y hábitos. Nada clínico: sin diagnósticos, sin tratamientos, sin hablar de
   métodos de autolesión.
5. Finanzas: principios (ahorro, deuda, interés compuesto). Nunca "compra tal acción o cripto".

Cada idea cita su fuente (libro, estudio o autor) en pantalla.

## Locaciones (Rodrigo, 12-nov-2026: "palcos, yates, oficinas, home office, departamentos con vistas increíbles... que la ropa siempre vaya ad hoc a donde esté")

La ropa SIEMPRE va con el lugar, con el estilo B aprobado (sección "Actitud y estilo"). Claves de `plan.json →
locaciones_nuevas` (se genera cada una una sola vez y se reutiliza) o de `manifest.locaciones_lujo` / `cuartos`.

| Locación (clave) | Vestuario que le corresponde |
|---|---|
| Palco de teatro (`palco_teatro`) | Vestido de noche negro o esmeralda, aretes largos dorados |
| Yate (`yate`) / velero (`barco_velero`) | Vestido de lino blanco o camel, lentes de sol, sombrero de ala ancha |
| Oficina ejecutiva (`oficina_ejecutiva`, `oficina`) | Blazer entallado sobre blusa o camisola de satín (foto de referencia: `assets/fotos/estilo-b-oficina-1.jpg`) |
| Home office (`home_office`) | Suéter fino o blusa de seda, pelo suelto, joyería mínima |
| Departamento con vista (`depa_vista`) | Vestido midi ajustado o pantalón de vestir con blusa de satín |
| Jacuzzi en rooftop (`jacuzzi`) | Bata de seda o traje de una pieza elegante; sentada en la orilla o con el agua al pecho; encuadre de hombros para arriba |
| Jet privado (`jet`, `jet_cabina`) | Traje sastre o pantalón palazzo con blazer |
| Coche de lujo (`coche`) | Blazer y lentes de sol, sin logotipos de marca |
| Estudio de podcast (`estudio_entrevista`) | Blazer de color (rojo, esmeralda, camel) sobre camisola |
| Bar speakeasy (`bar`) | Vestido de cóctel |
| Campo de golf (`golf`) / club de golf (`club_golf`) | Polo ajustado, falda plisada o pantalón blanco, visera |
| Cancha de tenis (`tenis`) | Vestido de tenis blanco, gorra o banda, sin marcas |
| Palco de estadio (`palco_estadio`, `palco_estadio_nfl`) | Blazer con jeans de diseñador o vestido de punto |
| Estadio vacío, yarda 50 (`estadio_yarda_50`) | Chamarra de piel o blazer, jeans y botines |
| Esquí (`esqui`) | Traje de esquí entallado blanco o negro, gogles en la cabeza |
| Restaurante caro (`restaurante_fino`, `restaurante`) | Vestido de noche o slip dress de satín con blazer sobre los hombros |
| Lobby de hotel (`hotel`) | Traje sastre de color |
| Sala de Navidad (`sala_navidad`) | Suéter de punto fino y pantalón de vestir |
| Departamento (sala, cocina, recámara, sillón) | Casual elegante |

Reglas:
- 3 de cada 4 videos en locación de lujo; 1 de cada 4 en casa (sala, cocina, home office), para que también se vea cercana.
- El lugar va con el TEMA: lo de salario mínimo, renta y deudas va en casa, home office u oficina (si habla de ganar
  el mínimo desde un yate, la gente se burla y no le cree). Los yates, jets, palcos, esquí y restaurantes van con temas
  de negocio, metas, aguinaldo bien usado, ahorro, "piensa como CEO" y opinión.
- Nunca logos de marcas ni de equipos (estadios, golf, tenis, coches, jet): genéricos y sin texto.
- "Caminando hacia la cámara" (bar) se usa en FOTOS (portadas de carrusel). En los videos hablando no: el modelo anima
  la cara desde una foto fija y caminar es lo que más falla en los labios.
- En videos hablando, el encuadre sigue siendo de pecho para arriba; Capital solo si el lugar lo pide (su casa, oficina o estudio) y no siempre (Rodrigo, 12-nov-2026: "no siempre tiene que salir Capital").

Cada locación se genera una vez como imagen maestra y se reutiliza (su yate, su jet), para que el
mundo del personaje sea consistente.

## Vestuario

Nunca se repite: cada combinación (prenda + color + tela) queda registrada como usada. El vestuario
siempre corresponde a la locación (tabla anterior).

## Actitud y estilo: "sexy entrepreneur", con elegancia (Rodrigo, 12-nov-2026)

Ampliado el 13-nov-2026 (Rodrigo): la sensualidad es parte de su personalidad, no solo de la ropa: sofisticada, segura,
carismática, ligeramente coqueta, vulgaridad 0 %. Movimientos naturales y elegantes con gestos pequeños; la dosis baja en
pensión y temas delicados (autoridad primero) y sube en temas ligeros. Detalle en PERSONAJE.md → "Identidad".

APROBADO: el estilo "B" (Rodrigo, 12-nov-2026: "Está perfecta la B"). Referencias: `assets/fotos/estilo-b-oficina-1.jpg` y
`estilo-b-oficina-2.jpg`: blazer negro sobre camisola de satín con escote en V suave, collar y aretes dorados, reloj
dorado, labios rojos, delineado ahumado suave, ondas cobrizas con volumen sobre un hombro, mano en el pelo, media
sonrisa y mirada directa y coqueta. Ese es el nivel: ni más conservador (la versión A se veía "súper conservadora") ni
más provocativo.

"Un poquito más coqueta, sensual. Nada sexoso, solo sexy entrepreneur... con elegancia." Cómo se traduce:
- SÍ: segura y encantadora. Sonrisa cálida y un poco traviesa, mirada directa a cámara con complicidad, alguna ceja
  levantada, postura erguida, gestos de manos finos. Maquillaje pulido (labios rojos o nude, delineado suave), pelo
  rojo con volumen y bien peinado, accesorios dorados discretos (aretes, pulsera, reloj).
- SÍ en ropa: prendas a la medida que favorecen la figura sin enseñar: blazer entallado, vestido midi ajustado, blusa
  de seda con un botón abierto, suéter fino, pantalón de vestir de talle alto, tacones. Colores de marca: rojo, negro,
  crema, verde esmeralda, camel.
- SÍ (estilo B): escote en V suave en camisolas y vestidos, pelo suelto con volumen, mano en el pelo, mirada coqueta.
- NO: escotes como protagonista, ropa interior o transparencias, poses de cama o de espalda, encuadres que se centran
  en el cuerpo, gestos o textos con doble sentido. Lo coqueto va en la mirada, la sonrisa y la actitud, no en el cuerpo.
- La regla para decidir: ¿lo usaría una empresaria segura en una sesión de fotos para una revista de negocios? Si sí, va.
- En el prompt de la foto base: "flirty, alluring 'sexy entrepreneur', glamorous and confident, tasteful and
  Instagram-appropriate", la ropa de la tabla de Locaciones, "glamorous makeup: classic red lip, soft smoky winged liner;
  voluminous tousled glossy copper waves", "sultry, confident half-smile and a teasing direct gaze into the lens",
  "no lingerie, no nudity". En el video: scripts/video_replicate.py ya trae la actitud.

## Videos largos: Victoria y lámina intercaladas (Rodrigo, 12-nov-2026: "ME GUSTA ESO DE QUE ELLA HABLE Y SALGA, ESO VENDE MUCHÍSIMO MÁS QUE UN SLIDE SHOW")

Regla fija: Victoria a cámara → lámina/gráfica/pasos → Victoria → lámina... Nunca dos láminas seguidas. Cada toma de
Victoria es una frase natural (8-25 palabras) que presenta la lámina que viene o reacciona a la anterior, como alguien
que habla, no un resumen. `scripts/largo.py intercalar <id>` lo hace solo en guiones viejos (la primera frase de la
segunda lámina pasa a Victoria). Costo: ~$0.30-0.45 USD por toma; un largo de 6 min ≈ $6-7 USD.

## Capital, el Rottweiler

Un solo perro fijo, con hoja de referencia propia (`assets/rottweiler-hoja.png`): Rottweiler adulto,
collar de piel negro con placa dorada. Aparece en **todos** los videos, a su lado y dentro del cuadro
de principio a fin. (El pomerania blanco quedó descartado.)

## Personas de fondo

En 1 de cada 3 videos: mesero, piloto, bartender, caddie, socios de negocios. Siempre fuera de foco
(se ven elegantes y se esconden mejor los errores de caras). Se generan nuevas cada vez; no se repiten.

## Movimiento

Plano medio con movimiento lateral lento. **Nada de acercamientos fuertes**: en el video 01 la cámara
se acercó y sacó a Capital del cuadro. Caminar mientras habla, solo de vez en cuando: es lo que más
falla en lip-sync.

## Subtítulos

Quemados en el video. Tipografía Inter, blanca con sombra suave, 2-4 palabras por línea, la palabra
clave en dorado, en el tercio inferior sin tapar la cara. Sincronizados con la voz real
(reconocimiento de voz), no con tiempos estimados.

## Los primeros 3 segundos

- Victoria dice el gancho en el segundo 0: sin "hola", sin presentarse, sin pausa. El control de
  calidad recorta cualquier silencio inicial de más de 0.4 s (`docs/PIPELINE.md`, paso 5).
- El subtítulo del gancho aparece desde el primer cuadro.
- Medido en otros canales: menos de 35 % de abandono al inicio dio 934 de alcance; más de 45 %, 194
  (`docs/REGLAS_APRENDIDAS.md`, regla 23).

## Lo que no se hace

- Logotipos o marcas reales (Ferrari, Rolex, nombres de estadios): riesgo de marca registrada.
- Consejos de inversión específicos o de salud mental clínica.
- Fingir que es una persona real.

## Victoria dinámica: nada de la misma pose (Rodrigo, 12-nov-2026: "es lo mismitititito, solo cambió el fondo y la ropa… sé más dinámica: que camine a la cámara, que se siente, que esté cocinando, un café, un trago, vino, cosas diferentes")

- **Prohibido repetir la selfie** (brazo derecho estirado hacia la cámara). Máximo 1 de cada 5 fotos o clips puede ser selfie.
- **La cámara es otra persona** (tercera persona): plano medio o americano, a veces de cuerpo entero, a veces de cerca. Cambia el ángulo entre tomas.
- **Siempre haciendo algo**: camina hacia la cámara con Capital con correa, se sienta y cruza la pierna, cocina en una cocina de lujo, toma café o espresso, brinda con vino o un coctel, lee en un sillón de piel, trabaja en la laptop riéndose, revisa el celular caminando, se acomoda el saco, acaricia a Capital, abre la puerta del coche, sube al jet.
- **Lugar, ropa y acción van juntos** (tabla de locaciones): vino en el rooftop al atardecer con vestido, café en la terraza con blazer, cocina con ropa casual elegante.
- **Capital siempre visible** y tranquilo; manos naturales, sin texto ni logos, nunca provocativa.
- Las fotos nuevas van en `assets/fotos/dinamica-<escena>.jpg` y los clips en `assets/broll/` (catalogo.json dice la acción). `reel_texto.py` mezcla acciones distintas en cada Reel.

## Capital con criterio y todo realista (Rodrigo, 12-nov-2026: "¿por qué tu perro estaría en un yate? ¿en la montaña? ¿en el estadio?… siempre lo acaricia de la misma forma… siempre realista los fondos, ropa, todo… ten criterio")

- **Capital sale solo donde un perro de verdad estaría**: su depa (sala, cocina, terraza), su oficina, su estudio de podcast, el coche (asiento de atrás), paseando en la calle o el parque, el lobby de su edificio y terrazas de café que aceptan perros.
- **Sin Capital**: bar, restaurante, antro, estadio, palco, nieve/esquí, yate, jet, golf, tenis, jacuzzi, tiendas de lujo.
- **Capital hace cosas distintas**: camina con correa, está echado, duerme, mira por la ventana, se asoma al coche. Nunca la misma caricia ni siempre sentado posando. A veces no sale aunque esté en casa.
- **Realismo**: el lugar existe y se ve como en la vida real (nada de fondos de catálogo); la ropa va con el lugar y la hora; la acción tiene sentido (cocina con ropa cómoda, vino al atardecer, café en la mañana); manos y objetos naturales; sin logos ni marcas legibles (si salen, se difuminan con borde suave).
- **Repertorio grande, pocas repeticiones**: cada mes se suman escenas nuevas (la tarea del día 23 con Everygen); `reel_texto.py` usa lo menos usado (`assets/broll/uso.json`). Escenas ya hechas: lobby, café, cocina, terraza del depa, lectura, calle, estudio, restaurante, bar, coche. Faltan: gimnasio/pilates, súper (comparando precios), banco/cajero, junta de negocios, mercado mexicano, aeropuerto, playa, golf, tenis, palco, departamento con vista de noche, home office en pijama elegante, firma de contrato, revisando estados de cuenta en la mesa.

## Trends virales (Rodrigo, 12-nov-2026: "a veces que Victoria haga algún trend viral, para hacerla más realista, tipo baile, o algo así")

- **Una vez a la semana** Victoria hace un trend del momento (baile corto, transición, gesto viral) con su estilo: elegante, segura, con humor, nunca provocativa. Si el trend se presta, le pega un dato de dinero en texto ("POV: ya te cayó el aguinaldo").
- **Cómo se hace**: Everygen `generate_video` con `motionGuide` (Kling 3.0): `characterImageUrl` = una foto de Victoria de cuerpo entero (assets/fotos/dinamica-*) y `videoUrl` = el clip de referencia del trend (3-15 s, sin texto encima). Victoria copia el movimiento con su ropa y su lugar.
- **El audio del trend** se pone en la app al publicar (TikTok/Instagram, con su sonido en tendencia), nunca dentro del archivo.
- **Realista**: lugar y ropa que tengan sentido para bailar (su sala, su terraza, la oficina después del trabajo); Capital solo si está en casa y a veces se suma moviendo la cola. Si el movimiento sale raro (piernas o manos deformes), se descarta.
- Sale de los créditos de Everygen (nunca Replicate).

## Repertorio completo: usar TODOS los lugares (Rodrigo, 12-nov-2026: "que esté en el yate, alberca, jacuzzi, montaña de esquiar, cancha de tenis, campo de golf, oficina, estadio, avión privado… hangar de helicóptero, un helicóptero, lobby, la calle, estudio de podcast, su sillón, su cuarto, ubicaciones TOP del mundo… usa TODOS")

**Lugares (todos se usan, rotando, ninguno se repite seguido):** yate · alberca infinita · jacuzzi (elegante, nunca provocativo) · montaña de esquí · cancha de tenis · campo de golf · su oficina · estadio vacío en la yarda 50 · palco · avión privado · hangar de helicópteros · helicóptero · lobby de su edificio · la calle de su colonia · su estudio de podcast · su sillón · su cuarto · su cocina · su terraza · café · restaurante · bar · coche · y lugares TOP del mundo (París, Nueva York, Tokio, Dubái, Santorini, Mónaco, Aspen, Cancún, Tulum, la Ciudad de México en Reforma y Polanco…), siempre sin logos ni marcas.

**Acciones con el fondo (que haga cosas):** maquillándose, tomando vino, cocinando, preparando café, brindando, leyendo, firmando un contrato, revisando estados de cuenta, en una junta, caminando hacia la cámara, subiendo al helicóptero o al jet, jugando tenis o golf, esquiando, saliendo de la alberca con bata, trabajando en la laptop, grabando el podcast, eligiendo ropa, haciendo ejercicio, en el súper comparando precios, paseando a Capital.

**Capital** sigue la regla "Capital con criterio": en su casa, oficina, estudio, coche, paseos y terrazas sí (y a veces no); en el yate, la alberca, el jacuzzi, la nieve, las canchas, el golf, el estadio, el palco, el jet, el helicóptero, bares, restaurantes y viajes, no.

**Ya hechas (12-nov):** lobby, café, cocina, terraza, lectura, calle, estudio, restaurante, bar, coche, yate, helipuerto, alberca, cuarto maquillándose. Lo que falta de la lista se hace con Everygen el día 23 de cada mes y cuando haya créditos.

## Victoria hablando: súper mega realista (Rodrigo, 12-nov-2026: "Replicate no pasa nada, si es necesario úsalo para hacer más shorts y cosas en que ella salga hablando, pero TIENE QUE SER SÚPER MEGA REALISTA")

- **Foto base**: una escena del repertorio dinámico (assets/fotos/dinamica-*) o una nueva hecha igual: tercera persona, Victoria mirando a la cámara de frente o a tres cuartos, cara bien iluminada y nítida, de cintura o pecho para arriba, en un lugar real (su cocina, su estudio, su terraza, el café, el coche estacionado, la oficina). Nada de selfies ni de la sala roja de siempre.
- **Lo que dice**: frases cortas y naturales, como habla una persona; al menos 4 palabras que empiecen con p, b, m o v por toma (así se revisan bien los labios) y sin cifras largas dichas en voz (las cifras van en pantalla). `largo.py victoria` ya no deja pagar tomas con frases que no cumplen.
- **Movimiento**: el de alguien que platica: parpadea, mueve un poco la cabeza y las manos, sonríe entre frases. Nunca rígida ni exagerada.
- **Revisión**: labios con qa_labios.py (y qa_sync.py si no se puede medir); además 6 cuadros a ojo: la cara igual en todo el clip, manos naturales, fondo sin deformarse. Si algo se ve falso, no se publica.
- **Shorts de 15 a 30 s** (≈$0.70–1.40 cada uno en Replicate): un solo dato fuerte, gancho en el primer segundo y el texto clave en pantalla.

## Movimiento real en las escenas (12-nov-2026)
Rodrigo: "haz más escenas con movimiento real, no importa el gasto de Replicate".
- `scripts/video_broll.py <escena> "<acción>"` anima la foto `assets/fotos/dinamica-<escena>` con Seedance 1 Pro
  (Replicate, 1080p vertical, 5 s, ≈ $0.75 por clip) y la deja en `assets/broll/<escena>-mov-N.mp4` + catálogo.
- Corre con `REPLICATE_AUTORIZACION=broll-movimiento` (autorización escrita en config.json; tope $12).
- QA: 4 cuadros por clip. Se tira si: cara distinta, manos deformes, Capital acariciado o raro, texto o logos.
- Cuando una escena ya tiene clip con movimiento, `reel_texto.py` deja de usar la foto fija de esa escena.
