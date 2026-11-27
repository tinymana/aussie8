/**
 * Aussie 8 online API: one Supabase Edge Function, called with POST { action, ... }.
 * Lives in the tiny-mana-jams project, in its own `aussie8` schema.
 *
 * Sign-in works like Typlympics: an arcade name and a four-digit PIN. A new name creates the driver; a known
 * name needs its PIN (five wrong PINs lock it for 15 minutes). The client gets a random session token; only its
 * SHA-256 is stored.
 *
 * Times are checked, not trusted: a lap must be slower than the fastest truck could physically go on that track,
 * and its ghost path has to match the time it claims and never move faster than a truck can.
 *
 * Deploy: this file is deployed as-is (no bundling).
 */
// @ts-expect-error Deno resolves npm: specifiers at runtime.
import postgres from 'npm:postgres@3.4.5';

declare const Deno: { env: { get(name: string): string | undefined }; serve(handler: (req: Request) => Promise<Response> | Response): void };

const sql = postgres(Deno.env.get('SUPABASE_DB_URL') as string, { prepare: false, max: 2, idle_timeout: 20 });

const PIN_ATTEMPTS = 5;
const LOCK_MINUTES = 15;
const TRACKS = 8;
const LAPS = 4;
/** Track length in game units (from play/index.html). */
const TRACK_LEN = [2088, 2294, 2187, 2437, 2287, 2257, 2354, 2435];
/** Fastest a truck can move: fully upgraded engine (281) with nitro (x1.35), plus a margin. */
const MAX_SPEED = 400;
/** Ghosts are sampled every 100 ms as [x, y, angle x 100]. */
const GHOST_STEP_MS = 100;
const BOARD_SIZE = 20;

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

class ApiError extends Error {
  constructor(readonly code: string, message: string, readonly status = 400) { super(message); }
}
type Row = Record<string, any>;
type Body = Record<string, unknown>;

function str(body: Body, key: string): string {
  const v = body[key];
  if (typeof v !== 'string') throw new ApiError('bad_request', `"${key}" is required.`);
  return v;
}
function int(body: Body, key: string, lo: number, hi: number): number {
  const v = body[key];
  if (typeof v !== 'number' || !Number.isInteger(v) || v < lo || v > hi) throw new ApiError('bad_request', `"${key}" is out of range.`);
  return v;
}

// ------------------------------------------------------------ names (same filter as Typlympics)
const BLOCKED_ANYWHERE = [
  'FUCK', 'SHIT', 'BITCH', 'CUNT', 'NIGG', 'NIGA', 'FAGG', 'FAGOT', 'DYKE', 'KIKE', 'CHINK', 'GOOK', 'WETBACK', 'TRANNY', 'RETARD',
  'WHORE', 'SLUT', 'PUSSY', 'PENIS', 'VAGINA', 'RAPIST', 'PEDO', 'NAZI', 'HITLER', 'KKK', 'PORN', 'JIZZ',
  'WANK', 'TWAT', 'BASTARD', 'ASSHOLE', 'ARSEHOLE', 'DOUCHE', 'BOLLOCK', 'MILF', 'DILDO', 'BLOWJOB', 'HANDJOB', 'CUMSHOT',
];
const BLOCKED_WORDS = ['DICK', 'COCK', 'SPIC', 'RAPE', 'ANUS', 'ASS', 'ARSE', 'CUM', 'FAG', 'TIT', 'TITS', 'SEX', 'HOE', 'COON', 'JAP', 'PISS', 'CRAP', 'DAMN', 'HELL'];
const DIGIT_LETTERS: Record<string, string> = { '0': 'O', '1': 'I', '3': 'E', '4': 'A', '5': 'S', '7': 'T', '8': 'B', '9': 'G' };
function nameAllowed(name: string): boolean {
  const read = name.toUpperCase().replace(/[0-9]/g, (d) => DIGIT_LETTERS[d] ?? '');
  const squashed = read.replace(/[^A-Z]/g, '');
  const collapsed = squashed.replace(/(.)\1+/g, '$1');
  for (const bad of BLOCKED_ANYWHERE) {
    if (squashed.includes(bad)) return false;
    const short = bad.replace(/(.)\1+/g, '$1');
    if (short.length >= 4 && collapsed.includes(short)) return false;
  }
  const words = read.split(/[^A-Z]+/).filter(Boolean);
  return !words.some((w) => BLOCKED_WORDS.includes(w)) && !BLOCKED_WORDS.includes(squashed);
}
function normalizeName(raw: string): string {
  return raw.toUpperCase().replace(/[^A-Z0-9 ]/g, '').replace(/\s+/g, ' ').trim().slice(0, 10).trim();
}

