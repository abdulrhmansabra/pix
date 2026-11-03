#!/usr/bin/env python3
"""Inspect a Figma-exported SVG without changing the source file.

Usage:
  python tools/inspect_svg.py pix.svg --out generated/svg-inspection.json

The report inventories IDs, hierarchy, transforms, basic geometry, references,
image instances, text, and clipping/masking/filter relationships. It is a
read-only structural inspection; it does not redraw or rewrite the SVG.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

INKSCAPE = "{http://www.inkscape.org/namespaces/inkscape}label"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?")
TRANSFORM = re.compile(r"([A-Za-z]+)\s*\(([^)]*)\)")
URL_REF = re.compile(r"""url\(\s*['\"]?#([^\s)'"]+)['\"]?\s*\)""")

# Affine matrix [a, b, c, d, e, f]: x'=a*x+c*y+e; y'=b*x+d*y+f.
IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
GEOMETRY_ATTRS = (
    "x", "y", "width", "height", "x1", "y1", "x2", "y2",
    "cx", "cy", "r", "rx", "ry", "d", "points", "viewBox",
)
STYLE_ATTRS = (
    "fill", "fill-opacity", "stroke", "stroke-width", "stroke-linecap",
    "stroke-linejoin", "stroke-opacity", "opacity", "display", "visibility",
    "clip-path", "mask", "filter", "style",
)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def number(value: str | None) -> float | None:
    if value is None:
        return None
    raw = value.strip()
    # Accept SVG unitless numbers and px values only. Percentages and other
    # physical units remain in the raw attribute instead of being misread.
    if raw.endswith("px"):
        raw = raw[:-2].strip()
    if not re.fullmatch(NUMBER, raw):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def numbers(value: str | None) -> list[float]:
    if not value:
        return []
    return [float(x) for x in NUMBER.findall(value)]


def multiply(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    a, b, c, d, e, f = left
    g, h, i, j, k, l = right
    return (
        a * g + c * h,
        b * g + d * h,
        a * i + c * j,
        b * i + d * j,
        a * k + c * l + e,
        b * k + d * l + f,
    )


def parse_transform(raw: str | None, diagnostics: list[dict[str, str]], element_id: str | None) -> tuple[float, ...]:
    if not raw:
        return IDENTITY
    result = IDENTITY
    position = 0
    for match in TRANSFORM.finditer(raw):
        if raw[position:match.start()].strip(" ,\t\r\n"):
            diagnostics.append({"elementId": element_id or "", "value": raw, "warning": "Unparsed transform syntax"})
        name = match.group(1)
        args = numbers(match.group(2))
        op = IDENTITY
        try:
            if name == "matrix" and len(args) == 6:
                op = tuple(args)
            elif name == "translate" and len(args) in (1, 2):
                op = (1.0, 0.0, 0.0, 1.0, args[0], args[1] if len(args) == 2 else 0.0)
            elif name == "scale" and len(args) in (1, 2):
                op = (args[0], 0.0, 0.0, args[1] if len(args) == 2 else args[0], 0.0, 0.0)
            elif name == "rotate" and len(args) in (1, 3):
                angle = math.radians(args[0])
                c, s = math.cos(angle), math.sin(angle)
                rotation = (c, s, -s, c, 0.0, 0.0)
                if len(args) == 3:
                    cx, cy = args[1], args[2]
                    op = multiply(multiply((1, 0, 0, 1, cx, cy), rotation), (1, 0, 0, 1, -cx, -cy))
                else:
                    op = rotation
            elif name == "skewX" and len(args) == 1:
                op = (1.0, 0.0, math.tan(math.radians(args[0])), 1.0, 0.0, 0.0)
            elif name == "skewY" and len(args) == 1:
                op = (1.0, math.tan(math.radians(args[0])), 0.0, 1.0, 0.0, 0.0)
            else:
                diagnostics.append({"elementId": element_id or "", "value": match.group(0), "warning": "Unsupported or malformed transform"})
                position = match.end()
                continue
            # SVG transform lists are composed in source order (matrix multiplication).
            result = multiply(result, op)
        except (ValueError, OverflowError):
            diagnostics.append({"elementId": element_id or "", "value": match.group(0), "warning": "Could not evaluate transform"})
        position = match.end()
    if raw[position:].strip(" ,\t\r\n") or not TRANSFORM.search(raw):
        diagnostics.append({"elementId": element_id or "", "value": raw, "warning": "Unparsed transform syntax"})
    return result


def matrix_list(matrix: tuple[float, ...]) -> list[float]:
    return [round(v, 8) for v in matrix]


def transformed_bounds(bounds: tuple[float, float, float, float], matrix: tuple[float, ...]) -> dict[str, float]:
    x, y, width, height = bounds
    a, b, c, d, e, f = matrix
    points = [
        (a * px + c * py + e, b * px + d * py + f)
        for px, py in ((x, y), (x + width, y), (x, y + height), (x + width, y + height))
    ]
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return {
        "x": round(min(xs), 6), "y": round(min(ys), 6),
        "width": round(max(xs) - min(xs), 6), "height": round(max(ys) - min(ys), 6),
    }


def primitive_bounds(tag: str, attrs: dict[str, str]) -> tuple[float, float, float, float] | None:
    def n(key: str, default: float = 0.0) -> float | None:
        value = number(attrs.get(key))
        return default if value is None and key not in attrs else value

    if tag in {"rect", "image", "foreignObject", "svg"}:
        x, y, w, h = n("x"), n("y"), n("width"), n("height")
        return (x, y, w, h) if None not in (x, y, w, h) else None
    if tag == "circle":
        cx, cy, r = n("cx"), n("cy"), n("r")
        return (cx - r, cy - r, 2 * r, 2 * r) if None not in (cx, cy, r) else None
    if tag == "ellipse":
        cx, cy, rx, ry = n("cx"), n("cy"), n("rx"), n("ry")
        return (cx - rx, cy - ry, 2 * rx, 2 * ry) if None not in (cx, cy, rx, ry) else None
    if tag == "line":
        x1, y1, x2, y2 = n("x1"), n("y1"), n("x2"), n("y2")
        return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)) if None not in (x1, y1, x2, y2) else None
    return None


