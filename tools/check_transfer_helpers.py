#!/usr/bin/env python3
"""Verify finite-domain scalar transfer projections against original words."""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

from check_runtime_helpers import Runtime,API
from check_integer_helpers import Memory,read,scenario
from check_call_helpers import contract as integer_contract
from ppc_leaf import execute,load_functions
from transfer_recovery import translate,render
from remaining_regions import remaining_rows

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'src/recovered/scalar_transfer_helpers.c'
SPECS=ROOT/'analysis/scalar-transfer-helper-specs.json'
REPORT=ROOT/'analysis/scalar-transfer-helpers-summary.json'
FUEL=2048
TRIALS=256
INVOKE=c.CFUNCTYPE(None,c.c_uint32,c.POINTER(c.c_uint32),c.POINTER(c.c_uint64))
class Calls(c.Structure):_fields_=[('invoke',INVOKE)]


def wide(single):
    return int.from_bytes(struct.pack('>d',struct.unpack('>f',single.to_bytes(4,'big'))[0]),'big')

VALUES=[wide(x) for x in (0,0x80000000,0x3f800000,0xbf800000,0x40000000,0x3f000000,0x00800000,0x7f7fffff)]


def contract(memory,target,state,fp,trial):
    before=len(memory.events)
    integer_contract(memory,target,state,trial)
    memory.events[before]=memory.events[before]+(tuple(fp),)
    fp[0]=VALUES[(target+trial)%len(VALUES)]
    fp[1]=VALUES[(trial//4)%4]


def verify(spec,words,library):
    address=spec['address'][2:];fn=getattr(library,'tak_transfer_'+address)
    fn.argtypes=[c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(c.c_uint64),c.POINTER(c.c_uint64),c.POINTER(API),c.POINTER(Calls)];fn.restype=c.c_uint32
    accepted=[];visited=set();excluded={'budget':0,'undefined_division':0,'floating_domain':0};observed_calls=0
    for trial in range(TRIALS):
        args,seed,style,data=scenario(address,trial)
        initial=[args[i%8] for i in range(32)];initial[1]=0x90010000;initial[2]=0x8033b140;initial[13]=0x80338280
        initial += [0x80001000+trial*4,trial%5]+[(trial+i)%8 for i in range(8)]
        fp=[VALUES[(trial+i)%len(VALUES)] for i in range(32)]
        original=Memory(seed,style,data);out=[];fout=[];seen=set()
        try:
            expected=execute(words,args,original,budget=FUEL,visited=seen,initial_context=initial,final_context=out,initial_fpr=fp,final_fpr=fout,
                             floating_calls=lambda target,state,scalar:contract(original,target,state,scalar,trial))
        except ValueError as error:
            category={'PowerPC instruction budget exhausted':'budget','Undefined integer division':'undefined_division','Outside floating transfer domain':'floating_domain'}.get(str(error))
            if category is None:raise
            excluded[category]+=1;continue
        native=Runtime();native.data=dict(data);native.read=lambda a,size:read(native,a,size,seed,style)
        def invoke(target,pointer,scalar):
            try:
                state=list(pointer[:42]);floating=list(scalar[:32]);contract(native,target,state,floating,trial)
                for i,value in enumerate(state):pointer[i]=value
                for i,value in enumerate(floating):scalar[i]=value
            except Exception as error:native.errors.append(error)
        callback=INVOKE(invoke);calls=Calls(callback);output=(c.c_uint32*42)();foutput=(c.c_uint64*32)()
        library.tak_integer_set_fuel(FUEL)
        actual=fn((c.c_uint32*42)(*initial),output,(c.c_uint64*32)(*fp),foutput,c.byref(native.runtime),c.byref(calls));native.clean()
        if library.tak_integer_exhausted():raise AssertionError((address,trial,'C budget exhausted'))
        if actual!=expected or list(output)!=out or list(foutput)!=fout:raise AssertionError((address,trial,'context mismatch'))
        if native.events!=original.events:
            index=next((i for i,pair in enumerate(zip(native.events,original.events)) if pair[0]!=pair[1]),min(len(native.events),len(original.events)))
            raise AssertionError((address,trial,'trace mismatch',index,native.events[index:index+2],original.events[index:index+2]))
        if native.data!=original.data:raise AssertionError((address,trial,'memory mismatch'))
        observed_calls+=sum(e[0]=='external_call' for e in original.events);visited|=seen;accepted.append(trial)
        if len(accepted)>=64 and (observed_calls or not spec['external_call_sites']):break
    passed=len(accepted)>=64 and (observed_calls or not spec['external_call_sites'])
    return {'address':spec['address'],'original_name':spec['original_name'],'original_bytes':len(words)*4,'accepted':passed,
            'instructions_verified':len(words),'instructions_exercised':len(visited),'unexercised_addresses':[f'0x{pc:08X}' for pc in sorted(set(words)-visited)],
            'differential_cases':len(accepted),'accepted_trials':accepted,'excluded_attempts':excluded,'observed_opaque_calls':observed_calls,
            'source':SOURCE.relative_to(ROOT).as_posix(),'scope':'Finite-domain scalar PS0 transfers and integer context; real callees, PS1, FPSCR, XER and original ABI unresolved'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--select',action='store_true');parser.add_argument('--reproduce',action='store_true');args=parser.parse_args()
    if args.select:
        specs=[]
        for row in remaining_rows():
            try:spec=translate(row)
            except ValueError:continue
            if spec['floating_transfer_instructions']:specs.append(spec)
    else:
        specs=json.loads(SPECS.read_text())['routines']
        if render(specs)!=SOURCE.read_text():raise ValueError('Source/specification disagreement')
    if args.reproduce:
        import csv,re
        from remaining_regions import ROOT as original_root
        rows={r['address']:r for r in csv.DictReader((original_root/'analysis/functions.csv').open())}
        words=load_functions([s['address'][2:] for s in specs]);recovered=[];files={}
        for spec in specs:
            row=dict(rows[spec['address']]);path=row['assembly']
            if path not in files:files[path]=(ROOT/path).read_text()
            name=re.escape(row['name']);body=re.search(r'^\.fn '+name+r',.*?^\.endfn '+name+r'\s*$',files[path],re.M|re.S)[0]
            row['ins']=re.findall(r'/\*.*?\*/\s*([^\n]+)',body);row['words']=list(words[row['address'][2:]].values());recovered.append(translate(row))
        if recovered!=specs:raise ValueError('Original disassembly does not reproduce specifications')
        print(f'PASS: {len(specs)} scalar-transfer projections reproduce from original words/disassembly');return
    words=load_functions([s['address'][2:] for s in specs]);selected=[];results=[];excluded=[]
    with tempfile.TemporaryDirectory(prefix='tak-scalar-transfers-') as tmp:
        path=Path(tmp)/'models.c';path.write_text(render(specs));out=Path(tmp)/'models.dylib'
        subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O2','-DTAK_VERIFY_BUDGET','-dynamiclib','-I'+str(ROOT/'src/recovered'),str(path),'-o',str(out)],check=True)
        library=c.CDLL(str(out));library.tak_integer_set_fuel.argtypes=[c.c_uint32];library.tak_integer_set_fuel.restype=None;library.tak_integer_exhausted.restype=c.c_int
        for i,spec in enumerate(specs,1):
            result=verify(spec,words[spec['address'][2:]],library)
            if not result['accepted']:
                if not args.select:raise AssertionError('Lost comparison evidence: '+spec['address'])
                excluded.append(result);print(f'EXCLUDE {i}/{len(specs)}: {spec["address"]}: {result["differential_cases"]} comparisons',flush=True);continue
            selected.append(spec);results.append(result);print(f'PASS {i}/{len(specs)}: {spec["address"]}: {result["differential_cases"]} comparisons',flush=True)
    if args.select:
        SPECS.write_text(json.dumps({'revision':'GJUE78 rev 0','kind':'Finite-domain PS0 transfer projections','routines':selected},indent=2)+'\n');SOURCE.write_text(render(selected))
        (ROOT/'analysis/scalar-transfer-selection-summary.json').write_text(json.dumps({'candidate_count':len(specs),'selected_count':len(selected),'excluded':excluded},indent=2)+'\n')
    summary={'revision':'GJUE78 rev 0','functions':len(results),'original_bytes':sum(r['original_bytes'] for r in results),
             'instructions_verified':sum(r['instructions_verified'] for r in results),'instructions_exercised':sum(r['instructions_exercised'] for r in results),
             'differential_cases':sum(r['differential_cases'] for r in results),'observed_opaque_calls':sum(r['observed_opaque_calls'] for r in results),
             'excluded_attempts':{k:sum(r['excluded_attempts'][k] for r in results) for k in ('budget','undefined_division','floating_domain')},
             'trial_limit':TRIALS,'caller_instruction_budget':FUEL,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'spec_sha256':hashlib.sha256(SPECS.read_bytes()).hexdigest(),'binary_matching':False,'routines':results}
    REPORT.write_text(json.dumps(summary,indent=2)+'\n')
    print(f'PASS: {len(results)} scalar-transfer projections, {summary["original_bytes"]} bytes, {summary["differential_cases"]} comparisons')


if __name__=='__main__':main()
