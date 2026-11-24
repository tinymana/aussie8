# Aussie 8

Outback trophy-truck racing in the browser, with RPG upgrades and a crew who remember every choice you make.

Eight trucks, eight red-dirt arenas from the Red Centre to the Daintree. Half are flat-out loops; the other half are figure-8s with a crossover where the field meets and side-on hits send trucks spinning. Between races you upgrade the truck, level up your driver and make good or shady choices that change how your crew and your rival feel about you. Push someone too far and they walk.

## Play

Open `index.html` in a browser. It has no build step and no dependencies apart from two Google Fonts.

To play it online, turn on GitHub Pages for this repo (Settings → Pages → deploy from the `main` branch, root folder). `index.html` loads `title.jpg` by relative path, so keep them together.

| Key | Action |
|---|---|
| Arrow keys / WASD | Drive |
| Space / Shift | Nitro |
| P / Esc | Pause |
| Enter | Start, from the title screen |

On touch devices, buttons appear under the screen during races. Progress saves to the browser's `localStorage` under the key `aussie8-v2`.

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

Everything lives in `index.html`: plain JavaScript inside one block, drawn on a canvas.

- **Pixel renderer:** the race is drawn on a 480×320 buffer, then scaled up 2× with nearest-neighbour filtering. Each track is painted once at load, reduced to a fixed palette of about 55 colours with 4×4 Bayer dithering, and then the crisp details are added on top: tyre walls, light towers and flags.
- **Truck sprites:** each truck is a 24×14 pixel-art image. It's rotated with nearest-neighbour sampling into 32 headings, and a 1px outline and a shadow are added to each.
- **Tracks:** each track is a list of control points joined into a closed Catmull-Rom spline. Each truck tracks its progress by finding the nearest point on the spline, searching only near where it was last frame. That keeps every truck on its own side of a figure-8 crossover. The start line is chosen automatically on the straightest stretch, well away from any crossing.
- **Physics:** a simple arcade model. Speed is split into forward and sideways parts, and the sideways part is damped by grip, which is what makes the trucks slide. Cars push each other apart, and a hard enough hit at a sharp angle triggers a crash.
- **Story:** `EVENTS` is plain data. Each choice has a tag (good, shady, neutral or gamble), its effects (money, karma, crew trust, rivalry, flags, XP, upgrades) and the text you see afterwards. Some events only appear when earlier choices have set flags, which is how payoffs and comebacks work.

### Tools

`tools/figure8_tracks.py` generates the figure-8 layouts and checks them: exactly one crossing, enough space between the walls everywhere else, everything inside the arena, and no corner too tight to drive. It needs Pillow (`pip install pillow`). Running it writes `tracks.json` and a `tracks_preview.png` contact sheet.

## Credits

Title art supplied by the project owner. Game code written with Claude.