function randomHex(bytes: number): string {
  const buf = new Uint8Array(bytes);
  crypto.getRandomValues(buf);
  return Array.from(buf, (b) => b.toString(16).padStart(2, '0')).join('');
}
async function sha256(text: string): Promise<string> {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, '0')).join('');
}

// ------------------------------------------------------------ drivers
async function enter(body: Body): Promise<Row> {
  const name = normalizeName(str(body, 'name'));
  const pin = str(body, 'pin');
  if (!name) throw new ApiError('bad_name', 'A name is required.');
  if (!/^[0-9]{4}$/.test(pin)) throw new ApiError('bad_pin', 'The PIN must be four digits.');
  let created = false;
  let rows: Row[] = await sql`
    select id, name, pin_hash = extensions.crypt(${pin}, pin_hash) as ok, coalesce(locked_until > now(), false) as locked
    from aussie8.drivers where name = ${name}`;
  if (rows.length === 0) {
    if (!nameAllowed(name)) throw new ApiError('bad_name', 'Pick another name.');
    rows = await sql`
      insert into aussie8.drivers (name, pin_hash) values (${name}, extensions.crypt(${pin}, extensions.gen_salt('bf', 10)))
      on conflict (name) do nothing returning id, name, true as ok, false as locked`;
    if (rows.length === 0) throw new ApiError('name_taken', 'That name was just taken. Try again.');
    created = true;
  }
  const d = rows[0];
  if (d.locked) throw new ApiError('locked', `Too many wrong PINs. Try again in ${LOCK_MINUTES} minutes.`, 429);
  if (!d.ok) {
    await sql`
      update aussie8.drivers set failed_attempts = failed_attempts + 1,
        locked_until = case when failed_attempts + 1 >= ${PIN_ATTEMPTS} then now() + make_interval(mins => ${LOCK_MINUTES}) else locked_until end
      where id = ${d.id}`;
    throw new ApiError('wrong_pin', 'That name is taken and the PIN does not match.', 401);
  }
  if (!created) await sql`update aussie8.drivers set failed_attempts = 0, locked_until = null where id = ${d.id}`;
  const token = randomHex(32);
  await sql`insert into aussie8.sessions (token_hash, driver_id) values (${await sha256(token)}, ${d.id})`;
  await sql`delete from aussie8.sessions where driver_id = ${d.id} and last_seen < now() - interval '60 days'`;
  return { token, created, driver: { id: d.id, name: d.name } };
}

async function auth(body: Body): Promise<Row> {
  const rows: Row[] = await sql`
    update aussie8.sessions s set last_seen = now() from aussie8.drivers d
    where s.token_hash = ${await sha256(str(body, 'token'))} and d.id = s.driver_id
    returning d.id, d.name`;
  if (rows.length === 0) throw new ApiError('signed_out', 'Sign in again.', 401);
  return rows[0];
}

// ------------------------------------------------------------ times
function minLapMs(track: number): number { return Math.floor((TRACK_LEN[track] / MAX_SPEED) * 1000); }

/** A ghost is a flat array [x0, y0, a0, x1, y1, a1, ...] sampled every 100 ms. */
function checkGhost(ghost: unknown, lapMs: number): number[] {
  if (!Array.isArray(ghost) || ghost.length % 3 !== 0 || ghost.length > 3 * 3000) throw new ApiError('bad_ghost', 'Ghost data is malformed.');
  if (!ghost.every((v) => typeof v === 'number' && Number.isFinite(v) && Math.abs(v) < 100000)) throw new ApiError('bad_ghost', 'Ghost data is malformed.');
  const n = ghost.length / 3;
  const span = (n - 1) * GHOST_STEP_MS;
  if (Math.abs(span - lapMs) > Math.max(400, lapMs * 0.08)) throw new ApiError('bad_ghost', 'Ghost does not match the lap time.');
  for (let i = 1; i < n; i++) {
    const dx = (ghost[i * 3] as number) - (ghost[i * 3 - 3] as number), dy = (ghost[i * 3 + 1] as number) - (ghost[i * 3 - 2] as number);
    if (Math.hypot(dx, dy) > MAX_SPEED * (GHOST_STEP_MS / 1000) * 1.25 + 2) throw new ApiError('bad_ghost', 'Ghost moves faster than a truck can.');
  }
  return ghost.map((v) => Math.round(v as number));
}

