import unittest
from pathlib import Path


class TestVirtualWorkshopUI(unittest.TestCase):

    def test_svg_is_rendered_as_html_component(self):
        source = Path(
            "virtual_workshop_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "st_components.html(",
            source,
        )
        self.assertNotIn(
            "st.markdown(\n            workshop_blueprint_html(",
            source,
        )

    def test_streamlit_component_module_is_not_shadowed_by_components_argument(self):
        source = Path(
            "virtual_workshop_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "import streamlit.components.v1 as st_components",
            source,
        )
        self.assertIn(
            "st_components.html(",
            source,
        )
        self.assertNotIn(
            "\n        components.html(",
            source,
        )

    def test_workshop_uses_system_dropdown(self):
        source = Path(
            "virtual_workshop_ui.py"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'st.selectbox(\n        "Inspect system"',
            source,
        )
        self.assertNotIn(
            '"#### Select vehicle system"',
            source,
        )


if __name__ == "__main__":
    unittest.main()
