import unittest
import xml.etree.ElementTree as ET

from PIL import Image

from tools.export_pix_components import (
    clone_branch,
    clip_viewbox,
    make_black_counters_transparent,
)


class ExportPixComponentsTests(unittest.TestCase):
    def test_clip_viewbox_applies_rect_translate(self):
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg"><defs>'
            '<clipPath id="card"><rect width="320" height="420" '
            'transform="translate(12 34)"/></clipPath></defs></svg>'
        )
        self.assertEqual(clip_viewbox(root, "card"), (12.0, 34.0, 320.0, 420.0))

    def test_clone_branch_keeps_only_selected_children(self):
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg"><g id="screen">'
            '<g id="icon"><path id="shape"/><path id="label"/></g>'
            '</g></svg>'
        )
        result = clone_branch(root, (0, 0), [0])
        ids = [node.get("id") for node in result.iter() if node.get("id")]
        self.assertEqual(ids, ["screen", "icon", "shape"])


    def test_black_counter_pixels_become_transparent_without_touching_artwork(self):
        image = Image.new("RGBA", (3, 1))
        image.putdata([
            (0, 0, 0, 255),
            (241, 242, 244, 255),
            (0, 0, 0, 0),
        ])
        result = make_black_counters_transparent(image)
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(result.getpixel((1, 0)), (241, 242, 244, 255))
        self.assertEqual(result.getpixel((2, 0)), (0, 0, 0, 0))

    def test_remove_masks_only_from_exported_copy(self):
        root = ET.fromstring(
            '<svg xmlns="http://www.w3.org/2000/svg"><g>'
            '<path id="shoulder" mask="url(#m)"/><mask id="m"/></g></svg>'
        )
        result = clone_branch(root, (0,), [0, 1], remove_masks=True)
        copied_path = next(node for node in result.iter() if node.get("id") == "shoulder")
        original_path = next(node for node in root.iter() if node.get("id") == "shoulder")
        self.assertIsNone(copied_path.get("mask"))
        self.assertEqual(original_path.get("mask"), "url(#m)")


if __name__ == "__main__":
    unittest.main()
