# State identities and frame phases: GJUE78 revision 0

Further progress: `LEVEL_LOADING.md` documents the descriptor table, DBU
loading path, and working text-manifest inspection on two real archives.

## Evidence now stronger than size-based guesses

The 0x32A0 state initializes particle libraries
`particles\\jujuParticles.dbl`, `particles\\jujuWaterParticles.dbl`,
`fonts\\karavan`, `tables\\SurfSurf.tbd`, `shell\\frontend.dbl`, and
`shell\\gadgets.dbl`. Its iteration method references `phase`, `plant`,
`yorbel`, and `moonstone`, and calls a broad group of game systems. This
supports a gameplay/world-state interpretation, with frontend/UI also
managed inside it. It does not establish that the class excludes menus.

The 0xEA4 state helper at **0x800CE6BC** passes address **0x802C48B8**
to an embedded object's virtual method. The text begins with the copyright
notice for Avalanche, Nickelodeon, and THQ. Together with its font setup
and default startup creation, this supports a **legal/startup-screen state**
label. Its exact visible sequence and timing still require a runtime trace.

The 0x452C0 state has an embedded polymorphic object at +0x0C, invokes it
during initialization and iteration, and returns code 4 on completion.
Its role remains unknown; do not call it a title screen or movie player yet.

## Startup result selection reconstructed

`src/recovered/startup_state_finish.c` models **0x800CEB2C**:

1. Call cleanup `0x80260A80`.
2. Read the selection word at **0x802F58A4**.
3. If -1: set it to 0x37 and return 1 (transition recreates the 0xEA4 state).
4. If 0x37: set game field +0xEC to 1 and return 2 (creates the 0x452C0 state).
5. Otherwise return 3.

This is a semantic host reconstruction with injected globals/callbacks,
not a matching PPC function. Return-code meanings follow the already
verified branches in `0x800E4608`; no original enum names are known.

## Profiler names give useful phase boundaries

Initializer **0x80100E54** registers these IDs through **0x80208D04**:

| ID | String address | Embedded name |
| --- | --- | --- |
| 0x22 | 0x802D2668 | Game logic |
| 0x23 | 0x802D2674 | Engine advance |
| 0x24 | 0x802D2684 | Render manager |
| 0x25 | 0x802D2694 | Env. actor init |
| 0x26 | 0x802D26A4 | Water init |

The caller passes ID/name pairs. The profiler interpretation of register,
begin `0x80208DF0`, and end `0x80208F0C` is supported by their paired usage
and labels; their complete implementations have not been reconstructed.

Within **0x80101E6C**:

- **0x80101EC8** begins 0x22. The broad body handles timing, subsystem
  methods, world-related state and UI. Exact subsystem roles remain mixed.
- **0x80102644** begins nested 0x23; **0x80102648** calls
  **0x801F3070**; **0x80102650** ends 0x23.
- **0x80102684** begins nested 0x24; **0x80102688** calls
  **0x801D8CA8**; **0x80102690** ends 0x24.
- **0x80102698** ends 0x22. Additional post-phase logic follows.

Thus `Game logic` includes both engine advance and rendering in this
profiling scheme. It must not be treated as a pure simulation function.
These are static instruction boundaries, not measured execution durations.

`0x801F3070` is a short orchestration function calling, in order:
`0x802087C0`, `0x801C6F70`, `0x801CA1E0`, `0x801E09FC`,
`0x801CF1B8`, `0x801C8650`, and `0x8018BD00`.
Their simulation/animation/audio roles still need independent evidence.

The separate render-manager phase reaches the previously verified graphics
FIFO path through `0x801D8CA8 -> 0x801877A4 -> 0x80130478`.

## Repeatable evidence extraction

`tools/function_report.py` exports one function's assembly and a JSON report
under `analysis/reports/`. It verifies every parsed instruction against the
hash-identified original DOL, lists direct call sites, and annotates printable
strings referenced by direct operands or analyst-supplied register bases.

```sh
python3 tools/function_report.py fn_80100E54 --base r30=0x802d2580
python3 tools/function_report.py fn_80101E6C
python3 tools/function_report.py fn_800CE6BC
python3 tools/function_report.py fn_800CEB2C
python3 tools/function_report.py fn_800CEDD8
python3 tools/function_report.py fn_801F3070
```

The supplied r30 base is established by instructions at 0x80100E74 and
0x80100E80. The report does not perform control-flow/data-flow analysis;
annotations are navigation aids requiring instruction review. A readable
operand may be a load from string bytes rather than a string argument.
Strings use Latin-1 so the copyright symbol is retained.

Checks: 1,616 instructions across the six functions above were compared
against original bytes. The host C reconstruction passes strict Clang
syntax checks. There is still no matching compiler build or runtime patch.

## Next investigation

Trace the 0x452C0 state's embedded virtual methods to identify its resource
loader and role. Follow the gameplay state's initialization helpers that
load levels and its engine-advance callees, then recover an independently
testable parser or simulation utility rather than labeling broad routines
from their position alone. Runtime state tracing will still be needed to
confirm title-to-gameplay behavior.
