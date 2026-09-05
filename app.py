import streamlit as st

from auth import (
    create_authenticated_client,
    sign_in,
    sign_out,
    sign_up,
)
from database import (
    add_message,
    add_vehicle,
    create_conversation,
    delete_conversation,
    delete_vehicle,
    get_conversations,
    get_messages,
    get_vehicles,
    rename_conversation,
    update_conversation_response_id,
    update_vehicle,
)
from garage_ai import ask_ai


st.set_page_config(
    page_title="Virtual Car Garage",
    page_icon="🚗",
)


AUTH_STATE_KEYS = (
    "auth_access_token",
    "auth_refresh_token",
    "auth_user_id",
    "auth_user_email",
)


def clear_app_session() -> None:
    """Clear user-specific Streamlit state."""

    keys_to_clear = (
        *AUTH_STATE_KEYS,
        "active_vehicle_id",
        "active_conversation_id",
    )

    for key in keys_to_clear:
        st.session_state.pop(
            key,
            None,
        )


def store_auth_session(auth_response) -> bool:
    """Save a successful Supabase auth response in Session State."""

    if (
        auth_response is None
        or auth_response.user is None
        or auth_response.session is None
    ):
        return False

    st.session_state.auth_access_token = (
        auth_response.session.access_token
    )

    st.session_state.auth_refresh_token = (
        auth_response.session.refresh_token
    )

    st.session_state.auth_user_id = str(
        auth_response.user.id
    )

    st.session_state.auth_user_email = (
        auth_response.user.email or ""
    )

    return True


def show_auth_screen() -> None:
    """Show sign-in and account-creation forms."""

    st.title("🚗 Virtual Car Garage")

    st.write(
        "Sign in to access your vehicles and Garage AI."
    )

    sign_in_tab, sign_up_tab = st.tabs(
        [
            "Sign in",
            "Create account",
        ]
    )

    with sign_in_tab:
        with st.form("sign_in_form"):
            email = st.text_input(
                "Email",
                key="sign_in_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                key="sign_in_password",
            )

            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not email.strip() or not password:
                st.warning(
                    "Enter both email and password."
                )
            else:
                try:
                    response = sign_in(
                        email.strip(),
                        password,
                    )
                except Exception:
                    st.error(
                        "Sign in failed. Check your email "
                        "and password and try again."
                    )
                else:
                    if store_auth_session(response):
                        st.rerun()
                    else:
                        st.error(
                            "Supabase did not return an "
                            "authenticated session."
                        )

    with sign_up_tab:
        with st.form("sign_up_form"):
            new_email = st.text_input(
                "Email",
                key="sign_up_email",
            )

            new_password = st.text_input(
                "Password",
                type="password",
                key="sign_up_password",
                help=(
                    "Use a password that meets your "
                    "Supabase project's password policy."
                ),
            )

            create_submitted = st.form_submit_button(
                "Create account",
                use_container_width=True,
            )

        if create_submitted:
            if not new_email.strip() or not new_password:
                st.warning(
                    "Enter both email and password."
                )
            else:
                try:
                    response = sign_up(
                        new_email.strip(),
                        new_password,
                    )
                except Exception as error:
                    st.error(
                        f"Account creation failed: {error}"
                    )
                else:
                    if store_auth_session(response):
                        st.success(
                            "Account created and signed in."
                        )
                        st.rerun()
                    else:
                        st.success(
                            "Account created. If email confirmation "
                            "is enabled in Supabase, confirm the "
                            "email before signing in."
                        )


for key in AUTH_STATE_KEYS:
    if key not in st.session_state:
        st.session_state[key] = None


if (
    not st.session_state.auth_access_token
    or not st.session_state.auth_refresh_token
    or not st.session_state.auth_user_id
):
    show_auth_screen()
    st.stop()


try:
    supabase = create_authenticated_client(
        st.session_state.auth_access_token,
        st.session_state.auth_refresh_token,
    )

    current_session = (
        supabase.auth.get_session()
    )

    if current_session is not None:
        st.session_state.auth_access_token = (
            current_session.access_token
        )
        st.session_state.auth_refresh_token = (
            current_session.refresh_token
        )

