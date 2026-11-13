#!/usr/bin/env python3
"""Follow only the cmpwi/branch decision tree in the verified type dispatcher."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
assembly = (root/'analysis/reports/fn_801B777C.s').read_text()
instructions = {int(pc, 16): text for pc, text in
                re.findall(r'/\* ([0-9A-F]{8}) .*?\*/\s*(.*)', assembly)}

def route(kind):
    pc, comparison = 0x801b786c, 0
    for _ in range(100):
        op = instructions[pc].split()
        if op[0] == 'cmpwi':
            if op[1] != 'r4,':
                raise ValueError('Unexpected comparison register')
            comparison = kind-int(op[-1], 0)
        elif op[0] in ('b', 'beq', 'bne', 'bge', 'bgt', 'blt', 'ble'):
            take = op[0] == 'b' or dict(beq=comparison == 0, bne=comparison != 0,
                                       bge=comparison >= 0, bgt=comparison > 0,
                                       blt=comparison < 0, ble=comparison <= 0).get(op[0], False)
            if take:
                pc = int(op[-1].split('_')[-1], 16)
                continue
        else:
            return pc
        pc += 4
    raise ValueError('Decision tree did not terminate')

counts = {}
for name in ('preload', 'hub'):
    for chunk in json.loads((root/f'analysis/{name}-chunks.json').read_text())['chunks']:
        entry = counts.setdefault(int(chunk['type'], 16), {})
        entry[name] = entry.get(name, 0)+1
rows = []
for kind, count in sorted(counts.items()):
    pc = route(kind)
    calls = []
    # Report only the initial straight-line handler block, not conditional paths.
    for i in range(32):
        instruction = instructions.get(pc+4*i, '')
        if not instruction or instruction.startswith(('b ', 'beq ', 'bne ', 'bge ', 'blt ')):
            break
        if instruction.startswith('bl '):
            calls.append(instruction[3:])
    rows.append(dict(type=f'0x{kind:04X}', handler_entry=f'0x{pc:08X}',
                     initial_direct_calls=calls, occurrences=count))
(root/'analysis/resource-types.json').write_text(json.dumps(dict(
    source='Verified fn_801B777C disassembly; partial decision-tree evaluation, not a PPC emulator',
    types=rows), indent=2)+'\n')
print(f'Mapped {len(rows)} observed resource types to dispatcher entries.')
