#!/usr/bin/env python3
"""Render the explicit scalar recovery specifications as ordinary host C.

The specs contain recovered expressions/accesses, never instruction bytes
or an instruction interpreter. This renderer does not establish correctness;
check_scalar_helpers.py independently compares original PPC execution.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'src/recovered/scalar_leaf_helpers.c'
SPECS = ROOT/'analysis/scalar-helper-specs.json'


def render(specs):
    out = ['/* Generated from analysis/scalar-helper-specs.json. See SCALAR_HELPERS.md.',
           ' * Complete straight-line semantic models for GJUE78 rev 0.',
           ' * a..d represent original r3..r6. The harness returns final r3;',
           ' * this does not infer original return types or establish ABI matching.',
           ' * No instruction bytes, assembly, or CPU interpreter are embedded here.',
           ' */', '#include "runtime_helpers.h"', '',
           'static uint32_t leading_zeros(uint32_t value)', '{',
           '    return value ? (uint32_t)__builtin_clz(value) : 32u;', '}', '',
           'static uint32_t sign_byte(uint32_t value)', '{',
           '    value &= 255u;',
           '    return (value & 128u) ? value | UINT32_C(0xffffff00) : value;', '}', '',
           'static uint32_t shift_signed(uint32_t value, unsigned amount)', '{',
           '    if (!amount) return value;',
           '    uint32_t fill = (value & UINT32_C(0x80000000)) ? ~(UINT32_MAX >> amount) : 0;',
           '    return (value >> amount) | fill;', '}', '']
    # Helpers are emitted only when referenced, keeping strict -Wunused-function.
    texts = '\n'.join('\n'.join(s['statements'])+'\n'+s['result'] for s in specs['routines'])
    for name, end in [('leading_zeros', 'sign_byte'), ('sign_byte', 'shift_signed'), ('shift_signed', None)]:
        if name+'(' not in texts:
            start = next(i for i, line in enumerate(out) if line.startswith('static uint32_t '+name+'('))
            stop = start+1
            while out[stop] != '}': stop += 1
            del out[start:stop+2]
    for spec in specs['routines']:
        a = spec['address'][2:]
        out += [f'/* {spec["behavior"]}; {spec["original_bytes"]} original bytes. */',
                f'uint32_t tak_scalar_{a}(uint32_t a, uint32_t b, uint32_t c, uint32_t d,',
                '                              const TakTarget *m)', '{',
                '    (void)a; (void)b; (void)c; (void)d; (void)m;']
        out += ['    '+line for line in spec['statements']]
        out += ['    return '+spec['result']+';', '}', '']
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    source = render(json.loads(SPECS.read_text()))
    if args.write:
        SOURCE.write_text(source)
    elif SOURCE.read_text() != source:
        raise SystemExit('Scalar source differs from specifications; run with --write')
    print('PASS: scalar C source agrees with explicit recovered specifications')


if __name__ == '__main__': main()
