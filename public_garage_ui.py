from __future__ import annotations

from html import escape

import streamlit as st

from public_garage import (
    GARAGE_THEMES,
    public_slug_error,
    public_vehicle_defaults,
)
from public_garage_repository import (
    get_public_garage_settings,
    get_public_vehicle_profiles,
    public_photo_url,
    publish_public_garage_snapshot,
    sync_public_vehicle_photo,
    upsert_public_garage_settings,
    upsert_public_vehicle_profile,
)
from ui_errors import log_ui_exception
from ui_theme import render_wordmark


THEME_LABELS = dict(
    GARAGE_THEMES
)


def _profile_lookup(
    profiles: list[dict],
) -> dict[int, dict]:
    return {
        int(
            profile[
                "vehicle_id"
            ]
        ): profile
        for profile in profiles
    }


def _sync_visible_public_photos(
    client,
    owner_id: str,
    vehicles: list[dict],
    profiles: list[dict],
    garage_is_public: bool,
) -> None:
    lookup = _profile_lookup(
        profiles
    )

    for vehicle in vehicles:
        profile = lookup.get(
            int(
                vehicle[
                    "id"
                ]
            )
        )

        if not profile:
            continue

        sync_public_vehicle_photo(
            client=client,
            owner_id=owner_id,
            vehicle=vehicle,
            public_profile=profile,
            garage_is_public=garage_is_public,
        )


