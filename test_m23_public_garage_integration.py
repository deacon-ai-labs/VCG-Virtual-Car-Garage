import unittest
from pathlib import Path


class TestM23PublicGarageIntegration(unittest.TestCase):

    def setUp(self):
        self.app = Path(
            "app.py"
        ).read_text(
            encoding="utf-8"
        )
        self.sql = "\n".join(
            Path(
                path
            ).read_text(
                encoding="utf-8"
            )
            for path in (
                "supabase_m23_public_garage_core.sql",
                "supabase_m23_public_garage_lifecycle.sql",
                "supabase_m23_public_garage_snapshot.sql",
                "supabase_m23_public_garage_invalidation.sql",
            )
        )
        self.ui = Path(
            "public_garage_ui.py"
        ).read_text(
            encoding="utf-8"
        )
        self.repository = Path(
            "public_garage_repository.py"
        ).read_text(
            encoding="utf-8"
        )

    def test_public_route_runs_before_auth_gate(self):
        public_route = self.app.index(
            'public_garage_slug = st.query_params.get('
        )
        auth_gate = self.app.index(
            'for key in AUTH_STATE_KEYS:'
        )

        self.assertLess(
            public_route,
            auth_gate,
        )
        self.assertIn(
            "fetch_public_garage(",
            self.app,
        )
        self.assertIn(
            "render_public_garage_showcase(",
            self.app,
        )

    def test_share_controls_do_not_create_another_primary_workspace(self):
        self.assertIn(
            "render_public_garage_settings(",
            self.app,
        )
        self.assertIn(
            '"Share garage"',
            self.ui,
        )

    def test_anonymous_access_is_limited_to_public_snapshots(self):
        self.assertIn(
            "public_garage_snapshots",
            self.sql,
        )
        self.assertIn(
            'for select to anon',
            self.sql.lower(),
        )
        self.assertNotIn(
            "grant select on public.vehicles",
            self.sql.lower(),
        )
        self.assertNotIn(
            "grant select on public.vehicle_components",
            self.sql.lower(),
        )
        self.assertNotIn(
            "grant execute on function",
            self.sql.lower(),
        )

    def test_snapshot_builder_never_reads_private_categories(self):
        builder = self.repository.split(
            "def build_public_garage_payload(",
            1,
        )[1].split(
            "def publish_public_garage_snapshot(",
            1,
        )[0]

        for forbidden in (
            "registration",
            "vin",
            "vehicle_evidence",
            "diagnostic",
            "maintenance",
            "conversation",
            "message",
        ):
            self.assertNotIn(
                forbidden,
                builder.lower(),
            )

    def test_public_photo_revocation_is_part_of_schema(self):
        self.assertIn(
            "public_photo_revoke",
            self.sql,
        )
        self.assertIn(
            "revoke_public_photo_when_source_changes",
            self.sql,
        )
        self.assertIn(
            "revoke_public_photos_when_garage_hidden",
            self.sql,
        )


if __name__ == "__main__":
    unittest.main()
