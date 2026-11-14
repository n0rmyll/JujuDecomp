# Fifth and sixth thousand: another 2,000 indexed models

This batch adds **2,000 distinct indexed integer-context models**, covering
**312,304 original bytes / 78,076 instructions** in GJUE78 revision 0.
The inventory now contains **6,000 models / 793,132 original text bytes**:
62.067% of the provisional 9,667 indexed regions and 28.865% of DOL text bytes.
These percentages describe indexed model coverage, not a playable source port
or binary-matching completion.

The new batch contains **1,953 compositional caller-body projections** with
opaque external boundaries and **47 call-free integer register-context
projections**. It includes game and SDK/runtime code, short forwarding thunks
and register accessors. There are 156 regions of at most 16 bytes, including
two four-byte external forwarding thunks. Original addresses range from
0x80005518 to 0x802A19B4; sizes range from 4 to 1,660 original bytes.
Referencing a callee does not add that callee to the recovered count.

## Artifacts

- `src/recovered/fifth_sixth_call_leaf_helpers.c`: 2,000 separate native C
  functions using the explicit 42-word integer context and target-memory
  callbacks. The common call interface is unused by the 47 call-free models.
- `fifth-sixth-call-helper-specs.json`: original names, source bodies, static
  reachability and 6,767 possible external call/transfer sites.
- `fifth-sixth-call-helpers-summary.json`: per-routine successful scenarios,
  reached instructions, coverage gaps, call counts, excluded attempts and
  source/specification hashes.
- `fifth-sixth-call-selection-summary.json`: 2,157 proposed candidates, 2,132
  considered, 132 excluded and 25 unattempted, with excluded addresses preserved.
- `semantic-functions.json`: distinct indexed regions, original sizes, source
  definitions and per-entry scope, with no overlaps or duplicate addresses.

The generated C represents control flow directly. Indirect jumps use explicit
switches over internal instruction addresses; external destinations cross an
opaque tail-transfer boundary. They do not execute original opcode data.

## Recovery support added

The translator and independent original-machine-word runner now support no-op
instructions, high-half XOR, clearing/setting modeled condition bits, high-half
signed/unsigned multiplication, integer division, add-immediate-with-record,
subtract-from-carry's integer result, and indirect CTR tail dispatch. Incoming
register values remain explicit. Carry/SO and other XER state are outside the
projection; operations that consume unmodeled carry are still rejected.

Indirect dispatch represents internal targets as branches to C blocks and
external targets as opaque boundaries, masking the low two target bits. There
are 34 selected models containing this dispatch. Focused tests exercise both
internal and external destinations and preservation of the link register.

Signed division uses truncation toward zero. Divide-by-zero and signed
minimum/-1 overflow attempts are excluded: the original result is not defined
for this comparison domain. The generated helper's guard value is not a claim
about hardware behavior on those inputs.

## Verification and coverage

The final selected source passes **128,157 terminating comparisons**, at least
64 per model. All 1,953 caller models exercise an external boundary in at least
one successful case; call-free models have no such requirement. Comparisons
check integer results, all 42 modeled context words, ordered target-memory
reads/writes, opaque-call targets and pre-call contexts, and final synthetic
memory. The oracle decodes original machine words independently of the C
translation and checks every original word against the expected local DOL.

Successful cases record **304,940 synthetic opaque-call events**. The callee
contracts are the established zero/one/pointer/scalar returns and bounded
object-field modifications. These are controlled test doubles, not real game
or SDK callee implementations. Original prototypes, floating-point ABI effects
and real callee behavior remain unresolved.

Successful cases exercise **63,036 / 78,076 instructions (80.737%)**.
All instructions execute in 1,618 models. **15,040 instruction addresses remain
unexercised** across the other 382 models; the summary lists every address.
Not every branch or external site is dynamically covered.

Among selected routines, **5,197 attempted cases exceed the 2,048-instruction
caller budget**, and **349 attempts encounter undefined integer division**.
Neither group enters the successful comparison count. Selection also excludes
132 candidates that lack enough terminating evidence or an exercised external
boundary. Unattempted remaining candidates are not counted.

The selected source is compiled and compared again after selection, reproduces
from the verified original disassembly, and passes strict host Clang checks
with and without verification instrumentation. The preceding 1,000-model batch
still passes all 64,069 comparisons. The focused test suites pass 33 oracle,
14 recovery-boundary and two native extension tests (49 total). Earlier caller
source/specification sets also still reproduce without changes.

## Reproduce

`--batch 5` identifies this combined 2,000-model fifth/sixth-thousand batch;
the default remains batch 3. Existing batch 3 and 4 artifacts are preserved.

```sh
python3 tools/recover_call_helpers.py --batch 5
python3 tools/check_call_helpers.py --batch 5
python3 tools/check_call_helpers.py --batch 4
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 -m unittest discover -s tests -p test_integer_recovery.py
python3 -m unittest discover -s tests -p test_integer_extensions.py
python3 tools/check_semantic_progress.py
python3 tools/update_matching_overview.py
```

`tools/select_call_helpers.py` proposes supported, previously uncounted regions
for future work; proposals do not enter the inventory until verification.

## Limits and matching

These are low-level integer projections under explicit interfaces and controlled
callee contracts. They do not establish original types, real callee semantics,
FPU/XER state, hardware memory validity, exceptions, timing or gameplay behavior.
The C is not an ABI-compatible replacement for the original executable. The
provisional function index includes SDK/runtime regions and may not correspond
one-to-one with original source functions. See the [preceding caller report](FOURTH_THOUSAND.md)
and [call-interface findings](THIRD_THOUSAND.md) for the shared scope.

**Exact compiler matches remain 1,057 routines / 11,096 original bytes.**
Of 6,000 models, 1,802 have compiler-survey results and 4,198 have not been
surveyed for matching. No new compiler match or linked executable rebuild is
claimed by this batch.
