# Third thousand: compositional integer caller models

This batch adds **1,000 indexed caller-body models**, covering **160,792
original bytes and 40,198 instructions**. The complete inventory reaches
**3,000 routine models covering 275,928 original text bytes**: 31.033% of
the provisional 9,667 indexed regions and 10.042% of DOL text bytes.

The new entries are **compositional low-level integer models**: every supported
instruction in the caller's indexed region is represented, while external
calls are explicit opaque boundaries. They are not recovered callee
implementations, original typed source, original ABI replacements, or new
compiler matches. This distinction is recorded on each inventory entry.

## What this batch adds

Unlike the preceding batch of small stubs, the selected callers are at least
48 bytes, have direct or indirect calls, and were selected from regions no
larger than 1,024 bytes. Their addresses run through the game and SDK/runtime
code; original symbols and addresses are retained in the specifications.
No empty/constant-return methods were added in this batch.

The recovery now supports:

- Direct external `bl` calls, recording the exact target and return address.
- Calls through CTR (`bctrl`) and LR (`blrl`), capturing the target before
  updating LR with the continuation address.
- External non-linking tail branches, which hand off without resuming the
  current caller body.
- Caller continuation with the callee's updated integer context and target
  memory, including branch decisions based on those effects.

Internal linked branches, unsupported instructions, indirect jump-table
dispatch and transfers not covered by these boundaries remain rejected.
Only fully represented caller regions enter the inventory. Callees are not
added to the count merely because they are referenced.

`src/recovered/call_leaf_helpers.c` contains separate native C functions with
explicit C control flow and integer context storage. It contains no embedded
original instruction bytes, opcode-dispatch interpreter or inline assembly.
`call_context.h` defines the synchronous external-call interface. Context
pointers are valid during the callback; callbacks provide callee effects on
the modeled integer state and shared target memory.

`call-helper-specs.json` stores each full caller body and its external call
sites. There are **3,596 static external-call sites** across the selected
routines. Some have direct resolved addresses; others retain dynamic target
expressions. Their runtime targets, signatures and implementations are not
established by this batch.

## Verification scope

`tools/check_call_helpers.py` validates the original executable SHA-256 and
all **40,198 original instruction words**, compiles the recovered native C,
and compares it with the independent machine-word runner. Both executions
use the same deliberately controlled external-callee test contracts.

The accepted group passes **64,103 terminating comparisons**, at least 64
per routine. **Every selected routine exercises at least one external call
boundary**. Additional cases are retained when needed to reach such a boundary;
routines without a reached boundary or enough terminating cases are excluded.
The selected final source/specification set is then compiled and checked again.

Each comparison checks:

- All 42 modeled integer-context words: GPR0..31, LR, CTR and the LT/GT/EQ
  bits of eight comparison fields.
- Target memory reads/writes: widths, addresses, values, ordering and final
  synthetic memory.
- External-call order and target, the complete pre-call context, the
  continuation address, and subsequent caller execution after callback effects.

The runs record **182,304 synthetic opaque-call events**. Test contracts return
zero, one, a synthetic object pointer or a small scalar. One contract also
changes a bounded object field to exercise caller reloads after external
effects. They preserve the stack/base/nonvolatile registers and LR and vary
selected result/temporary/comparison fields. **These are test doubles, not
implementations of the actual game or SDK callees.**

The successful cases exercise **35,595 of 40,198 caller instructions (88.549%)**.
All instructions execute in 782 of the 1,000 models. **4,603 instructions are
unexercised** by these scenarios and are listed by address in the summary.
Not every call site or branch is covered.

There are **2,559 budget-exceeded attempted cases** among the selected routines.
They do not count as successful comparisons. The budget is 2,048 caller
instructions per attempt; callee test contracts are outside that caller-step
count. C exhaustion for an original caller that terminates is a failure.

This is compositional evidence for caller translation under supplied external
contracts. It does **not** verify real callee behavior, valid GameCube memory
mapping, real gameplay results, FPU/XER state, exceptions, nonlocal exits,
devices, threading, caches or timing. The integer context does not recover
original argument/return types, including potential floating-point ABI effects.
Finite comparisons are not a proof over all possible states or callees.

## Reproduce

```sh
python3 tools/recover_call_helpers.py
python3 tools/check_call_helpers.py
python3 -m unittest discover -s tests -p test_ppc_leaf.py
python3 -m unittest discover -s tests -p test_integer_recovery.py
python3 tools/check_integer_helpers.py
python3 tools/check_context_helpers.py
python3 tools/check_semantic_progress.py
python3 tools/update_matching_overview.py
```

The recovery command re-derives all selected bodies and call targets from
verified local disassembly and checks the saved source/specifications. Add
`--write` to regenerate those files. Test instrumentation bounds execution;
it is disabled in a normal native C build.

The 27 oracle unit tests include direct-call LR updates, CTR/LR indirect
target capture, return continuation and tail-call handoff. Eleven recovery
tests include preservation of memory callback syntax and explicit call
boundaries. Earlier 600- and 198-model batches are regression checked because
the shared recovery and instruction runner changed.

## Accounting

`semantic-functions.json` marks these entries as compositional integer caller
bodies with opaque external callees, not whole-program semantic recovery.
`call-helpers-summary.json` records accepted cases, observed calls, coverage,
budget exclusions and source/specification hashes. The inventory checker
verifies 3,000 unique, non-overlapping indexed regions and source definitions.
Partial routines and the offline world-record reader stay excluded.

No new compiler matches are claimed: the combined matching inventory remains
**1,057 exact function-code matches / 11,096 original bytes**. Only 1,802 of
the now 3,000 models have been compiler-surveyed; 1,198 have not. No linked
game executable or native playable source port is produced.
