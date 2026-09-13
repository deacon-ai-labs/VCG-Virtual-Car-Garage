# 2 August 2026

## Goal

Build my first AI application.

## What I built

A Python application that sends prompts to GPT-4.1 Mini using the OpenAI SDK.

## Problems

- Git commit failed because I typed `/m` instead of `-m`.
- GPT-5 Mini required organisation verification.

## What I learned

- Virtual environments isolate project dependencies.
- GitHub Codespaces are an excellent development environment.
- AI models don't always produce identical responses because they are probabilistic.

## Next goal

Make the application conversational.

# Session 3



## What I learned



- What JSON is.

- Why data disappears when a program closes.

- How Python functions separate tasks.



## What I found difficult



- Understanding how Git detects a renamed file.



## Questions I still have



- When should data go in JSON versus a database?

DEVLOG.md is the technical history of the application:

# Session 4B



## What I learned



- A browser widget can send user input to server-side Python.

- Streamlit reruns the Python script when a user clicks a button.

- The OpenAI API key remains on the server.

- Input validation avoids unnecessary API requests.

- The browser, application server and OpenAI model perform different jobs.



## What I found difficult



- Add anything that was unclear during this session.



## Questions I still have



- How can a Streamlit app remember previous messages?


# Session 5



## What I learned



- Streamlit reruns the Python script after user interaction.

- Session State stores information for one visitor's browser session.

- OpenAI conversation memory and visible chat history are separate things.

- `st.chat_input()` clears automatically after submission.

- `st.chat_message()` displays a conversation in a chat-style interface.



## What I found difficult



- Python indentation controls which code belongs inside an `if`, `else`, or `with` block.

- A variable can produce a NameError if code using it runs outside the block where it was created.



## Questions I still have



- How long does Streamlit Session State last?

- How do we add a New Conversation button?

- How do we remember a vehicle after the browser session ends?

# Session 6



## What I learned



- PostgreSQL stores permanent structured data.

- Supabase hosts and manages a PostgreSQL database.

- Tables contain rows and columns.

- A primary key uniquely identifies each row.

- Row Level Security controls which database rows a user can access.

- Development and production environments need separate secrets.

- The user interface should not contain database connection logic.



## What I found difficult



- Add anything that was unclear.



## Questions I still have



- How will each user own only their own vehicles?

- Why do we need authentication before proper RLS?

- How will RAG use the same Postgres database?


# Session 7



## What I learned



- Streamlit can read permanent data from a hosted database.

- A database row has a permanent primary key.

- The UI can display a friendly profile name while internally using its ID.

- Session State stores the temporary active vehicle selection.

- Supabase remains the source of truth for vehicle details.

- Changing the active vehicle should reset incompatible chat context.

- Forms group related inputs and submit them together.

- Database errors should be handled rather than crashing the whole application.



## What I found difficult



- Add anything that was unclear during this session.



## Questions I still have



- How will authentication associate vehicles with individual users?

- How do we edit and delete vehicle profiles safely?

- How will RAG choose documents for the selected vehicle?


# Session 8 

  

## What I learned 

  

- RAG stands for Retrieval-Augmented Generation. It allows an AI application to retrieve relevant information from trusted documents before generating an answer. 

  

- Embeddings convert text into numerical representations that allow semantically similar questions and document chunks to be matched. 

  

- Vector similarity search can find relevant information even when the user's wording is different from the wording in the source document. 

  

- Supabase with pgvector can store embeddings and perform similarity searches directly in PostgreSQL. 

  

- RAG retrieval and AI generation are separate stages. First the application retrieves relevant evidence, then the language model uses that evidence to answer the question. 

  

- Retrieval quality is not just about finding similar text. The application also needs to understand which source is more authoritative. 

  

- Vehicle-specific documentation should take priority over generic documentation. A generic Civic specification must not automatically be treated as correct for a Civic Type R. 

  

- A RAG system should sometimes say that it does not have enough evidence rather than confidently filling a gap from the model's general knowledge. 

  

- Overlapping text chunks help prevent information being lost when a document is split in the middle of a sentence. 

  

- Returning more candidate chunks and removing near-duplicates can improve the variety and usefulness of the evidence sent to the AI. 

  

