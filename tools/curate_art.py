#!/usr/bin/env python3
"""Curate the AUSSIE8 master art library into the game's runtime folder.

Only approved, reviewed assets are copied, under the game's own identifiers.
Reference sheets, previews, source atlases and rejected art stay out of the build.

    python3 tools/curate_art.py /path/to/AUSSIE8_MASTER_ART_LIBRARY [BATCH15_STADIUM_CROWD] [BATCH17_RACE_ANNOUNCEMENTS]

Writes:
    play/art/...                  runtime images (PNG for sprites, lossless WebP for scenes)
    play/art/manifest.js          window.A8_ART: every runtime asset the game may load
    docs/ART_INTEGRATION_REPORT.md mapped / held back / missing, with reasons
"""
import json, sys, hashlib
from pathlib import Path
from PIL import Image
import numpy as np

LIB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/claude/artlib/master')
B15 = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('/home/claude/artlib/batch15')  # AUSSIE8_BATCH15_STADIUM_CROWD
B17 = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('/home/claude/artlib/batch17')  # AUSSIE8_BATCH17_RACE_ANNOUNCEMENTS
P = LIB / 'packs'
REPO = Path(__file__).resolve().parent.parent
OUT = REPO / 'play' / 'art'
OUTLINE = (20, 10, 8, 255)

mapped, held, missing = [], [], []


def src(rel):
    p = P / rel
    if not p.exists():
        raise SystemExit(f'missing source file: {rel}')
    return p


def rgba(rel):
    return Image.open(src(rel)).convert('RGBA')


def save(im, rel, lossless_webp=False):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if lossless_webp:
        im.convert('RGB').save(path, 'WEBP', lossless=True, method=6)
    else:
        im.save(path, optimize=True)
    return rel


def strip(frames):
    w, h = frames[0].size
    s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        assert f.size == (w, h), f.size
        s.alpha_composite(f, (i * w, 0))
    return s


def add_outline(im):
    a = np.array(im)
    m = a[..., 3] > 0
    edge = np.zeros_like(m)
    edge[1:, :] |= m[:-1, :]; edge[:-1, :] |= m[1:, :]; edge[:, 1:] |= m[:, :-1]; edge[:, :-1] |= m[:, 1:]
    edge &= ~m
    a[edge] = OUTLINE
    return Image.fromarray(a)


def clean_frame_edges(im, border=6):
    """Expression crops were cut from a framed sheet and carry pale frame lines up to 6 px in from
    each edge. Crop a clean border off (96 -> 84 px); the game scales portraits with nearest-neighbour."""
    w, h = im.size
    return im.crop((border, border, w - border, h - border))


def ok(game_id, rel_out, source, note=''):
    mapped.append((game_id, rel_out, source, note))


# ---------------------------------------------------------------- trucks + damage (Batch03)
TRUCK_ROWS = ['you', 'duke', 'sal', 'shazza', 'tash', 'thommo', 'yowie', 'earl']
FILE_ID = {'you': 'player'}
sheet = Image.new('RGBA', (24 * 4, 14 * len(TRUCK_ROWS)), (0, 0, 0, 0))
for r, tid in enumerate(TRUCK_ROWS):
    fid = FILE_ID.get(tid, tid)
    for s in range(4):
        name = f'truck_{fid}.png' if s == 0 else f'truck_{fid}_damage_{s}.png'
        im = rgba(f'BATCH03_TRUCK_DAMAGE/track/{name}')
        assert im.size == (24, 14)
        sheet.alpha_composite(im, (s * 24, r * 14))
    ok(f'truck:{tid} (clean + damage 1-3)', 'art/trucks.png', f'BATCH03_TRUCK_DAMAGE/track/truck_{fid}*.png')
save(sheet, 'trucks.png')

# ---------------------------------------------------------------- wreck debris (Batch08A)
DEBRIS = ['tyre', 'wheel', 'bumper', 'body_panel', 'hood_fragment', 'glass', 'metal_shard', 'exhaust', 'spring', 'headlight', 'plastic', 'oil']
deb = Image.new('RGBA', (16 * 3, 16 * len(DEBRIS)), (0, 0, 0, 0))
for r, t in enumerate(DEBRIS):
    for v in range(3):
        deb.alpha_composite(rgba(f'BATCH08A_WRECK_DEBRIS/{t}_{v + 1:02d}.png'), (v * 16, r * 16))
