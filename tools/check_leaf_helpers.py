#!/usr/bin/env python3
"""Differentially check 70 C routines against verified original PPC words."""
import ctypes as c
import json
from pathlib import Path
import random
import re
import subprocess
import tempfile

from check_runtime_helpers import Runtime
from ppc_leaf import execute, load_functions, MASK, signed

ROOT = Path(__file__).resolve().parents[1]
# Each entry is one indexed original region; void results are not compared.
CASES = {
    '8015C924': (False, 'Store three object fields'),
    '80160D8C': (True, 'Find a nonzero byte in a NUL-terminated string'),
    '80160DC0': (True, 'Skip spaces and tabs'),
    '80162950': (True, 'Select string address using byte +0x44'),
    '80162B00': (True, 'Select string address using byte +0x40'),
    '80162B9C': (True, 'Select alternate string address using byte +0x40'),
    '80162C38': (True, 'Select third string pair using byte +0x40'),
    '8016332C': (False, 'Set indirect owner byte +0x11'),
    '801633B0': (True, 'Advance signed index and fetch array item'),
    '80167CCC': (False, 'Clear object fields +0x10F8/+0x10FC'),
    '8016BBF8': (True, 'Initialize sparse zero-word fields and return object'),
    '8017860C': (False, 'Append a word pair if signed count permits'),
    '80178A94': (True, 'Return member address unless pointer already present'),
    '80179B98': (True, 'Advance iterator and return member while in range'),
    '80179BC4': (True, 'Fetch indirect table item'),
    '8017A52C': (False, 'Initialize pointer and zero word pair'),
    '8017B30C': (True, 'Insert into first free slot of 256-slot registry'),
    '8017B358': (True, 'Clear occupied registry slot using low-byte index'),
    '8017BDE0': (True, 'Clear two words and return object'),
    '8017DAC0': (True, 'Read indexed global table word'),
    '8017E6F0': (False, 'Remove matching values with stable in-place compaction'),
    '801809FC': (True, 'Initialize object table pointer and sparse defaults'),
    '80184564': (False, 'Set bits in global flags'),
    '80184574': (False, 'Clear bits in global flags'),
    '8018580C': (False, 'Publish shifted size plus constant'),
    '80185C6C': (False, 'Initialize zero/sentinel object fields'),
    '801862C0': (False, 'Request table entry when not flagged'),
    '801862E8': (True, 'Read table entry word +4'),
    '8018640C': (False, 'Set table entry flag byte'),
    '80186428': (False, 'Clear table entry flag byte'),
    '80186444': (True, 'Read table entry flag byte'),
    '80186664': (True, 'Read four little-endian bytes'),
    '80186688': (False, 'Write four little-endian bytes'),
    '801866AC': (False, 'Publish table value and clear request word'),
    '801866CC': (False, 'Publish global value and clear adjacent word'),
    '80186B20': (False, 'Request two-index table entry if not flagged'),
    '80186CC8': (True, 'Read two-index table entry word'),
    '80186D28': (False, 'Set two-index table entry flag'),
    '80186D4C': (False, 'Clear seven flags per table row'),
    '80188564': (False, 'Write global magic word'),
    '801885CC': (False, 'Write global byte'),
    '801885DC': (False, 'Copy four bytes to first global destination'),
    '80188608': (False, 'Write global word'),
    '80188628': (False, 'Copy four bytes to second global destination'),
    '80188654': (False, 'Select global mode 2/3 using low argument byte'),
    '80188834': (False, 'Publish global word and enable flag'),
    '8018B424': (False, 'Copy or clear object byte pair using low argument byte'),
    '8018B450': (False, 'Select object mode 2/3 using low argument byte'),
    '8018B558': (False, 'Store word pair and clear object byte'),
    '8018C40C': (True, 'Read global byte'),
    '8018C41C': (False, 'Write global byte'),
    '8018C4F8': (True, 'Read current global pointer'),
    '8018C510': (True, 'Read indexed halfword through object table pointer'),
    '8018C8A4': (False, 'Snapshot two global words'),
    '8018CC3C': (False, 'Resolve record halfwords via default or signed index'),
    '8018CC98': (True, 'Read default global halfword'),
    '8018CE48': (True, 'Read global halfword +0x30'),
    '8018CE58': (True, 'Read global halfword +0x2E'),
    '8018CE78': (True, 'Read global halfword +0x32'),
    '8018CE88': (True, 'Read global halfword +0x34'),
    '8018CE98': (False, 'Clear global halfword +0x32'),
    '8018CEAC': (False, 'Write global halfword +0x30'),
    '8018CEBC': (False, 'Enable global halfword and publish halfword +0x2E'),
    '8018D6BC': (False, 'Set/clear bit one throughout linked list'),
    '8018DE8C': (False, 'Clear byte through argument object pointer'),
    '8018F74C': (True, 'Fetch array item with negative-index last-item behavior'),
    '80195AF4': (True, 'Find first linked node with matching word'),
    '8019D194': (True, 'Calculate two-dimensional 224-byte record address'),
    '801A0C10': (True, 'Calculate two-dimensional halfword address'),
    '801AE384': (True, 'Append nonnull doubly-linked node and increment count'),
}


