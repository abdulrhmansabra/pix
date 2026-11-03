#!/usr/bin/env python3
"""Export embedded raster sources and exact frame crops from the original Pix SVG.

This is a source-preserving export step. It does not guess SVG node names or
claim that a full-screen crop is an individual reusable component.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import unquote_to_bytes

XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def href_of(node: ET.Element) -> str:
    return node.attrib.get("href") or node.attrib.get(XLINK_HREF) or ""


def parse_data_uri(uri: str) -> tuple[str, bytes]:
    """Decode a data URI without changing the embedded image bytes."""
    if not uri.startswith("data:") or "," not in uri:
        raise ValueError("Expected an embedded data URI")
    header, payload = uri[5:].split(",", 1)
    parts = header.split(";")
    mime_type = parts[0].strip().lower() or "application/octet-stream"
    if "base64" in {part.strip().lower() for part in parts[1:]}:
        # SVG exporters may wrap base64 data URIs across lines. Whitespace is not payload.
        payload = re.sub(r"\\s+", "", payload)
        try:
            content = base64.b64decode(payload, validate=True)
        except Exception as exc:
            raise ValueError(f"Invalid base64 payload for {mime_type}") from exc
    else:
        content = unquote_to_bytes(payload)
    if not content:
        raise ValueError(f"Embedded image payload is empty ({mime_type})")
    return mime_type, content


def safe_stem(value: str, fallback: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", value or "").strip("._")
    return stem or fallback


def collect_internal_href_references(root: ET.Element) -> dict[str, list[dict[str, Any]]]:
    """Index local href references so extracted sources keep their real usage links."""
    by_target: dict[str, list[dict[str, Any]]] = {}
    for node in root.iter():
        href = href_of(node)
        if not href.startswith("#"):
            continue
        target = href[1:]
        by_target.setdefault(target, []).append({
            "sourceTag": local_name(node.tag),
            "sourceId": node.attrib.get("id"),
            "sourceTransform": node.attrib.get("transform"),
            "sourceClipPath": node.attrib.get("clip-path"),
            "sourceMask": node.attrib.get("mask"),
        })
    return by_target


def extract_embedded_images(root: ET.Element, output_dir: Path) -> list[dict[str, Any]]:
    """Write embedded <image> payloads byte-for-byte and return their provenance."""
    output_dir.mkdir(parents=True, exist_ok=True)
    references = collect_internal_href_references(root)
    results: list[dict[str, Any]] = []

    for index, node in enumerate(root.iter()):
        if local_name(node.tag) != "image":
            continue
        href = href_of(node)
        image_id = node.attrib.get("id") or f"image_{index}"
        if not href.startswith("data:"):
            results.append({
                "id": image_id,
                "mimeType": None,
                "status": "not-embedded",
                "hrefType": "external" if href else "missing",
                "referencedBy": references.get(image_id, []),
            })
            continue

        mime_type, payload = parse_data_uri(href)
        extension = EXTENSIONS.get(mime_type)
        if extension is None:
            raise ValueError(
                f"Unsupported embedded image MIME type {mime_type!r} on element {image_id!r}"
            )
        filename = safe_stem(image_id, f"image_{index}") + extension
        destination = output_dir / filename
        # The output directory is generated data; rerunning the exporter is intentionally idempotent.
        destination.write_bytes(payload)

        results.append({
            "id": image_id,
            "status": "extracted",
            "mimeType": mime_type,
            "file": filename,
            "width": node.attrib.get("width"),
            "height": node.attrib.get("height"),
            "preserveAspectRatio": node.attrib.get("preserveAspectRatio"),
            "payloadBytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "referencedBy": references.get(image_id, []),
        })
    return results


def parse_viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    raw = root.attrib.get("viewBox")
    if not raw:
        raise ValueError("The SVG root has no viewBox; refusing to assume frame coordinates")
    values = [float(part) for part in re.split(r"[\s,]+", raw.strip()) if part]
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        raise ValueError(f"Unsupported SVG viewBox: {raw!r}")
    return values[0], values[1], values[2], values[3]


def validate_viewport(
    viewport: tuple[float, float, float, float],
    source_viewbox: tuple[float, float, float, float],
) -> None:
    x, y, width, height = viewport
    sx, sy, sw, sh = source_viewbox
    epsilon = 1e-6
    if width <= 0 or height <= 0:
        raise ValueError("Frame width and height must be positive")
    if (x < sx - epsilon or y < sy - epsilon or
            x + width > sx + sw + epsilon or y + height > sy + sh + epsilon):
        raise ValueError(
            f"Requested viewport {viewport} falls outside source viewBox {source_viewbox}"
        )


def render_frame(
    svg_path: Path,
    output_path: Path,
    viewport: tuple[float, float, float, float],
    scale: float,
) -> dict[str, Any]:
    """Render a frame by changing only the root viewport; keep all SVG descendants."""
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError(
            "CairoSVG is required for frame PNGs. Install it with "
            "'python -m pip install CairoSVG', or use --skip-render to export "
            "the original embedded image payloads only."
        ) from exc

    x, y, width, height = viewport
    root = ET.fromstring(svg_path.read_bytes())
    root.set("viewBox", f"{x:g} {y:g} {width:g} {height:g}")
    root.set("width", f"{width:g}px")
    root.set("height", f"{height:g}px")
    output_width = round(width * scale)
    output_height = round(height * scale)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(
        bytestring=ET.tostring(root, encoding="utf-8", xml_declaration=True),
        write_to=str(output_path),
        output_width=output_width,
        output_height=output_height,
    )
    return {
        "file": output_path.name,
        "viewport": {"x": x, "y": y, "width": width, "height": height},
        "outputPixels": {"width": output_width, "height": output_height},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="Path to the original pix.svg")
    parser.add_argument(
        "--out", type=Path, default=Path("generated/svg-artwork"),
        help="Export directory (default: generated/svg-artwork)",
    )
    parser.add_argument(
        "--template-x", type=float, default=1200.0,
        help="Left edge of the Template browsing frame in SVG coordinates (default: 1200)",
    )
    parser.add_argument(
        "--profile-x", type=float, default=0.0,
        help="Left edge of the Profile frame in SVG coordinates (default: 0)",
    )
    parser.add_argument("--scale", type=float, default=1.0, help="PNG output scale (default: 1)")
    parser.add_argument(
        "--skip-render", action="store_true",
        help="Extract embedded source images only; do not render frame PNGs",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.scale <= 0:
        raise SystemExit("--scale must be greater than zero")

    svg_path = args.svg
    if not svg_path.is_file():
        raise SystemExit(f"SVG file not found: {svg_path}")

    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        source_viewbox = parse_viewbox(root)
        args.out.mkdir(parents=True, exist_ok=True)

        embedded_dir = args.out / "embedded"
        embedded_images = extract_embedded_images(root, embedded_dir)

        frame_specs = [
            ("template-browsing", args.template_x, 0.0, 1080.0, 2115.0),
            ("profile", args.profile_x, 0.0, 1080.0, 2106.0),
        ]
        frame_exports: list[dict[str, Any]] = []
        if not args.skip_render:
            for name, x, y, width, height in frame_specs:
                viewport = (x, y, width, height)
                validate_viewport(viewport, source_viewbox)
                result = render_frame(
                    svg_path, args.out / f"{name}.png", viewport, args.scale
                )
                result["name"] = name
                frame_exports.append(result)

        manifest = {
            "manifestVersion": 1,
            "source": {
                "file": svg_path.name,
                "bytes": svg_path.stat().st_size,
                "sha256": hashlib.sha256(svg_path.read_bytes()).hexdigest(),
                "viewBox": list(source_viewbox),
            },
            "frameExports": frame_exports,
            "embeddedImages": embedded_images,
            "notes": [
                "Embedded image payloads are copied byte-for-byte from their SVG data URIs.",
                "The frame PNGs are full-screen visual references, not individual PixArtwork component assets.",
                "Image use references are recorded; their original clip paths and transforms remain in pix.svg.",
                "No SVG path, gradient, pattern, mask, clipPath, CSS, or source file is rewritten.",
                "CairoSVG output is a raster preview and must be visually checked against the original design.",
                "Component-level SVG node-to-CSS mapping remains a separate verification step.",
            ],
        }
        manifest_path = args.out / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (ET.ParseError, OSError, ValueError, RuntimeError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1

    extracted_count = sum(item.get("status") == "extracted" for item in embedded_images)
    print(f"Extracted {extracted_count} embedded image(s) into {embedded_dir}")
    if frame_exports:
        print(f"Rendered {len(frame_exports)} frame reference PNG(s) into {args.out}")
    else:
        print("Frame rendering skipped.")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