save(deb, 'debris.png')
ok('debris: 12 parts x 3 variants', 'art/debris.png', 'BATCH08A_WRECK_DEBRIS/*.png')

# ---------------------------------------------------------------- racing + surface effects (Batch04, Batch05)
FX = {
    'crash': ('BATCH04_RACING_EFFECTS/crash/crash_{:02d}.png', 8),
    'smoke': ('BATCH04_RACING_EFFECTS/smoke/smoke_{:02d}.png', 8),
    'nitro': ('BATCH04_RACING_EFFECTS/nitro/nitro_{:02d}.png', 6),
    'shunt': ('BATCH04_RACING_EFFECTS/shunt/shunt_{:02d}.png', 6),
    'drift_dust': ('BATCH05_SURFACE_EFFECTS/drift_dust/drift_dust_{:02d}.png', 10),
    'mud_spray': ('BATCH05_SURFACE_EFFECTS/mud_spray/mud_spray_{:02d}.png', 8),
    'water_splash': ('BATCH05_SURFACE_EFFECTS/water_splash/water_splash_{:02d}.png', 8),
    'mud_splatter': ('BATCH05_SURFACE_EFFECTS/mud_splatter/mud_splatter_{:02d}.png', 6),
}
fx_manifest = {}
for k, (pat, n) in FX.items():
    save(strip([rgba(pat.format(i)) for i in range(n)]), f'fx/{k}.png')
    fx_manifest[k] = {'src': f'fx/{k}.png', 'w': 32, 'h': 32, 'n': n}
    ok(f'fx:{k} ({n} frames)', f'art/fx/{k}.png', pat.format(0).rsplit('_', 1)[0] + '_*.png')

# ---------------------------------------------------------------- wildlife (Batch06): side view, outlined for contrast
WILD = {
    'roo_run': ('BATCH06_WILDLIFE/kangaroo_run_{:02d}.png', range(1, 9)),
    'roo_leap': ('BATCH06_WILDLIFE/kangaroo_leap_{:02d}.png', range(1, 5)),
    'emu_run': ('BATCH06_WILDLIFE/emu_run_{:02d}.png', range(1, 9)),
    'emu_evade': ('BATCH06_WILDLIFE/emu_evade_{:02d}.png', range(1, 5)),
}
wild_manifest = {}
for k, (pat, rng) in WILD.items():
    frames = [add_outline(rgba(pat.format(i))) for i in rng]
    save(strip(frames), f'wildlife/{k}.png')
    wild_manifest[k] = {'src': f'wildlife/{k}.png', 'w': 32, 'h': 32, 'n': len(frames)}
    ok(f'wildlife:{k}', f'art/wildlife/{k}.png', pat.format(1).rsplit('_', 1)[0] + '_*.png', '1px outline added for contrast on red dirt')
held.append(('BATCH06_WILDLIFE/kangaroo_hit_*.png, emu_hit_*.png', 'Show the animal knocked flat with dizzy stars. Canon: animals always bounce away unhurt, so collisions use the leap/evade frames.'))
held.append(('BATCH06_WILDLIFE/dust_*, dirt_kickup_*, icon_*, sign_*', 'Not needed at runtime (dust comes from Batch05); some frames are clipped (dust_trail_06, emu_evade_01).'))

# ---------------------------------------------------------------- pickups + Stewards (Batch07)
pick = {}
for k in ['nitro', 'cash', 'spanner', 'pie']:
    rel = save(rgba(f'BATCH07_PICKUPS_STEWARDS/track/pickup_{k}.png'), f'pickups/{k}.png')
    pick[k] = rel
    ok(f'pickup:{k}', 'art/' + rel, f'BATCH07_PICKUPS_STEWARDS/track/pickup_{k}.png')
for c in ['red', 'blue']:
    pick['stewards_' + c] = save(rgba(f'BATCH07_PICKUPS_STEWARDS/track/stewards_ute_{c}.png'), f'pickups/stewards_ute_{c}.png')
ok('stewards_ute (lights red / blue)', 'art/pickups/stewards_ute_*.png', 'BATCH07_PICKUPS_STEWARDS/track/stewards_ute_{red,blue}.png')

