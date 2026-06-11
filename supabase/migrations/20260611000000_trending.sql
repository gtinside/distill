-- Trending & Discovery: a shared global digest, curated now and architected to
-- become world-derived later. See docs/superpowers/specs/2026-06-11-distill-trending-discovery-design.md
-- and ADR-0004.

-- Trending Topics — admin-curated selection. Only the selection is curated;
-- card content is always freshly synthesized.
create table trending_topics (
  id uuid primary key default gen_random_uuid(),
  phrase text not null,
  rank int not null default 0,
  active boolean not null default true,
  created_at timestamptz default now()
);

-- Trending Cards — one current row per trending topic (upsert on generation).
create table trending_cards (
  id uuid primary key default gen_random_uuid(),
  trending_topic_id uuid references trending_topics(id) on delete cascade,
  tldr text,
  bullets jsonb,
  sources jsonb,
  status text not null default 'ok' check (status in ('ok', 'error')),
  generated_at timestamptz default now(),
  unique (trending_topic_id)
);

-- Seed timely curated topics with increasing rank.
insert into trending_topics (phrase, rank) values
  ('Fed policy', 0),
  ('EU AI regulation', 1),
  ('Commercial spaceflight', 2),
  ('Generative video models', 3),
  ('US-China trade', 4),
  ('Climate tech funding', 5),
  ('Ultra-low-latency systems', 6),
  ('NBA trades', 7),
  ('Quantum computing', 8),
  ('Longevity research', 9);

-- Trending is world-readable. Writes happen via the service-role key (bypasses RLS).
alter table trending_topics enable row level security;
alter table trending_cards enable row level security;

create policy "trending public read"
  on trending_topics for select
  using (true);

create policy "trending public read"
  on trending_cards for select
  using (true);
