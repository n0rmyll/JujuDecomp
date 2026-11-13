"""Limited integer PowerPC oracle for the recovered leaf routines.

Executes verified original instruction words, not C-derived expectations.
Not a general CPU emulator: unsupported operations, external branches, and
instruction-budget exhaustion fail explicitly. No SDK, FPU, MMIO or faults.
"""
import csv
import hashlib
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
MASK = 0xffffffff


def signed(value, bits=32):
    value &= (1 << bits)-1
    return value-(1 << bits) if value & (1 << (bits-1)) else value


def rotate(value, shift):
    shift &= 31
    return ((value << shift) | (value >> ((32-shift) & 31))) & MASK


def bitmask(begin, end):
    return sum(1 << (31-i) for i in range(32)
               if (begin <= i <= end if begin <= end else i >= begin or i <= end))


def load_functions(addresses):
    data = (ROOT/'analysis/main.dol').read_bytes()
    if hashlib.sha256(data).hexdigest() != '49faf28a7d2e25422c145754ef41b0c8a8dfcd83e688db1c39ecf21f6e34b706':
        raise ValueError('Unexpected executable revision')
    sections = [tuple(struct.unpack_from('>I', data, base+i*4)[0] for base in (0, 0x48, 0x90))
                for i in range(7)]
    rows = {r['name']: r for r in csv.DictReader((ROOT/'analysis/functions.csv').open())}
    bodies = {}
    for path in {rows['fn_'+a]['assembly'] for a in addresses}:
        for match in re.finditer(r'^\.fn (\w+),.*?^\.endfn \1\s*$',
                                 (ROOT/path).read_text(), re.M | re.S):
            bodies[match[1]] = match[0]
    result = {}
    for address in addresses:
        row = rows['fn_'+address]
        start, size = int(address, 16), int(row['size'])
        words = {}
        for match in re.finditer(r'/\* ([0-9A-F]{8}) [0-9A-F]+  ((?:[0-9A-F]{2} ){3}[0-9A-F]{2}) \*/',
                                 bodies['fn_'+address]):
            pc, raw = int(match[1], 16), bytes.fromhex(match[2])
            backed = False
            for offset, base, length in sections:
                if base <= pc and pc+4 <= base+length:
                    if data[offset+pc-base:offset+pc-base+4] != raw:
                        raise ValueError(f'Original byte mismatch at {pc:08X}')
                    backed = True
                    break
            if not backed:
                raise ValueError('Instruction outside DOL text')
            words[pc] = int.from_bytes(raw, 'big')
        if sorted(words) != list(range(start, start+size, 4)):
            raise ValueError(f'Incomplete indexed function {address}')
        result[address] = words
    return result


