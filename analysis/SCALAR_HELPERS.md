# Two hundred complete scalar leaf models

This batch adds **200 complete semantic models**, covering **4,132 original
bytes and 1,033 instructions** in GJUE78 revision 0. The complete inventory
now contains **400 unique functions covering 12,952 original text bytes**:
4.138% of the provisional 9,667 indexed function regions and 0.471% of the
2,747,776 DOL text-section bytes.

The new functions are small integer leaf routines from **0x80005B10** through
**0x80268E24**. This batch intentionally targets routines with no internal
branches or calls, ending in a single return. It includes field accessors,
flag changes, embedded-member setup, sparse initializers, pointer arithmetic,
word copies, global configuration setters, and scalar bit operations.

Of these 200 functions, 114 perform stores without target reads, 53 perform
both reads and stores, and 33 produce scalar results without stores.
Distinct original functions with duplicate setter/copy behavior count
separately. Constant-only return routines were excluded from this batch.
Function count does not measure equal effort, gameplay features, or overall
decompilation completion.

## Recoverable source and explicit specifications

- `src/recovered/scalar_leaf_helpers.c` contains ordinary C expressions,
  captured target reads, and ordered writes for all 200 routines.
- `scalar-helper-specs.json` preserves each address, original byte size,
  recovered expressions, ordered reads/writes, and result expression.
- `tools/render_scalar_helpers.py` deterministically renders those explicit
  specifications as C. Run with `--write` to regenerate; without that flag
  it checks that specifications and source agree.
- `scalar-helpers-summary.json` records each routine's verification results,
  plus hashes of the source and specifications.
- `semantic-functions.json` maps the full 400-function inventory to source
  definitions and original sizes.

The expressions were recovered by propagating the disassembly's integer
values and folding constants for this restricted straight-line subset.
Target loads are captured before later operations, preserving aliasing and
access order. The rendered C contains no instruction bytes, inline assembly,
register-machine interpreter, original stack bookkeeping, or dynamic dispatch
on opcodes. The renderer works from the explicit expression specifications;
it does not read the original executable or regenerate expressions from it.

The uniform host harness arguments represent original r3..r6. Each function
returns the final observed r3 bits for differential verification, including
incidental r3 contents in routines that may originally have returned void.
This is not a claim that original function prototypes or class names have
been recovered. CR/XER side effects are outside the modeled call interface;
none of the selected routines consumes carry produced by an earlier
instruction. Callee ABI compatibility and binary matching remain separate.

## Preserved details

- Target addresses and arithmetic wrap at 32 bits, independently of host
  pointer size. Byte/halfword stores truncate without touching neighbors.
- Original read and write widths, order, and values are preserved, including
  repeated loads and overlapping input/output regions.
- Global SDA-relative accesses resolve to their target addresses. Constant
  high/low address construction is folded into normal target constants.
- Boolean bit tricks, masked extracts, negation, and leading-zero counts
  preserve full word behavior rather than assuming input values are 0/1.
- Arithmetic right shift is implemented with explicit sign fill. Negation
  and subtraction use unsigned modulo arithmetic, avoiding signed overflow.
- Constructor-like routines retain all observed stores, including temporary
  table-pointer stores later overwritten by another table pointer.

## Differential validation

```sh
python3 tools/render_scalar_helpers.py
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 tools/check_scalar_helpers.py
python3 tools/check_leaf_helpers.py
python3 tools/check_resource_leaf_helpers.py
python3 tools/check_semantic_progress.py
```

The scalar checker validates the expected original executable revision and
all indexed function words against the DOL. It rejects incomplete regions
or any selected routine with a branch/call before its final `blr`, then
compiles the rendered C using host Clang with strict warnings.

The independent PowerPC runner decodes and executes the **original machine
words**, while the C uses the recovered expression models. Each routine
receives **128 deterministic scenarios**, for **25,600 comparisons**:

- Integer edges from zero through byte/halfword limits and signed word limits.
- Distinct scalar parameters and overlapping input/output addresses.
- Addresses around zero, normal target buffers, and 32-bit wraparound.
- Zero, all-ones, incrementing-byte, and hashed byte-addressed memory.
- Randomized argument values and explicitly seeded neighboring bytes.

Every case compares the final r3 harness bits, every target read and write
(including read values, widths, addresses and order), and final memory.
All **1,033 original instructions** execute in the comparisons. Any
instruction coverage gap fails the check.

The oracle gained integer negation, leading-zero count, immediate subtraction,
NOR, arithmetic right shift, and indexed byte load support. Fifteen independent
oracle tests pass, including new expected-value tests for those operations.
The preceding 70- and 100-function batches pass their 1,680 and 3,200
differential cases after the extension.

Synthetic memory is a total byte-addressed space with deterministic default
contents. Arbitrary target pointers never become host pointer dereferences.
These tests do not establish real GameCube memory mapping, faults, MMIO,
caches, timing, FPU behavior, or game integration. Finite comparisons are
evidence of semantic recovery, not exhaustive proof over all target states.

## Matching and accounting

No new compiler matches are claimed. The independently recorded **22 exact
function-code matches** remain unchanged; no linked game executable is rebuilt.
The inventory checker validates all 400 source definitions, unique and
non-overlapping original regions, original bytes, and byte totals. Partial
models and the offline world-record reader remain excluded.
