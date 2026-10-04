-- M13: Vehicle Digital Twin foundation

create table if not exists public.vehicle_components (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    parent_component_id uuid references public.vehicle_components(id) on delete cascade,
    component_type text not null check (
        component_type in ('system', 'assembly', 'component', 'consumable')
    ),
    system_key text not null,
    name text not null,
    position text,
    lifecycle_status text not null default 'installed' check (
        lifecycle_status in ('installed', 'planned', 'removed', 'unknown')
    ),
    is_oem boolean,
    manufacturer text,
    part_number text,
    quantity numeric(10, 3) not null default 1 check (quantity > 0),
    weight_kg numeric(10, 3) check (weight_kg is null or weight_kg >= 0),
    installed_at date,
    installed_mileage bigint check (installed_mileage is null or installed_mileage >= 0),
    removed_at date,
    removed_mileage bigint check (removed_mileage is null or removed_mileage >= 0),
    notes text,
    metadata jsonb not null default '{}'::jsonb,
    sort_order integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists vehicle_components_vehicle_idx
    on public.vehicle_components(vehicle_id);
create index if not exists vehicle_components_parent_idx
    on public.vehicle_components(parent_component_id);
create index if not exists vehicle_components_system_idx
    on public.vehicle_components(vehicle_id, system_key);
create index if not exists vehicle_components_status_idx
    on public.vehicle_components(vehicle_id, lifecycle_status);
create unique index if not exists vehicle_components_root_system_unique
    on public.vehicle_components(vehicle_id, system_key)
    where parent_component_id is null and component_type = 'system';

create table if not exists public.vehicle_specifications (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    component_id uuid references public.vehicle_components(id) on delete cascade,
    spec_key text not null,
    label text not null,
    value_text text,
    value_numeric numeric,
    unit text,
    source_kind text not null default 'unknown' check (
        source_kind in (
            'oem_document',
            'aftermarket_document',
            'measurement',
            'user',
            'derived',
            'unknown'
        )
    ),
    source_reference text,
    confidence text not null default 'unknown' check (
        confidence in ('verified', 'high', 'medium', 'low', 'unknown')
    ),
    is_current boolean not null default true,
    verified_at timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (value_text is not null or value_numeric is not null)
);

create index if not exists vehicle_specifications_vehicle_idx
    on public.vehicle_specifications(vehicle_id);
create index if not exists vehicle_specifications_component_idx
    on public.vehicle_specifications(component_id);
create index if not exists vehicle_specifications_key_idx
    on public.vehicle_specifications(vehicle_id, spec_key);

create table if not exists public.vehicle_component_events (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    component_id uuid not null references public.vehicle_components(id) on delete cascade,
    event_type text not null check (
        event_type in (
            'installed',
            'removed',
            'replaced',
            'serviced',
            'inspected',
            'repaired',
            'cleaned',
            'lubricated',
            'measured',
            'note'
        )
    ),
    occurred_at timestamptz not null default now(),
    mileage bigint check (mileage is null or mileage >= 0),
    notes text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists vehicle_component_events_vehicle_idx
    on public.vehicle_component_events(vehicle_id, occurred_at desc);
create index if not exists vehicle_component_events_component_idx
    on public.vehicle_component_events(component_id, occurred_at desc);

alter table public.maintenance_items
    add column if not exists twin_component_id uuid
    references public.vehicle_components(id)
    on delete set null;

create index if not exists maintenance_items_twin_component_idx
    on public.maintenance_items(twin_component_id);

alter table public.vehicle_components enable row level security;
alter table public.vehicle_specifications enable row level security;
alter table public.vehicle_component_events enable row level security;

create policy "Users can view own vehicle components"
    on public.vehicle_components
    for select to authenticated
    using (auth.uid() = owner_id);

create policy "Users can create own vehicle components"
    on public.vehicle_components
    for insert to authenticated
    with check (
        auth.uid() = owner_id
        and exists (
            select 1 from public.vehicles v
            where v.id = vehicle_components.vehicle_id
              and v.owner_id = auth.uid()
        )
    );

create policy "Users can update own vehicle components"
    on public.vehicle_components
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (
        auth.uid() = owner_id
        and exists (
            select 1 from public.vehicles v
            where v.id = vehicle_components.vehicle_id
              and v.owner_id = auth.uid()
        )
    );

create policy "Users can delete own vehicle components"
    on public.vehicle_components
    for delete to authenticated
    using (auth.uid() = owner_id);

create policy "Users can view own vehicle specifications"
    on public.vehicle_specifications
    for select to authenticated
    using (auth.uid() = owner_id);

create policy "Users can create own vehicle specifications"
    on public.vehicle_specifications
    for insert to authenticated
    with check (
        auth.uid() = owner_id
        and exists (
            select 1 from public.vehicles v
            where v.id = vehicle_specifications.vehicle_id
              and v.owner_id = auth.uid()
        )
        and (
            component_id is null
            or exists (
                select 1 from public.vehicle_components c
                where c.id = vehicle_specifications.component_id
                  and c.vehicle_id = vehicle_specifications.vehicle_id
                  and c.owner_id = auth.uid()
            )
        )
    );

create policy "Users can update own vehicle specifications"
    on public.vehicle_specifications
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (
        auth.uid() = owner_id
        and exists (
            select 1 from public.vehicles v
            where v.id = vehicle_specifications.vehicle_id
              and v.owner_id = auth.uid()
        )
        and (
            component_id is null
            or exists (
                select 1 from public.vehicle_components c
                where c.id = vehicle_specifications.component_id
                  and c.vehicle_id = vehicle_specifications.vehicle_id
                  and c.owner_id = auth.uid()
            )
        )
    );

create policy "Users can delete own vehicle specifications"
    on public.vehicle_specifications
    for delete to authenticated
    using (auth.uid() = owner_id);

create policy "Users can view own vehicle component events"
    on public.vehicle_component_events
    for select to authenticated
    using (auth.uid() = owner_id);

create policy "Users can create own vehicle component events"
    on public.vehicle_component_events
    for insert to authenticated
    with check (
        auth.uid() = owner_id
        and exists (
            select 1 from public.vehicle_components c
            where c.id = vehicle_component_events.component_id
              and c.vehicle_id = vehicle_component_events.vehicle_id
              and c.owner_id = auth.uid()
        )
    );

create policy "Users can update own vehicle component events"
    on public.vehicle_component_events
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (
        auth.uid() = owner_id
        and exists (
            select 1 from public.vehicle_components c
            where c.id = vehicle_component_events.component_id
              and c.vehicle_id = vehicle_component_events.vehicle_id
              and c.owner_id = auth.uid()
        )
    );

create policy "Users can delete own vehicle component events"
    on public.vehicle_component_events
    for delete to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own maintenance items"
    on public.maintenance_items;
create policy "Users can create own maintenance items"
    on public.maintenance_items
    for insert to authenticated
    with check (
        auth.uid() = owner_id
        and exists (
            select 1 from public.vehicles v
            where v.id = maintenance_items.vehicle_id
              and v.owner_id = auth.uid()
        )
        and (
            twin_component_id is null
            or exists (
                select 1 from public.vehicle_components c
                where c.id = maintenance_items.twin_component_id
                  and c.vehicle_id = maintenance_items.vehicle_id
                  and c.owner_id = auth.uid()
            )
        )
    );

drop policy if exists "Users can update own maintenance items"
    on public.maintenance_items;
create policy "Users can update own maintenance items"
    on public.maintenance_items
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (
        auth.uid() = owner_id
        and exists (
            select 1 from public.vehicles v
            where v.id = maintenance_items.vehicle_id
              and v.owner_id = auth.uid()
        )
        and (
            twin_component_id is null
            or exists (
                select 1 from public.vehicle_components c
                where c.id = maintenance_items.twin_component_id
                  and c.vehicle_id = maintenance_items.vehicle_id
                  and c.owner_id = auth.uid()
            )
        )
    );

create or replace function public.seed_vehicle_digital_twin_systems()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.vehicle_components (
        owner_id, vehicle_id, component_type, system_key,
        name, lifecycle_status, sort_order
    )
    values
        (new.owner_id, new.id, 'system', 'engine', 'Engine', 'installed', 10),
        (new.owner_id, new.id, 'system', 'transmission_driveline', 'Transmission & Driveline', 'installed', 20),
        (new.owner_id, new.id, 'system', 'intake_fuel', 'Intake & Fuel', 'installed', 30),
        (new.owner_id, new.id, 'system', 'cooling', 'Cooling', 'installed', 40),
        (new.owner_id, new.id, 'system', 'exhaust', 'Exhaust', 'installed', 50),
        (new.owner_id, new.id, 'system', 'brakes', 'Brakes', 'installed', 60),
        (new.owner_id, new.id, 'system', 'suspension_steering', 'Suspension & Steering', 'installed', 70),
        (new.owner_id, new.id, 'system', 'wheels_tyres', 'Wheels & Tyres', 'installed', 80),
        (new.owner_id, new.id, 'system', 'electrical', 'Electrical', 'installed', 90),
        (new.owner_id, new.id, 'system', 'body_exterior', 'Body & Exterior', 'installed', 100),
        (new.owner_id, new.id, 'system', 'interior_safety', 'Interior & Safety', 'installed', 110),
        (new.owner_id, new.id, 'system', 'fluids_consumables', 'Fluids & Consumables', 'installed', 120)
    on conflict do nothing;

    return new;
end;
$$;

drop trigger if exists seed_vehicle_digital_twin_systems_after_insert
    on public.vehicles;

create trigger seed_vehicle_digital_twin_systems_after_insert
after insert on public.vehicles
for each row
execute function public.seed_vehicle_digital_twin_systems();

insert into public.vehicle_components (
    owner_id, vehicle_id, component_type, system_key,
    name, lifecycle_status, sort_order
)
select
    v.owner_id, v.id, 'system',
    systems.system_key, systems.name, 'installed', systems.sort_order
from public.vehicles v
cross join (
    values
        ('engine', 'Engine', 10),
        ('transmission_driveline', 'Transmission & Driveline', 20),
        ('intake_fuel', 'Intake & Fuel', 30),
        ('cooling', 'Cooling', 40),
        ('exhaust', 'Exhaust', 50),
        ('brakes', 'Brakes', 60),
        ('suspension_steering', 'Suspension & Steering', 70),
        ('wheels_tyres', 'Wheels & Tyres', 80),
        ('electrical', 'Electrical', 90),
        ('body_exterior', 'Body & Exterior', 100),
        ('interior_safety', 'Interior & Safety', 110),
        ('fluids_consumables', 'Fluids & Consumables', 120)
) as systems(system_key, name, sort_order)
on conflict do nothing;
