#!/usr/bin/env python3
"""Compare additional stack-using integer models with original PPC words.

Uses an explicit integer register context; does not infer original prototypes.
"""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from check_runtime_helpers import Runtime, API
from check_integer_helpers import Memory, read, scenario
from integer_recovery import render
from ppc_leaf import execute, load_functions

ROOT=Path(__file__).resolve().parents[1]
SPECS=ROOT/'analysis/context-helper-specs.json'
SOURCE=ROOT/'src/recovered/context_leaf_helpers.c'
FUEL=4096


def verify(spec, words, library):
    addr=spec['address'][2:];fn=getattr(library,'tak_extended_'+addr)
    fn.argtypes=[c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(API)];fn.restype=c.c_uint32
    visited=set();accepted=[];budget_rejections=0
    for trial in range(256):
        args,seed,style,data=scenario(addr,trial)
        initial=[args[i%8] for i in range(32)]
        initial[1]=0x90010000;initial[2]=0x8033b140;initial[13]=0x80338280
        initial += [0x80001000+4*trial,trial%5]+[(trial+i)%8 for i in range(8)]
        original=Memory(seed,style,data);seen=set();output=[]
        try:expected=execute(words,args,original,budget=FUEL,visited=seen,initial_context=initial,final_context=output)
        except ValueError as e:
            if str(e)!='PowerPC instruction budget exhausted':raise
            budget_rejections+=1;continue
        native=Runtime();native.data=dict(data)
        native.read=lambda a,size:read(native,a,size,seed,style)
        result=(c.c_uint32*42)();library.tak_integer_set_fuel(FUEL)
        actual=fn((c.c_uint32*42)(*initial),result,c.byref(native.runtime));native.clean()
        if library.tak_integer_exhausted():raise AssertionError((addr,trial,'C budget exhausted'))
        if actual!=expected or list(result)!=output:
            bad=[i for i,pair in enumerate(zip(result,output)) if pair[0]!=pair[1]]
            raise AssertionError((addr,trial,'integer context mismatch',bad))
        if native.events!=original.events:
            n=next((i for i,pair in enumerate(zip(native.events,original.events)) if pair[0]!=pair[1]),min(len(native.events),len(original.events)))
            raise AssertionError((addr,trial,'memory trace',n,native.events[n:n+3],original.events[n:n+3]))
        assert native.data==original.data,(addr,trial,'final memory')
        visited|=seen;accepted.append(trial)
        if len(accepted)==64:break
    if len(accepted)!=64:return None
    return {'address':spec['address'],'original_name':spec['original_name'],'original_bytes':len(words)*4,
            'instructions_verified':len(words),'instructions_exercised':len(visited),
            'unexercised_addresses':[f'0x{pc:08X}' for pc in sorted(set(words)-visited)],
            'differential_cases':64,'accepted_trials':accepted,'original_budget_rejections':budget_rejections,
            'source':'src/recovered/context_leaf_helpers.c'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--select',type=Path)
    args=parser.parse_args()
    small=json.loads((ROOT/'analysis/small-helper-specs.json').read_text())['routines']
    required=1000-len(small)
    specs=json.loads((args.select if args.select else SPECS).read_text())
    if isinstance(specs,dict):specs=specs['routines']
    small_addresses={s['address'] for s in small}
    specs=[s for s in specs if s['address'] not in small_addresses]
    if not args.select:
        assert len(specs)==required
        if SOURCE.read_text()!=render(specs,full_context=True):raise ValueError('Source/spec disagreement')
    words=load_functions([s['address'][2:] for s in specs])
    selected=[];results=[]
    with tempfile.TemporaryDirectory(prefix='tak-context-') as tmp:
        source=Path(tmp)/'models.c';source.write_text(render(specs,full_context=True));lib=Path(tmp)/'models.dylib'
        subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O2','-DTAK_VERIFY_BUDGET','-dynamiclib',
                        '-I'+str(ROOT/'src/recovered'),str(source),'-o',str(lib)],check=True)
        library=c.CDLL(str(lib));library.tak_integer_set_fuel.argtypes=[c.c_uint32];library.tak_integer_set_fuel.restype=None
        library.tak_integer_exhausted.argtypes=[];library.tak_integer_exhausted.restype=c.c_int
        for spec in specs:
            result=verify(spec,words[spec['address'][2:]],library)
            if result is None:
                if args.select:continue
                raise AssertionError('Insufficient terminating cases: '+spec['address'])
            selected.append(spec);results.append(result)
            print(f'PASS {len(results)}/{required}: {spec["address"]}: 64 context/memory comparisons',flush=True)
            if args.select and len(results)==required:break
    if len(results)!=required:raise ValueError(f'Only {len(results)} verified; require {required}')
    if args.select:
        SPECS.write_text(json.dumps({'revision':'GJUE78 rev 0','routines':selected},indent=2)+'\n')
        SOURCE.write_text(render(selected,full_context=True))
    summary={'revision':'GJUE78 rev 0','functions':len(results),'original_bytes':sum(r['original_bytes'] for r in results),
             'instructions_verified':sum(r['instructions_verified'] for r in results),
             'instructions_exercised':sum(r['instructions_exercised'] for r in results),
             'differential_cases':sum(r['differential_cases'] for r in results),
             'original_budget_rejections':sum(r['original_budget_rejections'] for r in results),
             'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'binary_matching':False,'routines':results}
    (ROOT/'analysis/context-helpers-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f'PASS: {required} context models, {summary["original_bytes"]} bytes, {summary["differential_cases"]} comparisons')


if __name__=='__main__':main()
