from pathlib import Path

import streamlit as st

from auth import (
    create_authenticated_client,
    sign_in,
    sign_out,
    sign_up,
    user_auth_error_message,
)
from build_planner import build_plan_snapshot
from build_planner_ui import render_build_planner
from dashboard_state import apply_vehicle_selection
from dashboard_view import modification_items
from diagnostics import (
    diagnostic_vehicle_snapshot,
    format_diagnostic_context,
)
from diagnostics_ui import render_diagnostics_workspace
from digital_twin import (
    build_snapshot,
    twin_snapshot,
)
from database import (
    add_message,
    create_conversation,
    delete_conversation,
    get_build_plan_items,
    get_conversations,
    get_diagnostic_cases,
    get_diagnostic_checks,
    get_diagnostic_hypotheses,
    get_messages,
    get_maintenance_items,
    get_maintenance_records,
    get_vehicle_component_events,
    get_vehicle_components,
    get_vehicle_photo_url,
    get_vehicle_specifications,
    get_vehicles,
    rename_conversation,
    update_conversation_response_id,
)
from garage_ai import ask_ai
from maintenance_os import maintenance_health_snapshot
from maintenance_ui import render_maintenance_os
from time_utils import format_local_timestamp
from ui_theme import (
    apply_dashboard_shell,
    apply_global_theme,
    image_data_uri,
    render_wordmark,
)
from vehicle_intake_repository import (
    get_intake_candidates,
    get_vehicle_evidence,
)
from vehicle_intake_ui import (
    render_new_vehicle_intake_form,
    render_vehicle_intake_panel,
)
from vehicle_intelligence_context import (
    build_vehicle_intelligence_context,
)
from vehicle_manage_ui import render_vehicle_management
from virtual_twin_v0 import virtual_twin_v0_snapshot
from virtual_twin_v0_ui import render_virtual_twin_v0
from virtual_workshop_ui import render_virtual_workshop
from workspace_navigation import (
    contextual_badges,
    normalize_workspace,
    workspace_state_key,
)
from workspace_navigation_ui import (
    render_primary_navigation,
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

    user_state_prefixes = (
        "diagnostic_case_focus_",
        "vehicle_workspace_mode_",
        "workshop_selected_system_",
    )

    for key in list(
        st.session_state.keys()
    ):
        if key.startswith(
            user_state_prefixes
        ):
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


vehicle_evidence = []
intake_candidates = []
intake_load_failed = False

if active_vehicle:
    try:
        vehicle_evidence = get_vehicle_evidence(
            supabase,
            active_vehicle["id"],
        )
        intake_candidates = get_intake_candidates(
            supabase,
            active_vehicle["id"],
        )
    except Exception:
        vehicle_evidence = []
        intake_candidates = []
        intake_load_failed = True


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
twin_component_events = []
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
        twin_component_events = get_vehicle_component_events(
            supabase,
            active_vehicle["id"],
        )
    except Exception:
        twin_components = []
        twin_specifications = []
        twin_component_events = []
        twin_load_failed = True

twin = twin_snapshot(
    twin_components,
    twin_specifications,
)

structured_build = build_snapshot(
    twin_components
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

diagnostic_cases = []
diagnostic_hypotheses = []
diagnostic_checks = []
diagnostic_load_failed = False

if active_vehicle:
    try:
        diagnostic_cases = get_diagnostic_cases(
            supabase,
            active_vehicle["id"],
        )
        diagnostic_hypotheses = get_diagnostic_hypotheses(
            supabase,
            active_vehicle["id"],
        )
        diagnostic_checks = get_diagnostic_checks(
            supabase,
            active_vehicle["id"],
        )
    except Exception:
        diagnostic_cases = []
        diagnostic_hypotheses = []
        diagnostic_checks = []
        diagnostic_load_failed = True

diagnostic_snapshot = diagnostic_vehicle_snapshot(
    diagnostic_cases,
    diagnostic_hypotheses,
    diagnostic_checks,
)

diagnostic_focus_case_id = (
    st.session_state.get(
        "diagnostic_case_focus_"
        f"{active_vehicle['id']}"
    )
    if active_vehicle
    else None
)

diagnostic_context = (
    (
        "Diagnostic investigation data is unavailable in this app run."
        if diagnostic_load_failed
        else format_diagnostic_context(
            diagnostic_cases,
            diagnostic_hypotheses,
            diagnostic_checks,
            twin_components,
            focus_case_id=(
                diagnostic_focus_case_id
            ),
        )
    )
    if active_vehicle
    else "No vehicle is currently selected."
)

vehicle_intelligence_context = (
    (
        build_vehicle_intelligence_context(
            vehicle=active_vehicle,
            components=twin_components,
            specifications=twin_specifications,
            maintenance_items=maintenance_items,
            maintenance_records=maintenance_records,
            component_events=twin_component_events,
            build_plan_items=build_plan_items,
        )
        + "\n\nDIAGNOSTIC INVESTIGATIONS — RECORDED CASE STATE:\n"
        + diagnostic_context
    )
    if active_vehicle
    else "No vehicle is currently selected."
)

workspace_key = (
    workspace_state_key(
        active_vehicle[
            "id"
        ]
    )
    if active_vehicle
    else None
)

workspace_mode = (
    normalize_workspace(
        st.session_state.get(
            workspace_key
        )
    )
    if workspace_key
    else None
)

if workspace_key:
    st.session_state[
        workspace_key
    ] = workspace_mode

contextual_badge_counts = contextual_badges(
    maintenance,
    diagnostic_snapshot,
    build_plan,
)

twin_v0_snapshot = virtual_twin_v0_snapshot(
    vehicle=(
        active_vehicle
        or {}
    ),
    maintenance=maintenance,
    diagnostics=diagnostic_snapshot,
    build_plan=build_plan,
    structured_build=structured_build,
    twin=twin,
    component_events=twin_component_events,
    maintenance_records=maintenance_records,
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


# ---------- V0 garage shell ----------
if st.session_state.garage_collapsed:
    layout = [0.62, 9.38]
else:
    layout = [1.95, 8.05]

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
                saved_vehicle = render_new_vehicle_intake_form(
                    client=supabase,
                    owner_id=st.session_state.auth_user_id,
                )

                if saved_vehicle:
                    st.session_state.active_vehicle_id = (
                        saved_vehicle["id"]
                    )
                    st.session_state.active_conversation_id = None
                    st.rerun()

            if workspace_mode == "Garage AI":
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

        render_primary_navigation(
            state_key=workspace_key,
            current_workspace=workspace_mode,
        )

        if workspace_mode == "Virtual Twin":
            with st.container(
                key="vcg_twin_scroll"
            ):
                render_virtual_twin_v0(
                    vehicle=active_vehicle,
                    photo_url=active_photo_url,
                    snapshot=twin_v0_snapshot,
                    workspace_state_key=workspace_key,
                    contextual_badges=contextual_badge_counts,
                )

                st.divider()

                if intake_load_failed:
                    st.warning(
                        "VCG could not load vehicle intake/evidence data."
                    )
                else:
                    render_vehicle_intake_panel(
                        client=supabase,
                        owner_id=st.session_state.auth_user_id,
                        vehicle=active_vehicle,
                        evidence=vehicle_evidence,
                        candidates=intake_candidates,
                    )

                st.divider()

                render_vehicle_management(
                    client=supabase,
                    owner_id=st.session_state.auth_user_id,
                    vehicle=active_vehicle,
                    photo_url=active_photo_url,
                )
            st.stop()

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

        if workspace_mode == "Diagnostics":
            if diagnostic_load_failed:
                st.error(
                    "VCG could not load diagnostic investigations."
                )
                st.stop()

            with st.container(
                key="vcg_diagnostics_scroll"
            ):
                render_diagnostics_workspace(
                    client=supabase,
                    owner_id=st.session_state.auth_user_id,
                    vehicle=active_vehicle,
                    components=twin_components,
                    cases=diagnostic_cases,
                    hypotheses=diagnostic_hypotheses,
                    checks=diagnostic_checks,
                    workspace_state_key=(
                        "vehicle_workspace_mode_"
                        f"{active_vehicle['id']}"
                    ),
                )
            st.stop()

        if workspace_mode == "Maintenance OS":
            with st.container(
                key="vcg_workspace_scroll"
            ):
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

            with st.container(
                key="vcg_workspace_scroll"
            ):
                render_build_planner(
                    client=supabase,
                    vehicle=active_vehicle,
                    components=twin_components,
                    plan_items=build_plan_items,
                )
            st.stop()

        chat_col, intelligence_col = st.columns(
            [7.25, 2.75],
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
                f"Grounding loaded · "
                f"{structured_build['installed_count']} fitted · "
                f"{build_plan['active_count']} planned · "
                f"{maintenance['pending_count']} open maintenance · "
                f"{maintenance['history_count']} history · "
                f"{twin['verified_spec_count']} verified specs · "
                f"{len(twin_component_events)} lifecycle events · "
                f"{diagnostic_snapshot['active_case_count']} active diagnostic "
                f"case{'' if diagnostic_snapshot['active_case_count'] == 1 else 's'} · "
                "private Honda library"
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
                    f"{active_vehicle['year']} "
                    f"{active_vehicle['manufacturer']} "
                    f"{active_vehicle['model']} "
                    f"({active_vehicle['profile_name']}); "
                    f"engine={active_vehicle['engine']}; "
                    f"recorded_mileage={active_vehicle['mileage']} mi"
                )

                with st.spinner(
                    "Garage AI is investigating..."
                ):
                    try:
                        response = ask_ai(
                            user_message=user_message,
                            vehicle_description=vehicle_description,
                            vehicle_intelligence_context=(
                                vehicle_intelligence_context
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

        # ---------- Garage AI context ----------
        with intelligence_col:
            with st.container(
                key="vcg_insights_scroll"
            ):
                st.markdown(
                    """
                    <div class="vcg-section-heading">
                        <div>
                            <div class="vcg-section-kicker">GROUNDING</div>
                            <div class="vcg-section-title">AI Context</div>
                        </div>
                        <div class="vcg-live-pill">CONNECTED</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                context_a, context_b = st.columns(
                    2
                )

                with context_a:
                    st.metric(
                        "Fitted",
                        structured_build[
                            "installed_count"
                        ],
                        border=True,
                    )
                    st.metric(
                        "Maintenance",
                        maintenance[
                            "pending_count"
                        ],
                        border=True,
                    )

                with context_b:
                    st.metric(
                        "Diagnostics",
                        diagnostic_snapshot[
                            "active_case_count"
                        ],
                        border=True,
                    )
                    st.metric(
                        "Verified specs",
                        twin[
                            "verified_spec_count"
                        ],
                        border=True,
                    )

                st.markdown(
                    "#### Connected evidence"
                )
                st.caption(
                    "Digital twin · build plan · maintenance/history · "
                    "diagnostic cases · lifecycle events · private Honda library"
                )

                if diagnostic_focus_case_id:
                    focused_case = next(
                        (
                            case
                            for case in diagnostic_cases
                            if str(
                                case.get(
                                    "id"
                                )
                            )
                            == str(
                                diagnostic_focus_case_id
                            )
                        ),
                        None,
                    )

                    if focused_case:
                        st.info(
                            "**Focused diagnostic case**  \n"
                            + str(
                                focused_case.get(
                                    "title",
                                    "Untitled case",
                                )
                            )
                        )

                if maintenance[
                    "overdue_count"
                ]:
                    st.warning(
                        f"{maintenance['overdue_count']} recorded maintenance "
                        "item"
                        f"{'' if maintenance['overdue_count'] == 1 else 's'} "
                        "are overdue."
                    )

                if build_plan[
                    "active_count"
                ]:
                    st.caption(
                        f"{build_plan['active_count']} future build change"
                        f"{'' if build_plan['active_count'] == 1 else 's'} "
                        "are included as planning context, not current state."
                    )

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
