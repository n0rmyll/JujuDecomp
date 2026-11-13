# Resource dispatcher and first payload-directory decoder

Update: `WORLD_VOLUMES.md` traces the 0x0601 consumers and documents a
record exporter validated against Hub and Burial archives.

## Type routing

`analysis/resource-types.json` maps **42 observed chunk types** across the
two inspected archives to entries in the dispatcher at **0x801B777C**.
`tools/map_resource_types.py` follows only that routine's `cmpwi r4` and
conditional/unconditional branch decision tree, stopping at the first
handler instruction. It reports the initial straight-line calls, not all
possible calls inside a handler. No semantic type names are guessed.

The input disassembly was generated and original-byte checked with
`python3 tools/function_report.py fn_801B777C`. Regenerate it before mapping
if the original revision or split changes. This is targeted static analysis,
not an emulator or proof that every type executes in a given scene.

## Selected generic arrays

| Type | Handler entry | First handler routine | Observed payloads |
| --- | --- | --- | --- |
| 0x0065 | 0x801B7B70 | 0x801C5BAC | Particle resource directories |
| 0x006A | 0x801B7BA0 | 0x801C5C34 | One particle resource directory |
| 0x0601 | 0x801B7B10 | 0x801C59A4 | One world resource directory |

Path markers identify the surrounding source resource, not the precise
meaning of the records. Particle/model/scene fields inside these records
remain undecoded.

Common helper **0x801B91FC** reads a u16 count at payload +0 and u16 flags
at +2. If bit 0 is set, it sets bit 2 and adds the payload base to each
u32 entry starting at +4. This is an in-place relative-pointer relocation.
`src/recovered/resource_array.c` now models this helper as well as the
accessor. The original does not test bit 2 before relocating: repeated calls
add the base again. It also has no null-pointer guard and reloads the count
on each loop test. Address arithmetic wraps at 32 bits.

Verification checks all 18 original instructions against the local DOL,
then checks the host C relocation and accessor against 479 real record
starts in Preload and Hub. Another 64 cases cover flag combinations,
empty arrays, overflowing additions, and repeated relocation. These are
semantic checks; no original-target compilation or binary match is claimed.

Accessor **0x801B92FC**:

- Null payload pointer returns zero.
- Mask the supplied index to 24 bits.
- If flags & 3 equals 1: load a relocated pointer from +4 + index*4.
- If flags & 3 equals 2: read the stride at +4 and return base + header
  size + index*stride. Header size is 16 when flags & 8 is set, otherwise 8.
- Other modes return zero. No count bounds check is present in this routine.

`src/recovered/resource_array.c` reconstructs this accessor in C using
callbacks for the target address space. It is a semantic reconstruction,
not compiler-matched source.

## Actual byte-order and directory results

Selected payload headers and entries are **big-endian**, despite the
little-endian outer DBU headers. The offline decoder reads them explicitly
as big-endian and leaves the original bytes unmodified.

| Archive/type/path hint | Record count | Layout |
| --- | --- | --- |
| Preload / 0x0065 / particles\\jujuparticles.dbl | 290 | Relative offsets |
| Preload / 0x006A / particles\\jujuparticles.dbl | 8 | Relative offsets |
| Preload / 0x0065 / particles\\jujuwaterparticles.dbl | 36 | Relative offsets |
| Hub / 0x0065 / particles\\hubparticles.dbl | 137 | Relative offsets |
| Hub / 0x0601 / worlds\\hub\\hub.dbl | 8 | Fixed stride 192 bytes |

This recovers **479 record starts**, not 479 fully decoded assets. Relative
offsets are checked to follow the directory and remain inside the payload.
The last relative record's true size and any padding remain unknown. The
fixed-stride sample has 24 trailing payload bytes; those are recorded
without assuming their meaning.

## Run and verify

```sh
python3 tools/map_resource_types.py
python3 tools/decode_resource_arrays.py
python3 tools/check_resource_arrays.py
```

`analysis/resource-arrays.json` records all offsets and provenance. The
native Mac check compiles the recovered accessor, supplies target-memory
reads, applies the original relative-pointer relocation to a copy, and
compares every returned address with the offline decoder. It also checks
the original 24-bit index mask and rejects truncated/invalid directories.
This verifies array access; it does not execute each resource handler or
validate its nested object fields.

Next: recover a complete record layout for the 0x0601 fixed-stride array,
or a particle record, including any nested pointer fixups before exporting
portable assets. The directory decoder provides concrete bounds for that
work. Full scene rendering and a source-based game rebuild remain unfinished.
