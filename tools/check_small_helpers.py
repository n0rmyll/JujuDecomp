#!/usr/bin/env python3
"""Recover small target-layout C routines and require exact compiler matches.

No instruction masking or assembly substitution. A function enters this batch
only when its entire compiled code equals the original indexed region.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

from ppc_leaf import load_functions, signed
from ppc_matching import function_code

ROOT=Path(__file__).resolve().parents[1]
SPECS=ROOT/'analysis/small-helper-specs.json'
SOURCE=ROOT/'src/matching/small_helpers.cpp'


def propose(row, words):
    ins=row['ins'];address=row['address'];body=None;decl=[];symbols={};kind=None
    if ins==['blr']:body='';kind='empty method';result='void';params='void'
    elif len(ins)==2 and ins[-1]=='blr':
        if len(ins[0].split(None,1))!=2:return None
        op,args=ins[0].split(None,1);args=re.split(r',\s*',args)
        word=next(iter(words.values()));low=signed(word,16)
        result='u32';params='u32 a, u32 b, u32 c, u32 d'
        if op in ('li','lis') and args[0]=='r3':
            if '@sda21' in args[1]:
                base=(word>>16)&31
                target=((0x8033b140 if base==2 else 0x80338280)+low)&0xffffffff
                name=f'small_global_{target:08X}';decl=[f'extern u8 {name};'];symbols[name]=target
                body=f'return (u32)&{name};';kind='small-data address'
            else:
                value=(low<<(16 if op=='lis' else 0))&0xffffffff
                body=f'return 0x{value:08X}u;';kind='constant return'
        elif op in ('addi','subi') and args[:2]==['r3','r3']:
            body=f'return a + 0x{low&0xffffffff:08X}u;';kind='address/integer offset'
        elif op=='mr' and args[0]=='r3' and args[1] in ('r4','r5','r6'):
            body='return '+{'r4':'b','r5':'c','r6':'d'}[args[1]]+';';kind='argument forwarding'
        elif op in ('lwz','lbz','lhz','lha','stw','stb','sth','lfs','stfs'):
            is_store=op.startswith('st');is_float=op in ('lfs','stfs')
            if args[0] not in (('f1',) if is_float else ('r3','r4','r5','r6')):return None
            if not is_store and args[0] not in ('r3','f1'):return None
            ty={'lwz':'u32','stw':'u32','lbz':'u8','stb':'u8','lhz':'u16','sth':'u16','lha':'s16','lfs':'float','stfs':'float'}[op]
            m=re.fullmatch(r'(.+)\((r\d+)\)',args[1])
            if not m:return None
            displacement,base=m.groups()
            if '@sda21' in displacement:
                register=(word>>16)&31
                if register not in (2,13):return None
                target=((0x8033b140 if register==2 else 0x80338280)+low)&0xffffffff
                name=f'small_global_{target:08X}'
                qualifier='const ' if register==2 and not is_store else ''
                decl=[f'extern {qualifier}{ty} {name};'];symbols[name]=target
                location=name
            elif base in ('r3','r4','r5','r6') and '@' not in displacement:
                location=f'*({ty} *)('+{'r3':'a','r4':'b','r5':'c','r6':'d'}[base]+f' + 0x{low&0xffffffff:08X}u)'
            else:return None
            if is_float:
                if is_store:
                    if base!='r3':return None
                    result='void';params='u32 a, float value';body=f'{location} = value;';kind='float field store'
                else:result='float';body=f'return {location};';kind='float field load'
            elif is_store:
                result='void';value={'r3':'a','r4':'b','r5':'c','r6':'d'}[args[0]]
                body=f'{location} = ({ty}){value};';kind='integer field/global store'
            else:body=f'return {location};';kind='integer field/global load'
        else:return None
    else:return None
    if body is None:return None
    return {'address':address,'original_name':row['name'],'original_bytes':int(row['size']),
            'kind':kind,'declarations':decl,'symbols':symbols,'result_type':result,'parameters':params,'body':body}


def render(specs):
    out=['/* Target-layout C recovered from complete small original routines.',
         ' * Exact matching is measured by tools/check_small_helpers.py.',
         ' * Includes explicit empty methods and constant-return stubs.',
         ' */','typedef unsigned char u8;','typedef unsigned short u16;',
         'typedef signed short s16;','typedef unsigned int u32;','extern "C" {']
    # Declarations may differ for a shared address; give each function a scope
    # by compiling each original routine under its own preprocessor branch.
    for s in specs:
        a=s['address'][2:]
        out += [f'#if TAK_SMALL_FN == 0x{a}']+s['declarations']
        out += [f'{s["result_type"]} small_{a}({s["parameters"]}) {{ {s["body"]} }}','#endif']
    out += ['}','']
    return '\n'.join(out)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--select',type=Path,help='Recover from provisional tiny-region list')
    args=parser.parse_args()
    if args.select:
        rows=json.loads(args.select.read_text())
        candidates=[r for r in rows if r['ins'][-1]=='blr']
        words=load_functions([r['address'][2:] for r in candidates])
        specs=[s for r in candidates if (s:=propose(r,words[r['address'][2:]])) is not None]
    else:
        specs=json.loads(SPECS.read_text())['routines']
        words=load_functions([s['address'][2:] for s in specs])
        if SOURCE.read_text()!=render(specs):raise ValueError('Source/spec disagreement')
    output=ROOT/'build/small-matching';output.mkdir(parents=True,exist_ok=True)
    source=output/'candidates.cpp';source.write_text(render(specs))
    compiler=ROOT/'tools/mwcc/GC/1.3.2/mwcceppc.exe';runner=ROOT/'tools/wibo'
    matches=[];results=[]
    for spec in specs:
        address=spec['address'][2:];obj=output/f'{address}.o'
        command=[str(runner),str(compiler),'-c','-lang','c++','-proc','gekko','-O4,p','-nodefaults','-fp','hard',
                 f'-DTAK_SMALL_FN=0x{address}',str(source),'-o',str(obj)]
        run=subprocess.run(command,capture_output=True,text=True)
        result={'address':spec['address'],'original_name':spec['original_name'],
                'original_bytes':spec['original_bytes'],'kind':spec['kind'],'exact_match':False}
        if run.returncode:
            result.update(status='compile_error',error=run.stdout+run.stderr)
        else:
            actual,relocations=function_code(obj,'small_'+address,int(address,16),spec['symbols'])
            expected=b''.join(w.to_bytes(4,'big') for w in words[address].values())
            result.update(status='match' if actual==expected else 'different',exact_match=actual==expected,
                          candidate_bytes=len(actual),object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),
                          resolved_relocations=relocations)
        results.append(result)
        if result['exact_match']:matches.append(spec)
        elif not args.select:raise AssertionError(f'Exact match lost: {address}: {result}')
        print(f'{result["status"]}: {address}: {spec["kind"]}',flush=True)
    if args.select:
        SPECS.write_text(json.dumps({'revision':'GJUE78 rev 0','routines':matches},indent=2)+'\n')
        SOURCE.parent.mkdir(parents=True,exist_ok=True);SOURCE.write_text(render(matches))
    summary={'revision':'GJUE78 rev 0','dol_sha256':hashlib.sha256((ROOT/'analysis/main.dol').read_bytes()).hexdigest(),
             'checked':len(results),'matched':len(matches),
             'matched_bytes':sum(s['original_bytes'] for s in matches),
             'compiler':'CodeWarrior GC 1.3.2','flags':'-c -lang c++ -proc gekko -O4,p -nodefaults -fp hard',
             'compiler_sha256':hashlib.sha256(compiler.read_bytes()).hexdigest(),
             'runner_sha256':hashlib.sha256(runner.read_bytes()).hexdigest(),
             'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'scope':'Individual complete functions; no executable rebuild','results':results}
    (ROOT/'analysis/small-matching-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f'PASS: {len(matches)} complete function-code matches, {summary["matched_bytes"]} original bytes')


if __name__=='__main__':main()
