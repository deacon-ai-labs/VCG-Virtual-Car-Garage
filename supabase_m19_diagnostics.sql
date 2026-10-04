-- M19 — Diagnostic Investigation Workspace
-- Structured symptom -> hypothesis -> check/finding -> resolution records.

create table if not exists public.diagnostic_cases (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    title text not null,
    symptom_description text not null,
    status text not null default 'open' check (
        status in ('open', 'monitoring', 'resolved', 'closed')
    ),
    priority text not null default 'normal' check (
        priority in ('low', 'normal', 'high', 'critical')
    ),
    drive_risk text not null default 'unknown' check (
        drive_risk in (
            'unknown',
            'safe_with_caution',
            'avoid_driving',
            'do_not_drive'
        )
    ),
    onset_date date,
    onset_mileage bigint check (
        onset_mileage is null
        or onset_mileage >= 0
    ),
    operating_conditions text,
    resolution_summary text,
    resolved_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists diagnostic_cases_vehicle_idx
    on public.diagnostic_cases(
        vehicle_id,
        status,
        updated_at desc
    );

create table if not exists public.diagnostic_hypotheses (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    case_id uuid not null references public.diagnostic_cases(id) on delete cascade,
    component_id uuid references public.vehicle_components(id) on delete set null,
    title text not null,
    rationale text,
    status text not null default 'possible' check (
        status in (
            'possible',
            'leading',
            'weakened',
            'ruled_out',
            'confirmed'
        )
    ),
    source_kind text not null default 'user' check (
        source_kind in (
            'user',
            'garage_ai',
            'mechanic',
            'test_result',
            'other'
        )
    ),
    sort_order integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists diagnostic_hypotheses_case_idx
    on public.diagnostic_hypotheses(
        case_id,
        sort_order,
        created_at
    );

create table if not exists public.diagnostic_checks (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    case_id uuid not null references public.diagnostic_cases(id) on delete cascade,
    hypothesis_id uuid references public.diagnostic_hypotheses(id) on delete set null,
    component_id uuid references public.vehicle_components(id) on delete set null,
    title text not null,
    check_type text not null default 'inspection' check (
        check_type in (
            'observation',
            'inspection',
            'measurement',
            'scan',
            'mechanical_test',
            'test_drive',
            'other'
        )
    ),
    procedure text,
    safety_notes text,
    status text not null default 'planned' check (
        status in ('planned', 'completed', 'skipped')
    ),
    outcome text check (
        outcome is null
        or outcome in (
            'supports',
            'weakens',
            'neutral',
            'inconclusive',
            'not_applicable'
        )
    ),
    finding text,
    performed_at timestamptz,
    performed_mileage bigint check (
        performed_mileage is null
        or performed_mileage >= 0
    ),
    sort_order integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (
        status <> 'completed'
        or performed_at is not null
    ),
    check (
        status <> 'completed'
        or nullif(btrim(finding), '') is not null
    ),
    constraint diagnostic_checks_completed_outcome_check
    check (
        status <> 'completed'
        or outcome is not null
    )
);

create index if not exists diagnostic_checks_case_idx
    on public.diagnostic_checks(
        case_id,
        status,
        sort_order,
        created_at
    );

create index if not exists diagnostic_checks_hypothesis_idx
    on public.diagnostic_checks(
        hypothesis_id
    );

alter table public.diagnostic_cases enable row level security;
alter table public.diagnostic_hypotheses enable row level security;
alter table public.diagnostic_checks enable row level security;

drop policy if exists "Users can view own diagnostic cases"
    on public.diagnostic_cases;
create policy "Users can view own diagnostic cases"
    on public.diagnostic_cases
    for select to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own diagnostic cases"
    on public.diagnostic_cases;
create policy "Users can create own diagnostic cases"
    on public.diagnostic_cases
    for insert to authenticated
    with check (
        auth.uid() = owner_id
        and exists (
            select 1
            from public.vehicles v
            where v.id = diagnostic_cases.vehicle_id
              and v.owner_id = auth.uid()
        )
    );

drop policy if exists "Users can update own diagnostic cases"
    on public.diagnostic_cases;
create policy "Users can update own diagnostic cases"
    on public.diagnostic_cases
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (
        auth.uid() = owner_id
        and exists (
            select 1
            from public.vehicles v
            where v.id = diagnostic_cases.vehicle_id
              and v.owner_id = auth.uid()
        )
    );

drop policy if exists "Users can delete own diagnostic cases"
    on public.diagnostic_cases;
create policy "Users can delete own diagnostic cases"
    on public.diagnostic_cases
    for delete to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can view own diagnostic hypotheses"
    on public.diagnostic_hypotheses;
create policy "Users can view own diagnostic hypotheses"
    on public.diagnostic_hypotheses
    for select to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own diagnostic hypotheses"
    on public.diagnostic_hypotheses;
create policy "Users can create own diagnostic hypotheses"
    on public.diagnostic_hypotheses
    for insert to authenticated
    with check (auth.uid() = owner_id);

drop policy if exists "Users can update own diagnostic hypotheses"
    on public.diagnostic_hypotheses;
create policy "Users can update own diagnostic hypotheses"
    on public.diagnostic_hypotheses
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

drop policy if exists "Users can delete own diagnostic hypotheses"
    on public.diagnostic_hypotheses;
create policy "Users can delete own diagnostic hypotheses"
    on public.diagnostic_hypotheses
    for delete to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can view own diagnostic checks"
    on public.diagnostic_checks;
create policy "Users can view own diagnostic checks"
    on public.diagnostic_checks
    for select to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own diagnostic checks"
    on public.diagnostic_checks;
create policy "Users can create own diagnostic checks"
    on public.diagnostic_checks
    for insert to authenticated
    with check (auth.uid() = owner_id);

drop policy if exists "Users can update own diagnostic checks"
    on public.diagnostic_checks;
create policy "Users can update own diagnostic checks"
    on public.diagnostic_checks
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

drop policy if exists "Users can delete own diagnostic checks"
    on public.diagnostic_checks;
create policy "Users can delete own diagnostic checks"
    on public.diagnostic_checks
    for delete to authenticated
    using (auth.uid() = owner_id);

create or replace function public.validate_diagnostic_hypothesis()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    case_row public.diagnostic_cases%rowtype;
begin
    select *
    into case_row
    from public.diagnostic_cases
    where id = new.case_id;

    if not found then
        raise exception 'Diagnostic case does not exist.';
    end if;

    if case_row.owner_id <> new.owner_id
       or case_row.vehicle_id <> new.vehicle_id then
        raise exception 'Hypothesis must belong to the same owner and vehicle as its case.';
    end if;

    if new.component_id is not null
       and not exists (
            select 1
            from public.vehicle_components c
            where c.id = new.component_id
              and c.owner_id = new.owner_id
              and c.vehicle_id = new.vehicle_id
       ) then
        raise exception 'Hypothesis component must belong to the same vehicle.';
    end if;

    return new;
end;
$$;

revoke execute on function public.validate_diagnostic_hypothesis()
from public, anon, authenticated;

drop trigger if exists validate_diagnostic_hypothesis_before_write
    on public.diagnostic_hypotheses;
create trigger validate_diagnostic_hypothesis_before_write
before insert or update of
    owner_id,
    vehicle_id,
    case_id,
    component_id
on public.diagnostic_hypotheses
for each row
execute function public.validate_diagnostic_hypothesis();

create or replace function public.validate_diagnostic_check()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    case_row public.diagnostic_cases%rowtype;
begin
    select *
    into case_row
    from public.diagnostic_cases
    where id = new.case_id;

    if not found then
        raise exception 'Diagnostic case does not exist.';
    end if;

    if case_row.owner_id <> new.owner_id
       or case_row.vehicle_id <> new.vehicle_id then
        raise exception 'Diagnostic check must belong to the same owner and vehicle as its case.';
    end if;

    if new.hypothesis_id is not null
       and not exists (
            select 1
            from public.diagnostic_hypotheses h
            where h.id = new.hypothesis_id
              and h.case_id = new.case_id
              and h.owner_id = new.owner_id
              and h.vehicle_id = new.vehicle_id
       ) then
        raise exception 'Diagnostic check hypothesis must belong to the same case.';
    end if;

    if new.component_id is not null
       and not exists (
            select 1
            from public.vehicle_components c
            where c.id = new.component_id
              and c.owner_id = new.owner_id
              and c.vehicle_id = new.vehicle_id
       ) then
        raise exception 'Diagnostic check component must belong to the same vehicle.';
    end if;

    return new;
end;
$$;

revoke execute on function public.validate_diagnostic_check()
from public, anon, authenticated;

drop trigger if exists validate_diagnostic_check_before_write
    on public.diagnostic_checks;
create trigger validate_diagnostic_check_before_write
before insert or update of
    owner_id,
    vehicle_id,
    case_id,
    hypothesis_id,
    component_id
on public.diagnostic_checks
for each row
execute function public.validate_diagnostic_check();

create or replace function public.touch_diagnostic_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

revoke execute on function public.touch_diagnostic_updated_at()
from public, anon, authenticated;

drop trigger if exists touch_diagnostic_cases_updated_at
    on public.diagnostic_cases;
create trigger touch_diagnostic_cases_updated_at
before update on public.diagnostic_cases
for each row
execute function public.touch_diagnostic_updated_at();

drop trigger if exists touch_diagnostic_hypotheses_updated_at
    on public.diagnostic_hypotheses;
create trigger touch_diagnostic_hypotheses_updated_at
before update on public.diagnostic_hypotheses
for each row
execute function public.touch_diagnostic_updated_at();

drop trigger if exists touch_diagnostic_checks_updated_at
    on public.diagnostic_checks;
create trigger touch_diagnostic_checks_updated_at
before update on public.diagnostic_checks
for each row
execute function public.touch_diagnostic_updated_at();
