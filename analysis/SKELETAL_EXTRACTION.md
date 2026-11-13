# Skeletons and first animation reconstruction

The second model pass exports supported subtype-19 skeletal meshes with
glTF joints, hierarchy, inverse bind matrices, and rigid vertex influences.
It also decodes the EQM motion banks and attaches matching motion clips.
All outputs remain under ignored `assets/rigs/` and `assets/animations/`.

## Bone and skin evidence

Instruction reports under `analysis/reports/` check the following routines
against the expected GJUE78 main.dol bytes:

- `0x801C4FAC` locates skeletal data after the UV array. For subtype 19,
  alignment is 32 bytes in the enclosing payload's address space. Model
  arrays start individual records at nonzero offsets, so alignment must
  include the record's enclosing-payload offset.
- `0x801C4680` attaches the skeletal data to the model.
- `0x801C4FE8` traverses child/sibling indices at +0x80/+0x84, with 0xF0
  bytes per serialized bone. Child recursion receives the current bone as
  parent; sibling recursion retains the previous parent. Names are at
  +0xB0 and non-root matrix-array IDs are the bytes at +0xC9. The root is
  an exception: `0x801C4680` reads its byte into the skeleton bone count
  at `0x801C46AC`, then overwrites it with zero at `0x801C46B4`. The
  exporter uses runtime ID 0 for the root and retains the original byte
  as `serialized_source_id`; it does not create a count-valued ID alias.
- The first two 4x4 matrices are the bind transform and stored inverse
  transform. Their products are checked before export. Some stored inverses
  differ slightly from the stored bind matrices: export computes exact
  inverses from bind transforms, retaining both stored matrices and the
  original residual in each skeleton JSON. Residuals above 0.05 are rejected,
  and those records remain in the error manifest. This is an export bind
  consistency choice, not a claim that the original matrices match exactly.
- Renderer `0x80188CEC` supplies the skeletal matrix arrays. GX indexed
  position-matrix loads map source matrix IDs to palette slots. Each vertex's
  matrix index selects a slot; the exported influence is that source bone
  with weight one. Vertex deduplication includes the selected bone to keep
  different influences separate at shared positions.

The bone tree retains helper and attachment bones as serialized. Local
bind transforms are derived from parent-global inverse times child-global
bind. Source matrices use the storage order compatible with glTF's
column-major arrays after this interpretation.

## Motion-bank and sampler evidence

Type 0x0100 resources contain little-endian `EQM\0` banks. Loader
`0x801C33C4` swaps the fields, walks clip records after a directory at +0x14,
and places per-bone records and channel headers in memory. Bone records
are 0x3C bytes: a 16-byte name, channel mask, group field, nine-float
orientation basis, and a runtime pointer slot. Animated-channel count is
the mask population count (`0x801C3ACC`). Each channel has a 16-byte header
followed by `(u16 time, s16 value)` keys; runtime pointer/cache bytes are not
treated as file offsets. All 41 unique banks scan to their bounded padding.

Sampler `0x801EBB20` clamps outside the key range and linearly interpolates
inside it. `0x801EBEB4` supplies these quantization factors, stored at
`0x80336450` / `0x80336454` / `0x80336458`:

| Mask bits | Components | Factor before game-unit scale |
| --- | --- | --- |
| 0–2 | Translation XYZ | 256 / 32767 |
| 3–5 | Scale XYZ | 128 / 32767 |
| 6–9 | Quaternion XYZW | 2 / 32767 |

The default components initialized by `0x801EC650` are zero translation,
unit scale, and identity quaternion. Quaternion normalization is called by
the original sampler (`0x8025E90C`). Zero-scale channels hide attachments;
these are retained, with rotation recovered independently of scale.
For a zero quaternion, the exported rotation is identity, matching the
identity rotation obtained from the zero-component matrix formula rather
than emitting an invalid glTF quaternion.

Both game setup routines `0x80100E54` and `0x800E72BC` call translation-scale
setter `0x801EBB18` with 0.015625 (1/64). The exporter applies that factor.
Omitting it causes large, visibly incorrect displacements. Timing conversion
at `0x801E9DF8` uses 300 ticks per second. Exports bake every ten ticks
(30 Hz), including the final tick, with continuous quaternion signs.

Matrix preparation/composition routines `0x801EC180`, `0x801EC338`,
`0x801EC504`, and `0x801EC5A0` guide the first standalone pose reconstruction.
The animation orientation basis replaces the local bind orientation, and
sampled TRS is composed in that basis, preserving local bind translation.
The export covers standalone non-mirrored clips. Matching uses original
resource stems and bone names; it does not silently retarget missing bones.

## Actual outputs

