# Fifteen additional complete semantic routine models

`src/recovered/runtime_helpers.c` and its header recover these original
GJUE78 revision 0 function regions. Address-based names are descriptive
provenance, not original source symbols.

| Address | Bytes | Observed behavior |
| --- | ---: | --- |
| 0x801B90F4 | 156 | DBU cleanup/reset selection; optional free or size adjustment |
| 0x801B9190 | 108 | Relocate array, clear header flag bit zero, publish outputs |
| 0x801B9244 | 184 | Swap array header byte order; swap/relocate entries if bit zero is set |
| 0x801C5A64 | 32 | Clear header flag bit zero and publish payload/size without relocation |
| 0x8021311C | 36 | Call state activation and return 1 regardless of its result |
| 0x80213480 | 72 | Initialize first application member; conditionally initialize second |
| 0x80213710 | 52 | Call input-member initialization and normalize its low return byte |
| 0x80213744 | 56 | Call member +0x4D8 with argument zero; normalize low return byte |
| 0x800E53C4 | 8 | Read global byte at 0x803312FC |
| 0x800E53CC | 8 | Write low byte of argument to 0x803312FC |
| 0x80211ED4 | 128 | Copy 48 input-state bytes, clear pending field, call four device slots +0x28 |
| 0x80211F54 | 132 | Conditional member/pending calls, then four device slots +0x2C |
| 0x8020F964 | 100 | Base application constructor with allocation and conditional construction |
| 0x80213708 | 8 | Return constant 1 |
| 0x80280928 | 44 | Forward object/record to 0x80280BB4 and normalize its full return word |

Total: **15 regions, 1,124 original bytes, 281 instructions**. Small
accessors and the constant-return stub count as indexed functions, just as
larger routines do. This is not a measure of equal effort or game feature
coverage.

## Preserved behavior

- Cleanup uses only the low bytes of its two inputs, gives reset priority,
  and can pass a wrapping cursor-minus-base size to 0x80205F64.
- The byte-swapping helper swaps both header halfwords unconditionally.
  It only swaps/relocates the pointer entries when the swapped flag bit zero
  is set. Fixed-stride metadata is not swapped by this function.
- Input device slots and vtables are read when reached, so a callback can
  alter a later slot. The ending input method reloads the pending field
  after its first conditional callback.
- The base constructor records allocation failure as zero, forwards the
  called constructor's return value to the global, and returns the original
  application pointer. Only observed object fields are written.
- Application initialization returns success after the second call even
  when that second call returns false. The first call determines whether
  execution reaches it.
- Callback argument positions not established as meaningful at a call site
  use zero placeholders. These are semantic call interfaces, not an ABI
  model of all live PowerPC registers. Processor stack bookkeeping is
  represented by ordinary C execution.

## Verification

Run `python3 tools/check_runtime_helpers.py`. It regenerates original-byte
reports for all fifteen functions, rejecting an unexpected DOL revision,
then compiles the recovered C with strict host Clang warnings and checks:

- 120 cleanup branch/argument cases with exact memory and call traces.
- Both publication helpers, relocation, and header/output aliases.
- Five real Preload/Hub directory samples converted to little-endian inputs
  for the endian helper, plus empty arrays and flag preservation.
- 1,036 wrapper cases covering low-byte versus full-word normalization,
  arguments, member offsets, and unconditional success returns.
- First-stage initialization failure and ignored second-stage failure.
- All byte values plus truncation cases for the global getter/setter.
- Allocation failure and constructor return forwarding, including untouched
  neighboring application bytes.
- 64 paired input-method scenarios across all device occupancy masks,
  including callbacks that change pending work and remove a later device.

These checks compare host behavior to expectations derived from assembly;
they do not execute the original PowerPC code. Calls into unresolved game
functions use controlled callbacks, and those callees are not counted as
recovered. No original-target binary matching or game integration is claimed.
