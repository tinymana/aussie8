// Aussie 8 desktop shell (Electron). Loads the web game from ./game over a private app:// origin,
// keeps saves in a file Steam Cloud can sync, and talks to Steam through steam.js.
const { app, BrowserWindow, protocol, net, ipcMain, shell, Menu } = require('electron');
const path = require('path'), fs = require('fs'), { pathToFileURL } = require('url');
const steam = require('./steam');

steam.init();   // before app ready: the Steam overlay needs its GPU switches set early

protocol.registerSchemesAsPrivileged([{ scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true } }]);
const GAME = path.join(__dirname, 'game');

/* ---------- saves: userData/saves.json, the file to point Steam Auto-Cloud at ---------- */
const SAVE_FILE = () => path.join(app.getPath('userData'), 'saves.json');
let saves = {}, saveTimer = null;
function readSaves() {
  try { const j = JSON.parse(fs.readFileSync(SAVE_FILE(), 'utf8')); saves = j && j.data && typeof j.data === 'object' ? j.data : {}; }
  catch (e) { saves = {}; }
  return saves;
}
function writeSaves() {
  clearTimeout(saveTimer); saveTimer = null;
  const file = SAVE_FILE(), tmp = file + '.tmp';
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(tmp, JSON.stringify({ game: 'Aussie 8', version: 1, saved: new Date().toISOString(), data: saves }));
    fs.renameSync(tmp, file);   // atomic: a crash mid-write never leaves a half file
  } catch (e) { console.error('save write failed', e); }
}
ipcMain.on('save:load', e => { e.returnValue = readSaves(); });
ipcMain.on('save:set', (e, k, v) => {
  if (!/^aussie8/.test(k)) return;
  if (v == null) delete saves[k]; else saves[k] = v;
  if (!saveTimer) saveTimer = setTimeout(writeSaves, 400);
});

/* ---------- window prefs ---------- */
const PREFS = () => path.join(app.getPath('userData'), 'window.json');
let prefs = { fullscreen: true };
try { Object.assign(prefs, JSON.parse(fs.readFileSync(PREFS(), 'utf8'))); } catch (e) {}
const keepPrefs = () => { try { fs.writeFileSync(PREFS(), JSON.stringify(prefs)); } catch (e) {} };

let win = null;
function createWindow() {
  win = new BrowserWindow({
    width: 1280, height: 800, minWidth: 960, minHeight: 640, show: false, backgroundColor: '#140b22',
    title: 'Aussie 8', icon: path.join(__dirname, 'build', 'icon.png'), autoHideMenuBar: true,
    fullscreen: !!prefs.fullscreen || process.env.SteamDeck === '1',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: false, backgroundThrottling: false, spellcheck: false }
  });
  Menu.setApplicationMenu(null);
  win.once('ready-to-show', () => win.show());
  // links out (dev notes, GitHub) open in the player's browser; the game itself never navigates away
  win.webContents.setWindowOpenHandler(({ url }) => { if (/^https?:/.test(url)) shell.openExternal(url); return { action: 'deny' }; });
  win.webContents.on('will-navigate', (e, url) => { if (!url.startsWith('app://')) { e.preventDefault(); if (/^https?:/.test(url)) shell.openExternal(url); } });
  // F11 or Alt+Enter toggles fullscreen
  win.webContents.on('before-input-event', (e, i) => {
    if (i.type === 'keyDown' && (i.key === 'F11' || (i.key === 'Enter' && i.alt))) { e.preventDefault(); setFullscreen(!win.isFullScreen()); }
  });
  win.on('close', writeSaves);
  win.loadURL('app://aussie8/play/index.html');
}
function setFullscreen(on) { if (!win) return; win.setFullScreen(!!on); prefs.fullscreen = !!on; keepPrefs(); }

ipcMain.on('win:fullscreen', (e, on) => setFullscreen(on));
ipcMain.on('win:isFullscreen', e => { e.returnValue = !!(win && win.isFullScreen()); });
ipcMain.on('app:quit', () => { writeSaves(); app.quit(); });
ipcMain.on('steam:achievement', (e, id) => steam.achievement(id));
ipcMain.on('steam:sync', (e, ids) => steam.syncAchievements(ids));
ipcMain.on('steam:presence', (e, t) => steam.presence(t));
ipcMain.on('steam:info', e => { e.returnValue = { ok: steam.ok(), status: steam.status(), name: steam.playerName() }; });

app.whenReady().then(() => {
  protocol.handle('app', req => {
    const u = new URL(req.url), rel = decodeURIComponent(u.pathname).replace(/^\/+/, '');
    const file = path.normalize(path.join(GAME, rel));
    if (!file.startsWith(GAME + path.sep)) return new Response('Not found', { status: 404 });
    return net.fetch(pathToFileURL(file).toString());
  });
  createWindow();
});
app.on('window-all-closed', () => { writeSaves(); app.quit(); });
app.on('before-quit', writeSaves);
