#!/usr/bin/env python3
"""Differential checks for 100 complete resource/state leaf models."""
import ctypes as c
import json
from pathlib import Path
import random
import re
import subprocess
import tempfile

from check_leaf_helpers import Memory
from check_runtime_helpers import Runtime, API
from ppc_leaf import execute, load_functions, MASK

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    '801A1798': (True, 'Initialize sparse object fields'),
    '801A1C30': (True, 'Set nonnull object byte +0xF4'),
    '801A1C50': (True, 'Clear nonnull object byte +0xF4'),
    '801A1C70': (True, 'Read object byte +0xF4 with null default one'),
    '801A2210': (False, 'Set halfword flag bit zero'),
    '801A2220': (False, 'Clear halfword flag bit zero'),
    '801AE290': (True, 'Initialize pointer pair, byte and count'),
    '801B0170': (False, 'Replace first word preserving difference of pair'),
    '801B3660': (True, 'Initialize sparse fields with enabled byte'),
    '801B5620': (False, 'Clear word through nonnull pointer'),
    '801B6A14': (False, 'Clear first global iterator'),
    '801B6A28': (False, 'Clear second global iterator'),
    '801B6A3C': (False, 'Advance first cursor only when it matches input'),
    '801B6A5C': (False, 'Advance second cursor only when it matches input'),
    '801B6A7C': (True, 'Start halfword-filtered iteration and yield value'),
    '801B6ADC': (True, 'Continue halfword-filtered iteration and yield value'),
    '801B72EC': (False, 'OR global flags'),
    '801B7300': (False, 'Push flags onto inline stack without bounds check'),
    '801B7328': (False, 'Pop inline flag stack without underflow check'),
    '801B7350': (True, 'Return inline string if flag and first byte permit'),
    '801B8778': (True, 'Read first halfword with null default zero'),
    '801B8790': (True, 'Read second halfword with null default zero'),
    '801B8A9C': (False, 'Write global byte'),
    '801B8B30': (False, 'Set byte flag bit six through nonnull object'),
    '801B8C64': (True, 'Initialize global base/cursor/size'),
    '801B976C': (False, 'Clear halfword flag bit zero'),
    '801B977C': (False, 'Set halfword flag bit zero'),
    '801B99C8': (True, 'Read direct or indexed resource pointer'),
    '801B99FC': (False, 'Publish resource pointer into selected output word'),
    '801BA5E0': (False, 'Toggle paired byte/halfword flag masks'),
    '801BB8E8': (True, 'Initialize sparse word and byte fields'),
    '801BCF90': (False, 'Merge global byte flags into object'),
    '801BD24C': (True, 'Calculate address through nested indexed records'),
    '801BEFE0': (True, 'Calculate indexed record address through owner'),
    '801C235C': (False, 'Store field across signed-count record array'),
    '801C275C': (False, 'Write indexed pointer table entry'),
    '801C3284': (True, 'Find value in linked list and return boolean'),
    '801C3A88': (True, 'Insert in first zero word among supplied count'),
    '801C3ABC': (True, 'Read pointer using masked 16-bit index'),
    '801C3ACC': (True, 'Count bits in low 16 bits'),
    '801C3B54': (False, 'Prepend node and set owner'),
    '801C3B68': (False, 'Unlink owned node and clear owner'),
    '801C3BB8': (True, 'Find first value in owned linked list'),
    '801C3EEC': (True, 'Invert word flag bit thirty'),
    '801C4FAC': (True, 'Calculate type-dependent 16/32-byte aligned address'),
    '801C5378': (True, 'Scan bit pattern with first-zero and later-one rules'),
    '801C63A4': (True, 'Clear header flag and publish payload/size'),
    '801C8BC4': (True, 'Find masked halfword key in linked list'),
    '801CACD4': (True, 'Collect matching flagged nodes into output array'),
    '801CB534': (True, 'Read current global pointer'),
    '801CB550': (True, 'Return current member pointer or null'),
    '801CB7C4': (True, 'Postincrement word and reload old result'),
    '801CBA5C': (True, 'Return global member address'),
    '801CBB60': (False, 'Clear global byte'),
    '801CC83C': (False, 'Set global byte if a linked node has both flags'),
    '801CD000': (False, 'Initialize three fields, cursor, and enabled byte'),
    '801CD280': (True, 'Find word key in singly-linked list'),
    '801CDB38': (False, 'Write global byte'),
    '801CE658': (True, 'Return first matching global slot index or three'),
    '801CE720': (False, 'Write global word'),
    '801CFEE8': (True, 'Find masked halfword key through linked nodes'),
    '801CFF24': (False, 'Write first global word'),
    '801CFF34': (False, 'Write second global word'),
    '801D8C44': (False, 'Write global byte'),
    '801D8C60': (False, 'Enable indexed entry and publish word pair'),
    '801D8C84': (False, 'Clear indexed entry byte and word pair'),
    '801D8DE4': (False, 'Write alternate global byte'),
    '801D8F30': (True, 'Read global byte'),
    '801D90A4': (False, 'Write global word'),
    '801D9224': (True, 'Read global flag bit seven'),
    '801D928C': (True, 'Read global word'),
    '801D929C': (False, 'Write another global byte'),
    '801DA394': (True, 'Select first global node or find node with matching kind'),
    '801DA3DC': (True, 'Select next node or next node with matching kind'),
    '801DA410': (True, 'Return global object member pointer or null'),
    '801DB0EC': (False, 'Toggle object flag bit twenty-eight using low byte'),
    '801DB114': (False, 'Toggle object high flag bit using low byte'),
    '801DB5B8': (True, 'Pop global list and return inline member'),
    '801DB750': (False, 'Write global byte'),
    '801DB8A0': (False, 'Clear global word'),
    '801DCD90': (False, 'Enable global list updates'),
    '801DCDA4': (False, 'Disable global list updates'),
    '801DCE50': (False, 'Replace matching list values when globally enabled'),
    '801DEC18': (False, 'Clear global pointer pair if first matches input'),
    '801DF2C0': (False, 'Clear flag bit six on nodes matching halfword key'),
    '801DF2FC': (False, 'Set flag bit six on nodes matching halfword key'),
    '801E0C2C': (False, 'Clear ten sparse object words'),
    '801E1CE8': (False, 'Set object flag bit three'),
    '801E4E08': (True, 'Read indexed slot member with null default zero'),
    '801E5530': (False, 'Resolve slot-relative offset and clear slot field'),
    '801E5878': (True, 'Find object key through global list'),
    '801E58C0': (True, 'Test four slots without short circuiting reads'),
    '801E5910': (False, 'Write indexed nonnull slot byte five'),
    '801E6228': (False, 'Write indexed nonnull slot byte six'),
    '801E6244': (False, 'Write indexed nonnull slot byte seven'),
    '801E6260': (True, 'Read signed slot byte six or return minus one'),
    '801E6288': (True, 'Read signed slot byte seven or return minus one'),
    '801E6688': (True, 'Conditionally skip stream word and set owner flag'),
    '801E66CC': (True, 'Conditionally skip stream word and clear owner flag'),
    '801E6710': (True, 'Conditionally skip stream word and decrement slot byte'),
}


