#!/usr/bin/env python3
"""Compile and compare the remaining 29 modeled routines at original addresses."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
import struct
import subprocess

from check_application_flag import EXPECTED_HASH
from ppc_matching import function_code

ROOT = Path(__file__).resolve().parents[1]
ADDRESSES = [
    0x80213584, 0x801042FC, 0x800CEB2C, 0x80213140, 0x802131A0,
    0x801B91FC, 0x801B92FC, 0x801B8FD0, 0x801C5944, 0x801C59A4,
    0x801C5A04, 0x801C5BAC, 0x801C5C34, 0x801B90D0, 0x801B90F4,
    0x801B9190, 0x801B9244, 0x801C5A64, 0x8021311C, 0x80213480,
    0x80213710, 0x80213744, 0x800E53C4, 0x800E53CC, 0x80211ED4,
    0x80211F54, 0x8020F964, 0x80213708, 0x80280928,
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mw-cc', type=Path, default=ROOT / 'tools/mwcc/GC/1.3.2/mwcceppc.exe')
    parser.add_argument('--runner', type=Path, default=ROOT / 'tools/wibo')
    parser.add_argument('--optimization', default='4,p')
    parser.add_argument('--function', type=lambda x: int(x, 0), choices=ADDRESSES)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/matching')
    parser.add_argument('--require-all', action='store_true', help='Exit nonzero for any byte difference')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = output / 'report.json'
    report.unlink(missing_ok=True)
    data = (ROOT / 'analysis/main.dol').read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED_HASH:
        raise ValueError('Unexpected DOL revision')

    def original(address, size):
        for i in range(7):
            off, start, length = [struct.unpack_from('>I', data, base + i * 4)[0]
                                  for base in (0, 0x48, 0x90)]
            if start <= address and address + size <= start + length:
                return data[off + address - start:off + address - start + size]
        raise ValueError('Function outside DOL text')

    # Confirm the bases used by EMB_SDA21 against original startup instructions.
    if original(0x8000332c, 16).hex() != '3c4080336042b1403da0803361ad8280':
        raise ValueError('Small-data register initialization differs')
    with (ROOT / 'analysis/functions.csv').open() as stream:
        functions = {row['name']: row for row in csv.DictReader(stream)}
    symbols = {name: int(row['address'], 0) for name, row in functions.items()}
    for line in (ROOT / 'analysis/dol-info.txt').read_text().splitlines():
        match = re.match(r'\s*\.\w+\s*\|\s*(0x[0-9A-Fa-f]+)\s*\|[^|]*\|\s*(\S+)\s*$', line)
        if match and re.fullmatch(r'_(?:save|rest)gpr_\d+', match[2]):
            name, value = match[2], int(match[1], 0)
            if name in symbols and symbols[name] != value:
                raise ValueError(f'Conflicting original symbol {name}')
            symbols[name] = value
    source = ROOT / 'src/matching/routines.cpp'
    results = []
    addresses = [args.function] if args.function else ADDRESSES
    for address in addresses:
        name = f'fn_{address:08X}'
        size = int(functions[name]['size'])
        expected = original(address, size)
        obj = output / f'{name}.o'
        for suffix in ('.o', '.bin', '.original.bin', '.diff.txt', '.log'):
            (output / f'{name}{suffix}').unlink(missing_ok=True)
        command = [str(args.runner.resolve()), str(args.mw_cc.resolve()),
                   '-c', '-lang', 'c++', '-proc', 'gekko', f'-O{args.optimization}',
                   '-nodefaults', f'-DTAK_FN=0x{address:08X}', str(source), '-o', str(obj)]
        run = subprocess.run(command, capture_output=True, text=True)
        (output / f'{name}.log').write_text(run.stdout + run.stderr)
        result = dict(function=name, address=f'0x{address:08X}', original_size=size,
                      command=command, exact_match=False)
        if run.returncode:
            result.update(status='compile_error', error=run.stdout + run.stderr)
        else:
            result['object_sha256'] = hashlib.sha256(obj.read_bytes()).hexdigest()
            try:
                candidate, relocations = function_code(obj, name, address, symbols)
                (output / f'{name}.bin').write_bytes(candidate)
                (output / f'{name}.original.bin').write_bytes(expected)
                exact = candidate == expected
                differences = [
                    f'+0x{i:04x}: original {expected[i:i+4].hex() or "<end>"} '
                    f'candidate {candidate[i:i+4].hex() or "<end>"}'
                    for i in range(0, max(len(candidate), size), 4)
                    if candidate[i:i+4] != expected[i:i+4]]
                (output / f'{name}.diff.txt').write_text('\n'.join(differences) + ('\n' if differences else ''))
                result.update(status='match' if exact else 'different', exact_match=exact,
                              candidate_size=len(candidate), relocations=relocations,
                              equal_instructions=sum(candidate[i:i+4] == expected[i:i+4]
                                                     for i in range(0, min(len(candidate), size), 4)),
                              original_instructions=size // 4,
                              first_difference=next((i for i in range(max(len(candidate), size))
                                                     if candidate[i:i+1] != expected[i:i+1]), None))
            except (ValueError, IndexError, struct.error) as error:
                result.update(status='relocation_error', error=str(error))
        results.append(result)
        print(f'{name}: {result["status"]} ({result.get("candidate_size", "?")}/{size} bytes)', flush=True)
    matches = [r for r in results if r['exact_match']]
    report.write_text(json.dumps(dict(
        dol_sha256=EXPECTED_HASH, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        compiler_sha256=hashlib.sha256(args.mw_cc.read_bytes()).hexdigest(),
        runner_sha256=hashlib.sha256(args.runner.read_bytes()).hexdigest(),
        scope='Individual functions relocated to original addresses; no executable rebuild',
        checked=len(results), matched=len(matches), matched_bytes=sum(r['original_size'] for r in matches),
        results=results), indent=2) + '\n')
    print(f'{len(matches)}/{len(results)} exact matches; report: {report}')
    if any(r['status'].endswith('_error') for r in results) or (args.require_all and len(matches) != len(results)):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
