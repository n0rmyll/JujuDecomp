#!/usr/bin/env python3
"""Validate the complete semantic routine inventory against local evidence.

Does not replace the behavior tests or establish compiled binary matching.
"""
import json
from pathlib import Path
import re

from ppc_leaf import load_functions

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT/'analysis/semantic-functions.json').read_text())
    entries = manifest['routines']
    addresses = [entry['address'][2:] for entry in entries]
    if len(set(addresses)) != len(addresses):
        raise ValueError('Duplicate original function address')
    original = load_functions(addresses)
    regions = []
    definitions = {}
    macros = {}
    for entry, address in zip(entries, addresses):
        size = len(original[address])*4
        if size != entry['original_bytes'] or entry['status'] != 'complete-semantic-model':
            raise ValueError(f'Invalid size/status for {address}')
        path = entry['source']
        if path not in definitions:
            source = (ROOT/path).read_text()
            definitions[path] = set(re.findall(r'\b((?:tak_|small_)\w+)\s*\([^;]*?\)\s*\{', source, re.S))
            macros[path] = set(re.findall(r'^FN\(([0-9A-F]{8})\)', source, re.M))
        found = address in macros[path] or entry['symbol'] in definitions[path]
        if not found:
            raise ValueError(f'Missing source definition for {address}')
        regions.append((int(address, 16), int(address, 16)+size))
    regions.sort()
    if any(right[0] < left[1] for left, right in zip(regions, regions[1:])):
        raise ValueError('Overlapping original function regions')
    total = sum(entry['original_bytes'] for entry in entries)
    if len(entries) != manifest['complete_functions'] or total != manifest['original_bytes']:
        raise ValueError('Manifest totals disagree')
    print(f'PASS: {len(entries)} unique indexed routine models, {total} original bytes; '
          'source definitions, indexed regions and original instruction bytes verified')


if __name__ == '__main__':
    main()
