"""Explicit PS0 transfer projections; arithmetic, PS1 and FPSCR excluded.

Single conversions admit only signed zero and exactly representable normal
binary32 values. The native and word-decoded runners reject other scenarios
from comparison evidence. This is not a general floating-point emulator.
"""
import re
from integer_recovery import translate as integer_translate, render as integer_render

OPS={'lfs','lfd','stfs','stfd','fmr'}


def translate(row):
    masked=dict(row)
    masked['ins']=['nop' if line.split()[0] in OPS else line for line in row['ins']]
    spec=integer_translate(masked,full_context=True,allow_calls=True)
    patches={}
    for i,ins in enumerate(row['ins']):
        op=ins.split()[0]
        if op not in OPS:continue
        args=re.split(r',\s*',ins.split(None,1)[1])
        def register(text):
            if not re.fullmatch(r'f(?:[0-9]|[12][0-9]|3[01])',text):raise ValueError('Invalid FPR')
            return 'fp['+text[1:]+']'
        dest=register(args[0])
        if op=='fmr':lines=[f'{dest} = {register(args[1])};']
        else:
            displacement,base=re.fullmatch(r'(.+)\((r\d+)\)',args[1]).groups()
            if '@' in displacement:
                word=row['words'][i];base='r'+str((word>>16)&31);low=word&65535;offset=low-65536 if low&32768 else low
            else:offset=int(displacement,0)
            address=f'({"0u" if base=="r0" else base} + UINT32_C(0x{offset&0xffffffff:x}))'
            if op=='lfs':lines=[f'{dest} = tak_transfer_expand(m->r32({address}));']
            elif op=='stfs':lines=[f'm->w32({address}, tak_transfer_contract({dest}));']
            else:
                pc=int(row['address'],16)+4*i;name=f'fp_address_{pc:08X}'
                lines=[f'uint32_t {name} = {address};']
                if op=='lfd':lines += [f'{dest} = (uint64_t)m->r32({name}) << 32;',f'{dest} |= m->r32({name} + 4u);']
                else:lines += [f'm->w32({name}, (uint32_t)({dest} >> 32));',f'm->w32({name} + 4u, (uint32_t){dest});']
            spec['target_access_sites'] += 2 if op in ('lfd','stfd') else 1
        patches[i]=lines
    body=[];index=-1
    for line in spec['body']:
        if line=='TAK_INTEGER_STEP();':index+=1
        if index in patches and line=='(void)0;':body.extend(patches[index])
        else:body.append(line)
    spec['body']=body;spec['floating_transfer_instructions']=len(patches)
    return spec


HELPERS=r'''
/* Single values: signed zero or exact normal binary32 only. Outside this
 * domain the fallback zero is not a hardware result or a recovered behavior. */
static uint64_t tak_transfer_expand(uint32_t x) {
    uint32_t e=(x>>23)&255u;
    if (!e) return (uint64_t)(x & UINT32_C(0x80000000))<<32;
    if (e==255u) return 0;
    return ((uint64_t)(x & UINT32_C(0x80000000))<<32)
         | ((uint64_t)(e+896u)<<52) | ((uint64_t)(x & UINT32_C(0x7fffff))<<29);
}
static uint32_t tak_transfer_contract(uint64_t x) {
    uint64_t magnitude=x & UINT64_C(0x7fffffffffffffff);
    uint32_t sign=(uint32_t)(x>>32)&UINT32_C(0x80000000);
    if (!magnitude) return sign;
    uint32_t e=(uint32_t)(x>>52)&2047u;
    if (e<897u || e>1150u || (x & UINT64_C(0x1fffffff))) return 0;
    return sign | ((e-896u)<<23) | ((uint32_t)(x>>29)&UINT32_C(0x7fffff));
}
'''


def render(specs):
    source=integer_render(specs,full_context=True,allow_calls=True)
    source=source.replace('Complete low-level integer C models','Finite-domain scalar-transfer and integer projections')
    source=source.replace('#include "call_context.h"','#include "transfer_context.h"\n'+HELPERS)
    source=source.replace('calls->invoke((target), state)','calls->invoke((target), state, fp)')
    source=source.replace('tak_call_','tak_transfer_').replace('const TakOpaqueCalls *calls','const TakTransferCalls *calls')
    source=source.replace('const TakTarget *m, const TakTransferCalls *calls)', 'const uint64_t finput[32], uint64_t foutput[32], const TakTarget *m, const TakTransferCalls *calls)')
    source=source.replace('    uint32_t state[42];','    (void)foutput;\n    uint64_t fp[32];\n    for (unsigned i=0; i<32; ++i) fp[i]=finput[i];\n    uint32_t state[42];')
    source=source.replace('#define TAK_INTEGER_RETURN() do { if (output) { \\', '#define TAK_INTEGER_RETURN() do { if (foutput) { for (unsigned i=0; i<32; ++i) foutput[i]=fp[i]; } if (output) { \\')
    # Strict builds may omit one of the two single-transfer operations.
    if not any('tak_transfer_expand(' in line for s in specs for line in s['body']):
        source=source.replace('static uint64_t tak_transfer_expand','static __attribute__((unused)) uint64_t tak_transfer_expand')
    if not any('tak_transfer_contract(' in line for s in specs for line in s['body']):
        source=source.replace('static uint32_t tak_transfer_contract','static __attribute__((unused)) uint32_t tak_transfer_contract')
    return source
