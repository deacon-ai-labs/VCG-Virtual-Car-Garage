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


