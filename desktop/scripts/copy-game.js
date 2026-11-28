// Copies the web game (../play and the few site files it reads) into ./game for packaging.
// The web build stays the single source of truth: fix the game in play/, rebuild the desktop app.
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..', '..'), OUT = path.resolve(__dirname, '..', 'game');
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });
fs.cpSync(path.join(ROOT, 'play'), path.join(OUT, 'play'), { recursive: true });
for (const f of ['devnotes.json', 'favicon.png', 'manifest.webmanifest', 'assets/icon-192.png'])
  if (fs.existsSync(path.join(ROOT, f))) { fs.mkdirSync(path.dirname(path.join(OUT, f)), { recursive: true }); fs.copyFileSync(path.join(ROOT, f), path.join(OUT, f)); }
let n = 0; (function count(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) e.isDirectory() ? count(path.join(d, e.name)) : n++ })(OUT);
console.log(`game copied: ${n} files -> ${path.relative(process.cwd(), OUT)}`);
