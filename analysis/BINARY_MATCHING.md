# Binary matching: GJUE78 revision 0

## Current combined snapshot

The first 1,000-model survey below established 255 exact matches. A disjoint
batch of 802 small target-layout C routines now also matches completely with
CodeWarrior GC 1.3.2 using `-fp hard`, bringing the combined total to **1,057
unique function-code matches / 11,096 original bytes**. This includes empty
methods and constant-return stubs, listed explicitly in the batch report.

See [the matching overview](matching-overview.json), [small-routine proof](small-matching-summary.json),
and [second-thousand findings](SECOND_THOUSAND.md). The combined survey covers
1,802 of the now 7,160 modeled routines. The remaining 5,358 register-context,
compositional caller and finite-domain scalar-transfer models have comparison evidence but have not been
surveyed for compiler matching; see [remaining-function findings](REMAINING_FUNCTIONS.md).
Earlier sections and the all-model survey snapshot retain their original
scope. No linked game executable is rebuilt.

Reproduce the new matches and combine the reports with:

```sh
python3 tools/check_small_helpers.py
python3 tools/update_matching_overview.py
```

On November 12, 2026, `src/recovered/application_flag.c` compiled to the exact
12 bytes at `0x8020F9C8` in the original executable:

```text
38000001  li  r0, 1
98030004  stb r0, 4(r3)
4e800020  blr
```

The actual recovered source uses an unsigned-byte store without SDK headers.
Compiler: original CodeWarrior GC 1.3.2 executable, reporting **2.4.2 build 81**.
Flags: `-c -lang c -proc gekko -O4,p -nodefaults`. Execution uses **wibo 1.2.0**,
verified on this Intel macOS host. No assembly substitution is used.

## Reproduce

```sh
python3 tools/setup_matching.py
python3 tools/check_application_flag.py --mw-cc tools/mwcc/GC/1.3.2/mwcceppc.exe --runner tools/wibo
```

The setup script also accepts `--archive /path/to/compilers_20251015.zip`.
All downloaded tools stay ignored. The checker verifies the original DOL's
SHA-256, runs the existing exhaustive host behavior test, validates that the
output is a big-endian 32-bit relocatable PowerPC ELF, rejects relocations
targeting `.text`, and compares the complete text section against the original.
The successful run writes `build/application-flag/match.json` with hashes,
command, and matched bytes. Failed or host-only runs remove a previous report.

## Tool provenance

