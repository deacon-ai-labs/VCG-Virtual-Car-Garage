import streamlit as st

from openai import OpenAI

from database import add_vehicle, get_vehicles



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

if "active_vehicle_id" not in st.session_state:

    st.session_state.active_vehicle_id = None

try:

    vehicles = get_vehicles()



except Exception as error:

    st.error("Virtual Car Garage could not load the vehicle database.")

    st.exception(error)

    st.stop()

with st.sidebar:

    st.header("🚗 My Garage")



    if vehicles:

        vehicle_options = {

            vehicle["id"]: vehicle["profile_name"]

            for vehicle in vehicles

        }



        vehicle_ids = list(vehicle_options.keys())



        if st.session_state.active_vehicle_id not in vehicle_ids:

            st.session_state.active_vehicle_id = vehicle_ids[0]



        selected_vehicle_id = st.selectbox(

            "Active vehicle",

            options=vehicle_ids,

            format_func=lambda vehicle_id: vehicle_options[vehicle_id],

            index=vehicle_ids.index(

                st.session_state.active_vehicle_id

            ),

        )



        if selected_vehicle_id != st.session_state.active_vehicle_id:

            st.session_state.active_vehicle_id = selected_vehicle_id

            st.session_state.messages = []

            st.session_state.previous_response_id = None

            st.rerun()



    else:

        selected_vehicle_id = None

        st.session_state.active_vehicle_id = None

        st.info("No vehicles have been added yet.")





active_vehicle = None



if st.session_state.active_vehicle_id is not None:

    active_vehicle = next(

        (

            vehicle

            for vehicle in vehicles

            if vehicle["id"] == st.session_state.active_vehicle_id

        ),

        None,

    )





with st.sidebar:

    if active_vehicle:

        st.divider()

        st.subheader(active_vehicle["profile_name"])



        st.write(

            f"**Vehicle:** "

            f"{active_vehicle['year']} "

            f"{active_vehicle['manufacturer']} "

            f"{active_vehicle['model']}"

        )



        st.write(f"**Engine:** {active_vehicle['engine']}")

        st.write(f"**Mileage:** {active_vehicle['mileage']:,}")



        if active_vehicle["modifications"]:

            st.write("**Modifications:**")

            st.write(active_vehicle["modifications"])

    st.divider()



    with st.expander("➕ Add another vehicle"):

        with st.form("add_vehicle_form", clear_on_submit=True):

            profile_name = st.text_input(

                "Profile name",

                placeholder="Deacon's EP3",

            )



            manufacturer = st.text_input(

                "Manufacturer",

                placeholder="Honda",

            )



            model = st.text_input(

                "Model",

                placeholder="Civic Type R EP3",

            )



            year = st.number_input(

                "Year",

                min_value=1900,

                max_value=2100,

                step=1,

                value=2004,

            )



            engine = st.text_input(

                "Engine",

                placeholder="2.0-litre K20A2",

            )



            mileage = st.number_input(

                "Mileage",

                min_value=0,

                step=1000,

                value=0,

            )



            modifications = st.text_area(

                "Modifications",

                placeholder=(

                    "Enter one modification per line, "

                    "or leave blank if standard."

                ),

            )



            submitted = st.form_submit_button(

                "Save vehicle",

                type="primary",

                use_container_width=True,

            )
        if submitted:

            required_text_fields = {

                "Profile name": profile_name,

                "Manufacturer": manufacturer,

                "Model": model,

                "Engine": engine,

            }



            missing_fields = [

                field_name

                for field_name, field_value in required_text_fields.items()

                if not field_value.strip()

            ]



            if missing_fields:

                st.warning(

                    "Please complete: "

                    + ", ".join(missing_fields)

                )



            else:

                new_vehicle = {

                    "profile_name": profile_name.strip(),

                    "manufacturer": manufacturer.strip(),

                    "model": model.strip(),

                    "year": int(year),

                    "engine": engine.strip(),

                    "mileage": int(mileage),

                    "modifications": modifications.strip(),

                }



                try:

                    saved_vehicle = add_vehicle(new_vehicle)



                except Exception as error:

                    st.error("The vehicle could not be saved.")

                    st.exception(error)



                else:

                    st.session_state.active_vehicle_id = (

                        saved_vehicle["id"]

                    )



                    st.session_state.messages = []

                    st.session_state.previous_response_id = None



                    st.success(

                        f"Added {saved_vehicle['profile_name']}."

                    )



                    st.rerun()

vehicle_description = None



if active_vehicle:

    vehicle_description = (

        f"Profile name: {active_vehicle['profile_name']}\n"

        f"Year: {active_vehicle['year']}\n"

        f"Manufacturer: {active_vehicle['manufacturer']}\n"

        f"Model: {active_vehicle['model']}\n"

        f"Engine: {active_vehicle['engine']}\n"

        f"Mileage: {active_vehicle['mileage']}\n"

        f"Modifications: "

        f"{active_vehicle['modifications'] or 'Standard or unknown'}"

    )


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


if active_vehicle:

    st.caption(

        f"Currently discussing: "

        f"{active_vehicle['year']} "

        f"{active_vehicle['manufacturer']} "

        f"{active_vehicle['model']}"

    )



else:

    st.info(

        "Add a vehicle in the sidebar for personalised answers."

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

    "Help the user investigate automotive questions and problems. "

    "Do not claim certainty from limited information. "

    "Recommend only safe basic checks. "

    "Clearly state when a vehicle should not be driven or should "

    "be inspected by a qualified mechanic.\n\n"

    "The currently selected vehicle is:\n"

    f"{vehicle_description or 'No vehicle is currently selected.'}\n\n"

    "Use the selected vehicle information whenever it is relevant. "

    "Do not invent missing vehicle details."

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