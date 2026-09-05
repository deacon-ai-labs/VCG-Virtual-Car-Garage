DEVLOG.md is the technical history of the application:

# Session 3



## Changes made



- Renamed `test_ai.py` to `car_garage.py`.

- Added persistent vehicle profiles.

- Added `vehicle_profile.json`.

- Loaded vehicle details into the AI instructions.



## Problems fixed



- Corrected file rename and Git tracking issue.



## Next step



- Allow the user to edit the saved vehicle profile.

# Session 4B



## Changes made



- Connected the Streamlit interface to the OpenAI Responses API.

- Added a vehicle-problem text area.

- Added the Ask Garage AI button.

- Added empty-input validation.

- Added a loading spinner.

- Displayed the AI response in the web page.



## Current limitation



- Each request is independent.

- The web application does not yet preserve conversation history.



## Next development step



- Add web conversation memory using Streamlit Session State.


# Session 5



## Changes made



- Added Streamlit Session State.

- Added OpenAI conversation continuity using `previous_response_id`.

- Replaced the text area and button interface with chat components.

- Added visible user and assistant message history.

- Added an automatically clearing chat input.



## Bugs fixed



- Fixed incorrect indentation that caused `client` to be undefined.

- Corrected the placement of the OpenAI request and response handling.



## Current limitations



- Conversation history lasts only for the current browser session.

- There is no New Conversation button yet.

- Vehicle details are not yet persisted in the deployed web application.



## Next development step



- Add a sidebar with vehicle details and a New Conversation button.

# Session 6



## Changes made



- Created a Supabase project.

- Created the PostgreSQL vehicles table.

- Enabled Row Level Security.

- Added temporary prototype read and insert policies.

- Added the Supabase Python dependency.

- Added database.py.

- Connected Codespaces to Supabase using environment secrets.

- Saved and retrieved the first vehicle profile.



## Security limitation



- The prototype currently uses anonymous access.

- Vehicle rows are not yet separated by authenticated user.

- The public URL should remain limited to trusted testers.



## Next development step



- Connect the Streamlit sidebar to Supabase.

- Add vehicle selection.

- Pass the active vehicle profile into Garage AI.

- Add authentication and user-owned rows before wider sharing.

Then:

git status

git add requirements.txt database.py test_database.py LEARNING.md DEVLOG.md

git commit -m "Add Supabase vehicle database"

git pull --rebase

git push

Do not commit any .env, secrets.toml, database password or API key.


# Session 7



## Changes made



- Connected the Streamlit sidebar to Supabase.

- Loaded permanent vehicle profiles.

- Added active-vehicle selection.

- Displayed vehicle details in the sidebar.

- Added a form for creating additional vehicle profiles.

- Saved new vehicles permanently in PostgreSQL.

- Added selected-vehicle context to Garage AI.

- Reset chat context when switching vehicles.

- Rather than editing the app.py file, we got chatgpt to rewrite the file to include modify / delete capability of the saved cars.


## Architecture



- Supabase stores permanent vehicle records.

- Streamlit Session State stores the temporary active vehicle ID.

- database.py isolates database access from the user interface.

- Garage AI receives the active vehicle as contextual information.



## Current limitations



- All prototype visitors can currently see the same vehicles.

- There is no user authentication.

- Vehicles cannot yet be edited or deleted through the app.

- Conversation history is not stored permanently.



## Next development step



- Add Supabase authentication and user-owned vehicle records, or begin the first controlled RAG prototype with the EP3 owner’s manual.


# Session 8 

  

## Changes made 

  

- Created the first RAG retrieval layer for Virtual Car Garage. 

  

- Added a Supabase PostgreSQL function, `match_knowledge_chunks`, to perform pgvector cosine-similarity searches against the existing `knowledge_chunks` table. 

  

- Created `rag.py`. 

  

- Added OpenAI query embeddings using `text-embedding-3-small`. 

  

