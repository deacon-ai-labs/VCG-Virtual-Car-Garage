# VCG M11 — Security & Private Knowledge

## Product decision

The raw Honda PDFs are source material for building the RAG index. They are
not a runtime dependency of Virtual Car Garage.

This deliberately separates:

1. Admin ingestion:
   private_knowledge/ -> extraction -> embeddings -> knowledge_chunks

2. VCG runtime:
   user question -> query embedding -> match_knowledge_chunks -> Garage AI

This keeps the production app smaller, more reliable and easier to secure.

## Runtime architecture

Public GitHub source
→ Streamlit server
→ server-only SUPABASE_SECRET_KEY
→ locked knowledge_chunks / match_knowledge_chunks
→ Garage AI

The normal authenticated Supabase client remains responsible for user-owned
vehicles, conversations, messages, maintenance and vehicle photos.

## Raw source documents

- The private source folder is `private_knowledge/`.
- It is excluded by .gitignore.
- Raw PDFs must never be committed to Git again.
- A private Supabase Storage bucket may be retained as an optional archive,
  but VCG does not download PDFs from Storage at runtime and ingestion does
  not depend on that bucket.

## Migration order

1. Configure SUPABASE_SECRET_KEY in Codespaces and Streamlit Cloud.
2. Create the ignored local private source directory:
   `mkdir -p private_knowledge`
3. Before deleting the legacy tracked PDFs, copy them into it:
   `cp knowledge/*.pdf private_knowledge/`
4. Run:
   `python -m unittest discover -v`
5. Run:
   `python ingest_knowledge.py`
6. Verify Garage AI retrieves the expected Honda evidence.
7. Remove the legacy tracked `knowledge/` PDFs from Git.
8. Deploy/test the M11 branch.
9. Run `supabase_m11_lockdown.sql`.
10. Retest Garage AI.
11. Purge the old PDFs from Git history.
12. Retire the compromised legacy service-role key after every component has
    been verified on the new API-key model.

## Failure safety

The ingestion command validates all source files, extracts every document and
creates all new embeddings before it deletes any existing knowledge rows.

## Security rules

Never commit:

- SUPABASE_SECRET_KEY
- OPENAI_API_KEY
- .env
- .streamlit/secrets.toml
- private_knowledge/
- raw knowledge PDFs

The Supabase secret key is server/admin only.


## Lockdown verification

After deploying the M11 code and running `supabase_m11_lockdown.sql`, run:

`python verify_m11_lockdown.py`

A passing result requires all three conditions:

- publishable client cannot read `knowledge_chunks`
- publishable client cannot execute `match_knowledge_chunks`
- server-only RAG still retrieves EP3-specific evidence

Only after this passes should the old PDFs be purged from Git history and the
compromised legacy service-role key be retired.
