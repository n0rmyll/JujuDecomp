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

## Focused caller frame and interface recovery: 12 exact matches

A bounded follow-up replaces the register-context projection for twelve
48-byte caller wrappers with ordinary C++ interfaces. **All twelve match
exactly, adding 576 original bytes.** Two wrappers forward destination, fill
value, and size to separately inspected byte-fill implementations at
`0x80003488` and `0x8029DAD4`, then return the original destination. Ten load
an object pointer from a recovered field and call a recovered virtual slot.

The compiler now generates the 16-byte frames, link-register save/restore,
and (for the fill wrappers) r31 preservation. The source contains no explicit
stack pointer, LR, register context, assembly, opcode substitution, or masked
comparison. The virtual declarations account for CodeWarrior's two reserved
vtable words. Exact source types and meaningful return types for the virtual
wrappers remain provisional; matching their instruction bytes does not prove
those types or recover their callees.

`tools/caller_interfaces.py` recognizes only complete normalized executable
bodies with the expected frame, all argument/field operations, call target,
return address, and epilogue. Recognition is restricted to 48-byte regions.
A changed instruction statement, unknown fill target, unsupported virtual slot,
or different shape is excluded. The entire caller model source must still
reproduce from its specifications. The generated tracked C++ source must also
reproduce exactly unless `--write-source` is explicitly requested.

```sh
python3 tools/check_caller_interfaces.py --write-source
python3 tools/check_caller_interfaces.py
python3 tools/check_all_matching.py --collect-only --allow-partial --snapshot analysis/all-matching-summary.json
python3 tools/update_matching_overview.py
python3 -m unittest discover -s tests -p test_caller_interfaces.py
```

The checker compiles each candidate independently, verifies original words
against the local revision-checked DOL, applies all relocations, and compares
the complete function. Reports, candidate copies, objects, full byte streams,
word differences, hashes and compiler logs stay in `build/caller-interfaces/`.
The collector independently rechecks the original caller baseline objects
before rechecking the refined objects; it rejects duplicate refinements,
addresses outside the caller baseline, stale hashes, inconsistent saved
comparisons, and replacement of an existing match by a mismatch. Each refined
address replaces its earlier result rather than increasing the surveyed count.

The caller family now has **12 / 1,000 exact matches**, with 988 differences.
The aggregate survey has **328 / 2,198 exact matches / 7,752 bytes**, with
1,870 differences. With the separate 802 small routines, totals are **1,130
exact matches / 12,760 bytes**, **3,000 distinct functions surveyed**, and
**4,160 unsurveyed**. Every previous match is retained. No linked executable
or in-game test is added.

Five new tests cover complete-body recognition and rejection of every altered
executable statement, unknown fill targets, wrong region sizes, compiled
three-argument forwarding with destination preservation, and compiled virtual
slot dispatch. All five pass, along with the twelve existing candidate tests,
eight relocation tests, semantic inventory verification, and two consecutive
12-function target matching runs. Host dispatch uses host-aligned fields;
original target field offsets are verified by the exact PowerPC comparisons.

## Four more small caller shapes: 10 additional matches

The next focused pass adds **10 exact matches / 480 original bytes**, retaining
all twelve earlier caller matches. The interface checker now recognizes and
exactly matches **22 / 22 routines / 1,056 bytes**. The added shapes are:

| Shape | Matches | Recovered source behavior |
| --- | ---: | --- |
| Argument-swapping delegate | 4 | Load the object at offset `0x80`, pass the third argument second and the second argument third. |
| Nested-field guard | 2 | Load the object at `0x9c`, read an 8-bit or 32-bit field, call with the original object only when nonzero. |
| Byte-to-boolean result | 1 | Call the observed callee and normalize its low-byte result to false/true. |
| Flag-bit subobject guard | 3 | Test the high bit of the byte at `0x490`, call with the subobject at `0x3dc` when set. |

`extended_body` describes every normalized executable statement, including
call destinations and return addresses, conditional branch destinations,
load widths, offsets, argument ordering, and frame epilogues. Recovery accepts
a candidate only when its entire normalized body equals a supported template
and the indexed original region is 48 bytes. It does not remove arbitrary
spills, infer arbitrary callee effects, or relax byte comparisons.

For the flag guard, an unsigned-char bitfield with the active flag first
reproduces the original PowerPC rotate-and-mask extraction. A direct mask and
a right-shift expression were also probed locally but produced different
instructions. This establishes a matching source representation, not the
original declaration. Host bitfield layout is implementation-dependent; host
behavior tests set the named field, while the target layout and instruction
sequence are verified by full CodeWarrior-to-DOL equality.

The simple guarded-subobject routine at `0x800099CC` remains outside these
recognized shapes. Its straightforward C candidate combined the field load
and pointer adjustment into an update-form load and did not match. It is not
counted as an improvement. Exploratory probes remain local under `build/`.