def execute(words, args, memory, budget=20000, visited=None):
    registers = [0]*32
    registers[2], registers[13] = 0x8033b140, 0x80338280
    registers[3:7] = args
    pc, ctr = min(words), 0
    cr = [False]*32

    def compare(a, b, field=0):
        cr[field*4:field*4+3] = [a < b, a > b, a == b]

    for _ in range(budget):
        if pc not in words:
            raise ValueError(f'Branch outside function: {pc:08X}')
        if visited is not None:
            visited.add(pc)
        w = words[pc]
        op, rt, ra, rb = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
        imm = signed(w, 16)
        following, record = (pc+4) & MASK, False
        base = registers[ra] if ra else 0
        if op in (14, 15):
            registers[rt] = (base+(imm << (16 if op == 15 else 0))) & MASK
        elif op in (24, 25, 26, 28):
            immediate = w & 0xffff
            if op == 25:
                immediate <<= 16
            value = registers[rt]
            registers[ra] = (value & immediate if op == 28 else
                             value ^ immediate if op == 26 else value | immediate)
            if op == 28:
                compare(signed(registers[ra]), 0)
        elif op in (32, 33, 34, 40, 42, 36, 38, 44):
            address = (base+imm) & MASK
            size = {32: 4, 33: 4, 34: 1, 40: 2, 42: 2, 36: 4, 38: 1, 44: 2}[op]
            if op in (36, 38, 44):
                memory.write(address, registers[rt] & ((1 << (size*8))-1), size)
            else:
                value = memory.read(address, size)
                registers[rt] = (signed(value, 16) & MASK) if op == 42 else value
                if op == 33:
                    if not ra or ra == rt:
                        raise ValueError('Invalid load-with-update operands')
                    registers[ra] = address
        elif op in (10, 11):
            a = registers[ra] if op == 10 else signed(registers[ra])
            b = (w & 0xffff) if op == 10 else imm
            compare(a, b, (w >> 23) & 7)
        elif op == 7:
            registers[rt] = (registers[ra]*imm) & MASK
        elif op == 8:
            # subfic: carry is not consumed by any supported routine.
            registers[rt] = (imm-registers[ra]) & MASK
        elif op in (20, 21):
            mask = bitmask((w >> 6) & 31, (w >> 1) & 31)
            value = rotate(registers[rt], rb) & mask
            registers[ra] = value if op == 21 else (registers[ra] & ~mask) | value
            if w & 1:
                compare(signed(registers[ra]), 0)
        elif op == 18:
            if w & 3:
                raise ValueError('Absolute/linked branch unsupported')
            following = (pc+signed(w & 0x03fffffc, 26)) & MASK
        elif op == 16 or (op == 19 and (w >> 1) & 1023 == 16):
            bo, bi = rt, ra
            if w & 1:
                raise ValueError('Linked branch unsupported')
            if not bo & 4:
                ctr = (ctr-1) & MASK
            take = (bool(bo & 4) or ((ctr != 0) != bool(bo & 2))) and (
                bool(bo & 16) or cr[bi] == bool(bo & 8))
            if take:
                if op == 19:
                    return registers[3]
                if w & 2:
                    raise ValueError('Absolute conditional branch unsupported')
                following = (pc+signed(w & 0xfffc, 16)) & MASK
        elif op == 31:
            xo = (w >> 1) & 1023
            if xo in (0, 32):
                a, b = registers[ra], registers[rb]
                if xo == 0:
                    a, b = signed(a), signed(b)
                compare(a, b, (w >> 23) & 7)
            elif xo == 467 and ((w >> 16) & 31) == 9 and ((w >> 11) & 31) == 0:
                ctr = registers[rt]
            elif xo in (23, 87, 279, 151, 215):
                address = (base+registers[rb]) & MASK
                size = 2 if xo == 279 else 1 if xo in (87, 215) else 4
                if xo in (151, 215):
                    memory.write(address, registers[rt] & ((1 << (size*8))-1), size)
                else:
                    registers[rt] = memory.read(address, size)
            elif xo in (266, 40, 235):
                a, b = registers[ra], registers[rb]
                registers[rt] = (a+b if xo == 266 else b-a if xo == 40 else a*b) & MASK
                record = bool(w & 1)
                if record:
                    compare(signed(registers[rt]), 0)
            elif xo == 104:
                registers[rt] = (-registers[ra]) & MASK
                if w & 1:
                    compare(signed(registers[rt]), 0)
            elif xo in (444, 28, 60, 24, 954, 922, 124, 26, 824):
                a, b = registers[rt], registers[rb]
                if xo == 444: value = a | b
                elif xo == 28: value = a & b
                elif xo == 60: value = a & ~b
                elif xo == 24: value = 0 if b & 32 else a << (b & 31)
                elif xo == 124: value = ~(a | b)
                elif xo == 26: value = 32-a.bit_length()
                elif xo == 824: value = signed(a) >> rb
                else: value = signed(a, 8 if xo == 954 else 16)
                registers[ra] = value & MASK
                if w & 1:
                    compare(signed(registers[ra]), 0)
            else:
                raise ValueError(f'Unsupported op31/{xo} at {pc:08X}')
        else:
            raise ValueError(f'Unsupported instruction {w:08X} at {pc:08X}')
        pc = following
    raise ValueError('PowerPC instruction budget exhausted')
