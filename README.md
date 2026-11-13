# JujuDecomp

An early reverse-engineering workspace for **Tak and the Power of Juju (USA)** on GameCube, disc ID **GJUE78**, revision 0. Includes analysis tools, research notes, thirty complete routine models, two partial routine models, and a portable world-record reader in C.

**This is not a completed decompilation or a native source port.** There is no build system that recreates the original game executable yet. The recovered C files are research models; separate target-layout candidates now establish 22 exact function-code matches, but none are integrated into a rebuilt executable. Tak boot, gameplay, audio, performance, and saves have not yet been verified in this workspace.

No game image, extracted executable, game assets, or generated disassembly is included. Supply your own legally obtained copy of the game. Keep game files local; the ignore rules exclude disc images, extracted binaries, saves, and build outputs.

## Progress statistics

Snapshot: **November 12, 2026**, GJUE78 revision 0. These measure separate stages; they are not an overall completion percentage.

| Area | Current / measured total | Progress | Meaning |
| --- | ---: | ---: | --- |
| Game functions compiled and verified as matching | 22 / 9,667 indexed function regions | **0.228%** | The stop-request setter plus 21 target-layout candidates match with CodeWarrior GC 1.3.2 after resolving relocations at original addresses. Eight further candidates differ. No linked executable rebuild. |
| Original code bytes verified as matching | 1,512 / 2,747,776 DOL text-section bytes | **0.055%** | Complete instruction bytes of 22 functions, including resolved call/global operands. No masking or assembly substitution. |
| Game functions modeled in semantic C | 30 / 9,667 indexed function regions | **0.310%** | Thirty complete routines represented in nine C files; two additional C files contain partial DBU/world-volume models and an offline record reader, excluded from this count. Callbacks and host layouts may replace original mechanisms. |
| Original code bytes covered by those models | 2,448 / 2,747,776 DOL text-section bytes | **0.089%** | Size of the thirty fully modeled original routines; excludes partial DBU/world-volume models, the offline reader, and generated C/object size. This is semantic coverage; verified matching bytes are measured separately. |
| Extracted resource files inventoried | 1,163 / 1,163 locally extracted files | **100%** | File paths, sizes, and hashes recorded for the local `files/data_gcn` extraction; not proof of complete disc coverage. |
| Resource files with texture exports | 39 / 1,163 extracted files | **3.35%** | Base texture levels exported from 21 DBU and 18 DBL files; this is partial resource decoding, not complete conversion of those files. |
| Texture records exported as PNG | 5,512 / 5,527 encountered records | **99.73%** | Includes repeated textures across archives; 15 records have null pixel offsets. Mipmaps and animated frames are not supported. |
| DBU/DBL files scanned for binary chunk boundaries | 39 / 39 extracted DBU/DBL files | **100%** | Chunk parser reached exact EOF in all 21 DBU and 18 DBL files; payload types remain only partly decoded. |
| DBU bundles with text manifests inspected | 2 / 21 extracted DBU bundles | **9.52%** | Preload and Hub: 41 and 91 listed source entries. Binary chunk boundaries and some payload layouts are now documented; most resource semantics remain unresolved. |
| Spatial audio/reverb volume records exported | 10 records / 2 sampled DBU bundles | — | Eight records from Hub and two from Burial, each 192 bytes; field interpretation is provisional and the total across all archives is unknown. |

The asset inventory totals **1,447,253,921 bytes** (about **1.35 GiB**):

| Resource extension | Files | Share of extracted files |
| --- | ---: | ---: |
| `.dsp` | 1,005 | 86.41% |
| `.dba` | 39 | 3.35% |
| `.bik` | 33 | 2.84% |
| `.cut` | 27 | 2.32% |
| `.dbu` | 21 | 1.81% |
| `.adp` | 19 | 1.63% |
| `.dbl` | 18 | 1.55% |
| `.fnt` | 1 | 0.09% |

File shares are by count, not bytes, and are rounded. Bundles may contain many internal resources, whose total is unknown; the texture-record percentage covers only records encountered by the current decoder. No overall model/texture/animation completion percentage is available yet.

