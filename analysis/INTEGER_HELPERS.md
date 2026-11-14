# Six hundred complete low-level integer C models

This page describes the earlier call-free batch. The later call-aware variant
of the shared recovery code is documented in [third-thousand findings](THIRD_THOUSAND.md),
including its explicit opaque-callee boundary and verification limits.

This batch adds **600 complete indexed routine models**, covering **56,900
original bytes and 14,225 instructions** in GJUE78 revision 0. Combined with
the previous 400 models, the inventory reaches **1,000 routines covering
69,852 original text bytes**: 10.344% of the provisional 9,667 indexed regions
and 2.542% of DOL text bytes.

The new batch contains both game-specific routines and SDK/runtime routines.
For example, 254 selected addresses lie in the 0x8010A800..0x80150000 SDK
region, and 23 retain non-address original symbol labels. These classifications
are clues rather than a full provenance audit. This is an inventory of the
compiled executable's routines, not 1,000 independently named gameplay
functions or 10.344% of a working source port.

## What is recovered

`src/recovered/integer_leaf_helpers.c` contains generated **low-level C with
explicit branches, labels, loops, register-sized local values and target-memory
callbacks**. It is a step below recovered class structures and original typed
source. Each counted routine has its complete indexed instruction region
represented; these are not call-through wrappers or partial function bodies.

The batch includes list traversal, search and manipulation; string and byte
copying; table and buffer operations; conditional object setup; flag and
bit-field operations; pointer and integer calculations; and SDK register/data
access helpers. Small and duplicate helpers count separately when they occupy
distinct original regions. Function count is not a measure of equal effort.

Original function names, source addresses, model kind and sizes are recorded
in `semantic-functions.json`. `integer-helper-specs.json` preserves the full
recovered C body, access-site count, and static reachability information for
each new routine. `integer-helpers-summary.json` records differential cases,
accepted scenario numbers, original execution-budget exclusions, instruction
coverage, and source/specification hashes.

The host interface accepts eight integer inputs corresponding to original
r3..r10 and optionally publishes all eight final register values. It also
returns the final r3 bits. Publishing r4 retains potential wide return values;
this does not infer original prototypes, original C++ class names, or argument
types. Target reads/writes retain their original widths, ordering and values.
The host output array is separate from target memory.

## Recovery boundaries

`tools/integer_recovery.py` translates a restricted integer disassembly subset
into separate ordinary C functions. The result contains no opcode dispatcher,
embedded original code bytes, inline assembly, or calls back into an emulator.
The independently implemented test oracle executes original machine words.

The recovery rejects:

- Unsupported instructions, floating-point operations and privileged CPU work.
- External calls, external jumps, and indirect transfers beyond ordinary return.
- Stack-pointer use and mutation of the two established global base registers.
- Reads of implicit incoming temporary registers or comparison/count state.
- Incomplete instruction regions and transfers outside the indexed function.

A control-flow must-definition analysis checks every statically reachable
instruction: ordinary integer arguments and fixed global bases are explicit
inputs; other values must be defined along every incoming path before use.
This includes joins and loops. Signed comparisons, sign extension, arithmetic
right shifts, and modulo arithmetic use explicit unsigned C operations.

The supported interface models integer result registers and ordered memory
effects. It is not a complete CPU context/ABI simulation. CR comparisons and
count-register values are tracked where consumed inside a routine; unused
external CR/XER side effects, CPU exceptions and hardware timing are not
modeled. No selected routine consumes arithmetic carry generated earlier.

## Reproduction

```sh
python3 tools/recover_integer_helpers.py
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 -m unittest discover -s tests -p test_integer_recovery.py
python3 tools/check_integer_helpers.py
python3 tools/check_semantic_progress.py
```

The recovery command verifies the expected local DOL revision and original
instruction bytes, re-derives all 600 models from the indexed disassembly,
and checks the saved specifications/source. Add `--write` to regenerate those
files, then rerun differential verification. The default command does not
change either source or specifications.

Both the production and instrumented C build with host Clang and strict
warnings. Verification-only instrumentation adds an instruction budget to the
C execution. It is disabled in a normal build, so production models retain
the original termination behavior rather than adding target-visible guards.
The temporary compiled verification library is not a PowerPC binary match.

## Differential evidence and limits

Each accepted routine passes **64 terminating scenarios**, for **38,400
original-PowerPC/C comparisons**. Each compares r3..r10 output values, every
target read/write including widths, addresses, values and ordering, and final
synthetic target memory. The selected source/specification set is compiled and
verified again after initial selection.

Inputs include integer limits, small scalar parameters, null and overlapping
addresses, an acyclic synthetic object/table graph, and several deterministic
memory patterns. The memory is a total byte-addressed space, so arbitrary
target addresses never become host pointer dereferences.

Original execution receives a **1,024-instruction budget per attempted case**.
Across the selected routines, **2,557 attempted cases exceed that budget** and
do not count as successful comparisons. Such cases may represent loops,
cyclic/malformed synthetic structures or simply more work than the budget
permits; the checker does not classify them as original-code failures. For a
terminating original case, C budget exhaustion is a verification failure.

The successful cases execute **12,881 of 14,225 original instructions
(90.552%)**. All instructions execute in 490 of the 600 models. There are
**1,344 unexercised instructions** across the remaining models: five are
statically unreachable in their indexed control flow, while 1,339 remain
statically reachable and were not covered by these scenarios. Every gap is listed by address
in the summary. Entire indexed function bodies are modeled, but this batch
does **not** claim full dynamic path/instruction coverage or exhaustive
correctness across all inputs.

The oracle extension supports record-setting immediate addition/subtraction,
byte/halfword update loads, byte update stores, indexed halfword stores,
variable right shifts, XOR and eight argument registers. All **23 oracle
unit tests** and **nine recovery-boundary tests** pass. The latter exercise
undefined inputs, conditional definitions, global-base mutation, unsupported
operations, external transfers, reachability and SDA resolution. The preceding
70-, 100- and 200-function batches are regression-checked separately.

Synthetic comparisons do not establish GameCube memory faults/mapping, MMIO
device behavior, caches, threading, timing, FPU behavior, or game integration.
Hardware-facing routines are modeled as ordered raw accesses through callbacks;
no device emulation is claimed. These tests are finite evidence, not a formal
proof or a verified game rebuild.

## Accounting and matching

`tools/check_semantic_progress.py` verifies all 1,000 source definitions,
unique/non-overlapping indexed regions, original instruction bytes and total
coverage. Partial DBU/world-volume models and the offline record reader stay
outside the complete-function count. The latest 600 entries are explicitly
tagged as generated low-level integer control-flow models.

The independent **22 exact function-code matches** remain unchanged. No new
CodeWarrior matches, linked executable rebuild or native source port are
claimed by this batch.
