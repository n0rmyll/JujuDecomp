#!/usr/bin/env python3
"""Inspect the observed 0x1C-byte level descriptors in GJUE78 rev 0."""
import hashlib
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
            off, start, size = [struct.unpack_from('>I', data, base+i*4)[0]
                                for base in (offsets, addresses, sizes)]
            if size and start <= address and address+length <= start+size:
                off += address-start
                return data[off:off+length]
    raise ValueError(f'Unmapped address {address:#x}')

def text(address):
    result = bytearray()
    for i in range(256):
        byte = read(address+i, 1)[0]
        if byte == 0:
            return result.decode('ascii')
        if not 32 <= byte < 127:
            raise ValueError('Non-string pointer')
        result.append(byte)
    raise ValueError('Unterminated string')

rows = []
for index in range(128):
    address = 0x802cd918 + index*28
    words = struct.unpack('>7I', read(address, 28))
    try:
        names = [text(p) for p in words[:3]]
    except ValueError:
        break
    rows.append(dict(index=index, address=f'0x{address:08X}', internal_name=names[0],
                     display_name=names[1], resource_path=names[2],
                     unknown_words=[f'0x{w:08X}' for w in words[3:]],
                     unknown_18_float=struct.unpack('>f', struct.pack('>I', words[6]))[0]))
else:
    raise SystemExit('No descriptor boundary found')
if len(rows) != 54 or rows[0]['internal_name'] != 'Hub' or rows[-1]['internal_name'] != 'SnowBoardFMV':
    raise SystemExit('Unexpected descriptor sequence')
report = dict(table='0x802CD918', stride=28, count=len(rows),
              boundary='First record with invalid string pointers; original count constant not recovered',
              caveat='Includes development/FMV descriptors; does not establish assets exist or entries are playable.',
              entries=rows)
(root / 'analysis/levels.json').write_text(json.dumps(report, indent=2)+'\n')
print(f'Extracted {len(rows)} descriptors; unknown fields retained.')
