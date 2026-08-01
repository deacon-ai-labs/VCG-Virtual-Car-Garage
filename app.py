import streamlit as st

from openai import OpenAI





st.set_page_config(

    page_title="Virtual Car Garage",

    page_icon="🚗",

)



st.title("🚗 Virtual Car Garage")



st.write(

    "Describe a problem with your vehicle and Garage AI will help "

    "you investigate it."

)



car_problem = st.text_area(

    "What is happening with the car?",

    placeholder=(

        "For example: My 2004 Honda Civic Type R EP3 makes "

        "a clicking noise when turning slowly."

    ),

)



ask_button = st.button(

    "Ask Garage AI",

    type="primary",

)



if ask_button:

    if not car_problem.strip():

        st.warning("Please describe the problem first.")

    else:

        client = OpenAI()



        with st.spinner("Garage AI is investigating..."):

            response = client.responses.create(

                model="gpt-4.1-mini",

                instructions=(

                    "You are Virtual Car Garage's cautious automotive assistant. "

                    "Help the user investigate the problem by explaining likely "

                    "possibilities and asking useful follow-up questions. "

                    "Do not claim certainty from limited information. "

                    "Recommend only safe basic checks. Clearly state when the "

                    "vehicle should not be driven or should be inspected by a "

                    "qualified mechanic."

                ),

                input=car_problem,

            )



        st.subheader("Garage AI response")

        st.write(response.output_text)