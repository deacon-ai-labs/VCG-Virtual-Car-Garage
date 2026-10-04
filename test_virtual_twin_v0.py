import unittest

from virtual_twin_v0 import virtual_twin_v0_snapshot


class TestVirtualTwinV0(unittest.TestCase):

    def test_snapshot_keeps_v0_summary_small_and_factual(self):
        snapshot = virtual_twin_v0_snapshot(
            vehicle={
                "mileage": 151500,
            },
            maintenance={
                "state": "Attention",
                "detail": "1 overdue",
            },
            diagnostics={
                "active_case_count": 1,
            },
            build_plan={
                "active_count": 2,
            },
            structured_build={
                "installed_count": 5,
                "installed": [
                    {
                        "name": "K100 ECU",
                    }
                ],
            },
            twin={
                "verified_spec_count": 0,
                "mapped_component_count": 5,
            },
            component_events=[],
            maintenance_records=[],
        )

        self.assertEqual(
            snapshot[
                "mileage"
            ],
            151500,
        )
        self.assertEqual(
            snapshot[
                "installed_count"
            ],
            5,
        )
        self.assertEqual(
            snapshot[
                "maintenance_state"
            ],
            "Attention",
        )
        self.assertEqual(
            snapshot[
                "active_case_count"
            ],
            1,
        )
        self.assertNotIn(
            "power",
            snapshot,
        )
        self.assertNotIn(
            "handling",
            snapshot,
        )

    def test_recent_activity_is_bounded_and_newest_first(self):
        snapshot = virtual_twin_v0_snapshot(
            vehicle={
                "mileage": 0,
            },
            maintenance={
                "state": "Clear",
                "detail": "No open items",
            },
            diagnostics={
                "active_case_count": 0,
            },
            build_plan={
                "active_count": 0,
            },
            structured_build={
                "installed_count": 0,
                "installed": [],
            },
            twin={},
            component_events=[
                {
                    "event_type": "installed",
                    "occurred_at": "2026-10-03T12:00:00Z",
                    "notes": "Installed part",
                }
            ],
            maintenance_records=[
                {
                    "title": "Oil service",
                    "performed_at": "2026-10-04T12:00:00Z",
                },
                {
                    "title": "Brake fluid",
                    "performed_at": "2026-10-02T12:00:00Z",
                },
                {
                    "title": "Older service",
                    "performed_at": "2026-10-01T12:00:00Z",
                },
            ],
        )

        self.assertEqual(
            len(
                snapshot[
                    "recent_activity"
                ]
            ),
            3,
        )
        self.assertEqual(
            snapshot[
                "recent_activity"
            ][0][
                "title"
            ],
            "Oil service",
        )


if __name__ == "__main__":
    unittest.main()
