# Binary matching: GJUE78 revision 0

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
and all references resolve. **21 match exactly, covering 1,500 bytes.** With
the original setter, the current total is **22 routines / 1,512 bytes**.

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
and `0x80280928`.

### Remaining differences

| Routine | Original / candidate bytes | Observed difference |
| --- | ---: | --- |
| `0x801B91FC` | 72 / 72 | Indexed field addressing and register allocation |
| `0x801B92FC` | 112 / 112 | Base/index registers and pointer-add ordering |
| `0x801C5BAC` | 136 / 136 | Saved-register assignment and call argument scheduling |
| `0x801C5C34` | 136 / 136 | Same issue as `0x801C5BAC` |
| `0x801B90D0` | 36 / 36 | Cursor/remaining load, arithmetic, and store scheduling |
| `0x801B9244` | 184 / 184 | Byte-swap temporaries and register/addressing choices |
| `0x80211ED4` | 128 / 124 | Device-loop pointer/register setup |
| `0x80211F54` | 132 / 132 | Device-loop pointer/register allocation |

These are failed byte comparisons, regardless of equivalent behavior or
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

Next, refine the eight remaining candidates' layouts, expression forms, and
compiler settings. Establish an assembly-only linked baseline and verify its
DOL before integrating C/C++ replacements.