Matching results are recorded in [binary matching findings](analysis/BINARY_MATCHING.md) and [the 29-function snapshot](analysis/matching-summary.json). The function denominator comes from `analysis/index-summary.json` and is provisional: automatic regions include SDK/runtime code and may not map one-to-one to original source functions. The thirty fully modeled routines are `0x8020F9C8`, `0x80213584`, `0x801042FC`, `0x800CEB2C`, `0x80213140`, `0x802131A0`, `0x801B91FC`, `0x801B92FC`, `0x801B8FD0`, `0x801C5944`, `0x801C59A4`, `0x801C5A04`, `0x801C5BAC`, `0x801C5C34`, `0x801B90D0`, `0x801B90F4`, `0x801B9190`, `0x801B9244`, `0x801C5A64`, `0x8021311C`, `0x80213480`, `0x80213710`, `0x80213744`, `0x800E53C4`, `0x800E53CC`, `0x80211ED4`, `0x80211F54`, `0x8020F964`, `0x80213708`, and `0x80280928`. The partial models cover only `0x801B8F24..0x801B8F5C` within `0x801B8E60` and the scalar flag-bit operation within `0x8027F680`; both are excluded from the routine and byte totals, along with the offline world-record reader. Recalculate their original sizes using the ignored `analysis/functions.csv` after running `tools/index_dol.py`; text-section sizes come from the index summary. Asset counts come from the ignored `assets/manifest.json`, regenerated with `python3 tools/extract_assets.py --inventory-only`. Texture export counts come from the ignored `assets/textures/manifest.json`, regenerated with `python3 tools/decode_textures.py`; see [texture format findings](analysis/TEXTURE_EXTRACTION.md) for limits. World-volume counts come from `analysis/hub-world-volumes.json` and `analysis/burial-world-volumes.json`; see [world-volume findings](analysis/WORLD_VOLUMES.md) for decoder commands and limits. These numbers are a manual snapshot and should be refreshed when recovery advances.

## Get the source

```sh
git clone https://github.com/n0rmyll/JujuDecomp.git
cd JujuDecomp
```

## Testing with your own emulator

Use your own GameCube emulator and legally obtained game image to test the original game's behavior. This repository does not include an emulator or a runnable game build; the recovered C files are research models and cannot yet be tested as a rebuilt game.

## Reproduce the executable analysis

