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

## Locaciones

| Locación | Vestuario que le corresponde |
|---|---|
| Gimnasio de lujo | Conjunto deportivo de diseñador (leggings, top, chamarra ligera) |
| Jacuzzi en rooftop | Traje de baño de una pieza elegante, bata de seda a la mano |
| Bar tipo speakeasy | Vestido de cóctel |
| Yate | Lino blanco o vestido de verano, lentes de sol |
| Jet privado | Traje sastre o pantalón palazzo con blazer |
| Coche de lujo | Blazer, lentes de sol, sin logotipos de marca visibles |
| Restaurante de lujo | Vestido de noche |
| Lobby de hotel | Traje sastre de color |
| Campo de golf | Polo, falda plisada, visera |
| Plaza de toros vacía | Vestido midi con sombrero de ala ancha |
| Palco de estadio vacío | Blazer con jeans de diseñador |
| Departamento (sala, oficina, cocina, recámara, sillón) | Casual elegante |

Regla: 3 de cada 4 videos en locación de lujo, 1 de cada 4 en el departamento.

Cada locación se genera una vez como imagen maestra y se reutiliza (su yate, su jet), para que el
mundo del personaje sea consistente.

## Vestuario

Nunca se repite: cada combinación (prenda + color + tela) queda registrada como usada. El vestuario
siempre corresponde a la locación (tabla anterior).

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
