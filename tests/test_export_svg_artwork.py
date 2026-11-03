import base64
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.export_svg_artwork import (
    extract_embedded_images,
    parse_data_uri,
    validate_viewport,
)


class ExportSvgArtworkTests(unittest.TestCase):
    def test_data_uri_base64_is_decoded_without_modification(self):
        original = b"\x89PNG\r\n\x1a\nsource-pixels"
        uri = "data:image/png;base64," + base64.b64encode(original).decode("ascii")
        mime, payload = parse_data_uri(uri)
        self.assertEqual(mime, "image/png")
        self.assertEqual(payload, original)

    def test_percent_encoded_data_uri_is_supported(self):
        mime, payload = parse_data_uri("data:image/svg+xml,%3Csvg%2F%3E")
        self.assertEqual(mime, "image/svg+xml")
        self.assertEqual(payload, b"<svg/>")

    def test_base64_whitespace_is_ignored(self):
        original = b"embedded-payload"
        encoded = base64.b64encode(original).decode("ascii")
        wrapped = encoded[:5] + "\\n  " + encoded[5:]
        mime, payload = parse_data_uri("data:image/png;base64," + wrapped)
        self.assertEqual(mime, "image/png")
        self.assertEqual(payload, original)

    def test_embedded_image_is_saved_and_use_reference_is_recorded(self):
        original = b"tiny-image-payload"
        encoded = base64.b64encode(original).decode("ascii")
        source = f"""
        <svg xmlns="http://www.w3.org/2000/svg">
          <defs>
            <image id="source-photo" width="160" height="160"
              href="data:image/png;base64,{encoded}" />
          </defs>
          <g clip-path="url(#photo-clip)">
            <use id="photo-instance" href="#source-photo"
              transform="translate(4 7) scale(0.5)" />
          </g>
        </svg>
        """
        root = ET.fromstring(source)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            items = extract_embedded_images(root, out)
            self.assertEqual(len(items), 1)
            item = items[0]
            self.assertEqual(item["id"], "source-photo")
            self.assertEqual(item["status"], "extracted")
            self.assertEqual(item["width"], "160")
            self.assertEqual((out / item["file"]).read_bytes(), original)
            self.assertEqual(item["referencedBy"][0]["sourceId"], "photo-instance")
            self.assertEqual(
                item["referencedBy"][0]["sourceTransform"],
                "translate(4 7) scale(0.5)",
            )
            # Re-running into the same generated directory is safe.
            repeated = extract_embedded_images(root, out)
            self.assertEqual(repeated[0]["sha256"], item["sha256"])
            self.assertEqual((out / item["file"]).read_bytes(), original)

    def test_viewport_must_fit_source_viewbox(self):
        validate_viewport((1200, 0, 1080, 2115), (0, 0, 2280, 2115))
        with self.assertRaises(ValueError):
            validate_viewport((1201, 0, 1080, 2115), (0, 0, 2280, 2115))


if __name__ == "__main__":
    unittest.main()
