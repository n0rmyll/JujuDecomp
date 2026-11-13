# Static GameCube mesh extraction

`tools/decode_models.py` exports the supported subtype-19 model records to
self-contained GLB 2.0 files. The complete pass over 21 local DBUs produced
9,058 meshes, 1,713,896 triangles, and 8,464 meshes with an embedded PNG.
These counts retain repeated resources across levels and include individual
level mesh pieces, props, and shadow meshes. They are not counts of unique
characters or reconstructed full level scenes.

## Executable and format evidence

The original GJUE78 `main.dol` instruction bytes were checked by
`tools/function_report.py` for the relevant routines, with reports under
`analysis/reports/`:

- `0x801C4324`: single-model loader for resource types 0x20/0x21.
- `0x801C4468`: model-array loader for resource types 0x22/0x23, using the
  previously recovered generic array directory.
- The jump table at `0x802EC7E8` routes subtype 19 to `0x801C4C98`.
  That routine relocates model offsets +0x54, +0x88, +0x90, and +0x78.
  Display-list nodes have relative next pointers and material indices.
- Renderer `0x80188CEC` supplies position array +0x54 with stride 12,
  normal array +0x88 with stride 3, and UV array +0x90 with stride 8.
  At `0x80189308`, it submits node +0x20 using byte count at node +0x14
  to `0x80133AE0` (display-list submission inferred from its FIFO writes).
- `0x8018C7FC` loads material arrays; `0x8018CC3C` remaps each layer's
  signed texture index through the active texture list. The static exporter
  binds only an unambiguous single local layer from the same path-marker
  group; special/global and multi-layer cases retain a neutral material.

Position, normal, and UV counts are at model +0x50, +0x84, and +0x8C.
Positions and UVs use big-endian floats; normal triplets use signed bytes
and are normalized for glTF. Vertex keys preserve distinct normal/UV seams.
Names are read from model +0x30; file names are sanitized independently.

Display-list vertex descriptors select independent 8- or 16-bit indices.
The decoder tracks CP register writes, consumes supported matrix/XF/BP
commands, and triangulates GX triangle lists, strips, fans, and quads.
GX descriptor layouts were checked against Dolphin's
[CP register definitions](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/VideoCommon/CPMemory.h).
Unknown commands, direct attributes, invalid indices, non-finite data,
out-of-bounds ranges, and cyclic chains fail explicitly.

## Export behavior and limits

The exporter retains source mesh coordinates and UVs. It does not apply
skeletal or scene-placement transforms. Nonzero matrix indices are rejected
rather than discarded. Of 9,408 model records, 326 need those transforms,
and 24 have subtype 17, which is not yet decoded. Their offsets and reasons
are retained in the manifest. The command completes the supported export
pass while reporting these unresolved records.

The renderer's indexed color attributes come from a separate runtime
array. Their indices are consumed to maintain correct display-list parsing,
but baked vertex lighting is omitted. Multi-texture effects, blending,
shaders, wrap modes, and animation are not reproduced. Single texture layers
use a rough nonmetallic glTF material, double-sided rendering, and an alpha
mask as preview approximations. Exported PNGs are embedded directly, and
meshes without resolved texture bindings remain untextured.

`tools/model_gallery.py` generates the offline preview and searchable list.
The default coconut GLB is embedded in the page; the file picker previews
other local exports. The software canvas viewer uses painter sorting and
affine texture mapping, so complex intersections and perspective are
approximate. It is a convenience preview; GLBs can be imported into a full
3D editor. Browser JavaScript syntax was checked; browser UI verification
was unavailable in this environment.

## Validation

Five tests exercise strip/fan/quad winding, 8-/16-bit vertex indices,
known positions, malformed ranges/commands/indices, GLB binary round-trip,
and a real coconut closed-surface check: 42 vertices, 80 triangles, and
120 edges, each shared by two faces (Euler characteristic 2).

`tools/check_model_exports.py` independently reopens every exported GLB and
checks framing, buffer/accessor bounds and alignment, triangle indices,
unique output paths, and manifest vertex/triangle counts. These checks pass
for all 9,058 files. `tools/render_model_preview.py` rasterizes the exported
coconut using its embedded PNG; the resulting textured mesh was visually
inspected. This verifies one prop's appearance, not every exported model.

All generated models, manifest, gallery, and preview stay under ignored
`assets/models/`. No original disc file is modified.
