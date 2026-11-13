# DBU binary chunk boundaries recovered

Update: `RESOURCE_ARRAYS.md` documents the type dispatch map and a verified
payload-array directory decoder, including mixed outer/payload byte order.

The offline reader now scans both extracted archives to exact EOF, using
layout recovered from the game's own loader. This is the first verified
binary asset-directory step; it does not reconstruct original DBL files or
decode textures, models, animation, or compression.

## Original loader evidence

**0x801B8C80** copies a 32-byte archive header, obtains a leading decimal
offset through **0x80296AE0** (numeric conversion inferred), and rereads the
header at that offset when nonzero. It accepts the version word **0x100**
at header +0x10. If native-order interpretation fails, it byte-swaps four
words at header +0x10/+0x14/+0x18/+0x1C, then checks 0x100 again. This
establishes endian detection; the two provided samples use little-endian
storage despite the big-endian GameCube CPU.

The resource count at header +0x18 supplies the dispatch-loop counter in
**0x801B777C**. Its automatic split contains a large type switch; type
meanings are still mostly unknown.

**0x801B8E60** reads/swaps a chunk's first fields and selects the number of
header bytes according to flag bits 0x02 and 0x08:

| Flags & 0x08 | Flags & 0x02 | Header bytes |
| --- | --- | --- |
| clear | clear | 10 |
| clear | set | 42 |
| set | clear | 32 |
| set | set | 64 |

These are total header lengths, not alignment requests to round the file
offset independently. `src/recovered/dbu_chunk.c` reconstructs this branch
logic directly. The reader exports the fields at +0, +2, +4, and +8 as
type (u16), flags (u16), payload length (u32), and an unnamed u16.

**0x801B8FD0** uses context +0x50 (chunk +4) as the payload byte count to
consume after the handler returns. Depending on a flag, it calls
**0x801B9014** or **0x801B90D0**. The latter advances the input pointer
and decreases remaining bytes by that count. The former also supports
buffer compaction; the offline reader does not emulate in-place relocation.

## Actual sample results

| File | Binary header | Chunks | End position | Trailing bytes |
| --- | --- | --- | --- | --- |
| Preload.dbu | 0xC60 | 147 | 0x4143E0 | 0 |
| Hub.dbu | 0x1E80 | 276 | 0xB10EA0 | 0 |

Both version words decode to 0x100. The parser requires the observed `DB`
signature at binary header +8, validates boundaries/counts, and rejects
trailing bytes. This intentionally supports the observed layout; alternate
signatures or padded formats need further evidence before relaxing checks.

Chunks of type **0x0998** frequently contain a 256-byte payload beginning
with a resource path. The first Preload example is
`fluff\\inventoryicons.dbl`. Subsequent chunks are annotated with the most
recent readable marker as a navigation hint. This does not prove that a
marker and its following chunks reconstruct an unchanged source file.

## Tools and validation

```sh
python3 tools/inspect_dbu.py analysis/Preload.dbu --output analysis/preload-chunks.json
python3 tools/inspect_dbu.py analysis/Hub.dbu --output analysis/hub-chunks.json
python3 tools/check_dbu.py
```

The JSON reports record byte offsets, header sizes, type/flags, lengths,
path hints, and input SHA-256. No archive paths are used as output paths.

Validation includes:

- Exact-EOF scans over **423 real chunks** across two independent archives.
- Native Mac compilation of recovered header-size C, checked against every
  real chunk plus all four sizing branches.
- Two structurally equivalent big-endian header fixtures. Payloads are
  unchanged, so this tests header interpretation, not big-endian assets.
- Eight malformed cases covering truncation, impossible payload length,
  and trailing data.
- Original-byte verification of the loader assembly through function reports.

These checks validate boundary decoding and the recovered sizing function.
They do not constitute a matching CodeWarrior build or game execution using
reconstructed code.

## Next target

Map concrete resource type IDs to handlers in **0x801B777C**, then select a
simple payload type for a full decoder. Inspect relocation/endian handling
before treating payload bytes as host structs. This binary directory now
provides verified byte ranges for that work.
