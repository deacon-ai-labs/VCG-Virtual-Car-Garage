import unittest

from digital_twin import (
    build_snapshot,
    format_build_context,
    twin_snapshot,
)


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

    def test_build_snapshot_counts_states_and_known_weight(self):
        snapshot = build_snapshot(
            [
                {
                    "component_type": "system",
                    "name": "Suspension",
                },
                {
                    "component_type": "component",
                    "name": "Coilovers",
                    "lifecycle_status": "installed",
                    "weight_kg": 12.5,
                    "quantity": 1,
                },
                {
                    "component_type": "component",
                    "name": "Planned brace",
                    "lifecycle_status": "planned",
                    "weight_kg": 3,
                    "quantity": 1,
                },
            ]
        )

        self.assertEqual(
            snapshot["installed_count"],
            1,
        )
        self.assertEqual(
            snapshot["planned_count"],
            1,
        )
        self.assertEqual(
            snapshot["known_weight_kg"],
            15.5,
        )

    def test_format_build_context_includes_only_active_components(self):
        context = format_build_context(
            [
                {
                    "component_type": "component",
                    "name": "K100 ECU",
                    "lifecycle_status": "installed",
                    "system_key": "engine",
                    "manufacturer": None,
                    "part_number": None,
                    "weight_kg": None,
                    "is_oem": False,
                },
                {
                    "component_type": "component",
                    "name": "Old exhaust",
                    "lifecycle_status": "removed",
                    "system_key": "exhaust",
                },
            ]
        )

        self.assertIn(
            "K100 ECU",
            context,
        )
        self.assertIn(
            "origin=aftermarket",
            context,
        )
        self.assertNotIn(
            "Old exhaust",
            context,
        )


if __name__ == "__main__":
    unittest.main()