- Connected `rag.py` to the Supabase vector-search function. 

  

- Added command-line testing of RAG retrieval before integrating it into the Streamlit application. 

  

- Tested retrieval using real Honda Civic Type R questions including tyre size and tyre pressure. 

  

- Increased the number of retrieval candidates and added near-duplicate removal so repeated document passages do not consume all of the available context. 

  

- Added vehicle-aware retrieval using the existing `vehicle_scope` metadata. 

  

- Added an evidence hierarchy: 

  - `civic_type_r_ep3` evidence is treated as vehicle-specific and authoritative for the EP3. 

  - `civic_3door_all_models` evidence is treated as generic supplementary information. 

  

- Updated `garage_ai.py` to retrieve relevant documentation before sending a question to the OpenAI Responses API. 

  

- Added Honda reference material to the Garage AI instructions. 

  

- Added grounding rules requiring Garage AI to prefer vehicle-specific documentation over generic documentation. 

  

- Prevented generic Civic numerical specifications from being presented as Civic Type R specifications unless confirmed by Type R-specific evidence. 

  

- Added guidance for Garage AI to state when the supplied knowledge library cannot verify a requested model-specific value rather than filling the gap from general model knowledge. 

  

- Added source and page information to the retrieved context so Garage AI can reference the underlying Honda documentation. 

  

- Added safeguards to prevent Honda RAG data being used for unrelated vehicles. 

  

## Problems found and fixed 

  

- Initial retrieval results contained multiple near-identical chunks from overlapping Honda documents. Added de-duplication. 

  

- The generic Civic owner's manual initially outranked the Type R documentation for some questions and caused Garage AI to return the wrong wheel and tyre specification for the EP3. 

  

- Changed retrieval and prompt logic so Type R-specific evidence is authoritative and generic Civic information is supplementary only. 

  

- The generic owner's manual contained a 30 psi tyre-pressure specification for a different wheel and tyre configuration. Garage AI now avoids presenting this as an EP3 Type R specification when the Type R-specific documents do not verify it. 

  

- Discovered that the Codespace and deployed Streamlit Cloud application were running different versions of the code. The Codespace contained the new RAG files while GitHub `main`, and therefore Streamlit Cloud, still contained the old non-RAG version. 

  

## Testing 

  

- Confirmed vector similarity search retrieves relevant Honda documentation. 

  

- Confirmed a query about the 2004 Civic Type R tyre size retrieves Honda Type R documentation containing the correct `205/45 R17` tyre size and `17 x 7JJ` wheel specification. 

  

- Confirmed the updated Garage AI gives the correct Type R-specific tyre-size answer. 

  

- Confirmed Garage AI no longer treats the generic Civic tyre-pressure value as an authoritative Type R specification. 

  

- Confirmed the local Streamlit application can now answer questions using retrieved Honda documentation. 

  

## Architecture 

  

The RAG flow is now: 

  

User question   

→ OpenAI embedding   

→ Supabase pgvector similarity search   

→ vehicle-specific and supplementary evidence selection   

→ duplicate removal   

→ Garage AI prompt containing selected vehicle + retrieved evidence   

→ grounded AI response 

  

## Current limitations 

  

- The first controlled RAG implementation currently supports the Honda Civic / Civic Type R EP3 knowledge set. 

  

- Vehicle knowledge scope is inferred from the vehicle description rather than stored explicitly against the vehicle record. 

  

- The available Type R documents do not contain every possible maintenance specification, so some questions cannot yet be answered authoritatively from the knowledge library. 

  

- Deacon's actual EP3 modifications still need to be added as seed data once the complete modification list is available. 

  

- The new Session 8 RAG files have been tested locally but still need to be committed and pushed to GitHub before Streamlit Cloud will deploy them. 

  

- User authentication and user-owned vehicle records remain future work. 

  

## Next development step 

  

- Commit and push the Session 8 RAG changes to GitHub. 

  

