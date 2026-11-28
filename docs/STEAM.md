# Aussie 8 on Steam

The Steam build is an Electron app in `desktop/`. It wraps the web game in `play/` unchanged, so every fix to the
web game ships to Steam on the next build. Steam features switch on only inside the desktop app (`window.A8Desktop`);
the website is unaffected.

## Try it on your computer

You need Node.js 20 or newer.

```
cd desktop
npm install
npm start
```

It opens fullscreen. F11 or Alt+Enter toggles windowed mode, and so does Settings → Display. "Quit to desktop" is on the main menu.

### Test the Steam features before you have an app ID

`desktop/steam_appid.txt` contains `480`, which is Valve's public test app, Spacewar. With the Steam client running and
logged in, `npm start` connects to Steam as Spacewar:

- the Steam overlay opens with Shift+Tab
- friends see your status as "Racing at Kakadu Swamp" (or wherever you are)
- achievements won't unlock, because Spacewar doesn't have Aussie 8's achievements. That's expected

To run without Steam, set `AUSSIE8_NO_STEAM=1`. The game also falls back to that on its own whenever Steam isn't running.

## Build the folders you upload to Steam

```
npm run build:win     # dist/win-unpacked/Aussie 8.exe
npm run build:mac     # dist/mac/Aussie 8.app   (Intel; see Mac notes)
npm run build:linux   # dist/linux-unpacked/aussie8   (also covers Steam Deck)
npm run build:win-portable   # dist/Aussie8-1.0.0-windows-portable.exe: one file to share for testing (not for Steam)
```

Each `dist/...` folder is one Steam depot. Upload the **contents** of the folder.

- **Windows:** build on a Windows PC to get the Aussie 8 icon on the .exe. Building Windows on Mac or Linux works but leaves the default Electron icon.
- **Mac:** this build is Intel (x64); Apple Silicon Macs run it through Rosetta. For a native universal build and code signing, build on a Mac with an Apple Developer ID and notarise it. Steam doesn't strictly require signing, but unsigned apps can trip macOS security prompts.
- **Size:** about 280–330 MB unpacked per platform, mostly Electron itself. Steam compresses downloads to roughly a third of that.

## Steamworks setup checklist

1. **App ID.** Put your real app ID in `desktop/steam_appid.txt` instead of 480 (or set `AUSSIE8_STEAM_APPID`).
2. **Achievements** (Steamworks → Stats & Achievements). Enter these API names exactly; the game maps its trophies to them.
   Each achievement also needs two icons, 256×256 JPG or PNG: one in colour (achieved) and one greyed out (locked).

   | API name | Display name | Description |
   |---|---|---|
| `A8_FIRST_WIN` | First blood | Win a race. |
| `A8_CLEAN_WIN` | Not a scratch | Win a race without a single crash. |
| `A8_PODIUM3` | Regular on the box | Finish on the podium three races in a row. |
| `A8_SURVIVOR` | Held together with tape | Finish a race after three or more crashes. |
| `A8_NITRO5` | Nitro junkie | Fire five nitros in one race. |
| `A8_ROO` | Roo spotter | Get bounced by a kangaroo. |
| `A8_BET` | High roller | Win a side bet or a bet with a rival. |
| `A8_PIE_MATE` | Pie mates | Get the Yowie on side: mate level. |
| `A8_UNMASKED` | Unmasked | Beat the Yowie in the final round and see who’s under the helmet. |
| `A8_TRUTH` | Truth teller | Tell someone the truth about ’94. |
| `A8_CHAMPION` | Champion of the outback | Win the season. |
| `A8_PEOPLE` | The People’s Champion | Win the season with a great reputation. |
| `A8_OUTLAW` | Run out of town | Finish a season with a terrible reputation. |
| `A8_CLEAN_HANDS` | Clean hands | Finish a season without taking a single dirty envelope. |
| `A8_GHOST` | Ghost buster | Beat a ghost’s lap in Time Trial. |
| `A8_MEDAL` | On the podium of the world | Win a weekly challenge medal. |
| `A8_ONLINE` | Mates’ rates | Finish a live race with friends. |
| `A8_SEASON2` | Back for more | Start a second season. |

   Trophies earned before the Steam build (or while offline) are re-sent to Steam every time the game starts.
3. **Steam Cloud** (Steamworks → Cloud → Auto-Cloud). Saves live in one file, `saves.json`:

   | OS | Root | Subdirectory |
   |---|---|---|
   | Windows | `WinAppDataRoaming` | `Aussie 8` |
   | macOS | `MacAppSupport` | `Aussie 8` |
   | Linux / Steam Deck | `LinuxXdgConfigHome` | `Aussie 8` |

   Pattern: `saves.json`. Set a byte quota of 1 MB and a file limit of 10, which is plenty.
4. **Launch options** (Installation → General):
   - Windows: `Aussie 8.exe`
   - macOS: `Aussie 8.app`
   - Linux: `aussie8`
5. **Rich presence** works as is through the `status` key. For nicer text in friends' lists, add a localisation file in Steamworks; no code change is needed.
6. **Steam Deck:** the game starts fullscreen on the Deck automatically, and controller support is already in. Before you ask for "Verified", check the small in-race text on the Deck's 7" screen.
7. **Before release:** remove `steam_appid.txt` from the uploaded depots. Steam supplies the app ID itself when it launches the game.

## Online features

Sign-in, leaderboards, weekly challenge, cloud saves and live races talk to the same Supabase backend as the website.
Before charging money, move the Supabase project off the free plan so it doesn't pause when it's quiet.

## Still to do

- Steam store art: capsules, library art, screenshots, a trailer. Check Valve's current Graphical Assets page for the sizes.
- 36 achievement icons (18 achieved + 18 locked).
- Answer Steam's content survey honestly: AI-generated content, simulated gambling (Gazza and Dex), tobacco and alcohol references.
