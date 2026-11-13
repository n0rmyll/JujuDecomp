#!/usr/bin/env python3
"""Export a function with original-byte checks and explicit string annotations.

Example: python3 tools/function_report.py fn_80100E54 --base r30=0x802d2580
Base annotations are supplied by the analyst, not inferred data flow.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('function')
parser.add_argument('--base', action='append', default=[])
args = parser.parse_args()
if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', args.function):
    parser.error('Invalid function name')
bases = {reg: int(value, 0) for reg, value in (x.split('=') for x in args.base)}
data = (root / 'analysis/main.dol').read_bytes()
if hashlib.sha256(data).hexdigest() != '49faf28a7d2e25422c145754ef41b0c8a8dfcd83e688db1c39ecf21f6e34b706':
    raise SystemExit('Unexpected DOL revision')
sections = []
for count, offsets, addresses, sizes in ((7, 0, 0x48, 0x90), (11, 0x1c, 0x64, 0xac)):
    for i in range(count):
        off, addr, size = [struct.unpack_from('>I', data, base + i*4)[0]
                           for base in (offsets, addresses, sizes)]
        if size:
            sections.append((off, addr, size))

def read(addr, size):
    for off, start, length in sections:
        if start <= addr and addr + size <= start + length:
            return data[off+addr-start:off+addr-start+size]
    return None

def string_at(addr):
    out = bytearray()
    for i in range(512):
        raw = read(addr+i, 1)
        if raw is None:
            return None
        byte = raw[0]
        if byte == 0:
            return out.decode('latin-1') if len(out) >= 4 else None
        if byte not in (9, 10, 13, 0xa9) and not 32 <= byte < 127:
            return None
        out.append(byte)
    return None

matches = []
for path in sorted((root / 'analysis/split/asm').glob('*.s')):
    match = re.search(r'^\.fn ' + re.escape(args.function) + r',.*?^\.endfn '
                      + re.escape(args.function) + r'\s*$', path.read_text(), re.M | re.S)
    if match:
        matches.append((path, match.group()))
if len(matches) != 1:
    raise SystemExit(f'Expected one function definition, found {len(matches)}')
path, body = matches[0]
calls, references, instructions = [], [], []
for line in body.splitlines():
    match = re.match(r'/\* ([0-9A-F]{8}) [0-9A-F]+  ((?:[0-9A-F]{2} ){3}[0-9A-F]{2}) \*/\s*(.*)', line)
    if not match:
        continue
    pc, encoded, instruction = int(match[1], 16), bytes.fromhex(match[2]), match[3]
    if read(pc, 4) != encoded:
        raise SystemExit(f'Instruction mismatch at {pc:#x}')
    instructions.append(pc)
    call = re.fullmatch(r'bl (\S+)', instruction)
    if call:
        calls.append({'site': f'0x{pc:08X}', 'target': call[1]})
    addresses = []
    for label in re.finditer(r'lbl_([0-9A-F]{8})@(?:l\b|sda21\b)', instruction):
        addresses.append((int(label[1], 16), 'direct operand; may be a load rather than an address argument'))
    add = re.fullmatch(r'addi r\d+, (r\d+), (-?0x[0-9a-f]+)', instruction)
    if add and add[1] in bases:
        addresses.append((bases[add[1]] + int(add[2], 0), 'analyst-supplied register base'))
    for address, basis in addresses:
        text = string_at(address)
        if text:
            references.append({'site': f'0x{pc:08X}', 'address': f'0x{address:08X}',
                               'text': text, 'basis': basis})
if not instructions:
    raise SystemExit('No instructions parsed')
out = root / 'analysis/reports'
out.mkdir(exist_ok=True)
report = dict(function=args.function, source=str(path.relative_to(root)),
              start=f'0x{instructions[0]:08X}', instruction_count=len(instructions),
              byte_checks='PASS', supplied_bases=bases, calls=calls, strings=references)
(out / f'{args.function}.json').write_text(json.dumps(report, indent=2) + '\n')
(out / f'{args.function}.s').write_text(body + '\n')
print(json.dumps({'function': args.function, 'instructions_verified': len(instructions),
                  'direct_calls': len(calls), 'string_annotations': len(references)}))
