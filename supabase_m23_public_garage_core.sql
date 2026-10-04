-- M23 — Public Garage core schema and owner-only settings.

create table if not exists public.public_garages (
    owner_id uuid primary key references auth.users(id) on delete cascade,
    slug text not null unique,
    display_name text not null,
    bio text,
    theme text not null default 'midnight' check (
        theme in ('midnight','concrete','studio','neon')
    ),
    is_public boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint public_garages_slug_format check (
        slug ~ '^[a-z0-9][a-z0-9-]{2,31}$'
    )
);

create table if not exists public.public_vehicle_profiles (
    vehicle_id bigint primary key references public.vehicles(id) on delete cascade,
    owner_id uuid not null references auth.users(id) on delete cascade,
    is_public boolean not null default false,
    show_photo boolean not null default true,
    show_year boolean not null default true,
    show_manufacturer boolean not null default true,
    show_model boolean not null default true,
    show_engine boolean not null default false,
    show_mileage boolean not null default false,
    show_modifications boolean not null default false,
    show_specifications boolean not null default false,
    public_bio text,
    public_photo_path text,
    sort_order integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists public_vehicle_profiles_owner_idx
    on public.public_vehicle_profiles(owner_id, sort_order, vehicle_id);

alter table public.public_garages enable row level security;
alter table public.public_vehicle_profiles enable row level security;

drop policy if exists "Users can view own public garage settings"
    on public.public_garages;
create policy "Users can view own public garage settings"
    on public.public_garages
    for select to authenticated using (auth.uid() = owner_id);

drop policy if exists "Users can create own public garage settings"
    on public.public_garages;
create policy "Users can create own public garage settings"
    on public.public_garages
    for insert to authenticated with check (auth.uid() = owner_id);

drop policy if exists "Users can update own public garage settings"
    on public.public_garages;
create policy "Users can update own public garage settings"
    on public.public_garages
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

drop policy if exists "Users can delete own public garage settings"
    on public.public_garages;
create policy "Users can delete own public garage settings"
    on public.public_garages
    for delete to authenticated using (auth.uid() = owner_id);

drop policy if exists "Users can view own public vehicle settings"
    on public.public_vehicle_profiles;
create policy "Users can view own public vehicle settings"
    on public.public_vehicle_profiles
    for select to authenticated using (auth.uid() = owner_id);

drop policy if exists "Users can create own public vehicle settings"
    on public.public_vehicle_profiles;
create policy "Users can create own public vehicle settings"
    on public.public_vehicle_profiles
    for insert to authenticated with check (auth.uid() = owner_id);

drop policy if exists "Users can update own public vehicle settings"
    on public.public_vehicle_profiles;
create policy "Users can update own public vehicle settings"
    on public.public_vehicle_profiles
    for update to authenticated
    using (auth.uid() = owner_id)
    with check (auth.uid() = owner_id);

drop policy if exists "Users can delete own public vehicle settings"
    on public.public_vehicle_profiles;
create policy "Users can delete own public vehicle settings"
    on public.public_vehicle_profiles
    for delete to authenticated using (auth.uid() = owner_id);

create or replace function public.touch_public_garage_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

revoke execute on function public.touch_public_garage_updated_at()
from public, anon, authenticated;

drop trigger if exists touch_public_garages_updated_at
    on public.public_garages;
create trigger touch_public_garages_updated_at
before update on public.public_garages
for each row execute function public.touch_public_garage_updated_at();

drop trigger if exists touch_public_vehicle_profiles_updated_at
    on public.public_vehicle_profiles;
create trigger touch_public_vehicle_profiles_updated_at
before update on public.public_vehicle_profiles
for each row execute function public.touch_public_garage_updated_at();

create or replace function public.validate_public_vehicle_profile()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if not exists (
        select 1 from public.vehicles v
        where v.id = new.vehicle_id
          and v.owner_id = new.owner_id
    ) then
        raise exception 'Public vehicle profile must belong to the vehicle owner.';
    end if;
    return new;
end;
$$;

revoke execute on function public.validate_public_vehicle_profile()
from public, anon, authenticated;

drop trigger if exists validate_public_vehicle_profile_before_write
    on public.public_vehicle_profiles;
create trigger validate_public_vehicle_profile_before_write
before insert or update of owner_id, vehicle_id
on public.public_vehicle_profiles
for each row execute function public.validate_public_vehicle_profile();

insert into storage.buckets (
    id,name,public,file_size_limit,allowed_mime_types
)
values (
    'public-garage',
    'public-garage',
    true,
    8388608,
    array['image/jpeg','image/png','image/webp']
)
on conflict (id) do update
set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Users can publish own garage photos"
    on storage.objects;
create policy "Users can publish own garage photos"
    on storage.objects
    for insert to authenticated
    with check (
        bucket_id = 'public-garage'
        and owner_id = auth.uid()::text
    );

drop policy if exists "Users can update own garage photos"
    on storage.objects;
create policy "Users can update own garage photos"
    on storage.objects
    for update to authenticated
    using (
        bucket_id = 'public-garage'
        and owner_id = auth.uid()::text
    )
    with check (
        bucket_id = 'public-garage'
        and owner_id = auth.uid()::text
    );

drop policy if exists "Users can delete own garage photos"
    on storage.objects;
create policy "Users can delete own garage photos"
    on storage.objects
    for delete to authenticated
    using (
        bucket_id = 'public-garage'
        and owner_id = auth.uid()::text
    );