# ---------------------------------------------------------------- track backdrops + props (Batch08)
TRACK_BACKDROPS = ['red_centre', 'kakadu', 'flinders', 'coober_pedy', 'nullarbor', 'kimberley', 'daintree', 'showdown']
bd = []
for k in TRACK_BACKDROPS:
    bd.append(save(rgba(f'BATCH08_TRACK_SCENERY/backdrops/{k}.png'), f'backdrops/{k}.png'))
    ok(f'backdrop:{k}', f'art/backdrops/{k}.png', f'BATCH08_TRACK_SCENERY/backdrops/{k}.png')
PROPS = ['tyre_stack', 'hay_bale', 'rock_small', 'rock_cluster', 'saltbush', 'desert_scrub', 'paperbark_canopy', 'boab_canopy', 'rainforest_canopy', 'mine_mound', 'barrel', 'traffic_cone', 'gold_ring_marker', 'mud_puddle', 'water_puddle']
props = {}
for k in PROPS:
    props[k] = save(rgba(f'BATCH08_TRACK_SCENERY/props/{k}.png'), f'props/{k}.png')
ok('props: ' + ', '.join(PROPS), 'art/props/*.png', 'BATCH08_TRACK_SCENERY/props/*.png')

# ---------------------------------------------------------------- portraits
portraits = {}
for rid in ['sal', 'shazza', 'tash', 'thommo', 'earl']:
    portraits[rid] = {'neutral': save(rgba(f'BATCH08B_RIVALS/portraits/{rid}.png'), f'portraits/{rid}_neutral.png')}
    ok(f'portrait:{rid}_neutral', f'art/portraits/{rid}_neutral.png', f'BATCH08B_RIVALS/portraits/{rid}.png', 'only one mood supplied')
# Owner's call (Nov 2026): Duke is the blond champion with sunglasses (PROFILE_ASSETS), not the rival-kit Duke in a cap.
portraits['duke'] = {'neutral': save(rgba('PROFILE_ASSETS/profiles/duke.png'), 'portraits/duke_neutral.png')}
ok('portrait:duke_neutral (blond)', 'art/portraits/duke_neutral.png', 'PROFILE_ASSETS/profiles/duke.png', 'owner picked the blond Duke; only one mood supplied')
ROSA = {'neutral': 1, 'smug': 2, 'happy': 3, 'neutral2': 4, 'serious': 5, 'surprised': 6}
portraits['rosa'] = {m: save(clean_frame_edges(rgba(f'PROFILE_ASSETS/expressions/rosa_{i:02d}.png')), f'portraits/rosa_{m}.png') for m, i in ROSA.items()}
ok('portrait:rosa (neutral, smug, happy, neutral2, serious, surprised)', 'art/portraits/rosa_*.png', 'PROFILE_ASSETS/expressions/rosa_01..06.png', '6 px framed edge cropped (84x84); no true angry/sad: "serious" is used as a labelled stand-in')
YOWIE = {'neutral': 1, 'calm': 2, 'smug': 3, 'angry': 4, 'surprised': 5, 'sad': 6}
portraits['yowie'] = {m: save(clean_frame_edges(rgba(f'PROFILE_ASSETS/expressions/yowie_{i:02d}.png')), f'portraits/yowie_{m}.png') for m, i in YOWIE.items()}
ok('portrait:yowie (neutral, calm, smug, angry, surprised, sad)', 'art/portraits/yowie_*.png', 'PROFILE_ASSETS/expressions/yowie_01..06.png', 'head-only crops, 6 px framed edge cropped (84x84): no bandolier')
portraits['hank_1994'] = {'neutral': save(rgba('PROFILE_ASSETS/profiles/hank_1994.png'), 'portraits/hank_1994_neutral.png')}
ok('portrait:hank_1994_neutral', 'art/portraits/hank_1994_neutral.png', 'PROFILE_ASSETS/profiles/hank_1994.png', 'sepia 1994 archive photo; shown in the finale reveal')
for rid in ['marge', 'rick']:
    portraits[rid] = {'neutral': save(rgba(f'PROFILE_ASSETS/profiles/{rid}.png'), f'portraits/{rid}_neutral.png')}
    ok(f'portrait:{rid}_neutral', f'art/portraits/{rid}_neutral.png', f'PROFILE_ASSETS/profiles/{rid}.png')
