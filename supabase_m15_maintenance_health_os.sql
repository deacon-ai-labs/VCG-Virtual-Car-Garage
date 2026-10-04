-- M15: Maintenance & Vehicle Health OS

alter table public.maintenance_items
    add column if not exists category text not null default 'service',
    add column if not exists priority text not null default 'normal',
    add column if not exists interval_miles bigint,
    add column if not exists interval_months integer,
    add column if not exists estimated_cost_gbp numeric(10, 2),
    add column if not exists last_completed_at date,
    add column if not exists last_completed_mileage bigint;

alter table public.maintenance_items
    drop constraint if exists maintenance_items_category_check;
alter table public.maintenance_items
    add constraint maintenance_items_category_check
    check (category in ('service','fluid','consumable','inspection','repair','advisory'));

alter table public.maintenance_items
    drop constraint if exists maintenance_items_priority_check;
alter table public.maintenance_items
    add constraint maintenance_items_priority_check
    check (priority in ('low','normal','high','critical'));

alter table public.maintenance_items
    drop constraint if exists maintenance_items_interval_miles_check;
alter table public.maintenance_items
    add constraint maintenance_items_interval_miles_check
    check (interval_miles is null or interval_miles > 0);

alter table public.maintenance_items
    drop constraint if exists maintenance_items_interval_months_check;
alter table public.maintenance_items
    add constraint maintenance_items_interval_months_check
    check (interval_months is null or interval_months > 0);

alter table public.maintenance_items
    drop constraint if exists maintenance_items_estimated_cost_check;
alter table public.maintenance_items
    add constraint maintenance_items_estimated_cost_check
    check (estimated_cost_gbp is null or estimated_cost_gbp >= 0);

alter table public.maintenance_items
    drop constraint if exists maintenance_items_last_completed_mileage_check;
alter table public.maintenance_items
    add constraint maintenance_items_last_completed_mileage_check
    check (last_completed_mileage is null or last_completed_mileage >= 0);

create table if not exists public.maintenance_records (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    maintenance_item_id uuid references public.maintenance_items(id) on delete set null,
    twin_component_id uuid references public.vehicle_components(id) on delete set null,
    title text not null,
    category text not null default 'service' check (
        category in ('service','fluid','consumable','inspection','repair','advisory')
    ),
    performed_at date not null,
    performed_mileage bigint check (performed_mileage is null or performed_mileage >= 0),
    cost_gbp numeric(10, 2) check (cost_gbp is null or cost_gbp >= 0),
    provider text,
    notes text,
    evidence_reference text,
    created_at timestamptz not null default now()
);

create index if not exists maintenance_records_vehicle_idx
    on public.maintenance_records(vehicle_id, performed_at desc);
create index if not exists maintenance_records_item_idx
    on public.maintenance_records(maintenance_item_id);
create index if not exists maintenance_records_component_idx
    on public.maintenance_records(twin_component_id);

alter table public.maintenance_records enable row level security;

drop policy if exists "Users can view own maintenance records"
    on public.maintenance_records;
create policy "Users can view own maintenance records"
    on public.maintenance_records
    for select to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own maintenance records"
    on public.maintenance_records;
create policy "Users can create own maintenance records"
    on public.maintenance_records
    for insert to authenticated
    with check (
        auth.uid() = owner_id
        and exists (
            select 1
            from public.vehicles v
            where v.id = maintenance_records.vehicle_id
              and v.owner_id = auth.uid()
        )
        and (
            twin_component_id is null
            or exists (
                select 1
                from public.vehicle_components c
                where c.id = maintenance_records.twin_component_id
                  and c.vehicle_id = maintenance_records.vehicle_id
                  and c.owner_id = auth.uid()
            )
        )
    );

drop policy if exists "Users can update own maintenance records"
    on public.maintenance_records;
drop policy if exists "Users can delete own maintenance records"
    on public.maintenance_records;

revoke update, delete
on table public.maintenance_records
from anon, authenticated;

grant select, insert
on table public.maintenance_records
to authenticated;

grant select, insert, update, delete
on table public.maintenance_records
to service_role;

