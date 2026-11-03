#!/usr/bin/env python3
"""Inspect a Figma-exported SVG without changing the source file.

Usage:
  python tools/inspect_svg.py pix.svg --out generated/svg-inspection.json

The report inventories real SVG IDs, named groups, text nodes, image payloads,
clipping/masking/filter references, and element counts. It does not redraw,
rename, optimize, or rewrite the source SVG.
"""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

INKSCAPE = "{http://www.inkscape.org/namespaces/inkscape}label"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def inspect(path: Path) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    ids: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    texts: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []
    references: list[dict[str, str]] = []
    root = ET.parse(path).getroot()

    for node in root.iter():
        tag = local_name(node.tag)
        counts[tag] += 1
        element_id = node.attrib.get("id")
        label = node.attrib.get(INKSCAPE) or node.attrib.get("data-name")
        if element_id:
            ids.append({"id": element_id, "tag": tag, "label": label})
        if tag == "g" and (element_id or label):
            groups.append({"id": element_id, "label": label})
        if tag in {"text", "tspan"}:
            value = "".join(node.itertext()).strip()
            if value:
                texts.append({"id": element_id, "text": value})
        if tag == "image":
            href = node.attrib.get("href") or node.attrib.get(XLINK_HREF) or ""
            embedded = href.startswith("data:")
            match = re.match(r"data:([^;,]+)(?:;base64)?,", href) if embedded else None
            images.append({
                "id": element_id,
                "hrefType": "embedded-data" if embedded else ("external" if href else "missing"),
                "mimeType": match.group(1) if match else None,
                "payloadCharacters": max(0, len(href) - href.find(",") - 1) if embedded and "," in href else 0,
                "x": node.attrib.get("x"), "y": node.attrib.get("y"),
                "width": node.attrib.get("width"), "height": node.attrib.get("height"),
                "preserveAspectRatio": node.attrib.get("preserveAspectRatio"),
            })
        for attr in ("clip-path", "mask", "filter"):
            value = node.attrib.get(attr)
            if value:
                effects.append({"id": element_id, "tag": tag, "kind": attr, "value": value})
        for attr, value in node.attrib.items():
            if attr in {"href", XLINK_HREF} and value.startswith("#"):
                references.append({"from": element_id or tag, "attribute": local_name(attr), "target": value[1:]})

    return {
        "sourceFile": path.name,
        "sourceBytes": path.stat().st_size,
        "root": {"tag": local_name(root.tag), "viewBox": root.attrib.get("viewBox"),
                 "width": root.attrib.get("width"), "height": root.attrib.get("height")},
        "elementCounts": dict(sorted(counts.items())),
        "idCount": len(ids),
        "ids": ids,
        "namedGroups": groups,
        "textNodes": texts,
        "images": images,
        "effects": effects,
        "internalReferences": references,
        "notes": [
            "This is a structural inventory, not a visual or pixel-parity validation.",
            "Review image crops, masks, clipping paths, filters, and referenced definitions before exporting artwork.",
            "The source SVG is read-only; this report does not modify it."
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="Path to the original SVG export")
    parser.add_argument("--out", type=Path, default=Path("generated/svg-inspection.json"))
    args = parser.parse_args()
    report = inspect(args.svg)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Inspected {report['sourceBytes']} bytes; found {report['idCount']} IDs, "
          f"{len(report['namedGroups'])} named groups, and {len(report['images'])} image elements.")
    print(f"Report: {args.out}")


if __name__ == "__main__":
    main()
