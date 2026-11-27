# Aussie 8

Outback trophy-truck racing in the browser, with RPG upgrades and a crew who remember every choice you make.

Eight trucks, eight red-dirt arenas from the Red Centre to the Daintree. Half are flat-out loops; the other half are figure-8s with a crossover where the field meets and side-on hits send trucks spinning. Between races you upgrade the truck, level up your driver and make good or shady choices that change how your crew and your rival feel about you. Push someone too far and they walk.

## Site layout

```
index.html            Landing page: hero, features, phone controls, dev notes
style.css, main.js    Landing page styles and script (main.js renders the dev notes)
devnotes.json         Changelog. The landing page AND the in-game "What's new" both read it
manifest.webmanifest  "Add to Home Screen": opens /play/ fullscreen in landscape
_headers              Cache rules for Netlify / Cloudflare Pages
favicon.png, assets/  Icons, title art and screenshots
play/index.html       The game (single file, no build step)
play/title.jpg        Title screen art
tools/                Track generator
```

## Hosting

The site is fully static, with no build step.

- **Netlify:** import the repo, leave the build command empty and set the publish directory to `/`. Every push to `main` deploys, and pull requests get preview links. Netlify picks up `_headers` automatically.
- **GitHub Pages:** Settings → Pages → deploy from `main`, root folder.

`devnotes.json` is loaded with `fetch`, so open the site through a web server, not by double-clicking `index.html`. For a quick local server, run `python3 -m http.server` and visit `http://localhost:8000/`.

## Posting dev notes

Add an entry to the **top** of `notes` in `devnotes.json` whenever you push an update:

```json
{
  "version": "0.6",
  "date": "2026-12-01",
  "title": "Short headline",
  "items": [
    { "tag": "new", "text": "Something added." },
    { "tag": "improved", "text": "Something better." },
    { "tag": "fixed", "text": "Something that was broken." }
  ]
}
```

The landing page shows every entry, newest first, and marks the top one Latest. The game's menu shows the top entry as "What's new".

## Controls

| Keyboard | Action |
|---|---|
| Arrow keys / WASD | Drive |
| Space / Shift | Nitro |
| P / Esc | Pause |
| Enter | Start, from the title screen |

**Phones:** races go fullscreen, with the controls beside the track.

- **Drag to steer** (the default): put your thumb down anywhere on the left and point where you want to go. Gas is automatic, NITRO is under your right thumb, and BRAKE is beside it.
- **Buttons:** big ◀ ▶, with GAS and NITRO side by side so you can roll your thumb across.
- **Left-handed:** swaps the steering and pedal sides.

You can change these on the game's menu and in the garage. Progress saves to the browser's `localStorage` (`aussie8-v2`; control settings are saved under `aussie8-ctl`).

## What's in the game

- **Racing:** 4 laps, 8 trucks, mud, water, jump ridges, nitro and cash pickups, and kangaroos that hop across the track. Computer drivers get faster through the season and adjust their pace to stay close to you.
- **Crashes:** side-on hits above a speed threshold spin both trucks out for about a second. These mostly happen at figure-8 crossovers.
- **RPG:** you earn XP and level up, then spend points on four driver stats: Handling, Grit, Nerve and Charm. Prize money buys engine, tyre, shock and nitro upgrades.
- **Choices:** a story event comes between each race, with good, shady and gamble options. A karma meter tracks your reputation, and a separate rivalry meter tracks Duke Vance, who rams you if he hates you.
- **Crew:**
  - Rosa, the mechanic, likes honesty.
  - Dex, the hustler, likes shady deals.
  - June, the spotter, likes kindness.

  Each has a trust meter, gives a perk once trust is high enough, and quits if trust drops too low.
- **Endings:** six endings, depending on the title result, karma, who stayed in your crew and where things stand with Duke.

## How it's built

The game is `play/index.html`: plain JavaScript inside one block, drawn on a canvas.

- **Pixel renderer:** the race is drawn on a 480×320 buffer, then scaled up 2× with nearest-neighbour filtering. Each track is painted once at load, reduced to a fixed palette of about 55 colours with 4×4 Bayer dithering, and then the crisp details are added on top: tyre walls, light towers and flags.
- **Truck sprites:** each truck is a 24×14 pixel-art image. It's rotated with nearest-neighbour sampling into 32 headings, and a 1px outline and a shadow are added to each.
- **Tracks:** each track is a list of control points joined into a closed Catmull-Rom spline. Each truck tracks its progress by finding the nearest point on the spline, searching only near where it was last frame. That keeps every truck on its own side of a figure-8 crossover. The start line is chosen automatically on the straightest stretch, well away from any crossing.
- **Physics:** a simple arcade model. Speed is split into forward and sideways parts, and the sideways part is damped by grip, which is what makes the trucks slide. Cars push each other apart, and a hard enough hit at a sharp angle triggers a crash.
- **Story:** `EVENTS` is plain data. Each choice has a tag (good, shady, neutral or gamble), its effects (money, karma, crew trust, rivalry, flags, XP, upgrades) and the text you see afterwards. Some events only appear when earlier choices have set flags, which is how payoffs and comebacks work.

### Art

Runtime art lives in `play/art/` and is listed in `play/art/manifest.js`. Both are generated, so don't edit them by hand. To rebuild them from the master art library (kept outside the repo, about 60 MB):

```
python3 tools/curate_art.py /path/to/AUSSIE8_MASTER_ART_LIBRARY /path/to/AUSSIE8_BATCH15_STADIUM_CROWD /path/to/AUSSIE8_BATCH17_RACE_ANNOUNCEMENTS
```

The stadium strip above each track is built from Batch 15 (crowd, bleachers, camera, banner) and the owner's Uluru painting in `tools/art_src/outback_stadium_sunset.png`, which is the backdrop on every course. The crowd is drawn live each frame and only reacts to the race; it never changes race rules. Reaction triggers, reach and cooldowns are in `CRE` in `play/index.html`.

The script copies only reviewed assets under the game's own names, builds sprite strips and atlases, and writes `docs/ART_INTEGRATION_REPORT.md`, listing what was mapped, what was held back and why, and what art is still missing. If any art fails to load, the game falls back to its built-in pixel art.

### Tools

`tools/curate_art.py` builds the runtime art (above). `tools/figure8_tracks.py` generates the figure-8 layouts and checks them: exactly one crossing, enough space between the walls everywhere else, everything inside the arena, and no corner too tight to drive. It needs Pillow (`pip install pillow`). Running it writes `tracks.json` and a `tracks_preview.png` contact sheet.

## Credits

Title art supplied by the project owner. Game code written with Claude.

### Online

Online features run on the owner's **tiny-mana-jams** Supabase project, in their own `aussie8` schema (nothing is shared with Typlympics or the other games there).

- `supabase/functions/aussie8/index.ts`: the edge function, deployed as-is. Actions: `enter` (name + PIN, like Typlympics), `me`, `submit_lap` (Time Trial best lap + ghost, checked against the fastest a truck can go), `submit_race`, `board`, `ghost`, `signout`.
- `supabase/migrations/`: the schema. The API roles have no access to it; only the function does.
- Live races use Supabase Realtime broadcast on channel `aussie8:<ROOM>` with the publishable key; each player broadcasts their own truck 15 times a second, the host also broadcasts the AI rivals. `play/vendor/supabase-2.119.2.js` is the supabase-js browser build (MIT).

