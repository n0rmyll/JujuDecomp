"""Recover completely recognized small caller shapes from saved models.

C types are provisional. Full relocated code equality determines matching.
"""
import re


def virtual_body(address, offset, slot):
    pc = int(address, 0)
    return [
        'm->w32((r1 + UINT32_C(0xfffffff0)), (uint32_t)r1);',
        'r1 = (r1 + UINT32_C(0xfffffff0));', 'r0 = lr;',
        'm->w32((r1 + UINT32_C(0x14)), (uint32_t)r0);',
        f'r3 = m->r32((r3 + UINT32_C({hex(offset)})));',
        'r12 = m->r32((r3 + UINT32_C(0x0)));',
        f'r12 = m->r32((r12 + UINT32_C({hex(slot)})));',
        'ctr = r12;', f'uint32_t call_target_{pc+28:08X} = ctr;',
        f'lr = UINT32_C({hex(pc+32)});',
        f'TAK_OPAQUE_CALL(call_target_{pc+28:08X});',
        'r0 = m->r32((r1 + UINT32_C(0x14)));', 'lr = r0;',
        'r1 = r1 + UINT32_C(0x10);', 'return r3;']


def fill_body(address, target):
    pc = int(address, 0)
    return virtual_body(address, 0, 8)[:4] + [
        'm->w32((r1 + UINT32_C(0xc)), (uint32_t)r31);', 'r31 = r3;',
        f'uint32_t call_target_{pc+20:08X} = UINT32_C({hex(target)});',
        f'lr = UINT32_C({hex(pc+24)});',
        f'TAK_OPAQUE_CALL(call_target_{pc+20:08X});',
        'r0 = m->r32((r1 + UINT32_C(0x14)));', 'r3 = r31;',
        'r31 = m->r32((r1 + UINT32_C(0xc)));', 'lr = r0;',
        'r1 = r1 + UINT32_C(0x10);', 'return r3;']


def extended_body(entry):
    address = entry['address']
    pc = int(address, 0)
    kind = entry['kind']
    prologue = virtual_body(address, 0, 8)[:4]
    epilogue = virtual_body(address, 0, 8)[-4:]
    call_pc = pc + (12 if kind == 'byte_bool' else 28)
    call = [f'uint32_t call_target_{call_pc:08X} = UINT32_C({hex(entry["target"])});',
            f'lr = UINT32_C({hex(call_pc+4)});',
            f'TAK_OPAQUE_CALL(call_target_{call_pc:08X});']
    if kind == 'swap':
        middle = ['r0 = r4;', 'r4 = r5;',
                  f'r3 = m->r32((r3 + UINT32_C({hex(entry["offset"])})));', 'r5 = r0;'] + call
    elif kind == 'nested_guard':
        middle = [f'r4 = m->r32((r3 + UINT32_C({hex(entry["offset"])})));',
                  f'r0 = m->r{entry["width"]}((r4 + UINT32_C({hex(entry["guard"])})));',
                  'cr0 = cmp_unsigned(r0, UINT32_C(0x0));',
                  f'if ((cr0 & 4u)) goto block_{pc+32:08X};'] + call + [f'block_{pc+32:08X}: ;']
    elif kind == 'bit_guard':
        middle = [f'r0 = m->r8((r3 + UINT32_C({hex(entry["guard"])})));',
                  'r0 = ((r0 << 25) | (r0 >> 7)) & UINT32_C(0x1);',
                  'cr0 = cmp_signed(r0, 0u);',
                  f'if ((cr0 & 4u)) goto block_{pc+32:08X};',
                  f'r3 = r3 + UINT32_C({hex(entry["offset"])});'] + call + [f'block_{pc+32:08X}: ;']
    elif kind == 'byte_bool':
        middle = call + ['r3 = r3 & UINT32_C(0xff);', 'r0 = 0u - r3;',
                         'r0 = r0 | r3;', 'r3 = r0 >> 31;']
    else:
        raise ValueError('Unknown caller shape: ' + kind)
    return prologue + middle + epilogue


def recover_extended(spec, body):
    text = '\n'.join(body)
    target = re.search(r'uint32_t call_target_[0-9A-F]+ = UINT32_C\((0x[0-9a-f]+)\);', text)
    if not target:
        return None
    common = dict(address=spec['address'], target=int(target[1], 0))
    candidates = [dict(common, kind='byte_bool')]
    offset = re.search(r'r3 = m->r32\(\(r3 \+ UINT32_C\((0x[0-9a-f]+)\)\)\);', text)
    if offset:
        candidates.append(dict(common, kind='swap', offset=int(offset[1], 0)))
    offset = re.search(r'r4 = m->r32\(\(r3 \+ UINT32_C\((0x[0-9a-f]+)\)\)\);', text)
    guard = re.search(r'r0 = m->r(8|32)\(\(r4 \+ UINT32_C\((0x[0-9a-f]+)\)\)\);', text)
    if offset and guard:
        candidates.append(dict(common, kind='nested_guard', offset=int(offset[1], 0),
                               width=int(guard[1]), guard=int(guard[2], 0)))
    offset = re.search(r'r3 = r3 \+ UINT32_C\((0x[0-9a-f]+)\);', text)
    guard = re.search(r'r0 = m->r8\(\(r3 \+ UINT32_C\((0x[0-9a-f]+)\)\)\);', text)
    if offset and guard:
        candidates.append(dict(common, kind='bit_guard', offset=int(offset[1], 0), guard=int(guard[1], 0)))
    return next((entry for entry in candidates if body == extended_body(entry)), None)


