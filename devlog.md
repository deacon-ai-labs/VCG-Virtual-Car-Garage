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