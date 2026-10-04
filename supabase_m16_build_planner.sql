-- M16 — Build Planner & Modification Intelligence
-- Separates physical current-state components from future install/removal plans.

alter table public.vehicle_components
    drop constraint if exists vehicle_components_lifecycle_status_check;

alter table public.vehicle_components
    add constraint vehicle_components_lifecycle_status_check
    check (
        lifecycle_status in (
            'installed',
            'planned',
            'removed',
            'unknown',
            'cancelled'
        )
    );

create table if not exists public.vehicle_build_plan_items (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    component_id uuid not null references public.vehicle_components(id) on delete cascade,
    action text not null check (action in ('install', 'remove')),
    status text not null default 'planned' check (
        status in ('wishlist', 'planned', 'ready', 'completed', 'cancelled')
    ),
    priority text not null default 'normal' check (
        priority in ('low', 'normal', 'high')
    ),
    estimated_cost_gbp numeric(10, 2) check (
        estimated_cost_gbp is null or estimated_cost_gbp >= 0
    ),
    actual_cost_gbp numeric(10, 2) check (
        actual_cost_gbp is null or actual_cost_gbp >= 0
    ),
    compatibility_status text not null default 'unknown' check (
        compatibility_status in (
            'unknown',
            'compatible',
            'needs_review',
            'incompatible'
        )
    ),
    compatibility_notes text,
    target_date date,
    notes text,
    sort_order integer not null default 0,
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists vehicle_build_plan_items_vehicle_idx
    on public.vehicle_build_plan_items(vehicle_id, status, sort_order);

create index if not exists vehicle_build_plan_items_component_idx
    on public.vehicle_build_plan_items(component_id);

create unique index if not exists vehicle_build_plan_active_action_unique
    on public.vehicle_build_plan_items(component_id, action)
    where status in ('wishlist', 'planned', 'ready');

alter table public.vehicle_build_plan_items enable row level security;

drop policy if exists "Users can view own build plan items"
    on public.vehicle_build_plan_items;
create policy "Users can view own build plan items"
    on public.vehicle_build_plan_items
    for select
    to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own build plan items"
    on public.vehicle_build_plan_items;
create policy "Users can create own build plan items"
    on public.vehicle_build_plan_items
    for insert
    to authenticated
    with check (
        auth.uid() = owner_id
        and exists (
            select 1
            from public.vehicles v
            where v.id = vehicle_build_plan_items.vehicle_id
              and v.owner_id = auth.uid()
        )
        and exists (
            select 1
            from public.vehicle_components c
            where c.id = vehicle_build_plan_items.component_id
              and c.vehicle_id = vehicle_build_plan_items.vehicle_id
              and c.owner_id = auth.uid()
              and c.component_type <> 'system'
        )
    );

drop policy if exists "Users can update own build plan items"
    on public.vehicle_build_plan_items;
create policy "Users can update own build plan items"
    on public.vehicle_build_plan_items
    for update
    to authenticated
    using (auth.uid() = owner_id)
    with check (
        auth.uid() = owner_id
        and exists (
            select 1
            from public.vehicles v
            where v.id = vehicle_build_plan_items.vehicle_id
              and v.owner_id = auth.uid()
        )
        and exists (
            select 1
            from public.vehicle_components c
            where c.id = vehicle_build_plan_items.component_id
              and c.vehicle_id = vehicle_build_plan_items.vehicle_id
              and c.owner_id = auth.uid()
              and c.component_type <> 'system'
        )
    );

drop policy if exists "Users can delete own build plan items"
    on public.vehicle_build_plan_items;
create policy "Users can delete own build plan items"
    on public.vehicle_build_plan_items
    for delete
    to authenticated
    using (auth.uid() = owner_id);

create or replace function public.validate_build_plan_item()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    component_row public.vehicle_components%rowtype;
begin
    select *
    into component_row
    from public.vehicle_components
    where id = new.component_id;

    if not found then
        raise exception 'Build-plan component does not exist.';
    end if;

    if component_row.owner_id <> new.owner_id
       or component_row.vehicle_id <> new.vehicle_id then
        raise exception 'Build-plan component must belong to the same owner and vehicle.';
    end if;

    if component_row.component_type = 'system' then
        raise exception 'Build plans must reference a component, not a root system.';
    end if;

    if new.action = 'install'
       and new.status in ('wishlist', 'planned', 'ready')
       and component_row.lifecycle_status not in ('planned', 'unknown') then
        raise exception 'Install plans must reference a planned component.';
    end if;

    if new.action = 'remove'
       and new.status in ('wishlist', 'planned', 'ready')
       and component_row.lifecycle_status <> 'installed' then
        raise exception 'Removal plans must reference an installed component.';
    end if;

    return new;
end;
$$;

revoke execute on function public.validate_build_plan_item()
from public, anon, authenticated;

drop trigger if exists validate_build_plan_item_before_write
    on public.vehicle_build_plan_items;

create trigger validate_build_plan_item_before_write
before insert or update of
    owner_id,
    vehicle_id,
    component_id,
    action,
    status
on public.vehicle_build_plan_items
for each row
execute function public.validate_build_plan_item();

create or replace function public.create_build_plan_install(
    p_vehicle_id bigint,
    p_parent_system_id uuid,
    p_name text,
    p_manufacturer text default null,
    p_part_number text default null,
    p_weight_kg numeric default null,
    p_is_oem boolean default null,
    p_plan_status text default 'planned',
    p_priority text default 'normal',
    p_estimated_cost_gbp numeric default null,
    p_compatibility_status text default 'unknown',
    p_compatibility_notes text default null,
    p_target_date date default null,
    p_notes text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
    parent_row public.vehicle_components%rowtype;
    component_id uuid;
    plan_item_id uuid;
    clean_name text;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    clean_name := nullif(btrim(p_name), '');

    if clean_name is null then
        raise exception 'Component name is required.';
    end if;

    if p_plan_status not in ('wishlist', 'planned', 'ready') then
        raise exception 'Invalid active plan status.';
    end if;

    if p_priority not in ('low', 'normal', 'high') then
        raise exception 'Invalid priority.';
    end if;

    if p_compatibility_status not in (
        'unknown',
        'compatible',
        'needs_review',
        'incompatible'
    ) then
        raise exception 'Invalid compatibility status.';
    end if;

    if p_weight_kg is not null and p_weight_kg < 0 then
        raise exception 'Weight cannot be negative.';
    end if;

    if p_estimated_cost_gbp is not null and p_estimated_cost_gbp < 0 then
        raise exception 'Estimated cost cannot be negative.';
    end if;

    if not exists (
        select 1
        from public.vehicles v
        where v.id = p_vehicle_id
          and v.owner_id = auth.uid()
    ) then
        raise exception 'Vehicle not found.';
    end if;

    select *
    into parent_row
    from public.vehicle_components
    where id = p_parent_system_id
      and vehicle_id = p_vehicle_id
      and owner_id = auth.uid()
      and component_type = 'system'
      and parent_component_id is null;

    if not found then
        raise exception 'Vehicle system not found.';
    end if;

    insert into public.vehicle_components (
        owner_id,
        vehicle_id,
        parent_component_id,
        component_type,
        system_key,
        name,
        lifecycle_status,
        is_oem,
        manufacturer,
        part_number,
        weight_kg,
        notes,
        metadata
    )
    values (
        auth.uid(),
        p_vehicle_id,
        parent_row.id,
        'component',
        parent_row.system_key,
        clean_name,
        'planned',
        p_is_oem,
        nullif(btrim(p_manufacturer), ''),
        nullif(btrim(p_part_number), ''),
        p_weight_kg,
        nullif(btrim(p_notes), ''),
        jsonb_build_object('source', 'm16_build_planner')
    )
    returning id into component_id;

    insert into public.vehicle_build_plan_items (
        owner_id,
        vehicle_id,
        component_id,
        action,
        status,
        priority,
        estimated_cost_gbp,
        compatibility_status,
        compatibility_notes,
        target_date,
        notes
    )
    values (
        auth.uid(),
        p_vehicle_id,
        component_id,
        'install',
        p_plan_status,
        p_priority,
        p_estimated_cost_gbp,
        p_compatibility_status,
        nullif(btrim(p_compatibility_notes), ''),
        p_target_date,
        nullif(btrim(p_notes), '')
    )
    returning id into plan_item_id;

    return jsonb_build_object(
        'component_id', component_id,
        'plan_item_id', plan_item_id
    );
end;
$$;

create or replace function public.create_build_plan_removal(
    p_component_id uuid,
    p_plan_status text default 'planned',
    p_priority text default 'normal',
    p_estimated_cost_gbp numeric default null,
    p_target_date date default null,
    p_notes text default null
)
returns uuid
language plpgsql
security invoker
set search_path = public
as $$
declare
    component_row public.vehicle_components%rowtype;
    plan_item_id uuid;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    if p_plan_status not in ('wishlist', 'planned', 'ready') then
        raise exception 'Invalid active plan status.';
    end if;

    if p_priority not in ('low', 'normal', 'high') then
        raise exception 'Invalid priority.';
    end if;

    if p_estimated_cost_gbp is not null and p_estimated_cost_gbp < 0 then
        raise exception 'Estimated cost cannot be negative.';
    end if;

    select *
    into component_row
    from public.vehicle_components
    where id = p_component_id
      and owner_id = auth.uid()
      and component_type <> 'system'
      and lifecycle_status = 'installed';

    if not found then
        raise exception 'Installed component not found.';
    end if;

    insert into public.vehicle_build_plan_items (
        owner_id,
        vehicle_id,
        component_id,
        action,
        status,
        priority,
        estimated_cost_gbp,
        compatibility_status,
        target_date,
        notes
    )
    values (
        auth.uid(),
        component_row.vehicle_id,
        component_row.id,
        'remove',
        p_plan_status,
        p_priority,
        p_estimated_cost_gbp,
        'unknown',
        p_target_date,
        nullif(btrim(p_notes), '')
    )
    returning id into plan_item_id;

    return plan_item_id;
end;
$$;

create or replace function public.complete_build_plan_item(
    p_plan_item_id uuid,
    p_completed_at date,
    p_mileage bigint default null,
    p_actual_cost_gbp numeric default null,
    p_notes text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
    plan_row public.vehicle_build_plan_items%rowtype;
    component_row public.vehicle_components%rowtype;
    event_type text;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    if p_completed_at is null then
        raise exception 'Completion date is required.';
    end if;

    if p_mileage is not null and p_mileage < 0 then
        raise exception 'Mileage cannot be negative.';
    end if;

    if p_actual_cost_gbp is not null and p_actual_cost_gbp < 0 then
        raise exception 'Actual cost cannot be negative.';
    end if;

    select *
    into plan_row
    from public.vehicle_build_plan_items
    where id = p_plan_item_id
      and owner_id = auth.uid()
    for update;

    if not found then
        raise exception 'Build plan item not found.';
    end if;

    if plan_row.status not in ('wishlist', 'planned', 'ready') then
        raise exception 'Build plan item is not active.';
    end if;

    select *
    into component_row
    from public.vehicle_components
    where id = plan_row.component_id
      and owner_id = auth.uid()
      and vehicle_id = plan_row.vehicle_id
    for update;

    if not found then
        raise exception 'Build-plan component not found.';
    end if;

    if plan_row.action = 'install' then
        if component_row.lifecycle_status not in ('planned', 'unknown') then
            raise exception 'Component is not available for installation.';
        end if;

        update public.vehicle_components
        set
            lifecycle_status = 'installed',
            installed_at = p_completed_at,
            installed_mileage = p_mileage,
            removed_at = null,
            removed_mileage = null,
            updated_at = now()
        where id = component_row.id;

        event_type := 'installed';
    elsif plan_row.action = 'remove' then
        if component_row.lifecycle_status <> 'installed' then
            raise exception 'Component is not currently installed.';
        end if;

        update public.vehicle_components
        set
            lifecycle_status = 'removed',
            removed_at = p_completed_at,
            removed_mileage = p_mileage,
            updated_at = now()
        where id = component_row.id;

        event_type := 'removed';
    else
        raise exception 'Unsupported build-plan action.';
    end if;

    update public.vehicle_build_plan_items
    set
        status = 'completed',
        actual_cost_gbp = p_actual_cost_gbp,
        completed_at = p_completed_at::timestamptz,
        notes = coalesce(nullif(btrim(p_notes), ''), notes),
        updated_at = now()
    where id = plan_row.id;

    insert into public.vehicle_component_events (
        owner_id,
        vehicle_id,
        component_id,
        event_type,
        occurred_at,
        mileage,
        notes,
        metadata
    )
    values (
        plan_row.owner_id,
        plan_row.vehicle_id,
        plan_row.component_id,
        event_type,
        p_completed_at::timestamptz,
        p_mileage,
        coalesce(
            nullif(btrim(p_notes), ''),
            case
                when event_type = 'installed'
                then 'Completed through VCG Build Planner.'
                else 'Removal completed through VCG Build Planner.'
            end
        ),
        jsonb_strip_nulls(
            jsonb_build_object(
                'build_plan_item_id', plan_row.id,
                'actual_cost_gbp', p_actual_cost_gbp
            )
        )
    );

    return jsonb_build_object(
        'plan_item_id', plan_row.id,
        'component_id', plan_row.component_id,
        'action', plan_row.action,
        'status', 'completed'
    );
end;
$$;

create or replace function public.cancel_build_plan_item(
    p_plan_item_id uuid,
    p_notes text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
    plan_row public.vehicle_build_plan_items%rowtype;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    select *
    into plan_row
    from public.vehicle_build_plan_items
    where id = p_plan_item_id
      and owner_id = auth.uid()
    for update;

    if not found then
        raise exception 'Build plan item not found.';
    end if;

    if plan_row.status not in ('wishlist', 'planned', 'ready') then
        raise exception 'Build plan item is not active.';
    end if;

    update public.vehicle_build_plan_items
    set
        status = 'cancelled',
        notes = coalesce(nullif(btrim(p_notes), ''), notes),
        updated_at = now()
    where id = plan_row.id;

    if plan_row.action = 'install' then
        update public.vehicle_components
        set
            lifecycle_status = 'cancelled',
            updated_at = now()
        where id = plan_row.component_id
          and lifecycle_status = 'planned';
    end if;

    return jsonb_build_object(
        'plan_item_id', plan_row.id,
        'component_id', plan_row.component_id,
        'status', 'cancelled'
    );
end;
$$;

revoke all on function public.create_build_plan_install(
    bigint,uuid,text,text,text,numeric,boolean,text,text,numeric,text,text,date,text
) from public, anon;
grant execute on function public.create_build_plan_install(
    bigint,uuid,text,text,text,numeric,boolean,text,text,numeric,text,text,date,text
) to authenticated, service_role;

revoke all on function public.create_build_plan_removal(
    uuid,text,text,numeric,date,text
) from public, anon;
grant execute on function public.create_build_plan_removal(
    uuid,text,text,numeric,date,text
) to authenticated, service_role;

revoke all on function public.complete_build_plan_item(
    uuid,date,bigint,numeric,text
) from public, anon;
grant execute on function public.complete_build_plan_item(
    uuid,date,bigint,numeric,text
) to authenticated, service_role;

revoke all on function public.cancel_build_plan_item(
    uuid,text
) from public, anon;
grant execute on function public.cancel_build_plan_item(
    uuid,text
) to authenticated, service_role;


-- Final M16 hardening: an install explicitly marked incompatible
-- cannot be completed until its compatibility state is resolved.
create or replace function public.complete_build_plan_item(
    p_plan_item_id uuid,
    p_completed_at date,
    p_mileage bigint default null,
    p_actual_cost_gbp numeric default null,
    p_notes text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
    plan_row public.vehicle_build_plan_items%rowtype;
    component_row public.vehicle_components%rowtype;
    event_type text;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    if p_completed_at is null then
        raise exception 'Completion date is required.';
    end if;

    if p_mileage is not null and p_mileage < 0 then
        raise exception 'Mileage cannot be negative.';
    end if;

    if p_actual_cost_gbp is not null and p_actual_cost_gbp < 0 then
        raise exception 'Actual cost cannot be negative.';
    end if;

    select *
    into plan_row
    from public.vehicle_build_plan_items
    where id = p_plan_item_id
      and owner_id = auth.uid()
    for update;

    if not found then
        raise exception 'Build plan item not found.';
    end if;

    if plan_row.status not in ('wishlist', 'planned', 'ready') then
        raise exception 'Build plan item is not active.';
    end if;

    if plan_row.action = 'install'
       and plan_row.compatibility_status = 'incompatible' then
        raise exception
            'An install marked incompatible must be resolved before completion.';
    end if;

    select *
    into component_row
    from public.vehicle_components
    where id = plan_row.component_id
      and owner_id = auth.uid()
      and vehicle_id = plan_row.vehicle_id
    for update;

    if not found then
        raise exception 'Build-plan component not found.';
    end if;

    if plan_row.action = 'install' then
        if component_row.lifecycle_status not in ('planned', 'unknown') then
            raise exception 'Component is not available for installation.';
        end if;

        update public.vehicle_components
        set
            lifecycle_status = 'installed',
            installed_at = p_completed_at,
            installed_mileage = p_mileage,
            removed_at = null,
            removed_mileage = null,
            updated_at = now()
        where id = component_row.id;

        event_type := 'installed';
    elsif plan_row.action = 'remove' then
        if component_row.lifecycle_status <> 'installed' then
            raise exception 'Component is not currently installed.';
        end if;

        update public.vehicle_components
        set
            lifecycle_status = 'removed',
            removed_at = p_completed_at,
            removed_mileage = p_mileage,
            updated_at = now()
        where id = component_row.id;

        event_type := 'removed';
    else
        raise exception 'Unsupported build-plan action.';
    end if;

    update public.vehicle_build_plan_items
    set
        status = 'completed',
        actual_cost_gbp = p_actual_cost_gbp,
        completed_at = p_completed_at::timestamptz,
        notes = coalesce(nullif(btrim(p_notes), ''), notes),
        updated_at = now()
    where id = plan_row.id;

    insert into public.vehicle_component_events (
        owner_id,
        vehicle_id,
        component_id,
        event_type,
        occurred_at,
        mileage,
        notes,
        metadata
    )
    values (
        plan_row.owner_id,
        plan_row.vehicle_id,
        plan_row.component_id,
        event_type,
        p_completed_at::timestamptz,
        p_mileage,
        coalesce(
            nullif(btrim(p_notes), ''),
            case
                when event_type = 'installed'
                then 'Completed through VCG Build Planner.'
                else 'Removal completed through VCG Build Planner.'
            end
        ),
        jsonb_strip_nulls(
            jsonb_build_object(
                'build_plan_item_id', plan_row.id,
                'actual_cost_gbp', p_actual_cost_gbp
            )
        )
    );

    return jsonb_build_object(
        'plan_item_id', plan_row.id,
        'component_id', plan_row.component_id,
        'action', plan_row.action,
        'status', 'completed'
    );
end;
$$;
