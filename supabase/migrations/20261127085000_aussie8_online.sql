-- Aussie 8 online (applied to the tiny-mana-jams project as migration "aussie8_online").
-- Drivers (arcade name + 4-digit PIN), sessions, best laps with ghosts, best races.
-- Only the aussie8 edge function touches these tables (it connects as the database owner); the public
-- API roles get no access to the schema at all. Live races use Realtime broadcast and need no tables.
create schema if not exists aussie8;
revoke all on schema aussie8 from public, anon, authenticated;

create table aussie8.drivers (
  id uuid primary key default gen_random_uuid(),
  name text not null unique check (name ~ '^[A-Z0-9]+( [A-Z0-9]+)*$' and char_length(name) between 1 and 10),
  pin_hash text not null,
  failed_attempts int not null default 0,
  locked_until timestamptz,
  created_at timestamptz not null default now()
);

create table aussie8.sessions (
  token_hash text primary key,
  driver_id uuid not null references aussie8.drivers (id) on delete cascade,
  created_at timestamptz not null default now(),
  last_seen timestamptz not null default now()
);
create index sessions_driver_idx on aussie8.sessions (driver_id);

create table aussie8.laps (
  driver_id uuid not null references aussie8.drivers (id) on delete cascade,
  track int not null check (track between 0 and 7),
  lap_ms int not null check (lap_ms between 4000 and 600000),
  ghost jsonb not null,
  achieved_at timestamptz not null default now(),
  primary key (driver_id, track)
);
create index laps_board_idx on aussie8.laps (track, lap_ms);

create table aussie8.races (
  driver_id uuid not null references aussie8.drivers (id) on delete cascade,
  track int not null check (track between 0 and 7),
  race_ms int not null check (race_ms between 16000 and 1800000),
  place int check (place between 1 and 8),
  achieved_at timestamptz not null default now(),
  primary key (driver_id, track)
);
create index races_board_idx on aussie8.races (track, race_ms);

alter table aussie8.drivers enable row level security;
alter table aussie8.sessions enable row level security;
alter table aussie8.laps enable row level security;
alter table aussie8.races enable row level security;

-- Migration "aussie8_saves_weekly": cloud saves and the weekly best-lap challenge.
create table aussie8.saves (
  driver_id uuid primary key references aussie8.drivers (id) on delete cascade,
  data jsonb not null,
  version int not null default 0,
  updated_at timestamptz not null default now()
);
-- Week n starts on Monday 00:00 UTC, counted from Monday 2026-11-23 (week 0).
create table aussie8.weekly_laps (
  week int not null check (week >= 0),
  driver_id uuid not null references aussie8.drivers (id) on delete cascade,
  track int not null check (track between 0 and 7),
  lap_ms int not null check (lap_ms between 4000 and 600000),
  ghost jsonb not null,
  achieved_at timestamptz not null default now(),
  primary key (week, driver_id)
);
create index weekly_laps_board_idx on aussie8.weekly_laps (week, lap_ms);
create table aussie8.medals (
  week int not null,
  driver_id uuid not null references aussie8.drivers (id) on delete cascade,
  place int not null check (place between 1 and 3),
  track int not null,
  lap_ms int not null,
  primary key (week, driver_id)
);
create index medals_driver_idx on aussie8.medals (driver_id);
create table aussie8.weeks_closed (week int primary key, closed_at timestamptz not null default now());
alter table aussie8.saves enable row level security;
alter table aussie8.weekly_laps enable row level security;
alter table aussie8.medals enable row level security;
alter table aussie8.weeks_closed enable row level security;
