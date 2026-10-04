import unittest

from vehicle_home import vehicle_home_snapshot


class TestVehicleHome(unittest.TestCase):

    def test_home_surfaces_evidence_based_attention(self):
        snapshot = vehicle_home_snapshot(
            maintenance={
                "state": "Attention",
                "detail": "1 overdue",
                "overdue_count": 1,
                "due_soon_count": 0,
            },
            diagnostics={
                "active_case_count": 1,
            },
            build_plan={
                "active_count": 1,
                "incompatible_count": 0,
                "compatibility_review_count": 1,
            },
            twin={
                "system_count": 12,
                "mapped_component_count": 5,
                "verified_spec_count": 0,
            },
            structured_build={
                "installed_count": 5,
            },
            component_events=[],
            maintenance_records=[],
        )

        titles = [
            item[
                "title"
            ]
            for item in snapshot[
                "attention"
            ]
        ]

        self.assertIn(
            "Maintenance attention",
            titles,
        )
        self.assertIn(
            "Active diagnostic investigation",
            titles,
        )
        self.assertIn(
            "Build compatibility review",
            titles,
        )

    def test_home_does_not_invent_health_score(self):
        snapshot = vehicle_home_snapshot(
            maintenance={
                "state": "Clear",
                "detail": "No open items",
                "overdue_count": 0,
                "due_soon_count": 0,
            },
            diagnostics={
                "active_case_count": 0,
            },
            build_plan={
                "active_count": 0,
                "incompatible_count": 0,
                "compatibility_review_count": 0,
            },
            twin={
                "system_count": 12,
                "mapped_component_count": 0,
                "verified_spec_count": 0,
            },
            structured_build={
                "installed_count": 0,
            },
            component_events=[],
            maintenance_records=[],
        )

        self.assertNotIn(
            "health_score",
            snapshot,
        )
        self.assertEqual(
            snapshot[
                "attention"
            ][0][
                "severity"
            ],
            "success",
        )

    def test_recent_activity_combines_service_and_component_events(self):
        snapshot = vehicle_home_snapshot(
            maintenance={
                "state": "Clear",
                "detail": "No open items",
                "overdue_count": 0,
                "due_soon_count": 0,
            },
            diagnostics={
                "active_case_count": 0,
            },
            build_plan={
                "active_count": 0,
                "incompatible_count": 0,
                "compatibility_review_count": 0,
            },
            twin={},
            structured_build={},
            component_events=[
                {
                    "event_type": "installed",
                    "occurred_at": "2026-10-02T10:00:00Z",
                    "notes": "Installed component",
                }
            ],
            maintenance_records=[
                {
                    "title": "Oil service",
                    "performed_at": "2026-10-03",
                }
            ],
        )

        self.assertEqual(
            snapshot[
                "recent_activity"
            ][0][
                "title"
            ],
            "Oil service",
        )
        self.assertEqual(
            snapshot[
                "recent_activity"
            ][1][
                "title"
            ],
            "Installed",
        )


if __name__ == "__main__":
    unittest.main()
