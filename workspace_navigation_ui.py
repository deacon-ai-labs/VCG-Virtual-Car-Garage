from __future__ import annotations

import streamlit as st

from workspace_navigation import PRIMARY_WORKSPACES


def _set_workspace(
    state_key: str,
    workspace_name: str,
) -> None:
    st.session_state[
        state_key
    ] = workspace_name


def render_primary_navigation(
    state_key: str,
    current_workspace: str,
) -> None:
    """Render only the persistent V0 vehicle destinations."""

    with st.container(
        key="vcg_primary_nav"
    ):
        columns = st.columns(
            len(
                PRIMARY_WORKSPACES
            ),
            gap="small",
        )

        for column, workspace in zip(
            columns,
            PRIMARY_WORKSPACES,
        ):
            with column:
                st.button(
                    (
                        f"{workspace['icon']} "
                        f"{workspace['short_name']}"
                    ),
                    key=(
                        "primary_nav_"
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
