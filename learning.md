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