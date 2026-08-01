import streamlit as st

from openai import OpenAI





st.set_page_config(

    page_title="Virtual Car Garage",

    page_icon="🚗",

)





# OpenAI uses this ID to remember the conversation context.

if "previous_response_id" not in st.session_state:

    st.session_state.previous_response_id = None





# Streamlit uses this list to display the visible chat history.

if "messages" not in st.session_state:

    st.session_state.messages = []





st.title("🚗 Virtual Car Garage")



st.write(

    "Describe a problem with your vehicle and Garage AI will help "

    "you investigate it."

)





# Redisplay all previous messages whenever Streamlit reruns the page.

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])





# This stays at the bottom of the page and clears after submission.

user_message = st.chat_input(

    "Describe the problem or answer Garage AI's question..."

)





if user_message:

    # Save and display the user's message.

    st.session_state.messages.append(

        {

            "role": "user",

            "content": user_message,

        }

    )



    with st.chat_message("user"):

        st.markdown(user_message)



    client = OpenAI()



    request = {

        "model": "gpt-4.1-mini",

        "instructions": (

            "You are Virtual Car Garage's cautious automotive assistant. "

            "Help the user investigate the problem by explaining likely "

            "possibilities and asking useful follow-up questions. "

            "Do not claim certainty from limited information. "

            "Recommend only safe basic checks. Clearly state when the "

            "vehicle should not be driven or should be inspected by a "

            "qualified mechanic."

        ),

        "input": user_message,

    }



    if st.session_state.previous_response_id is not None:

        request["previous_response_id"] = (

            st.session_state.previous_response_id

        )



    with st.chat_message("assistant"):

        with st.spinner("Garage AI is investigating..."):

            response = client.responses.create(**request)



        assistant_message = response.output_text

        st.markdown(assistant_message)



    # Save the OpenAI conversation link.

    st.session_state.previous_response_id = response.id



    # Save the visible assistant message.

    st.session_state.messages.append(

        {

            "role": "assistant",

            "content": assistant_message,

        }

    )