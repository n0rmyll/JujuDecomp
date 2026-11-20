#!/usr/bin/env python3
"""Link original DTK split objects and require an exact GJUE78 DOL roundtrip.

This is a binary-derived baseline. It does not rebuild the game from recovered C.
All output, original binaries and split objects remain local under ignored paths.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from check_application_flag import EXPECTED_HASH

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dol_layout(data):
    """Validate initialized DOL sections and describe them without original bytes."""
    if len(data) < 0x100:
        raise ValueError('Truncated DOL header')
    sections = []
    for index in range(18):
        offset, address, size = [struct.unpack_from('>I', data, base + index * 4)[0]
                                 for base in (0, 0x48, 0x90)]
        if not (offset or address or size):
            continue
        if not all((offset, address, size)) or offset < 0x100 or offset + size > len(data):
            raise ValueError('Invalid initialized section: ' + str(index))
        if address + size > 0x100000000:
            raise ValueError('Wrapped section address')
        sections.append(dict(index=index, kind='text' if index < 7 else 'data',
                             address=f'0x{address:08X}', offset=offset, size=size,
                             sha256=hashlib.sha256(data[offset:offset + size]).hexdigest()))
    for key in ('offset', 'address'):
        ordered = sorted(sections, key=lambda s: int(s[key], 0) if key == 'address' else s[key])
        for left, right in zip(ordered, ordered[1:]):
            start = int(left[key], 0) if key == 'address' else left[key]
            next_start = int(right[key], 0) if key == 'address' else right[key]
            if start + left['size'] > next_start:
                raise ValueError('Overlapping initialized sections: ' + key)
    bss_address, bss_size, entry = struct.unpack_from('>III', data, 0xD8)
    return dict(entry=f'0x{entry:08X}', bss_address=f'0x{bss_address:08X}',
                bss_size=bss_size, initialized_bytes=sum(s['size'] for s in sections),
                sections=sections)


def compare_dols(original, rebuilt):
    before, after = dol_layout(original), dol_layout(rebuilt)
    if original != rebuilt:
        first = next((i for i, (a, b) in enumerate(zip(original, rebuilt)) if a != b),
                     min(len(original), len(rebuilt)))
        raise ValueError(f'DOL roundtrip differs: first difference at file offset 0x{first:X}; '
                         f'original size {len(original)}, rebuilt size {len(rebuilt)}')
    if before != after:
        raise ValueError('DOL layout differs despite equal files')
    return before


def run_logged(command, path):
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
    path.write_text(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError(f'Command failed ({run.returncode}); see {path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/rebuild-foundation')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / 'report.json'
    report_path.unlink(missing_ok=True)
    original_path = ROOT / 'analysis/main.dol'
    original = original_path.read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED_HASH:
        raise ValueError('Unexpected DOL revision')
    config_path = ROOT / 'analysis/split/config.json'
    config = json.loads(config_path.read_text())
    if config.get('version') != '1.8.4' or config.get('modules') or config.get('links'):
        raise ValueError('Unsupported split configuration')
    units = config['units']
    objects = [ROOT / unit['object'] for unit in units]
    if not objects or len(set(objects)) != len(objects):
        raise ValueError('Empty or duplicate split object list')
    lcf = ROOT / config['ldscript']
    runner = ROOT / 'tools/wibo'
    linker = ROOT / 'tools/mwcc/GC/1.3.2/mwldeppc.exe'
    dtk = ROOT / 'tools/dtk'
    elf = output / 'baseline.elf'
    dol = output / 'baseline.dol'
    for path in (elf, dol, output / 'baseline.map'):
        path.unlink(missing_ok=True)
    command = [str(runner), str(linker), '-nodefaults', '-fp', 'hardware', '-lcf', str(lcf),
               '-m', config['entry'], '-o', str(elf), '-map', str(output / 'baseline.map'),
               *[str(path) for path in objects]]
    run_logged(command, output / 'link.log')
    conversion = [str(dtk), 'elf2dol', str(elf), str(dol)]
    run_logged(conversion, output / 'elf2dol.log')
    layout = compare_dols(original, dol.read_bytes())
    report = dict(revision='GJUE78 rev 0', exact_match=True,
                  scope='Original binary-derived DTK object relink; no recovered C replacement or in-game test',
                  original_sha256=EXPECTED_HASH, rebuilt_sha256=digest(dol),
                  rebuilt_size=dol.stat().st_size, elf_sha256=digest(elf),
                  map_sha256=digest(output / 'baseline.map'),
                  split_config_sha256=digest(config_path), lcf_sha256=digest(lcf),
                  checker_sha256=digest(Path(__file__).resolve()),
                  tools={str(path.relative_to(ROOT)): digest(path) for path in (runner, linker, dtk)},
                  object_count=len(objects), autogenerated_units=sum(bool(u.get('autogenerated')) for u in units),
                  object_hashes={str(path.relative_to(ROOT)): digest(path) for path in objects},
                  commands=[command, conversion], **layout)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: {len(objects)} original split objects relink to an exact {len(original):,}-byte DOL; '
          f'{len(layout["sections"])} initialized sections; SHA-256 {EXPECTED_HASH}')
    print(report_path)


if __name__ == '__main__':
    main()
