import unittest

from digital_twin import twin_snapshot


class TestDigitalTwin(unittest.TestCase):

    def test_snapshot_separates_systems_from_components(self):
        snapshot = twin_snapshot(
            [
                {
                    "component_type": "system",
                    "parent_component_id": None,
                    "system_key": "engine",
                    "name": "Engine",
                    "sort_order": 10,
                    "lifecycle_status": "installed",
                },
                {
                    "component_type": "component",
                    "parent_component_id": "root-1",
                    "system_key": "engine",
                    "name": "K20A2 engine",
                    "lifecycle_status": "installed",
                },
                {
                    "component_type": "component",
                    "parent_component_id": "root-1",
                    "system_key": "engine",
                    "name": "Future camshaft",
                    "lifecycle_status": "planned",
                },
            ],
            [],
        )

        self.assertEqual(
            snapshot["system_count"],
            1,
        )
        self.assertEqual(
            snapshot["mapped_component_count"],
            2,
        )
        self.assertEqual(
            snapshot["installed_component_count"],
            1,
        )
        self.assertEqual(
            snapshot["counts_by_system"]["engine"],
            2,
        )

    def test_snapshot_counts_only_current_verified_specs(self):
        snapshot = twin_snapshot(
            [],
            [
                {
                    "confidence": "verified",
                    "is_current": True,
                },
                {
                    "confidence": "high",
                    "is_current": True,
                },
                {
                    "confidence": "verified",
                    "is_current": False,
                },
            ],
        )

        self.assertEqual(
            snapshot["verified_spec_count"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