class Memory:
    """Synthetic big-endian target memory; unmapped bytes read as zero.

    No host dereferencing occurs. Zero default deliberately models a total
    address space, not GameCube access faults or pointer validity.
    """
    def __init__(self, data=None):
        self.data = dict(data or {})
        self.events = []

    def put(self, a, value, size=4):
        for i, byte in enumerate((value & ((1 << (size*8))-1)).to_bytes(size, 'big')):
            self.data[(a+i) & MASK] = byte

    def load(self, a, raw):
        for i, byte in enumerate(raw): self.data[(a+i) & MASK] = byte

    def read(self, a, size):
        self.events.append(('read', size, a))
        return int.from_bytes(bytes(self.data.get((a+i) & MASK, 0) for i in range(size)), 'big')

    def write(self, a, value, size):
        self.events.append(('write', size, a, value))
        self.put(a, value, size)


def fixture(address, case):
    rng = random.Random(int(address, 16)+case)
    t = Memory()
    a, b, c0, d = 0x81000000, 0x82000000, 0x83000000, 0x84000000
    owner, table = 0x85000000, 0x86000000
    # Random neighboring bytes expose excessive stores and width mistakes.
    for base in (a, b, c0, d, owner, table, 0x8031a778, 0x8031a900,
                 0x8031b090, 0x802eb678, 0x80332cb0):
        t.load(base, rng.randbytes(0x300))
    edge = (0, 1, 2, 3, 255, 256, 257, 0x7fffffff, 0x80000000, MASK)[case % 10]
    scalar_a = {'8017B358', '8017DAC0', '80184564', '80184574', '8018580C',
                '801862C0', '801862E8', '8018640C', '80186428', '80186444',
                '801866AC', '801866CC', '80186B20', '80186CC8', '80186D28',
                '801885CC', '80188608', '80188654', '80188834', '8018C41C',
                '8018CEAC', '8018CEBC', '8018D6BC'}
    if address in scalar_a: a = edge
    if address in ('80186B20', '80186CC8', '80186D28'): b = case % 8
    if address in ('8015C924', '8017A52C', '801866AC', '80186688', '8018B558'):
        b = edge
    if address == '80160D8C':
        a = (0, 32, 9, 65, 127, 128, 255, 0x141)[case % 8]
        t.load(b, (b'', b'A', b'\xff\x80A', b' \tQ', b'\x7f')[case % 5]+b'\0')
    if address == '80160DC0':
        t.load(a, (b'', b' ', b'\t\t  ', b'\n ', b' \t\xff')[case % 5]+b'\0')
    if address in ('80162950', '80162B00', '80162B9C', '80162C38'):
        t.put(a+(0x44 if address == '80162950' else 0x40), edge, 1)
    if address == '8016332C': t.put(a+0x28, owner)
    if address == '801633B0':
        t.put(a+0x28, owner); t.put(b, edge); t.put(owner+4, 3); t.put(owner, table)
        for i in range(-1, 4): t.put(table+4*i, rng.getrandbits(32))
        if case >= 20:
            # Index store aliases object pointer, enabling the original late
            # failure path and proving the object pointer is reloaded.
            b = a+0x28; t.put(b, 0x1000); t.put(0x1004, 0x7fffffff)
    if address == '8017860C':
        b, c0 = edge, rng.getrandbits(32)
        t.put(a, table if case < 20 else a); t.put(a+8, case % 5)
        t.put(a+4, (0, 3, 0x80000000, MASK)[case % 4])
    if address == '80178A94':
        b = 0 if case % 5 == 0 else edge
        t.put(a+0x40, 0 if case % 7 == 0 else owner)
        t.put(owner+0x18, (0, 3, MASK, 0x80000000)[case % 4]); t.put(owner+0x20, table)
        for i in range(3): t.put(table+i*4, b if i == case % 4 else rng.getrandbits(32))
    if address == '80179B98':
        t.put(a+0x58, edge); t.put(a+0x54, owner); t.put(owner+0x18, case % 5)
    if address == '80179BC4':
        t.put(a+8, owner); t.put(a+0xc, edge); t.put(owner+0x20, table)
        t.put((table+edge*4) & MASK, rng.getrandbits(32))
    if address == '8017B30C':
        for i in range(256): t.put(0x802eae88+4*i, 0 if i == (0, 1, 255, 256)[case % 4] else i+1)
        a = edge
    if address == '8017B358': t.put((0x802eae88+(a & 255)*4) & MASK, 0 if case % 2 else 42)
    if address == '8017DAC0': t.put((0x8031a6b4+a*24) & MASK, rng.getrandbits(32))
    if address == '8017E6F0':
        a = edge; t.put(0x80332cbc, (0, 1, 6, MASK)[case % 4])
        for i in range(6): t.put(0x8031a8ec+4*i, a if (case+i) % 3 else i+17)
    if address in ('801862C0', '801862E8', '8018640C', '80186428', '80186444', '801866AC'):
        entry = (0x8031a778+a*12) & MASK
        t.put(entry+8, edge, 1); t.put(entry+4, rng.getrandbits(32)); t.put(entry, rng.getrandbits(32))
    if address in ('80186B20', '80186CC8', '80186D28'):
        entry = (0x8031a900+a*0x54+b*12) & MASK
        t.put(entry+8, edge, 1); t.put(entry, rng.getrandbits(32)); t.put(entry+4, rng.getrandbits(32))
    if address == '80186D4C': t.put(0x80332cc8, (0, 1, 3, MASK)[case % 4])
    if address in ('801885DC', '80188628') and case >= 16:
        dest = 0x802eb69d if address == '801885DC' else 0x802eb6ac
        a = dest + (case % 3)-1
    if address in ('8018B424', '8018B450'): b = edge
    if address == '8018C510':
        b = edge; t.put(a+0x2c, table); t.put((table+b*2) & MASK, rng.getrandbits(16), 2)
    if address == '8018CC3C':
        t.put(a+4, case % 4, 1); t.put(0x8031b154, owner); t.put(owner+0x2c, table)
        for i in range(3):
            index = (0, 1, 0xffff)[i]; t.put(a+6+i*0x28, index, 2)
            t.put(a+13+i*0x28, 16 if (case+i) % 2 else 0, 1)
            t.put((table+signed(index, 16)*2) & MASK, rng.getrandbits(16), 2)
    if address == '8018D6BC':
        t.put(0x8031b160, owner if case % 4 else 0)
        for i in range(3):
            node = owner+i*0x100
            t.put(node, node+0x100 if i < 2 else 0); t.put(node+0xe, rng.getrandbits(16), 2)
    if address == '8018DE8C': t.put(b+0x94, owner)
    if address == '8018F74C':
        b = edge; t.put(a, owner); t.put(owner+4, case % 5); t.put(owner, table)
        index = (case % 5)-1 if edge & 0x80000000 else edge
        t.put((table+index*4) & MASK, rng.getrandbits(32))
    if address == '80195AF4':
        b = edge; t.put(a+4, 0 if case % 4 == 0 else owner)
        for i in range(3):
            node = owner+i*0x400
            t.put(node+0x40, b if i == case % 4 else rng.getrandbits(32))
            t.put(node+0x398, node+0x400 if i < 2 else 0)
    if address in ('8019D194', '801A0C10'):
        b, c0 = edge, rng.getrandbits(32)
    if address == '801AE384':
        b = (0, owner, owner, a, a+4)[case % 5]
        t.put(a, 0 if case % 3 else table); t.put(a+4, table); t.put(a+0xc, edge)
    # Include unsigned address wrap for direct memory helpers.
    if address in ('80186664', '80186688', '8015C924', '80167CCC') and case >= 20:
        a = MASK-1
    return t, (a, b, c0, d)