def fixture(address, case):
    rng = random.Random(int(address, 16)+case)
    t = Memory()
    a, b, c0, d = 0x81000000, 0x82000000, 0x83000000, 0x84000000
    owner, table, node0 = 0x85000000, 0x86000000, 0x87000000
    edges = (0, 1, 2, 3, 255, 256, 257, 0x7fffffff, 0x80000000, MASK,
             0xffff, 0x10000, 0x55555555, 0xaaaaaaaa, 0x8001, 0xffff0000)
    edge = edges[case % len(edges)]
    for base in (a, b, c0, d, owner, table, 0x80322d78, 0x80322f90,
                 0x803230d4, 0x803236e0, 0x80323834, 0x80323900):
        t.load(base, rng.randbytes(0x400))

    def chain(head_address, next_offset, key_offset, key, half=False, flags=False):
        t.put(head_address, 0 if case % 5 == 0 else node0)
        for i in range(3):
            node = node0+i*0x400
            t.put(node+next_offset, node+0x400 if i < 2 else 0)
            if key_offset is not None:
                value = key if i == case % 4 else (key+17+i)
                t.put(node+key_offset, value, 2 if half else 4)
            if flags: t.put(node+8, rng.getrandbits(32))

    scalar = {'801B6A7C', '801B72EC', '801B8A9C', '801B8C64', '801C3ACC',
              '801C5378', '801C8BC4', '801CDB38', '801CE658', '801CE720',
              '801CFEE8', '801CFF24', '801CFF34', '801D8C44', '801D8C60',
              '801D8C84', '801D8DE4', '801D90A4', '801D929C', '801DA394',
              '801DB750', '801DCE50', '801DF2C0', '801DF2FC'}
    if address in scalar: a = edge
    if address in ('801A1C30', '801A1C50', '801A1C70'): b = 0 if case % 3 == 0 else b
    if address in ('801B5620', '801B8778', '801B8790', '801B8B30') and case % 3 == 0: a = 0
    if address in ('801A2210', '801A2220', '801B976C', '801B977C', '801B7350'):
        t.put(a+2, edge, 2); t.put(a+0xa, case % 3, 1)
    if address in ('801B0170', '801D8C60', '801DCE50'): b = edge
    if address in ('801B6A3C', '801B6A5C'):
        current = 0 if case % 3 == 0 else node0
        t.put(0x80322dac if address == '801B6A3C' else 0x80322db4, current)
        a = current if case % 2 == 0 else current+4
        t.put(current, table)
    if address in ('801B6A7C', '801B6ADC'):
        wanted = edge & 0xffff
        chain(0x80322d88, 0, 8, wanted, half=True)
        # Both start and continuation can inspect the same varied chain.
        t.put(0x80322dac, 0 if case % 5 == 0 else node0)
        t.put(0x80322db0, wanted, 2)
        for i in range(3): t.put(node0+i*0x400+4, rng.getrandbits(32))
    if address in ('801B7300', '801B7328'):
        depth = (0, 1, 2, 3, 4, MASK)[case % 6]
        t.put(0x80322e10, depth); t.put(0x80322e00, edge)
        if address == '801B7328': t.put((0x80322e04+(depth-1)*4) & MASK, rng.getrandbits(32))
    if address == '801B99C8':
        b = edge; t.put(a+2, 4 if case % 2 else 0, 2); t.put(a+0x78, table)
        t.put((table+b*4) & MASK, rng.getrandbits(32))
    if address == '801B99FC':
        t.put(a+2, 4 if case % 2 else 0, 2); t.put(a+0x78, table)
        if case >= 24: b = a+0x78+(case % 3)-1
    if address in ('801BA5E0', '801DB0EC', '801DB114'): b = edge
    if address == '801BD24C':
        b = edge; t.put(a+0xc, table); t.put((table+b*0x24) & MASK, node0)
        t.put(node0, owner); t.put(node0+4, rng.getrandbits(32)); t.put(owner, d)
        t.put(d+0x24, rng.getrandbits(32)); t.put(d+0x2c, rng.getrandbits(32))
    if address == '801BEFE0': b = edge; t.put(a+4, owner); t.put(owner+4, table)
    if address == '801C235C':
        b = edge; t.put(a+4, (0, 1, 3, MASK)[case % 4]); t.put(a+0xc, table)
        for i in range(3): t.put(table+i*0xb0+0x78, node0+i*0x400)
        if case >= 24:
            # First store aliases count and terminates the loop.
            b = 0; t.put(a+4, 3); t.put(table+0x78, a+4-0x40)
    if address == '801C275C':
        b, c0 = edge, rng.getrandbits(32); t.put(a+8, table)
    if address in ('801C3284', '801C3BB8', '801CD280'):
        b = edge
        head_offset, next_offset, key_offset = ((8, 8, 0) if address == '801C3284' else
                                               (4, 8, 0) if address == '801C3BB8' else (0, 0, 4))
        chain(a+head_offset, next_offset, key_offset, b)
    if address == '801C3A88':
        c0 = (0, 1, 4)[case % 3]; b = edge
        for i in range(4): t.put(a+i*4, 0 if i == case % 5 else i+1)
    if address == '801C3ABC':
        b = edge; t.put(a+4, table); t.put(table+(b & 0xffff)*4, rng.getrandbits(32))
    if address == '801C3B54' and case >= 24: b = a+(case % 4)*4
    if address == '801C3B68':
        # Every unlink input is a member; absent nodes do not terminate.
        a = node0+(case % 3)*0x400
        t.put(a+0xc, owner); t.put(owner+4, node0)
        for i in range(3): t.put(node0+i*0x400+8, node0+(i+1)*0x400 if i < 2 else 0)
    if address == '801C3EEC': t.put(a+0x14, edge)
    if address == '801C4FAC':
        t.put(a, (0xe, 0x13, 0, 0xff)[case % 4], 1)
        t.put(a+0x8c, edge); t.put(a+0x90, rng.getrandbits(32))
    if address == '801C63A4' and case >= 24:
        c0 = b+4; d = b+(case % 3)*4
    if address in ('801C8BC4', '801CFEE8'):
        if address == '801C8BC4': chain(0x80322f9c, 0x84, 8, edge & 0xffff, half=True)
        else: chain(0x803231a0, 0xb4, 0xb8, edge & 0xffff, half=True)
    if address == '801CACD4':
        b = (0, 1, 2, 0x200, 0xffff)[case % 5]
        chain(0x80322f9c, 0x84, None, 0)
        t.put(0x80322fb8, table)
        for i in range(3): t.put(node0+i*0x400+2, (0, 0x201, 0x202, 0xffff)[(case+i) % 4], 2)
        if case >= 24: t.put(0x80322fb8, 0x80322fbc)  # result aliases count
    if address in ('801CB534', '801CB550'): t.put(0x80322fc0, 0 if case % 2 else edge)
    if address == '801CB7C4': t.put(a+4, edge)
    if address == '801CC83C':
        chain(0x80322fec, 0, 4, edge)
        for i in range(3): t.put(node0+i*0x400+4, (0, 1, 8, 9)[(case+i) % 4])
    if address == '801CE658':
        for i in range(3): t.put(0x803231e0+4*i, a if i == case % 4 else a+i+1)
    if address in ('801D8C60', '801D8C84'):
        entry = (0x803236e0+a*12) & MASK
        t.load(entry, rng.randbytes(12))
    if address == '801D9224': t.put(0x8032374c, edge)
    if address in ('801DA394', '801DA3DC'):
        key = a if address == '801DA394' else edge
        head_address = 0x80323844 if address == '801DA394' else a
        if address == '801DA3DC': b = edge
        chain(head_address, 0, 0x2f8, key)
    if address in ('801DA410', '801DB5B8'):
        t.put(0x80323868 if address == '801DA410' else 0x80323864, 0 if case % 3 == 0 else node0)
        t.put(node0, table)
    if address == '801DCE50':
        a = edge; t.put(0x80323924, case % 2, 1); chain(0x80323910, 0, 4, a)
    if address == '801DEC18':
        a = edge; t.put(0x80323958, a if case % 2 else a+1)
    if address in ('801DF2C0', '801DF2FC'):
        chain(0x80323948, 0, 0x12, a & 0xffff, half=True, flags=True)
    if address.startswith('801E') and address not in ('801E0C2C', '801E1CE8'):
        b = case % 4; t.put(a+b*4+0xf0, 0 if case % 3 == 0 else node0)
        t.load(node0, rng.randbytes(0x40)); t.put(node0+0x1c, owner)
        t.put(owner+0x20, table); t.put(owner+0x38, 0 if case % 4 == 0 else edge)
        t.put(c0, edge); t.put((table+c0*4) & MASK, rng.getrandbits(32))
        t.put(node0+6, edge, 1); t.put(node0+7, edge, 1); t.put(node0+8, edge, 1)
        if case >= 24 and address in ('801E6688', '801E66CC', '801E6710'):
            # Cursor stores alias owner flags, slot pointer, or slot byte.
            c0 = (a+0x110, a+b*4+0xf0, node0+8)[case % 3]
            t.put(c0, edge)
    if address == '801E58C0':
        for i in range(4): t.put(a+0xf0+4*i, node0 if case & (1 << i) else 0)
    if address == '801E5878':
        a = edge; t.put(0x80332fd0, owner); chain(owner+0x18, 0x18, None, 0)
        for i in range(3):
            node = node0+i*0x400; obj = table+i*0x400
            t.put(node+4, obj); t.put(obj+0x13c, a if i == case % 4 else a+i+1)
    # Target address wrapping in straightforward object operations.
    if address in ('801A1798', '801AE290', '801B3660', '801BB8E8', '801E0C2C') and case >= 24:
        a = MASK-3
    return t, (a, b, c0, d)