- [wibo 1.2.0](https://github.com/decompals/wibo/releases/tag/1.2.0), macOS executable SHA-256:
  `2b3000ef6a7a490c24ccd71967735ae0005e218922e51806cca1b8d77fd3cf7c`.
- [Compiler archive, October 15, 2025](https://files.decomp.dev/compilers_20251015.zip), downloaded archive SHA-256:
  `491cb62317c7f3669ac283ae159e82e3c97a5713b78299571ba4cf023dc7e95e`.
- Archive member `GC/1.3.2/mwcceppc.exe`, SHA-256:
  `7cbae0a5bd81e07d7fa8975bbc4e969b5dea265cc29c5ee6bae0453a6e25f225`.

The archive/compiler hashes pin the artifacts inspected in this workspace;
they are not independently authenticated publisher checksums. The runner hash
agrees with the GitHub release asset metadata. An initial WebAssembly compiler
experiment was not used for the successful match.

## Remaining 29 routines: complete survey

`python3 tools/check_matching.py` compiles a separate target-layout candidate
for every remaining modeled routine. Source: `src/matching/routines.cpp`, with
`-c -lang c++ -proc gekko -O4,p -nodefaults -DTAK_FN=<address>`. All 29 compile
and all references resolve. **22 match exactly, covering 1,536 bytes.** With
the original setter, this initial group totals **23 routines / 1,548 bytes**.

The host callback models cannot be treated as target ABI source. The new
candidates use direct memory layouts and calls, and C++ virtual methods where
the assembly uses virtual dispatch. For example, `0x800E53CC` takes its value
in r4, consistent with an unused r3 object argument; its host model alone did
not preserve that argument position. Descriptive types remain provisional.

### Exact results

`0x80213584`, `0x801042FC`, `0x800CEB2C`, `0x80213140`, `0x802131A0`,
`0x801B8FD0`, `0x801C5944`, `0x801C59A4`, `0x801C5A04`, `0x801B90F4`,
`0x801B9190`, `0x801C5A64`, `0x8021311C`, `0x80213480`, `0x80213710`,
`0x80213744`, `0x800E53C4`, `0x800E53CC`, `0x8020F964`, `0x80213708`,
`0x80280928`, and `0x801B90D0`.

### Remaining differences

| Routine | Original / candidate bytes | Observed difference |
| --- | ---: | --- |
| `0x801B91FC` | 72 / 72 | Indexed field addressing and register allocation |
| `0x801B92FC` | 112 / 112 | Base/index registers and pointer-add ordering |
| `0x801C5BAC` | 136 / 136 | Saved-register assignment and call argument scheduling |
| `0x801C5C34` | 136 / 136 | Same issue as `0x801C5BAC` |
| `0x801B9244` | 184 / 184 | Byte-swap temporaries and register/addressing choices |
| `0x80211ED4` | 128 / 124 | Device-loop pointer/register setup |
| `0x80211F54` | 132 / 132 | Device-loop pointer/register allocation |

The November 13 pass matched `0x801B90D0` by expressing the cursor and remaining-size updates directly on the context fields. This preserved the original load/arithmetic/store scheduling without assembly or volatile accesses.

The seven routines above are failed byte comparisons, regardless of equivalent behavior or
equal code size. Trials with `-O4,s` and `-O3,p` did not match any additional
routines (14 and four matches respectively). This is not an exhaustive
compiler-version or flag search.

### Comparison method and evidence

`tools/ppc_matching.py` extracts the named ELF function using its symbol size,
excluding neighboring functions and section padding. It applies explicit
PPC `ADDR32`, `ADDR16_LO/HI/HA`, `REL24`, and `EMB_SDA21` relocations, then
compares every instruction byte with the SHA-256-verified original DOL.
No operand bytes are masked. Unknown relocations, missing symbol placements,
and out-of-range branches fail the check. Small-data bases r13=`0x80338280`
and r2=`0x8033B140` are checked against original startup instructions.
Original symbol addresses come from the indexed function table and DOL info;
address-named globals/callees retain their explicit target addresses.

The machine-readable snapshot is `analysis/matching-summary.json`.
Live evidence, including hashes, commands, relocation lists, original and
relocated candidate bytes, logs, and word differences, is generated under
ignored `build/matching/`. `--require-all` fails if any function differs;
the default reports differences without treating them as tool errors.

Eight synthetic ELF/relocation tests pass with:

```sh
python3 -m unittest discover -s tests -p test_ppc_matching.py
```

They cover function boundaries, signed branches, high-adjusted address carry,
small-data register selection, addends, and rejection of unresolved,
unsupported, out-of-range, or malformed inputs. The original setter's host
behavior and exact compiler comparison also still pass.

## Scope and next steps

CodeWarrior 1.3.2 is now supported by multiple nontrivial matches, but an exact
original compiler version and full-project flag configuration have not been
uniquely identified. These comparisons place individual functions at original
addresses; they do not verify exception tables, data sections, object-file
layout, or a complete linked executable. There is no runnable rebuilt game.

Next, refine the seven remaining initial candidates' layouts, expression forms, and
compiler settings. Establish an assembly-only linked baseline and verify its
DOL before integrating C/C++ replacements.

## Complete 1,000-function survey: November 13, 2026

All 970 additional semantic models have now been compiled as direct-memory,
target-argument candidates and compared against original function bytes.
The combined inventory is **255 exact matches / 1,000 checked routines**,
covering **6,088 original code bytes**. The other **745 differ**. Every routine
has a completed byte comparison; there are no compiler or relocation errors.

| Group | Checked | Exact matches | Matching bytes |
| --- | ---: | ---: | ---: |
| Original routines | 30 | 23 | 1,548 |
| Leaf helpers | 70 | 18 | 556 |
| Resource leaf helpers | 100 | 25 | 696 |
| Scalar helpers | 200 | 139 | 2,560 |
| Integer/control-flow helpers | 600 | 50 | 728 |
| Total | 1,000 | 255 | 6,088 |

Reproduce the entire survey and portable snapshot with:

```sh
python3 tools/check_all_matching.py --snapshot analysis/all-matching-summary.json
```

`tools/check_new_matching.py` reads the actual current semantic models. It
expands their function macros, substitutes direct byte/halfword/word accesses
for host callbacks, and supplies original integer inputs as PPC argument
positions. Harness-only output buffers and verification fuel are removed.
Routines classified as void use void candidates; unresolved return types
retain the model's final-r3 behavior. Constant offset-list loops are expanded
in their original store order, avoiding invented target-side constant tables.
The integer source is checked against its current recovery specifications.
Compilation uses GC 1.3.2 with `-lang c++ -proc gekko -O4,p -inline all -nodefaults`.
These are candidate adaptations, not a claim of original types or ABI recovery
for the 745 routines that still differ. Low-level control-flow models generally
need further restructuring before a compiler can reproduce the original code.

`build/new-matching/` retains each generated candidate, compiler log, ELF
object, relocated function bytes, original bytes, and full word differences.
`build/new-matching/report.json` records hashes and outcomes for all 970.
The original 29-function group retains its separate report and snapshot.

The all-inventory collector re-extracts and re-relocates every ELF function,
re-reads original words in address order, recomputes equality, checks
source/object/compiler hashes, rejects duplicate/missing entries, and requires
coverage of the complete semantic manifest. This also rechecks the 12-byte
setter. Use `--collect-only` to do that validation without recompiling.
`analysis/all-matching-summary.json` contains all 1,000 individual outcomes,
source hashes, group totals, and the verified DOL identity; it contains no
original instruction bytes. This remains a function-code matching survey,
not a linked executable rebuild or data/exception-table comparison.

Six additional candidate-generation tests cover callback removal, function
boundaries, fixed-list store order, rejected transformations, and encoding
original instruction values rather than their address keys:

```sh
python3 -m unittest discover -s tests -p test_new_matching.py
```

The eight relocation tests and the original setter's exhaustive host behavior
check also pass. Existing unrelated semantic and asset work is retained.

## Bounded improvement pass: 28 additional matches

A later pass retained every earlier match and added 28 functions / 508 bytes.
The original 1,000-routine survey now has **283 exact matches / 6,596 bytes**;
717 differ, with no unresolved comparisons. Together with the separately
verified 802 small routines, the overview totals **1,085 matches / 11,604 bytes**.
Of the expanded 7,160-model inventory, 1,802 have been surveyed and 5,358 have
not yet been surveyed. See `matching-overview.json` for the combined totals.

`matching-adaptations.json` explicitly selects the 28 verified source-level
adaptations: named global declarations enable the original small-data
addressing; a signed comparison replaces an equivalent unsigned sign-bit
comparison. No opcode substitution, operand masking, or host-model edits are
used. The target candidate preamble also accepts 64-bit integer helpers now
present in the shared recovery tooling. All generated candidate bytes are
still compared in full with the original function region.

Eight candidate-generation tests and eight relocation tests pass. Independent
object revalidation confirms that all 255 previous survey matches remain and
exactly 28 new matches were added. To reproduce the 970 newer candidate checks
and collect their results within the larger inventory:

```sh
python3 tools/check_new_matching.py
python3 tools/check_all_matching.py --collect-only --allow-partial --snapshot analysis/all-matching-summary.json
python3 tools/update_matching_overview.py
```

The collector rejects incomplete coverage by default. `--allow-partial` opts
into an explicitly counted subset and records the inventory total and the
number not yet surveyed; it does not turn missing comparisons into matches.

## Integer context survey: 198 additional routines

The November 14 pass surveys every model in `context_leaf_helpers.c` using
`python3 tools/check_new_matching.py --family context`. **33 / 198 match exactly,
covering 580 original bytes**; 165 differ. All candidates compile and every
relocation resolves. No error or missing comparison counts as a match.

The candidate interface places r3..r10 first, followed by all other modeled
integer context inputs as explicit C arguments. Those extra arguments are an
exploratory projection, not recovered original parameters. The candidate returns
r3, removes the host output array and verification budget, and replaces memory
callbacks with width-correct direct accesses. The generated source retains the
recovered control flow. Byte sign extension, signed shifts, and comparisons use
C casts/expressions expanded at their use sites to avoid out-of-line synthetic
helpers in the largest routine. Arguments to these expressions are side-effect-free
recovered register expressions. Other helper definitions remain inline C.

The generator rejects context source that no longer reproduces from its saved
specifications. Candidate, object, compiler and source hashes are recorded in
`build/context-matching/report.json`; complete original and candidate bytes,
word differences, and compiler logs stay local under the same directory.
The all-inventory collector independently extracts and relocates each function
again and rejects stale objects/candidates, mismatched saved results, duplicate
addresses, and incomplete comparisons. Run:

```sh
python3 tools/check_new_matching.py
python3 tools/check_new_matching.py --family context
python3 tools/check_all_matching.py --collect-only --allow-partial --snapshot analysis/all-matching-summary.json
python3 tools/update_matching_overview.py
python3 -m unittest discover -s tests -p test_new_matching.py
python3 -m unittest discover -s tests -p test_ppc_matching.py
```

Recompiling the earlier leaf family retains all 260 matches there and all 283
matches in the original 1,000-routine survey. The expanded survey has **316 /
1,198 exact matches / 7,176 bytes**, with 882 differences. Including the separate
802 small matches gives **1,118 exact matches / 12,184 bytes**, with 2,000 of
7,160 models surveyed and 5,160 unsurveyed. These remain individual function-code
matches; no executable has been linked or tested in-game.

Ten candidate tests and eight relocation tests pass. The added candidate tests
check explicit context-input mapping and run compiled boundary checks for sign
extension, every signed-shift count 0..31, and signed/unsigned comparisons.
The semantic inventory check still verifies 7,160 models / 1,158,944 original bytes.

## Integer caller baseline: 1,000 additional comparisons

The next November 14 pass adds `--family call` for every model in
`call_leaf_helpers.c`. All **1,000 compile and complete relocation and byte
comparison; none match**. Candidate generation first checks that the saved
call specifications reproduce the complete host source with
`render(..., full_context=True, allow_calls=True)`.

This is explicitly a candidate ABI hypothesis, not a behavior-preserving
lowering of the opaque-call models. A direct callee becomes an external C
function declared at its recovered address, taking eight integer arguments
(r3..r10) and returning r3. Computed callees use a function-pointer call with
the same signature. Other modeled context registers remain local values;
arbitrary callee writes to them are not represented. All 42 initial integer
inputs remain explicit as in the context survey. The full opaque host models
and their sources remain unchanged. Candidate interfaces are retained in the
portable aggregate report so this limitation travels with the results.

Every modeled stack frame remains explicit in the candidate, in addition to
whatever frame the C compiler generates. All 1,000 models contain r1-relative
operations. Of their candidates, **997 are larger, two have equal size, and
one is smaller** than the original. Original regions total **160,792 bytes**;
candidates total **355,696 bytes**. The median size ratio is approximately
**2.148**. All **4,522 applied relocations** are PPC relative branches. These
measurements describe this initial projection; they do not prove the causes
of every mismatch. Inspection of `0x8028D288`, for example, shows the compiler
frame surrounding the modeled frame and extra input loads.

Reproduce with:

```sh
python3 tools/check_new_matching.py --family call
python3 tools/check_all_matching.py --collect-only --allow-partial --snapshot analysis/all-matching-summary.json
python3 tools/update_matching_overview.py
```

Generated source, objects, complete original/candidate bytes, word differences,
and compiler logs remain local under `build/call-matching/`. The collector
independently extracts and relocates every function again, checking hashes and
saved results. The existing leaf and context surveys are recompiled as well.
The expanded aggregate covers **2,198 routines: 316 exact matches / 7,176 bytes,
1,882 differences, zero unresolved comparisons**. With the separate small-routine
survey, this is **3,000 distinct modeled functions surveyed**, **1,118 exact
matches / 12,184 original bytes**, and **4,160 not yet surveyed**. Existing
matches remain unchanged. No executable rebuild or in-game validation is added.

Twelve candidate tests and eight relocation tests pass. New tests cover direct
and computed destinations, rejected opaque-call syntax, and compiled host
execution that verifies all eight integer arguments and the callee result.
The semantic inventory still verifies 7,160 models / 1,158,944 original bytes.

Before broadening this caller projection, recover the real frame and callee
interfaces for a small representative group. Replacing modeled spills and
restores with compiler-managed locals, and establishing which values survive
each call, should produce more informative candidates than expanding this
unchanged projection into another caller batch.