def render_public_garage_settings(
    client,
    owner_id: str,
    vehicles: list[dict],
) -> None:
    try:
        garage = get_public_garage_settings(
            client,
            owner_id,
        )
        profiles = get_public_vehicle_profiles(
            client,
            owner_id,
        )
    except Exception as error:
        st.error(
            "VCG could not load your public garage settings."
        )
        log_ui_exception(
            error,
            context="Public garage settings load failed",
        )
        return

    profile_lookup = _profile_lookup(
        profiles
    )

    with st.expander(
        "Share garage"
    ):
        st.caption(
            "Your garage is private unless you switch it public. "
            "VIN, registration, evidence, diagnostics, maintenance "
            "and Garage AI are never included in the public profile."
        )

        current_theme = (
            garage.get(
                "theme",
                "midnight",
            )
            if garage
            else "midnight"
        )

        theme_keys = [
            key
            for key, _label in GARAGE_THEMES
        ]

        with st.form(
            "public_garage_settings_form"
        ):
            display_name = st.text_input(
                "Garage name",
                value=(
                    garage.get(
                        "display_name",
                        "My Garage",
                    )
                    if garage
                    else "My Garage"
                ),
                placeholder="Deacon's Garage",
            )

            slug = st.text_input(
                "Share link",
                value=(
                    garage.get(
                        "slug",
                        "",
                    )
                    if garage
                    else ""
                ),
                placeholder="deacons-garage",
                help=(
                    "Letters, numbers and hyphens. "
                    "This becomes ?garage=your-link."
                ),
            )

            bio = st.text_area(
                "Garage bio",
                value=(
                    garage.get(
                        "bio"
                    )
                    or ""
                    if garage
                    else ""
                ),
                placeholder=(
                    "A short public description of your garage/builds."
                ),
            )

            theme = st.selectbox(
                "Garage background",
                theme_keys,
                index=(
                    theme_keys.index(
                        current_theme
                    )
                    if current_theme in theme_keys
                    else 0
                ),
                format_func=lambda value: THEME_LABELS[
                    value
                ],
            )

            is_public = st.checkbox(
                "Make my garage public",
                value=bool(
                    garage.get(
                        "is_public"
                    )
                    if garage
                    else False
                ),
            )

            save_garage = st.form_submit_button(
                "Save garage profile",
                type="primary",
                width="stretch",
            )

        if save_garage:
            slug_problem = public_slug_error(
                slug
            )

            if not display_name.strip():
                st.warning(
                    "Give your public garage a name."
                )
            elif slug_problem:
                st.warning(
                    slug_problem
                )
            else:
                try:
                    saved_garage = upsert_public_garage_settings(
                        client=client,
                        owner_id=owner_id,
                        settings={
                            "display_name": display_name,
                            "slug": slug,
                            "bio": bio,
                            "theme": theme,
                            "is_public": is_public,
                        },
                    )

                    refreshed_profiles = get_public_vehicle_profiles(
                        client,
                        owner_id,
                    )

                    _sync_visible_public_photos(
                        client=client,
                        owner_id=owner_id,
                        vehicles=vehicles,
                        profiles=refreshed_profiles,
                        garage_is_public=bool(
                            saved_garage[
                                "is_public"
                            ]
                        ),
                    )

                    refreshed_profiles = get_public_vehicle_profiles(
                        client,
                        owner_id,
                    )

                    publish_public_garage_snapshot(
                        client=client,
                        garage=saved_garage,
                        vehicles=vehicles,
                        profiles=refreshed_profiles,
                    )
                except Exception as error:
                    st.error(
                        "VCG could not save this public garage profile. "
                        "The share link may already be in use."
                    )
                    log_ui_exception(
                        error,
                        context="Public garage settings save failed",
                    )
                else:
                    st.rerun()

        if garage:
            if garage.get(
                "is_public"
            ):
                safe_slug = escape(
                    str(
                        garage[
                            "slug"
                        ]
                    ),
                    quote=True,
                )

                st.markdown(
                    (
                        '<a class="vcg-public-preview-link" '
                        f'href="?garage={safe_slug}" target="_self">'
                        "Preview public garage →"
                        "</a>"
                    ),
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Open the preview, then copy the browser URL to share it."
                )
            else:
                st.caption(
                    "Public sharing is currently off."
                )

        if not vehicles:
            return

        st.divider()
        st.markdown(
            "#### Cars on your profile"
        )

        for vehicle in vehicles:
            vehicle_id = int(
                vehicle[
                    "id"
                ]
            )
            existing = profile_lookup.get(
                vehicle_id
            )
            profile = (
                existing
                or public_vehicle_defaults(
                    vehicle_id,
                    owner_id,
                )
            )

            with st.container(
                border=True,
            ):
                st.markdown(
                    f"**{vehicle['profile_name']}**"
                )
                st.caption(
                    f"{vehicle['year']} · "
                    f"{vehicle['manufacturer']} {vehicle['model']}"
                )

                with st.form(
                    f"public_vehicle_profile_{vehicle_id}"
                ):
                    vehicle_public = st.checkbox(
                        "Show this car publicly",
                        value=bool(
                            profile.get(
                                "is_public"
                            )
                        ),
                    )

                    public_bio = st.text_area(
                        "Public build description",
                        value=(
                            profile.get(
                                "public_bio"
                            )
                            or ""
                        ),
                        placeholder=(
                            "What would you like visitors to know about this car?"
                        ),
                    )

                    st.caption(
                        "Choose exactly what visitors can see:"
                    )

                    show_photo = st.checkbox(
                        "Photo",
                        value=bool(
                            profile.get(
                                "show_photo",
                                True,
                            )
                        ),
                        disabled=not bool(
                            vehicle.get(
                                "photo_path"
                            )
                        ),
                    )
                    show_year = st.checkbox(
                        "Year",
                        value=bool(
                            profile.get(
                                "show_year",
                                True,
                            )
                        ),
                    )
                    show_manufacturer = st.checkbox(
                        "Manufacturer",
                        value=bool(
                            profile.get(
                                "show_manufacturer",
                                True,
                            )
                        ),
                    )
                    show_model = st.checkbox(
                        "Model",
                        value=bool(
                            profile.get(
                                "show_model",
                                True,
                            )
                        ),
                    )
                    show_engine = st.checkbox(
                        "Engine",
                        value=bool(
                            profile.get(
                                "show_engine"
                            )
                        ),
                    )
                    show_mileage = st.checkbox(
                        "Mileage",
                        value=bool(
                            profile.get(
                                "show_mileage"
                            )
                        ),
                    )
                    show_modifications = st.checkbox(
                        "Installed modifications",
                        value=bool(
                            profile.get(
                                "show_modifications"
                            )
                        ),
                    )
                    show_specifications = st.checkbox(
                        "Recorded specifications",
                        value=bool(
                            profile.get(
                                "show_specifications"
                            )
                        ),
                    )

                    save_vehicle = st.form_submit_button(
                        "Save car visibility",
                        width="stretch",
                    )

                if save_vehicle:
                    try:
                        saved_profile = upsert_public_vehicle_profile(
                            client=client,
                            owner_id=owner_id,
                            vehicle_id=vehicle_id,
                            changes={
                                "is_public": vehicle_public,
                                "show_photo": show_photo,
                                "show_year": show_year,
                                "show_manufacturer": show_manufacturer,
                                "show_model": show_model,
                                "show_engine": show_engine,
                                "show_mileage": show_mileage,
                                "show_modifications": show_modifications,
                                "show_specifications": show_specifications,
                                "public_bio": public_bio,
                            },
                            existing=existing,
                        )

                        sync_public_vehicle_photo(
                            client=client,
                            owner_id=owner_id,
                            vehicle=vehicle,
                            public_profile=saved_profile,
                            garage_is_public=bool(
                                garage
                                and garage.get(
                                    "is_public"
                                )
                            ),
                        )

                        refreshed_profiles = get_public_vehicle_profiles(
                            client,
                            owner_id,
                        )

                        publish_public_garage_snapshot(
                            client=client,
                            garage=garage,
                            vehicles=vehicles,
                            profiles=refreshed_profiles,
                        )
                    except Exception as error:
                        st.error(
                            "VCG could not update this car's public profile."
                        )
                        log_ui_exception(
                            error,
                            context="Public vehicle visibility save failed",
                        )
                    else:
                        st.rerun()