def main():
    assert len(CASES) == 100
    words = load_functions(CASES)
    source = (ROOT/'src/recovered/resource_leaf_helpers.c').read_text()
    assert set(re.findall(r'^FN\(([0-9A-F]{8})\)', source, re.M)) == set(CASES)
    with tempfile.TemporaryDirectory(prefix='tak-resource-leaves-') as tmp:
        output = Path(tmp)/'models.dylib'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-dynamiclib',
                        str(ROOT/'src/recovered/resource_leaf_helpers.c'), '-o', str(output)], check=True)
        library = c.CDLL(str(output))
        results = []
        for address, (returns, description) in CASES.items():
            fn = getattr(library, 'tak_resource_leaf_'+address)
            fn.argtypes = [c.c_uint32]*4+[c.POINTER(API)]; fn.restype = c.c_uint32
            visited = set()
            for case in range(32):
                initial, args = fixture(address, case)
                original = Memory(initial.data)
                expected = execute(words[address], args, original, visited=visited)
                native = Runtime(); native.data = dict(initial.data)
                native.read = lambda a, size: Memory.read(native, a, size)
                actual = fn(*args, c.byref(native.runtime)); native.clean()
                if returns and actual != expected:
                    raise AssertionError(f'{address} case {case}: result {actual:08X} != {expected:08X}')
                if native.events != original.events:
                    index = next((i for i, pair in enumerate(zip(native.events, original.events)) if pair[0] != pair[1]),
                                 min(len(native.events), len(original.events)))
                    raise AssertionError(f'{address} case {case}: trace {index}: '
                                         f'{native.events[index:index+3]} != {original.events[index:index+3]}')
                assert native.data == original.data, (address, case, 'final memory differs')
            unvisited = sorted(set(words[address])-visited)
            # The node is already known nonnull at this instruction's
            # predecessor, so the restart load at 0x801E58AC is unreachable.
            allowed = [0x801e58ac] if address == '801E5878' else []
            assert unvisited == allowed, (address, 'instruction coverage gap', unvisited)
            results.append({'address': '0x'+address, 'original_bytes': len(words[address])*4,
                            'instructions_verified': len(words[address]), 'instructions_exercised': len(visited),
                            'unexercised_addresses': [f'0x{pc:08X}' for pc in unvisited],
                            'return_checked': returns, 'differential_cases': 32, 'behavior': description,
                            'source': 'src/recovered/resource_leaf_helpers.c'})
            print(f'PASS: {address}: 32 original-PPC/C cases; {len(visited)}/{len(words[address])} instructions exercised', flush=True)
        summary = {'revision': 'GJUE78 rev 0', 'functions': len(results),
                   'original_bytes': sum(r['original_bytes'] for r in results),
                   'instructions_verified': sum(r['instructions_verified'] for r in results),
                   'instructions_exercised': sum(r['instructions_exercised'] for r in results),
                   'differential_cases': sum(r['differential_cases'] for r in results),
                   'binary_matching': False, 'routines': results}
        (ROOT/'analysis/resource-leaf-helpers-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(f'PASS: {summary["functions"]} complete models, {summary["original_bytes"]} original bytes, '
              f'{summary["differential_cases"]} differential cases')


if __name__ == '__main__': main()
