#!/usr/bin/env python3
"""Compile frame-free caller interfaces and compare all original bytes."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess

from caller_interfaces import recover, render
from check_new_matching import original_bytes
from integer_recovery import render as render_models
from ppc_leaf import load_functions
from ppc_matching import function_code

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'src/matching/caller_interfaces.cpp'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-source', action='store_true', help='Regenerate the tracked C++ candidates')
    args = parser.parse_args()
    specs = json.loads((ROOT / 'analysis/call-helper-specs.json').read_text())['routines']
    if render_models(specs, full_context=True, allow_calls=True) != (ROOT / 'src/recovered/call_leaf_helpers.c').read_text():
        raise ValueError('Caller models differ from saved specifications')
    entries = recover(specs)
    if not entries:
        raise ValueError('No recognized caller interfaces')
    source = render(entries)
    if args.write_source:
        (ROOT / SOURCE).write_text(source)
    elif (ROOT / SOURCE).read_text() != source:
        raise ValueError('Caller interface source differs; regenerate explicitly')
    manifest = json.loads((ROOT / 'analysis/semantic-functions.json').read_text())
    inventory = {x['address']: x for x in manifest['routines']}
    words = load_functions([x['address'][2:] for x in entries])
    output = ROOT / 'build/caller-interfaces'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').unlink(missing_ok=True)
    cc = ROOT / 'tools/mwcc/GC/1.3.2/mwcceppc.exe'
    runner = ROOT / 'tools/wibo'
    results = []
    for entry in entries:
        address = entry['address']
        model = inventory[address]
        name = 'fn_' + address[2:]
        src = output / (name + '.cpp')
        obj = output / (name + '.o')
        for suffix in ('.o', '.bin', '.original.bin', '.diff.txt'):
            (output / (name + suffix)).unlink(missing_ok=True)
        src.write_text('#define TAK_FN ' + address + '\n' + source)
        command = [str(runner), str(cc), '-c', '-lang', 'c++', '-proc', 'gekko',
                   '-O4,p', '-nodefaults', str(src), '-o', str(obj)]
        run = subprocess.run(command, capture_output=True, text=True)
        (output / (name + '.log')).write_text(run.stdout + run.stderr)
        record = dict(address=address, function=name, model_source=model['source'],
                      model_symbol=model['symbol'], original_size=model['original_bytes'],
                      interface=entry, candidate_sha256=digest(src), command=command, exact_match=False)
        if run.returncode:
            record.update(status='compile_error', error=run.stdout + run.stderr)
        else:
            record['object_sha256'] = digest(obj)
            try:
                code, relocations = function_code(obj, name, int(address, 0), {})
                expected = original_bytes(words[address[2:]])
                if len(expected) != model['original_bytes']:
                    raise ValueError('Inventory size differs from verified original')
                (output / (name + '.bin')).write_bytes(code)
                (output / (name + '.original.bin')).write_bytes(expected)
                diffs = [f'+0x{i:04x}: original {expected[i:i+4].hex() or "<end>"} candidate {code[i:i+4].hex() or "<end>"}'
                         for i in range(0, max(len(code), len(expected)), 4) if code[i:i+4] != expected[i:i+4]]
                (output / (name + '.diff.txt')).write_text('\n'.join(diffs))
                record.update(status='match' if code == expected else 'different',
                              exact_match=code == expected, candidate_size=len(code), relocations=relocations)
            except (ValueError, IndexError) as error:
                record.update(status='relocation_error', error=str(error))
        results.append(record)
    sources = [SOURCE, 'src/recovered/call_leaf_helpers.c', 'analysis/call-helper-specs.json',
               'tools/caller_interfaces.py', 'tools/check_caller_interfaces.py', 'tools/integer_recovery.py']
    report = dict(family='caller-interfaces', dol_sha256=manifest['dol_sha256'],
                  scope='Full relocated function code; compiler-managed frames, provisional C interfaces',
                  compiler_sha256=digest(cc), runner_sha256=digest(runner),
                  model_hashes={p: digest(ROOT / p) for p in sources},
                  candidate_interface='Recognized 48-byte fill, virtual, swap, nested/bit-guard, and byte-bool wrappers; types provisional; compiler-managed frames',
                  checked=len(results), matched=sum(r['exact_match'] for r in results),
                  matched_bytes=sum(r['original_size'] for r in results if r['exact_match']), results=results)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'{report["matched"]}/{len(results)} exact matches / {report["matched_bytes"]} bytes; '
          f'{dict(collections.Counter(r["status"] for r in results))}')
    if any(r['status'].endswith('_error') for r in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