def main():
    assert len(CASES) == 70
    words = load_functions(CASES)
    source = (ROOT/'src/recovered/leaf_helpers.c').read_text()
    assert set(re.findall(r'^FN\(([0-9A-F]{8})\)', source, re.M)) == set(CASES)
    with tempfile.TemporaryDirectory(prefix='tak-leaves-') as tmp:
        library = Path(tmp)/'leaves.dylib'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-dynamiclib',
                        str(ROOT/'src/recovered/leaf_helpers.c'), '-o', str(library)], check=True)
        lib = c.CDLL(str(library))
        from check_runtime_helpers import API
        results = []
        for address, (returns, description) in CASES.items():
            fn = getattr(lib, 'tak_leaf_'+address)
            fn.argtypes = [c.c_uint32]*4+[c.POINTER(API)]
            fn.restype = c.c_uint32
            count = 0
            visited = set()
            for case in range(24):
                initial, args = fixture(address, case)
                oracle = Memory(initial.data)
                expected = execute(words[address], args, oracle, visited=visited)
                native = Runtime()
                native.data = dict(initial.data)
                # Synthetic space has zero-valued unmapped bytes in both runs.
                native.read = lambda a, size: Memory.read(native, a, size)
                actual = fn(*args, c.byref(native.runtime))
                native.clean()
                if returns and actual != expected:
                    raise AssertionError(f'{address} case {case}: return {actual:08X} != {expected:08X}')
                if native.events != oracle.events:
                    n = next((i for i, pair in enumerate(zip(native.events, oracle.events)) if pair[0] != pair[1]),
                             min(len(native.events), len(oracle.events)))
                    raise AssertionError(f'{address} case {case}: trace at {n}: '
                                         f'{native.events[n:n+3]} != {oracle.events[n:n+3]}')
                assert native.data == oracle.data, (address, case, 'memory differs')
                count += 1
            # 0x8018D6F0 is an unreachable branch immediately after blr;
            # all other original instructions must execute in these cases.
            allowed_unvisited = {0x8018d6f0} if address == '8018D6BC' else set()
            assert set(words[address])-visited == allowed_unvisited, (address, 'coverage gap')
            results.append({'address': '0x'+address, 'original_bytes': len(words[address])*4,
                            'instructions_verified': len(words[address]), 'behavior': description,
                            'instructions_exercised': len(visited),
                            'unexercised_addresses': [f'0x{pc:08X}' for pc in sorted(set(words[address])-visited)],
                            'return_checked': returns, 'differential_cases': count,
                            'source': 'src/recovered/leaf_helpers.c'})
            print(f'PASS: {address}: {count} original-PPC/C differential cases', flush=True)
        summary = {'revision': 'GJUE78 rev 0', 'functions': len(results),
                   'original_bytes': sum(r['original_bytes'] for r in results),
                   'instructions_verified': sum(r['instructions_verified'] for r in results),
                   'differential_cases': sum(r['differential_cases'] for r in results),
                   'binary_matching': False, 'routines': results}
        (ROOT/'analysis/leaf-helpers-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print(f'PASS: {summary["functions"]} functions, {summary["original_bytes"]} original bytes, '
              f'{summary["differential_cases"]} differential cases')


if __name__ == '__main__':
    main()
