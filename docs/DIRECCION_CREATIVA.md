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
- En videos hablando, el encuadre sigue siendo de pecho para arriba con Capital pegado a ella (PIPELINE paso 3).

Cada locación se genera una vez como imagen maestra y se reutiliza (su yate, su jet), para que el
mundo del personaje sea consistente.

## Vestuario

Nunca se repite: cada combinación (prenda + color + tela) queda registrada como usada. El vestuario
siempre corresponde a la locación (tabla anterior).

## Actitud y estilo: "sexy entrepreneur", con elegancia (Rodrigo, 12-nov-2026)

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
