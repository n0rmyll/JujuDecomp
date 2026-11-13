# One hundred additional resource and state helpers

`src/recovered/resource_leaf_helpers.c` adds **100 complete semantic
function models**, covering **3,888 original bytes and 972 instructions**
in GJUE78 revision 0. The project inventory now contains **200 complete
models covering 8,820 original text bytes**: 2.069% of the provisional
9,667 indexed regions and 0.321% of DOL text bytes.

These are host semantic reconstructions. No additional compiler matches,
rebuilt game executable, or native port are claimed. The separately recorded
22 exact function-code matches remain unchanged.

## Scope and provenance

The new routines occupy distinct original regions from **0x801A1798**
through **0x801E6710**. `resource-leaf-helpers-summary.json` lists each
address, original size, observed behavior, return-check classification,
instruction coverage, and test count. The full project inventory is
`semantic-functions.json`.

The batch includes:

- Object initialization, null-aware accessors and byte/halfword flags.
- Two global iterators, halfword-filtered start/continue operations, and
  an inline push/pop stack for loader flags.
- Direct/indexed resource lookup, output publication, nested record-address
  calculations and type-dependent 16/32-byte alignment.
- Array-wide field updates, first-free-slot insertion, a masked pointer
  accessor, low-halfword population count, and a separate 32-bit pattern scan.
- Linked-list boolean searches, key searches, prepend/unlink, flag filters,
  collection into an output array, conditional replacement, and global pop.
- Indexed slot access, signed byte reads, relative-offset resolution,
  conditional stream-word skips and unconditional owner flag updates.

Small accessors and independently indexed routines with duplicate flag or
publication behavior count separately. They are not equal-sized units of
work, and these percentages do not measure game features or matching code.
Address labels avoid assuming original class names or resource semantics.

## Details retained from the original instructions

- The first two list-cursor advancement helpers do not guard a matching
  null pointer before dereferencing it. The models preserve that access.
- The flag stack has no overflow/underflow checks. All target arithmetic
  wraps modulo 2^32; underflow and stores that alias stack metadata are
  included in the comparisons.
- Filtered iteration reloads the global cursor and filter where the original
  reloads them, writes the cursor while skipping nodes, and advances again
  after yielding a matching value.
- Halfword and byte operations preserve neighboring bytes and unaffected
  flag bits. Boolean inputs are narrowed only at observed low-byte tests.
- Record output stores can alias headers, count fields and cursor metadata;
  loads remain in original order rather than caching values across stores.
- `0x801C3ACC` counts only the low 16 input bits. `0x801C5378` performs a
  distinct 32-step scan with a first-zero/later-one rule; it is not treated
  as a normal population count.
- Unlink searches for the predecessor without a null guard. Tests use nodes
  that belong to the owner list; absent/cyclic inputs can fail to terminate.
- Slot-relative resolution at `0x801E5530` reloads owner/table pointers and
  the slot pointer, preserving behavior when output stores alias them.
- `0x801E6688` and `0x801E66CC` always change their owner's flag, whether
  or not a conditional stream-word skip occurs. `0x801E6710` decrements the
  slot byte when a slot exists; when no slot exists it advances the stream
  cursor unconditionally. No additional validation is introduced.

## Verification

```sh
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 tools/check_resource_leaf_helpers.py
python3 tools/check_leaf_helpers.py
python3 tools/check_semantic_progress.py
```

The new checker builds the C with host Clang and strict warnings, validates
the expected DOL SHA-256, and checks all 972 instruction words against the
local indexed disassembly. The limited integer PowerPC runner executes those
**original machine words**, independently of the hand-written C models.

Each routine is tested with **32 deterministic synthetic scenarios**, for
**3,200 differential cases**. The checker compares complete target memory
read/write traces (widths, addresses, ordering, and stored values), final
memory, and results for value-returning routines. Void-operation harness
results are unspecified and are not counted as recovered ABI behavior.

Inputs include signed limits, byte and halfword truncation, null objects,
zero/one/multiple-node lists, first/middle/last/no matches, inline stack
underflow, address wrap, aliasing between outputs and metadata, all 16
occupancy masks for the four-slot test, and conditional cursor
updates. Every new routine has its own address-specific fixtures.

The scenarios execute **971 of 972 original instructions**. The only
unexecuted instruction, **0x801E58AC**, is a list-head reload reached only
by a null test on a node already known nonnull, with no intervening change
to that register. The checker enforces this precise exception; any other
instruction coverage gap fails.

The oracle gained `lwzu` support for the global flag update. Two new
independent tests verify base-register update and rejection of invalid
operands. All ten oracle tests pass, and the preceding 70-function batch
also passes its 1,680 differential cases after this addition.

As in the prior batch, synthetic unmapped bytes read as zero. The runner
does not model GameCube mapping, faults, MMIO, caches, timing, FPU operations,
or a running game. It rejects unsupported instructions/external branches
and enforces an instruction budget. Finite scenarios provide evidence of
semantic recovery, not an exhaustive proof over every possible input.

The inventory checker validates 200 distinct source definitions against
non-overlapping indexed regions and all original instruction bytes. Partial
DBU/world-volume models, the offline reader and unresolved callees stay
outside the complete-function count.
