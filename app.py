from html import escape
from pathlib import Path

import streamlit as st

from auth import (
    create_authenticated_client,
    sign_in,
    sign_out,
    sign_up,
    user_auth_error_message,
)
from build_planner import (
    build_plan_snapshot,
    format_build_plan_context,
)
from build_planner_ui import render_build_planner
from dashboard_state import apply_vehicle_selection
from dashboard_view import modification_items
from digital_twin import (
    build_snapshot,
    format_build_context,
    twin_snapshot,
)
from database import (
    add_message,
    add_vehicle,
    add_vehicle_component,
    add_vehicle_component_event,
    create_conversation,
    delete_conversation,
    delete_vehicle,
    get_build_plan_items,
    get_conversations,
    get_messages,
    get_maintenance_items,
    get_maintenance_records,
    get_vehicle_components,
    get_vehicle_photo_url,
    get_vehicle_specifications,
    get_vehicles,
    rename_conversation,
    update_conversation_response_id,
    update_vehicle,
    update_vehicle_component,
)
from garage_ai import ask_ai
from maintenance_os import (
    maintenance_due_label,
    maintenance_health_snapshot,
)
from maintenance_ui import render_maintenance_os
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
from virtual_workshop_ui import render_virtual_workshop


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
                    width="stretch",
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
                    except Exception as error:
                        st.error(
                            user_auth_error_message(
                                error,
                                action="sign in",
                            )
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
                    width="stretch",
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
                            user_auth_error_message(
                                error,
                                action="create the account",
                            )
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


maintenance_items = []
maintenance_records = []
maintenance_load_failed = False

if active_vehicle:
    try:
        maintenance_items = get_maintenance_items(
            supabase,
            active_vehicle["id"],
        )
        maintenance_records = get_maintenance_records(
            supabase,
            active_vehicle["id"],
        )
    except Exception:
        maintenance_items = []
        maintenance_records = []
        maintenance_load_failed = True


maintenance = maintenance_health_snapshot(
    maintenance_items,
    maintenance_records,
    (
        int(active_vehicle["mileage"])
        if active_vehicle
        else 0
    ),
)

if maintenance_load_failed:
    maintenance["state"] = "Unavailable"
    maintenance["detail"] = "Could not load"

build_items = modification_items(
    (
        active_vehicle.get("modifications")
        if active_vehicle
        else None
    )
)

twin_components = []
twin_specifications = []
twin_load_failed = False

if active_vehicle:
    try:
        twin_components = get_vehicle_components(
            supabase,
            active_vehicle["id"],
        )
        twin_specifications = get_vehicle_specifications(
            supabase,
            active_vehicle["id"],
        )
    except Exception:
        twin_components = []
        twin_specifications = []
        twin_load_failed = True

twin = twin_snapshot(
    twin_components,
    twin_specifications,
)

structured_build = build_snapshot(
    twin_components
)

structured_build_context = (
    format_build_context(
        twin_components
    )
)

build_plan_items = []
build_plan_load_failed = False

if active_vehicle:
    try:
        build_plan_items = get_build_plan_items(
            supabase,
            active_vehicle["id"],
        )
    except Exception:
        build_plan_items = []
        build_plan_load_failed = True

build_plan = build_plan_snapshot(
    build_plan_items,
    twin_components,
)

build_plan_context = (
    format_build_plan_context(
        build_plan_items,
        twin_components,
    )
)


# ---------- top bar ----------
top_brand, top_account = st.columns(
    [5.2, 1.8],
    gap="large",
    vertical_alignment="center",
)

with top_brand:
    render_wordmark()

with top_account:
    account_text, signout_col = st.columns(
        [2.2, 1],
        vertical_alignment="center",
    )

    with account_text:
        st.caption(
            "SIGNED IN"
        )
        st.markdown(
            f"**{st.session_state.auth_user_email}**"
        )

    with signout_col:
        if st.button(
            "Sign out",
            width="stretch",
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


# ---------- M12 dashboard shell ----------
if st.session_state.garage_collapsed:
    layout = [0.62, 9.38]
else:
    layout = [2.25, 7.75]

garage_col, workspace_col = st.columns(
    layout,
    gap="medium",
    vertical_alignment="top",
)


# ---------- fleet rail ----------
with garage_col:
    with st.container(
        key="vcg_garage_scroll"
    ):
        if st.session_state.garage_collapsed:
            if st.button(
                "»",
                key="expand_garage",
                help="Expand My Garage",
                width="stretch",
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
                    key=(
                        "collapsed_vehicle_"
                        f"{vehicle['id']}"
                    ),
                    help=vehicle[
                        "profile_name"
                    ],
                    type=(
                        "primary"
                        if is_active
                        else "secondary"
                    ),
                    width="stretch",
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
                    """
                    <div class="vcg-rail-kicker">FLEET</div>
                    <div class="vcg-rail-title">My Garage</div>
                    """,
                    unsafe_allow_html=True,
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
                    width="stretch",
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
                    photo_url = (
                        signed_vehicle_photo(
                            supabase,
                            vehicle,
                        )
                    )

                    if photo_url:
                        st.image(
                            photo_url,
                            width="stretch",
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
                            "Selected"
                            if is_active
                            else "Open vehicle"
                        ),
                        key=(
                            "vehicle_card_"
                            f"{vehicle['id']}"
                        ),
                        type=(
                            "primary"
                            if is_active
                            else "secondary"
                        ),
                        width="stretch",
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
                        placeholder="My EP3",
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
                        "Legacy modification notes (optional)",
                        placeholder=(
                            "Enter one modification per line, "
                            "or leave blank if standard."
                        ),
                    )

                    add_submitted = (
                        st.form_submit_button(
                            "Save vehicle",
                            type="primary",
                            width="stretch",
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
                            st.exception(
                                error
                            )
                        else:
                            st.session_state.active_vehicle_id = (
                                saved_vehicle["id"]
                            )
                            st.session_state.active_conversation_id = None
                            st.rerun()

            st.markdown(
                """
                <div class="vcg-rail-section">
                    CONVERSATIONS
                </div>
                """,
                unsafe_allow_html=True,
            )

            if conversations:
                for conversation in conversations:
                    conversation_id = (
                        conversation["id"]
                    )

                    title = (
                        conversation.get(
                            "title"
                        )
                        or "Conversation"
                    )

                    local_time = format_local_timestamp(
                        conversation.get(
                            "updated_at"
                        ),
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
                        key=(
                            "conversation_"
                            f"{conversation_id}"
                        ),
                        type=(
                            "primary"
                            if is_active_conversation
                            else "secondary"
                        ),
                        width="stretch",
                    ):
                        st.session_state.active_conversation_id = (
                            conversation_id
                        )
                        st.rerun()

                if active_conversation:
                    with st.expander(
                        "Manage conversation"
                    ):
                        with st.form(
                            "rename_conversation_form"
                        ):
                            new_title = st.text_input(
                                "Conversation name",
                                value=active_conversation[
                                    "title"
                                ],
                            )

                            rename_submitted = (
                                st.form_submit_button(
                                    "Rename",
                                    width="stretch",
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
                                    active_conversation[
                                        "id"
                                    ],
                                    new_title,
                                )
                                st.rerun()

                        confirm_delete_conversation = (
                            st.checkbox(
                                "Confirm permanent delete",
                                key=(
                                    "confirm_delete_conversation_"
                                    f"{active_conversation['id']}"
                                ),
                            )
                        )

                        if st.button(
                            "Delete conversation",
                            key=(
                                "delete_conversation_"
                                f"{active_conversation['id']}"
                            ),
                            disabled=(
                                not confirm_delete_conversation
                            ),
                            width="stretch",
                        ):
                            delete_conversation(
                                supabase,
                                active_conversation[
                                    "id"
                                ],
                            )
                            st.session_state.active_conversation_id = None
                            st.rerun()

            else:
                st.caption(
                    "No saved conversations yet."
                )


# ---------- active vehicle workspace ----------
with workspace_col:
    if active_vehicle:
        active_photo_url = (
            signed_vehicle_photo(
                supabase,
                active_vehicle,
            )
        )

        spotlight_photo, spotlight_info = st.columns(
            [2.65, 5.35],
            gap="medium",
            vertical_alignment="center",
        )

        with spotlight_photo:
            with st.container(
                key="vcg_spotlight_photo"
            ):
                if active_photo_url:
                    st.image(
                        active_photo_url,
                        width="stretch",
                    )
                else:
                    st.markdown(
                        """
                        <div class="vcg-photo-placeholder vcg-photo-spotlight">
                            <span>🚘</span>
                            <small>Add a vehicle photo</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        spotlight_profile = escape(
            str(active_vehicle["profile_name"])
        )
        spotlight_manufacturer = escape(
            str(active_vehicle["manufacturer"])
        )
        spotlight_model = escape(
            str(active_vehicle["model"])
        )
        spotlight_engine = escape(
            str(active_vehicle["engine"])
        )

        with spotlight_info:
            st.markdown(
                f"""
                <div class="vcg-spotlight">
                    <div class="vcg-section-kicker">ACTIVE VEHICLE</div>
                    <div class="vcg-spotlight-profile">
                        {spotlight_profile}
                    </div>
                    <div class="vcg-spotlight-title">
                        {active_vehicle['year']} {spotlight_manufacturer}
                        {spotlight_model}
                    </div>
                    <div class="vcg-spotlight-subtitle">
                        {spotlight_engine}
                    </div>
                    <div class="vcg-status-grid">
                        <div class="vcg-status-card">
                            <span>MILEAGE</span>
                            <strong>{int(active_vehicle['mileage']):,} mi</strong>
                        </div>
                        <div class="vcg-status-card">
                            <span>MAINTENANCE</span>
                            <strong>{maintenance['state']}</strong>
                            <small>{maintenance['detail']}</small>
                        </div>
                        <div class="vcg-status-card">
                            <span>BUILD</span>
                            <strong>{structured_build['installed_count']} installed</strong>
                            <small>{build_plan['active_count']} planned changes</small>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="vcg-workspace-divider"></div>',
            unsafe_allow_html=True,
        )

        workspace_mode = st.radio(
            "Vehicle workspace",
            [
                "Garage AI",
                "Virtual Workshop",
                "Maintenance OS",
                "Build Planner",
            ],
            horizontal=True,
            label_visibility="collapsed",
            key=(
                "vehicle_workspace_mode_"
                f"{active_vehicle['id']}"
            ),
        )

        if workspace_mode == "Virtual Workshop":
            with st.container(
                key="vcg_workshop_scroll"
            ):
                render_virtual_workshop(
                    vehicle=active_vehicle,
                    components=twin_components,
                    plan_items=build_plan_items,
                    maintenance_items=maintenance_items,
                    maintenance_records=maintenance_records,
                    specifications=twin_specifications,
                    workspace_state_key=(
                        "vehicle_workspace_mode_"
                        f"{active_vehicle['id']}"
                    ),
                )
            st.stop()

        if workspace_mode == "Maintenance OS":
            render_maintenance_os(
                client=supabase,
                owner_id=st.session_state.auth_user_id,
                vehicle=active_vehicle,
                items=maintenance_items,
                records=maintenance_records,
                components=twin_components,
            )
            st.stop()

        if workspace_mode == "Build Planner":
            if build_plan_load_failed:
                st.error(
                    "VCG could not load the build plan."
                )
                st.stop()

            render_build_planner(
                client=supabase,
                vehicle=active_vehicle,
                components=twin_components,
                plan_items=build_plan_items,
            )
            st.stop()

        chat_col, intelligence_col = st.columns(
            [6.35, 3.65],
            gap="medium",
            vertical_alignment="top",
        )

        # ---------- Garage AI ----------
        with chat_col:
            st.markdown(
                """
                <div class="vcg-section-heading vcg-ai-heading">
                    <div>
                        <div class="vcg-section-kicker">AI CO-PILOT</div>
                        <div class="vcg-section-title">Garage AI</div>
                    </div>
                    <div class="vcg-live-pill">LIVE VEHICLE CONTEXT</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                f"Grounded on {active_vehicle['year']} "
                f"{active_vehicle['manufacturer']} "
                f"{active_vehicle['model']} and the private Honda library."
            )

            with st.container(
                key="vcg_chat_scroll",
            ):
                if active_conversation:
                    st.markdown(
                        f"#### {active_conversation['title']}"
                    )
                elif not messages:
                    st.markdown(
                        """
                        <div class="vcg-ai-empty">
                            <strong>Start with the car, not a blank chat.</strong>
                            <span>
                                Ask about a symptom, service procedure,
                                specification or modification decision.
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                for message in messages:
                    with st.chat_message(
                        message["role"]
                    ):
                        st.markdown(
                            message["content"]
                        )

            user_message = st.chat_input(
                "Ask Garage AI about this vehicle...",
            )

            if user_message:
                if active_conversation is None:
                    try:
                        active_conversation = create_conversation(
                            supabase,
                            st.session_state.auth_user_id,
                            active_vehicle[
                                "id"
                            ],
                            make_conversation_title(
                                user_message
                            ),
                        )
                    except Exception as error:
                        st.error(
                            "The conversation could not be created."
                        )
                        st.exception(
                            error
                        )
                        st.stop()

                    st.session_state.active_conversation_id = (
                        active_conversation[
                            "id"
                        ]
                    )

                    messages = []

                try:
                    add_message(
                        supabase,
                        st.session_state.auth_user_id,
                        active_conversation[
                            "id"
                        ],
                        "user",
                        user_message,
                    )
                except Exception as error:
                    st.error(
                        "Your message could not be saved."
                    )
                    st.exception(
                        error
                    )
                    st.stop()

                vehicle_description = (
                    f"Profile name: {active_vehicle['profile_name']}\n"
                    f"Year: {active_vehicle['year']}\n"
                    f"Manufacturer: {active_vehicle['manufacturer']}\n"
                    f"Model: {active_vehicle['model']}\n"
                    f"Engine: {active_vehicle['engine']}\n"
                    f"Mileage: {active_vehicle['mileage']}\n"
                    "Current physical structured build "
                    "(source of truth):\n"
                    f"{structured_build_context}\n"
                    "Active future build plan "
                    "(NOT physically fitted/removed yet):\n"
                    f"{build_plan_context}\n"
                    "Legacy modification notes (archive only): "
                    f"{active_vehicle['modifications'] or 'None'}"
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
                        st.exception(
                            error
                        )
                        st.stop()

                assistant_message = (
                    response.output_text
                )

                try:
                    add_message(
                        supabase,
                        st.session_state.auth_user_id,
                        active_conversation[
                            "id"
                        ],
                        "assistant",
                        assistant_message,
                    )

                    update_conversation_response_id(
                        supabase,
                        active_conversation[
                            "id"
                        ],
                        response.id,
                    )
                except Exception as error:
                    st.error(
                        "Garage AI answered, but the response "
                        "could not be saved."
                    )
                    st.exception(
                        error
                    )
                    st.stop()

                st.rerun()

        # ---------- vehicle intelligence ----------
        with intelligence_col:
            with st.container(
                key="vcg_insights_scroll"
            ):
                st.markdown(
                    """
                    <div class="vcg-section-heading">
                        <div>
                            <div class="vcg-section-kicker">VEHICLE INTELLIGENCE</div>
                            <div class="vcg-section-title">At a glance</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                (
                    overview_tab,
                    twin_tab,
                    maintenance_tab,
                    build_tab,
                ) = st.tabs(
                    [
                        "Overview",
                        "Digital Twin",
                        "Maintenance",
                        "Build",
                    ]
                )

                with overview_tab:
                    (
                        overview_a,
                        overview_b,
                        overview_c,
                    ) = st.columns(
                        3
                    )

                    with overview_a:
                        st.metric(
                            "Open maintenance",
                            maintenance[
                                "pending_count"
                            ],
                            border=True,
                        )

                    with overview_b:
                        st.metric(
                            "Twin components",
                            twin[
                                "mapped_component_count"
                            ],
                            border=True,
                        )

                    with overview_c:
                        st.metric(
                            "Planned changes",
                            build_plan[
                                "active_count"
                            ],
                            border=True,
                        )

                    if maintenance[
                        "overdue_count"
                    ]:
                        st.warning(
                            f"{maintenance['overdue_count']} "
                            "maintenance item"
                            f"{'' if maintenance['overdue_count'] == 1 else 's'} "
                            "have reached a recorded due point."
                        )
                    elif maintenance[
                        "due_soon_count"
                    ]:
                        st.warning(
                            f"{maintenance['due_soon_count']} "
                            "maintenance item"
                            f"{'' if maintenance['due_soon_count'] == 1 else 's'} "
                            "are approaching a recorded due point."
                        )
                    elif maintenance[
                        "pending_count"
                    ]:
                        st.info(
                            "Maintenance is planned with no "
                            "recorded overdue or due-soon items."
                        )
                    else:
                        st.success(
                            "No open maintenance items are recorded."
                        )

                    st.markdown(
                        "##### Vehicle profile"
                    )
                    st.markdown(
                        f"**Engine:** {spotlight_engine}  \n"
                        f"**Mileage:** {int(active_vehicle['mileage']):,} mi  \n"
                        f"**Profile:** {spotlight_profile}"
                    )

                with twin_tab:
                    twin_a, twin_b, twin_c = st.columns(
                        3
                    )

                    with twin_a:
                        st.metric(
                            "Systems",
                            twin[
                                "system_count"
                            ],
                            border=True,
                        )

                    with twin_b:
                        st.metric(
                            "Mapped parts",
                            twin[
                                "mapped_component_count"
                            ],
                            border=True,
                        )

                    with twin_c:
                        st.metric(
                            "Verified specs",
                            twin[
                                "verified_spec_count"
                            ],
                            border=True,
                        )

                    if twin_load_failed:
                        st.warning(
                            "The structured digital twin could not be loaded."
                        )
                    else:
                        st.caption(
                            "M13 establishes the vehicle structure. "
                            "Parts and verified specifications are populated "
                            "as real data is added in later milestones."
                        )

                        systems = twin[
                            "systems"
                        ]

                        if systems:
                            left_systems, right_systems = st.columns(
                                2
                            )

                            for index, system in enumerate(
                                systems
                            ):
                                target = (
                                    left_systems
                                    if index % 2 == 0
                                    else right_systems
                                )

                                with target:
                                    mapped_count = (
                                        twin[
                                            "counts_by_system"
                                        ].get(
                                            system[
                                                "system_key"
                                            ],
                                            0,
                                        )
                                    )

                                    st.markdown(
                                        f"**{system['name']}**"
                                    )
                                    st.caption(
                                        f"{mapped_count} mapped "
                                        f"component"
                                        f"{'' if mapped_count == 1 else 's'}"
                                    )
                        else:
                            st.info(
                                "No digital-twin systems are available "
                                "for this vehicle yet."
                            )

                with maintenance_tab:
                    pending_items = (
                        maintenance[
                            "pending_items"
                        ]
                    )

                    if pending_items:
                        for item in pending_items[
                            :5
                        ]:
                            due_label = (
                                maintenance_due_label(
                                    item
                                )
                            )
                            st.markdown(
                                f"**{item['title']}**"
                            )
                            st.caption(
                                f"Due: {due_label}"
                            )

                            if item.get(
                                "notes"
                            ):
                                st.caption(
                                    item[
                                        "notes"
                                    ]
                                )

                            st.markdown(
                                '<div class="vcg-mini-divider"></div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption(
                            "No open maintenance items recorded."
                        )

                    if maintenance[
                        "history_count"
                    ]:
                        st.caption(
                            f"{maintenance['history_count']} "
                            "service-history record"
                            f"{'' if maintenance['history_count'] == 1 else 's'} "
                            "stored."
                        )

                with build_tab:
                    build_a, build_b = st.columns(
                        2
                    )

                    with build_a:
                        st.metric(
                            "Installed",
                            structured_build[
                                "installed_count"
                            ],
                            border=True,
                        )

                    with build_b:
                        st.metric(
                            "Planned changes",
                            build_plan[
                                "active_count"
                            ],
                            border=True,
                        )

                    installed_components = (
                        structured_build[
                            "installed"
                        ]
                    )

                    if installed_components:
                        for component in installed_components[
                            :8
                        ]:
                            st.markdown(
                                f"**{component['name']}**"
                            )
                            st.caption(
                                str(
                                    component.get(
                                        "system_key",
                                        "Other",
                                    )
                                ).replace(
                                    "_",
                                    " ",
                                ).title()
                            )
                    else:
                        st.caption(
                            "No installed structured components recorded."
                        )

                    if build_plan[
                        "active_count"
                    ]:
                        st.info(
                            "Open Build Planner to compare and manage "
                            "future installs/removals."
                        )

                with st.expander(
                    "Manage vehicle"
                ):
                    photo_version_key = (
                        "photo_uploader_version_"
                        f"{active_vehicle['id']}"
                    )

                    if photo_version_key not in st.session_state:
                        st.session_state[
                            photo_version_key
                        ] = 0

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
                            "Add or replace the vehicle photo."
                        ),
                    )

                    processed_photo_key = (
                        "processed_photo_upload_"
                        f"{active_vehicle['id']}"
                    )

                    if uploaded_photo is not None:
                        upload_token = (
                            photo_upload_token(
                                uploaded_photo
                            )
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
                                        active_vehicle[
                                            "id"
                                        ]
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
                                st.exception(
                                    error
                                )
                            else:
                                st.session_state[
                                    processed_photo_key
                                ] = upload_token
                                st.rerun()

                    if active_vehicle.get(
                        "photo_path"
                    ):
                        if st.button(
                            "Remove photo",
                            key=(
                                "remove_active_vehicle_photo_"
                                f"{active_vehicle['id']}"
                            ),
                            width="stretch",
                        ):
                            try:
                                remove_vehicle_photo(
                                    client=supabase,
                                    vehicle_id=(
                                        active_vehicle[
                                            "id"
                                        ]
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
                                st.exception(
                                    error
                                )
                            else:
                                st.session_state[
                                    photo_version_key
                                ] += 1
                                st.session_state.pop(
                                    processed_photo_key,
                                    None,
                                )
                                st.rerun()

                    with st.form(
                        f"edit_vehicle_form_{active_vehicle['id']}",
                        clear_on_submit=False,
                    ):
                        edit_profile_name = st.text_input(
                            "Profile name",
                            value=active_vehicle[
                                "profile_name"
                            ],
                        )
                        edit_manufacturer = st.text_input(
                            "Manufacturer",
                            value=active_vehicle[
                                "manufacturer"
                            ],
                        )
                        edit_model = st.text_input(
                            "Model",
                            value=active_vehicle[
                                "model"
                            ],
                        )
                        edit_year = st.number_input(
                            "Year",
                            min_value=1900,
                            max_value=2100,
                            step=1,
                            value=int(
                                active_vehicle[
                                    "year"
                                ]
                            ),
                        )
                        edit_engine = st.text_input(
                            "Engine",
                            value=active_vehicle[
                                "engine"
                            ],
                        )
                        edit_mileage = st.number_input(
                            "Mileage",
                            min_value=0,
                            step=1000,
                            value=int(
                                active_vehicle[
                                    "mileage"
                                ]
                            ),
                        )
                        edit_modifications = st.text_area(
                            "Legacy modification notes",
                            value=(
                                active_vehicle[
                                    "modifications"
                                ]
                                or ""
                            ),
                        )

                        update_submitted = (
                            st.form_submit_button(
                                "Update vehicle",
                                type="primary",
                                width="stretch",
                            )
                        )

                    if update_submitted:
                        updated_vehicle_data = {
                            "profile_name": edit_profile_name.strip(),
                            "manufacturer": edit_manufacturer.strip(),
                            "model": edit_model.strip(),
                            "year": int(
                                edit_year
                            ),
                            "engine": edit_engine.strip(),
                            "mileage": int(
                                edit_mileage
                            ),
                            "modifications": edit_modifications.strip(),
                        }

                        required_values = [
                            updated_vehicle_data[
                                "profile_name"
                            ],
                            updated_vehicle_data[
                                "manufacturer"
                            ],
                            updated_vehicle_data[
                                "model"
                            ],
                            updated_vehicle_data[
                                "engine"
                            ],
                        ]

                        if not all(
                            required_values
                        ):
                            st.warning(
                                "Profile name, manufacturer, "
                                "model and engine are required."
                            )
                        else:
                            try:
                                update_vehicle(
                                    supabase,
                                    active_vehicle[
                                        "id"
                                    ],
                                    updated_vehicle_data,
                                )
                            except Exception as error:
                                st.error(
                                    "The vehicle could not be updated."
                                )
                                st.exception(
                                    error
                                )
                            else:
                                st.rerun()

                with st.expander(
                    "Danger zone"
                ):
                    st.warning(
                        "Deleting this vehicle also removes "
                        "its related conversations."
                    )

                    confirm_delete = st.checkbox(
                        "Confirm permanent delete",
                        key=(
                            "confirm_delete_vehicle_"
                            f"{active_vehicle['id']}"
                        ),
                    )

                    if st.button(
                        "Delete vehicle",
                        key=(
                            "delete_vehicle_"
                            f"{active_vehicle['id']}"
                        ),
                        disabled=not confirm_delete,
                        width="stretch",
                    ):
                        try:
                            delete_vehicle(
                                supabase,
                                active_vehicle[
                                    "id"
                                ],
                            )
                        except Exception as error:
                            st.error(
                                "The vehicle could not be deleted."
                            )
                            st.exception(
                                error
                            )
                        else:
                            st.session_state.active_vehicle_id = None
                            st.session_state.active_conversation_id = None
                            st.rerun()

    else:
        st.markdown(
            """
            <div class="vcg-empty-garage">
                <div class="vcg-section-kicker">YOUR GARAGE</div>
                <h2>Add your first vehicle</h2>
                <p>
                    VCG becomes vehicle-specific once a car is selected.
                    Add a vehicle from the garage rail to begin.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
