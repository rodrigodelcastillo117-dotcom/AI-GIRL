// Todo lo demás del sistema (scripts/sistema.py → datos/sistema.json): Victoria Hoy, comunidad, Instagram a fondo,
// Facebook, página web y automatizaciones. Solo con sesión.
import {autorizado, leer, negar} from './_comun.js';

export default function handler(req, res) {
  if (!autorizado(req)) return negar(res);
  res.setHeader('Cache-Control', 'private, no-store');
  try {
    res.status(200).json(leer('sistema.json'));
  } catch {
    res.status(200).json({});
  }
}
