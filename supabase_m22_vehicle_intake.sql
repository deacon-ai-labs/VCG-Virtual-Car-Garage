-- M22 — Vehicle Intake & Evidence Engine
-- Adds intake identity, private evidence, reviewable candidates,
-- provenance-preserving approval, and guarded intake completion.

alter table public.vehicles
    add column if not exists registration text,
    add column if not exists vin text,
    add column if not exists intake_status text not null default 'complete',
    add column if not exists intake_completed_at timestamptz;

alter table public.vehicles
    drop constraint if exists vehicles_intake_status_check;

alter table public.vehicles
    add constraint vehicles_intake_status_check
    check (
        intake_status in (
            'in_progress',
            'review',
            'complete'
        )
    );

create unique index if not exists vehicles_owner_registration_unique
    on public.vehicles (
        owner_id,
        upper(registration)
    )
    where registration is not null
      and btrim(registration) <> '';

create unique index if not exists vehicles_owner_vin_unique
    on public.vehicles (
        owner_id,
        upper(vin)
    )
    where vin is not null
      and btrim(vin) <> '';

create table if not exists public.vehicle_evidence (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    evidence_type text not null check (
        evidence_type in (
            'photo',
            'invoice',
            'receipt',
            'document',
            'dyno',
            'obd',
            'service',
            'other'
        )
    ),
    title text not null,
    storage_path text,
    original_filename text,
    content_type text,
    source_kind text not null default 'user_upload' check (
        source_kind in (
            'user_upload',
            'manual_entry',
            'provider',
            'community',
            'other'
        )
    ),
    notes text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (
        storage_path is not null
        or source_kind <> 'user_upload'
    )
);

create index if not exists vehicle_evidence_vehicle_idx
    on public.vehicle_evidence(
        vehicle_id,
        created_at desc
    );

