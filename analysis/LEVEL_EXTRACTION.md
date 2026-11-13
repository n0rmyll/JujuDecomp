# Hub static scene assembly

`tools/decode_level.py` assembles the authored world records from the local
GJUE78 Hub archive into one self-contained, instanced GLB. It preserves
serialized matrices and mesh references rather than positioning meshes by
name or visual guesswork. Generated game data stays under ignored
`assets/levels/Hub/`.

## Original-code evidence

The new reports for `0x801BA628` and `0x801BA264` verify all 72 and 154
instructions, respectively, against the expected `analysis/main.dol` bytes.

- Resource type `0x0060` dispatches to `0x801BA628`. It fixes up the generic
  array, looks up type `0x0022` (falling back to `0x0023` / `0x0028`), and
  passes every record to `0x801BA264` with the model-array handle.
- `0x801BA264` reads the model index at record `+0x78` and resolves it with
  `0x801B92FC`. Flag bit `0x0004` selects alternate type `0x0062` references;
  the scene decoder rejects that unimplemented branch.
- The same routine passes record `+0x10` to matrix decomposition routine
  `0x8025E824` in its flag-`0x8000` path. The block is a 16-float matrix,
  with translation at `+0x40..+0x48`. Hub has no flag-`0x8000` records, so
  no corresponding runtime matrix rewrite is needed here.
- Record `+0x94` is a record-relative pointer to auxiliary data. Its `+0x14`
  field is either `0xFFFFFFFF` or another instance index. Every Hub record
  has the sentinel. Other archives with parented records are rejected until
  their transform semantics are established.
- `0x801B92FC` masks resource indices to their lower 24 bits. The decoder
  retains the full reference and resolves the same lower-bit index.

Hub chunk 179 contains the fixed-stride array: 1,888 records, stride 176,
16-byte header. All model indices resolve into chunk 178 in the same
`worlds\hub\hub.dbl` resource group. That model array contains 1,017
subtype-19 models, all already exported by the static mesh pass. The full
archive SHA-256 must agree with the source model manifest before assembly.

The matrix interpretation is additionally checked against the world-space
min/max bounds at record `+0x60..+0x74`. Every non-proxy mesh, transformed
with the exported matrix, fits the stored bounds within 0.000046 game units.
This independently supports both matrix storage order and placement scale.

## Outputs

- **1,888 placed nodes**, preserving every source record and its flags.
- **1,017 shared meshes**; repeated placements reference the same mesh.
- **320,475 placed triangles** across all records.
- **145 unique embedded PNGs**, deduplicated by MIME type and content hash;
  materials and texture references are remapped when meshes are combined.
- `Hub.glb`, about 7.9 MB, plus a placement `manifest.json` retaining archive
  byte offsets, source model paths, exact matrices, flags, parent sentinels,
  source/export bounds, and validation residuals.
- `index.html`, an offline WebGL 2 viewer with orbit, pan, zoom, top view,
  mesh-name filtering, textures, and inspection filters.
- `preview.png` and `top.png`, independently rasterized cutaway views.

The default cutaway hides canopy/outer trees, sky, distant backdrop, named
collision/death helpers, and untextured eight-vertex/twelve-triangle boxes.
These are **inspection heuristics based on names and geometry**, not recovered
game visibility rules. Every placement remains in the GLB. Viewer checkboxes
can restore those groups. The sky alone spans roughly 6,000 units and
otherwise obscures the map overview.

Some world models are box placeholders named for actors or effects, rather
than the full corresponding character geometry. Of the 1,888 placements,
113 exceed their stored world bounds by more than 0.01 units; all 113 use
untextured eight-vertex/twelve-triangle boxes. Examples include `monkey`,
`rhino`, `chicken`, `vine1`, and `None`. The maximum box overflow is 1.49461.
These boxes are retained and reported, not silently substituted with an
unverified character rig or used as proof of a transform error.

## Reproduction and validation

Run the texture and static model exports first, then:

```sh
python3 tools/decode_level.py
python3 tools/check_level_export.py
python3 tools/render_level_preview.py
python3 tools/render_level_preview.py --top --output assets/levels/Hub/top.png
python3 -m unittest discover -s tests -p 'test_decode_*.py'
```

The level checker validates GLB framing and buffer/accessor ranges, finite
attributes, triangle indices, materials, image deduplication, and scene
membership. It checks every node's matrix **exactly against original DBU
float bytes**, every resolved model reference, all source vertex attributes
and indices, original embedded texture bytes, and transformed bounds.

Five new tests cover tagged model references, nonuniform/negative scale,
bad/unsupported instance records, actual texture deduplication during merge,
shared mesh references, a known rotated/scaled/translated triangle, and all
1,888 actual Hub placements. The full `test_decode_*.py` selection passes
39 tests. Viewer JavaScript passes `node --check`.

The in-app browser rejected the local `file:` URL, so interactive WebGL
execution was not verified in this session. The two CPU renders were
visually inspected instead; they load the exported GLB, traverse placed
nodes, transform vertices, and sample embedded textures independently of
the WebGL viewer.

## Scope

This is a recognizable **authored static scene**, not a playable level or
a frame-matched gameplay reconstruction. Gameplay actor creation, visibility
and LOD selection, skeletal animation, collision behavior, particles,
lighting/vertex colors, and layered materials remain unresolved. Some
surfaces therefore appear neutral or differ from game rendering. The
exporter is deliberately restricted to the verified instance format and
does not claim that all other levels have been assembled.
