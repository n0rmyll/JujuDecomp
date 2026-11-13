# Six additional complete routine models

`src/recovered/resource_loaders.c` models these GJUE78 revision 0 routines:

| Address | Original bytes | Complete observed behavior |
| --- | ---: | --- |
| 0x801C5944 | 96 | Relocate array, publish payload pointer, copy header word +4, return 1 |
| 0x801C59A4 | 96 | Same logic at a distinct original function address |
| 0x801C5A04 | 96 | Same logic at a distinct original function address |
| 0x801C5BAC | 136 | Relocate array, pass each item to 0x801C5D28, clear header flag bit 0, publish outputs, return 1 |
| 0x801C5C34 | 136 | Same processing loop with callee 0x801C5F1C |
| 0x801B90D0 | 36 | Advance global cursor +0x18 and subtract amount from remaining word +0x1C |

The first three are counted as three indexed original function regions,
not three distinct algorithms. They share a publication helper in the C
model. Together the six routines cover 596 original bytes.

The four original loader arguments are target addresses: payload, header,
output-pointer location, and output-size location. The callback interface
preserves 32-bit address arithmetic, memory access order, and aliasing.
Per-record processing is represented by callbacks for unresolved callees;
their implementations are not included in the completion count. Compiler
register-save helpers and stack bookkeeping are represented by normal C
call semantics. These are complete semantic models, not matching builds.

Important details preserved from the assembly:

- Relocation runs before processing or publication.
- The processing loops reload the u16 count after every callback and use
  the low 16 bits of the loop index. A callback can change the iteration count.
- Header flag bit zero is cleared after processing; other bits survive.
- Payload output is written before header word +4 is read, even if aliased.
- Cursor helper reads both words before either store. Addition/subtraction
  wraps modulo 2^32, with no bounds validation.

Run `python3 tools/check_resource_loaders.py`. It verifies all 149 original
instructions against the expected local executable revision, then compiles
the C with host Clang and checks:

- 25 loader executions across five real Preload/Hub directories, including
  958 per-record calls, complete payload-byte comparison, and output values.
- Three aliased header/output cases.
- Eight loop cases covering empty arrays, count shrink/growth by callbacks,
  and the maximum u16 count (65,535).
- 64 cursor cases covering exact access order and 32-bit overflow/underflow.

Tests exercise caller semantics using controlled record-processing callbacks;
they do not establish the behavior of the two unresolved record processors.
No original-target compiler match or game executable integration is claimed.