async function submitLap(body: Body): Promise<Row> {
  const d = await auth(body);
  const track = int(body, 'track', 0, TRACKS - 1);
  const lapMs = int(body, 'lap_ms', 1, 600000);
  if (lapMs < minLapMs(track)) throw new ApiError('too_fast', 'That lap is faster than a truck can go.', 422);
  const ghost = checkGhost(body['ghost'], lapMs);
  const rows: Row[] = await sql`
    insert into aussie8.laps (driver_id, track, lap_ms, ghost) values (${d.id}, ${track}, ${lapMs}, ${sql.json(ghost)})
    on conflict (driver_id, track) do update set lap_ms = excluded.lap_ms, ghost = excluded.ghost, achieved_at = now()
      where aussie8.laps.lap_ms > excluded.lap_ms
    returning lap_ms`;
  const best: Row[] = await sql`select lap_ms from aussie8.laps where driver_id = ${d.id} and track = ${track}`;
  const rank: Row[] = await sql`select count(*)::int + 1 as rank from aussie8.laps where track = ${track} and lap_ms < ${best[0].lap_ms}`;
  return { improved: rows.length > 0, best_ms: best[0].lap_ms, rank: rank[0].rank };
}

async function submitRace(body: Body): Promise<Row> {
  const d = await auth(body);
  const track = int(body, 'track', 0, TRACKS - 1);
  const raceMs = int(body, 'race_ms', 1, 1800000);
  const place = int(body, 'place', 1, 8);
  if (raceMs < minLapMs(track) * LAPS) throw new ApiError('too_fast', 'That race is faster than a truck can go.', 422);
  const rows: Row[] = await sql`
    insert into aussie8.races (driver_id, track, race_ms, place) values (${d.id}, ${track}, ${raceMs}, ${place})
    on conflict (driver_id, track) do update set race_ms = excluded.race_ms, place = excluded.place, achieved_at = now()
      where aussie8.races.race_ms > excluded.race_ms
    returning race_ms`;
  return { improved: rows.length > 0 };
}

async function board(body: Body): Promise<Row> {
  const track = int(body, 'track', 0, TRACKS - 1);
  const laps: Row[] = await sql`
    select d.id, d.name, l.lap_ms as ms, l.achieved_at as at from aussie8.laps l join aussie8.drivers d on d.id = l.driver_id
    where l.track = ${track} order by l.lap_ms, l.achieved_at limit ${BOARD_SIZE}`;
  const races: Row[] = await sql`
    select d.id, d.name, r.race_ms as ms, r.place, r.achieved_at as at from aussie8.races r join aussie8.drivers d on d.id = r.driver_id
    where r.track = ${track} order by r.race_ms, r.achieved_at limit ${BOARD_SIZE}`;
  return { track, laps, races };
}

async function ghost(body: Body): Promise<Row> {
  const track = int(body, 'track', 0, TRACKS - 1);
  const id = str(body, 'driver_id');
  if (!/^[0-9a-f-]{36}$/.test(id)) throw new ApiError('bad_request', 'Unknown driver.');
  const rows: Row[] = await sql`
    select d.name, l.lap_ms, l.ghost from aussie8.laps l join aussie8.drivers d on d.id = l.driver_id
    where l.track = ${track} and l.driver_id = ${id}`;
  if (rows.length === 0) throw new ApiError('no_ghost', 'No ghost for that driver on this track.', 404);
  return { name: rows[0].name, lap_ms: rows[0].lap_ms, step_ms: GHOST_STEP_MS, ghost: rows[0].ghost };
}

async function signout(body: Body): Promise<Row> {
  await sql`delete from aussie8.sessions where token_hash = ${await sha256(str(body, 'token'))}`;
  return { ok: true };
}

const ACTIONS: Record<string, (b: Body) => Promise<Row>> = {
  enter, me: async (b) => ({ driver: await auth(b) }), submit_lap: submitLap, submit_race: submitRace, board, ghost, signout,
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  const json = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: { ...CORS, 'Content-Type': 'application/json' } });
  try {
    if (req.method !== 'POST') throw new ApiError('bad_request', 'POST only.', 405);
    const body = (await req.json().catch(() => null)) as Body | null;
    if (!body || typeof body !== 'object') throw new ApiError('bad_request', 'JSON body required.');
    const fn = ACTIONS[String(body['action'])];
    if (!fn) throw new ApiError('bad_request', 'Unknown action.');
    return json(await fn(body));
  } catch (e) {
    if (e instanceof ApiError) return json({ error: e.code, message: e.message }, e.status);
    console.error(e);
    return json({ error: 'server', message: 'Something went wrong. Try again.' }, 500);
  }
});
