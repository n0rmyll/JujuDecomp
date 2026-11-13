#!/usr/bin/env python3
"""Inspect an observed DBLMerge text prefix; do not decode binary payloads."""
import argparse
import hashlib
import json
import re
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('archive', type=Path)
p.add_argument('--output', type=Path, required=True)
args = p.parse_args()
data = args.archive.read_bytes()
if not re.fullmatch(rb'[0-9]+ *\n', data[:8]):
    raise SystemExit('Unsupported eight-byte decimal prefix')
offset = int(data[:8].strip())
if not 8 < offset <= min(len(data), 1024*1024):
    raise SystemExit('Invalid prefix boundary')
header = data[8:offset].rstrip(b'\0').decode('ascii')
if 'created by DBLMerge' not in header or '\nContents:\n' not in header:
    raise SystemExit('Unrecognized DBLMerge header')
build, contents = header.split('\nContents:\n', 1)
entries = []
for line in contents.splitlines():
    match = re.fullmatch(r'\s*(\d+): (.+) (\d+)\s*', line)
    if not match or int(match[1]) != len(entries):
        raise SystemExit(f'Invalid contents record: {line!r}')
    entries.append(dict(index=int(match[1]), source_path=match[2], declared_size=int(match[3])))
report = dict(archive=args.archive.name, sha256=hashlib.sha256(data).hexdigest(),
              file_size=len(data), observed_binary_offset=offset, build_header=build,
              caveat='Text metadata only. Source sizes are not payload offsets; no binary extraction layout inferred.',
              entries=entries)
args.output.write_text(json.dumps(report, indent=2)+'\n')
print(f'{args.archive.name}: {len(entries)} declared resources; observed binary offset {offset:#x}')
