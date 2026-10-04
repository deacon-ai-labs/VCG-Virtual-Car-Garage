from __future__ import annotations

import streamlit as st

from database import (
    delete_vehicle,
    update_vehicle,
)
from photo_service import (
    remove_vehicle_photo,
    replace_vehicle_photo,
)
from photo_ui import (
    build_photo_uploader_css,
    photo_upload_token,
)


def render_vehicle_management(
    client,
    owner_id: str,
    vehicle: dict,
    photo_url: str | None,
) -> None:
    """Render vehicle settings independently of any feature workspace."""

    with st.expander(
        "Vehicle settings"
    ):
        photo_version_key = (
            "photo_uploader_version_"
            f"{vehicle['id']}"
        )

        if photo_version_key not in st.session_state:
            st.session_state[
                photo_version_key
            ] = 0

        photo_widget_key = (
            "active_vehicle_photo_"
            f"{vehicle['id']}_"
            f"{st.session_state[photo_version_key]}"
        )

        st.markdown(
            build_photo_uploader_css(
                photo_widget_key,
                photo_url,
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
            f"{vehicle['id']}"
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
                        client=client,
                        owner_id=owner_id,
                        vehicle_id=vehicle[
                            "id"
                        ],
                        old_photo_path=vehicle.get(
                            "photo_path"
                        ),
                        filename=uploaded_photo.name,
                        file_bytes=uploaded_photo.getvalue(),
                        content_type=(
                            uploaded_photo.type
                            or "image/jpeg"
                        ),
                    )
                except Exception as error:
                    st.error(
                        "The vehicle photo could not be saved."
                    )
                    st.exception(
                        error
                    )
                else:
                    st.session_state[
                        processed_photo_key
                    ] = upload_token
                    st.rerun()

        if vehicle.get(
            "photo_path"
        ):
            if st.button(
                "Remove photo",
                key=(
                    "remove_active_vehicle_photo_"
                    f"{vehicle['id']}"
                ),
                width="stretch",
            ):
                try:
                    remove_vehicle_photo(
                        client=client,
                        vehicle_id=vehicle[
                            "id"
                        ],
                        photo_path=vehicle.get(
                            "photo_path"
                        ),
                    )
                except Exception as error:
                    st.error(
                        "The vehicle photo could not be removed."
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
            f"edit_vehicle_form_{vehicle['id']}",
            clear_on_submit=False,
        ):
            edit_profile_name = st.text_input(
                "Profile name",
                value=vehicle[
                    "profile_name"
                ],
            )
            edit_manufacturer = st.text_input(
                "Manufacturer",
                value=vehicle[
                    "manufacturer"
                ],
            )
            edit_model = st.text_input(
                "Model",
                value=vehicle[
                    "model"
                ],
            )
            edit_year = st.number_input(
                "Year",
                min_value=1900,
                max_value=2100,
                step=1,
                value=int(
                    vehicle[
                        "year"
                    ]
                ),
            )
            edit_engine = st.text_input(
                "Engine",
                value=vehicle[
                    "engine"
                ],
            )
            edit_mileage = st.number_input(
                "Mileage",
                min_value=0,
                step=1000,
                value=int(
                    vehicle[
                        "mileage"
                    ]
                ),
            )
            edit_modifications = st.text_area(
                "Legacy modification notes",
                value=(
                    vehicle[
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
                    "Profile name, manufacturer, model and engine are required."
                )
            else:
                try:
                    update_vehicle(
                        client,
                        vehicle[
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
            "Deleting this vehicle removes its related VCG records."
        )

        confirm_delete = st.checkbox(
            "Confirm permanent delete",
            key=(
                "confirm_delete_vehicle_"
                f"{vehicle['id']}"
            ),
        )

        if st.button(
            "Delete vehicle",
            key=(
                "delete_vehicle_"
                f"{vehicle['id']}"
            ),
            disabled=not confirm_delete,
            width="stretch",
        ):
            try:
                delete_vehicle(
                    client,
                    vehicle[
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