def inspect(path: Path) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    ids: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    texts: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []
    references: list[dict[str, Any]] = []
    elements: list[dict[str, Any]] = []
    transform_diagnostics: list[dict[str, str]] = []
    id_to_nodes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    node_by_uid: dict[str, dict[str, Any]] = {}
    tree = ET.parse(path)
    root = tree.getroot()

    def walk(node: ET.Element, parent: dict[str, Any] | None, depth: int, path_key: str,
             parent_matrix: tuple[float, ...]) -> dict[str, Any]:
        tag = local_name(node.tag)
        counts[tag] += 1
        index = len(elements)
        uid = f"n{index:04d}"
        attrs = {local_name(k): v for k, v in node.attrib.items()}
        element_id = attrs.get("id")
        label = node.attrib.get(INKSCAPE) or attrs.get("data-name")
        local_matrix = parse_transform(attrs.get("transform"), transform_diagnostics, element_id)
        world_matrix = multiply(parent_matrix, local_matrix)
        geom = {key: attrs[key] for key in GEOMETRY_ATTRS if key in attrs}
        style = {key: attrs[key] for key in STYLE_ATTRS if key in attrs}
        href = node.attrib.get("href") or node.attrib.get(XLINK_HREF)
        if href:
            geom["href"] = href if not href.startswith("data:") else f"data:{href[5:35]}…"

        local_bounds = primitive_bounds(tag, attrs)
        world_bounds = transformed_bounds(local_bounds, world_matrix) if local_bounds else None
        record: dict[str, Any] = {
            "uid": uid,
            "id": element_id,
            "tag": tag,
            "label": label,
            "parentUid": parent["uid"] if parent else None,
            "parentId": parent["id"] if parent else None,
            "depth": depth,
            "treePath": path_key,
            "childUids": [],
            "geometry": geom,
            "style": style,
            "transform": attrs.get("transform"),
            "localMatrix": matrix_list(local_matrix),
            "worldMatrix": matrix_list(world_matrix),
            "localBounds": ({"x": local_bounds[0], "y": local_bounds[1], "width": local_bounds[2], "height": local_bounds[3]} if local_bounds else None),
            "worldBounds": world_bounds,
        }
        if tag == "path" and "d" in attrs:
            record["pathDataLength"] = len(attrs["d"])
            record["pathDataPrefix"] = attrs["d"][:120]
            record["geometry"].pop("d", None)
        if tag in {"polygon", "polyline"}:
            record["pointsCount"] = len(numbers(attrs.get("points"))) // 2
        if parent:
            parent["childUids"].append(uid)
        elements.append(record)
        node_by_uid[uid] = record
        if element_id:
            id_to_nodes[element_id].append(record)
            ids.append({"id": element_id, "tag": tag, "label": label, "uid": uid, "parentId": record["parentId"]})
        if tag == "g" and (element_id or label):
            groups.append({"id": element_id, "label": label, "uid": uid, "parentId": record["parentId"]})
        if tag in {"text", "tspan"}:
            value = "".join(node.itertext()).strip()
            if value:
                texts.append({"id": element_id, "uid": uid, "parentId": record["parentId"], "text": value})
        if tag == "image":
            image_href = node.attrib.get("href") or node.attrib.get(XLINK_HREF) or ""
            embedded = image_href.startswith("data:")
            mime_match = re.match(r"data:([^;,]+)(?:;base64)?,", image_href) if embedded else None
            images.append({
                "id": element_id, "uid": uid,
                "parentId": record["parentId"], "treePath": path_key,
                "hrefType": "embedded-data" if embedded else ("external" if image_href else "missing"),
                "mimeType": mime_match.group(1) if mime_match else None,
                "payloadCharacters": max(0, len(image_href) - image_href.find(",") - 1) if embedded and "," in image_href else 0,
                "x": attrs.get("x"), "y": attrs.get("y"),
                "width": attrs.get("width"), "height": attrs.get("height"),
                "preserveAspectRatio": attrs.get("preserveAspectRatio"),
                "worldMatrix": matrix_list(world_matrix), "worldBounds": world_bounds,
            })
        for attr in ("clip-path", "mask", "filter"):
            value = attrs.get(attr)
            if value:
                effects.append({"id": element_id, "uid": uid, "tag": tag, "kind": attr, "value": value})
        for raw_attr, value in node.attrib.items():
            attr = local_name(raw_attr)
            targets: list[str] = []
            if attr == "href" and value.startswith("#"):
                targets.append(value[1:])
            targets.extend(URL_REF.findall(value))
            for target in dict.fromkeys(targets):
                references.append({
                    "fromUid": uid, "fromId": element_id, "fromTag": tag,
                    "attribute": attr, "targetId": target,
                    "relation": "use" if tag == "use" and attr == "href" else "definition-reference",
                })
        for child_index, child in enumerate(list(node), start=1):
            walk(child, record, depth + 1, f"{path_key}/{local_name(child.tag)}[{child_index}]", world_matrix)
        return record

    walk(root, None, 0, f"/{local_name(root.tag)}[1]", IDENTITY)

    # Resolve references in both directions without guessing labels.
    for ref in references:
        targets = id_to_nodes.get(ref["targetId"], [])
        ref["targetUid"] = targets[0]["uid"] if len(targets) == 1 else None
        ref["targetTag"] = targets[0]["tag"] if len(targets) == 1 else None
        ref["resolution"] = "resolved" if len(targets) == 1 else ("duplicate-id" if len(targets) > 1 else "unresolved")
        ref["targetMatches"] = [item["uid"] for item in targets]
    refs_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ref in references:
        refs_by_target[ref["targetId"]].append(ref)
    for image in images:
        image["referencedBy"] = [
            {"sourceUid": ref["fromUid"], "sourceId": ref["fromId"], "sourceTag": ref["fromTag"],
             "relation": ref["relation"], "attribute": ref["attribute"]}
            for ref in refs_by_target.get(image["id"], [])
        ] if image["id"] else []

    use_instances = []
    for ref in references:
        if ref["relation"] != "use":
            continue
        source = node_by_uid[ref["fromUid"]]
        target_nodes = id_to_nodes.get(ref["targetId"], [])
        x = number(source["geometry"].get("x")) or 0.0
        y = number(source["geometry"].get("y")) or 0.0
        xy_matrix = (1.0, 0.0, 0.0, 1.0, x, y)
        instance_matrix = multiply(tuple(source["worldMatrix"]), xy_matrix)
        use_instances.append({
            "useUid": source["uid"], "useId": source["id"],
            "targetId": ref["targetId"], "targetUid": ref["targetUid"],
            "targetTag": ref["targetTag"], "resolution": ref["resolution"],
            "x": source["geometry"].get("x"), "y": source["geometry"].get("y"),
            "useWorldMatrix": source["worldMatrix"],
            "instanceMatrixBeforeTargetTransform": matrix_list(instance_matrix),
            "targetMatches": [item["uid"] for item in target_nodes],
        })

    # A group's aggregate bounds are deliberately marked partial: paths, text,
    # stroke expansion and several SVG geometry types are not analytically measured.
    group_summaries = []
    for item in elements:
        if item["tag"] not in {"g", "svg", "symbol", "a"}:
            continue
        descendants = []
        prefix = item["treePath"] + "/"
        for candidate in elements:
            if candidate["treePath"].startswith(prefix) and candidate["worldBounds"] is not None:
                descendants.append(candidate["worldBounds"])
        aggregate = None
        if descendants:
            min_x = min(b["x"] for b in descendants)
            min_y = min(b["y"] for b in descendants)
            max_x = max(b["x"] + b["width"] for b in descendants)
            max_y = max(b["y"] + b["height"] for b in descendants)
            aggregate = {"x": round(min_x, 6), "y": round(min_y, 6),
                         "width": round(max_x - min_x, 6), "height": round(max_y - min_y, 6)}
        group_summaries.append({
            "uid": item["uid"], "id": item["id"], "tag": item["tag"],
            "parentId": item["parentId"], "childCount": len(item["childUids"]),
            "descendantCount": sum(1 for candidate in elements if candidate["treePath"].startswith(prefix)),
            "aggregateBoundsFromSupportedPrimitives": aggregate,
            "boundsStatus": "partial-estimate" if aggregate else "not-computable-from-supported-primitives",
        })

    duplicate_ids = {key: [item["uid"] for item in value] for key, value in id_to_nodes.items() if len(value) > 1}
    unresolved = [ref for ref in references if ref["resolution"] != "resolved"]
    root_attrs = {local_name(k): v for k, v in root.attrib.items()}
    root_record = {
        "tag": local_name(root.tag), "viewBox": root_attrs.get("viewBox"),
        "width": root_attrs.get("width"), "height": root_attrs.get("height"),
        "preserveAspectRatio": root_attrs.get("preserveAspectRatio"),
        "transform": root_attrs.get("transform"),
        "namespace": root.tag.split("}")[0][1:] if "}" in root.tag else None,
    }
    return {
        "reportVersion": 2,
        "sourceFile": path.name,
        "sourceBytes": path.stat().st_size,
        "root": root_record,
        "elementCounts": dict(sorted(counts.items())),
        "elementCount": len(elements),
        "idCount": len(ids),
        "ids": ids,
        "namedGroups": groups,
        "textNodes": texts,
        "images": images,
        "effects": effects,
        "internalReferences": references,
        "elementTree": elements,
        "groupSummaries": group_summaries,
        "useInstances": use_instances,
        "duplicateIds": duplicate_ids,
        "unresolvedReferences": unresolved,
        "transformDiagnostics": transform_diagnostics,
        "geometryLimitations": [
            "worldBounds are computed for rect, image, foreignObject, svg, circle, ellipse and line primitives only.",
            "Path and text geometry is inventoried but not analytically bounded; no path data is rewritten.",
            "Group aggregate bounds are partial estimates based only on supported descendant primitives.",
            "Stroke expansion, markers, filters, masks, clip geometry, CSS stylesheets and symbol/use rendering are not flattened into a final visual bound.",
            "Transform matrices describe element ancestry; use-instance matrices are reported before the referenced target's own transform.",
        ],
        "notes": [
            "This is a structural inventory, not a visual or pixel-parity validation.",
            "Use elementTree.parentUid/childUids and treePath to trace SVG hierarchy.",
            "Use internalReferences and useInstances to follow image, gradient, mask, and clipping relationships.",
            "The source SVG is read-only; this report does not modify it.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path, help="Path to the original SVG export")
    parser.add_argument("--out", type=Path, default=Path("generated/svg-inspection.json"))
    args = parser.parse_args()
    report = inspect(args.svg)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Inspected {report['sourceBytes']} bytes; found {report['elementCount']} elements, "
        f"{report['idCount']} IDs, {len(report['internalReferences'])} references, "
        f"and {len(report['images'])} image elements."
    )
    print(f"Report: {args.out}")


if __name__ == "__main__":
    main()