def _public_theme_css(
    theme: str,
) -> str:
    backgrounds = {
        "midnight": (
            "radial-gradient(circle at 50% 15%, rgba(84,133,176,.18), "
            "transparent 35%), linear-gradient(180deg,#0a1017,#090e14)"
        ),
        "concrete": (
            "radial-gradient(circle at 30% 5%, rgba(255,255,255,.08), "
            "transparent 28%), linear-gradient(180deg,#202326,#101214)"
        ),
        "studio": (
            "radial-gradient(circle at 50% 12%, rgba(255,255,255,.16), "
            "transparent 32%), linear-gradient(180deg,#222831,#0f141a)"
        ),
        "neon": (
            "radial-gradient(circle at 80% 10%, rgba(98,72,255,.22), "
            "transparent 30%), radial-gradient(circle at 15% 20%, "
            "rgba(255,107,74,.12), transparent 28%), "
            "linear-gradient(180deg,#090b14,#090e14)"
        ),
    }

    background = backgrounds.get(
        theme,
        backgrounds[
            "midnight"
        ],
    )

    return f"""
    <style>
    .stApp {{
        background: {background} !important;
    }}

    .vcg-public-header {{
        max-width: 1120px;
        margin: 0 auto 1.2rem auto;
        padding: 0.4rem 0;
    }}

    .vcg-public-title {{
        color: #F4F7FA;
        font-size: clamp(2rem,5vw,4rem);
        font-weight: 900;
        letter-spacing: -0.05em;
        line-height: 1;
        margin-top: 1.1rem;
    }}

    .vcg-public-bio {{
        color: #A8B3BF;
        max-width: 720px;
        margin-top: 0.6rem;
        font-size: 0.95rem;
    }}

    .vcg-public-badge {{
        display: inline-block;
        border: 1px solid rgba(255,107,74,.38);
        background: rgba(255,107,74,.08);
        color: #FF967E;
        border-radius: 999px;
        padding: .28rem .56rem;
        font-size: .62rem;
        font-weight: 850;
        letter-spacing: .08em;
    }}

    .vcg-public-preview-link {{
        color: #FF8C72 !important;
        text-decoration: none !important;
        font-weight: 800;
    }}

    .vcg-public-car {{
        border: 1px solid #2A3746;
        background: rgba(13,20,28,.86);
        border-radius: 20px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    </style>
    """


