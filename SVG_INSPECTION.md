# SVG source inspection

The Compose screens intentionally accept original artwork as Painter inputs. Inspect the actual SVG structure before binding those inputs; never infer SVG IDs from CSS layer names.

## Run locally

From the repository root, run:

    python tools/inspect_svg.py pix.svg --out generated/svg-inspection.json

The inspector has no third-party Python dependencies. It reads pix.svg and writes only the requested JSON report. The source SVG is never modified.

## What the version 2 report adds

In addition to IDs, text, embedded images and effects, the report now includes:

- elementTree: every SVG node in document order, with a stable report-local uid, treePath, depth, parentUid, parentId and childUids.
- localMatrix and worldMatrix: each node's own transform and its accumulated ancestor transform. Supported transforms are matrix, translate, scale, rotate, skewX and skewY.
- localBounds and worldBounds: measured bounds for basic rect, image, foreignObject, nested svg, circle, ellipse and line geometry when coordinates are absolute numbers or px.
- groupSummaries: child and descendant counts plus partial aggregate bounds from supported primitives.
- internalReferences: href and url(#id) edges, resolved to actual target nodes when possible; unresolved or duplicate IDs are flagged.
- useInstances: the use source, target, x/y offset and instance matrix before the referenced target's own transform.
- images[].referencedBy: the use or other internal references that point to each image element.
- transformDiagnostics, duplicateIds and unresolvedReferences for cases that need manual review.

Path data is represented by pathDataPrefix and pathDataLength so the report can identify paths without copying or rewriting full path strings.

## Geometry accuracy boundary

This is a structural and transform-aware inventory, not a browser renderer or pixel-parity test. Bounds are intentionally partial: path and text geometry, stroke expansion, markers, filters, masks, clipping results, stylesheet-computed styles, and final use rendering are not flattened into rendered bounds. Percentage coordinates are preserved as source strings and are not treated as absolute numbers. A group aggregate is explicitly marked partial-estimate so it is not mistaken for a complete visual bounding box.

## Mapping to Compose

1. Regenerate the v2 report with the command above.
2. Follow elementTree parent/child links to identify each actual group and its descendants.
3. Follow internalReferences and useInstances to understand how images, gradients, masks and clipping definitions are reused.
4. Compare actual geometry and transforms with pix.css and svg-css-layer-map.json. A matching coordinate or a nearby element is not proof that it is the same layer.
5. Export only a confirmed original artwork region, preserving the original image crop, clip path, mask, transform and aspect ratio.
6. Bind the confirmed export to the matching PixArtwork field in compose/PixScreens.kt.

Run the lightweight regression tests with:

    python -m unittest discover -s tests -v

The tests use small synthetic SVG fixtures; they do not replace inspection of the original pix.svg.
