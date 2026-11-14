# Second thousand: matched small routines and context models

This batch adds **1,000 complete indexed routine models**, bringing the
inventory to **2,000 models covering 115,136 original text bytes**. These
measure 20.689% of the provisional 9,667 indexed regions and 4.190% of DOL
text bytes. The inventory includes both game and SDK/runtime routines;
it is not 20.689% completion of a gameplay source port.

## Batch composition

| Group | Routines | Original bytes | Evidence |
| --- | ---: | ---: | --- |
| Small target-layout C routines | 802 | 5,008 | Entire compiled function code exactly matches original bytes |
| Integer register-context C models | 198 | 40,276 | 12,672 terminating original-PPC/C comparisons |
| Added total | 1,000 | 45,284 | Distinct non-overlapping original regions |

The small group consists of **352 empty methods, 166 constant-return stubs,
119 integer loads, 54 integer stores, 33 small-data address returns, 25
offset calculations, one argument-forwarding helper, and 52 float loads or
stores**. Small stubs are counted explicitly: this milestone is not 1,000
equally complex new gameplay algorithms. Constant/empty methods were excluded
from an earlier batch but are included here as whole original functions with
measured compiler matches.

The other 198 models prioritize remaining integer functions with multiple
instructions, branches, loops, and stack/register save/restore sequences.
They remain low-level generated C, not recovered original classes or typed
source structures.

## Exact matching of small routines

`src/matching/small_helpers.cpp` provides typed target-layout C under per-address
preprocessor guards. Empty methods and constant returns are ordinary C bodies;
loads/stores use explicit field widths and offsets. There is no assembly
substitution or injected original instruction data.

`tools/check_small_helpers.py` compiles each routine separately with
CodeWarrior GC 1.3.2 using:

```text
-c -lang c++ -proc gekko -O4,p -nodefaults -fp hard
```

The hardware floating-point option is material for the 52 float helpers:
without it, this compiler's default under `-nodefaults` generates integer
loads/stores instead of the original floating-point instructions. The matching
check compares the complete function region, including resolved relocations,
with no byte masks. Only exact matches enter this source/specification batch.

`small-helper-specs.json` records each C definition, original symbol/address,
size, routine kind, external symbol addresses, and declarations.
`small-matching-summary.json` records every match plus compiler, runner, source,
object and executable hashes. Compiled outputs remain ignored under `build/`.

The pre-existing all-model survey established 255 exact matches among the
first 1,000 models. These 802 are disjoint additions, bringing the combined
matching inventory to **1,057 unique function-code matches covering 11,096
original bytes**. `matching-overview.json` combines the two reports without
double-counting addresses. It records **1,802 surveyed models** and **198 not
yet surveyed for compiler matching**. No combined 2,000-function compiler
survey or linked game executable is claimed.

## Register-context recovery

`src/recovered/context_leaf_helpers.c` represents complete supported integer
instruction regions as ordinary C control flow. The shared recovery helper
now accepts an explicit context for 32 integer registers, LR, CTR, and the
LT/GT/EQ bits of eight comparison fields. Stack addresses are target addresses
accessed through callbacks; they are never dereferenced as host pointers.

The new support includes word/halfword update stores, multiple-register
save/restore, link-register reads/writes, count-register reads, and left-bit
extracts. Effective addresses are captured before multiple-register loads can
overwrite their base. SDA accesses use the actual base register from the
verified instruction, rather than assuming every global uses r13.

All 42 modeled context words and every memory read/write are compared with
original machine-word execution. The context is a research interface, not an
inferred C/C++ prototype, original ABI replacement, or full CPU model. XER,
FPU arithmetic, exceptions, devices, caches and timing remain outside it.
Unsupported instructions and external transfers remain excluded.

Each of 198 accepted routines passes **64 terminating comparisons** using a
**4,096-instruction budget per attempted case**. The accepted cases exercise
**9,271 of 10,069 original instructions (92.075%)**. All original instruction
bytes are verified, but finite scenarios do not cover every path or prove
correctness for all possible states. The summary lists every unexercised
address. **5,456 attempted original executions** exceed the budget and are
excluded from the successful comparison count; they are not classified as
original-code failures.

`context-helper-specs.json` holds all selected bodies and reachability
metadata. `context-helpers-summary.json` records successful scenario numbers,
coverage, budget exclusions, and the source hash. The selected final source
is compiled and checked independently after selection.

## Reproduce and audit

```sh
python3 tools/check_small_helpers.py
python3 tools/check_context_helpers.py
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 -m unittest discover -s tests -p test_integer_recovery.py
python3 tools/check_integer_helpers.py
python3 tools/update_matching_overview.py
python3 tools/check_semantic_progress.py
```

The 24 oracle tests include stack-pointer updates, multiple-register transfers
and link-register preservation. Ten recovery-boundary tests pass, including
the explicit stack/register-context mode. The preceding integer-model batch
is regression checked because it shares the recovery/oracle implementation.

`semantic-functions.json` maps every one of the 2,000 addresses to a source
definition and original size, distinguishing matched small routines from
register-context models. The inventory checker validates source definitions,
original executable identity, all instruction bytes, unique regions and totals.
Partial DBU/world-volume models and the offline record reader stay excluded.

The previous matching survey remains a historical report for its original
1,000-model scope; the matching overview is the combined current snapshot.
None of these individual function-code matches establishes complete linked
executable reproduction, verified data layout for the whole game, or a native
playable source port.
