# Remaining-function pass: verified progress and explicit blockers

**The request to finish every remaining function is not complete.** This pass
adds **1,160 verified indexed models**: 50 integer-context projections and 1,110
finite-domain scalar-transfer projections. **2,507 indexed regions remain
unresolved and excluded from the recovered inventory.** No placeholder bodies
or opaque replacements for unsupported instructions enter the count.

The inventory now has **7,160 distinct models / 1,158,944 original code bytes**,
covering 74.066% of the provisional 9,667 indexed regions and 42.178% of DOL
text bytes. Twenty source files provide the counted definitions. These are
model-coverage measures, not native-port or compiler-matching percentages.

## All remaining regions accounted for

`remaining-functions.json` maps every unresolved original address, name, size
and assembly file to a blocker. Its groups are exclusive, assigned in the
order shown by the audit tool; operation lists can overlap.

| Primary blocker | Indexed regions |
| --- | ---: |
| Paired-single or quantized operations | 931 |
| Other scalar floating operations or control | 1,135 |
| Processor state or hardware operations | 87 |
| Other unsupported integer operations or control flow | 230 |
| Supported projection, insufficient comparison evidence | 124 |
| **Unresolved total** | **2,507** |

These remaining regions account for **1,588,628 original indexed bytes**.
The index is provisional and includes SDK/runtime code. The audit checks
original bytes and proves the partition: **7,160 counted + 2,507 unresolved =
9,667 indexed regions**, with no duplicated addresses. It does not mark an
unsupported instruction as recovered merely because disassembly is available.

Completing these groups requires broader floating/paired-single and processor
state recovery, plus better execution fixtures or nontermination reasoning for
the insufficient-evidence regions. The current machinery cannot verify those
bodies. Existing caller contracts also leave real callee behavior unresolved.

## Additional integer models

`remaining_integer_helpers.c` contains 50 new integer-context projections,
covering **88,868 original bytes / 22,217 instructions**. There are 31 callers
with opaque external boundaries and 19 call-free regions. The verifier tries
up to 1,024 deterministic scenarios per candidate while retaining the
2,048-instruction caller budget and at least 64 successful comparisons.

These models pass **3,414 terminating comparisons**. Successful cases exercise
11,150 instructions; all instructions execute in 22 models. Selected routines
have 4,068 budget-exceeded and 3,744 undefined-division attempted cases, excluded
from success counts. Of 157 supported integer candidates, 107 remain excluded
for insufficient evidence. The selection report preserves their addresses.

These are integer projections, with the same original-type, ABI, XER and callee
limitations as the [preceding batch](FIFTH_SIXTH_THOUSAND.md).

## Scalar-transfer projections

`scalar_transfer_helpers.c` contains **1,110** models covering **276,944 original
bytes / 69,236 instructions**, including 11,928 floating transfer instructions.
There are 879 callers with opaque boundaries and 231 call-free regions.
The supported operations are `lfs`, `stfs`, `lfd`, `stfd` and non-recording `fmr`,
alongside the established integer subset. Floating arithmetic is rejected.

The interface adds 32 scalar binary64 words to the existing 42-word integer
context. It models scalar PS0 interpretation; **PS1, mixed scalar/paired
reinterpretation, FPSCR, XER, exception behavior and real callees are unresolved**.
This is not a complete Gekko FPU model or an ABI-compatible game replacement.

Single conversions admit **signed zero and exactly representable normal
binary32 values only**. Native expansion/contraction uses explicit integer bit
operations. The independent word runner uses separately implemented host
binary packing and rejects non-finite, subnormal, overflowing or inexact single
conversions before native comparison. Fallback zero values in generated helper
guards are outside the admitted domain, **not recovered hardware behavior**.
Raw double loads/stores and register copies preserve scalar binary64 bits.
Double memory transfers use two ordered 32-bit callbacks in this ordinary-memory
projection; atomic device behavior is not claimed.

The scalar load conversion design follows [IBM's load-single documentation](https://www.ibm.com/docs/da/ssw_aix_72/assembler/idalangref_lfs_lfps_instr.html).
The PS0/PS1 distinction and paired-state limits are described in the
[IBM Gekko manual, programming model and load/store sections](https://datasheets.chipdb.org/IBM/PowerPC/Gekko/gekko_user_manual.pdf).
The controlled fixtures do not establish behavior on actual console hardware.

These models pass **71,127 terminating comparisons**, at least 64 per model.
Successful cases exercise 56,325 instructions; all instructions execute in 903
models. There are 266,392 synthetic opaque-call events. Call contracts preserve
most scalar registers and supply finite scalar f0/f1 effects, alongside the
existing controlled integer and bounded-memory effects. Both complete pre-call
contexts and all post-call scalar words are compared. They are test doubles,
not recovered callees.

Selected scalar routines have 1,043 budget-exceeded and 35,339 floating-domain
attempt exclusions. These are not successful comparisons. Of 1,127 candidates,
17 have too little admitted terminating evidence and remain uncounted.

## Validation

The two new groups pass **74,541 comparisons** in total. Every original
instruction word is verified against the expected local DOL revision. Checks
compare integer results, complete modeled integer/scalar contexts, ordered
memory and call traces, and final synthetic memory. Successful cases exercise
**67,475 / 91,453 instructions (73.781%)**. Every unexercised
address is listed in the per-routine summaries; path coverage is incomplete.

Both selected source sets are compiled and compared again, reproduce from
verified original disassembly, and pass strict instrumented and normal host
Clang builds. Four transfer tests cover 528 bit-pattern round trips, signed
zero, normal exponent boundaries, wrapped addresses, double transfer ordering,
callee scalar effects and explicit unsupported-domain rejection. The existing
33 oracle and 16 integer/recovery/native-extension tests pass. The preceding
1,000-model caller batch still passes 64,069 comparisons with the updated oracle.

## Reproduce

```sh
python3 tools/recover_call_helpers.py --batch 6
python3 tools/check_call_helpers.py --batch 6
python3 tools/check_transfer_helpers.py --reproduce
python3 tools/check_transfer_helpers.py
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 -m unittest discover -s tests -p 'test_integer*.py'
python3 -m unittest discover -s tests -p test_transfer_recovery.py
python3 tools/audit_remaining_functions.py
python3 tools/check_semantic_progress.py
python3 tools/update_matching_overview.py
```

`--batch 6` selects the variable-size remaining integer group; earlier batch
identifiers and source artifacts are preserved. Selection summaries retain
excluded candidates separately from successful final verification summaries.

**Exact compiler matches remain 1,057 routines / 11,096 original bytes.**
Of 7,160 models, 1,802 have compiler-survey results and 5,358 have not been
surveyed for matching. No linked executable rebuild or playable native port is
claimed. The 2,507 unresolved regions need substantive recovery work; they are
not counted as complete.
