// Steamworks bridge. Everything here is optional: if Steam isn't running (or this isn't a Steam build),
// the game runs exactly the same, just without achievements, overlay or rich presence.
const fs = require('fs'), path = require('path');

// Steam app ID: AUSSIE8_STEAM_APPID env var, else steam_appid.txt beside the executable, else 480 (Valve's Spacewar test app).
function appId() {
  if (process.env.AUSSIE8_STEAM_APPID) return Number(process.env.AUSSIE8_STEAM_APPID);
  for (const dir of [path.dirname(process.execPath), process.resourcesPath && path.join(process.resourcesPath, '..'), process.cwd(), __dirname].filter(Boolean)) {
    try { const n = Number(fs.readFileSync(path.join(dir, 'steam_appid.txt'), 'utf8').trim()); if (n) return n; } catch (e) {}
  }
  return 480;
}

// In-game trophy id -> Steam achievement API name. Enter these API names in Steamworks (see docs/STEAM.md).
const ACH = id => 'A8_' + String(id).toUpperCase();

let sw = null, client = null, status = 'not started';
function init() {
  if (process.env.AUSSIE8_NO_STEAM) { status = 'disabled (AUSSIE8_NO_STEAM)'; return null; }
  try {
    sw = require('steamworks.js');
    client = sw.init(appId());
    sw.electronEnableSteamOverlay();   // must run before any window is created
    status = 'connected (app ' + appId() + ')';
  } catch (e) { client = null; status = 'not available: ' + (e && e.message || e); }
  return client;
}
const ok = () => !!client;
function achievement(id) {
  if (!client) return false;
  try { const name = ACH(id); return client.achievement.isActivated(name) || client.achievement.activate(name); } catch (e) { return false; }
}
function syncAchievements(ids) { if (!client) return 0; let n = 0; for (const id of ids || []) if (achievement(id)) n++; return n; }
function presence(text) {
  if (!client) return;
  try { client.localplayer.setRichPresence('status', text ? String(text).slice(0, 255) : null); } catch (e) {}
}
function playerName() { try { return client ? client.localplayer.getName() : null; } catch (e) { return null; } }
module.exports = { init, ok, achievement, syncAchievements, presence, playerName, status: () => status, ACH, appId };
