# Hub actor and prop placement previews

`python3 tools/decode_level.py --actors` replaces 20 authored box placements
with eight extracted replacement resources. The placement matrices are
unchanged. Rigged resources are shown in validated bind poses; static
resources retain their exported geometry. This pass reconstructs model
associations and static appearance, not runtime actor behavior.

## Source evidence

The function reports created for this pass verify their instruction bytes
against the expected GJUE78 DOL SHA-256
`49faf28a7d2e25422c145754ef41b0c8a8dfcd83e688db1c39ecf21f6e34b706`.

- `0x80242728` requests resource `0x0402` from `Worlds\%s\%s.env` and
  advances its reader past a 16-byte prefix. Hub's environment payload is
  archive chunk 273.
- `0x8007D810` reads actor class strings and dispatches through actor
  initialization functions. The actor class registry contains 249 entries.
  `0x8007E380` also constructs an actor from this stream.
- String readers `0x8024269C` and `0x802425CC` advance by
  `(strlen(string) + 4) & ~3`, or four bytes for an empty field. Values are
  ASCII strings with NUL terminators and padding; padding can contain `0xEE`.
- The common actor initializer `0x80252EEC` reads the instance name, looks
  it up with `0x801FD4FC`, and then reads the `model_name` override. The
  report includes string annotations using the original r30 base
  `0x802F0B70`.
- `0x801FD4FC` requests the world `0x0060` instance array and calls
  `0x801FD5C4`. That lookup compares the requested instance name with the
  inline string at `instance[+0x94] + 0x20`. These are the actual links
  between environment definitions and placed world records.
- With an explicit override, `0x801FCFF4` constructs the replacement
  resource path using `Replace\` (`0x802EE1E8`) and `.dbl`. The export
  resolver requires that full normalized resource marker; it does not pick
  a character merely because a box or asset has a similar name.
- `0x801B99FC` retrieves a placed instance's geometry handle, and
  `0x8022872C` forwards geometry through the actor model setup path. The
  common initializer also decomposes the linked instance matrix for the
  actor's transform.

This implementation is deliberately a **bounded prefix extractor**. It
recognizes eight supported class tokens, requires four-byte alignment and
an exact named instance association, and reads only the class, instance
name, and model override. It does not claim to decode every field or record
boundary in the variable-length `.env` stream. Incidental suffix matches
inside longer class strings are excluded. Ambiguous instance names, absent
explicit overrides, and ambiguous/missing replacement resources are reported
and not replaced.

## Recovered placements

| Class | Placements | Resource | Source |
| --- | ---: | --- | --- |
| chicken | 2 | `replace\chicken.dbl` | Hub rig |
| monkey | 1 | `replace\monkey.dbl` | Hub rig |
| rhino | 1 | `replace\rhino.dbl` | Hub rig |
| sheep | 5 | `replace\sheep.dbl` | Preload rig |
| yorbel | 5 | `replace\yorbel.dbl` | Hub static model |
| tiki | 1 | `replace\tiki.dbl` | Hub static model |
| rope | 2 | `replace\vine1.dbl` | Hub rig |
| zipline | 3 | `replace\zipline50.dbl` | Hub rig |

Resource lookup uses Hub first and the already extracted Preload second;
models from unrelated levels are not used. Each binding retains the
environment chunk/byte offset, prefix field offsets, original instance
index/name, model override, replacement archive/chunk/index, archive hash,
asset GLB hash, source path, and pose mode in the placement manifest and
GLB node extras.

For example, Hub instance 1678 is linked by `ENV_Chkn_SIM_chkn14` to the
`chicken` environment prefix, which explicitly requests `chicken`. Its
replacement is the Hub chicken rig at chunk 67, record 0. Instance 1763
links `ENV_Mnky_SIM_Mnky2` to the monkey rig at chunk 99. Instance 1872
links `ENV_Rhino` to the rhino rig at chunk 103.

There are 20 matched prefixes and 20 replacements in this supported pass,
with no unresolved bindings among those 20. **232 other box markers remain**,
including triggers, actor placeholders with unsupported classes, and objects
whose models are chosen by constructor defaults or scripts. This is not a
claim that all 232 are missing visible actors. In particular, this pass does
not guess feather or gremlin geometry for `None` overrides.

## Scene integration and validation

The populated scene contains 1,888 original placement nodes, 1,025 embedded
meshes, 348,140 placed triangles, and 194 unique embedded images. Original
world meshes remain embedded, including the box meshes, for provenance;
the 20 selected nodes reference replacement meshes. Repeated actor resources
share geometry and deduplicated texture bytes. The viewer enables its Actors
group by default and supports filtering by class or instance name.

Before removing a rig's skin attributes for static display, the existing
rig validator checks joint bounds, weights, and bind reconstruction. At bind
pose, `globalJoint * inverseBind` is identity, so positions and normals can
be preserved exactly. Skinned mesh-node transforms and animated GLBs are
rejected by this conversion path. The source rig GLBs remain unchanged.

`tools/check_level_export.py` additionally checks every actor prefix against
the original environment bytes, resolves its name against the original
instance auxiliary data, checks the exact full replacement path and asset
provenance/hash, and compares all exported positions, normals, UVs, indices,
and texture bytes with the source asset. Original placement matrices still
match the archive exactly. Unchanged non-proxy world geometry remains within
its authored bounds to 0.000046 units.

Actor bind poses can extend outside the gameplay bounds stored on their box
markers. The monkey's spread limbs and the extended zipline are examples;
the maximum overflow after replacement is 11.86596 units. These residuals
remain reported rather than using the box bounds to resize or crop models.
Gameplay pose/attachment selection is not reconstructed.

Five new tests cover padded/aligned strings, exact instance anchors, suffix
false positives, malformed strings, scoped resource fallback, ambiguous
bindings, unsupported overrides, bind-skin validation/removal, and all 20
actual Hub bindings. The full `test_decode_*.py` selection passes 44 tests.
Level validation and viewer JavaScript syntax checks pass. Interactive
browser rendering remains unverified because local-file preview was blocked
in the preceding level pass; no browser-policy workaround was attempted.

The CPU renderer includes actors and can isolate placements:

```sh
python3 tools/decode_level.py --actors
python3 tools/check_level_export.py
python3 tools/render_level_preview.py
python3 tools/render_level_preview.py --instance 1678 --output assets/levels/Hub/chicken.png
python3 tools/render_level_preview.py --instance 1763 --output assets/levels/Hub/monkey.png
python3 tools/render_level_preview.py --instance 1872 --output assets/levels/Hub/rhino.png
```

The chicken, monkey, and rhino close-ups in `actors-preview.png` were
independently rasterized from the assembled GLB and visually inspected.
