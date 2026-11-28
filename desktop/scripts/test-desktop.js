// Usage: npm i -D playwright-core; xvfb-run node scripts/test-desktop.js <electron or packaged exe> [app dir]
// Drives the desktop app headless (under xvfb): boot, a full race, trophies -> achievements bridge, save file round trip, quit.
const { _electron } = require('playwright-core');
const fs = require('fs'), path = require('path'), os = require('os');
const EXE = process.argv[2], APPDIR = process.argv[3] || null, UD = fs.mkdtempSync(path.join(os.tmpdir(), 'a8ud-'));
const log = (...a) => console.log(...a);
async function launch() {
  const args = (APPDIR ? [APPDIR] : []).concat(['--user-data-dir=' + UD, '--no-sandbox']);
  const app = await _electron.launch({ executablePath: EXE, args, env: { ...process.env, AUSSIE8_NO_STEAM: process.env.WITH_STEAM ? '' : '1' }, timeout: 60000 });
  const pg = await app.firstWindow(); const errs = []; pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()) });
  await pg.waitForTimeout(2500); return { app, pg, errs };
}
(async () => {
  let { app, pg, errs } = await launch();
  log('url', pg.url(), '| title', await pg.title());
  log('desktop bridge', await pg.evaluate(() => !!window.A8Desktop && { plat: A8Desktop.platform, steam: A8Desktop.steam(), fs: A8Desktop.isFullscreen() }));
  log('art loaded', await pg.evaluate(() => Object.keys(window.__A8.ART.img).length), '| footer', await pg.evaluate(() => document.querySelector('.foot span:last-child').textContent));
  await pg.screenshot({ path: '/tmp/desk_title.png' });
  await pg.keyboard.press('Enter'); await pg.waitForTimeout(300);
  log('menu has Quit', !!(await pg.$('[data-act=quit]')));
  await pg.click('[data-act=new]'); await pg.click('[data-act="ch:0"]');
  if (await pg.$('[data-act=paddock]')) await pg.click('[data-act=paddock]');
  await pg.click('[data-act=garage]'); await pg.click('[data-act=race]'); await pg.waitForTimeout(400);
  await pg.evaluate(() => window.__A8.gridChoice('ignore')); await pg.waitForTimeout(3700);
  await pg.screenshot({ path: '/tmp/desk_race.png' });
  const steps = await pg.evaluate(() => { const A = window.__A8; A.R.pl.auto = true; const ov = document.getElementById('ov'); let i = 0; while (A.R && ov.hidden && i < 60 * 260) { A.updRace(1 / 60); i++ } return i });
  await pg.waitForTimeout(300);
  log('race steps', steps, '| results:', (await pg.evaluate(() => document.getElementById('ov').innerText.slice(0, 70))).replace(/\n/g, ' '));
  const trophies = await pg.evaluate(() => JSON.parse(localStorage.getItem('aussie8-trophies') || '[]'));
  const race = await pg.evaluate(() => window.__A8.G.race);
  await pg.waitForTimeout(800);
  const file = path.join(UD, 'saves.json'); const sj = JSON.parse(fs.readFileSync(file, 'utf8'));
  log('save file keys', Object.keys(sj.data), '| race in file', JSON.parse(sj.data['aussie8-v2']).race, '(game', race + ')', '| trophies', trophies);
  // settings: fullscreen toggle exists
  await pg.click('[data-act=after]').catch(() => {}); await pg.waitForTimeout(200);
  await pg.evaluate(() => showSettings()); await pg.waitForTimeout(200);
  log('settings has Display card', !!(await pg.$('[data-act=fullscreen]')));
  log('errors run 1', errs);
  // quit from the menu, then relaunch and check the save came back from the file
  await pg.evaluate(() => { localStorage.clear(); });   // prove the restore comes from saves.json, not Chromium's own storage
  await new Promise(r => setTimeout(r, 900));
  const sj2 = JSON.parse(fs.readFileSync(file, 'utf8'));
  log('file survives localStorage.clear():', !!sj2.data['aussie8-v2']);
  await app.close();
  ({ app, pg, errs } = await launch());
  const back = await pg.evaluate(() => { const s = JSON.parse(localStorage.getItem('aussie8-v2') || 'null'); return s && { race: s.race, money: s.money } });
  log('after relaunch, save restored from file:', back);
  await pg.keyboard.press('Enter'); await pg.waitForTimeout(300);
  log('continue button:', await pg.evaluate(() => (document.querySelector('[data-act=cont]') || {}).innerText || 'none'));
  await pg.click('[data-act=quit]'); await new Promise(r => setTimeout(r, 1500));
  log('quit closed the app:', app.windows().length === 0 || (await app.evaluate(({ BrowserWindow }) => BrowserWindow.getAllWindows().length).catch(() => 0)) === 0);
  log('errors run 2', errs);
  await app.close().catch(() => {});
})().catch(e => { console.error('FAILED', e); process.exit(1) });