held.append(('PROFILE_ASSETS june / dex profiles + expressions, radio_june_calm', 'Off-model: June is canon a 22-year-old Black woman with braids in a green and gold polo (the art shows an older woman in a straw hat and glasses). Dex is canon a slick 45-year-old in a gold suit (the art shows a bearded old man with a cigar). The Batch09 event cards draw both closer to canon.'))
held.append(('PROFILE_ASSETS duke/marge/rick/hank_1994 expressions', 'Bad crops: heads cut off and name-plate fragments ("UKE", "RGE", "ICK", "NK") baked in.'))
held.append(('BATCH08B_RIVALS portraits/duke.png, BATCH13 radio_duke_calm.png, 02_DRIVER_REFERENCES duke_*', 'The brown-haired Duke in a cap. Superseded: the owner chose the blond Duke.'))
held.append(('BATCH08B_RIVALS grid/*.png, radio/*.png cards', 'Names are baked into the image and the Yowie\'s is truncated ("THE"). The game draws names itself over the clean portraits.'))

# ---------------------------------------------------------------- radio heads (Batch13)
radio = {}
for rid in ['sal', 'shazza', 'tash', 'thommo', 'earl', 'yowie']:
    radio[rid] = save(rgba(f'BATCH13_BROADCAST_HUD/ui/radio_{rid}_calm.png'), f'radio/{rid}.png')
radio['duke'] = save(rgba('PROFILE_ASSETS/profiles/duke.png').crop((14, 4, 82, 72)).resize((32, 32), Image.LANCZOS), 'radio/duke.png')
ok('radio head: duke (blond)', 'art/radio/duke.png', 'PROFILE_ASSETS/profiles/duke.png', 'face cropped from the blond portrait until a drawn radio head arrives')
ok('radio heads (calm): duke, sal, shazza, tash, thommo, earl, yowie', 'art/radio/*.png', 'BATCH13_BROADCAST_HUD/ui/radio_*_calm.png', 'calm only; angry is shown with a red frame, labelled placeholder')

# ---------------------------------------------------------------- RPG locations (Batch10 + two CORE scenes)
scenes = {}
for k in ['paddock', 'roadhouse', 'rosas_garage', 'dexs_gambling_shed', 'outback_casino', 'gold_coast_nightlife', 'bush_camp', 'channel8_race_control', 'flying_doctor_strip', 'hanks_homestead', 'scrap_yard', 'mining_town']:
    scenes[k] = save(rgba(f'BATCH10_RPG_LOCATIONS/backgrounds/{k}.png'), f'scenes/{k}.webp', True)
ok('scenes: 12 RPG locations', 'art/scenes/*.webp', 'BATCH10_RPG_LOCATIONS/backgrounds/*.png')
for k in ['pit_garage_night', 'ch8_interview']:
    scenes[k] = save(rgba(f'CORE_ASSETS/assets/scenes/{k}.png'), f'scenes/{k}.webp', True)
    ok(f'scene:{k}', f'art/scenes/{k}.webp', f'CORE_ASSETS/assets/scenes/{k}.png', 'softer than Batch10; replace when a sharper version exists')
held.append(('CORE_ASSETS/assets/scenes/roadhouse.png, paddock_dusk.png', 'Superseded by the sharper Batch10 roadhouse and paddock.'))

# ---------------------------------------------------------------- story event cards (Batch09)
EVENT_ART = {
    'stranded': 'hank_stranded', 'june_intro': 'june_spotter', 'dex_intro': 'dex_betting_line',
    'garage_night': 'unlocked_shed', 'benefit': 'flying_doctor_benefit', 'casino': 'gold_coast_casino',
    'rosa_shop': 'rosa_repossession', 'dex_debt': 'dex_debt', 'june_doubt': 'june_shaky_hands',
    'reporter': 'live_channel_8', 'hank_revenge': 'loose_wheel_nuts', 'quiet': 'open_road', 'yowie_pies': 'yowie_pies',
}
events = {}
for eid, f in EVENT_ART.items():
    events[eid] = save(rgba(f'BATCH09_STORY_EVENTS/events/{f}.png'), f'events/{f}.webp', True)
    ok(f'event:{eid}', f'art/events/{f}.webp', f'BATCH09_STORY_EVENTS/events/{f}.png')
held.append(('BATCH09_STORY_EVENTS duke_envelope.png, duke_roadhouse.png', 'Show an old man in a cowboy hat, not Duke (young, blond champion). Those events use the paddock/roadhouse backgrounds with Duke\'s portrait instead.'))
held.append(('BATCH09_STORY_EVENTS hank_racing_cam.png', 'Shows a video camera; in the story Hank\'s "racing cam" is an engine camshaft. The event uses Hank\'s homestead instead.'))

