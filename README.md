# JujuDecomp

An early reverse-engineering workspace for **Tak and the Power of Juju (USA)** on GameCube, disc ID **GJUE78**, revision 0. Includes analysis tools, research notes, 1,000 complete routine models (including generated low-level integer C), two partial routine models, and a portable world-record reader in C.

**This is not a completed decompilation or a native source port.** There is no build system that recreates the original game executable yet. The recovered C files are research models; separate target-layout candidates now establish 255 exact function-code matches, but none are integrated into a rebuilt executable. Tak boot, gameplay, audio, performance, and saves have not yet been verified in this workspace.

No game image, extracted executable, game assets, or generated disassembly is included. Supply your own legally obtained copy of the game. Keep game files local; the ignore rules exclude disc images, extracted binaries, saves, and build outputs.

## Progress statistics

Snapshot: **November 13, 2026**, GJUE78 revision 0. These measure separate stages; they are not an overall completion percentage.

| Area | Current / measured total | Progress | Meaning |
| --- | ---: | ---: | --- |
| Game functions compiled and verified as matching | 255 / 9,667 indexed function regions | **2.638%** | All 1,000 modeled routines checked: 255 exact matches and 745 byte differences with CodeWarrior GC 1.3.2. Relocations resolved at original addresses; no linked executable rebuild. |
| Original code bytes verified as matching | 6,088 / 2,747,776 DOL text-section bytes | **0.222%** | Complete instruction bytes of 255 functions, including resolved call/global operands. No masking or assembly substitution. |
| Indexed functions modeled in C | 1,000 / 9,667 indexed function regions | **10.344%** | 1,000 complete routine models in thirteen C files, including game and SDK/runtime code; the latest 600 are generated low-level integer control-flow models. Two additional C files contain partial DBU/world-volume models and an offline record reader, excluded from this count. Callbacks and host layouts may replace original mechanisms. |
| Original code bytes covered by those models | 69,852 / 2,747,776 DOL text-section bytes | **2.542%** | Size of the 1,000 fully modeled indexed routines; excludes partial DBU/world-volume models, the offline reader, and generated C/object size. This is semantic coverage; verified matching bytes are measured separately. |
| Extracted resource files inventoried | 1,163 / 1,163 locally extracted files | **100%** | File paths, sizes, and hashes recorded for the local `files/data_gcn` extraction; not proof of complete disc coverage. |
| Resource files with texture exports | 39 / 1,163 extracted files | **3.35%** | Base texture levels exported from 21 DBU and 18 DBL files; this is partial resource decoding, not complete conversion of those files. |
| Texture records exported as PNG | 5,512 / 5,527 encountered records | **99.73%** | Includes repeated textures across archives; 15 records have null pixel offsets. Mipmaps and animated frames are not supported. |
| DBU/DBL files scanned for binary chunk boundaries | 39 / 39 extracted DBU/DBL files | **100%** | Chunk parser reached exact EOF in all 21 DBU and 18 DBL files; payload types remain only partly decoded. |
| DBU bundles with text manifests inspected | 2 / 21 extracted DBU bundles | **9.52%** | Preload and Hub: 41 and 91 listed source entries. Binary chunk boundaries and some payload layouts are now documented; most resource semantics remain unresolved. |
| Spatial audio/reverb volume records exported | 10 records / 2 sampled DBU bundles | — | Eight records from Hub and two from Burial, each 192 bytes; field interpretation is provisional and the total across all archives is unknown. |
| Standalone DSP audio files exported as WAV | 1,005 / 1,005 extracted DSP files | **100%** | 72.26 minutes of mono PCM audio; zero decoding errors. Loop metadata retained; listening/hardware comparison remains unverified. |
| ADP music streams exported as WAV | 19 / 19 extracted ADP files | **100%** | 35.80 minutes of stereo PCM at nominal 48 kHz; zero decoding errors. Game-controlled looping remains unresolved. |
| Static model records exported as GLB | 9,058 / 9,408 encountered model records | **96.28%** | 1,713,896 triangles; 8,464 meshes include embedded textures. Static pass leaves 326 matrix-dependent and 24 subtype-17 records unresolved; repeated resources retained. |
| Skeletal model records exported as skinned GLB | 341 / 354 attempted skeletal records | **96.33%** | Separate rig pass; corrected runtime root ID recovered 67 records. Thirteen records retain inconsistent bind matrices. These records overlap the model scan and are not additive completion totals. |
| Unique motion banks decoded | 41 / 41 encountered unique banks | **100%** | 949 parsed clips, zero bank-decoding errors; banks deduplicated by source SHA-256. |
| Motion banks attached to exported rigs | 30 / 41 decoded banks | **73.17%** | 30 animated GLBs with 808 attached clips; 11 banks remain JSON-only. Partial track bindings and 30 Hz baking are not verified gameplay playback. |
| Hub authored placements assembled | 1,888 / 1,888 Hub instance records | **100%** | One sampled level only: actor-populated export contains 1,025 embedded meshes, 348,140 placed triangles, and 194 unique embedded images. Original placement matrices retained; gameplay behavior, visibility, LOD, lighting, and effects are not reconstructed. |
| Hub actor/prop preview bindings resolved | 20 / 20 supported matched environment prefixes | **100%** | Eight supported classes and eight replacement resources; rigs displayed in bind pose. Another 232 box markers remain, including triggers and unsupported placeholders; this is not overall actor completion. |

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