def recover(specs):
    result = []
    for spec in specs:
        if spec['original_bytes'] != 48:
            continue
        # Full-context declarations are fixed by integer_recovery.render.
        body = [line for line in spec['body'][84:] if line != 'TAK_INTEGER_STEP();']
        extended = recover_extended(spec, body)
        if extended:
            result.append(extended)
            continue
        if len(body) != 15:
            continue
        offset = re.fullmatch(r'r3 = m->r32\(\(r3 \+ UINT32_C\((0x[0-9a-f]+)\)\)\);', body[4])
        slot = re.fullmatch(r'r12 = m->r32\(\(r12 \+ UINT32_C\((0x[0-9a-f]+)\)\)\);', body[6])
        if offset and slot:
            off, index = int(offset[1], 0), int(slot[1], 0)
            if index >= 8 and index <= 0x100 and index % 4 == 0 and body == virtual_body(spec['address'], off, index):
                result.append(dict(address=spec['address'], kind='virtual', offset=off, slot=index))
                continue
        # These two callees were separately inspected as byte-fill implementations.
        for target in (0x80003488, 0x8029DAD4):
            if body == fill_body(spec['address'], target):
                result.append(dict(address=spec['address'], kind='fill', target=target))
    return result


def render(entries):
    out = ['/* GJUE78 rev 0 caller interface candidates. Generated by',
           ' * tools/check_caller_interfaces.py --write-source. Types remain provisional.',
           ' * No explicit stack/register harness; compiler owns the ABI frame. */',
           'typedef unsigned char u8;', 'typedef unsigned int u32;',
           'struct CallerActiveFlag { u8 active:1; u8 other:7; };',
           'class CallerVirtual { public:']
    maximum = max((e['slot'] for e in entries if e['kind'] == 'virtual'), default=8)
    out += [f'    virtual void slot_{slot:02X}();' for slot in range(8, maximum+4, 4)]
    out += ['};', 'extern "C" {',
            'extern void fn_80003488(void *, int, u32);',
            'extern void fn_8029DAD4(void *, int, u32);']
    for entry in entries:
        address = entry['address']
        out += [f'#if TAK_FN == {address}']
        if entry['kind'] == 'virtual':
            out += [f'void fn_{address[2:]}(void *self) {{',
                    f'    (*(CallerVirtual **)((u8 *)self + {hex(entry["offset"])}))->slot_{entry["slot"]:02X}();', '}']
        elif entry['kind'] == 'fill':
            out += [f'void *fn_{address[2:]}(void *destination, int value, u32 size) {{',
                    f'    fn_{entry["target"]:08X}(destination, value, size);',
                    '    return destination;', '}']
        elif entry['kind'] == 'swap':
            out += [f'extern void fn_{entry["target"]:08X}(void *, u32, u32);',
                    f'void fn_{address[2:]}(void *self, u32 first, u32 second) {{',
                    f'    fn_{entry["target"]:08X}(*(void **)((u8 *)self + {hex(entry["offset"])}), second, first);', '}']
        elif entry['kind'] == 'nested_guard':
            value_type = 'u8' if entry['width'] == 8 else 'u32'
            out += [f'extern void fn_{entry["target"]:08X}(void *);',
                    f'void fn_{address[2:]}(void *self) {{',
                    f'    if (*({value_type} *)(*(u8 **)((u8 *)self + {hex(entry["offset"])}) + {hex(entry["guard"])}))',
                    f'        fn_{entry["target"]:08X}(self);', '}']
        elif entry['kind'] == 'bit_guard':
            out += [f'extern void fn_{entry["target"]:08X}(void *);',
                    f'void fn_{address[2:]}(void *self) {{',
                    f'    if (((CallerActiveFlag *)((u8 *)self + {hex(entry["guard"])}))->active)',
                    f'        fn_{entry["target"]:08X}((u8 *)self + {hex(entry["offset"])});', '}']
        elif entry['kind'] == 'byte_bool':
            out += [f'extern u8 fn_{entry["target"]:08X}(void *);',
                    f'bool fn_{address[2:]}(void *self) {{',
                    f'    return fn_{entry["target"]:08X}(self) != 0;', '}']
        else:
            raise ValueError('Unknown caller interface: ' + entry['kind'])
        out += ['#endif']
    return '\n'.join(out + ['}', ''])
