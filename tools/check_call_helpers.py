#!/usr/bin/env python3
"""Compositional comparisons of caller bodies with opaque external callees.

The callback fixtures are test contracts, not recovered callee implementations.
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
from ppc_leaf import execute, load_functions, MASK

ROOT=Path(__file__).resolve().parents[1]
SPECS=ROOT/'analysis/call-helper-specs.json'
SOURCE=ROOT/'src/recovered/call_leaf_helpers.c'
FUEL=2048
TRIALS=256
INVOKE=c.CFUNCTYPE(None,c.c_uint32,c.POINTER(c.c_uint32))


class Calls(c.Structure):
    _fields_=[('invoke',INVOKE)]


def contract(memory,target,state,trial):
    """A deterministic, normal-return opaque callee used in both executions.

    Preserves stack/base/nonvolatile registers and LR. Returns zero, one,
    a synthetic object pointer, or a small scalar. One mode writes a bounded
    object field to verify caller reloads after possible external effects.
    """
    memory.events.append(('external_call',target,tuple(state)))
    mode=(trial//4)%4
    argument=state[3]
    if mode==3 and 0x81000000<=argument<0x81010000:
        value=memory.read((argument+0x10)&MASK,4)
        memory.write((argument+0x10)&MASK,(value+1)&MASK,4)
    state[0]=(target^trial)&MASK
    state[3]=(0 if mode==0 else 1 if mode==1 else 0x81000000+(target%5)*0x1000 if mode==2 else (target^trial)&3)
    state[34]=(1,2,4)[trial%3]
    state[35]=(1,2,4)[(trial+1)%3]


def verify(spec,words,library):
    address=spec['address'][2:];fn=getattr(library,'tak_call_'+address)
    fn.argtypes=[c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(API),c.POINTER(Calls)]
    fn.restype=c.c_uint32
    accepted=[];visited=set();rejected=0;undefined=0;observed_calls=0
    for trial in range(TRIALS):
        args,seed,style,data=scenario(address,trial)
        initial=[args[i%8] for i in range(32)]
        initial[1]=0x90010000;initial[2]=0x8033b140;initial[13]=0x80338280
        initial += [0x80001000+trial*4,trial%5]+[(trial+i)%8 for i in range(8)]
        original=Memory(seed,style,data);out=[];seen=set()
        try:
            expected=execute(words,args,original,budget=FUEL,visited=seen,initial_context=initial,final_context=out,
                             calls=lambda target,state:contract(original,target,state,trial))
        except ValueError as error:
            if str(error)=='Undefined integer division':
                undefined+=1;continue
            if str(error)!='PowerPC instruction budget exhausted':raise
            rejected+=1;continue
        native=Runtime();native.data=dict(data)
        native.read=lambda a,size:read(native,a,size,seed,style)

        def invoke(target,pointer):
            try:
                state=list(pointer[:42]);contract(native,target,state,trial)
                for i,value in enumerate(state):pointer[i]=value
            except Exception as error:native.errors.append(error)

        callback=INVOKE(invoke);calls=Calls(callback);output=(c.c_uint32*42)()
        library.tak_integer_set_fuel(FUEL)
        actual=fn((c.c_uint32*42)(*initial),output,c.byref(native.runtime),c.byref(calls));native.clean()
        if library.tak_integer_exhausted():raise AssertionError((address,trial,'C budget exhausted'))
        if actual!=expected or list(output)!=out:
            indices=[i for i,pair in enumerate(zip(output,out)) if pair[0]!=pair[1]]
            raise AssertionError((address,trial,'context differs',indices))
        if native.events!=original.events:
            n=next((i for i,pair in enumerate(zip(native.events,original.events)) if pair[0]!=pair[1]),min(len(native.events),len(original.events)))
            raise AssertionError((address,trial,'event trace',n,native.events[n:n+2],original.events[n:n+2]))
        assert native.data==original.data,(address,trial,'final memory')
        observed_calls+=sum(e[0]=='external_call' for e in original.events)
        visited|=seen;accepted.append(trial)
        if len(accepted)>=64 and (observed_calls or not spec['external_call_sites']):break
    if len(accepted)<64 or (spec['external_call_sites'] and not observed_calls):return None
    return {'address':spec['address'],'original_name':spec['original_name'],'original_bytes':len(words)*4,
            'instructions_verified':len(words),'instructions_exercised':len(visited),
            'unexercised_addresses':[f'0x{pc:08X}' for pc in sorted(set(words)-visited)],
            'differential_cases':len(accepted),'accepted_trials':accepted,'original_budget_rejections':rejected,
            'undefined_division_rejections':undefined,'observed_opaque_calls':observed_calls,'external_call_sites':spec['external_call_sites'],
            'scope':('Integer caller body with unresolved opaque external callees' if spec['external_call_sites'] else 'Call-free integer context projection'),
            'source':SOURCE.relative_to(ROOT).as_posix()}


def main():
    global SPECS,SOURCE,TRIALS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--select',type=Path)
    parser.add_argument('--batch',type=int,choices=(3,4,5,6),default=3)
    args=parser.parse_args()
    if args.batch==4:
        SPECS=ROOT/'analysis/fourth-call-helper-specs.json'
        SOURCE=ROOT/'src/recovered/fourth_call_leaf_helpers.c'
    if args.batch==5:
        SPECS=ROOT/'analysis/fifth-sixth-call-helper-specs.json'
        SOURCE=ROOT/'src/recovered/fifth_sixth_call_leaf_helpers.c'
    if args.batch==6:
        SPECS=ROOT/'analysis/remaining-integer-helper-specs.json'
        SOURCE=ROOT/'src/recovered/remaining_integer_helpers.c'
        TRIALS=1024
    specs=json.loads((args.select if args.select else SPECS).read_text())
    if isinstance(specs,dict):specs=specs['routines']
    count=(None if args.select else len(specs)) if args.batch==6 else 2000 if args.batch==5 else 1000
    if not args.select:
        assert len(specs)==count
        if SOURCE.read_text()!=render(specs,full_context=True,allow_calls=True):raise ValueError('Source/spec disagreement')
    words=load_functions([s['address'][2:] for s in specs]);selected=[];results=[];insufficient=[]
    with tempfile.TemporaryDirectory(prefix='tak-caller-models-') as tmp:
        source=Path(tmp)/'models.c';source.write_text(render(specs,full_context=True,allow_calls=True));out=Path(tmp)/'models.dylib'
        subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O2','-DTAK_VERIFY_BUDGET','-dynamiclib',
                        '-I'+str(ROOT/'src/recovered'),str(source),'-o',str(out)],check=True)
        library=c.CDLL(str(out));library.tak_integer_set_fuel.argtypes=[c.c_uint32];library.tak_integer_set_fuel.restype=None
        library.tak_integer_exhausted.argtypes=[];library.tak_integer_exhausted.restype=c.c_int
        for spec in specs:
            result=verify(spec,words[spec['address'][2:]],library)
            if result is None:
                if args.select:insufficient.append(spec['address']);continue
                raise AssertionError('Insufficient cases: '+spec['address'])
            selected.append(spec);results.append(result)
            print(f'PASS {len(results)}/{count}: {spec["address"]}: {result["differential_cases"]} comparisons; {result["observed_opaque_calls"]} opaque calls',flush=True)
            if args.select and count is not None and len(results)==count:break
    if count is None:count=len(results)
    if len(results)!=count:raise ValueError(f'Only {len(results)} verified integer-context models')
    if args.select:
        SPECS.write_text(json.dumps({'revision':'GJUE78 rev 0','kind':('Integer context models with opaque external boundaries' if args.batch==5 else 'Compositional integer caller bodies'),
                                    'function_count':count,'routines':selected},indent=2)+'\n')
        SOURCE.write_text(render(selected,full_context=True,allow_calls=True))
    summary={'revision':'GJUE78 rev 0','batch':args.batch,'functions':count,'caller_functions':sum(bool(s['external_call_sites']) for s in selected),'call_free_functions':sum(not s['external_call_sites'] for s in selected),'original_bytes':sum(r['original_bytes'] for r in results),
             'instructions_verified':sum(r['instructions_verified'] for r in results),
             'instructions_exercised':sum(r['instructions_exercised'] for r in results),
             'differential_cases':sum(r['differential_cases'] for r in results),
             'observed_opaque_calls':sum(r['observed_opaque_calls'] for r in results),
             'original_budget_rejections':sum(r['original_budget_rejections'] for r in results),
             'undefined_division_rejections':sum(r['undefined_division_rejections'] for r in results),
             'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'spec_sha256':hashlib.sha256(SPECS.read_bytes()).hexdigest(),
             'source_style':'Generated low-level integer C with explicit unresolved callee boundaries',
             'trial_limit':TRIALS,'caller_instruction_budget':FUEL,'binary_matching':False,'insufficient_cases':insufficient,'routines':results}
    report=ROOT/('analysis/fourth-call-helpers-summary.json' if args.batch==4 else 'analysis/call-helpers-summary.json')
    if args.batch==5:report=ROOT/'analysis/fifth-sixth-call-helpers-summary.json'
    if args.batch==6:report=ROOT/'analysis/remaining-integer-helpers-summary.json'
    report.write_text(json.dumps(summary,indent=2)+'\n')
    print(f'PASS: {count} integer-context models, {summary["original_bytes"]} original bytes, '
          f'{summary["differential_cases"]} comparisons; opaque callees remain unresolved')


if __name__=='__main__':main()