# ---------------------------------------------------------------- endings (Batch11)
endings = {}
for k in ['peoples_champion', 'champion_no_halo', 'crowned_in_red_dirt', 'hero_of_the_outback', 'just_another_driver', 'run_out_of_town']:
    endings[k] = save(rgba(f'BATCH11_SIX_ENDINGS/endings/{k}.png'), f'endings/{k}.webp', True)
ok('endings: all six', 'art/endings/*.webp', 'BATCH11_SIX_ENDINGS/endings/*.png', 'note: the art shows the player as one specific man; the bible keeps the player unstated')

# ---------------------------------------------------------------- Yowie reveal + flashback (Batch12): held back
held.append(('BATCH12_FLASHBACK_YOWIE/endings/yowie_reveal.png', 'Drawn as a real person (Ivan "Ironman" Stewart). Not used: the game does not depict or name real people. The finale reveal is built and gated, using fictional canon until the owner picks an original character and art.'))
held.append(('BATCH12_FLASHBACK_YOWIE/scenes/flashback_1994.png', 'The 1994 crash shows a white #8 truck; canon is Hank\'s \'71 ute vs Rick Vance, and #8 is the rookie number. Audit also asked for brand-marking review. Not used yet (the 1994 storyline is still planned).'))
held.append(('01_CHARACTER_MASTERS, 02_YOWIE_EXPRESSIONS, 03_YOWIE_PADDOCK full-body Yowie art', 'Reference only. The diagonal bandolier with silver boxes plus the all-brown fur body reads as Chewbacca, a protected character. Runtime uses head-only Yowie art; any full-body Yowie needs the bandolier replaced (a plain racing harness would do).'))

# ---------------------------------------------------------------- broadcast HUD (Batch13) + rival UI (Batch08B)
hud = {}
for k in ['live_bug', 'ticker', 'lower_third', 'starting_grid', 'final_lap', 'race_complete', 'position', 'lap_timer',
          'damage_bar', 'damage_bar_empty', 'penalty_bar', 'penalty_bar_empty', 'nitro_bar', 'nitro_bar_empty',
          'flag_black', 'flag_yellow', 'flag_chequered', 'radio_bubble', 'btn_shunt', 'btn_shunt_pressed']:
    hud[k] = save(rgba(f'BATCH13_BROADCAST_HUD/ui/{k}.png'), f'hud/{k}.png')
ok('broadcast HUD: ' + ', '.join(hud), 'art/hud/*.png', 'BATCH13_BROADCAST_HUD/ui/*.png')
badges = {k: save(rgba(f'BATCH08B_RIVALS/status/{k}.png'), f'ui/status_{k}.png') for k in ['mate', 'friendly', 'neutral', 'hostile', 'nemesis']}
choices = {k: save(rgba(f'BATCH08B_RIVALS/choices/{k}.png'), f'ui/choice_{k}.png') for k in ['taunt', 'encourage', 'ignore']}
ok('rival status badges + grid choice buttons', 'art/ui/*.png', 'BATCH08B_RIVALS/status/*.png, choices/*.png')
held.append(('BATCH02_ASSETS (trucks, damage, effects, props, ui, tiles)', 'Early concept sheet cut-outs with opaque backgrounds (no transparency) at odd sizes; superseded by Batch03-08 and Batch13.'))
held.append(('BATCH13 race_intro, race_results, standings rows, timing_row, driver_number, replay_bug, position', 'Available but not needed in this pass (results and standings are drawn as page UI).'))