- Confirm that Streamlit Cloud redeploys the RAG-enabled version successfully. 

  

- Test the same grounded questions against the deployed application. 

  

- Add seed data describing Deacon's actual EP3 modifications once that information is available. 

  

- Later, consider adding an explicit knowledge scope/model identifier to vehicle records so RAG document selection can scale beyond the EP3. 


# Session 9 

  

## Changes made 

  

### Authentication and user-owned garages 

  

- Added Supabase email/password authentication. 

  

- Created Deacon's Supabase Auth user. 

  

- Added `owner_id` to the `vehicles` table. 

  

- Assigned the existing EP3 and BYD vehicle records to Deacon's Auth user UUID. 

  

- Added a foreign key from `vehicles.owner_id` to `auth.users(id)`. 

  

- Made `vehicles.owner_id` mandatory. 

  

- Removed the original prototype shared-access RLS policies. 

  

- Added authenticated user-specific RLS policies for: 

  - SELECT 

  - INSERT 

  - UPDATE 

  - DELETE 

  

- Added `auth.py`. 

  

- Added authentication functions for: 

  - sign-up 

  - sign-in 

  - sign-out 

  - restoring an authenticated Supabase client from an existing session 

  

- Added `test_auth.py`. 

  

- Added four authentication unit tests. 

  

- Updated `database.py` so all vehicle CRUD operations use the authenticated Supabase client. 

  

- Updated new vehicle creation so the authenticated user's UUID is automatically stored as `owner_id`. 

  

- Added `test_database.py`. 

  

- Added database tests for authenticated vehicle CRUD. 

  

- Updated `app.py` with: 

  - sign-in UI 

  - create-account UI 

  - sign-out 

  - authenticated Streamlit session state 

  - authenticated Supabase client restoration 

  - prevention of vehicle loading before authentication succeeds 

  

- Added signed-in user information to the sidebar. 

  

- Verified Deacon can sign in and see only his EP3 and BYD. 

  

- Created a second test user. 

  

- Verified the second user initially sees an empty garage. 

  

- Verified the second user can create a separate VW Polo. 

  

- Verified Deacon cannot see the second user's VW Polo. 

  

- Verified the second user cannot see Deacon's vehicles. 

  

### Persistent conversations 

  

- Created a `conversations` table in Supabase. 

  

- Added: 

  - `owner_id` 

  - `vehicle_id` 

  - `title` 

  - `last_response_id` 

  - `created_at` 

  - `updated_at` 

  

- Created a `messages` table in Supabase. 

  

- Added: 

  - `conversation_id` 

  - `owner_id` 

  - `role` 

  - `content` 

  - `created_at` 

  

- Added database indexes for conversation and message lookup. 

  

- Enabled Row Level Security on both new tables. 

  

- Added user-specific RLS policies for conversations and messages. 

  

- Added checks preventing users from attaching conversations to another user's vehicle. 

  

- Added checks preventing users from attaching messages to another user's conversation. 

  

- Added conversation database functions: 

  - `get_conversations` 

  - `create_conversation` 

  - `get_messages` 

  - `add_message` 

  - `update_conversation_response_id` 

  - `rename_conversation` 

  - `delete_conversation` 

  

- Increased database unit tests from 5 to 10 and later to 13 tests. 

  

- Added persistent message storage in Supabase. 

  

- Added persistent `last_response_id` storage for OpenAI Responses API continuation. 

  

- Added vehicle-specific conversation history. 

  

- Added New Conversation functionality. 

  

- Added loading of previous conversations and messages after Streamlit reruns. 

  

- Added automatic conversation titles based on the first user message. 

  

- Added manual conversation rename. 

  

- Added conversation deletion with confirmation. 

  

- Added cascading deletion of messages when a conversation is deleted. 

  

- Replaced the conversation dropdown with explicit conversation buttons. 

  

## Problems found and fixed 

  