except Exception:
    clear_app_session()

    st.warning(
        "Your sign-in session has expired. "
        "Please sign in again."
    )

    show_auth_screen()
    st.stop()


if "active_vehicle_id" not in st.session_state:
    st.session_state.active_vehicle_id = None

if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None


def make_conversation_title(
    first_message: str,
    max_length: int = 55,
) -> str:
    """Create a useful, zero-cost title from the first user message."""

    title = " ".join(
        first_message.strip().split()
    )

    if not title:
        return "New conversation"

    if len(title) <= max_length:
        return title

    return (
        title[: max_length - 1].rstrip()
        + "…"
    )


try:
    vehicles = get_vehicles(
        supabase
    )
except Exception as error:
    st.error(
        "Virtual Car Garage could not load "
        "your vehicle database."
    )
    st.exception(error)
    st.stop()


with st.sidebar:
    st.header("🚗 My Garage")

    if st.session_state.auth_user_email:
        st.caption(
            f"Signed in as "
            f"{st.session_state.auth_user_email}"
        )

    if st.button(
        "Sign out",
        use_container_width=True,
    ):
        try:
            sign_out(
                supabase
            )
        except Exception:
            pass

        clear_app_session()
        st.rerun()

    st.divider()

    if vehicles:
        vehicle_options = {
            vehicle["id"]: vehicle["profile_name"]
            for vehicle in vehicles
        }

        vehicle_ids = list(
            vehicle_options.keys()
        )

        if (
            st.session_state.active_vehicle_id
            not in vehicle_ids
        ):
            st.session_state.active_vehicle_id = (
                vehicle_ids[0]
            )

        selected_vehicle_id = st.selectbox(
            "Active vehicle",
            options=vehicle_ids,
            format_func=lambda vehicle_id: (
                vehicle_options[vehicle_id]
            ),
            index=vehicle_ids.index(
                st.session_state.active_vehicle_id
            ),
        )

        if (
            selected_vehicle_id
            != st.session_state.active_vehicle_id
        ):
            st.session_state.active_vehicle_id = (
                selected_vehicle_id
            )
            st.session_state.active_conversation_id = None
            st.rerun()

    else:
        selected_vehicle_id = None
        st.session_state.active_vehicle_id = None
        st.session_state.active_conversation_id = None

        st.info(
            "No vehicles have been added yet."
        )


active_vehicle = None

if st.session_state.active_vehicle_id is not None:
    active_vehicle = next(
        (
            vehicle
            for vehicle in vehicles
            if vehicle["id"]
            == st.session_state.active_vehicle_id
        ),
        None,
    )


conversations = []

if active_vehicle:
    try:
        conversations = get_conversations(
            supabase,
            active_vehicle["id"],
        )
    except Exception as error:
        st.error(
            "Virtual Car Garage could not load "
            "conversation history."
        )
        st.exception(error)
        st.stop()