File shares are by count, not bytes, and are rounded. Bundles may contain many internal resources, whose total is unknown; the texture-record percentage covers only records encountered by the current decoder. Model and animation percentages cover only the encountered or attempted records listed above. No overall model/texture/animation completion percentage is available yet; DBA sound banks remain undecoded.

Matching results are recorded in [binary matching findings](analysis/BINARY_MATCHING.md) and [the complete 1,000-function matching snapshot](analysis/all-matching-summary.json). The function denominator comes from `analysis/index-summary.json` and is provisional: automatic regions include SDK/runtime code and may not map one-to-one to original source functions. The 1,000 fully modeled indexed routines are listed with source definitions and original sizes in [the semantic function inventory](analysis/semantic-functions.json). Validate this inventory with `python3 tools/check_semantic_progress.py`; see [the latest 600-function batch](analysis/INTEGER_HELPERS.md) for its low-level recovery scope, SDK/runtime inclusion, differential checks, and explicit coverage limits. The partial models cover only `0x801B8F24..0x801B8F5C` within `0x801B8E60` and the scalar flag-bit operation within `0x8027F680`; both are excluded from the routine and byte totals, along with the offline world-record reader. Recalculate their original sizes using the ignored `analysis/functions.csv` after running `tools/index_dol.py`; text-section sizes come from the index summary. Asset counts come from the ignored `assets/manifest.json`, regenerated with `python3 tools/extract_assets.py --inventory-only`. Texture export counts come from the ignored `assets/textures/manifest.json`, regenerated with `python3 tools/decode_textures.py`; see [texture format findings](analysis/TEXTURE_EXTRACTION.md) for limits. World-volume counts come from `analysis/hub-world-volumes.json` and `analysis/burial-world-volumes.json`; see [world-volume findings](analysis/WORLD_VOLUMES.md) for decoder commands and limits. Audio, music, model, rig, and animation counts come from the ignored manifests under `assets/audio/`, `assets/music/`, `assets/models/`, `assets/rigs/`, and `assets/animations/`. See [audio extraction](analysis/AUDIO_EXTRACTION.md), [music extraction](analysis/MUSIC_EXTRACTION.md), [static mesh extraction](analysis/MODEL_EXTRACTION.md), and [skeletal/animation extraction](analysis/SKELETAL_EXTRACTION.md) for validation and limits. Hub scene and actor-binding counts come from the ignored `assets/levels/Hub/manifest.json`; see [level extraction](analysis/LEVEL_EXTRACTION.md) and [actor placement previews](analysis/ACTOR_PLACEMENT.md) for the base scene, supported prefix scope, provenance checks, and limits. These numbers are a manual snapshot and should be refreshed when recovery advances.

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

The latest 600-function batch and its checks are documented in [integer helper findings](analysis/INTEGER_HELPERS.md). Earlier batches are documented in [scalar helper findings](analysis/SCALAR_HELPERS.md), [resource leaf helper findings](analysis/RESOURCE_LEAF_HELPERS.md), [leaf helper findings](analysis/LEAF_HELPERS.md), and [runtime helper findings](analysis/RUNTIME_HELPERS.md).

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

To convert standalone Nintendo DSP audio to playable WAV files:

```sh
python3 tools/decode_audio.py
python3 -m unittest discover -s tests -p test_decode_audio.py
```

Open `assets/audio/index.html` to search and play the exported clips. The
decoder preserves the original sample rate and writes mono 16-bit PCM WAVs;
`assets/audio/manifest.json` records source/PCM hashes, durations, peak levels,
and loop metadata. It uses only Python's standard library. DBA sound banks
require a separate decoder. See [audio findings](analysis/AUDIO_EXTRACTION.md).

To convert the ADP music streams (requires Python 3 and Clang):

```sh
python3 tools/decode_music.py
python3 -m unittest discover -s tests -p test_decode_music.py
```

Open `assets/music/index.html` to search and play all 19 tracks. The exporter
writes stereo 48 kHz PCM WAVs and a manifest with original filenames, sample
counts, durations, and source/PCM hashes. The first full pass exported 35.80
minutes with no errors. Tracks play once without inferred loop points or
trimming. See [music format findings](analysis/MUSIC_EXTRACTION.md).

## Export static models

After extracting the disc and textures, run:

```sh
python3 tools/decode_models.py
python3 -m unittest discover -s tests -p test_decode_models.py
python3 tools/check_model_exports.py
```

The first pass exported 9,058 static GLB meshes (1,713,896 triangles), including
8,464 meshes with an embedded texture. Repeated assets across levels are retained.
Open `assets/models/index.html` for the searchable list and local preview, or
import GLBs into Blender. Use the viewer's file picker to preview other exports;
the coconut is embedded as its default example. The viewer has no external dependencies.

