-- Web pivot: magic-link auth + email delivery.
-- Adds email + timezone, relaxes the Apple-only constraint, and auto-creates
-- a public.users row when a Supabase Auth user is created.

alter table public.users
  add column if not exists email text,
  add column if not exists timezone text not null default 'UTC';

-- apple_sub was required for Sign in with Apple; web users authenticate via
-- magic link and have no apple_sub.
alter table public.users
  alter column apple_sub drop not null;

-- Create the application user row on Supabase Auth signup so id == auth.uid().
create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.users (id, email)
  values (new.id, new.email)
  on conflict (id) do update set email = excluded.email;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_auth_user();