create table if not exists public.vehicle_intake_candidates (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    vehicle_id bigint not null references public.vehicles(id) on delete cascade,
    evidence_id uuid references public.vehicle_evidence(id) on delete set null,
    candidate_kind text not null check (
        candidate_kind in (
            'vehicle_identity',
            'component',
            'specification'
        )
    ),
    source_kind text not null default 'user' check (
        source_kind in (
            'user',
            'evidence',
            'provider',
            'ai_extraction',
            'community'
        )
    ),
    source_reference text,
    confidence text not null default 'unknown' check (
        confidence in (
            'verified',
            'high',
            'medium',
            'low',
            'unknown'
        )
    ),
    payload jsonb not null,
    review_status text not null default 'pending' check (
        review_status in (
            'pending',
            'approved',
            'rejected'
        )
    ),
    reviewed_at timestamptz,
    applied_reference text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists vehicle_intake_candidates_vehicle_idx
    on public.vehicle_intake_candidates(
        vehicle_id,
        review_status,
        created_at
    );

alter table public.vehicle_evidence enable row level security;
alter table public.vehicle_intake_candidates enable row level security;

drop policy if exists "Users can view own vehicle evidence"
    on public.vehicle_evidence;
create policy "Users can view own vehicle evidence"
    on public.vehicle_evidence
    for select to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own vehicle evidence"
    on public.vehicle_evidence;
create policy "Users can create own vehicle evidence"
    on public.vehicle_evidence
    for insert to authenticated
    with check (auth.uid() = owner_id);

drop policy if exists "Users can update own vehicle evidence"
    on public.vehicle_evidence;
create policy "Users can update own vehicle evidence"
    on public.vehicle_evidence
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

drop policy if exists "Users can delete own vehicle evidence"
    on public.vehicle_evidence;
create policy "Users can delete own vehicle evidence"
    on public.vehicle_evidence
    for delete to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can view own intake candidates"
    on public.vehicle_intake_candidates;
create policy "Users can view own intake candidates"
    on public.vehicle_intake_candidates
    for select to authenticated
    using (auth.uid() = owner_id);

drop policy if exists "Users can create own intake candidates"
    on public.vehicle_intake_candidates;
create policy "Users can create own intake candidates"
    on public.vehicle_intake_candidates
    for insert to authenticated
    with check (auth.uid() = owner_id);

drop policy if exists "Users can update own intake candidates"
    on public.vehicle_intake_candidates;
create policy "Users can update own intake candidates"
    on public.vehicle_intake_candidates
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

drop policy if exists "Users can delete own intake candidates"
    on public.vehicle_intake_candidates;
create policy "Users can delete own intake candidates"
    on public.vehicle_intake_candidates
    for delete to authenticated
    using (auth.uid() = owner_id);

create or replace function public.validate_vehicle_evidence()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if not exists (
        select 1
        from public.vehicles v
        where v.id = new.vehicle_id
          and v.owner_id = new.owner_id
    ) then
        raise exception 'Evidence vehicle must belong to the same owner.';
    end if;

    return new;
end;
$$;

revoke execute on function public.validate_vehicle_evidence()
from public, anon, authenticated;

drop trigger if exists validate_vehicle_evidence_before_write
    on public.vehicle_evidence;

create trigger validate_vehicle_evidence_before_write
before insert or update of
    owner_id,
    vehicle_id
on public.vehicle_evidence
for each row
execute function public.validate_vehicle_evidence();

create or replace function public.validate_vehicle_intake_candidate()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if not exists (
        select 1
        from public.vehicles v
        where v.id = new.vehicle_id
          and v.owner_id = new.owner_id
    ) then
        raise exception 'Candidate vehicle must belong to the same owner.';
    end if;

    if new.evidence_id is not null
       and not exists (
            select 1
            from public.vehicle_evidence e
            where e.id = new.evidence_id
              and e.vehicle_id = new.vehicle_id
              and e.owner_id = new.owner_id
       ) then
        raise exception 'Candidate evidence must belong to the same vehicle.';
    end if;

    return new;
end;
$$;

revoke execute on function public.validate_vehicle_intake_candidate()
from public, anon, authenticated;

drop trigger if exists validate_vehicle_intake_candidate_before_write
    on public.vehicle_intake_candidates;

create trigger validate_vehicle_intake_candidate_before_write
before insert or update of
    owner_id,
    vehicle_id,
    evidence_id
on public.vehicle_intake_candidates
for each row
execute function public.validate_vehicle_intake_candidate();

create or replace function public.touch_vehicle_intake_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

revoke execute on function public.touch_vehicle_intake_updated_at()
from public, anon, authenticated;

drop trigger if exists touch_vehicle_evidence_updated_at
    on public.vehicle_evidence;
create trigger touch_vehicle_evidence_updated_at
before update on public.vehicle_evidence
for each row
execute function public.touch_vehicle_intake_updated_at();

drop trigger if exists touch_vehicle_intake_candidates_updated_at
    on public.vehicle_intake_candidates;
create trigger touch_vehicle_intake_candidates_updated_at
before update on public.vehicle_intake_candidates
for each row
execute function public.touch_vehicle_intake_updated_at();

insert into storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
values (
    'vehicle-evidence',
    'vehicle-evidence',
    false,
    15728640,
    array[
        'image/jpeg',
        'image/png',
        'image/webp',
        'application/pdf',
        'text/plain',
        'text/csv',
        'application/json'
    ]
)
on conflict (id) do update
set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Users can view own vehicle evidence files"
    on storage.objects;
create policy "Users can view own vehicle evidence files"
    on storage.objects
    for select to authenticated
    using (
        bucket_id = 'vehicle-evidence'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists "Users can upload own vehicle evidence files"
    on storage.objects;
create policy "Users can upload own vehicle evidence files"
    on storage.objects
    for insert to authenticated
    with check (
        bucket_id = 'vehicle-evidence'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists "Users can update own vehicle evidence files"
    on storage.objects;
create policy "Users can update own vehicle evidence files"
    on storage.objects
    for update to authenticated
    using (
        bucket_id = 'vehicle-evidence'
        and (storage.foldername(name))[1] = auth.uid()::text
    )
    with check (
        bucket_id = 'vehicle-evidence'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

drop policy if exists "Users can delete own vehicle evidence files"
    on storage.objects;
create policy "Users can delete own vehicle evidence files"
    on storage.objects
    for delete to authenticated
    using (
        bucket_id = 'vehicle-evidence'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

create or replace function public.approve_vehicle_intake_component_candidate(
    p_candidate_id uuid
)
returns uuid
language plpgsql
security invoker
set search_path = public
as $$
declare
    candidate_row public.vehicle_intake_candidates%rowtype;
    root_component_id uuid;
    new_component_id uuid;
    payload_name text;
    payload_system_key text;
    payload_is_oem boolean;
    payload_quantity numeric;
    payload_weight numeric;
begin
    select *
    into candidate_row
    from public.vehicle_intake_candidates
    where id = p_candidate_id
      and owner_id = auth.uid()
    for update;

    if not found then
        raise exception 'Candidate was not found.';
    end if;

    if candidate_row.review_status <> 'pending' then
        raise exception 'Only pending candidates can be approved.';
    end if;

    if candidate_row.candidate_kind <> 'component' then
        raise exception 'This approval path only supports component candidates.';
    end if;

    payload_name := nullif(
        btrim(candidate_row.payload ->> 'name'),
        ''
    );

    payload_system_key := nullif(
        btrim(candidate_row.payload ->> 'system_key'),
        ''
    );

    if payload_name is null then
        raise exception 'Component candidate requires a name.';
    end if;

    if payload_system_key is null then
        raise exception 'Component candidate requires a vehicle system.';
    end if;

    select id
    into root_component_id
    from public.vehicle_components
    where owner_id = candidate_row.owner_id
      and vehicle_id = candidate_row.vehicle_id
      and component_type = 'system'
      and parent_component_id is null
      and system_key = payload_system_key
    limit 1;

    if root_component_id is null then
        raise exception 'The selected vehicle system does not exist.';
    end if;

    begin
        payload_is_oem := (
            candidate_row.payload ->> 'is_oem'
        )::boolean;
    exception
        when others then
            payload_is_oem := null;
    end;

    begin
        payload_quantity := coalesce(
            nullif(
                candidate_row.payload ->> 'quantity',
                ''
            )::numeric,
            1
        );
    exception
        when others then
            payload_quantity := 1;
    end;

    begin
        payload_weight := nullif(
            candidate_row.payload ->> 'weight_kg',
            ''
        )::numeric;
    exception
        when others then
            payload_weight := null;
    end;

    insert into public.vehicle_components (
        owner_id,
        vehicle_id,
        parent_component_id,
        component_type,
        system_key,
        name,
        position,
        lifecycle_status,
        is_oem,
        manufacturer,
        part_number,
        quantity,
        weight_kg,
        notes,
        metadata
    )
    values (
        candidate_row.owner_id,
        candidate_row.vehicle_id,
        root_component_id,
        'component',
        payload_system_key,
        payload_name,
        nullif(btrim(candidate_row.payload ->> 'position'), ''),
        'installed',
        payload_is_oem,
        nullif(btrim(candidate_row.payload ->> 'manufacturer'), ''),
        nullif(btrim(candidate_row.payload ->> 'part_number'), ''),
        greatest(payload_quantity, 0.000001),
        payload_weight,
        nullif(btrim(candidate_row.payload ->> 'notes'), ''),
        jsonb_strip_nulls(
            jsonb_build_object(
                'intake_candidate_id',
                candidate_row.id,
                'intake_source_kind',
                candidate_row.source_kind,
                'intake_source_reference',
                candidate_row.source_reference,
                'intake_evidence_id',
                candidate_row.evidence_id,
                'intake_confidence',
                candidate_row.confidence
            )
        )
    )
    returning id into new_component_id;

    update public.vehicle_intake_candidates
    set
        review_status = 'approved',
        reviewed_at = now(),
        applied_reference = (
            'vehicle_component:'
            || new_component_id::text
        )
    where id = candidate_row.id;

    return new_component_id;
end;
$$;

revoke execute on function public.approve_vehicle_intake_component_candidate(uuid)
from public, anon;

grant execute on function public.approve_vehicle_intake_component_candidate(uuid)
to authenticated, service_role;

create or replace function public.protect_approved_vehicle_evidence()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if exists (
        select 1
        from public.vehicle_intake_candidates c
        where c.evidence_id = old.id
          and c.review_status = 'approved'
    ) then
        raise exception 'Evidence supporting approved Twin data cannot be deleted.';
    end if;

    return old;
end;
$$;

revoke execute on function public.protect_approved_vehicle_evidence()
from public, anon, authenticated;

drop trigger if exists protect_approved_vehicle_evidence_before_delete
    on public.vehicle_evidence;

create trigger protect_approved_vehicle_evidence_before_delete
before delete on public.vehicle_evidence
for each row
execute function public.protect_approved_vehicle_evidence();

create or replace function public.complete_vehicle_intake(
    p_vehicle_id bigint
)
returns public.vehicles
language plpgsql
security invoker
set search_path = public
as $$
declare
    vehicle_row public.vehicles%rowtype;
begin
    select *
    into vehicle_row
    from public.vehicles
    where id = p_vehicle_id
      and owner_id = auth.uid()
    for update;

    if not found then
        raise exception 'Vehicle was not found.';
    end if;

    if exists (
        select 1
        from public.vehicle_intake_candidates c
        where c.vehicle_id = p_vehicle_id
          and c.owner_id = auth.uid()
          and c.review_status = 'pending'
    ) then
        raise exception 'Review all pending intake candidates before finishing setup.';
    end if;

    update public.vehicles
    set
        intake_status = 'complete',
        intake_completed_at = now()
    where id = p_vehicle_id
    returning *
    into vehicle_row;

    return vehicle_row;
end;
$$;

revoke execute on function public.complete_vehicle_intake(bigint)
from public, anon;

grant execute on function public.complete_vehicle_intake(bigint)
to authenticated, service_role;