with st.sidebar:
    if active_vehicle:
        st.divider()
        st.subheader(
            active_vehicle["profile_name"]
        )

        st.write(
            f"**Vehicle:** "
            f"{active_vehicle['year']} "
            f"{active_vehicle['manufacturer']} "
            f"{active_vehicle['model']}"
        )

        st.write(
            f"**Engine:** "
            f"{active_vehicle['engine']}"
        )

        st.write(
            f"**Mileage:** "
            f"{active_vehicle['mileage']:,}"
        )

        if active_vehicle["modifications"]:
            st.write(
                "**Modifications:**"
            )
            st.write(
                active_vehicle["modifications"]
            )

        with st.expander(
            "✏️ Edit active vehicle"
        ):
            with st.form(
                f"edit_vehicle_form_"
                f"{active_vehicle['id']}",
                clear_on_submit=False,
            ):
                edit_profile_name = st.text_input(
                    "Profile name",
                    value=active_vehicle[
                        "profile_name"
                    ],
                    key=(
                        "edit_profile_name_"
                        f"{active_vehicle['id']}"
                    ),
                )

                edit_manufacturer = st.text_input(
                    "Manufacturer",
                    value=active_vehicle[
                        "manufacturer"
                    ],
                    key=(
                        "edit_manufacturer_"
                        f"{active_vehicle['id']}"
                    ),
                )

                edit_model = st.text_input(
                    "Model",
                    value=active_vehicle["model"],
                    key=(
                        "edit_model_"
                        f"{active_vehicle['id']}"
                    ),
                )

                edit_year = st.number_input(
                    "Year",
                    min_value=1900,
                    max_value=2100,
                    step=1,
                    value=int(
                        active_vehicle["year"]
                    ),
                    key=(
                        "edit_year_"
                        f"{active_vehicle['id']}"
                    ),
                )

                edit_engine = st.text_input(
                    "Engine",
                    value=active_vehicle["engine"],
                    key=(
                        "edit_engine_"
                        f"{active_vehicle['id']}"
                    ),
                )

                edit_mileage = st.number_input(
                    "Mileage",
                    min_value=0,
                    step=1000,
                    value=int(
                        active_vehicle["mileage"]
                    ),
                    key=(
                        "edit_mileage_"
                        f"{active_vehicle['id']}"
                    ),
                )

                edit_modifications = st.text_area(
                    "Modifications",
                    value=(
                        active_vehicle[
                            "modifications"
                        ]
                        or ""
                    ),
                    key=(
                        "edit_modifications_"
                        f"{active_vehicle['id']}"
                    ),
                )

                update_submitted = (
                    st.form_submit_button(
                        "Update vehicle",
                        type="primary",
                        use_container_width=True,
                    )
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
                    for (
                        field_name,
                        field_value,
                    )
                    in required_text_fields.items()
                    if not field_value.strip()
                ]

                if missing_fields:
                    st.warning(
                        "Please complete: "
                        + ", ".join(
                            missing_fields
                        )
                    )
                else:
                    updated_vehicle_data = {
                        "profile_name": (
                            edit_profile_name
                            .strip()
                        ),
                        "manufacturer": (
                            edit_manufacturer
                            .strip()
                        ),
                        "model": (
                            edit_model.strip()
                        ),
                        "year": int(
                            edit_year
                        ),
                        "engine": (
                            edit_engine.strip()
                        ),
                        "mileage": int(
                            edit_mileage
                        ),
                        "modifications": (
                            edit_modifications
                            .strip()
                        ),
                    }

                    try:
                        update_vehicle(
                            supabase,
                            active_vehicle["id"],
                            updated_vehicle_data,
                        )
                    except Exception as error:
                        st.error(
                            "The vehicle could "
                            "not be updated."
                        )
                        st.exception(error)
                    else:
                        st.success(
                            f"Updated "
                            f"{updated_vehicle_data['profile_name']}."
                        )
                        st.rerun()

        with st.expander(
            "🗑️ Delete active vehicle"
        ):
            st.warning(
                f"This will permanently delete "
                f"{active_vehicle['profile_name']}."
            )

            confirm_delete = st.checkbox(
                "I understand that this cannot "
                "be undone.",
                key=(
                    "confirm_delete_"
                    f"{active_vehicle['id']}"
                ),
            )

            delete_clicked = st.button(
                "Delete vehicle",
                type="primary",
                use_container_width=True,
                disabled=not confirm_delete,
                key=(
                    "delete_vehicle_"
                    f"{active_vehicle['id']}"
                ),
            )

            if delete_clicked:
                deleted_vehicle_name = (
                    active_vehicle[
                        "profile_name"
                    ]
                )

                try:
                    delete_vehicle(
                        supabase,
                        active_vehicle["id"],
                    )
                except Exception as error:
                    st.error(
                        "The vehicle could "
                        "not be deleted."
                    )
                    st.exception(error)
                else:
                    st.session_state.active_vehicle_id = None
                    st.session_state.active_conversation_id = None

                    st.success(
                        f"Deleted "
                        f"{deleted_vehicle_name}."
                    )

                    st.rerun()

        st.divider()
        st.subheader("💬 Conversations")

        if st.button(
            "➕ New conversation",
            use_container_width=True,
        ):
            try:
                new_conversation = create_conversation(
                    supabase,
                    st.session_state.auth_user_id,
                    active_vehicle["id"],
                    "New conversation",
                )
            except Exception as error:
                st.error(
                    "The conversation could not be created."
                )
                st.exception(error)
            else:
                st.session_state.active_conversation_id = (
                    new_conversation["id"]
                )
                st.rerun()

        if conversations:
            conversation_ids = [
                conversation["id"]
                for conversation in conversations
            ]

            if (
                st.session_state.active_conversation_id
                not in conversation_ids
            ):
                st.session_state.active_conversation_id = (
                    conversation_ids[0]
                )

            for conversation in conversations:
                conversation_id = conversation["id"]
                title = (
                    conversation.get("title")
                    or "New conversation"
                )

                created_at = (
                    conversation.get("created_at")
                    or ""
                )

                date_label = ""

                if len(created_at) >= 16:
                    date_label = (
                        f" · {created_at[8:10]}/"
                        f"{created_at[5:7]} "
                        f"{created_at[11:16]}"
                    )

                is_active = (
                    conversation_id
                    == st.session_state.active_conversation_id
                )

                button_label = (
                    f"{'▶ ' if is_active else ''}"
                    f"{title}{date_label}"
                )

                if st.button(
                    button_label,
                    key=f"conversation_{conversation_id}",
                    use_container_width=True,
                    type=(
                        "primary"
                        if is_active
                        else "secondary"
                    ),
                ):
                    st.session_state.active_conversation_id = (
                        conversation_id
                    )
                    st.rerun()

            active_sidebar_conversation = next(
                (
                    conversation
                    for conversation in conversations
                    if conversation["id"]
                    == st.session_state.active_conversation_id
                ),
                None,
            )

            if active_sidebar_conversation:
                with st.expander(
                    "✏️ Rename conversation"
                ):
                    with st.form(
                        "rename_conversation_form"
                    ):
                        new_title = st.text_input(
                            "Conversation name",
                            value=(
                                active_sidebar_conversation[
                                    "title"
                                ]
                            ),
                        )

                        rename_submitted = (
                            st.form_submit_button(
                                "Rename",
                                use_container_width=True,
                            )
                        )

                    if rename_submitted:
                        if not new_title.strip():
                            st.warning(
                                "Conversation name cannot be empty."
                            )
                        else:
                            try:
                                rename_conversation(
                                    supabase,
                                    active_sidebar_conversation["id"],
                                    new_title,
                                )
                            except Exception as error:
                                st.error(
                                    "The conversation could not "
                                    "be renamed."
                                )
                                st.exception(error)
                            else:
                                st.success(
                                    "Conversation renamed."
                                )
                                st.rerun()

                with st.expander(
                    "🗑️ Delete conversation"
                ):
                    st.warning(
                        "This permanently deletes this "
                        "conversation and all of its messages."
                    )

                    confirm_delete_conversation = st.checkbox(
                        "I understand this cannot be undone.",
                        key=(
                            "confirm_delete_conversation_"
                            f"{active_sidebar_conversation['id']}"
                        ),
                    )

                    if st.button(
                        "Delete conversation",
                        key=(
                            "delete_conversation_"
                            f"{active_sidebar_conversation['id']}"
                        ),
                        disabled=not confirm_delete_conversation,
                        use_container_width=True,
                    ):
                        deleted_id = (
                            active_sidebar_conversation["id"]
                        )

                        try:
                            delete_conversation(
                                supabase,
                                deleted_id,
                            )
                        except Exception as error:
                            st.error(
                                "The conversation could not "
                                "be deleted."
                            )
                            st.exception(error)
                        else:
                            remaining_ids = [
                                conversation["id"]
                                for conversation in conversations
                                if conversation["id"] != deleted_id
                            ]

                            st.session_state.active_conversation_id = (
                                remaining_ids[0]
                                if remaining_ids
                                else None
                            )

                            st.rerun()

        else:
            st.session_state.active_conversation_id = None

            st.caption(
                "No conversations yet. "
                "Start a new one above."
            )

    st.divider()

    with st.expander(
        "➕ Add another vehicle",
        expanded=not vehicles,
    ):
        with st.form(
            "add_vehicle_form",
            clear_on_submit=True,
        ):
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

            submitted = (
                st.form_submit_button(
                    "Save vehicle",
                    type="primary",
                    use_container_width=True,
                )
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
                for (
                    field_name,
                    field_value,
                )
                in required_text_fields.items()
                if not field_value.strip()
            ]

            if missing_fields:
                st.warning(
                    "Please complete: "
                    + ", ".join(
                        missing_fields
                    )
                )
            else:
                new_vehicle = {
                    "profile_name": (
                        profile_name.strip()
                    ),
                    "manufacturer": (
                        manufacturer.strip()
                    ),
                    "model": model.strip(),
                    "year": int(year),
                    "engine": engine.strip(),
                    "mileage": int(mileage),
                    "modifications": (
                        modifications.strip()
                    ),
                }

                try:
                    saved_vehicle = add_vehicle(
                        supabase,
                        st.session_state.auth_user_id,
                        new_vehicle,
                    )
                except Exception as error:
                    st.error(
                        "The vehicle could "
                        "not be saved."
                    )
                    st.exception(error)
                else:
                    st.session_state.active_vehicle_id = (
                        saved_vehicle["id"]
                    )
                    st.session_state.active_conversation_id = None

                    st.success(
                        f"Added "
                        f"{saved_vehicle['profile_name']}."
                    )

                    st.rerun()


