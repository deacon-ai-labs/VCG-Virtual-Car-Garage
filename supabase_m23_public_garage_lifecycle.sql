-- M23 — Public showcase photo revocation lifecycle.

create or replace function public.queue_public_showcase_photo_cleanup()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if tg_op = 'DELETE' then
        if old.public_photo_path is not null then
            insert into public.storage_cleanup_queue (
                owner_id,bucket_id,storage_path,reason
            )
            values (
                old.owner_id,'public-garage',old.public_photo_path,'public_photo_revoke'
            )
            on conflict (owner_id,bucket_id,storage_path) do nothing;
        end if;
        return old;
    end if;

    if (
        old.public_photo_path is not null
        and old.public_photo_path is distinct from new.public_photo_path
    ) then
        insert into public.storage_cleanup_queue (
            owner_id,bucket_id,storage_path,reason
        )
        values (
            old.owner_id,'public-garage',old.public_photo_path,'public_photo_revoke'
        )
        on conflict (owner_id,bucket_id,storage_path) do nothing;
    end if;

    if (not new.is_public or not new.show_photo) then
        if new.public_photo_path is not null then
            insert into public.storage_cleanup_queue (
                owner_id,bucket_id,storage_path,reason
            )
            values (
                new.owner_id,'public-garage',new.public_photo_path,'public_photo_revoke'
            )
            on conflict (owner_id,bucket_id,storage_path) do nothing;
        end if;
        new.public_photo_path := null;
    end if;

    return new;
end;
$$;

revoke execute on function public.queue_public_showcase_photo_cleanup()
from public, anon, authenticated;

drop trigger if exists queue_public_showcase_photo_before_change
    on public.public_vehicle_profiles;
create trigger queue_public_showcase_photo_before_change
before update or delete on public.public_vehicle_profiles
for each row execute function public.queue_public_showcase_photo_cleanup();

create or replace function public.revoke_public_photos_when_garage_hidden()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    target_owner uuid;
begin
    target_owner := coalesce(new.owner_id, old.owner_id);

    if tg_op = 'DELETE'
       or (old.is_public and not new.is_public) then
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

drop trigger if exists revoke_public_photos_after_garage_private
    on public.public_garages;
drop trigger if exists revoke_public_photos_after_garage_hidden
    on public.public_garages;
create trigger revoke_public_photos_after_garage_hidden
after update of is_public or delete on public.public_garages
for each row execute function public.revoke_public_photos_when_garage_hidden();

drop function if exists public.revoke_public_photos_when_garage_private();

create or replace function public.revoke_public_photo_when_source_changes()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if old.photo_path is distinct from new.photo_path then
        update public.public_vehicle_profiles
        set public_photo_path = null
        where vehicle_id = new.id
          and owner_id = new.owner_id
          and public_photo_path is not null;
    end if;

    return new;
end;
$$;

revoke execute on function public.revoke_public_photo_when_source_changes()
from public, anon, authenticated;

drop trigger if exists revoke_public_photo_after_vehicle_photo_change
    on public.vehicles;
create trigger revoke_public_photo_after_vehicle_photo_change
after update of photo_path on public.vehicles
for each row execute function public.revoke_public_photo_when_source_changes();