The static-pass manifest records source offsets and 350 unresolved records.
The separate rig/animation pass below handles supported skeletal meshes.
Baked vertex colors and layered materials remain unreconstructed. Hub's
static object placements are assembled in the level pass below. See
[model extraction findings](analysis/MODEL_EXTRACTION.md).

## Export skeletons and animations

After the texture and static-model passes, run:

```sh
python3 tools/decode_rigs.py
python3 tools/decode_animations.py
python3 tools/rig_galleries.py
python3 -m unittest discover -s tests -p test_decode_rigs.py
python3 tools/check_rig_exports.py
```

Open `assets/animations/index.html` to preview Tak's motions, choose a clip,
play/pause, or scrub the timeline. Use the file picker for other animated
exports, or import the self-contained GLBs into Blender. Bind-pose rigs have
a separate gallery at `assets/rigs/index.html`.

The rig pass now exports 341 skinned meshes and decodes 949 clips from 41
unique motion banks. Matching rigs receive 808 clips across 30 animated
GLBs, including Tak's 137-bone rig and 185 bound motions from its 186-clip bank.
The blink clip has no matching bone tracks and remains in the JSON export. The animation-bank
parser reported no errors; 13 skeletal model records remain unresolved.
Correcting the serialized root count to runtime matrix ID 0 recovered 67
models and enabled Plant Man's 35 clips plus Tak's splash animation.
Some reduced rigs omit unmatched animation tracks, listed in the manifest.
Serialized helper-bone rotations are also baked, including Tak's 21 hand,
arm, spine, and leg helpers. The remaining neck deformation gap still needs
verification against gameplay. Motion is baked at 30 Hz from the game's 300 Hz timeline; gameplay blending,
mirroring, IK, and procedural effects are not reconstructed. See
[skeletal extraction findings](analysis/SKELETAL_EXTRACTION.md).

## Assemble the Hub level

After the texture, static-model, and rig exports, run:

```sh
python3 tools/decode_level.py --actors
python3 tools/check_level_export.py
python3 tools/render_level_preview.py
```

Open `assets/levels/Hub/index.html` for the offline level viewer, or import
`assets/levels/Hub/Hub.glb` into Blender. The scene contains 1,888 placements,
1,025 embedded meshes, 348,140 placed triangles, and 194 unique embedded textures.
Twenty box placements now use eight extracted actor/prop models, including
chickens, a monkey, a rhino, sheep, Yorbel, a tiki, ropes, and ziplines.
Characters are static bind-pose previews. Omit `--actors` for the original
1,017-mesh static world export.
The viewer starts with a cutaway; enable canopy, sky, backdrop, and helper
groups to inspect additional records. All placements remain in the GLB.

Matrices and model references are checked against original archive bytes.
This is an authored static scene; actor behavior, visibility/LOD selection,
lighting, and effects are not reconstructed. See
[level extraction findings](analysis/LEVEL_EXTRACTION.md) and
[actor placement findings](analysis/ACTOR_PLACEMENT.md).

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
in place of the host models' callbacks. With GC 1.3.2 and `-O4,p`, **22 of 29**
match exactly; seven differ. The earlier stop setter brings the total to
**23 of the original 30 modeled routines / 1,548 bytes**. The host models remain available
for behavior research.

`build/matching/report.json` records every result, compiler/source hashes,
commands, and applied relocations. Per-function `.diff.txt` files show all
word differences; binaries and compiler logs stay under ignored `build/`.
The checker resolves supported PPC relocations at original addresses and
compares every byte, including branch/global operands. Unsupported or
unresolved relocations fail. Add `--require-all` to also exit nonzero for
byte differences; the default completes the survey and reports mismatches.
Use `--function 0x801B91FC --output build/matching-one` for an isolated check.

## Check all modeled routines

```sh
python3 tools/check_all_matching.py --snapshot analysis/all-matching-summary.json
python3 -m unittest discover -s tests -p test_new_matching.py
```

The complete survey covers all 1,000 entries in the semantic inventory:
**255 match exactly (6,088 bytes), and 745 differ**. The 970 newer routines
contribute 232 matches; the original 30 contribute 23. Generated candidates
replace host memory callbacks with target-width accesses and remove harness
output buffers; their current compiler results do not imply every source
model is suitable as an original-ABI replacement.

The new-family checker is `tools/check_new_matching.py`. Generated candidates,
objects, logs, and differences stay in ignored `build/new-matching/`.
`tools/check_all_matching.py --collect-only` independently rechecks existing
objects against the original DOL, verifies source/object hashes, and requires
exact coverage of the current semantic inventory. It writes
`build/all-matching/report.json`. Add `--snapshot analysis/all-matching-summary.json`
to refresh the portable per-function summary. Unmatched routines remain
explicit byte differences; no unresolved comparisons are counted as matches.

## Attribution

Commercial game code and assets are not supplied or licensed by this repository.
