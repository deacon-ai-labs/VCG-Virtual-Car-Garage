-- VCG M11 — Phase B: final RAG lockdown.
-- Run only after the M11 branch is deployed with SUPABASE_SECRET_KEY
-- configured and Garage AI retrieval has been successfully tested.
--
-- Supabase secret API keys operate as the service_role Postgres role, so
-- service_role remains the correct database role name in these GRANTs.

alter table public.knowledge_chunks enable row level security;

revoke all on table public.knowledge_chunks
from anon, authenticated;

grant select, insert, update, delete
on table public.knowledge_chunks
to service_role;

do $$
declare
    fn record;
begin
    for fn in
        select p.oid::regprocedure as signature
        from pg_proc p
        join pg_namespace n
          on n.oid = p.pronamespace
        where n.nspname = 'public'
          and p.proname = 'match_knowledge_chunks'
    loop
        execute format(
            'revoke all on function %s from public, anon, authenticated',
            fn.signature
        );

        execute format(
            'grant execute on function %s to service_role',
            fn.signature
        );
    end loop;
end
$$;

select
    n.nspname as schema_name,
    p.proname as function_name,
    p.oid::regprocedure as signature
from pg_proc p
join pg_namespace n
  on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname = 'match_knowledge_chunks';
