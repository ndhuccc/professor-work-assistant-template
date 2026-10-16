# JianBauDau schema v3

Observed native root: `schemaVersion: 3`, `rootSceneId`, `scenes` object, `nodes` object, `steps` array, `metadata`.

Each scene has `id`, `name`, `parentFrameId`, `nodeIds`, `camera`. Nodes belong to one `sceneId`. A root `frame` node may link to a child via `frame.childSceneId`; those coordinates are separate.

A node contains `id`, `type`, `name`, `sceneId`, `transform` (x,y,scaleX,scaleY,rotation), `width`, `height`, `zIndex`, `locked`, `style`, `text`. An image additionally has `image: {src: data URI, alt: string, fit: contain}`. Preserve unknown fields. Avoid printing image.src. Rotations are treated conservatively by the insertion utility using a bounding circle, independent of angle units.

A playback step contains `id`, `order`, `label`, `target`, `durationMs`, `holdMs`, `easing`, optional `speakerNotes` and `fallbackCamera`. Supported target: `{kind: scene-point, sceneId, point: {x,y}, zoom, referenceViewport: {width,height}}`. Camera rectangle is centered at point with world width = viewport width / zoom and corresponding height. A rotated camera conservatively reserves its diagonal square. Unknown target kinds must be resolved by a format-aware adapter, not ignored.

“Next page” means array playback order with contiguous order values; it does not mean moving the original canvas objects. Preserve user-added intermediate zoom steps.

The utility places comic cameras below the maximum occupied y boundary in their own scene, with a minimum 160-world-unit gap. It reserves the full camera rectangle with a further perimeter buffer. Collision checking includes original shape/image/text bounds, frame bounds, original camera views and every inserted comic view. Connectors require endpoint IDs; use endpoint bounds as a conservative reservation. Unsupported grouping fails for explicit adapter handling.

## Compressed image embedding

Default: JPEG quality 90, 4:4:4 subsampling, maximum width 1920 pixels; preserve aspect ratio and never upscale. Flatten transparency onto white for JPEG only. Per-item `image_format: png` retains lossless encoding, subject to resizing; `image_format: original` embeds unchanged bytes without resizing and requires normalized EXIF orientation. MIME follows actual encoded bytes, not filename. Preserve original image files and deck nodes. Inspect compressed characters, formulas and thin lines before delivery; the utility cannot decide visual legibility.
