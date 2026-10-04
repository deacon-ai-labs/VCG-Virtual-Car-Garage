-- M22.1 — Security & Data Lifecycle Hardening
-- Adds retryable private-storage cleanup for vehicle deletion.

create table if not exists public.storage_cleanup_queue (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    bucket_id text not null,
    storage_path text not null,
    reason text not null default 'vehicle_delete',
    attempts integer not null default 0 check (attempts >= 0),
    last_error_type text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (owner_id, bucket_id, storage_path)
);

create index if not exists storage_cleanup_queue_owner_idx
    on public.storage_cleanup_queue(
        owner_id,
        created_at
    );

alter table public.storage_cleanup_queue enable row level security;

drop policy if exists "Users can view own cleanup queue"
    on public.storage_cleanup_queue;
create policy "Users can view own cleanup queue"
    on public.storage_cleanup_queue
    for select to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own cleanup queue"
    on public.storage_cleanup_queue;
create policy "Users can create own cleanup queue"
    on public.storage_cleanup_queue
    for insert to authenticated
    with check (auth.uid() = owner_id);

drop policy if exists "Users can update own cleanup queue"
    on public.storage_cleanup_queue;
create policy "Users can update own cleanup queue"
    on public.storage_cleanup_queue
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

drop policy if exists "Users can delete own cleanup queue"
    on public.storage_cleanup_queue;
create policy "Users can delete own cleanup queue"
    on public.storage_cleanup_queue
    for delete to authenticated
    using (auth.uid() = owner_id);

create or replace function public.touch_storage_cleanup_queue_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

revoke execute on function public.touch_storage_cleanup_queue_updated_at()
from public, anon, authenticated;

drop trigger if exists touch_storage_cleanup_queue_updated_at
    on public.storage_cleanup_queue;

create trigger touch_storage_cleanup_queue_updated_at
before update on public.storage_cleanup_queue
for each row
execute function public.touch_storage_cleanup_queue_updated_at();

create or replace function public.delete_vehicle_for_cleanup(
    p_vehicle_id bigint
)
returns void
language plpgsql
security invoker
set search_path = public
as $$
begin
    if not exists (
        select 1
        from public.vehicles
        where id = p_vehicle_id
          and owner_id = auth.uid()
    ) then
        raise exception 'Vehicle was not found.';
    end if;

    delete from public.vehicle_intake_candidates
    where vehicle_id = p_vehicle_id
      and owner_id = auth.uid();

    delete from public.vehicles
    where id = p_vehicle_id
      and owner_id = auth.uid();
end;
$$;

revoke execute on function public.delete_vehicle_for_cleanup(bigint)
from public, anon;

grant execute on function public.delete_vehicle_for_cleanup(bigint)
to authenticated, service_role;