create or replace function public.complete_maintenance_item(
    p_item_id uuid,
    p_performed_at date,
    p_performed_mileage bigint default null,
    p_cost_gbp numeric default null,
    p_provider text default null,
    p_notes text default null,
    p_evidence_reference text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
    item public.maintenance_items%rowtype;
    record_id uuid;
    is_recurring boolean;
    next_due_mileage bigint;
    next_due_date date;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    if p_performed_at is null then
        raise exception 'Performed date is required.';
    end if;

    if p_performed_mileage is not null and p_performed_mileage < 0 then
        raise exception 'Performed mileage cannot be negative.';
    end if;

    if p_cost_gbp is not null and p_cost_gbp < 0 then
        raise exception 'Cost cannot be negative.';
    end if;

    select *
    into item
    from public.maintenance_items
    where id = p_item_id
      and owner_id = auth.uid()
    for update;

    if not found then
        raise exception 'Maintenance item not found.';
    end if;

    insert into public.maintenance_records (
        owner_id, vehicle_id, maintenance_item_id, twin_component_id,
        title, category, performed_at, performed_mileage, cost_gbp,
        provider, notes, evidence_reference
    )
    values (
        item.owner_id, item.vehicle_id, item.id, item.twin_component_id,
        item.title, item.category, p_performed_at, p_performed_mileage,
        p_cost_gbp, nullif(btrim(p_provider), ''), nullif(btrim(p_notes), ''),
        nullif(btrim(p_evidence_reference), '')
    )
    returning id into record_id;

    if item.twin_component_id is not null then
        insert into public.vehicle_component_events (
            owner_id, vehicle_id, component_id, event_type,
            occurred_at, mileage, notes, metadata
        )
        values (
            item.owner_id,
            item.vehicle_id,
            item.twin_component_id,
            'serviced',
            p_performed_at::timestamptz,
            p_performed_mileage,
            item.title || case
                when nullif(btrim(p_notes), '') is not null
                then ': ' || btrim(p_notes)
                else ''
            end,
            jsonb_strip_nulls(
                jsonb_build_object(
                    'maintenance_record_id', record_id,
                    'cost_gbp', p_cost_gbp,
                    'provider', nullif(btrim(p_provider), '')
                )
            )
        );
    end if;

    is_recurring := (
        item.interval_miles is not null
        or item.interval_months is not null
    );

    if item.interval_miles is not null then
        if p_performed_mileage is null then
            raise exception
                'Performed mileage is required for mileage-based recurring maintenance.';
        end if;
        next_due_mileage := p_performed_mileage + item.interval_miles;
    else
        next_due_mileage := null;
    end if;

    if item.interval_months is not null then
        next_due_date := (
            p_performed_at
            + make_interval(months => item.interval_months)
        )::date;
    else
        next_due_date := null;
    end if;

    update public.maintenance_items
    set
        status = case when is_recurring then 'pending' else 'completed' end,
        due_mileage = case when is_recurring then next_due_mileage else due_mileage end,
        due_date = case when is_recurring then next_due_date else due_date end,
        completed_at = case
            when is_recurring then null
            else p_performed_at::timestamptz
        end,
        last_completed_at = p_performed_at,
        last_completed_mileage = p_performed_mileage,
        updated_at = now()
    where id = item.id;

    return jsonb_build_object(
        'maintenance_record_id', record_id,
        'recurring', is_recurring,
        'next_due_mileage', next_due_mileage,
        'next_due_date', next_due_date
    );
end;
$$;

revoke all on function public.complete_maintenance_item(
    uuid,date,bigint,numeric,text,text,text
) from public, anon;
grant execute on function public.complete_maintenance_item(
    uuid,date,bigint,numeric,text,text,text
) to authenticated, service_role;

create or replace function public.record_maintenance_history(
    p_vehicle_id bigint,
    p_title text,
    p_category text,
    p_performed_at date,
    p_performed_mileage bigint default null,
    p_cost_gbp numeric default null,
    p_provider text default null,
    p_notes text default null,
    p_evidence_reference text default null,
    p_twin_component_id uuid default null
)
returns uuid
language plpgsql
security invoker
set search_path = public
as $$
declare
    record_id uuid;
    clean_title text;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    clean_title := nullif(btrim(p_title), '');

    if clean_title is null then
        raise exception 'Maintenance title is required.';
    end if;

    if p_category not in (
        'service','fluid','consumable','inspection','repair','advisory'
    ) then
        raise exception 'Invalid maintenance category.';
    end if;

    if not exists (
        select 1
        from public.vehicles v
        where v.id = p_vehicle_id
          and v.owner_id = auth.uid()
    ) then
        raise exception 'Vehicle not found.';
    end if;

    if p_twin_component_id is not null
       and not exists (
            select 1
            from public.vehicle_components c
            where c.id = p_twin_component_id
              and c.vehicle_id = p_vehicle_id
              and c.owner_id = auth.uid()
       ) then
        raise exception 'Component does not belong to this vehicle.';
    end if;

    if p_performed_mileage is not null and p_performed_mileage < 0 then
        raise exception 'Performed mileage cannot be negative.';
    end if;

    if p_cost_gbp is not null and p_cost_gbp < 0 then
        raise exception 'Cost cannot be negative.';
    end if;

    insert into public.maintenance_records (
        owner_id, vehicle_id, twin_component_id, title, category,
        performed_at, performed_mileage, cost_gbp, provider,
        notes, evidence_reference
    )
    values (
        auth.uid(), p_vehicle_id, p_twin_component_id, clean_title,
        p_category, p_performed_at, p_performed_mileage, p_cost_gbp,
        nullif(btrim(p_provider), ''), nullif(btrim(p_notes), ''),
        nullif(btrim(p_evidence_reference), '')
    )
    returning id into record_id;

    if p_twin_component_id is not null then
        insert into public.vehicle_component_events (
            owner_id, vehicle_id, component_id, event_type,
            occurred_at, mileage, notes, metadata
        )
        values (
            auth.uid(),
            p_vehicle_id,
            p_twin_component_id,
            'serviced',
            p_performed_at::timestamptz,
            p_performed_mileage,
            clean_title || case
                when nullif(btrim(p_notes), '') is not null
                then ': ' || btrim(p_notes)
                else ''
            end,
            jsonb_strip_nulls(
                jsonb_build_object(
                    'maintenance_record_id', record_id,
                    'cost_gbp', p_cost_gbp,
                    'provider', nullif(btrim(p_provider), '')
                )
            )
        );
    end if;

    return record_id;
end;
$$;

revoke all on function public.record_maintenance_history(
    bigint,text,text,date,bigint,numeric,text,text,text,uuid
) from public, anon;
grant execute on function public.record_maintenance_history(
    bigint,text,text,date,bigint,numeric,text,text,text,uuid
) to authenticated, service_role;


-- Final M15 refinement: preserve component lifecycle semantics by mapping
-- inspection -> inspected, repair -> repaired, and other maintenance -> serviced.

create or replace function public.complete_maintenance_item(
    p_item_id uuid,
    p_performed_at date,
    p_performed_mileage bigint default null,
    p_cost_gbp numeric default null,
    p_provider text default null,
    p_notes text default null,
    p_evidence_reference text default null
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
    item public.maintenance_items%rowtype;
    record_id uuid;
    is_recurring boolean;
    next_due_mileage bigint;
    next_due_date date;
    component_event_type text;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    if p_performed_at is null then
        raise exception 'Performed date is required.';
    end if;

    if p_performed_mileage is not null and p_performed_mileage < 0 then
        raise exception 'Performed mileage cannot be negative.';
    end if;

    if p_cost_gbp is not null and p_cost_gbp < 0 then
        raise exception 'Cost cannot be negative.';
    end if;

    select *
    into item
    from public.maintenance_items
    where id = p_item_id
      and owner_id = auth.uid()
    for update;

    if not found then
        raise exception 'Maintenance item not found.';
    end if;

    insert into public.maintenance_records (
        owner_id, vehicle_id, maintenance_item_id, twin_component_id,
        title, category, performed_at, performed_mileage, cost_gbp,
        provider, notes, evidence_reference
    )
    values (
        item.owner_id, item.vehicle_id, item.id, item.twin_component_id,
        item.title, item.category, p_performed_at, p_performed_mileage,
        p_cost_gbp, nullif(btrim(p_provider), ''), nullif(btrim(p_notes), ''),
        nullif(btrim(p_evidence_reference), '')
    )
    returning id into record_id;

    component_event_type := case item.category
        when 'inspection' then 'inspected'
        when 'repair' then 'repaired'
        else 'serviced'
    end;

    if item.twin_component_id is not null then
        insert into public.vehicle_component_events (
            owner_id, vehicle_id, component_id, event_type,
            occurred_at, mileage, notes, metadata
        )
        values (
            item.owner_id,
            item.vehicle_id,
            item.twin_component_id,
            component_event_type,
            p_performed_at::timestamptz,
            p_performed_mileage,
            item.title || case
                when nullif(btrim(p_notes), '') is not null
                then ': ' || btrim(p_notes)
                else ''
            end,
            jsonb_strip_nulls(
                jsonb_build_object(
                    'maintenance_record_id', record_id,
                    'cost_gbp', p_cost_gbp,
                    'provider', nullif(btrim(p_provider), '')
                )
            )
        );
    end if;

    is_recurring := (
        item.interval_miles is not null
        or item.interval_months is not null
    );

    if item.interval_miles is not null then
        if p_performed_mileage is null then
            raise exception
                'Performed mileage is required for mileage-based recurring maintenance.';
        end if;
        next_due_mileage := p_performed_mileage + item.interval_miles;
    else
        next_due_mileage := null;
    end if;

    if item.interval_months is not null then
        next_due_date := (
            p_performed_at
            + make_interval(months => item.interval_months)
        )::date;
    else
        next_due_date := null;
    end if;

    update public.maintenance_items
    set
        status = case when is_recurring then 'pending' else 'completed' end,
        due_mileage = case when is_recurring then next_due_mileage else due_mileage end,
        due_date = case when is_recurring then next_due_date else due_date end,
        completed_at = case
            when is_recurring then null
            else p_performed_at::timestamptz
        end,
        last_completed_at = p_performed_at,
        last_completed_mileage = p_performed_mileage,
        updated_at = now()
    where id = item.id;

    return jsonb_build_object(
        'maintenance_record_id', record_id,
        'recurring', is_recurring,
        'next_due_mileage', next_due_mileage,
        'next_due_date', next_due_date
    );
end;
$$;

create or replace function public.record_maintenance_history(
    p_vehicle_id bigint,
    p_title text,
    p_category text,
    p_performed_at date,
    p_performed_mileage bigint default null,
    p_cost_gbp numeric default null,
    p_provider text default null,
    p_notes text default null,
    p_evidence_reference text default null,
    p_twin_component_id uuid default null
)
returns uuid
language plpgsql
security invoker
set search_path = public
as $$
declare
    record_id uuid;
    clean_title text;
    component_event_type text;
begin
    if auth.uid() is null then
        raise exception 'Authentication required.';
    end if;

    clean_title := nullif(btrim(p_title), '');

    if clean_title is null then
        raise exception 'Maintenance title is required.';
    end if;

    if p_category not in (
        'service','fluid','consumable','inspection','repair','advisory'
    ) then
        raise exception 'Invalid maintenance category.';
    end if;

    if not exists (
        select 1
        from public.vehicles v
        where v.id = p_vehicle_id
          and v.owner_id = auth.uid()
    ) then
        raise exception 'Vehicle not found.';
    end if;

    if p_twin_component_id is not null
       and not exists (
            select 1
            from public.vehicle_components c
            where c.id = p_twin_component_id
              and c.vehicle_id = p_vehicle_id
              and c.owner_id = auth.uid()
       ) then
        raise exception 'Component does not belong to this vehicle.';
    end if;

    if p_performed_mileage is not null and p_performed_mileage < 0 then
        raise exception 'Performed mileage cannot be negative.';
    end if;

    if p_cost_gbp is not null and p_cost_gbp < 0 then
        raise exception 'Cost cannot be negative.';
    end if;

    insert into public.maintenance_records (
        owner_id, vehicle_id, twin_component_id, title, category,
        performed_at, performed_mileage, cost_gbp, provider,
        notes, evidence_reference
    )
    values (
        auth.uid(), p_vehicle_id, p_twin_component_id, clean_title,
        p_category, p_performed_at, p_performed_mileage, p_cost_gbp,
        nullif(btrim(p_provider), ''), nullif(btrim(p_notes), ''),
        nullif(btrim(p_evidence_reference), '')
    )
    returning id into record_id;

    component_event_type := case p_category
        when 'inspection' then 'inspected'
        when 'repair' then 'repaired'
        else 'serviced'
    end;

    if p_twin_component_id is not null then
        insert into public.vehicle_component_events (
            owner_id, vehicle_id, component_id, event_type,
            occurred_at, mileage, notes, metadata
        )
        values (
            auth.uid(),
            p_vehicle_id,
            p_twin_component_id,
            component_event_type,
            p_performed_at::timestamptz,
            p_performed_mileage,
            clean_title || case
                when nullif(btrim(p_notes), '') is not null
                then ': ' || btrim(p_notes)
                else ''
            end,
            jsonb_strip_nulls(
                jsonb_build_object(
                    'maintenance_record_id', record_id,
                    'cost_gbp', p_cost_gbp,
                    'provider', nullif(btrim(p_provider), '')
                )
            )
        );
    end if;

    return record_id;
end;
$$;
