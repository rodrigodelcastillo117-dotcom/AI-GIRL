// Video "calcúlalo conmigo" (9-nov-2026, 0 créditos): graba la calculadora de aguinaldo siguiendo los tiempos de la voz clonada.
// Uso: node scripts/grabar_calculadora.js d0 d1 d2 d3 d4 carpeta  (d = duración de cada frase de videos/calcula/voz-0N.mp3)
// Después: ffmpeg recorta el arranque, encima la cara (carrusel.cara) y subtitulos (videos/calcula/subs.ass). Ver aprendizajes 9-nov.
const { chromium } = require('playwright');
const [d0, d1, d2, d3, d4] = process.argv.slice(2, 7).map(Number);
const dir = process.argv[7];
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 720, height: 1280 }, locale: 'es-MX', timezoneId: 'America/Mexico_City', recordVideo: { dir, size: { width: 720, height: 1280 } } });
  const p = await ctx.newPage();
  await p.goto('https://victoriatheceo.vercel.app/aguinaldo', { waitUntil: 'networkidle' });
  await p.addStyleTag({ content: 'html{scroll-behavior:smooth} #sueldo{outline:4px solid #F5C542}' });
  await p.fill('#sueldo', ''); await p.dispatchEvent('#sueldo', 'input');
  const t0 = Date.now();
  const hasta = async (s) => { const falta = s * 1000 - (Date.now() - t0); if (falta > 0) await p.waitForTimeout(falta); };
  await hasta(0.6 + d0 * 0.6);
  await p.evaluate(() => document.getElementById('sueldo').scrollIntoView({ block: 'center' }));
  await hasta(0.6 + d0);
  await p.click('#sueldo');
  await p.waitForTimeout(d1 * 450);
  await p.type('#sueldo', '15000', { delay: 140 });
  await hasta(0.6 + d0 + d1 + 0.3);
  await p.evaluate(() => document.getElementById('total').scrollIntoView({ block: 'center' }));
  await p.evaluate(() => { const t = document.getElementById('total'); t.style.transition = 'transform .4s'; t.style.transform = 'scale(1.15)'; });
  await hasta(0.6 + d0 + d1 + d2 + 0.6);
  await p.evaluate(() => { const e = document.getElementById('exento').closest('li'); e.scrollIntoView({ block: 'center' }); e.style.outline = '4px solid #F5C542'; e.style.outlineOffset = '6px'; });
  await hasta(0.6 + d0 + d1 + d2 + d3 + 0.9);
  await p.evaluate(() => window.scrollTo(0, 0));
  await hasta(0.6 + d0 + d1 + d2 + d3 + d4 + 1.5);
  const v = p.video(); await ctx.close(); console.log(await v.path(), (Date.now() - t0) / 1000);
  await b.close();
})();
