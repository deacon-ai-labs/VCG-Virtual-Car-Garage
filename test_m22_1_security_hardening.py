import unittest
from pathlib import Path


USER_FACING_MODULES = (
    "app.py",
    "build_planner_ui.py",
    "diagnostics_ui.py",
    "maintenance_ui.py",
    "vehicle_intake_ui.py",
    "vehicle_manage_ui.py",
    "public_garage_ui.py",
)


class TestM221SecurityHardening(unittest.TestCase):

    def test_user_facing_modules_do_not_render_raw_exceptions(self):
        for path in USER_FACING_MODULES:
            source = Path(
                path
            ).read_text(
                encoding="utf-8"
            )

            self.assertNotIn(
                "st.exception(",
                source,
                msg=path,
            )

    def test_internal_errors_are_logged_server_side(self):
        source = Path(
            "ui_errors.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "logger.error(",
            source,
        )
        self.assertIn(
            "exc_info=True",
            source,
        )

    def test_vehicle_delete_uses_retryable_cleanup_lifecycle(self):
        manage = Path(
            "vehicle_manage_ui.py"
        ).read_text(
            encoding="utf-8"
        )
        app = Path(
            "app.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "delete_vehicle_with_assets(",
            manage,
        )
        self.assertIn(
            "process_pending_storage_cleanup(",
            app,
        )

    def test_signup_flow_has_vcg_password_floor(self):
        auth = Path(
            "auth.py"
        ).read_text(
            encoding="utf-8"
        )
        app = Path(
            "app.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "def signup_password_error(",
            auth,
        )
        self.assertIn(
            "len(\n        password\n    ) < 12",
            auth,
        )
        self.assertIn(
            "signup_password_error(",
            app,
        )

    def test_cleanup_migration_is_reproducible(self):
        sql = Path(
            "supabase_m22_1_security_hardening.sql"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "storage_cleanup_queue",
            sql,
        )
        self.assertIn(
            "delete_vehicle_for_cleanup",
            sql,
        )
        self.assertIn(
            "enable row level security",
            sql.lower(),
        )

    def test_upload_validation_is_enforced_at_storage_boundaries(self):
        database = Path(
            "database.py"
        ).read_text(
            encoding="utf-8"
        )
        intake = Path(
            "vehicle_intake_repository.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "validate_vehicle_photo_upload(",
            database,
        )
        self.assertIn(
            "validate_evidence_upload(",
            intake,
        )


if __name__ == "__main__":
    unittest.main()
