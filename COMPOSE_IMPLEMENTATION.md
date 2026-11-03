# Compose implementation

## Added implementation

- `compose/PixScreens.kt` contains two reusable Jetpack Compose screens: `PixTemplateBrowsingScreen` and `PixProfileScreen`.
- Both screens use the original 1080px CSS coordinate system and the measured 3px-to-1dp scale. They preserve the source frame aspect ratio and scale to fit the available area.
- Backgrounds, surfaces, card dimensions, spacing, gradients, borders, text sizes, and the positions of the visible components are taken from `pix.css`.
- All source text that is not explicitly readable in CSS is supplied by the caller through screen text data classes. No labels are invented.
- Artwork is injected through `PixArtwork`. This is deliberate: the source SVG is about 3.6 MB and the GitHub file connector did not return its contents, so it was not possible to truthfully map every path, crop, or embedded photo in this run. Missing Painter assets stay empty rather than being replaced with approximations.

## Hooking up the source artwork

Export each named artwork group from `pix.svg` without changing its crop, then provide the corresponding Painter in `PixArtwork`:

| CSS / SVG layer | PixArtwork property |
| --- | --- |
| Search icon group | `search` |
| Gift artwork | `gift` |
| Credit lightning | `creditLightning` |
| Settings icon | `settings` |
| Bottom navigation icons | `discover`, `templates`, `inbox`, `profile` plus optional `discoverActive`, `templatesActive`, `inboxActive`, `profileActive` variants |
| Template usage sparkle | `usageSparkle` |
| Promotion gem | `promotionGem` |
| Invite gift artwork | `inviteGift` |
| Four template photographs | `templatePhotos` in CSS card order |
| Two profile thumbnails | `profilePhotos` in CSS order |
| Profile content-tab icons | `privateFolder`, `privateLock`, `collectionGrid` |

The full name-to-slot mapping is also recorded in `svg-css-layer-map.json`.

## Use

Place the Kotlin file in the app's source set and update its package declaration to match the app. Supply text and Painter assets from the app:

```kotlin
PixTemplateBrowsingScreen(
    text = PixTemplateScreenText(
        subscribe = /* exact source label */,
        useTemplate = /* exact source label */,
        hotBadge = /* exact source label */
    ),
    credits = /* current credits text */,
    templates = /* the four source template entries */,
    artwork = /* Painter mapping from the exported SVG groups */
)
```

```kotlin
PixProfileScreen(
    text = PixProfileScreenText(
        subscribe = /* exact source label */,
        avatarInitial = /* profile initial */,
        editProfile = /* exact source label */,
        displayName = /* profile value */,
        handle = /* profile value */,
        followingCount = /* profile value */,
        followingLabel = /* exact source label */,
        followersCount = /* profile value */,
        followersLabel = /* exact source label */,
        subscriptionTitle = /* exact source label */,
        subscriptionSubtitle = /* exact source label */,
        inviteTitle = /* exact source label */,
        inviteSubtitle = /* exact source label */,
        videoFilter = /* exact source label */,
        imageFilter = /* exact source label */,
        agentFilter = /* exact source label */
    ),
    credits = /* current credits text */,
    artwork = /* Painter mapping from the exported SVG groups */
)
```

## Limits

This is a first Compose implementation based on the inspectable CSS measurements, not a certified pixel-perfect reproduction. Exact SVG art and text outlines still need to be exported and supplied as Painter assets. Compare screenshots at the source frame ratio (360 x 705dp and 360 x 702dp) after binding those assets. No source file (`pix.svg`, `pix.css`, or `pix.kt`) is changed by this implementation.


## Original SVG source export (first pass)

Use `tools/export_svg_artwork.py` to extract embedded raster payloads and render full-frame comparison images from the original SVG. See `SVG_ARTWORK_EXPORT.md`.

Important:
- The full-frame PNGs are visual references; they are not individual `PixArtwork` painters.
- Extracted embedded images preserve their source IDs and `<use>` references. Some are reused as large source images through SVG clipping and transforms, so they must not be assigned directly to individual photo slots.
- Individual component painters remain unbound until their exact SVG subtree, referenced definitions, crop, and transform chain have been verified.

This first-pass export intentionally leaves `PixScreens.kt` unchanged. It does not claim pixel parity or alter the existing screen layout.
