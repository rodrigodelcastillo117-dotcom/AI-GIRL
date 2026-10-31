// Agenda en vivo de cada red (Publer y YouTube): qué sale, a qué hora y qué ya salió. Ver agenda() en vivo.js.
import {autorizado, leer, negar} from './_comun.js';
import {agenda} from './vivo.js';

const leerSiHay = (nombre) => { try { return leer(nombre); } catch { return []; } };

export default async function handler(req, res) {
  if (!autorizado(req)) return negar(res);
  res.setHeader('Cache-Control', 'private, no-store');
  try {
    const lista = await agenda(leer('estado.json')[0], [...leer('videos.json'), ...leerSiHay('carruseles.json')]);
    res.status(200).json({actualizado: new Date().toISOString(), agenda: lista});
  } catch (err) {
    res.status(200).json({actualizado: null, agenda: null, error: err.message});
  }
}
