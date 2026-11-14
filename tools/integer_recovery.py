"""Restricted disassembly-to-C recovery for call-free integer routines.

This is a source recovery helper, not a CPU interpreter. Each accepted
routine becomes a separate ordinary C function with explicit control flow.
Unsupported operations, external transfers and undefined inputs are rejected.
The independent verifier decodes original machine words instead of this text.
"""
import re
from ppc_leaf import bitmask

MASK = 0xffffffff


def immediate(text):
    if '@' not in text: return int(text, 0)
    match = re.search(r'_([0-9A-Fa-f]{8})(?:@|$)', text)
    if not match: raise ValueError('Unresolved symbol: '+text)
    value = int(match[1], 16)
    if '@sda21' in text: return value
    if '@ha' in text: return ((value+0x8000) >> 16) & 0xffff
    if '@l' in text:
        value &= 0xffff
        return value-65536 if value & 0x8000 else value
    raise ValueError(text)


def constant(value): return f'UINT32_C(0x{value & MASK:x})'


def translate(row, full_context=False, allow_calls=False):
    start, size = int(row['address'], 16), int(row['size'])
    instructions = row['ins']
    if len(instructions)*4 != size: raise ValueError('Incomplete instruction text')
    operations = []
    all_vars = ({f'r{i}' for i in range(32)} | {'lr','ctr'} | {f'cr{i}' for i in range(8)}) if full_context else {f'r{i}' for i in range(3,11)}
    targets = set()
    accesses = 0
    call_sites=[]
    for index, ins in enumerate(instructions):
        pc = start+index*4
        pieces = ins.split(None, 1)
        opcode = pieces[0]
        args = re.split(r',\s*', pieces[1]) if len(pieces) > 1 else []
        reads, defines, lines = set(), set(), []
        successors = [pc+4] if pc+4 < start+size else []

        def number(text):
            if '@' not in text or 'words' not in row: return immediate(text)
            word = row['words'][index]
            low = word & 0xffff
            if '@sda21' in text:
                base = (word >> 16) & 31
                if base not in (2,13): raise ValueError('Unexpected SDA base')
                return ((0x8033b140 if base == 2 else 0x80338280)
                        + (low-65536 if low & 0x8000 else low)) & MASK
            if '@l' in text and not opcode.startswith(('ori','xori','andi')):
                return low-65536 if low & 0x8000 else low
            return low

        def read(var):
            if not re.fullmatch(r'(r\d+|cr[0-7]|ctr|lr)', var): raise ValueError('Unknown register '+var)
            reads.add(var); all_vars.add(var); return var

        def define(var):
            defines.add(var); all_vars.add(var); return var

        def address(text):
            displacement, base = re.fullmatch(r'(.+)\((r\d+)\)', text).groups()
            if '@sda21' in displacement:
                if full_context:
                    register=(row['words'][index]>>16)&31
                    low=row['words'][index]&65535
                    return f'({read("r"+str(register))} + {constant(low-65536 if low&32768 else low)})',base
                return constant(number(displacement)), base
            return f'({"0u" if base == "r0" else read(base)} + {constant(number(displacement))})', base

        def rotate(value, amount):
            amount &= 31
            return value if not amount else f'(({value} << {amount}) | ({value} >> {32-amount}))'

        def record(value): lines.append(f'{define("cr0")} = cmp_signed({value}, 0u);')

        def target(text):
            match = re.fullmatch(r'\.L_([0-9A-Fa-f]+)', text)
            if not match: raise ValueError('External branch')
            value = int(match[1], 16)
            if not start <= value < start+size or (value-start) % 4:
                raise ValueError('Branch outside indexed function')
            targets.add(value); return value

        def external_call(destination, linked):
            for var in all_vars.copy():
                if re.fullmatch(r'(r\d+|lr|ctr|cr[0-7])',var):read(var)
            for var in list(reads):define(var)
            lines.append(f'uint32_t call_target_{pc:08X} = {destination};')
            if linked:lines.append(f'lr = {constant(pc+4)};')
            lines.append(f'TAK_OPAQUE_CALL(call_target_{pc:08X});')
            call_sites.append({'pc':f'0x{pc:08X}','target':destination,'linked':linked})

        base_op = opcode.rstrip('.')
        if base_op == 'nop':
            lines.append('(void)0;')
        elif base_op in ('crclr','crset') and full_context:
            named=re.fullmatch(r'cr([0-7])(lt|gt|eq|so)',args[0])
            bit=int(named[1])*4+('lt','gt','eq','so').index(named[2]) if named else number(args[0])
            if not 0 <= bit < 32 or bit%4==3:raise ValueError('Unmodeled condition SO bit')
            field='cr'+str(bit//4);value=read(field);mask=1<<(bit%4)
            lines.append(f'{define(field)} = {value} '+('|' if base_op=='crset' else '&')+f' {constant(mask if base_op=="crset" else ~mask)};')
        elif base_op in ('li', 'lis'):
            if full_context and '@sda21' in args[1]:
                word=row['words'][index]; register=(word>>16)&31;low=word&65535
                expr=f'{read("r"+str(register))} + {constant(low-65536 if low&32768 else low)}'
            else:expr=constant(number(args[1]) << (16 if base_op == 'lis' else 0))
            lines.append(f'{define(args[0])} = {expr};')
        elif base_op == 'mr':
            value = read(args[1]); dest = define(args[0])
            lines.append(f'{dest} = {value};' if dest != value else f'(void){dest};')
            if opcode.endswith('.'): record(args[0])
        elif base_op in ('addi', 'addis', 'subi', 'subis', 'subic'):
            value = read(args[1]); n = number(args[2]) << (16 if base_op in ('addis', 'subis') else 0)
            operation = '-' if base_op.startswith('sub') else '+'
            lines.append(f'{define(args[0])} = {value} {operation} {constant(n)};')
            if opcode.endswith('.'): record(args[0])
        elif base_op in ('lwz', 'lwzu', 'lbz', 'lbzu', 'lhz', 'lhzu', 'lha'):
            location, base = address(args[1]); accesses += 1
            width = 32 if base_op.startswith('lw') else 8 if base_op.startswith('lb') else 16
            expr = f'm->r{width}({location})'
            if base_op == 'lha': expr = f'sign_half({expr})'
            if base_op.endswith('u') and (base == 'r0' or base == args[0]):
                raise ValueError('Invalid load-with-update operands')
            lines.append(f'{define(args[0])} = {expr};')
            if base_op.endswith('u'): lines.append(f'{define(base)} = {location};')
        elif base_op in ('stw', 'stb', 'sth', 'stbu', 'stwu', 'sthu'):
            value = read(args[0]); location, base = address(args[1]); accesses += 1
            width = 32 if base_op.startswith('stw') else 16 if base_op.startswith('sth') else 8
            lines.append(f'm->w{width}({location}, (uint{width}_t){value});')
            if base_op.endswith('u'):
                if base == 'r0': raise ValueError('Invalid store-with-update')
                lines.append(f'{define(base)} = {location};')
        elif base_op in ('stmw','lmw') and full_context:
            location,base=address(args[1]);first=int(args[0][1:]);accesses+=32-first
            # Capture effective address before a load can overwrite its base.
            lines.append(f'uint32_t transfer_{pc:08X} = {location};')
            for regnum in range(first,32):
                at=f'(transfer_{pc:08X} + {4*(regnum-first)}u)'
                if base_op=='stmw':lines.append(f'm->w32({at}, {read("r"+str(regnum))});')
                else:lines.append(f'{define("r"+str(regnum))} = m->r32({at});')
        elif base_op in ('lwzx', 'lbzx', 'lhzx', 'stwx', 'stbx', 'sthx'):
            base = '0u' if args[1] == 'r0' else read(args[1]); offset = read(args[2]); accesses += 1
            width = 32 if base_op in ('lwzx', 'stwx') else 16 if base_op in ('lhzx', 'sthx') else 8
            location = f'({base} + {offset})'
            if base_op.startswith('st'):
                lines.append(f'm->w{width}({location}, (uint{width}_t){read(args[0])});')
            else: lines.append(f'{define(args[0])} = m->r{width}({location});')
        elif base_op in ('cmpw', 'cmplw', 'cmpwi', 'cmplwi'):
            field = args[0] if len(args) == 3 else 'cr0'
            x, y = args[-2:]; x = read(x)
            y = constant(number(y)) if base_op.endswith('i') else read(y)
            compare = 'cmp_unsigned' if base_op.startswith('cmpl') else 'cmp_signed'
            lines.append(f'{define(field)} = {compare}({x}, {y});')
        elif base_op in ('add', 'subf', 'subfc', 'mullw', 'and', 'andc', 'or', 'xor', 'nor'):
            x, y = read(args[1]), read(args[2])
            if base_op in ('subf','subfc'): expr = f'{y} - {x}'
            elif base_op == 'andc': expr = f'{x} & ~{y}'
            elif base_op == 'nor': expr = f'~({x} | {y})'
            else: expr = f'{x} '+{'add':'+', 'mullw':'*', 'and':'&', 'or':'|', 'xor':'^'}[base_op]+f' {y}'
            lines.append(f'{define(args[0])} = {expr};')
            if opcode.endswith('.'): record(args[0])
        elif base_op in ('ori', 'oris', 'xori', 'xoris', 'andi'):
            x = read(args[1]); n = number(args[2]) << (16 if base_op in ('oris','xoris') else 0)
            lines.append(f'{define(args[0])} = {x} '+('&' if base_op == 'andi' else '^' if base_op in ('xori','xoris') else '|')+f' {constant(n)};')
            if opcode.endswith('.'): record(args[0])
        elif base_op in ('mulhw','divw','divwu'):
            x,y=read(args[1]),read(args[2])
            helper={'mulhw':'multiply_high_signed','divw':'divide_signed','divwu':'divide_unsigned'}[base_op]
            lines.append(f'{define(args[0])} = {helper}({x}, {y});')
            if opcode.endswith('.'):record(args[0])
        elif base_op == 'mulhwu':
            x,y=read(args[1]),read(args[2])
            lines.append(f'{define(args[0])} = (uint32_t)(((uint64_t){x} * (uint64_t){y}) >> 32);')
            if opcode.endswith('.'):record(args[0])
        elif base_op == 'addic':
            x=read(args[1]);n=constant(number(args[2]))
            lines.append(f'{define(args[0])} = {x} + {n};')
            if opcode.endswith('.'):record(args[0])
        elif base_op in ('mulli', 'subfic'):
            x = read(args[1]); n = constant(number(args[2]))
            expr = f'{x} * {n}' if base_op == 'mulli' else f'{n} - {x}'
            lines.append(f'{define(args[0])} = {expr};')
        elif base_op in ('neg', 'cntlzw', 'extsb', 'extsh'):
            x = read(args[1])
            expr = f'0u - {x}' if base_op == 'neg' else {'cntlzw':'leading_zeros', 'extsb':'sign_byte', 'extsh':'sign_half'}[base_op]+f'({x})'
            lines.append(f'{define(args[0])} = {expr};')
            if opcode.endswith('.'): record(args[0])
        elif base_op in ('slwi', 'srwi', 'srawi', 'slw', 'srw'):
            x = read(args[1])
            if base_op.endswith('i'):
                n = number(args[2])
                if not 0 <= n < 32: raise ValueError('Invalid shift')
                expr = f'shift_signed({x}, {n})' if base_op == 'srawi' else f'{x} '+('<<' if base_op == 'slwi' else '>>')+f' {n}'
            else:
                n = read(args[2]); expr = ('shift_left' if base_op == 'slw' else 'shift_right')+f'({x}, {n})'
            lines.append(f'{define(args[0])} = {expr};')
            if opcode.endswith('.'): record(args[0])
        elif base_op in ('clrlwi', 'clrrwi', 'clrlslwi', 'extrwi', 'extlwi', 'rlwinm', 'rlwimi'):
            x = read(args[1]); n = number(args[2])
            if base_op == 'clrlwi': expr = f'{x} & {constant(MASK >> n)}'
            elif base_op == 'clrrwi': expr = f'{x} & {constant(MASK << n)}'
            elif base_op == 'clrlslwi': expr = f'({x} & {constant(MASK >> n)}) << {number(args[3])}'
            elif base_op == 'extrwi':
                expr = f'{rotate(x, n+number(args[3]))} & {constant((1 << n)-1)}'
            elif base_op == 'extlwi':expr=f'{rotate(x, number(args[3]))} & {constant(MASK << (32-n))}'
            else:
                mask = bitmask(number(args[3]), number(args[4])); value = f'({rotate(x, n)} & {constant(mask)})'
                expr = value if base_op == 'rlwinm' else f'({read(args[0])} & {constant(~mask)}) | {value}'
            lines.append(f'{define(args[0])} = {expr};')
            if opcode.endswith('.'): record(args[0])
        elif base_op == 'mtctr': lines.append(f'{define("ctr")} = {read(args[0])};')
        elif base_op in ('mflr','mtlr','mfctr') and full_context:
            if base_op=='mtlr':lines.append(f'{define("lr")} = {read(args[0])};')
            else:lines.append(f'{define(args[0])} = {read("lr" if base_op=="mflr" else "ctr")};')
        elif allow_calls and base_op == 'bctr':
            value=read('ctr');destinations=list(range(start,start+size,4))
            targets.update(destinations);successors=destinations
            lines.append(f'switch ({value} & UINT32_C(0xfffffffc)) {{')
            for destination in destinations:
                lines.append(f'case {constant(destination)}: goto block_{destination:08X};')
            lines.append('default: break;')
            lines.append('}')
            external_call(f'({value} & UINT32_C(0xfffffffc))',False)
            lines.append('return r3;')
        elif allow_calls and base_op in ('bl','bctrl','blrl'):
            if not full_context:raise ValueError('Calls require explicit context')
            if base_op=='bl':
                word=row['words'][index];offset=word&0x03fffffc
                if offset&0x02000000:offset-=0x04000000
                destination=((offset if word&2 else pc+offset)&MASK)
                if start<=destination<start+size:raise ValueError('Internal linked branch unsupported')
                expr=constant(destination)
            else:expr=read('ctr' if base_op=='bctrl' else 'lr')
            external_call(expr,True)
        elif base_op == 'blr':
            read('r3'); lines.append('return r3;'); successors = []
        elif base_op == 'b':
            word=row['words'][index] if 'words' in row else None
            if allow_calls and word is not None:
                offset=word&0x03fffffc
                if offset&0x02000000:offset-=0x04000000
                dest=((offset if word&2 else pc+offset)&MASK)
                if not start<=dest<start+size:
                    external_call(constant(dest),False);lines.append('return r3;');successors=[]
                else:targets.add(dest);lines.append(f'goto block_{dest:08X};');successors=[dest]
            else:dest = target(args[0]); lines.append(f'goto block_{dest:08X};'); successors = [dest]
        elif base_op == 'bdnz':
            read('ctr'); define('ctr'); dest = target(args[0])
            lines += ['--ctr;', f'if (ctr) goto block_{dest:08X};']; successors.append(dest)
        elif re.fullmatch(r'b(eq|ne|lt|gt|le|ge)(lr)?', base_op):
            condition = base_op[1:3]; is_return = base_op.endswith('lr')
            field = args[0] if (len(args) == (1 if is_return else 2)) else 'cr0'
            bits = read(field)
            mask = {'eq':4, 'ne':4, 'lt':1, 'gt':2, 'le':2, 'ge':1}[condition]
            check = f'({bits} & {mask}u)'
            if condition in ('ne', 'le', 'ge'): check = '!'+check
            if is_return:
                read('r3'); lines.append(f'if ({check}) return r3;')
            else:
                dest = target(args[-1]); lines.append(f'if ({check}) goto block_{dest:08X};'); successors.append(dest)
        else: raise ValueError('Unsupported instruction '+opcode)
        operations.append({'pc':pc, 'lines':lines, 'reads':reads, 'defines':defines, 'next':successors})

    # Must-definition analysis rejects implicit incoming temporaries/flags.
    reachable = {start}
    for _ in range(len(operations)):
        new = reachable | {n for op in operations if op['pc'] in reachable for n in op['next']}
        if new == reachable: break
        reachable = new
    initial = set(all_vars) if full_context else {'r2','r13'} | {f'r{i}' for i in range(3,11)}
    universe = set().union(*(op['reads'] | op['defines'] for op in operations)) | initial
    predecessors = {op['pc']:[] for op in operations}
    for op in operations:
        if op['pc'] in reachable:
            for n in op['next']: predecessors[n].append(op['pc'])
    incoming = {op['pc']:set(initial if op['pc'] == start else universe) for op in operations}
    outgoing = {op['pc']:incoming[op['pc']] | op['defines'] for op in operations}
    for _ in range(len(operations)*2):
        changed = False
        for op in operations:
            pc = op['pc']
            if pc not in reachable: continue
            states = [outgoing[p] for p in predecessors[pc]]
            if pc == start: states.append(initial)
            value = set.intersection(*states)
            result = value | op['defines']
            if value != incoming[pc] or result != outgoing[pc]: changed = True
            incoming[pc], outgoing[pc] = value, result
        if not changed: break
    else: raise ValueError('Definition analysis failed to converge')
    for op in operations:
        if op['pc'] in reachable and not op['reads'] <= incoming[op['pc']]:
            raise ValueError('Implicit incoming state: '+str(op['reads']-incoming[op['pc']]))
        if not full_context and op['defines'] & {'r2','r13'}:
            raise ValueError('Global base-register mutation excluded')
    if not full_context and 'r1' in all_vars: raise ValueError('Stack-pointer routine excluded')
    if any(n not in predecessors for op in operations for n in op['next']): raise ValueError('Incomplete control flow')
    if operations[-1]['next'] == [] and not any('return ' in s or 'goto ' in s for s in operations[-1]['lines']):
        raise ValueError('Unterminated routine')
    lines = []
    for var in sorted(all_vars):
        if full_context:
            slot=int(var[1:]) if var.startswith('r') else 32 if var=='lr' else 33 if var=='ctr' else 34+int(var[2:])
            value=f'input[{slot}]'
        else:value = f'input[{int(var[1:])-3}]' if re.fullmatch(r'r(?:[3-9]|10)',var) else constant(0x8033b140 if var == 'r2' else 0x80338280 if var == 'r13' else 0)
        lines += [f'uint32_t {var} = {value};', f'(void){var};']
    for op in operations:
        if op['pc'] in targets: lines.append(f'block_{op["pc"]:08X}: ;')
        lines.append('TAK_INTEGER_STEP();')
        lines += op['lines']
    result={'address':row['address'], 'original_name':row['name'], 'original_bytes':size,
            'body':lines, 'target_access_sites':accesses,
            'static_reachable_instructions':len(reachable),
            'static_unreachable_addresses':[f'0x{op["pc"]:08X}' for op in operations if op['pc'] not in reachable]}
    if allow_calls:result['external_call_sites']=call_sites
    return result


HELPERS = {
 'signed_wide':'static int64_t signed_wide(uint32_t x) { return (int64_t)x - (x & UINT32_C(0x80000000) ? INT64_C(4294967296) : 0); }',
 'multiply_high_signed':'static uint32_t multiply_high_signed(uint32_t x, uint32_t y) { return (uint32_t)((uint64_t)(signed_wide(x) * signed_wide(y)) >> 32); }',
 'divide_signed':'static uint32_t divide_signed(uint32_t x, uint32_t y) { return !y || (x == UINT32_C(0x80000000) && y == UINT32_MAX) ? 0u : (uint32_t)(signed_wide(x) / signed_wide(y)); }',
 'divide_unsigned':'static uint32_t divide_unsigned(uint32_t x, uint32_t y) { return y ? x / y : 0u; }',
 'cmp_unsigned':'static uint32_t cmp_unsigned(uint32_t a, uint32_t b) { return a < b ? 1u : a > b ? 2u : 4u; }',
 'cmp_signed':'static uint32_t cmp_signed(uint32_t a, uint32_t b) { return cmp_unsigned(a ^ UINT32_C(0x80000000), b ^ UINT32_C(0x80000000)); }',
 'sign_byte':'static uint32_t sign_byte(uint32_t x) { x &= 255u; return x & 128u ? x | UINT32_C(0xffffff00) : x; }',
 'sign_half':'static uint32_t sign_half(uint32_t x) { x &= 65535u; return x & 32768u ? x | UINT32_C(0xffff0000) : x; }',
 'leading_zeros':'static uint32_t leading_zeros(uint32_t x) { return x ? (uint32_t)__builtin_clz(x) : 32u; }',
 'shift_signed':'static uint32_t shift_signed(uint32_t x, unsigned n) { if (!n) return x; return (x >> n) | (x & UINT32_C(0x80000000) ? ~(UINT32_MAX >> n) : 0u); }',
 'shift_left':'static uint32_t shift_left(uint32_t x, uint32_t n) { return n & 32u ? 0u : x << (n & 31u); }',
 'shift_right':'static uint32_t shift_right(uint32_t x, uint32_t n) { return n & 32u ? 0u : x >> (n & 31u); }',
}


def render(specs, full_context=False, allow_calls=False):
    text = '\n'.join('\n'.join(s['body']) for s in specs)
    if 'multiply_high_signed(' in text or 'divide_signed(' in text:text += '\nsigned_wide('
    out = ['/* Complete low-level integer C models, GJUE78 rev 0.',
           ' * Generated from explicit recovered control-flow specifications.',
           ' * Not original source types, ABI-compatible replacements, or compiler matches.',
           ' * See analysis/INTEGER_HELPERS.md. No instruction interpreter is embedded.',
           ' */', '#include "runtime_helpers.h"', '',
           '#ifdef TAK_VERIFY_BUDGET',
           'static _Thread_local uint32_t verify_fuel;',
           'static _Thread_local int verify_exhausted;',
           'void tak_integer_set_fuel(uint32_t value) { verify_fuel = value; verify_exhausted = 0; }',
           'int tak_integer_exhausted(void) { return verify_exhausted; }',
           '#define TAK_INTEGER_STEP() do { if (!verify_fuel) { verify_exhausted = 1; return 0; } --verify_fuel; } while (0)',
           '#else', '#define TAK_INTEGER_STEP() ((void)0)', '#endif', '']
    variables=([f'r{i}' for i in range(32)]+['lr','ctr']+[f'cr{i}' for i in range(8)]) if full_context else [f'r{i}' for i in range(3,11)]
    out += ['#define TAK_INTEGER_RETURN() do { if (output) { \\']
    if full_context:out += [f'    output[{i}]={v}; \\' for i,v in enumerate(variables)]
    else:out += ['    output[0]=r3; output[1]=r4; output[2]=r5; output[3]=r6; \\',
                 '    output[4]=r7; output[5]=r8; output[6]=r9; output[7]=r10; \\']
    out += ['    } return r3; } while (0)', '']
    for name, helper in HELPERS.items():
        if name+'(' in text or (name == 'cmp_unsigned' and 'cmp_signed(' in text): out += [helper,'']
    for spec in specs:
        out += [f'/* {spec["address"]}: {spec["original_bytes"]} original bytes. */',
                f'uint32_t {"tak_extended_" if full_context else "tak_integer_"}{spec["address"][2:]}(const uint32_t input[{len(variables)}], uint32_t output[{len(variables)}], const TakTarget *m)',
                '{', '    (void)input; (void)m;']
        out += ['    '+line.replace('return r3;', 'TAK_INTEGER_RETURN();') for line in spec['body']]
        out += ['}', '']
    out += ['#undef TAK_INTEGER_STEP', '#undef TAK_INTEGER_RETURN', '']
    result='\n'.join(out)
    if allow_calls:
        result=result.replace('#include "runtime_helpers.h"','#include "call_context.h"\n#define TAK_OPAQUE_CALL(target) calls->invoke((target), state)')
        # Bodies retain explicit C branches; only register storage changes
        # from individual locals to a context array for the call interface.
        result=result.replace('tak_extended_','tak_call_')
        result=result.replace('const TakTarget *m)','const TakTarget *m, const TakOpaqueCalls *calls)')
        result=result.replace('    (void)input; (void)m;','    (void)input; (void)m; (void)calls; (void)output;\n    uint32_t state[42];\n    for (unsigned i=0; i<42; ++i) state[i]=input[i];')
        result=re.sub(r'^    uint32_t (r\d+|lr|ctr|cr[0-7]) = input\[\d+\];\n    \(void\)\1;\n','',result,flags=re.M)
        def stored(match):
            name=match[0];slot=int(name[1:]) if re.fullmatch(r'r\d+',name) else 32 if name=='lr' else 33 if name=='ctr' else 34+int(name[2:])
            return f'state[{slot}]'
        result=re.sub(r'(?<!->)\b(?:r(?:[0-9]|[12][0-9]|3[01])|lr|ctr|cr[0-7])\b',stored,result)
        result += '\n#undef TAK_OPAQUE_CALL\n'
    return result
