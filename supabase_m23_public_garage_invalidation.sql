-- M23 — Fail-closed public snapshot invalidation.

create or replace function public.invalidate_public_snapshot_from_profile()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    target_owner uuid;
begin
    target_owner := coalesce(new.owner_id, old.owner_id);

    delete from public.public_garage_snapshots s
    using public.public_garages g
    where s.slug = g.slug
      and g.owner_id = target_owner;

    if tg_op = 'DELETE' then
        return old;
    end if;

    return new;
end;
$$;

revoke execute on function public.invalidate_public_snapshot_from_profile()
from public, anon, authenticated;

drop trigger if exists invalidate_public_snapshot_after_profile_change
    on public.public_vehicle_profiles;
create trigger invalidate_public_snapshot_after_profile_change
after insert or update or delete
on public.public_vehicle_profiles
for each row
execute function public.invalidate_public_snapshot_from_profile();

create or replace function public.invalidate_public_snapshot_from_garage()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if new.is_public then
        delete from public.public_garage_snapshots
        where slug = new.slug;
    end if;

    return new;
end;
$$;

revoke execute on function public.invalidate_public_snapshot_from_garage()
from public, anon, authenticated;

drop trigger if exists invalidate_public_snapshot_after_garage_change
    on public.public_garages;
create trigger invalidate_public_snapshot_after_garage_change
after update of slug, display_name, bio, theme
on public.public_garages
for each row
execute function public.invalidate_public_snapshot_from_garage();

create or replace function public.invalidate_public_snapshot_from_vehicle()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if exists (
        select 1
        from public.public_vehicle_profiles p
        join public.public_garages g
          on g.owner_id = p.owner_id
        where p.vehicle_id = new.id
          and p.owner_id = new.owner_id
          and p.is_public = true
          and g.is_public = true
    ) then
        delete from public.public_garage_snapshots s
        using public.public_garages g
        where s.slug = g.slug
          and g.owner_id = new.owner_id;
    end if;

    return new;
end;
$$;

revoke execute on function public.invalidate_public_snapshot_from_vehicle()
from public, anon, authenticated;

drop trigger if exists invalidate_public_snapshot_after_vehicle_change
    on public.vehicles;
create trigger invalidate_public_snapshot_after_vehicle_change
after update of
    profile_name,
    manufacturer,
    model,
    year,
    engine,
    mileage,
    photo_path
on public.vehicles
for each row
execute function public.invalidate_public_snapshot_from_vehicle();

create or replace function public.invalidate_public_snapshot_from_component()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    target_owner uuid;
    target_vehicle bigint;
begin
    target_owner := coalesce(new.owner_id, old.owner_id);
    target_vehicle := coalesce(new.vehicle_id, old.vehicle_id);

    if exists (
        select 1
        from public.public_vehicle_profiles p
        join public.public_garages g
          on g.owner_id = p.owner_id
        where p.vehicle_id = target_vehicle
          and p.owner_id = target_owner
          and p.is_public = true
          and p.show_modifications = true
          and g.is_public = true
    ) then
        delete from public.public_garage_snapshots s
        using public.public_garages g
        where s.slug = g.slug
          and g.owner_id = target_owner;
    end if;

    if tg_op = 'DELETE' then
        return old;
    end if;

    return new;
end;
$$;

revoke execute on function public.invalidate_public_snapshot_from_component()
from public, anon, authenticated;

drop trigger if exists invalidate_public_snapshot_after_component_change
    on public.vehicle_components;
create trigger invalidate_public_snapshot_after_component_change
after insert or update or delete
on public.vehicle_components
for each row
execute function public.invalidate_public_snapshot_from_component();

create or replace function public.invalidate_public_snapshot_from_specification()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    target_owner uuid;
    target_vehicle bigint;
begin
    target_owner := coalesce(new.owner_id, old.owner_id);
    target_vehicle := coalesce(new.vehicle_id, old.vehicle_id);

    if exists (
        select 1
        from public.public_vehicle_profiles p
        join public.public_garages g
          on g.owner_id = p.owner_id
        where p.vehicle_id = target_vehicle
          and p.owner_id = target_owner
          and p.is_public = true
          and p.show_specifications = true
          and g.is_public = true
    ) then
        delete from public.public_garage_snapshots s
        using public.public_garages g
        where s.slug = g.slug
          and g.owner_id = target_owner;
    end if;

    if tg_op = 'DELETE' then
        return old;
    end if;

    return new;
end;
$$;

revoke execute on function public.invalidate_public_snapshot_from_specification()
from public, anon, authenticated;

drop trigger if exists invalidate_public_snapshot_after_specification_change
    on public.vehicle_specifications;
create trigger invalidate_public_snapshot_after_specification_change
after insert or update or delete
on public.vehicle_specifications
for each row
execute function public.invalidate_public_snapshot_from_specification();