vehicle_description = None

if active_vehicle:
    vehicle_description = (
        f"Profile name: "
        f"{active_vehicle['profile_name']}\n"
        f"Year: {active_vehicle['year']}\n"
        f"Manufacturer: "
        f"{active_vehicle['manufacturer']}\n"
        f"Model: {active_vehicle['model']}\n"
        f"Engine: {active_vehicle['engine']}\n"
        f"Mileage: "
        f"{active_vehicle['mileage']}\n"
        f"Modifications: "
        f"{active_vehicle['modifications'] or 'Standard or unknown'}"
    )


active_conversation = None

if st.session_state.active_conversation_id:
    active_conversation = next(
        (
            conversation
            for conversation in conversations
            if conversation["id"]
            == st.session_state.active_conversation_id
        ),
        None,
    )


messages = []

if active_conversation:
    try:
        messages = get_messages(
            supabase,
            active_conversation["id"],
        )
    except Exception as error:
        st.error(
            "Virtual Car Garage could not load messages."
        )
        st.exception(error)
        st.stop()


st.title("🚗 Virtual Car Garage")

st.write(
    "Describe a problem with your vehicle and Garage AI "
    "will help you investigate it."
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
        "Add a vehicle in the sidebar "
        "for personalised answers."
    )


if active_conversation:
    st.subheader(
        active_conversation["title"]
    )

    for message in messages:
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )
else:
    st.info(
        "Create a conversation in the sidebar "
        "to start chatting with Garage AI."
    )


