#!/usr/bin/env python3
"""Index the original DOL and dtk disassembly; no third-party dependencies."""
import csv
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis'
data = (OUT / 'main.dol').read_bytes()
sections = []
for kind, count, off_base, addr_base, size_base in (
    ('text', 7, 0, 0x48, 0x90), ('data', 11, 0x1c, 0x64, 0xac)
):
    for i in range(count):
        off, addr, size = (struct.unpack_from('>I', data, base + 4*i)[0]
                           for base in (off_base, addr_base, size_base))
        if size:
            assert off + size <= len(data), 'DOL section exceeds file'
            sections.append(dict(kind=kind, index=i, offset=off, address=addr, size=size))

def address(offset):
    for section in sections:
        if section['offset'] <= offset < section['offset'] + section['size']:
            return section['address'] + offset - section['offset']
    return None

def write_csv(name, fields, rows):
    with (OUT / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

strings = []
for match in re.finditer(rb'[\x20-\x7e]{5,}\x00', data):
    addr = address(match.start())
    if addr is not None:
        strings.append(dict(address=f'0x{addr:08X}', offset=f'0x{match.start():X}',
                            text=match.group()[:-1].decode('ascii')))
write_csv('strings.csv', ['address', 'offset', 'text'], strings)

functions, calls = [], []
for path in sorted((OUT / 'split' / 'asm').glob('*.s')):
    text = path.read_text()
    for match in re.finditer(r'^\.fn (\S+),[^\n]*\n(.*?)^\.endfn', text, re.M | re.S):
        name, body = match.groups()
        instructions = re.findall(r'^/\* ([0-9A-F]{8}) [^\n]*?\*/\s*(.*)', body, re.M)
        if not instructions:
            continue
        start, end = int(instructions[0][0], 16), int(instructions[-1][0], 16) + 4
        functions.append(dict(name=name, address=f'0x{start:08X}', size=end-start,
                              assembly=str(path.relative_to(ROOT))))
        for pc, instruction in instructions:
            call = re.fullmatch(r'bl\s+(\S+)', instruction)
            if call:
                calls.append(dict(caller=name, site=f'0x{pc}', callee=call[1], kind='direct'))
            elif instruction.strip() in ('bctrl', 'blrl'):
                calls.append(dict(caller=name, site=f'0x{pc}', callee='', kind='indirect'))
write_csv('functions.csv', ['name', 'address', 'size', 'assembly'], functions)
write_csv('calls.csv', ['caller', 'site', 'callee', 'kind'], calls)
summary = dict(sha256=hashlib.sha256(data).hexdigest(),
               entry=f'0x{struct.unpack_from(">I", data, 0xe0)[0]:08X}',
               sections=sections, function_regions=len(functions),
               direct_calls=sum(c['kind'] == 'direct' for c in calls),
               indirect_calls=sum(c['kind'] == 'indirect' for c in calls),
               strings=len(strings),
               caveat='Automatic function boundaries and names are provisional. Calls omit tail branches; strings require printable ASCII and a trailing NUL.')
(OUT / 'index-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'sections'}, indent=2))
