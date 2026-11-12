// Estadísticas del panel (scripts/estadisticas.py → datos/estadisticas.json): vistas y seguidores por día, YouTube a
// fondo, mejores días, horas y temas, comparativas, dinero y créditos. Solo con sesión.
import {autorizado, leer, negar} from './_comun.js';

export default function handler(req, res) {
  if (!autorizado(req)) return negar(res);
  res.setHeader('Cache-Control', 'private, no-store');
  try {
    res.status(200).json(leer('estadisticas.json'));
  } catch {
    res.status(200).json({});
  }
}
