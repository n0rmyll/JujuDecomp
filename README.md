# JujuDecomp

An early reverse-engineering workspace for **Tak and the Power of Juju (USA)** on GameCube, disc ID **GJUE78**, revision 0. Includes analysis tools, research notes, two small semantic C reconstructions, and a browser emulator frontend based on [wasm-dolphin](https://github.com/dougchansan/wasm-dolphin) at commit `7e38409ace3dda709c178312ff63fd92a3653cc7`.

**This is not a completed decompilation or a native source port.** There is no build system that recreates the original game executable yet. The browser route runs your own disc image through Dolphin; the recovered C files are research models, not matching replacements. Tak boot, gameplay, audio, performance, and saves have not yet been verified in this workspace.

No game image, extracted executable, game assets, generated disassembly, or compiled emulator build is included. Supply your own legally obtained copy of the game. Keep game files local; the ignore rules exclude disc images, extracted binaries, saves, and build outputs.

## Get the source

```sh
git clone https://github.com/n0rmyll/JujuDecomp.git
cd JujuDecomp
```

The browser source is included directly; no submodule initialization is required. Its original license and documentation are preserved under `browser/`.

## Build the browser emulator

A source-only clone needs a compiled Dolphin WebAssembly core before it can run a game. The animated demo alone does not show that the game is running.

The inherited reproducible build currently pins **Windows x64** tools, including their executable hashes. Its recorded versions are Node.js 24.12.0, Emscripten SDK 5.0.7, CMake 4.3.2, Ninja 1.13.0.git.kitware.jobserver-pipe-1, and Rust nightly 1.97.0-nightly with `rust-src` and the `wasm32-unknown-emscripten` target. Exact revisions and hashes are in [the toolchain lock](browser/provenance/wasm-toolchain.lock.json). See [the reproducible build guide](browser/docs/repro-build.md) and [Rust/Naga setup](browser/docs/webgpu-naga-bridge.md) before installing the toolchain.

In PowerShell with those tools installed, from the repository root:

```powershell
cd browser
npm test
npm run check
npm run verify:toolchain
npm run fetch:dolphin
npm run patch:upstream
npm run configure:upstream
npm run build:upstream:full-core
npm run verify:provenance
npm start
```

Configuration builds the Rust/Naga bridge and the full-core target writes `browser/cores/dolphin/dolphin-core-upstream.js`, `.wasm`, and a build record. Downloads and outputs remain ignored. The JavaScript tooling uses Node built-ins; `package.json` has no package dependencies to install.

The exact build is **not currently validated on macOS or Linux**: the toolchain verifier rejects a different platform or executable hash. Serving an already-built core works separately from compiling it. Porting the locked toolchain is still required to support a fresh native build on those systems; changing version strings alone is insufficient. These build instructions document the inherited pipeline, which has not been rerun in this workspace.

## Run with your own game

Once you have built the core, run `cd browser && npm start` from the root and open the localhost URL printed by the server (normally `http://127.0.0.1:8080/`) in desktop Chrome. On macOS, `./play.command` also starts the server and opens the page if a core is available.

Use **Open a GameCube disc image**, or drag your own `.rvz`, `.iso`, or `.gcm` onto the page. The image is read locally in your browser. Start with the Software renderer; Hardware WebGPU is experimental and has no validated Tak profile.

Keyboard: WASD moves; X = A, Z = B, V = X, B = Y, Enter = Start, Q/E = L/R, C = Z. Arrow keys control the D-pad; IJKL control the C-stick. Standard gamepads are supported. Click Muted to enable audio.

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

Read [decompilation notes](analysis/DECOMP_NOTES.md) and [application dispatch findings](analysis/APPLICATION_DISPATCH.md) for current evidence and limitations. `src/recovered/` contains semantic reconstructions; original-target compiler identification, binary matching, asset decoding, and platform replacement work remain before a game source build is possible.

## Attribution

Browser runtime source and patches retain [the upstream GPL license](browser/LICENSE). Dolphin is copyright the Dolphin Emulator Project and distributed under GPLv2 or later. Preserve applicable notices and provide corresponding source when distributing compiled runtime builds; the inherited `npm run dist:source` tooling is documented in `browser/`. Commercial game code and assets are not supplied or licensed by this repository.
