#!/usr/bin/env python3
"""Compare 200 recovered scalar helpers to original PowerPC execution."""
import ctypes as c
import hashlib
import json
from pathlib import Path
import random
import subprocess
import tempfile

from check_runtime_helpers import Runtime, API
from ppc_leaf import execute, load_functions, MASK
from render_scalar_helpers import render, SPECS, SOURCE

ROOT = Path(__file__).resolve().parents[1]
EDGES = (0, 1, 2, 3, 7, 8, 15, 16, 31, 32, 127, 128, 255, 256,
         257, 32767, 32768, 65535, 65536, 0x7fffffff, 0x80000000,
         0x80000001, 0xfffffffe, MASK, 0x55555555, 0xaaaaaaaa)


def default_byte(address, seed, style):
    if style == 0: return 0
    if style == 1: return 255
    if style == 2: return address & 255
    # A deterministic total byte-addressed space: arbitrary chains can be
    # tested without host pointer dereferences or mapped-memory assumptions.
    value = (address ^ seed) & MASK
    value = ((value ^ (value >> 16))*0x45d9f3b) & MASK
    value = ((value ^ (value >> 16))*0x45d9f3b) & MASK
    return (value ^ (value >> 16)) & 255


def read(memory, address, size, seed, style):
    value = int.from_bytes(bytes(memory.data.get((address+i) & MASK,
                                default_byte((address+i) & MASK, seed, style))
                                for i in range(size)), 'big')
    memory.events.append(('read', size, address, value))
    return value


class Memory:
    def __init__(self, seed, style, data):
        self.seed, self.style, self.data = seed, style, dict(data)
        self.events = []

    def read(self, address, size):
        return read(self, address, size, self.seed, self.style)

    def write(self, address, value, size):
        self.events.append(('write', size, address, value))
        for i, byte in enumerate(value.to_bytes(size, 'big')):
            self.data[(address+i) & MASK] = byte


def inputs(address, case):
    rng = random.Random(int(address, 16)+case)
    if case < 26:
        edge = EDGES[case]
        args = (edge, edge, edge, edge)
    elif case < 52:
        edge = EDGES[case-26]
        args = (0x81000000, edge, edge ^ MASK, (edge+1) & MASK)
    elif case < 78:
        # Overlapping input/output pointers and addresses near wrap-around.
        base = (0, 0x81000000, MASK-7)[case % 3]
        args = (base, (base+case % 5) & MASK,
                (base+(case % 3)*4) & MASK, (base-1) & MASK)
    else:
        args = tuple(rng.getrandbits(32) for _ in range(4))
    style = case % 4
    data = {}
    if case >= 78:
        # Seed neighboring byte patterns around arguments, including overlaps.
        for base in args:
            for i in range(24): data[(base+i) & MASK] = rng.getrandbits(8)
    return args, rng.getrandbits(32), style, data


def main():
    specs = json.loads(SPECS.read_text())
    assert specs['function_count'] == len(specs['routines']) == 200
    if SOURCE.read_text() != render(specs):
        raise ValueError('Source and recovered expression specifications disagree')
    addresses = [spec['address'][2:] for spec in specs['routines']]
    assert len(set(addresses)) == 200
    words = load_functions(addresses)
    results = []
    with tempfile.TemporaryDirectory(prefix='tak-scalar-models-') as tmp:
        output = Path(tmp)/'models.dylib'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-dynamiclib',
                        str(SOURCE), '-o', str(output)], check=True)
        library = c.CDLL(str(output))
        for spec, address in zip(specs['routines'], addresses):
            original = words[address]
            assert len(original)*4 == spec['original_bytes']
            # This batch must be straight-line with exactly one final return.
            assert original[max(original)] == 0x4e800020
            assert all((w >> 26) not in (16, 18, 19) for pc, w in original.items() if pc != max(original))
            fn = getattr(library, 'tak_scalar_'+address)
            fn.argtypes = [c.c_uint32]*4+[c.POINTER(API)]; fn.restype = c.c_uint32
            visited = set()
            for case in range(128):
                args, seed, style, data = inputs(address, case)
                oracle = Memory(seed, style, data)
                expected = execute(original, args, oracle, visited=visited)
                native = Runtime(); native.data = dict(data)
                native.read = lambda a, size: read(native, a, size, seed, style)
                actual = fn(*args, c.byref(native.runtime)); native.clean()
                if actual != expected:
                    raise AssertionError(f'{address} case {case}: r3 {actual:08X} != {expected:08X}')
                if native.events != oracle.events:
                    n = next((i for i, pair in enumerate(zip(native.events, oracle.events)) if pair[0] != pair[1]),
                             min(len(native.events), len(oracle.events)))
                    raise AssertionError(f'{address} case {case}: trace {n}: '
                                         f'{native.events[n:n+3]} != {oracle.events[n:n+3]}')
                assert native.data == oracle.data, (address, case, 'final memory differs')
            assert visited == set(original), (address, 'instruction coverage gap')
            results.append({'address': spec['address'], 'original_bytes': spec['original_bytes'],
                            'instructions_verified': len(original), 'instructions_exercised': len(visited),
                            'differential_cases': 128, 'behavior': spec['behavior'],
                            'source': 'src/recovered/scalar_leaf_helpers.c',
                            'return_check': 'Final r3 harness bits; original return type unresolved'})
            print(f'PASS: {address}: 128 original-PPC/C comparisons, full instruction coverage', flush=True)
    summary = {'revision': 'GJUE78 rev 0', 'functions': len(results),
               'original_bytes': sum(r['original_bytes'] for r in results),
               'instructions_verified': sum(r['instructions_verified'] for r in results),
               'instructions_exercised': sum(r['instructions_exercised'] for r in results),
               'differential_cases': sum(r['differential_cases'] for r in results),
               'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               'spec_sha256': hashlib.sha256(SPECS.read_bytes()).hexdigest(),
               'binary_matching': False, 'routines': results}
    (ROOT/'analysis/scalar-helpers-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(f'PASS: {summary["functions"]} complete models, {summary["original_bytes"]} original bytes, '
          f'{summary["differential_cases"]} differential cases')


if __name__ == '__main__': main()
