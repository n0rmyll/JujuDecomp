# First binary match: GJUE78 revision 0

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

## Scope and next steps

This establishes **one matching function / 12 matching code bytes**. Three simple
instructions are not enough to distinguish compiler versions or optimization
settings. CodeWarrior 1.3.2 is a working candidate, not an identified original
toolchain. There is no matching linked executable or runnable rebuilt game.

Next, select several relocation-free leaf routines with arithmetic, branches,
and field accesses to discriminate compiler versions and flags. Keep matching
sources faithful to original object layouts rather than the host callback
models. Add symbol-aware, relocation-aware object comparison for functions
that call other routines or access globals. Finally establish an assembly-only
linked baseline and verify its DOL before integrating C replacements.