# ---------------------------------------------------------------- stadium + crowd (Batch15)
stadium = None
if B15.exists():
    ACTS = ['idle', 'sit', 'cheer', 'wave', 'flag', 'rail', 'photo', 'boo', 'victory']
    atlas = Image.new('RGBA', (10 * 4 * len(ACTS), 12 * 6), (0, 0, 0, 0))
    for f in range(6):
        for ai, a in enumerate(ACTS):
            for k in range(4):
                im = Image.open(B15 / 'crowd' / f'fan_{f+1:02d}_{a}_{k:02d}.png').convert('RGBA')
                atlas.paste(im, ((ai * 4 + k) * 10, f * 12))
    stadium = {'crowd': {'src': save(atlas, 'stadium/crowd.png'), 'w': 10, 'h': 12, 'frames': 4, 'fans': 6, 'acts': ACTS, 'ms': 150}}
    ok('stadium crowd: 6 fans x 9 actions x 4 frames', 'art/stadium/crowd.png', 'BATCH15 crowd/fan_*_*.png', 'packed into one atlas (rows = fans, columns = action x frame)')
    # track order: Red Centre, Kakadu, Flinders, Coober Pedy, Nullarbor, Kimberley, Daintree, Outback Showdown
    # Owner's call (Nov 2026): Uluru is the backdrop on every course. Source: tools/art_src/outback_stadium_sunset.png
    # (2172x724). The band above its painted crowd (rows 110-291: lamps, clouds, the rock) is scaled to the 480x40 strip.
    uluru = Image.open(REPO / 'tools' / 'art_src' / 'outback_stadium_sunset.png').convert('RGB')
    k = uluru.width / 480
    band = uluru.crop((0, 110, uluru.width, 110 + round(40 * k))).resize((480, 40), Image.LANCZOS)
    stadium['bg'] = [save(band.convert('RGBA'), 'stadium/bg_uluru.png')]
    stadium['lamps'] = [[40, 0, 36, 6], [418, 0, 36, 6]]   # floodlight heads in the painted sky, flashed on a win
    ok('stadium sky: Uluru at sunset on all tracks (480x40)', 'art/stadium/bg_uluru.png', 'tools/art_src/outback_stadium_sunset.png (owner supplied)', 'crowd painted in the source is cropped off; the live sprite crowd stands in front')
    held.append(('BATCH15 backgrounds/*.png (8 regional skies)', 'Superseded: the owner chose the Uluru backdrop for every course.'))
    stadium['stands'] = [save(Image.open(B15 / 'stands' / f'bleacher_{i}.png').convert('RGBA'), f'stadium/bleacher_{i}.png') for i in range(1, 5)]
    stadium['props'] = {k: save(Image.open(B15 / 'props' / f'{k}.png').convert('RGBA'), f'stadium/{k}.png') for k in ['camera', 'banner_blank']}
    ok('stadium bleachers (4) + props (TV camera, banner)', 'art/stadium/*.png', 'BATCH15 stands/*.png, props/camera.png, banner_blank.png')
    held.append(('BATCH15 props floodlight, flagpole, speaker', 'The Uluru painting already has floodlights and flags; the speaker reads as a grey lollipop among the fans.'))
    held.append(('BATCH15 preview.png', 'Sample composite, not a runtime sprite (as the batch notes say).'))
    missing.append(('Crowd "surprise" reaction frames', 'Wrecks use the rail lean then a cheer as the cartoon "ooh"; a dedicated surprise action would read better.'))
else:
    held.append(('BATCH15 stadium crowd', f'Not found at {B15}; the game keeps the Batch08 backdrop strip.'))

# ---------------------------------------------------------------- race announcements (Batch17)
announce = None
if B17.exists():
    m17 = json.loads((B17 / 'manifest.json').read_text())
    announce = {'ms': m17.get('frame_ms', 180), 'dur': {k: v / 1000 for k, v in m17.get('suggested_duration_ms', {}).items()}}
    for ev in ['final_lap', 'race_finished']:
        frames = [Image.open(B17 / f'{ev}_{i:02d}.png').convert('RGBA') for i in (1, 2)]
        announce[ev] = {'src': save(strip(frames), f'announce/{ev}.png'), 'w': 256, 'h': 48, 'n': 2}
    ok('race announcements: FINAL LAP!, RACE FINISHED! (2 frames each)', 'art/announce/*.png', 'BATCH17 final_lap_0*.png, race_finished_0*.png', 'replace the Batch13 final_lap / race_complete banners (those stay as a fallback)')
    held.append(('BATCH17 preview.png', 'Sample sheet, not a runtime sprite.'))

