-- M13 hardening: prevent direct seed RPC execution and enforce
-- parent/child component integrity without a self-referencing RLS policy.

revoke execute on function public.seed_vehicle_digital_twin_systems()
from public, anon, authenticated;

create or replace function public.validate_vehicle_component_parent()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    parent_owner uuid;
    parent_vehicle bigint;
begin
    if new.parent_component_id is null then
        return new;
    end if;

    select owner_id, vehicle_id
    into parent_owner, parent_vehicle
    from public.vehicle_components
    where id = new.parent_component_id;

    if parent_owner is null then
        raise exception 'Parent component does not exist.';
    end if;

    if parent_owner <> new.owner_id
       or parent_vehicle <> new.vehicle_id then
        raise exception 'Parent component must belong to the same owner and vehicle.';
    end if;

    return new;
end;
$$;

revoke execute on function public.validate_vehicle_component_parent()
from public, anon, authenticated;

drop trigger if exists validate_vehicle_component_parent_before_write
    on public.vehicle_components;

create trigger validate_vehicle_component_parent_before_write
before insert or update of parent_component_id, owner_id, vehicle_id
on public.vehicle_components
for each row
execute function public.validate_vehicle_component_parent();

drop policy if exists "Users can create own vehicle components"
    on public.vehicle_components;

create policy "Users can create own vehicle components"
    on public.vehicle_components
    for insert
    to authenticated
    with check (
        auth.uid() = owner_id
        and exists (
            select 1
            from public.vehicles v
            where v.id = vehicle_components.vehicle_id
              and v.owner_id = auth.uid()
        )
    );

drop policy if exists "Users can update own vehicle components"
    on public.vehicle_components;

create policy "Users can update own vehicle components"
    on public.vehicle_components
    for update
    to authenticated
    using (auth.uid() = owner_id)
    with check (
        auth.uid() = owner_id
        and exists (
            select 1
            from public.vehicles v
            where v.id = vehicle_components.vehicle_id
              and v.owner_id = auth.uid()
        )
    );
