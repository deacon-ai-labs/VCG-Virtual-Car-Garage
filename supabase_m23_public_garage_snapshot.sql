-- M23 — Sanitised public snapshot read model.
-- Anonymous users can read only rows that already contain public-safe payloads.

create table if not exists public.public_garage_snapshots (
    slug text primary key
        references public.public_garages(slug)
        on update cascade
        on delete cascade,
    payload jsonb not null check (
        jsonb_typeof(payload) = 'object'
    ),
    published_at timestamptz not null default now()
);

alter table public.public_garage_snapshots enable row level security;

drop policy if exists "Anyone can view published garage snapshots"
    on public.public_garage_snapshots;
create policy "Anyone can view published garage snapshots"
    on public.public_garage_snapshots
    for select to anon
    using (true);

drop policy if exists "Owners can view own garage snapshots"
    on public.public_garage_snapshots;
create policy "Owners can view own garage snapshots"
    on public.public_garage_snapshots
    for select to authenticated
    using (
        exists (
            select 1
            from public.public_garages g
            where g.slug = public_garage_snapshots.slug
              and g.owner_id = auth.uid()
        )
    );

drop policy if exists "Owners can publish own garage snapshots"
    on public.public_garage_snapshots;
create policy "Owners can publish own garage snapshots"
    on public.public_garage_snapshots
    for insert to authenticated
    with check (
        exists (
            select 1
            from public.public_garages g
            where g.slug = public_garage_snapshots.slug
              and g.owner_id = auth.uid()
              and g.is_public = true
        )
    );

drop policy if exists "Owners can update own garage snapshots"
    on public.public_garage_snapshots;
create policy "Owners can update own garage snapshots"
    on public.public_garage_snapshots
    for update to authenticated
    using (
        exists (
            select 1
            from public.public_garages g
            where g.slug = public_garage_snapshots.slug
              and g.owner_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1
            from public.public_garages g
            where g.slug = public_garage_snapshots.slug
              and g.owner_id = auth.uid()
              and g.is_public = true
        )
    );

drop policy if exists "Owners can delete own garage snapshots"
    on public.public_garage_snapshots;
create policy "Owners can delete own garage snapshots"
    on public.public_garage_snapshots
    for delete to authenticated
    using (
        exists (
            select 1
            from public.public_garages g
            where g.slug = public_garage_snapshots.slug
              and g.owner_id = auth.uid()
        )
    );

grant select on public.public_garage_snapshots to anon;
grant select, insert, update, delete
on public.public_garage_snapshots
to authenticated;

drop function if exists public.get_public_garage(text);

create or replace function public.revoke_public_photos_when_garage_hidden()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    target_owner uuid;
    target_slug text;
begin
    target_owner := coalesce(new.owner_id, old.owner_id);
    target_slug := coalesce(new.slug, old.slug);

    if tg_op = 'DELETE'
       or (old.is_public and not new.is_public) then
        delete from public.public_garage_snapshots
        where slug = target_slug;

        update public.public_vehicle_profiles
        set public_photo_path = null
        where owner_id = target_owner
          and public_photo_path is not null;
    end if;

    if tg_op = 'DELETE' then
        return old;
    end if;

    return new;
end;
$$;

revoke execute on function public.revoke_public_photos_when_garage_hidden()
from public, anon, authenticated;