# ---------------------------------------------------------------- environments sheet (owner, Nov 2026)
# tools/art_src/batch06_environments_sheet.png is a composite sheet, so each sprite is cut out by its box and
# connected parts, scaled to game size and given hard pixel edges. Boxes are in sheet pixels (1536x1024).
ENV = REPO / 'tools' / 'art_src' / 'batch06_environments_sheet.png'
env = None
if ENV.exists():
    from scipy import ndimage
    ea = np.array(Image.open(ENV).convert('RGBA'))
    elab, _ = ndimage.label(ea[:, :, 3] > 40, structure=np.ones((3, 3)))
    def cut(box, h, minpart=150):
        x0, y0, x1, y1 = box
        sub = elab[y0:y1, x0:x1]
        ids = [i for i in np.unique(sub) if i and (sub == i).sum() >= minpart]
        c = ea[y0:y1, x0:x1].copy(); c[~np.isin(sub, ids), 3] = 0
        c = Image.fromarray(c); c = c.crop(c.getchannel('A').getbbox())
        s = np.array(c.resize((max(1, round(c.width * h / c.height)), h), Image.LANCZOS))
        s[:, :, 3] = np.where(s[:, :, 3] > 110, 255, 0)
        return Image.fromarray(s)
    SIDE = {'barrier_red': ((19, 342, 135, 405), 11), 'barrier_concrete': ((150, 345, 248, 402), 10),
            'tyres_red': ((272, 332, 339, 406), 13), 'tyres_white': ((361, 332, 428, 406), 13), 'tyres_black': ((449, 332, 515, 406), 13),
            'hay_bale_side': ((536, 335, 630, 403), 11), 'drum_red': ((654, 325, 710, 406), 14), 'drum_rust': ((734, 326, 788, 404), 14),
            'cone_side': ((807, 329, 861, 402), 13)}
    BIG = {'tower': ((832, 851, 991, 987), 40), 'gazebo': ((1380, 860, 1517, 987), 30), 'floodlight_tall': ((1191, 842, 1257, 987), 40),
           'flag_au': ((1009, 861, 1073, 987), 32), 'camera_crane': ((1088, 865, 1173, 987), 32), 'roo_sign': ((673, 881, 785, 1001), 20)}
    env = {'trackside': {k: save(cut(b, h), f'env/{k}.png') for k, (b, h) in SIDE.items()},
           'structures': {k: save(cut(b, h, 2000 if k == 'gazebo' else 150), f'env/{k}.png') for k, (b, h) in BIG.items()}}
    ok('trackside props, side-on (barriers, tyre stacks x3, hay bale, drums x2, cone)', 'art/env/*.png', 'tools/art_src/batch06_environments_sheet.png', 'mixed in with the Batch08 top-down trackside props')
    ok('set pieces (race tower, gazebo, floodlight, flag, camera crane, roo sign)', 'art/env/*.png', 'tools/art_src/batch06_environments_sheet.png', '2-3 per track, outside the walls; decorative only')
    pick['nitro'] = save(cut((1301, 336, 1341, 400), 12), 'pickups/nitro.png')
    pick['spanner'] = save(cut((1219, 334, 1280, 396), 11), 'pickups/spanner.png')
    ok('pickup:nitro, pickup:spanner (replace Batch07)', 'art/pickups/{nitro,spanner}.png', 'environments sheet: lightning bolt, wrench')
    held.append(('Environments sheet: Castrol, Shell, Dunlop and XXXX billboards', 'Real company trademarks; not used. The roo sign is used.'))
    held.append(('Environments sheet: AUSSIE 8 billboard and sheet logo', 'Blue/red logo differs from the gold/green wordmark used on the site; not used until the owner picks one.'))
    held.append(('Environments sheet: track tiles, tyre-mark/dust/mud/gravel overlays', 'Tracks are drawn procedurally as dirt and the game already has dust/mud effects; asphalt tiles do not fit.'))
    held.append(('Environments sheet: 16x24 crowd and bleacher sections', 'Single frames; the animated Batch 15 crowd is used instead.'))
    held.append(('Environments sheet: daytime Uluru parallax', 'The owner chose the sunset Uluru for every course; could be a daytime variant.'))
    held.append(('Environments sheet: jerry can, crossed tools, first-aid kit, bollard, rope and chain fences, windsock', 'No matching pickup or slot yet; the windsock lost its sock in the cut.'))

