#!/usr/bin/env python3
"""Verify recovered dispatch pointers against the identified original DOL."""
import hashlib
import csv
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = (root / 'analysis/main.dol').read_bytes()
if hashlib.sha256(data).hexdigest() != '49faf28a7d2e25422c145754ef41b0c8a8dfcd83e688db1c39ecf21f6e34b706':
    raise SystemExit('Unexpected executable revision')

def read(address, length):
    for count, offsets, addresses, sizes in ((7, 0, 0x48, 0x90), (11, 0x1c, 0x64, 0xac)):
        for i in range(count):
            off, start, size = [struct.unpack_from('>I', data, base + 4*i)[0]
                                for base in (offsets, addresses, sizes)]
            if size and start <= address and address + length <= start + size:
                offset = off + address - start
                return data[offset:offset+length]
    raise ValueError(f'Address not backed by DOL data: {address:#x}')

def words(address, count):
    return list(struct.unpack(f'>{count}I', read(address, count*4)))

def require(actual, expected, label):
    if actual != expected:
        raise SystemExit(f'{label} mismatch: {actual!r} != {expected!r}')

tables = {
    'application': (0x802ef344, [0, 0, 0x80213214, 0x802132ac, 0x802134c8, 0x80213584, 0]),
    'game': (0x802ce4d8, [0, 0, 0x800e3fb0, 0x800e4060, 0x800e53c4, 0x800e53cc,
                         0x800e414c, 0x80212a80, 0x800e45c4, 0x800e4608]),
    'input_member': (0x802ef2a0, [0, 0, 0x80211d68, 0x80211ed4, 0x80211f54,
                                 0x80211fdc, 0x80211fe4]),
    'state_0ea4': (0x802c73c0, [0, 0, 0x800ce3b8, 0x800ce484, 0x800ce88c, 0x800ceb2c]),
    'state_452c0': (0x802c73a8, [0, 0, 0x800cec98, 0x800ced44, 0x800cedd8, 0x800ceec0]),
    'state_32a0_primary': (0x802d4274, [0, 0, 0x80100644, 0x80100e54, 0x80101e6c, 0x801028f4]),
}
for name, (address, expected) in tables.items():
    require(words(address, len(expected)), expected, name)
require(words(0x803320e0, 1), [0x803276f8], 'application global')
require(words(0x803312f8, 1), [0x802f71ec], 'game global')
# Constructor actually installs the application table, not merely references it.
require(words(0x802137ac, 4), [0x3c80802f, 0x387f0478, 0x3804f344, 0x901f0000],
        'application vtable installation')
require(words(0x800e5400, 3), [0x381f6d58, 0x387e0104, 0x901e0000],
        'game vtable installation (r31 loaded with 0x802c7780 earlier)')
require(words(0x8020f9c8, 3), [0x38000001, 0x98030004, 0x4e800020], 'stop flag setter')
# This path reaches a literal hardware store, not just a function with a guessed name.
require(words(0x80130478, 4), [0x38000048, 0x3c60cc01, 0x98038000, 0x4e800020],
        'graphics command byte store to 0xCC008000')
graphics_path = ['fn_80101E6C', 'fn_801D8CA8', 'fn_801877A4', 'fn_80130478']
with (root / 'analysis/calls.csv').open() as stream:
    edges = {(r['caller'], r['callee']) for r in csv.DictReader(stream) if r['kind'] == 'direct'}
for edge in zip(graphics_path, graphics_path[1:]):
    require(edge in edges, True, f'graphics call edge {edge}')
result = {name: {'address': f'0x{address:08X}',
                 'slots': {f'0x{i*4:02X}': f'0x{word:08X}' for i, word in enumerate(expected)}}
          for name, (address, expected) in tables.items()}
result['graphics_path'] = graphics_path
result['verification'] = 'PASS: DOL identity, tables, singleton pointers, constructor stores, stop setter, graphics store and indexed call path'
(root / 'analysis/application-map.json').write_text(json.dumps(result, indent=2) + '\n')
print(result['verification'])