def render_public_garage_showcase(
    client,
    payload: dict | None,
) -> None:
    if not payload:
        render_wordmark()
        st.error(
            "This garage is private or the share link does not exist."
        )
        st.markdown(
            '<a class="vcg-public-preview-link" href="./">Open VCG →</a>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        _public_theme_css(
            str(
                payload.get(
                    "theme",
                    "midnight",
                )
            )
        ),
        unsafe_allow_html=True,
    )

    with st.container():
        render_wordmark()

        display_name = escape(
            str(
                payload.get(
                    "display_name"
                )
                or "Public Garage"
            )
        )
        bio = escape(
            str(
                payload.get(
                    "bio"
                )
                or ""
            )
        )

        st.markdown(
            f"""
            <div class="vcg-public-header">
                <div class="vcg-public-badge">PUBLIC GARAGE</div>
                <div class="vcg-public-title">{display_name}</div>
                <div class="vcg-public-bio">{bio}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    vehicles = payload.get(
        "vehicles"
    ) or []

    if not vehicles:
        st.info(
            "This garage is public, but no cars are currently on display."
        )
        return

    for vehicle in vehicles:
        with st.container(
            border=True,
        ):
            photo_path = vehicle.get(
                "public_photo_path"
            )
            photo = public_photo_url(
                client,
                photo_path,
            )

            photo_col, detail_col = st.columns(
                [1.5, 1],
                gap="large",
                vertical_alignment="center",
            )

            with photo_col:
                if photo:
                    st.image(
                        photo,
                        width="stretch",
                    )
                else:
                    st.markdown(
                        """
                        <div class="vcg-twin-placeholder">
                            <span>🚘</span>
                            <strong>Private photo</strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with detail_col:
                st.markdown(
                    f"## {escape(str(vehicle.get('profile_name') or 'Vehicle'))}"
                )

                identity = [
                    str(
                        value
                    )
                    for value in (
                        vehicle.get(
                            "year"
                        ),
                        vehicle.get(
                            "manufacturer"
                        ),
                        vehicle.get(
                            "model"
                        ),
                    )
                    if value not in (
                        None,
                        "",
                    )
                ]

                if identity:
                    st.caption(
                        " · ".join(
                            identity
                        )
                    )

                if vehicle.get(
                    "engine"
                ):
                    st.markdown(
                        f"**Engine:** {escape(str(vehicle['engine']))}"
                    )

                if vehicle.get(
                    "mileage"
                ) is not None:
                    st.markdown(
                        f"**Mileage:** {int(vehicle['mileage']):,}"
                    )

                if vehicle.get(
                    "public_bio"
                ):
                    st.write(
                        str(
                            vehicle[
                                "public_bio"
                            ]
                        )
                    )

            components = vehicle.get(
                "installed_components"
            ) or []

            if components:
                with st.expander(
                    f"Installed modifications · {len(components)}"
                ):
                    for component in components:
                        line = str(
                            component.get(
                                "name"
                            )
                            or "Component"
                        )

                        manufacturer = component.get(
                            "manufacturer"
                        )
                        part_number = component.get(
                            "part_number"
                        )

                        details = [
                            str(
                                value
                            )
                            for value in (
                                manufacturer,
                                part_number,
                            )
                            if value
                        ]

                        if details:
                            line += (
                                " · "
                                + " · ".join(
                                    details
                                )
                            )

                        st.markdown(
                            f"- {escape(line)}"
                        )

            specifications = vehicle.get(
                "specifications"
            ) or []

            if specifications:
                with st.expander(
                    f"Specifications · {len(specifications)}"
                ):
                    for spec in specifications:
                        value = (
                            spec.get(
                                "value_text"
                            )
                            if spec.get(
                                "value_text"
                            )
                            is not None
                            else spec.get(
                                "value_numeric"
                            )
                        )

                        unit = spec.get(
                            "unit"
                        )

                        rendered = str(
                            value
                        )

                        if unit:
                            rendered += (
                                f" {unit}"
                            )

                        st.markdown(
                            f"- **{escape(str(spec.get('label') or 'Specification'))}:** "
                            f"{escape(rendered)}"
                        )

    st.markdown(
        '<div style="margin-top:1rem"><a class="vcg-public-preview-link" '
        'href="./">Create your own garage in VCG →</a></div>',
        unsafe_allow_html=True,
    )
