-- Users
create table users (
  id uuid primary key default gen_random_uuid(),
  apple_sub text unique not null,
  delivery_time time not null default '07:00',
  device_token text,
  created_at timestamptz default now()
);

-- Topics
create table topics (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  phrase text not null,
  display_order int not null default 0,
  created_at timestamptz default now()
);

-- Digests
create table digests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  generated_at timestamptz default now()
);

-- Topic Cards
create table topic_cards (
  id uuid primary key default gen_random_uuid(),
  digest_id uuid references digests(id) on delete cascade,
  topic_id uuid references topics(id) on delete cascade,
  tldr text,
  bullets jsonb,
  sources jsonb,
  status text not null default 'ok' check (status in ('ok', 'error')),
  last_refreshed_at timestamptz
);

-- Row Level Security
alter table users enable row level security;
alter table topics enable row level security;
alter table digests enable row level security;
alter table topic_cards enable row level security;

-- RLS Policies: users may only access their own rows
-- (auth.uid() maps to the Supabase Auth user id; we join via apple_sub on sign-in)

create policy "users: own row only"
  on users for all
  using (id = auth.uid());

create policy "topics: own rows only"
  on topics for all
  using (user_id = auth.uid());

create policy "digests: own rows only"
  on digests for all
  using (user_id = auth.uid());

create policy "topic_cards: own rows only"
  on topic_cards for all
  using (
    digest_id in (
      select id from digests where user_id = auth.uid()
    )
  );
