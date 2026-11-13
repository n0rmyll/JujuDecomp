# GJUE78 revision 0: initial reverse-engineering findings

## Identity and reproducibility

`main.dol` SHA-256: `49faf28a7d2e25422c145754ef41b0c8a8dfcd83e688db1c39ecf21f6e34b706`.
decomp-toolkit v1.8.4 generated the split assembly and objects. Run
`python3 tools/index_dol.py` from any working directory to regenerate the
addressed string table, function index, and direct/indirect call-site index.

The current automatic split contains 9,667 function regions, 33,431 direct
call sites, 7,105 indirect call sites, and 5,102 printable NUL-terminated
strings. These are provisional analysis counts, not decompilation progress.
Disassembly and relocatable objects do not constitute recovered C/C++ or a
verified rebuild. Tail calls and arbitrary computed dispatch are not covered
by the call-site index.

## Startup and application loop

Verified in `split/asm/auto_00_80003100_init.s`:

- `__start`, `0x80003154`, initializes registers, hardware, and data.
- It calls `DBInit`, `OSInit`, and `__init_user`.
- The branch at `0x800032A8` calls `main`, `0x8020F7E0`.

Verified in `split/asm/auto_03_8020C094_text.s`:

- `main`, `0x8020F7E0..0x8020F954`, loads the application pointer from
  `0x803320E0`. Its initial value in the DOL is `0x803276F8`, in BSS.
- Calls `fn_8020F9D4(application, argc, argv)`. That function begins with
  `OSInit`, `DVDInit`, and further platform initialization calls.
- Computes a buffer size from arguments 1 through argc-1, logs arguments,
  allocates storage through `fn_80206370`, and builds a space-separated
  command line. `fn_80295904` is inferred to be concatenation from this usage;
  its implementation still needs verification.
- At `0x8020F8F4`, calls the application vtable entry at byte offset `0x0C`
  with the command-line buffer, then releases that buffer through
  `0x802064EC` (deallocation is inferred from usage).
- Checks application byte `+0x04`; while zero, calls the vtable entry at
  `+0x14` (`0x8020F914`). This is the top-level iteration loop; exactly how
  it schedules frames remains to be traced.
- Calls vtable entry `+0x10` at `0x8020F934`, then returns zero.

Conceptual control flow (descriptive names, not original symbols):

```text
platform_setup(application, argc, argv)
command_line = join_arguments_with_spaces(argv[1:argc])
application.virtual_slot_0C(command_line)
release(command_line)
while application.byte_04 == 0:
    application.virtual_slot_14()
application.virtual_slot_10()
return 0
```

`fn_8020F9C8` stores 1 into application byte `+0x04` and returns.
`src/recovered/application_flag.c` is the first small semantic C
reconstruction, with provenance. It passes the host Clang syntax check;
it now has an exact 12-byte CodeWarrior GC 1.3.2 object-code match, but is not
integrated into the original executable. See `BINARY_MATCHING.md`.

The actual derived application vtable must be recovered from static
initialization before naming its methods. The nearby base-class vtable at
`0x802EF19C` has stub methods and must not be mistaken for the live game loop.

## Toolchain and asset clues

The executable contains `Metrowerks CW runtime library initializing default
heap` and the Metrowerks PowerPC resident-kernel string. This supports a
CodeWarrior-family toolchain inference; the exact compiler version and flags
remain unknown. Embedded Nintendo SDK release dates describe SDK components,
not the final game's build date.

The extracted `copydata.bat` is evidence of a developer asset-copy pipeline:

- Source workspace: `d:\dev\bigjuju`.
- Levels: `data_gcn/*.dbu`.
- Shared cutscene source: `data/cutscene/*.cut`.
- Other resources: `.dbl`, `.fnt`, `.bik`, `.adp`, `.dsp`, `.dba`.

The script is reference data only; do not execute it. No format decoder has
yet been recovered, and filename extensions alone do not establish layouts.

## External reference

[Cwf1997/takandthepowerofjuju](https://github.com/Cwf1997/takandthepowerofjuju)
describes a work-in-progress PS2 matching decompilation. It is not a matching
GameCube source tree; platform addresses and binaries cannot be reused
directly. No source from that repository has been imported.

## Next concrete milestone

### Recovered DBU payload dispatch

`src/recovered/dbu_payload_dispatch.c` models the complete 68-byte routine
at **0x801B8FD0**. It reads the u16 at **0x80322E4E**, then the u32 at
**0x80322E50**, and passes the latter to **0x801B9014** when flag bit zero
is set, otherwise to **0x801B90D0**. Both handler names remain address-based;
this recovery does not claim to recover their implementations.

`python3 tools/function_report.py fn_801B8FD0` verified all 17 instructions
against the local executable. The host behavior test covers all 65,536
flag values and four argument bit patterns, checking the read addresses,
read order, selected handler, argument, and exactly one call:

```sh
clang -std=c11 -Wall -Wextra -Werror -O2 src/recovered/dbu_payload_dispatch.c tests/dbu_payload_dispatch.c -o /tmp/tak-dbu-payload-dispatch-test
/tmp/tak-dbu-payload-dispatch-test
```

This is a semantic reconstruction using callbacks, not a PowerPC binary match.

Update: the constructor and live tables have now been traced. See
`APPLICATION_DISPATCH.md` and `application-map.json` for the recovered
application iteration and active-state dispatch. The following was the
initial investigation plan:

Trace constructors that initialize the BSS application at `0x803276F8`,
recover its live vtable, and follow slot `+0x14` into update/render work.
In parallel, identify disc reads and the DBU/DBL loaders from addressed
strings and call sites. Only assign semantic names when supported by the
instructions. A matching rebuild requires identifying the original compiler,
assembling/linking the split with suitable tools, and comparing the complete
output against the original before replacing functions incrementally.

The user reports that the RVZ reaches the title screen and works in an
emulator. Use your own emulator for future behavioral comparisons; this does
not validate any recovered source yet.
