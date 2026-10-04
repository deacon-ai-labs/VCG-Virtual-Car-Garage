import unittest
from pathlib import Path


class TestM24FirstRunExperience(unittest.TestCase):

    def setUp(self):
        self.app = Path(
            "app.py"
        ).read_text(
            encoding="utf-8"
        )
        self.theme = Path(
            "ui_theme.py"
        ).read_text(
            encoding="utf-8"
        )
        self.intake = Path(
            "vehicle_intake_ui.py"
        ).read_text(
            encoding="utf-8"
        )

    def test_zero_vehicle_accounts_stop_at_first_run_before_advanced_loading(self):
        first_run = self.app.index(
            "if not vehicles:"
        )
        first_run_renderer = self.app.index(
            "render_first_run_onboarding(",
            first_run,
        )
        vehicle_context = self.app.index(
            "vehicle_ids = ["
        )
        maintenance_load = self.app.index(
            "maintenance_items = []"
        )

        self.assertLess(
            first_run,
            vehicle_context,
        )
        self.assertLess(
            first_run_renderer,
            maintenance_load,
        )
        self.assertIn(
            "st.stop()",
            self.app[
                first_run:
                vehicle_context
            ],
        )

    def test_first_vehicle_becomes_active_after_creation(self):
        block = self.app.split(
            "if not vehicles:",
            1,
        )[1].split(
            "vehicle_ids = [",
            1,
        )[0]

        self.assertIn(
            "saved_vehicle",
            block,
        )
        self.assertIn(
            "st.session_state.active_vehicle_id",
            block,
        )
        self.assertIn(
            'saved_vehicle[\n                "id"\n            ]',
            block,
        )

    def test_sign_in_explains_actual_v0_product(self):
        for phrase in (
            "Build a living Virtual Twin of your real car.",
            "Virtual Twin",
            "Garage AI",
            "Maintenance",
            "Diagnostics",
            "Public Garage",
            "private by default",
        ):
            self.assertIn(
                phrase,
                self.app,
            )

    def test_mobile_auth_hides_decorative_hero(self):
        mobile = self.theme.split(
            "@media (max-width: 900px) {{",
            1,
        )[1].split(
            "}}\n        </style>",
            1,
        )[0]

        self.assertIn(
            ".vcg-login-hero {{",
            mobile,
        )
        self.assertIn(
            "display: none;",
            mobile,
        )

    def test_m24_global_theme_css_escapes_fstring_braces(self):
        for selector in (
            ".vcg-auth-title",
            ".vcg-auth-copy",
            ".vcg-auth-feature-row",
            ".vcg-first-run-shell",
            ".vcg-first-run-title",
            ".vcg-first-run-step",
        ):
            self.assertIn(
                selector + " {{",
                self.theme,
            )
            self.assertNotIn(
                selector + " {\n",
                self.theme,
            )

    def test_new_vehicle_form_has_no_owner_specific_year_default(self):
        self.assertIn(
            'value=None',
            self.intake,
        )
        self.assertNotIn(
            'value=2004',
            self.intake,
        )
        self.assertIn(
            'placeholder="e.g. 2004"',
            self.intake,
        )

    def test_public_garage_route_still_runs_before_auth(self):
        public_route = self.app.index(
            "public_garage_slug = st.query_params.get("
        )
        auth_state = self.app.index(
            "AUTH_STATE_KEYS ="
        )

        self.assertLess(
            public_route,
            auth_state,
        )


if __name__ == "__main__":
    unittest.main()
