# AI-GIRL

Personaje IA (pelirroja, ojos verdes, pecas, empresaria) que publica un video de 12 segundos cada
2 días en Instagram, TikTok y Facebook, siempre con su Rottweiler y con subtítulos en español.

- `docs/MARCA.md`: opciones de nombre, biografías y texto de publicación.
- `docs/DIRECCION_CREATIVA.md`: pilares, locaciones, vestuario, perro y subtítulos.
- `docs/AUDITORIA.md`: auditoría de nicho y monetización.
- `docs/ARQUITECTURA.md`: flujo automático, componentes y presupuesto.
- `assets/`: hojas de personaje y del perro, locaciones, voz de referencia, pruebas;
  `manifest.json` guarda los IDs de OpenArt que usa la automatización.
- `perfil/`: foto de perfil.
- `scripts/transcribir.py`: tiempos por palabra con faster-whisper.
- `scripts/subtitular.py`: quema subtítulos sincronizados (Inter, palabras clave en dorado).

La modelo es una IA y se etiqueta como tal en cada publicación.
