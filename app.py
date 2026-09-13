from pathlib import Path

import streamlit as st

from auth import (
    create_authenticated_client,
    sign_in,
    sign_out,
    sign_up,
)
from dashboard_state import apply_vehicle_selection
from database import (
    add_message,
    add_vehicle,
    create_conversation,
    delete_conversation,
    delete_vehicle,
    get_conversations,
    get_messages,
    get_vehicle_photo_url,
    get_vehicles,
    rename_conversation,
    update_conversation_response_id,
    update_vehicle,
)
from garage_ai import ask_ai
from photo_service import (
    remove_vehicle_photo,
    replace_vehicle_photo,
)
from photo_ui import (
    build_photo_uploader_css,
    photo_upload_token,
)
from time_utils import format_local_timestamp
from ui_theme import (
    apply_dashboard_shell,
    apply_global_theme,
    image_data_uri,
    render_wordmark,
)


st.set_page_config(
    page_title="Virtual Car Garage",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_theme()


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
        "garage_collapsed",
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
    """Show the approved VCG sign-in/create-account experience."""

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }

        [data-testid="stAppViewContainer"] > .main {
            padding-left: 0;
        }

        .block-container {
            padding-top: 1rem;
            max-width: 1700px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    hero_uri = image_data_uri(
        Path("assets/login_hero.png")
    )

    hero_col, auth_col = st.columns(
        [1.72, 0.92],
        gap="large",
        vertical_alignment="top",
    )

    with hero_col:
        st.markdown(
            f"""
            <div class="vcg-login-hero">
                <img
                    src="{hero_uri}"
                    alt="Virtual Car Garage hero"
                />
            </div>
            """,
            unsafe_allow_html=True,
        )

    with auth_col:
        st.markdown(
            '<div class="vcg-auth-shell">',
            unsafe_allow_html=True,
        )

        render_wordmark()

        st.markdown(
            '<div class="vcg-auth-kicker">'
            'Sign in to your garage'
            '</div>',
            unsafe_allow_html=True,
        )

        sign_in_tab, sign_up_tab = st.tabs(
            [
                "Sign In",
                "Create Account",
            ]
        )

        with sign_in_tab:
            with st.form("sign_in_form"):
                email = st.text_input(
                    "Email Address",
                    key="sign_in_email",
                    placeholder="you@yourdomain.com",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    key="sign_in_password",
                    placeholder="Enter your password",
                )

                submitted = st.form_submit_button(
                    "Sign In  →",
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
                    "Email Address",
                    key="sign_up_email",
                    placeholder="you@yourdomain.com",
                )

                new_password = st.text_input(
                    "Password",
                    type="password",
                    key="sign_up_password",
                    placeholder="Create a password",
                    help=(
                        "Use a password that meets your "
                        "Supabase project's password policy."
                    ),
                )

                create_submitted = st.form_submit_button(
                    "Create Account  →",
                    type="primary",
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
                                "Account created. Confirm the "
                                "email before signing in if "
                                "email confirmation is enabled."
                            )

        st.markdown(
            """
            <div class="vcg-auth-note">
                Secure email/password access.
                Social login is intentionally not enabled.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


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


def signed_vehicle_photo(
    client,
    vehicle: dict,
) -> str | None:
    """Return a signed vehicle photo URL when available."""

    photo_path = vehicle.get(
        "photo_path"
    )

    if not photo_path:
        return None

    try:
        return get_vehicle_photo_url(
            client,
            photo_path,
        )
    except Exception:
        return None


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

if "garage_collapsed" not in st.session_state:
    st.session_state.garage_collapsed = False


apply_dashboard_shell()


try:
    browser_timezone = (
        st.context.timezone
        or "UTC"
    )
except Exception:
    browser_timezone = "UTC"


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


vehicle_ids = [
    vehicle["id"]
    for vehicle in vehicles
]

if (
    st.session_state.active_vehicle_id
    not in vehicle_ids
):
    st.session_state.active_vehicle_id = (
        vehicle_ids[0]
        if vehicle_ids
        else None
    )
    st.session_state.active_conversation_id = None


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


conversation_ids = [
    conversation["id"]
    for conversation in conversations
]

if (
    st.session_state.active_conversation_id
    is not None
    and st.session_state.active_conversation_id
    not in conversation_ids
):
    st.session_state.active_conversation_id = None


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


# ---------- top bar ----------
top_brand, top_account = st.columns(
    [4.8, 2.2],
    gap="large",
    vertical_alignment="center",
)

with top_brand:
    render_wordmark()

with top_account:
    account_text, signout_col = st.columns(
        [2.3, 1],
        vertical_alignment="center",
    )

    with account_text:
        st.caption(
            "Signed in as"
        )
        st.markdown(
            f"**{st.session_state.auth_user_email}**"
        )

    with signout_col:
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

st.markdown(
    '<div class="vcg-top-divider"></div>',
    unsafe_allow_html=True,
)


# ---------- dashboard columns ----------
if st.session_state.garage_collapsed:
    layout = [0.58, 7.05, 3.2]
else:
    layout = [2.45, 6.55, 3.2]

garage_col, chat_col, vehicle_col = st.columns(
    layout,
    gap="medium",
    vertical_alignment="top",
)


# ---------- left garage rail ----------
with garage_col:
    with st.container(key="vcg_garage_scroll"):
        if st.session_state.garage_collapsed:
            if st.button(
                "»",
                key="expand_garage",
                help="Expand My Garage",
                use_container_width=True,
            ):
                st.session_state.garage_collapsed = False
                st.rerun()

            for vehicle in vehicles:
                is_active = (
                    vehicle["id"]
                    == st.session_state.active_vehicle_id
                )

                if st.button(
                    "🚗",
                    key=f"collapsed_vehicle_{vehicle['id']}",
                    help=vehicle["profile_name"],
                    type=(
                        "primary"
                        if is_active
                        else "secondary"
                    ),
                    use_container_width=True,
                ):
                    new_state = apply_vehicle_selection(
                        st.session_state.active_vehicle_id,
                        vehicle["id"],
                        st.session_state.active_conversation_id,
                    )
                    st.session_state.update(
                        new_state
                    )
                    st.rerun()

        else:
            garage_header, collapse_col = st.columns(
                [4, 1],
                vertical_alignment="center",
            )

            with garage_header:
                st.markdown(
                    "### 🏠 My Garage"
                )
                st.caption(
                    f"{len(vehicles)} vehicle"
                    f"{'' if len(vehicles) == 1 else 's'}"
                )

            with collapse_col:
                if st.button(
                    "‹",
                    key="collapse_garage",
                    help="Collapse My Garage",
                    use_container_width=True,
                ):
                    st.session_state.garage_collapsed = True
                    st.rerun()

            for vehicle in vehicles:
                is_active = (
                    vehicle["id"]
                    == st.session_state.active_vehicle_id
                )

                with st.container(
                    border=True,
                ):
                    photo_url = signed_vehicle_photo(
                        supabase,
                        vehicle,
                    )

                    if photo_url:
                        st.image(
                            photo_url,
                            use_container_width=True,
                        )
                    else:
                        st.markdown(
                            """
                            <div class="vcg-photo-placeholder vcg-photo-small">
                                <span>🚘</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        f"**{vehicle['profile_name']}**"
                    )
                    st.caption(
                        f"{vehicle['year']} · "
                        f"{vehicle['manufacturer']} "
                        f"{vehicle['model']}"
                    )

                    if st.button(
                        (
                            "Active Vehicle"
                            if is_active
                            else "Open Garage"
                        ),
                        key=f"vehicle_card_{vehicle['id']}",
                        type=(
                            "primary"
                            if is_active
                            else "secondary"
                        ),
                        use_container_width=True,
                    ):
                        new_state = apply_vehicle_selection(
                            st.session_state.active_vehicle_id,
                            vehicle["id"],
                            st.session_state.active_conversation_id,
                        )
                        st.session_state.update(
                            new_state
                        )
                        st.rerun()

            with st.expander(
                "＋ Add vehicle",
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

                    add_submitted = (
                        st.form_submit_button(
                            "Save vehicle",
                            type="primary",
                            use_container_width=True,
                        )
                    )

                if add_submitted:
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
                            "profile_name": profile_name.strip(),
                            "manufacturer": manufacturer.strip(),
                            "model": model.strip(),
                            "year": int(year),
                            "engine": engine.strip(),
                            "mileage": int(mileage),
                            "modifications": modifications.strip(),
                        }

                        try:
                            saved_vehicle = add_vehicle(
                                supabase,
                                st.session_state.auth_user_id,
                                new_vehicle,
                            )
                        except Exception as error:
                            st.error(
                                "The vehicle could not be saved."
                            )
                            st.exception(error)
                        else:
                            st.session_state.active_vehicle_id = (
                                saved_vehicle["id"]
                            )
                            st.session_state.active_conversation_id = None
                            st.rerun()

            st.markdown(
                "#### 💬 Conversations"
            )

            if conversations:
                for conversation in conversations:
                    conversation_id = (
                        conversation["id"]
                    )

                    title = (
                        conversation.get("title")
                        or "Conversation"
                    )

                    local_time = format_local_timestamp(
                        conversation.get("updated_at"),
                        browser_timezone,
                    )

                    button_label = title

                    if local_time:
                        button_label += (
                            f" · {local_time}"
                        )

                    is_active_conversation = (
                        conversation_id
                        == st.session_state.active_conversation_id
                    )

                    if st.button(
                        button_label,
                        key=f"conversation_{conversation_id}",
                        type=(
                            "primary"
                            if is_active_conversation
                            else "secondary"
                        ),
                        use_container_width=True,
                    ):
                        st.session_state.active_conversation_id = (
                            conversation_id
                        )
                        st.rerun()

                if active_conversation:
                    with st.expander(
                        "Manage current conversation"
                    ):
                        with st.form(
                            "rename_conversation_form"
                        ):
                            new_title = st.text_input(
                                "Conversation name",
                                value=active_conversation["title"],
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
                                rename_conversation(
                                    supabase,
                                    active_conversation["id"],
                                    new_title,
                                )
                                st.rerun()

                        confirm_delete_conversation = st.checkbox(
                            "Confirm permanent delete",
                            key=(
                                "confirm_delete_conversation_"
                                f"{active_conversation['id']}"
                            ),
                        )

                        if st.button(
                            "Delete conversation",
                            key=(
                                "delete_conversation_"
                                f"{active_conversation['id']}"
                            ),
                            disabled=not confirm_delete_conversation,
                            use_container_width=True,
                        ):
                            delete_conversation(
                                supabase,
                                active_conversation["id"],
                            )
                            st.session_state.active_conversation_id = None
                            st.rerun()

            else:
                st.caption(
                    "No saved conversations yet."
                )



# ---------- centre Garage AI ----------
with chat_col:
    st.markdown(
        """
        <div class="vcg-section-heading">
            <div>
                <div class="vcg-section-kicker">AI CO-PILOT</div>
                <div class="vcg-section-title">Garage AI</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if active_vehicle:
        st.caption(
            f"Discussing {active_vehicle['year']} "
            f"{active_vehicle['manufacturer']} "
            f"{active_vehicle['model']}"
        )

    with st.container(
        key="vcg_chat_scroll",
    ):
        if active_conversation:
            st.markdown(
                f"#### {active_conversation['title']}"
            )

        for message in messages:
            with st.chat_message(
                message["role"]
            ):
                st.markdown(
                    message["content"]
                )

    user_message = st.chat_input(
        (
            "Ask Garage AI about this vehicle..."
            if active_vehicle
            else "Add a vehicle to start chatting..."
        ),
        disabled=active_vehicle is None,
    )

    if user_message and active_vehicle:
        if active_conversation is None:
            try:
                active_conversation = create_conversation(
                    supabase,
                    st.session_state.auth_user_id,
                    active_vehicle["id"],
                    make_conversation_title(
                        user_message
                    ),
                )
            except Exception as error:
                st.error(
                    "The conversation could not be created."
                )
                st.exception(error)
                st.stop()

            st.session_state.active_conversation_id = (
                active_conversation["id"]
            )

            messages = []

        try:
            add_message(
                supabase,
                st.session_state.auth_user_id,
                active_conversation["id"],
                "user",
                user_message,
            )
        except Exception as error:
            st.error(
                "Your message could not be saved."
            )
            st.exception(error)
            st.stop()

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

        with st.spinner(
            "Garage AI is investigating..."
        ):
            try:
                response = ask_ai(
                    user_message=user_message,
                    vehicle_description=vehicle_description,
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
                "could not be saved."
            )
            st.exception(error)
            st.stop()

        st.rerun()


# ---------- right active vehicle ----------
with vehicle_col:
    with st.container(key="vcg_vehicle_scroll"):
        st.markdown(
            """
            <div class="vcg-section-kicker">ACTIVE VEHICLE</div>
            """,
            unsafe_allow_html=True,
        )

        if active_vehicle:
            st.markdown(
                f"### {active_vehicle['year']} "
                f"{active_vehicle['manufacturer']} "
                f"{active_vehicle['model']}"
            )

            active_photo_url = signed_vehicle_photo(
                supabase,
                active_vehicle,
            )

            photo_version_key = (
                "photo_uploader_version_"
                f"{active_vehicle['id']}"
            )

            if photo_version_key not in st.session_state:
                st.session_state[photo_version_key] = 0

            photo_widget_key = (
                "active_vehicle_photo_"
                f"{active_vehicle['id']}_"
                f"{st.session_state[photo_version_key]}"
            )

            st.markdown(
                build_photo_uploader_css(
                    photo_widget_key,
                    active_photo_url,
                ),
                unsafe_allow_html=True,
            )

            uploaded_photo = st.file_uploader(
                "Vehicle photo",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                    "webp",
                ],
                key=photo_widget_key,
                label_visibility="collapsed",
                help=(
                    "Click the image to add or replace "
                    "the vehicle photo."
                ),
            )

            processed_photo_key = (
                "processed_photo_upload_"
                f"{active_vehicle['id']}"
            )

            if uploaded_photo is not None:
                upload_token = photo_upload_token(
                    uploaded_photo
                )

                if (
                    st.session_state.get(
                        processed_photo_key
                    )
                    != upload_token
                ):
                    try:
                        replace_vehicle_photo(
                            client=supabase,
                            owner_id=(
                                st.session_state
                                .auth_user_id
                            ),
                            vehicle_id=(
                                active_vehicle["id"]
                            ),
                            old_photo_path=(
                                active_vehicle.get(
                                    "photo_path"
                                )
                            ),
                            filename=(
                                uploaded_photo.name
                            ),
                            file_bytes=(
                                uploaded_photo.getvalue()
                            ),
                            content_type=(
                                uploaded_photo.type
                                or "image/jpeg"
                            ),
                        )
                    except Exception as error:
                        st.error(
                            "The vehicle photo could "
                            "not be saved."
                        )
                        st.exception(error)
                    else:
                        st.session_state[
                            processed_photo_key
                        ] = upload_token
                        st.rerun()

            if active_vehicle.get("photo_path"):
                if st.button(
                    "Remove photo",
                    key=(
                        "remove_active_vehicle_photo_"
                        f"{active_vehicle['id']}"
                    ),
                    help=(
                        "Remove the current vehicle photo."
                    ),
                    use_container_width=True,
                ):
                    try:
                        remove_vehicle_photo(
                            client=supabase,
                            vehicle_id=(
                                active_vehicle["id"]
                            ),
                            photo_path=(
                                active_vehicle.get(
                                    "photo_path"
                                )
                            ),
                        )
                    except Exception as error:
                        st.error(
                            "The vehicle photo could "
                            "not be removed."
                        )
                        st.exception(error)
                    else:
                        st.session_state[
                            photo_version_key
                        ] += 1
                        st.session_state.pop(
                            processed_photo_key,
                            None,
                        )
                        st.rerun()

            stat1, stat2 = st.columns(2)

            with stat1:
                st.metric(
                    "Year",
                    active_vehicle["year"],
                    border=True,
                )
                st.metric(
                    "Mileage",
                    f"{active_vehicle['mileage']:,}",
                    border=True,
                )

            with stat2:
                st.metric(
                    "Engine",
                    active_vehicle["engine"],
                    border=True,
                )
                st.metric(
                    "Profile",
                    active_vehicle["profile_name"],
                    border=True,
                )

            st.markdown(
                "#### 🔧 Modifications & Build Notes"
            )

            if active_vehicle["modifications"]:
                st.write(
                    active_vehicle["modifications"]
                )
            else:
                st.caption(
                    "No modifications recorded yet."
                )

            with st.expander(
                "Edit vehicle"
            ):
                with st.form(
                    f"edit_vehicle_form_{active_vehicle['id']}",
                    clear_on_submit=False,
                ):
                    edit_profile_name = st.text_input(
                        "Profile name",
                        value=active_vehicle["profile_name"],
                    )
                    edit_manufacturer = st.text_input(
                        "Manufacturer",
                        value=active_vehicle["manufacturer"],
                    )
                    edit_model = st.text_input(
                        "Model",
                        value=active_vehicle["model"],
                    )
                    edit_year = st.number_input(
                        "Year",
                        min_value=1900,
                        max_value=2100,
                        step=1,
                        value=int(active_vehicle["year"]),
                    )
                    edit_engine = st.text_input(
                        "Engine",
                        value=active_vehicle["engine"],
                    )
                    edit_mileage = st.number_input(
                        "Mileage",
                        min_value=0,
                        step=1000,
                        value=int(active_vehicle["mileage"]),
                    )
                    edit_modifications = st.text_area(
                        "Modifications",
                        value=(
                            active_vehicle["modifications"]
                            or ""
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
                    updated_vehicle_data = {
                        "profile_name": edit_profile_name.strip(),
                        "manufacturer": edit_manufacturer.strip(),
                        "model": edit_model.strip(),
                        "year": int(edit_year),
                        "engine": edit_engine.strip(),
                        "mileage": int(edit_mileage),
                        "modifications": edit_modifications.strip(),
                    }

                    required_values = [
                        updated_vehicle_data["profile_name"],
                        updated_vehicle_data["manufacturer"],
                        updated_vehicle_data["model"],
                        updated_vehicle_data["engine"],
                    ]

                    if not all(required_values):
                        st.warning(
                            "Profile name, manufacturer, model "
                            "and engine are required."
                        )
                    else:
                        try:
                            update_vehicle(
                                supabase,
                                active_vehicle["id"],
                                updated_vehicle_data,
                            )
                        except Exception as error:
                            st.error(
                                "The vehicle could not be updated."
                            )
                            st.exception(error)
                        else:
                            st.rerun()

            with st.expander(
                "Delete vehicle"
            ):
                st.warning(
                    "This permanently deletes the vehicle "
                    "and its related conversations."
                )

                confirm_delete = st.checkbox(
                    "Confirm permanent delete",
                    key=f"confirm_delete_vehicle_{active_vehicle['id']}",
                )

                if st.button(
                    "Delete vehicle",
                    key=f"delete_vehicle_{active_vehicle['id']}",
                    disabled=not confirm_delete,
                    use_container_width=True,
                ):
                    try:
                        delete_vehicle(
                            supabase,
                            active_vehicle["id"],
                        )
                    except Exception as error:
                        st.error(
                            "The vehicle could not be deleted."
                        )
                        st.exception(error)
                    else:
                        st.session_state.active_vehicle_id = None
                        st.session_state.active_conversation_id = None
                        st.rerun()

            st.markdown(
                """
                <div class="vcg-maintenance-shell">
                    <div class="vcg-maintenance-title">
                        🔧 Maintenance Checklist
                    </div>
                    <div class="vcg-maintenance-empty">
                        Maintenance tracking is ready for the next phase.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.info(
                "Add a vehicle to populate the active vehicle panel."
            )
