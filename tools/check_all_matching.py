#!/usr/bin/env python3
"""Run matching checks for the complete semantic inventory and verify every object."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from check_new_matching import original_bytes
from ppc_leaf import load_functions
from ppc_matching import function_code

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(allow_partial=False):
    manifest = json.loads((ROOT / 'analysis/semantic-functions.json').read_text())
    entries = {x['address']: x for x in manifest['routines']}
    words = load_functions([address[2:] for address in entries])
    old = json.loads((ROOT / 'build/matching/report.json').read_text())
    new = json.loads((ROOT / 'build/new-matching/report.json').read_text())
    flag = json.loads((ROOT / 'build/application-flag/match.json').read_text())
    if old['source_sha256'] != digest(ROOT / 'src/matching/routines.cpp'):
        raise ValueError('Stale original candidate report')
    if flag['source_sha256'] != digest(ROOT / 'src/recovered/application_flag.c'):
        raise ValueError('Stale stop-setter report')
    for source, expected in new['model_hashes'].items():
        if digest(ROOT / source) != expected:
            raise ValueError('Stale new-model report: ' + source)
    compiler_hash = digest(ROOT / 'tools/mwcc/GC/1.3.2/mwcceppc.exe')
    if any(report['compiler_sha256'] != compiler_hash for report in (old, new, flag)):
        raise ValueError('Compiler hashes disagree')
    with (ROOT / 'analysis/functions.csv').open() as stream:
        symbols = {r['name']: int(r['address'], 0) for r in csv.DictReader(stream)}
    for m in re.finditer(r'\.text\s*\|\s*(0x[0-9A-Fa-f]+)\s*\|[^|\n]*\|\s*(_(?:save|rest)gpr_\d+)',
                         (ROOT / 'analysis/dol-info.txt').read_text()):
        symbols[m[2]] = int(m[1], 0)
    records = [(r, ROOT / 'build/matching', r['function'], r['function'] + '.o')
               for r in old['results']]
    records += [(r, ROOT / 'build/new-matching', r['function'], r['function'] + '.o')
                for r in new['results']]
    records += [(dict(address='0x8020F9C8', status='match', exact_match=True,
                     object_sha256=flag['object_sha256']), ROOT / 'build/application-flag',
                 'tak_application_request_stop', 'application_flag.o')]
    results = []
    seen = set()
    for record, directory, symbol, object_name in records:
        address = record.get('address', '0x' + record['function'][-8:]) if 'function' in record else record['address']
        if address in seen or address not in entries:
            raise ValueError('Duplicate or unregistered matching result: ' + address)
        seen.add(address)
        if record['status'] not in ('match', 'different'):
            raise ValueError('Incomplete byte comparison: ' + address)
        obj = directory / object_name
        if digest(obj) != record['object_sha256']:
            raise ValueError('Stale object: ' + address)
        if 'candidate_sha256' in record:
            if digest(directory / (record['function'] + '.cpp')) != record['candidate_sha256']:
                raise ValueError('Stale generated candidate: ' + address)
        code, _ = function_code(obj, symbol, int(address, 0), symbols)
        expected = original_bytes(words[address[2:]])
        if len(expected) != entries[address]['original_bytes']:
            raise ValueError('Manifest size mismatch: ' + address)
        exact = code == expected
        if exact != record['exact_match']:
            raise ValueError('Saved result differs from independently recomputed comparison: ' + address)
        results.append(dict(address=address, source=entries[address]['source'],
                            original_bytes=len(expected), candidate_bytes=len(code),
                            status='match' if exact else 'different'))
    if len(entries) != manifest['complete_functions'] or (seen != set(entries) and not allow_partial):
        raise ValueError('Matching results do not cover the complete inventory')
    matches = [x for x in results if x['status'] == 'match']
    families = {}
    for source in sorted({x['source'] for x in results}):
        group = [x for x in results if x['source'] == source]
        families[source] = dict(checked=len(group), matched=sum(x['status'] == 'match' for x in group),
                                matched_bytes=sum(x['original_bytes'] for x in group if x['status'] == 'match'))
    return dict(revision=manifest['revision'], dol_sha256=manifest['dol_sha256'],
                compiler='CodeWarrior GC 1.3.2 (2.4.2 build 81)', compiler_sha256=compiler_hash,
                scope='Exact relocated individual function code; no linked executable or data verification',
                checked=len(results), matched=len(matches), different=len(results)-len(matches),
                inventory_total=len(entries), not_yet_surveyed=len(entries)-len(results),
                matched_bytes=sum(x['original_bytes'] for x in matches),
                families=families,
                source_hashes={p: digest(ROOT/p) for p in sorted({x['source'] for x in results} |
                    {'src/matching/routines.cpp', 'tools/check_new_matching.py', 'tools/ppc_matching.py',
                     'analysis/matching-adaptations.json',
                     'analysis/semantic-functions.json'})},
                results=sorted(results, key=lambda x: x['address']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collect-only', action='store_true', help='Revalidate existing objects without recompiling')
    parser.add_argument('--snapshot', type=Path, help='Also write a portable summary at this path')
    parser.add_argument('--allow-partial', action='store_true', help='Explicitly report surveyed coverage if the inventory has grown')
    args = parser.parse_args()
    path = ROOT / 'build/all-matching/report.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    if not args.collect_only:
        for command in (
            ['tools/check_matching.py'],
            ['tools/check_application_flag.py', '--mw-cc', 'tools/mwcc/GC/1.3.2/mwcceppc.exe', '--runner', 'tools/wibo'],
            ['tools/check_new_matching.py'],
        ):
            subprocess.run([sys.executable, *command], cwd=ROOT, check=True)
    report = collect(allow_partial=args.allow_partial)
    text = json.dumps(report, indent=2) + '\n'
    path.write_text(text)
    if args.snapshot:
        args.snapshot.write_text(text)
    print(f'{report["matched"]}/{report["checked"]} exact matches, {report["matched_bytes"]} bytes; '
          f'{report["different"]} differ; no unresolved comparisons')
    print(path)


if __name__ == '__main__':
    main()