Requires Python 3 and [decomp-toolkit v1.8.4](https://github.com/encounter/decomp-toolkit/releases/tag/v1.8.4). Download the appropriate `dtk` release for your OS and place it at `tools/dtk` (or use `tools/dtk.exe` on Windows and adjust the commands). The original local tool was the Intel macOS release; Apple Silicon may require Rosetta. On macOS/Linux, make it executable with `chmod +x tools/dtk`.

Place your GJUE78 revision 0 image in the root, then run from the root (replace the image filename if needed):

```sh
mkdir -p analysis
tools/dtk vfs cp 'Tak and the Power of Juju (USA).rvz:sys/main.dol' analysis/main.dol
tools/dtk dol info analysis/main.dol > analysis/dol-info.txt
tools/dtk dol split analysis/config.yml analysis/split
python3 tools/index_dol.py
python3 tools/verify_application_map.py
```

The expected executable SHA-256 is `49faf28a7d2e25422c145754ef41b0c8a8dfcd83e688db1c39ecf21f6e34b706`. The dispatch verifier rejects a different executable revision. Indexing regenerates the ignored function, call, and string CSVs from your local executable and disassembly. Extracted code and data remain local.

The latest recovered batch and its checks are documented in [runtime helper findings](analysis/RUNTIME_HELPERS.md).

Read [decompilation notes](analysis/DECOMP_NOTES.md) and [application dispatch findings](analysis/APPLICATION_DISPATCH.md) for current evidence and limitations. `src/recovered/` contains semantic reconstructions; original compiler identification, broader binary matching, asset decoding, and platform replacement work remain before a game source build is possible.

## Extract local assets

With `tools/dtk` installed and your disc image available, run:

```sh
python3 tools/extract_assets.py 'Tak and the Power of Juju (USA).rvz'
```

This recursively copies `files/data_gcn` into ignored `assets/disc/` and writes
`assets/manifest.json` with file sizes, SHA-256 hashes, and the first 16 bytes
of each file. Rebuild the inventory without extracting again with
`python3 tools/extract_assets.py --inventory-only`.

The local revision 0 extraction contains 1,163 files (1,447,253,921 bytes):
21 `.dbu` bundles, 18 `.dbl` files, 27 `.cut` files, 39 `.dba` files,
1,005 `.dsp` files, 19 `.adp` files, 33 `.bik` movies, and one `.fnt` file.
These are original resource files. To export the base texture levels as PNGs:

```sh
python3 tools/decode_textures.py
python3 -m unittest discover -s tests -p test_decode_textures.py
```

The decoder needs only Python's standard library. Open `assets/textures/index.html`
for a searchable local gallery. `assets/textures/manifest.json` records names,
archive hashes, source offsets, formats, and unresolved records. The first full
pass exported 5,512 PNGs from 39 DBU/DBL files; 15 records had null pixel offsets
and were reported as errors (the command exits nonzero when records cannot be
exported). Repeated textures across levels are retained. Mipmaps, animated
texture frames, models, and audio conversion are not yet supported. See
[texture format findings](analysis/TEXTURE_EXTRACTION.md) for evidence and limits.

## Check the first recovered function

From the repository root, run:

```sh
python3 tools/check_application_flag.py
```

This compiles and runs a host behavior test for `application_flag.c`, checking
all 256 prior flag values, neighboring bytes, and repeated calls. It also checks
the local original DOL's SHA-256 and the three original instructions (12 bytes).
Requires Python 3, Clang, and the extracted `analysis/main.dol`. Outputs go under
ignored `build/application-flag/`. A missing or wrong DOL fails the check.

The first exact PowerPC match is reproducible with locally installed, pinned
CodeWarrior GC 1.3.2 and wibo 1.2.0 (Intel macOS or x86-64 Linux):

```sh
python3 tools/setup_matching.py
python3 tools/check_application_flag.py --mw-cc tools/mwcc/GC/1.3.2/mwcceppc.exe --runner tools/wibo
```

Setup downloads tools into ignored paths, checks SHA-256 hashes, and makes no
system-wide changes. Use `--archive /path/to/compilers_20251015.zip` to supply
an existing archive. The checker runs the host behavior test, verifies the DOL
revision, compiles the actual recovered source, rejects text relocations, and
compares its entire `.text` with the original 12 bytes. A successful comparison
writes `build/application-flag/match.json` with source, compiler, and object
hashes plus the compilation command. A new run clears any previous report.

A Clang with a PowerPC backend can alternatively be tested with
`--ppc-cc /path/to/clang`; Apple Clang lacks that backend. Only the CodeWarrior
command above has been verified as matching here. This single-function match
does not identify the original compiler version/flags, prove broader ABI
compatibility, or establish a complete executable rebuild. See
[binary matching findings](analysis/BINARY_MATCHING.md) for evidence and next steps.

## Check the other 29 modeled routines

```sh
python3 tools/check_matching.py
python3 -m unittest discover -s tests -p test_ppc_matching.py
```

This compiles `src/matching/routines.cpp` separately for each target routine,
using original field offsets, direct calls, globals, and C++ virtual dispatch
in place of the host models' callbacks. With GC 1.3.2 and `-O4,p`, **21 of 29**
match exactly; eight differ. The earlier stop setter brings the total to
**22 of 30 modeled routines / 1,512 bytes**. The host models remain available
for behavior research.

`build/matching/report.json` records every result, compiler/source hashes,
commands, and applied relocations. Per-function `.diff.txt` files show all
word differences; binaries and compiler logs stay under ignored `build/`.
The checker resolves supported PPC relocations at original addresses and
compares every byte, including branch/global operands. Unsupported or
unresolved relocations fail. Add `--require-all` to also exit nonzero for
byte differences; the default completes the survey and reports mismatches.
Use `--function 0x801B91FC --output build/matching-one` for an isolated check.

## Attribution

Commercial game code and assets are not supplied or licensed by this repository.
