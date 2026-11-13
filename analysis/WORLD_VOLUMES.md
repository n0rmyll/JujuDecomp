# First fixed-size world record export

## Consumer traced

The lookup loop around **0x801B4DE0** requests resource type **0x0601**,
gets each record through **0x801B92FC**, then passes it to **0x80280928**.
That wrapper calls **0x80280BB4** and converts its result to boolean.

`0x80280BB4` receives the record in r4. It reads:

| Record offset | Observed operation |
| --- | --- |
| +0x04..+0x0C | Three floats, negated and copied as well as copied unchanged |
| +0x10..+0x18 | Three floats copied to a construction buffer |
| +0x1C..+0x3C | Nine floats copied to a construction buffer |
| +0x40 | Inline string passed to 0x802861E4 |
| +0x60 | Float passed to constructor 0x8027F88C |
| +0x98 | Second float passed to that constructor |

The helper **0x8027F680** additionally copies an inline string from +0x64,
bit zero of the word at +0, floats at +0x84/+0x90/+0x94, and words at
+0x88/+0x8C into a runtime object. It is called during the same construction
path. No pointer fixups occur in the generic 0x0601 loader beyond the array
helper, which leaves fixed-stride mode unchanged.

The lookup routine **0x802861E4** compares preset strings including
`PADDEDCELL`, `BATHROOM`, `LIVINGROOM`, `STONEROOM`, `AUDITORIUM`,
`CONCERTHALL`, and `STONECORRIDOR`. Together with the spatial construction
and surrounding resource setup, this supports a **spatial audio/reverb
volume interpretation**. Exact original class names and parameter units
remain unverified. These records are not level meshes.

## What is decoded

`tools/decode_world_volumes.py` exports type-0x0601 fixed-stride records:

- Flags word at +0.
- Float triples at +4 and +0x10, with offset-based names.
- Nine floats at +0x1C, labeled a matrix candidate.
- 32-byte NUL-terminated strings at +0x40 and +0x64.
- Observed scalar/word fields through +0x98.
- Uninterpreted +0x9C..+0xBF bytes.
- Full original 192-byte record as hex for lossless comparison.

The exporter uses big-endian payload fields and validates sizes, finite
values in the fields interpreted as floats, and string termination. Those
checks define the supported offline sample format, not every input the
original game might accept. The remaining bytes are preserved, not silently
assigned meanings or discarded.

## Two real archive results

| Archive | Records | Presets |
| --- | --- | --- |
| Hub.dbu | 8 | STONECORRIDOR |
| Burial.dbu | 2 | STONEROOM, CAVE |

Burial was independently extracted from the provided RVZ. Its outer scan
contains 302 chunks and reaches exact EOF at **0xA52340**. Its 0x0601
payload has the same 192-byte stride as Hub.

```sh
python3 tools/decode_world_volumes.py analysis/Hub.dbu --output analysis/hub-world-volumes.json
python3 tools/decode_world_volumes.py analysis/Burial.dbu --output analysis/burial-world-volumes.json
python3 tools/check_world_volumes.py
```

Outputs retain archive/chunk provenance and absolute archive byte offsets.
No game data is uploaded or published.

## Native code and checks

`src/recovered/world_volume.c` supplies an offline portable big-endian
reader and the scalar flag-bit operation observed in 0x8027F680. It does
not claim to reconstruct the full runtime constructor: allocation,
spatial-object creation, preset lookup, and insertion remain original-code
analysis targets.

The native Mac test compiles the C reader, checks all **48 words** of each
of **10 real records** against Python decoding, and reconstructs the exact
original record bytes. Short records and unterminated interpreted strings
are rejected. The consumers and helpers have original-byte-checked function
reports under `analysis/reports/`.

This is a validated record export and a useful portable asset-inspection
component, not a completed audio engine or a matching original build.

## Next target

Follow type **0x0082/0x0086** through **0x8018BF18** to identify the
texture/material payload representation, or trace the spatial constructor
far enough to name its remaining parameters. Rendering a real scene still
requires decoding geometry, materials, textures, and their references.
