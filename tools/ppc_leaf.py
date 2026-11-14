"""Restricted PowerPC word oracle for integer and scalar-transfer projections.

Executes verified original instruction words, not C-derived expectations.
Not a general CPU emulator: unsupported operations and exhausted instruction
budgets fail explicitly. Optional scalar PS0 transfers have a restricted exact
single-conversion domain. No SDK implementations, FP arithmetic, PS1, FPSCR,
MMIO or hardware fault model.
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
    by_address = {r['address'][2:].upper(): r for r in rows.values()}
    bodies = {}
    for path in {by_address[a]['assembly'] for a in addresses}:
        for match in re.finditer(r'^\.fn (\w+),.*?^\.endfn \1\s*$',
                                 (ROOT/path).read_text(), re.M | re.S):
            bodies[match[1]] = match[0]
    result = {}
    for address in addresses:
        row = by_address[address]
        start, size = int(address, 16), int(row['size'])
        words = {}
        for match in re.finditer(r'/\* ([0-9A-F]{8}) [0-9A-F]+  ((?:[0-9A-F]{2} ){3}[0-9A-F]{2}) \*/',
                                 bodies[row['name']]):
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


def execute(words, args, memory, budget=20000, visited=None, final_registers=None, initial_context=None, final_context=None, calls=None, initial_fpr=None, final_fpr=None, floating_calls=None):
    floating=[0]*32
    if initial_fpr is not None:
        if len(initial_fpr)!=32:raise ValueError('Expected 32 scalar FPR words')
        floating[:]=initial_fpr
    registers = [0]*32
    registers[2], registers[13] = 0x8033b140, 0x80338280
    if not 1 <= len(args) <= 8:
        raise ValueError('Expected one to eight integer argument registers')
    registers[3:3+len(args)] = args
    pc, ctr = min(words), 0
    cr = [False]*32
    lr=0
    if initial_context is not None:
        if len(initial_context)!=42:raise ValueError('Expected 42 integer context words')
        registers[:]=initial_context[:32]
        lr,ctr=initial_context[32:34]
        for field in range(8):
            flags=initial_context[34+field]
            cr[field*4:field*4+3]=[bool(flags&1),bool(flags&2),bool(flags&4)]

    def compare(a, b, field=0):
        cr[field*4:field*4+3] = [a < b, a > b, a == b]

    def snapshot():
        flags=[(int(cr[i*4]) | int(cr[i*4+1])<<1 | int(cr[i*4+2])<<2) for i in range(8)]
        return registers+[lr,ctr]+flags

    def invoke(target):
        nonlocal lr,ctr
        if calls is None and floating_calls is None:raise ValueError('External call boundary unsupported')
        state=snapshot()
        if floating_calls is not None:floating_calls(target,state,floating)
        else:calls(target,state)
        registers[:]=state[:32];lr,ctr=state[32:34]
        for field in range(8):
            flags=state[34+field]
            cr[field*4:field*4+3]=[bool(flags&1),bool(flags&2),bool(flags&4)]

    def finish():
        if final_fpr is not None:final_fpr[:]=floating
        if final_registers is not None:final_registers[:]=registers
        if final_context is not None:final_context[:]=snapshot()
        return registers[3]

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
        if op in (12, 13):
            registers[rt] = (registers[ra]+imm) & MASK
            if op == 13:
                compare(signed(registers[rt]), 0)
        elif op in (14, 15):
            registers[rt] = (base+(imm << (16 if op == 15 else 0))) & MASK
        elif op in (24, 25, 26, 27, 28):
            immediate = w & 0xffff
            if op in (25,27):
                immediate <<= 16
            value = registers[rt]
            registers[ra] = (value & immediate if op == 28 else
                             value ^ immediate if op in (26,27) else value | immediate)
            if op == 28:
                compare(signed(registers[ra]), 0)
        elif op in (48,50,52,54):
            if initial_fpr is None:raise ValueError('Floating transfer context required')
            address=(base+imm)&MASK
            if op==48:
                raw=memory.read(address,4)
                value=struct.unpack('>f',raw.to_bytes(4,'big'))[0]
                if raw&0x7fffffff and not 1<=(raw>>23)&255<=254:
                    raise ValueError('Outside floating transfer domain')
                floating[rt]=int.from_bytes(struct.pack('>d',value),'big')
            elif op==50:
                floating[rt]=(memory.read(address,4)<<32)|memory.read((address+4)&MASK,4)
            elif op==54:
                memory.write(address,floating[rt]>>32,4)
                memory.write((address+4)&MASK,floating[rt]&MASK,4)
            else:
                raw=floating[rt];value=struct.unpack('>d',raw.to_bytes(8,'big'))[0]
                try:packed=struct.pack('>f',value)
                except OverflowError:raise ValueError('Outside floating transfer domain')
                bits=int.from_bytes(packed,'big')
                if (bits&0x7fffffff and not 1<=(bits>>23)&255<=254) or struct.unpack('>f',packed)[0]!=value:
                    raise ValueError('Outside floating transfer domain')
                memory.write(address,bits,4)
        elif op==63 and (w>>1)&1023==72 and not w&1:
            if initial_fpr is None:raise ValueError('Floating transfer context required')
            floating[rt]=floating[rb]
        elif op in (32, 33, 34, 35, 37, 39, 40, 41, 42, 36, 38, 44, 45):
            address = (base+imm) & MASK
            size = {32: 4, 33: 4, 34: 1, 35: 1, 37:4, 39: 1, 40: 2, 41: 2, 42: 2, 36: 4, 38: 1, 44: 2,45:2}[op]
            if op in (36, 37,38, 39, 44,45):
                memory.write(address, registers[rt] & ((1 << (size*8))-1), size)
                if op in (37,39,45):
                    if not ra:
                        raise ValueError('Invalid store-with-update operand')
                    registers[ra] = address
            else:
                value = memory.read(address, size)
                registers[rt] = (signed(value, 16) & MASK) if op == 42 else value
                if op in (33, 35, 41):
                    if not ra or ra == rt:
                        raise ValueError('Invalid load-with-update operands')
                    registers[ra] = address
        elif op in (46,47):
            address=(base+imm)&MASK
            for register in range(rt,32):
                if op==46:registers[register]=memory.read(address,4)
                else:memory.write(address,registers[register],4)
                address=(address+4)&MASK
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
            offset=signed(w&0x03fffffc,26)
            destination=(offset if w&2 else pc+offset)&MASK
            if w&1:
                if destination in words:raise ValueError('Internal linked branch unsupported')
                lr=following;invoke(destination)
            elif destination not in words and (calls is not None or floating_calls is not None):
                invoke(destination);return finish()
            else:
                if w&2:raise ValueError('Absolute/linked branch unsupported')
                following=destination
        elif op==19 and (w>>1)&1023 in (193,289):
            if rt!=ra or rt!=rb or rt%4==3:
                raise ValueError('Unsupported CR boolean operation')
            cr[rt]=((w>>1)&1023)==289
        elif op==19 and (w>>1)&1023==528 and not w&1:
            if rt!=20:raise ValueError('Conditional CTR transfer unsupported')
            target=ctr&~3
            if target in words:following=target
            else:invoke(target);return finish()
        elif op==19 and (w>>1)&1023==528 and w&1:
            target=ctr;lr=following;invoke(target)
        elif op == 16 or (op == 19 and (w >> 1) & 1023 == 16):
            bo, bi = rt, ra
            if w & 1 and not (op==19 and (calls is not None or floating_calls is not None)):
                raise ValueError('Linked branch unsupported')
            if not bo & 4:
                ctr = (ctr-1) & MASK
            take = (bool(bo & 4) or ((ctr != 0) != bool(bo & 2))) and (
                bool(bo & 16) or cr[bi] == bool(bo & 8))
            if take:
                if op == 19:
                    if w&1:
                        target=lr;lr=following;invoke(target)
                    else:return finish()
                else:
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
            elif xo==467 and ((w>>16)&31)==8 and ((w>>11)&31)==0:
                lr=registers[rt]
            elif xo==339 and ((w>>16)&31) in (8,9) and ((w>>11)&31)==0:
                registers[rt]=lr if ((w>>16)&31)==8 else ctr
            elif xo in (23, 87, 279, 151, 215, 407):
                address = (base+registers[rb]) & MASK
                size = 2 if xo in (279, 407) else 1 if xo in (87, 215) else 4
                if xo in (151, 215, 407):
                    memory.write(address, registers[rt] & ((1 << (size*8))-1), size)
                else:
                    registers[rt] = memory.read(address, size)
            elif xo in (266, 40, 8, 235):
                a, b = registers[ra], registers[rb]
                registers[rt] = (a+b if xo == 266 else b-a if xo in (40,8) else a*b) & MASK
                record = bool(w & 1)
                if record:
                    compare(signed(registers[rt]), 0)
            elif xo in (75,459,491):
                a,b=registers[ra],registers[rb]
                if xo==75:value=(signed(a)*signed(b))>>32
                else:
                    if not b or (xo==491 and a==0x80000000 and b==MASK):
                        raise ValueError('Undefined integer division')
                    if xo==459:value=a//b
                    else:
                        a,b=signed(a),signed(b)
                        value=abs(a)//abs(b)
                        if (a<0)!=(b<0):value=-value
                registers[rt]=value&MASK
                if w&1:compare(signed(registers[rt]),0)
            elif xo == 11:
                registers[rt]=(registers[ra]*registers[rb])>>32
                if w&1:compare(signed(registers[rt]),0)
            elif xo == 104:
                registers[rt] = (-registers[ra]) & MASK
                if w & 1:
                    compare(signed(registers[rt]), 0)
            elif xo in (444, 28, 60, 24, 954, 922, 124, 26, 824, 536, 316):
                a, b = registers[rt], registers[rb]
                if xo == 444: value = a | b
                elif xo == 28: value = a & b
                elif xo == 60: value = a & ~b
                elif xo == 24: value = 0 if b & 32 else a << (b & 31)
                elif xo == 124: value = ~(a | b)
                elif xo == 26: value = 32-a.bit_length()
                elif xo == 824: value = signed(a) >> rb
                elif xo == 536: value = 0 if b & 32 else a >> (b & 31)
                elif xo == 316: value = a ^ b
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