user_message = st.chat_input(
    "Describe the problem or answer "
    "Garage AI's question...",
    disabled=active_conversation is None,
)


if user_message and active_conversation:
    try:
        add_message(
            supabase,
            st.session_state.auth_user_id,
            active_conversation["id"],
            "user",
            user_message,
        )

        if (
            active_conversation.get("title")
            == "New conversation"
            and not messages
        ):
            rename_conversation(
                supabase,
                active_conversation["id"],
                make_conversation_title(
                    user_message
                ),
            )

    except Exception as error:
        st.error(
            "Your message could not be saved."
        )
        st.exception(error)
        st.stop()

    with st.chat_message("user"):
        st.markdown(
            user_message
        )

    with st.chat_message("assistant"):
        with st.spinner(
            "Garage AI is investigating..."
        ):
            try:
                response = ask_ai(
                    user_message=user_message,
                    vehicle_description=(
                        vehicle_description
                    ),
                    previous_response_id=(
                        active_conversation[
                            "last_response_id"
                        ]
                    ),
                )
            except Exception as error:
                st.error(
                    "Garage AI could not complete the response."
                )
                st.exception(error)
                st.stop()

        assistant_message = (
            response.output_text
        )

        st.markdown(
            assistant_message
        )

    try:
        add_message(
            supabase,
            st.session_state.auth_user_id,
            active_conversation["id"],
            "assistant",
            assistant_message,
        )

        update_conversation_response_id(
            supabase,
            active_conversation["id"],
            response.id,
        )

    except Exception as error:
        st.error(
            "Garage AI answered, but the response "
            "could not be saved to conversation history."
        )
        st.exception(error)
        st.stop()

    st.rerun()
