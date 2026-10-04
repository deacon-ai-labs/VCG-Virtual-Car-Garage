from __future__ import annotations

import streamlit as st

from workspace_navigation import WORKSPACES


def _set_workspace(
    state_key: str,
    workspace_name: str,
) -> None:
    st.session_state[
        state_key
    ] = workspace_name


def render_workspace_navigation(
    state_key: str,
    current_workspace: str,
    badges: dict[str, int] | None = None,
) -> None:
    """Render the primary vehicle workspace navigation."""

    badges = badges or {}

    with st.container(
        key="vcg_workspace_nav"
    ):
        columns = st.columns(
            len(
                WORKSPACES
            ),
            gap="small",
        )

        for column, workspace in zip(
            columns,
            WORKSPACES,
        ):
            with column:
                badge = int(
                    badges.get(
                        workspace[
                            "name"
                        ],
                        0,
                    )
                    or 0
                )

                label = (
                    f"{workspace['icon']} "
                    f"{workspace['short_name']}"
                )

                if badge:
                    label += (
                        f" · {badge}"
                    )

                st.button(
                    label,
                    key=(
                        "workspace_nav_"
                        + workspace[
                            "name"
                        ].lower().replace(
                            " ",
                            "_",
                        )
                    ),
                    type=(
                        "primary"
                        if workspace[
                            "name"
                        ]
                        == current_workspace
                        else "secondary"
                    ),
                    width="stretch",
                    on_click=_set_workspace,
                    args=(
                        state_key,
                        workspace[
                            "name"
                        ],
                    ),
                )