# ---------------------------------------------------------------- missing artwork
missing += [
    ('Portraits: Gazza, Hank (present day), Lou Tran, Chief Steward Pemberton, Barry Doolan, Biscuit, the Windbreakers', 'Game falls back to coloured initials.'),
    ('Portraits: June and Dex on-model', 'Held back as off-model; initials used.'),
    ('Mood sets for the six rivals, Marge and Rick (angry, happy, sad, smug, surprised)', 'Neutral is shown; reactions that should be angry are marked with a red frame as a labelled placeholder.'),
    ('Angry radio heads for all rivals', 'Calm head plus red frame placeholder.'),
    ('Blond Duke: expressions (angry, happy, sad, smug, surprised) and a drawn 32x32 radio head', 'Neutral portrait shown; radio head is cropped from it.'),
    ('Rosa angry and sad', '"serious" used as a labelled stand-in.'),
    ('Paddock standing sprites and idle animations', 'Only reference poses supplied; paddock uses portraits.'),
    ('Duke event cards (envelope, roadhouse) and Hank racing-cam card', 'Held back as off-model; backgrounds plus portraits used.'),
    ('Finale reveal art for an original (fictional) character', 'Reveal uses the Yowie portrait and Hank\'s fictional canon until replaced.'),
]

# ---------------------------------------------------------------- manifest.js
manifest = {
    'base': 'art/',
    'trucks': {'src': 'trucks.png', 'w': 24, 'h': 14, 'stages': 4, 'rows': {t: i for i, t in enumerate(TRUCK_ROWS)}},
    'debris': {'src': 'debris.png', 'size': 16, 'variants': 3, 'types': DEBRIS},
    'fx': fx_manifest, 'wildlife': wild_manifest, 'pickups': pick,
    'backdrops': bd, 'props': props, 'portraits': portraits, 'radio': radio,
    'stadium': stadium, 'announce': announce, 'env': env, 'scenes': scenes, 'events': events, 'endings': endings, 'hud': hud, 'badges': badges, 'choices': choices,
    'placeholders': {'rosa.angry': 'serious', 'rosa.sad': 'serious', 'radio.angry': 'calm + red frame', 'portrait.mood': 'neutral + frame tint'},
}
(OUT / 'manifest.js').write_text('// Generated by tools/curate_art.py. Do not edit by hand.\nwindow.A8_ART=' + json.dumps(manifest, separators=(',', ':')) + ';\n')

# ---------------------------------------------------------------- report
lines = ['# Art integration report', '', f'Generated by `tools/curate_art.py` from the AUSSIE8 master art library. {len(mapped)} runtime mappings, {len(held)} items held back, {len(missing)} gaps.', '',
         '## Mapped into the game', '', '| Game asset | Runtime file | Source | Note |', '| --- | --- | --- | --- |']
lines += [f'| {a} | `{b}` | `{c}` | {d} |' for a, b, c, d in mapped]
lines += ['', '## Held back (not used at runtime)', '', '| Source | Why |', '| --- | --- |'] + [f'| `{a}` | {b} |' for a, b in held]
lines += ['', '## Missing artwork', '', '| Needed | What the game does meanwhile |', '| --- | --- |'] + [f'| {a} | {b} |' for a, b in missing]
lines += ['', '## Decisions for the owner', '',
  '- **Finale reveal identity (open).** The owner wants the Yowie unmasked as Ivan "Ironman" Stewart. That is not implemented: the game does not name or depict real people, and the Batch12 reveal art is held back. The reveal is built and gated on beating the Yowie in the final round; the identity lives in `REVEAL` in `play/index.html` and is the fictional Hank Booker. A credits dedication to Super Off Road is offered instead.',
  '- **Player likeness (open).** The six ending illustrations show the player as one specific man; the story bible keeps the player unstated.',
  '',
  '### Settled (Nov 2026)',
  '',
  '- **Duke** is the blond champion with sunglasses. Blond expressions and a drawn radio head are still needed.',
  '- **Yowie** full-body art: a plain racing harness replaces the bandolier before any full-body Yowie is used.',
  '- **Logo:** the gold and green wordmark.',
  '- **Debris** slows a truck that drives over it, then breaks up; untouched parts blink out after about 25 s (`DEBRIS` in `play/index.html`).',
  '- **Damage** now costs a little top speed and adds a gentle steering weave past 45% (`WOBBLE`); crashes need a harder, more side-on hit (`CRASH`). Damage stages stay at 20 / 45 / 75.']
(REPO / 'docs').mkdir(exist_ok=True)
(REPO / 'docs' / 'ART_INTEGRATION_REPORT.md').write_text('\n'.join(lines) + '\n')
size = sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())
print(f'runtime files: {sum(1 for f in OUT.rglob("*") if f.is_file())}, {size/1e6:.2f} MB; mapped {len(mapped)}, held {len(held)}, missing {len(missing)}')
