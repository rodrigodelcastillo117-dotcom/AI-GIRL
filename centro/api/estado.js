// La última foto que dejó la tarea automática: plan, bitácora, lecciones, mejores horas, estado y auditoría.
import {autorizado, leer, negar} from './_comun.js';

const leerSiHay = (nombre) => { try { return leer(nombre); } catch { return []; } };

export default function handler(req, res) {
  if (!autorizado(req)) return negar(res);
  res.setHeader('Cache-Control', 'private, no-store');
  const estado = leer('estado.json')[0];
  delete estado.cuentas_publer;
  res.status(200).json({
    estado,
    videos: leer('videos.json'),
    ejecuciones: leer('ejecuciones.json'),
    aprendizajes: leer('aprendizajes.json'),
    mejores_horas: leer('mejores_horas.json'),
    auditoria: leer('auditoria.json'),
    carruseles: leerSiHay('carruseles.json'),
    calendario: leerSiHay('calendario.json'),
  });
}
