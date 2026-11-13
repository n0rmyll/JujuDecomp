# Seventy additional complete semantic function models

`src/recovered/leaf_helpers.c` adds 70 original function regions, covering
**2,484 original bytes (621 instructions)**. Together with the previous 30,
the project now contains **100 complete semantic models covering 4,932
original text bytes**. This is 1.034% of the provisional 9,667 function
regions and 0.179% of DOL text bytes. These percentages measure semantic
coverage; compiled binary matching remains a separate metric.

The complete address/source inventory is `semantic-functions.json`.
`leaf-helpers-summary.json` lists the 70 new addresses, sizes, behaviors,
return-check classifications, and differential test counts. Each entry is
a whole indexed original function. No partial decoder or unresolved
callee is added to the count.

## Recovered behavior

The batch concentrates on related leaf routines in 0x8015C924..0x801AE384:

- Byte-string membership and space/tab skipping, including signed-byte
  comparisons and the behavior of a NUL search.
- Pointer-array iteration, signed indices, capacity-checked word-pair
  insertion, registry insertion/removal, stable in-place compaction,
  linked-list search and append.
- Fixed-stride global tables, row flag resets, request/flag operations,
  and little-endian word readers/writers.
- Record halfword resolution through either a global default or signed
  table index, and linked-list flag updates.
- Object initialization, sentinel fields, paired snapshots, global and
  object byte/halfword/word accessors, and two-dimensional address arithmetic.

These are generally small functions. Distinct indexed accessors count
individually and are listed explicitly; function count is not a measure
of equal effort or game-feature completion. Original class names, parameter
units, and high-level subsystem names remain provisional.

## Exact details preserved

- All target arithmetic wraps modulo 2^32. Signed comparisons use explicit
  bit-based ordering, avoiding host conversion assumptions.
- Callback reads and writes retain the original widths and ordering.
  Copies that load all four bytes before storing preserve overlap behavior.
- Registry search examines exactly 256 entries. Insertion in slot zero and
  a full registry both return zero, as in the original.
- Negative indices select the last item in two array helpers, without
  additional empty-array validation.
- `0x8018F74C` loads from target address zero on its out-of-range path.
  `0x801633B0` does the same if aliasing makes its second range check fail.
  These accesses are preserved, without assuming target address zero faults
  or returns a particular value.
- Table/count fields are reloaded where the original reloads them, including
  changes caused by aliased output stores.
- String membership checks the terminator before the candidate comparison,
  so a NUL search returns false. Only space and tab are skipped by the
  whitespace helper.

## Differential verification

Run:

```sh
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 tools/check_leaf_helpers.py
python3 tools/check_semantic_progress.py
```

The differential checker compiles the C with strict host Clang warnings.
It validates the original DOL SHA-256 and all function instruction bytes
against the indexed disassembly, then runs the **original machine words**
in the limited PowerPC integer oracle `tools/ppc_leaf.py`. The C and oracle
receive separate copies of the same deterministic synthetic target memory.

**1,680 scenarios** compare every target read/write (including widths,
addresses, values, and ordering), complete final synthetic memory, and the
result for routines classified as returning a value. For modeled void
operations, incidental register r3 contents are deliberately not compared.
The uniform C harness signature is not a recovered GameCube ABI.

Scenarios cover zero/positive/negative/limit values, address wrap, signed
indexing, null owners, occupied/full registries, duplicate removal, overlapping
copies, aliased stores, alternate linked-list paths, and both flag branches.
The scenarios exercise **620 of 621 original instructions**. The remaining
instruction at `0x8018D6F0` is an unreachable unconditional branch immediately
after `blr`. The checker enforces that no other instruction is unexercised.

Eight independent oracle tests cover PPC bit numbering, signed comparisons,
rotates, modulo arithmetic, count-register loops, signed halfword loads,
byte stores, SDA base addressing, and rejection of unsupported/runaway code.

The oracle supports only the integer instruction subset needed here. It
rejects unsupported instructions and branches outside the function, and
enforces an execution budget. Synthetic unmapped bytes read as zero; this
tests instruction semantics, not real memory mapping, faults, caches, MMIO,
timing, or behavior in a running game. Arbitrary malformed/cyclic lists or
unterminated strings are not made safe by the recovered routines. Passing
finite scenarios is evidence, not an exhaustive proof over all target states.

## Progress accounting

`tools/check_semantic_progress.py` validates all 100 unique addresses,
non-overlapping original regions, complete byte coverage, source definitions,
and totals against the local index and expected executable revision. It does
not substitute for behavior checks. Partial DBU/world-volume models and the
offline record decoder remain excluded.

No new compiler matches are claimed in this batch. The separately established
22 exact function-code matches remain unchanged, and no rebuilt game
executable or native port is produced by these host models.