- Local development and deployed production code can be different. The Codespace was running the new RAG files while Streamlit Cloud was still running the older files stored on GitHub. 

  

- Testing with real questions is important because it can reveal problems that are not obvious from reading the code. 

  

## What I found difficult 

  

- Understanding why a semantically relevant result can still be the wrong source for a particular vehicle. 

  

- Understanding the difference between generic vehicle information and authoritative model-specific specifications. 

  

- Diagnosing why the local Streamlit application behaved differently from the deployed Streamlit Cloud application. 

  

## Questions I still have 

  

- How should we associate the correct knowledge documents with each vehicle when the garage contains many different makes and models? 

  

- Should knowledge scope eventually be stored as a proper field in the vehicle database instead of being inferred from the vehicle description? 

  

- How should modifications to an individual vehicle affect the information Garage AI retrieves and the advice it gives? 

  

- How can we measure whether our RAG retrieval is consistently finding the best evidence? 


# Session 9 

  

## What I learned 

  

- Authentication and authorization are different things. 

  

- Authentication proves who the user is. 

  

- Authorization decides what that user is allowed to access. 

  

- Supabase Auth can create and manage users using email and password. 

  

- Each authenticated Supabase user has a unique UUID that can be used as a permanent owner ID in application data. 

  

- Row Level Security (RLS) can enforce user isolation directly in PostgreSQL. 

  

- Using `auth.uid() = owner_id` means the database only returns rows owned by the currently authenticated user. 

  

- Database-level security is safer than relying only on Python filtering because RLS still protects the data if application code contains a mistake. 

  

- An authenticated Supabase client carries the user's session and allows PostgreSQL to know which user is making the request. 

  

- Streamlit Session State can hold temporary authentication tokens so the user remains signed in while the browser session is active. 

  

- Different users can share the same application and database while still seeing completely separate garages. 

  

- Conversation history should be stored by the application rather than relying only on temporary Streamlit state. 

  

- OpenAI conversation continuation state and visible chat history are separate things. 

  

- `last_response_id` can be stored for OpenAI conversation continuation, while Supabase stores the permanent user and assistant messages. 

  

- Conversations can belong to both a user and a vehicle. 

  

- Row Level Security should also protect conversations and messages, not just vehicles. 

  

- Foreign keys and `ON DELETE CASCADE` help keep related data consistent. For example, deleting a conversation can automatically delete its messages. 

  

- Stable application state is important when building interactive Streamlit components. 

  

- A Streamlit widget can cause a rerun, so unstable widget state can accidentally interrupt another action such as sending a chat message. 

  

- Explicit conversation IDs are more reliable than relying on hidden dropdown widget state. 

  

- Automated tests can verify database helper functions before testing the full user interface. 

  

## What I found difficult 

  

- Understanding how Supabase authentication tokens are passed back into the database so RLS can identify the logged-in user. 

  

- Understanding why the application stopped seeing vehicles after anonymous RLS access was removed. 

  

- Diagnosing why the second chat message disappeared even though no error was shown. 

  

- Understanding the interaction between Streamlit reruns, widget state, conversation selection, and chat input. 

  

- Understanding why visible chat history and OpenAI conversation continuation need to be persisted separately. 

  

## Questions I still have 

  

- How should we securely keep a user signed in across a complete browser restart? 

  

- How should password reset and account recovery work? 

  

- Should conversations eventually support archive, search, favourites, or categories? 

  

- Should conversation titles continue to be based on the first message, or should Garage AI generate better summaries later? 

  

- How should conversation history be summarized if a thread becomes very long? 

  

- How should user-specific vehicle modifications and service history be incorporated into future RAG retrieval? 

  

- How should we design the UI so authentication, vehicles, conversations, and Garage AI feel like one polished product? 


# Session 10 

  

## What I learned 

  

- Git branches let us make large changes without putting the stable `main` version at risk. 

  

- A feature branch is useful when a session includes major UI changes, new files, new database features, and behavior changes. 

  

- Streamlit can be styled heavily with CSS while still using native Streamlit widgets for application behavior. 

  

- It is better to use native Streamlit controls for interactive features and use CSS mainly for presentation rather than trying to build the whole interface in custom HTML. 

  

- Streamlit columns can be used to create an application-style dashboard with separate areas for the garage, Garage AI, and vehicle details. 

  

