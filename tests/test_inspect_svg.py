from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.inspect_svg import inspect


class InspectSvgTests(unittest.TestCase):
    def inspect_fixture(self, source: str) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fixture.svg"
            path.write_text(source, encoding="utf-8")
            return inspect(path)

    def test_hierarchy_and_accumulated_transform_bounds(self) -> None:
        report = self.inspect_fixture(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<g id="parent" transform="translate(10 20)">'
            '<rect id="child" x="2" y="3" width="4" height="5" transform="scale(2)"/>'
            '</g></svg>'
        )
        parent = next(item for item in report["elementTree"] if item["id"] == "parent")
        child = next(item for item in report["elementTree"] if item["id"] == "child")
        self.assertEqual(child["parentUid"], parent["uid"])
        self.assertIn(child["uid"], parent["childUids"])
        self.assertEqual(child["worldMatrix"], [2.0, 0.0, 0.0, 2.0, 10.0, 20.0])
        self.assertEqual(child["worldBounds"], {"x": 14.0, "y": 26.0, "width": 8.0, "height": 10.0})

    def test_use_image_reference_and_clip_definition_are_resolved(self) -> None:
        report = self.inspect_fixture(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 100 100">'
            '<defs><image id="photo" width="10" height="20" '
            'xlink:href="data:image/png;base64,QUJD"/></defs>'
            '<g id="holder" transform="translate(5 7)">'
            '<use id="photoUse" x="3" y="4" xlink:href="#photo"/>'
            '</g>'
            '<rect id="clipped" width="12" height="12" clip-path="url(#clip1)"/>'
            '<clipPath id="clip1"><rect width="8" height="8"/></clipPath>'
            '</svg>'
        )
        use_ref = next(ref for ref in report["internalReferences"] if ref["fromId"] == "photoUse")
        self.assertEqual(use_ref["targetId"], "photo")
        self.assertEqual(use_ref["resolution"], "resolved")
        self.assertEqual(
            report["useInstances"][0]["instanceMatrixBeforeTargetTransform"],
            [1.0, 0.0, 0.0, 1.0, 8.0, 11.0],
        )
        image = report["images"][0]
        self.assertEqual(image["mimeType"], "image/png")
        self.assertEqual(image["referencedBy"][0]["sourceId"], "photoUse")
        self.assertTrue(
            any(effect["id"] == "clipped" and effect["kind"] == "clip-path" for effect in report["effects"])
        )

    def test_percent_geometry_is_not_treated_as_absolute_number(self) -> None:
        report = self.inspect_fixture(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect id="relative" x="10%" y="0" width="50%" height="20"/>'
            '</svg>'
        )
        rect = next(item for item in report["elementTree"] if item["id"] == "relative")
        self.assertIsNone(rect["worldBounds"])
        self.assertEqual(rect["geometry"]["x"], "10%")


if __name__ == "__main__":
    unittest.main()
