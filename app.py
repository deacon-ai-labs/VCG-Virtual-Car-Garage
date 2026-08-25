import streamlit as st 

  

from database import ( 

    add_vehicle, 

    delete_vehicle, 

    get_vehicles, 

    update_vehicle, 

) 

from garage_ai import ask_ai 

  

  

st.set_page_config( 

    page_title="Virtual Car Garage", 

    page_icon="🚗", 

) 

  

  

# OpenAI uses this ID to continue the current conversation. 

if "previous_response_id" not in st.session_state: 

    st.session_state.previous_response_id = None 

  

# Streamlit uses this list to display the visible chat history. 

if "messages" not in st.session_state: 

    st.session_state.messages = [] 

  

# The selected vehicle is temporary UI state; Supabase stores the full record. 

if "active_vehicle_id" not in st.session_state: 

    st.session_state.active_vehicle_id = None 

  

  

def reset_conversation() -> None: 

    """Clear the visible and OpenAI-side conversation state.""" 

  

    st.session_state.messages = [] 

    st.session_state.previous_response_id = None 

  

  

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

            index=vehicle_ids.index(st.session_state.active_vehicle_id), 

        ) 

  

        if selected_vehicle_id != st.session_state.active_vehicle_id: 

            st.session_state.active_vehicle_id = selected_vehicle_id 

            reset_conversation() 

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

  

        with st.expander("✏️ Edit active vehicle"): 

            with st.form( 

                f"edit_vehicle_form_{active_vehicle['id']}", 

                clear_on_submit=False, 

            ): 

                edit_profile_name = st.text_input( 

                    "Profile name", 

                    value=active_vehicle["profile_name"], 

                    key=f"edit_profile_name_{active_vehicle['id']}", 

                ) 

  

                edit_manufacturer = st.text_input( 

                    "Manufacturer", 

                    value=active_vehicle["manufacturer"], 

                    key=f"edit_manufacturer_{active_vehicle['id']}", 

                ) 

  

                edit_model = st.text_input( 

                    "Model", 

                    value=active_vehicle["model"], 

                    key=f"edit_model_{active_vehicle['id']}", 

                ) 

  

                edit_year = st.number_input( 

                    "Year", 

                    min_value=1900, 

                    max_value=2100, 

                    step=1, 

                    value=int(active_vehicle["year"]), 

                    key=f"edit_year_{active_vehicle['id']}", 

                ) 

  

                edit_engine = st.text_input( 

                    "Engine", 

                    value=active_vehicle["engine"], 

                    key=f"edit_engine_{active_vehicle['id']}", 

                ) 

  

                edit_mileage = st.number_input( 

                    "Mileage", 

                    min_value=0, 

                    step=1000, 

                    value=int(active_vehicle["mileage"]), 

                    key=f"edit_mileage_{active_vehicle['id']}", 

                ) 

  

                edit_modifications = st.text_area( 

                    "Modifications", 

                    value=active_vehicle["modifications"] or "", 

                    key=f"edit_modifications_{active_vehicle['id']}", 

                ) 

  

                update_submitted = st.form_submit_button( 

                    "Update vehicle", 

                    type="primary", 

                    use_container_width=True, 

                ) 

  

            if update_submitted: 

                required_text_fields = { 

                    "Profile name": edit_profile_name, 

                    "Manufacturer": edit_manufacturer, 

                    "Model": edit_model, 

                    "Engine": edit_engine, 

                } 

  

                missing_fields = [ 

                    field_name 

                    for field_name, field_value 

                    in required_text_fields.items() 

                    if not field_value.strip() 

                ] 

  

                if missing_fields: 

                    st.warning( 

                        "Please complete: " + ", ".join(missing_fields) 

                    ) 

                else: 

                    updated_vehicle_data = { 

                        "profile_name": edit_profile_name.strip(), 

                        "manufacturer": edit_manufacturer.strip(), 

                        "model": edit_model.strip(), 

                        "year": int(edit_year), 

                        "engine": edit_engine.strip(), 

                        "mileage": int(edit_mileage), 

                        "modifications": edit_modifications.strip(), 

                    } 

  

                    try: 

                        update_vehicle( 

                            active_vehicle["id"], 

                            updated_vehicle_data, 

                        ) 

                    except Exception as error: 

                        st.error("The vehicle could not be updated.") 

                        st.exception(error) 

                    else: 

                        reset_conversation() 

                        st.success( 

                            f"Updated " 

                            f"{updated_vehicle_data['profile_name']}." 

                        ) 

                        st.rerun() 

  

        with st.expander("🗑️ Delete active vehicle"): 

            st.warning( 

                f"This will permanently delete " 

                f"{active_vehicle['profile_name']}." 

            ) 

  

            confirm_delete = st.checkbox( 

                "I understand that this cannot be undone.", 

                key=f"confirm_delete_{active_vehicle['id']}", 

            ) 

  

            delete_clicked = st.button( 

                "Delete vehicle", 

                type="primary", 

                use_container_width=True, 

                disabled=not confirm_delete, 

                key=f"delete_vehicle_{active_vehicle['id']}", 

            ) 

  

            if delete_clicked: 

                deleted_vehicle_name = active_vehicle["profile_name"] 

  

                try: 

                    delete_vehicle(active_vehicle["id"]) 

                except Exception as error: 

                    st.error("The vehicle could not be deleted.") 

                    st.exception(error) 

                else: 

                    st.session_state.active_vehicle_id = None 

                    reset_conversation() 

                    st.success(f"Deleted {deleted_vehicle_name}.") 

                    st.rerun() 

  

    st.divider() 

  

    with st.expander("➕ Add another vehicle", expanded=not vehicles): 

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

                for field_name, field_value 

                in required_text_fields.items() 

                if not field_value.strip() 

            ] 

  

            if missing_fields: 

                st.warning( 

                    "Please complete: " + ", ".join(missing_fields) 

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

                    reset_conversation() 

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

  

if active_vehicle: 

    st.caption( 

        f"Currently discussing: " 

        f"{active_vehicle['year']} " 

        f"{active_vehicle['manufacturer']} " 

        f"{active_vehicle['model']}" 

    ) 

else: 

    st.info("Add a vehicle in the sidebar for personalised answers.") 

  

  

# Redisplay all previous messages whenever Streamlit reruns the page. 

for message in st.session_state.messages: 

    with st.chat_message(message["role"]): 

        st.markdown(message["content"]) 

  

  

# This stays at the bottom of the page and clears after submission. 

user_message = st.chat_input( 

    "Describe the problem or answer Garage AI's question..." 

) 

  

  

if user_message: 

    st.session_state.messages.append( 

        { 

            "role": "user", 

            "content": user_message, 

        } 

    ) 

  

    with st.chat_message("user"): 

        st.markdown(user_message) 

  

    with st.chat_message("assistant"): 

        with st.spinner("Garage AI is investigating..."): 

            response = ask_ai( 

                user_message=user_message, 

                vehicle_description=vehicle_description, 

                previous_response_id=( 

                    st.session_state.previous_response_id 

                ), 

            ) 

  

        assistant_message = response.output_text 

        st.markdown(assistant_message) 

  

    st.session_state.previous_response_id = response.id 

  

    st.session_state.messages.append( 

        { 

            "role": "assistant", 

            "content": assistant_message, 

        } 

    ) 