- Streamlit Session State is useful for application UI state such as: 

  - selected vehicle 

  - selected conversation 

  - whether My Garage is collapsed 

  

- Selecting a different vehicle should also intentionally reset conversation state so Garage AI starts with a clean conversation for that vehicle. 

  

- A new chat does not need to exist in the database until the user actually sends the first message. 

  

- Creating conversations lazily avoids filling the database with empty `New conversation` records. 

  

- Conversation timestamps are best stored in UTC in the database and converted to the user's local timezone for display. 

  

- Streamlit provides the browser timezone through `st.context.timezone`. 

  

- Using the browser timezone means the same application can correctly display GMT/BST in the UK and local time in other countries without asking the user to configure a timezone manually. 

  

- `updated_at` is more useful than `created_at` for a recent-conversation list because it tells us when the conversation was last active. 

  

- Long chat interfaces work better when they behave like an application rather than a long webpage. 

  

- Garage AI can have its own scrollable history while the input remains available and the garage and vehicle panels remain visible. 

  

- Care is needed when mixing fixed viewport heights and Streamlit's `st.chat_input()` because clipping the parent container can accidentally hide the prompt box. 

  

- CSS written inside a Python f-string must escape literal braces as `{{` and `}}`. 

  

- Private Supabase Storage is appropriate for user-owned vehicle photos. 

  

- A database can store the private Storage object path rather than storing a permanent public URL. 

  

- Temporary signed URLs can then be created when the application needs to display a private photo. 

  

- User files can be isolated in Storage using owner-scoped paths such as: 

  

  `<owner UUID>/<vehicle ID>/<filename>` 

  

- Replacing a stored image safely should happen in this order: 

  1. upload the new object 

  2. update the database to point to it 

  3. delete the previous object 

  

- If the database update fails, the newly uploaded object should be removed so orphaned files are not left behind. 

  

- A polished UI should make the vehicle image itself act as the photo upload/change control rather than exposing unnecessary administrative buttons. 

  

- Desktop and mobile web layouts do not need to behave identically. 

  

- For VCG: 

  - desktop can use a fixed multi-panel application layout 

  - mobile browser can use a simpler vertically stacked fallback 

  - the native iPhone app planned for Session 11 can later become the premium mobile experience 

  

## Design lessons 

  

- The car should remain visually important even though Garage AI owns the largest portion of the workspace. 

  

- The approved visual language is: 

  - dark charcoal / slate grey 

  - orange/coral highlights 

  - soft white text 

  - premium enthusiast garage feel 

  - clean rather than heavily futuristic 

  

- The vehicle card itself should be the main vehicle selector. 

  

- A second Current Vehicle dropdown is unnecessary if users can already select the car from My Garage. 

  

- The sign-in page should feel like part of the same product rather than a separate generic authentication screen. 

  

- Garage AI should be the dominant workspace in the signed-in application. 

  

## Problems we encountered 

  

- The first login hero implementation cropped the approved image at normal browser zoom. 

  

- The cause was `object-fit: cover` combined with a fixed minimum height. 

  

- Changing the layout to preserve the image aspect ratio and use `object-fit: contain` fixed the problem. 

  

- New Phase 4 CSS initially caused a Python `NameError`. 

  

- The cause was unescaped CSS braces inside a Python f-string. 

  

- Escaping the CSS braces fixed both the runtime error and the editor warnings. 

  

- The first fixed-scroll implementation caused the Garage AI prompt box to disappear. 

  

- The cause was clipping the Streamlit block container to `100vh` while the chat input was rendered below the independently sized chat-history area. 

  

- The corrected design leaves room for the composer rather than clipping the entire page container. 

  

## Questions / future learning 

  

- How should we compress and resize uploaded vehicle photos before storing them? 

  

- Should VCG eventually support multiple photos per vehicle rather than one primary image? 

  

- Should vehicle photos have metadata such as: 

  - front 

  - rear 

  - engine bay 

  - interior 

  - modifications 

  

- How should maintenance records integrate with vehicle mileage and reminders? 

  

- What UI patterns from the Streamlit version should carry forward into the native SwiftUI iPhone app? 

  

- How should the Python Garage AI / RAG layer be exposed as a secure API for the iPhone app?