- 341 skinned mesh GLBs, retaining repeated meshes across archives.
- 13 skeletal model records rejected for inconsistent stored bind/inverse
  matrices. The corrected runtime root-ID mapping recovered all 67 former
  missing-palette-ID failures (32 distinct source path markers), including
  Plant Man, blimps, suspension bridges, foliage, and props. Record-level
  details are in [root-ID recovery](rig-root-recovery.json).
- 41 unique motion banks (deduplicated by source SHA-256), 949 parsed clips,
  zero bank-decoding errors.
- 30 animated GLBs with 808 attached clips. Eleven banks lack a matching
  exported rig and remain structured JSON motion exports.
  Newly matched banks include Plant Man (35 clips) and Tak's splash (one).
- Tak: 137 serialized bones, 186 parsed clips and 185 bound clips, including
  `DVWALK`, `DVRUN`, `DVJOG`, and jump/weapon motions. `B_BLINK` has only
  unmatched eyelid tracks and is retained in JSON without a GLB animation.

Some reduced character rigs lack tracks present in the full animation bank.
The exported bank manifest lists unmatched names. These partial bindings,
30 Hz baking, and glTF quaternion interpolation mean the exports are a first
animation reconstruction, not verified frame-for-frame gameplay playback.
Gameplay state transitions, blended animation layers, mirrored motions,
IK, and procedural effects remain separate work. Serialized helper-bone
updates are now baked as described below.

## Procedural helper bones

`0x801ED2A4` calls `0x801ED354` when serialized bone byte `+0xCE`
is nonzero. Bytes `+0xCA..0xCF` contain a mode, three unsigned percentage
weights, a source bone ID, and an optional second source bone ID. The
exporter retains these bytes as named helper fields, plus the pivot at
`+0x94`, in each skeleton JSON.

The routine reads the referenced bone's local **skin deformation** matrix
at runtime `+0x40`, extracts its quaternion, and either scales quaternion
XYZ components independently (with W=1), slerps from identity by the first
percentage, or applies an X-only quaternion component. A second weighted
reference, when enabled, is blended with the first using a 0.5 slerp.
The percentage and blend constants are 0.01 and 0.5 in the original DOL.
`0x801ED354` and `0x801ED680` compose the result about the serialized
object-space pivot: `T(pivot) * R * T(-pivot)`.

For glTF, the exporter converts this replacement local skin deformation
back into joint-local TRS with `parentInverseBind * deformation * bind`.
Using the helper quaternion directly as a joint-local rotation would
rotate about the wrong origin. Dependencies are evaluated recursively;
missing targets and cycles are reported as errors. Tak has 21 such helpers,
covering hands, arms, spine, and legs. Their TRS channels are baked along
with ordinary tracks, including helpers with no named animation track.

The ordinary transform composition is consistent with the original matrix
preparation: `0x801EC180` yields the rotation `inverseBind * parentBind`,
and `0x801EC338` cancels the first factor when preparing the track basis.
Together with `0x801EC504`, this preserves local bind translation and
composes the sampled TRS in the track basis, as the exporter already did.

Two independently rasterized walk frames were inspected after adding
helpers. The neck separation remains visible; this change does **not**
establish that the neck/shoulder deformation issue is resolved. There is
still no comparison against original gameplay, and ordinary transform
composition was not changed speculatively to hide the gap.

## Validation and preview

The rig tests cover hierarchy/inversion, corrupt skeleton pointers,
GLB joint attributes and inverse binds, a small independently constructed
EQM fixture, channel quantization/interpolation, TRS round-trip, hidden
zero-scale channels, and all 137 real Tak bind/inverse products. A separate
model regression test preserves UVs when textured and untextured primitives
share the same vertex buffer.
Helper tests additionally cover serialized percentages, rotation about an
object-space pivot under a translated parent, independent XYZ weighting,
two-reference blending, X-only mode, shortest-arc interpolation, and invalid
dependencies. The texture/model/rig test selection contains 22 passing tests,
including root-count-to-ID conversion, actual exported root influences,
rejection of the count as a palette ID, and Tak's runtime ID range 0–136.

`tools/check_rig_exports.py` reopens 371 skinned GLBs and checks hierarchy,
bind reconstruction, joint bounds, normalized weights, accessor bounds,
finite values, animation timelines, and unit quaternion outputs. The offline
viewer supports clip selection, play/pause, scrubbing, and skin deformation.
`tools/render_rig_preview.py` independently samples the exported GLB and
rasterizes two Tak walk poses using the embedded texture images.

Browser UI execution was unavailable; viewer JavaScript syntax is checked.
No comparison against original-hardware playback is claimed. The rigs,
raw keys, source offsets, and failure manifests are retained for continued
verification and refinement.

The Dolphin comparison attempt reached the main menu but was stopped at
the user's request before gameplay capture. The current animation exports
are provisionally accepted for continued extraction, not frame-matched
against Dolphin. This does not change the recorded neck-gap limitation.
