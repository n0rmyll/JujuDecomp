# Fourth thousand: another integer caller-body batch

This batch adds **1,000 indexed caller-body models**, covering **204,900
original bytes and 51,225 instructions** in GJUE78 revision 0. The inventory
now contains **4,000 models covering 480,828 original text bytes**: 41.378%
of the provisional 9,667 indexed regions and 17.499% of DOL text bytes.

These are the same research tier as the preceding caller batch: **generated
integer caller-body projections with explicit opaque external callees**.
Every supported caller instruction is represented, but original prototypes,
floating-point ABI effects and real callee behavior remain unresolved. This
is neither a new source-port completion percentage nor a compiler-match claim.

## Selected routines and artifacts

The new selected addresses range from **0x801220FC to 0x80208974** and include
game and SDK/runtime code. Candidates have at least 48 and at most 1,024
original bytes and contain direct or indirect calls. No empty or
constant-return stubs were added in this batch.

- `src/recovered/fourth_call_leaf_helpers.c` contains the 1,000 distinct native
  C models, with explicit control flow and the shared integer/call interface.
- `fourth-call-helper-specs.json` records bodies, original names, static
  reachability and **3,860 external call sites**.
- `fourth-call-helpers-summary.json` records accepted scenarios, context/memory
  comparisons, reached calls, coverage gaps, execution-budget exclusions and
  source/specification hashes.
- `semantic-functions.json` identifies these entries as compositional caller
  models and maps them to their source definitions and original sizes.

Only distinct original caller regions enter the count. Referencing an
external function does not count as recovering that callee.

## Verification

The selected final source passed **64,069 terminating comparisons**, at least
64 per routine. **Every selected routine reaches an external call boundary**
in a successful case. Cases are retained beyond the first 64 when necessary
to exercise such a boundary. Routines without enough terminating evidence or
a reached boundary are excluded.

The native C and independent original-machine-word runner compare:

- All 42 modeled integer-context words, including LR, CTR and comparison bits.
- Every target read/write, including widths, addresses, values and ordering.
- Call targets, complete pre-call contexts, continuation addresses and caller
  execution after controlled callee effects.
- Final synthetic memory and integer results.

Successful cases record **154,943 synthetic opaque-call events**. Callee
callbacks use the same zero/one/pointer/scalar return contracts and bounded
object-field modification as the preceding batch. They are **test doubles**,
not implementations or verification of the corresponding game/SDK functions.

All **51,225 original instruction words** were checked against the expected
local DOL revision. Successful cases execute **44,885 instructions (87.623%)**;
all instructions execute in 661 models. **6,340 instructions remain
unexercised** across the other models, with every address listed in the summary.
Not every branch or call site is dynamically covered.

There are **4,520 budget-exceeded attempted cases** among the selected routines.
They are excluded from the comparison count and are not treated as failures
of the original game. The budget remains 2,048 caller instructions per attempt;
callee test-contract execution is outside that caller count. C exhaustion
when the original caller returns is a verification failure.

The source/specification set was compiled and compared again after selection.
It also reproduces from the verified original disassembly. Strict host Clang
checks cover the verification build and normal build. No assembly or original
instruction data is substituted into the generated native C.

## Reproduce

The shared tools now accept `--batch 4`; their default remains the preceding
third-thousand batch, whose files are preserved:

```sh
python3 tools/recover_call_helpers.py --batch 4
python3 tools/check_call_helpers.py --batch 4
python3 tools/check_call_helpers.py --batch 3
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 -m unittest discover -s tests -p test_integer_recovery.py
python3 tools/check_semantic_progress.py
python3 tools/update_matching_overview.py
```

The preceding 1,000-caller batch passes its 64,103 comparisons after the
batch-routing change. All 27 oracle tests and 11 recovery-boundary tests pass.
The inventory checker validates 4,000 unique, non-overlapping indexed regions,
their original instruction bytes, source definitions and byte totals.

## Limits and matching

The opaque-call interface, test contracts and scope limits are detailed in
[third-thousand findings](THIRD_THOUSAND.md). These finite comparisons establish
caller translation evidence under supplied contracts, not real callee
semantics, original types, device behavior, valid hardware memory mapping,
FPU/XER state, exceptions, timing or gameplay behavior. The generated C is not
an ABI-compatible replacement for the original executable.

**Exact compiler matches remain 1,057 routines / 11,096 original bytes.**
Of the now 4,000 models, 1,802 have compiler-survey results and 2,198 have not
been surveyed for matching. No new matching claim, linked executable rebuild
or native playable port is made by this caller-body batch.
