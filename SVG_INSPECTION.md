# SVG source inspection

The Compose screens intentionally accept original artwork as `Painter` inputs. Before binding those inputs, inspect the actual SVG structure rather than guessing group names or drawing replacements.

## Run locally

From the repository root:

```bash
python tools/inspect_svg.py pix.svg --out generated/svg-inspection.json
```

The read-only report inventories:

- SVG element IDs and named groups (including Inkscape labels and `data-name` values).
- Text and tspan contents.
- Embedded versus external image references, image dimensions, and payload lengths.
- Clip-path, mask, and filter attributes.
- Internal references to definitions such as gradients and clipping paths.
- Root viewBox, dimensions, and counts by SVG element type.

## Next implementation step

1. Open `generated/svg-inspection.json` and correlate the real IDs with the CSS layer names in `svg-css-layer-map.json`.
2. Inspect the referenced definitions and image crops in the original SVG.
3. Export each exact artwork region without changing its proportions, clipping, or crop.
4. Bind those exports to the existing `PixArtwork` fields in `compose/PixScreens.kt`.
5. Compare screenshots against the original Figma frames before claiming visual parity.

The inspector does not modify `pix.svg`, does not export replacement assets, and does not claim that similarly named CSS and SVG layers are necessarily identical.
