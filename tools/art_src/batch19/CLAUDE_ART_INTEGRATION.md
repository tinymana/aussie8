# Batch 19 — integration
Read manifest.json. Map proposed filenames to existing character and mood IDs; preserve approved neutral portraits unless replacement is approved. Dex laugh maps to happy. June focused is a new optional mood. Windbreakers is a group portrait, wider than standard. Portraits have opaque light backgrounds, not alpha cutouts; use within dialogue frames. Inspect crops and character canon before replacing initials.

Crowd: four static opaque section tiles, not animation frames. Use existing Batch 15 animated crowd for ambient motion. On a wreck, briefly switch selected sections to surprised for 700–1200 ms, then restore previous state; debounce repeated impacts. Tiles are alternate illustrations, not pose-aligned animation; avoid visible popping by using a short cut or use as reference for individual spectator animations. Keep outside overhead track and collision system.

Billboards: 120x32 opaque front-facing signs for stadium horizon, not overhead track obstacles. Names are proposed fictional sponsors; review trademarks before commercial use. Keep original racing physics, save system and Yowie reveal. No code changes included.
