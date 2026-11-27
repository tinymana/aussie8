# Aussie 8: art needed for Batch 21 (radio, talk back, Barry)

Please send this as **AUSSIE8_BATCH21_RADIO.zip**. You can use the same folder layout as Batch 19 and 20.

Everything below already works in the game with placeholder art. When the zip arrives, I'll add each file to the art pipeline and it will replace its placeholder. The list is in priority order.

## General rules (same as earlier batches)

- PNG files with transparent backgrounds, unless a section says otherwise.
- Portraits are **96 × 96**, head and shoulders, facing the camera or turned slightly. Match the painted style of the current Duke, Yowie, June and Rosa portraits.
- Name files `<character>_<mood>.png`, all lower case, for example `sal_angry.png`.
- No real people, real brands or look-alikes of existing characters.
- In the radio box, a 96px portrait is shown at 64px. It needs to read clearly at that size: strong expression, simple background.

---

## 1. Rival mood portraits (top priority)

At the moment only Duke and the Yowie change face on the radio. Everyone else shows the same neutral face whether they're gloating, crashing or getting sledged.

Folder: `portraits/`

| Character | Moods needed | When the game shows each one |
|---|---|---|
| Sal Vitale | angry, smug, happy, sad, surprised | angry: you sledge him or ram him. smug: he passes you. happy: you finish behind him. sad: you beat him. surprised: he wrecks. |
| Shazza Kelly | angry, smug, happy, sad, surprised | same as above |
| Tash Kowalski | angry, smug, happy, sad, surprised | same as above (Tash's "angry" can be a cold glare) |
| Thommo Price | angry, smug, happy, sad, surprised | same as above (Thommo's "happy" can be hyped for the camera) |
| Big Earl | angry, smug, happy, sad, surprised | same as above |

That's 25 portraits. If you need to cut, do **angry**, **smug** and **surprised** first. Those three come up the most.

## 2. Crew mood portraits

Folder: `portraits/`

| Character | Moods needed | When the game shows each one |
|---|---|---|
| Rosa | happy, smug | happy: you grab a spanner repair. smug: optional. The happy and smug slots currently reuse her neutral face. |
| June | happy | when you win or reach the podium, and for friendly calls |
| Gazza (bookie) | happy, angry | happy: you move into the top three. angry: you drop out ("You're killing me, son!") |
| Dex | surprised | optional, for future radio calls about the odds |

## 3. Player radio head: "#8" (YOU)

When you talk back, the game shows **you** in the radio box. Right now that's a placeholder pixel helmet: yellow with a green stripe, a dark visor and an "8".

Folder: `radio/`

| File | Size | Notes |
|---|---|---|
| `you.png` | 32 × 32 (same as the other radio heads) | Helmet on, visor up or down. Gold and green with the number 8. No face needed, so it works for every player. |
| `you_cocky.png` (optional) | 32 × 32 | Visor flipped up with a grin or a wink, for sledges |

## 4. Talk-back button (phones)

On phones, a **TALK** button pops up above SHUNT for about three seconds after a rival speaks. At the moment it's a plain green rounded box.

Folder: `hud/`

| File | Size | Notes |
|---|---|---|
| `btn_talk.png` | 46 × 22 (shown at 2×, so about 92 × 44) | A walkie-talkie or speech-bubble icon with the word TALK. Match the style of `btn_shunt`. |
| `btn_talk_pressed.png` | 46 × 22 | The pressed version, a few pixels lower and darker, like `btn_shunt_pressed` |

## 5. Barry Doolan lower-third (Channel 8 commentary)

Barry's lines now appear as a TV lower-third at the bottom of the screen: a yellow name tab, a dark navy bar, his portrait on the left and a red LIVE tag. It's all drawn in code for now, so it works without art.

Folder: `hud/`

| File | Size | Notes |
|---|---|---|
| `barry_lower_third.png` | 310 × 31 (shown at 2×, so 620 × 62) | The frame only, with no text. Leave a **31 × 31 square on the left** for his portrait and an empty text area of about **270 × 22** on the right. Channel 8 style: navy, gold and green, with the "8" logo. |
| `barry_excited.png` (optional) | 96 × 96, in `portraits/` | Barry mid-shout, mic up. Used for crashes, lead changes and sledges. |

## 6. Nice to have

- **Radio static frames**, `fx/radio_static_01–04.png`, 32 × 32. A quick static burst over the portrait as each call connects. The game currently draws white scan lines.
- **Rivalry badge**, `ui/grudge.png`, 16 × 16. A small angry-face or crossed-wrenches icon. It could show beside a rival on the grid screen when they hold a grudge from the last race.

---

## Already on your list from earlier

- Extra moods for Hank (beyond neutral, sad and angry)
- Crowd "surprised" animation frames for the stadium strip

## Checklist

- [ ] Sal × 5 moods
- [ ] Shazza × 5 moods
- [ ] Tash × 5 moods
- [ ] Thommo × 5 moods
- [ ] Earl × 5 moods
- [ ] Rosa happy, smug · June happy · Gazza happy, angry · Dex surprised
- [ ] `radio/you.png` (and optionally `you_cocky.png`)
- [ ] `hud/btn_talk.png` + `btn_talk_pressed.png`
- [ ] `hud/barry_lower_third.png` (and optionally `portraits/barry_excited.png`)
- [ ] Optional: radio static frames, grudge badge
