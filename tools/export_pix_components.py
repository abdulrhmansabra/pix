#!/usr/bin/env python3
"""Export verified source SVG artwork into transparent PNG and lossless WebP crops.

Run from the repository root:
    python -m pip install CairoSVG Pillow
    python tools/export_pix_components.py pix.svg --out generated/pix-artwork
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
from PIL import Image

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
SVG_TAG = f"{{{SVG_NS}}}svg"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def node_at(root: ET.Element, path: tuple[int, ...]) -> ET.Element:
    node = root
    for index in path:
        node = list(node)[index]
    return node


def clip_viewbox(root: ET.Element, clip_id: str) -> tuple[float, float, float, float]:
    for clip in root.iter():
        if local_name(clip.tag) != "clipPath" or clip.get("id") != clip_id:
            continue
        rect = next((child for child in clip if local_name(child.tag) == "rect"), None)
        if rect is None:
            raise ValueError(f"Clip path {clip_id} does not contain a rect")
        x, y = float(rect.get("x", "0")), float(rect.get("y", "0"))
        width, height = float(rect.attrib["width"]), float(rect.attrib["height"])
        match = re.search(r"translate\(\s*([\d.+-]+)(?:[ ,]+([\d.+-]+))?", rect.get("transform", ""))
        if match:
            x += float(match.group(1))
            y += float(match.group(2) or 0)
        return x, y, width, height
    raise KeyError(f"Clip path not found: {clip_id}")


def clone_branch(root: ET.Element, path: tuple[int, ...], children: list[int] | None,
                 remove_masks: bool = False) -> ET.Element:
    nodes = [root]
    target = root
    for index in path:
        target = list(target)[index]
        nodes.append(target)
    if children is None:
        selected = copy.deepcopy(target)
    else:
        selected = ET.Element(target.tag, dict(target.attrib))
        original_children = list(target)
        for index in children:
            selected.append(copy.deepcopy(original_children[index]))
    for ancestor in reversed(nodes[1:-1]):
        wrapper = ET.Element(ancestor.tag, dict(ancestor.attrib))
        wrapper.append(selected)
        selected = wrapper
    if remove_masks:
        for element in selected.iter():
            element.attrib.pop("mask", None)
    return selected


class Exporter:
    def __init__(self, svg_path: Path, output_dir: Path):
        self.svg_path, self.output_dir = svg_path, output_dir
        self.root = ET.parse(svg_path).getroot()
        self.defs = next((c for c in self.root if local_name(c.tag) == "defs"), None)
        if self.defs is None:
            raise ValueError("SVG root has no defs element")
        self.assets: list[dict] = []

    def render(self, name: str, path: tuple[int, ...], children: list[int] | None = None,
               viewbox: tuple[float, float, float, float] | None = None,
               clip: str | None = None, remove_masks: bool = False):
        if clip:
            viewbox = clip_viewbox(self.root, clip)
        if viewbox is None:
            raise ValueError(f"{name}: viewBox or clip path is required")
        x, y, width, height = viewbox
        frame = ET.Element(SVG_TAG, {
            "width": f"{width:g}", "height": f"{height:g}",
            "viewBox": f"{x:g} {y:g} {width:g} {height:g}"
        })
        frame.append(copy.deepcopy(self.defs))
        frame.append(clone_branch(self.root, path, children, remove_masks))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        png = self.output_dir / f"{name}.png"
        cairosvg.svg2png(
            bytestring=ET.tostring(frame, encoding="utf-8", xml_declaration=True),
            write_to=str(png), output_width=max(1, round(width)),
            output_height=max(1, round(height))
        )
        image = Image.open(png).convert("RGBA")
        bounds = image.getchannel("A").getbbox()
        if bounds:
            image = image.crop(bounds)
        image.save(png, optimize=True)
        webp = self.output_dir / f"{name}.webp"
        image.save(webp, "WEBP", lossless=True, method=6)
        self.assets.append({
            "name": name, "sourceNodePath": list(path),
            "selectedChildIndices": children, "clipPath": clip,
            "viewBox": [x, y, width, height],
            "width": image.width, "height": image.height,
            "png": png.name, "pngBytes": png.stat().st_size,
            "webp": webp.name, "webpBytes": webp.stat().st_size,
            "webpLossless": True,
            "sha256Webp": hashlib.sha256(webp.read_bytes()).hexdigest()
        })
        print(f"{name}: {image.width}x{image.height}, {webp.stat().st_size:,} byte lossless WebP")

    def export(self):
        # Four exact template photo subtrees; original pattern and nested clipping stay intact.
        cards = [
            ((0, 20), "clip3_0_1"), ((0, 21), "clip6_0_1"),
            ((0, 22), "clip9_0_1"), ((0, 23), "clip12_0_1")
        ]
        for index, (path, clip) in enumerate(cards, 1):
            self.render(f"template_photo_{index:02d}", path, [1], clip=clip)
        self.render("profile_photo_01", (1, 21), clip="clip31_0_1")
        self.render("profile_photo_02", (1, 22), clip="clip32_0_1")

        # Header artwork differs between the two original screens.
        self.render("template_gift_action", (0, 3), clip="clip2_0_1")
        self.render("profile_gift_action", (1, 4), clip="clip22_0_1")
        self.render("search", (0, 1), clip="clip1_0_1")
        self.render("settings", (1, 2), clip="clip21_0_1")
        self.render("credit_lightning_template", (0, 5), viewbox=(1922.47, 60.2938, 29.62, 35.9648))
        self.render("credit_lightning_profile", (1, 6), viewbox=(722.105, 60, 29.474, 35.7895))

        self.render("promotion_gem", (1, 18), [3], clip="clip25_0_1")
        self.render("invite_gift", (1, 18), [7], clip="clip26_0_1")
        self.render("usage_sparkle", (0, 20, 5), [0, 1], clip="clip5_0_1")

        self.render("nav_discover", (0, 25), [0], clip="clip15_0_1")
        self.render("nav_templates_active", (0, 26), [0], clip="clip16_0_1")
        self.render("nav_inbox", (0, 27), [0], clip="clip18_0_1")
        # The full source frame visibly shows this as a head circle plus shoulder ring.
        # Removing its mask reference corrects CairoSVG's divergent masked result only in this export.
        self.render("nav_profile", (0, 28), [0, 2], clip="clip19_0_1", remove_masks=True)
        self.render("nav_templates", (1, 25), [0], clip="clip34_0_1")
        self.render("nav_profile_active", (1, 27), [0, 1], clip="clip37_0_1")

        self.render("private_folder", (1, 19, 0), [0], clip="clip28_0_1")
        self.render("private_lock", (1, 19, 0), [1], clip="clip28_0_1")
        self.render("collection_grid", (1, 19, 1), [0], clip="clip29_0_1")
        self.render("agent_category", (0, 19), viewbox=(2131.22, 235.066, 35.965, 35.965))

        manifest = {
            "manifestVersion": 2, "sourceSvg": self.svg_path.name,
            "sourceBytes": self.svg_path.stat().st_size,
            "sourceSha256": hashlib.sha256(self.svg_path.read_bytes()).hexdigest(),
            "rasterScale": "1 pixel per SVG user unit",
            "assets": self.assets,
            "notes": [
                "Crops are taken from the listed SVG nodes and exact original clip paths.",
                "The source defs, image references, patterns and gradients are retained during rendering.",
                "Template photo crops preserve source composition exactly, including partial adjacent image content where present.",
                "Navigation labels and other dynamic text are not part of the icon resources.",
                "All WebP files are lossless encodings of their exported PNG pixels.",
                "For nav_profile only, the mask reference is omitted in the exported copy because CairoSVG output otherwise differs from the full-frame source rendering; the source SVG is not changed.",
                "The original pix.svg and pix.css are read-only inputs."
            ]
        }
        (self.output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"Exported {len(self.assets)} assets to {self.output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="Original pix.svg")
    parser.add_argument("--out", type=Path, default=Path("generated/pix-artwork"))
    args = parser.parse_args()
    if not args.svg.is_file():
        parser.error(f"SVG file not found: {args.svg}")
    Exporter(args.svg, args.out).export()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
