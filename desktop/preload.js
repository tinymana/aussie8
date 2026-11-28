// Runs before the game's own scripts. Restores the save file into localStorage (the game reads it at boot)
// and gives the game a small, explicit bridge to the desktop app.
const { contextBridge, ipcRenderer } = require('electron');

try {
  const saved = ipcRenderer.sendSync('save:load');   // { key: value } from saves.json
  if (saved && typeof saved === 'object') {
    for (const k of Object.keys(saved)) if (/^aussie8/.test(k) && typeof saved[k] === 'string') localStorage.setItem(k, saved[k]);
  }
} catch (e) { console.warn('save restore failed', e); }

contextBridge.exposeInMainWorld('A8Desktop', {
  platform: process.platform,
  store: (k, v) => ipcRenderer.send('save:set', String(k), v == null ? null : String(v)),
  achievement: id => ipcRenderer.send('steam:achievement', String(id)),
  syncAchievements: ids => ipcRenderer.send('steam:sync', Array.isArray(ids) ? ids.map(String) : []),
  presence: text => ipcRenderer.send('steam:presence', text == null ? null : String(text)),
  steam: () => ipcRenderer.sendSync('steam:info'),
  setFullscreen: on => ipcRenderer.send('win:fullscreen', !!on),
  isFullscreen: () => ipcRenderer.sendSync('win:isFullscreen'),
  quit: () => ipcRenderer.send('app:quit')
});