Reproduce the focused survey and the independent aggregate comparison with:

```sh
python3 tools/check_caller_interfaces.py --write-source
python3 tools/check_caller_interfaces.py
python3 tools/check_all_matching.py --collect-only --allow-partial --snapshot analysis/all-matching-summary.json
python3 tools/update_matching_overview.py
python3 -m unittest discover -s tests -p test_caller_interfaces.py
```

All **nine** focused tests pass, including both paths for both nested guard
widths and the flag guard, actual object/argument forwarding for the swap,
all 256 byte values for the boolean result, and rejection after changing each
executable statement in representative bodies for all six supported shapes.
The twelve existing candidate tests, eight relocation tests, and semantic
inventory verification also pass.

The caller family now has **22 exact matches / 978 differences**. The combined
aggregate has **338 / 2,198 exact matches / 8,232 bytes**, with 1,860 differences
and no unresolved comparisons. With the 802 separately matched small routines,
totals are **1,140 exact matches / 13,240 original bytes**, **3,000 surveyed
models**, and **4,160 unsurveyed models**. This pass improves already surveyed
functions; it adds no regions to the surveyed count. Callee implementations,
full source types, executable linking, and in-game verification remain unresolved.

## November 20 parallel caller pass: 12 more matches

Two isolated matching workers add **12 exact matches / 608 original bytes**,
while a third establishes the independent executable relink foundation described
in [REBUILD_FOUNDATION.md](REBUILD_FOUNDATION.md). Matching totals still count
individual compiled functions; the original-object relink adds no source matches.

`tools/caller_patterns_next.py` recognizes seven complete 52-byte caller shapes
and matches **eight routines / 416 bytes**: two calls with the same object,
guarded byte clearing, post-call result storage, subobject-pointer initialization,
null-checked delegation, small-data sentinel update, and clearing a field before
calling a subobject. Repeated placeholders must agree throughout the body, and
call destinations, return addresses, branches and frame operations all have to
match the template. Its generated source is `src/matching/caller_patterns_next.cpp`.

`tools/caller_compiler_fixes.py` matches **four 48-byte routines / 192 bytes**:

| Address | Matching source representation |
| --- | --- |
| `0x800099CC` | A typed embedded subobject prevents the raw-pointer candidate's update-form load fusion. |
| `0x800C76F8` | A `switch` with case 2 retains the original two-branch layout. |
| `0x800718D4` | Swap two pointer arguments and append zero. |
| `0x8008A318` | Update two byte flags on the pointer returned by the callee. |

Its generated source is `src/matching/caller_compiler_fixes.cpp`. Both passes
use unchanged GC 1.3.2 `-O4,p`, compiler-managed frames, and ordinary C/C++.
Declarations and inferred types remain provisional. No assembly substitution,
operand masking, or edits to recovered host models are used.

```sh
python3 tools/caller_patterns_next.py
python3 tools/caller_compiler_fixes.py
python3 tools/check_all_matching.py --collect-only --allow-partial --snapshot analysis/all-matching-summary.json
python3 tools/update_matching_overview.py
```

Candidate objects and reports live separately under `build/agent-caller-patterns/`
and `build/agent-compiler-fixes/`. The all-inventory collector validates all
registered report DOL, source, compiler, runner, candidate and object identities;
it independently extracts and relocates the baseline and refined functions.
Overlapping worker results and addresses outside the caller baseline are rejected.
Every refinement requires a validated baseline, and an existing match cannot be
replaced by a mismatch. Dynamic source hashes include each registered report's
source inputs so both new source files remain covered by the portable snapshot.

Four focused pattern tests cover recognition/rejection and compiled behavior
for all seven shapes, including a callee changing the result destination before
the post-call load. Five compiler-fix tests cover full-body recognition and
compiled behavior for all four fixes. Eight integration tests cover disjoint
worker outputs, duplicate and unknown addresses, symbol/address disagreement,
replacement without double counting, missing baselines, and match-regression
rejection. The existing 29 matching tests and semantic inventory also pass.

All **1,140 previous exact matches are retained**. The caller family now has
**34 / 1,000 matches / 1,664 bytes**, with 966 differences. The aggregate survey
has **350 / 2,198 matches / 8,840 bytes**, with 1,848 differences. With the
802 separate small-routine matches, totals are **1,152 matches / 13,848 bytes**,
**3,000 distinct models surveyed**, and **4,160 unsurveyed**. No surveyed-region
count increases in this pass. No recovered-source executable or gameplay
validation is claimed.

## First source-integrated full executable link

