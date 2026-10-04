import unittest
from unittest.mock import patch

from vehicle_intelligence_context import (
    build_vehicle_intelligence_context,
)


class TestVehicleIntelligenceContext(unittest.TestCase):

    @patch(
        "vehicle_intelligence_context.maintenance_is_due_soon",
        return_value=False,
    )
    @patch(
        "vehicle_intelligence_context.maintenance_is_overdue",
        return_value=True,
    )
    def test_context_separates_physical_plan_maintenance_and_history(
        self,
        _overdue,
        _due_soon,
    ):
        vehicle = {
            "profile_name": "EP3",
            "year": 2004,
            "manufacturer": "Honda",
            "model": "Civic Type R EP3",
            "engine": "K20A2",
            "mileage": 151500,
        }

        components = [
            {
                "id": "root-engine",
                "component_type": "system",
                "system_key": "engine",
                "name": "Engine",
                "lifecycle_status": "installed",
            },
            {
                "id": "ecu",
                "component_type": "component",
                "system_key": "engine",
                "name": "K100 ECU",
                "lifecycle_status": "installed",
                "manufacturer": "Hondata",
                "is_oem": False,
            },
            {
                "id": "cams",
                "component_type": "component",
                "system_key": "engine",
                "name": "Camshafts",
                "lifecycle_status": "planned",
                "is_oem": False,
            },
        ]

        context = build_vehicle_intelligence_context(
            vehicle=vehicle,
            components=components,
            specifications=[
                {
                    "component_id": "ecu",
                    "label": "ECU calibration",
                    "value_text": "K100",
                    "value_numeric": None,
                    "unit": None,
                    "confidence": "verified",
                    "is_current": True,
                    "source_kind": "user",
                    "source_reference": "VCG build record",
                }
            ],
            maintenance_items=[
                {
                    "title": "Oil service",
                    "status": "pending",
                    "category": "service",
                    "priority": "high",
                    "due_mileage": 151000,
                    "due_date": None,
                }
            ],
            maintenance_records=[
                {
                    "title": "Brake fluid",
                    "category": "fluid",
                    "performed_at": "2026-09-01",
                    "performed_mileage": 150000,
                    "twin_component_id": "root-engine",
                }
            ],
            component_events=[
                {
                    "component_id": "ecu",
                    "event_type": "installed",
                    "occurred_at": "2026-08-01T10:00:00Z",
                    "mileage": 149000,
                }
            ],
            build_plan_items=[
                {
                    "component_id": "cams",
                    "action": "install",
                    "status": "planned",
                    "priority": "normal",
                    "compatibility_status": "unknown",
                }
            ],
        )

        self.assertIn(
            "CURRENT PHYSICAL BUILD",
            context,
        )
        self.assertIn(
            "K100 ECU",
            context,
        )
        self.assertIn(
            "ACTIVE FUTURE BUILD PLAN",
            context,
        )
        self.assertIn(
            "Camshafts; action=install",
            context,
        )
        self.assertIn(
            "state=overdue",
            context,
        )
        self.assertIn(
            "Brake fluid",
            context,
        )
        self.assertIn(
            "event=installed",
            context,
        )

    @patch(
        "vehicle_intelligence_context.maintenance_is_due_soon",
        return_value=False,
    )
    @patch(
        "vehicle_intelligence_context.maintenance_is_overdue",
        return_value=False,
    )
    def test_only_verified_current_specs_are_included(
        self,
        _overdue,
        _due_soon,
    ):
        context = build_vehicle_intelligence_context(
            vehicle={
                "profile_name": "Car",
                "mileage": 0,
            },
            components=[],
            specifications=[
                {
                    "label": "Verified",
                    "value_text": "yes",
                    "confidence": "verified",
                    "is_current": True,
                    "source_kind": "measurement",
                },
                {
                    "label": "Unverified",
                    "value_text": "no",
                    "confidence": "high",
                    "is_current": True,
                    "source_kind": "user",
                },
                {
                    "label": "Old verified",
                    "value_text": "old",
                    "confidence": "verified",
                    "is_current": False,
                    "source_kind": "user",
                },
            ],
            maintenance_items=[],
            maintenance_records=[],
            component_events=[],
            build_plan_items=[],
        )

        self.assertIn(
            "Verified; value=yes",
            context,
        )
        self.assertNotIn(
            "Unverified; value=no",
            context,
        )
        self.assertNotIn(
            "Old verified; value=old",
            context,
        )


if __name__ == "__main__":
    unittest.main()