- Enabling proper vehicle RLS temporarily caused the application to stop seeing vehicles because the app was still using anonymous Supabase access. 

  

- Fixed this by creating and restoring an authenticated Supabase client after sign-in. 

  

- Supabase confirmation emails initially redirected to `localhost:3000`. 

  

- Identified this as a Supabase Site URL / redirect configuration issue. 

  

- Initial persistent conversation implementation allowed one message exchange but the second user message caused the page to refresh and the conversation to appear empty. 

  

- Investigation showed the second message was never stored in Supabase. 

  

- Root cause was unstable conversation selector state combined with Streamlit reruns. 

  

- Initially changed conversation ordering from `updated_at` to stable `created_at` ordering. 

  

- Added explicit conversation selector state handling. 

  

- Multi-turn conversation messaging then worked correctly. 

  

- The dropdown still contained multiple conversations all named `New conversation`, making selection unclear. 

  

- Older conversation selection was also unreliable. 

  

- Replaced the dropdown with explicit conversation buttons using conversation IDs. 

  

- Added meaningful automatic conversation titles. 

  

- Added manual rename and delete functionality. 

  

## Testing 

  

- Authentication tests: 4 passed. 

  

- Initial authenticated database tests: 5 passed. 

  

- Conversation persistence database tests: 10 passed. 

  

- Final conversation-management database tests: 13 passed. 

  

- Confirmed Deacon can sign in and see his EP3 and BYD. 

  

- Confirmed a second user sees no Deacon vehicles. 

  

- Confirmed the second user can create their own vehicle. 

  

- Confirmed Deacon cannot see the second user's VW Polo. 

  

- Confirmed multi-turn Garage AI conversations now work. 

  

- Confirmed follow-up questions remain in the same conversation. 

  

- Confirmed older conversations can be reopened. 

  

- Confirmed new conversations receive meaningful titles. 

  

- Confirmed conversations can be renamed. 

  

- Confirmed conversations can be deleted. 

  

- Confirmed conversation messages persist in Supabase. 

  

## Architecture 

  

The authenticated application flow is now: 

  

User opens VCG   

→ sign in with Supabase Auth   

→ authenticated Supabase session   

→ PostgreSQL RLS identifies `auth.uid()`   

→ only that user's vehicles are returned   

→ selected vehicle   

→ only that vehicle's conversations are returned   

→ selected conversation   

→ messages loaded from Supabase   

→ Garage AI + RAG   

→ user and assistant messages saved   

→ `last_response_id` updated   

→ future turns continue the same OpenAI conversation 

  

Private data ownership is now: 

  

User   

→ Vehicles   

→ Conversations   

→ Messages 

  

Honda RAG knowledge remains shared reference data and is separate from private user data. 

  

## Current limitations 

  

- Authentication currently uses email/password only. 

  

- Users may need to sign in again after a complete browser session restart. 

  

- Password reset/account recovery UI is not yet implemented. 

  

- Supabase Site URL / redirect configuration should be updated so email confirmation links redirect to the deployed Streamlit application rather than localhost. 

  

- Conversation titles are currently generated from the first user message rather than by AI. 

  

- Conversation search/archive features do not yet exist. 

  

- Deacon's full EP3 modification seed data still needs to be added once the complete modification list is available. 

  

- Persistent conversation functionality has been tested locally and still needs final deployed Streamlit Cloud verification after committing and pushing the Session 9 code. 

  

## Next development step 

  

- Update `learning.md` and `devlog.md`. 

  

- Commit and push all Session 9 changes. 

  

- Confirm Streamlit Cloud redeploys the authenticated and persistent-conversation version. 

  

- Verify authentication, vehicle isolation, persistent conversations, and Honda RAG on the deployed application. 

  

- Fix Supabase production redirect URL. 

  

- Begin Session 10: redesign the Streamlit UI to make Virtual Car Garage look polished, modern, and automotive-focused. 