`python3 tools/check_source_link.py` now places the already matched 12-byte
stop setter into the executable as compiled recovered C. It splits exactly
`0x8020F9C8..0x8020F9D4`, substitutes the compiled source object for the extracted
unit, and links it with 147 binary-derived fallback objects. All **3,113,248
DOL bytes compare equal** to the revision-checked original. This adds no new
function matches: the setter was already included in the **1,152 / 13,848-byte**
matching totals. Linked recovered-source coverage is now **one function / 12
original code bytes**, tracked separately from the function survey.

The unchanged `application_flag.c` is compiled as C with GC 1.3.2, `-O4,p`,
`-proc gekko`, and `-fp hardware`. A preprocessor definition maps its descriptive
name to the original `fn_8020F9C8` link symbol. The checker verifies its complete
function bytes, excludes the extracted target object from link inputs, checks
that only the compiled object defines the target globally, and checks the
linker's map for the original address and size in that compiled object.
It then compares every original and rebuilt DOL byte, including data and headers.

The former 146-object binary baseline becomes a 148-input source-integrated
link: the original containing object is split into a prefix, the source-sized
unit, and a suffix; only the source-sized unit is replaced. The first standalone
probe and the complete reproducible checker both passed. The seven focused
source-link tests and six original foundation tests pass. The checker also runs
the existing exhaustive flag behavior test. Original models, matching reports,
source bytes, and extracted binaries remain unchanged.

See [rebuild foundation](REBUILD_FOUNDATION.md#first-recovered-source-replacement)
for the command, exact ownership checks, audit outputs, and remaining scope.
No emulator boot or gameplay test has been performed.

## Manifest-driven second source replacement: global relocations

The source-integrated build now retains the stop setter and adds the already
matched level-name lookup at `0x801042FC` (28 bytes). The default manifest links
**two compiled source functions / 40 original code bytes** with **148 binary-derived
fallback objects**. All **3,113,248 DOL bytes remain equal** to the original.
No new individual match is counted: both functions were already included in
the 1,152-match / 13,848-byte survey.

`analysis/source-link-manifest.json` supplies source/unit identity, exact code
range, language, defines and expected relocation records. The checker derives
split ranges from this manifest, rejects overlaps/duplicates and unsupported
inputs, and substitutes every manifest object exactly once in DTK's ordered
unit list. The section template no longer duplicates function coordinates.

The lookup selects the existing C++ target-layout candidate in
`src/matching/routines.cpp` using `TAK_FN=0x801042FC`. The stop setter retains its
unchanged recovered C body. The lookup has two zero-addend relocations to
`lbl_802CD918`: HA at function offset 6 and LO at offset 10. The global table
remains binary-derived in `auto_07_802ADBA0_data.o`; its single provider and
`0x802CD918` map placement are checked. The compiled function's full relocated
code is compared, then the real executable linker independently resolves the
same external global, and the full output DOL is compared again.

The checker requires sole source ownership and original placement/size for both
functions, excludes both extracted target objects, verifies the exact relocation
contracts, and audits the manifest, source, tool and all actual input hashes.
Twelve source-link tests, six DOL layout/comparison tests, and eight PowerPC
relocation tests pass. Two complete two-source builds passed. No emulator or
gameplay test is claimed. See [rebuild foundation](REBUILD_FOUNDATION.md#manifest-driven-source-link)
for reproduction and the remaining direct-call milestone.

## Third source replacement: compiled application iteration calls compiled setter

The default source-link manifest now adds `fn_80213584`, the already matched
124-byte application iteration, while retaining the setter and level-name lookup.
The executable contains **three source functions / 164 original code bytes**
and **149 binary-derived fallback objects**. All **3,113,248 DOL bytes compare
exactly** to the original. Isolated function-matching totals remain unchanged.

The new source has three required relocation records: REL24 at offset 44 to
binary-derived `fn_80283F7C`; EMB_SDA21 at offset 48 to binary-derived
`lbl_803312F8`; and REL24 at offset 80 to source-owned `fn_8020F9C8`.
The checker verifies each provider and original map address. In particular,
the stop target is owned solely by `compiled_application_flag.o`, so this is
now a compiled-source-to-compiled-source call within the full executable link.

The first link with default C++ exception settings failed the full DOL/layout
comparison despite exact instruction bytes. CodeWarrior emitted additional
unwind and exception-index records. The explicit per-unit manifest option
`cpp_exceptions: false` removes those records without changing any of the 124
code bytes or relocation records. No post-link patching or masked
comparison is used. This illustrates why isolated code matching does not
establish complete object or executable compatibility.

Fifteen source-link tests, six DOL layout/comparison tests, and eight relocation
tests pass, along with the setter's exhaustive host behavior check. The
corrected full executable link passes. Source types and larger subsystem
semantics remain provisional; emulator execution is still untested. Reproduce
with `python3 tools/check_source_link.py`; see
[rebuild foundation](REBUILD_FOUNDATION.md#direct-call-and-small-data-integration).
