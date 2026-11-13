#!/usr/bin/env python3
"""Verify complete integer C models against original PowerPC routines.

--select reads provisional recovery specs and keeps the first 600 routines
with 64 terminating differential cases. This is not a binary match checker.
"""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import random
import subprocess
import tempfile

from check_runtime_helpers import Runtime, API
from integer_recovery import render
from ppc_leaf import execute, load_functions, MASK

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT/'analysis/integer-helper-specs.json'
SOURCE = ROOT/'src/recovered/integer_leaf_helpers.c'
REQUIRED = 64
FUEL = 1024
EDGES = (0,1,2,3,7,8,15,16,31,32,127,128,255,256,257,32767,32768,65535,
         65536,0x7fffffff,0x80000000,0x80000001,0xfffffffe,MASK,0x55555555,0xaaaaaaaa)


def byte(address, seed, style):
    if style == 0 or address < 64: return 0
    if style == 1: return 255
    x = (address ^ seed) & MASK
    x = ((x ^ (x >> 16))*0x45d9f3b) & MASK
    x = ((x ^ (x >> 16))*0x45d9f3b) & MASK
    x ^= x >> 16
    if style == 2: return (x & 3) if address & 3 == 3 else 0
    return x & 255


def read(memory, address, size, seed, style):
    value = int.from_bytes(bytes(memory.data.get((address+i) & MASK,
                                byte((address+i) & MASK, seed, style)) for i in range(size)), 'big')
    memory.events.append(('read',size,address,value))
    return value


class Memory:
    def __init__(self, seed, style, data):
        self.seed,self.style,self.data = seed,style,dict(data)
        self.events = []

    def read(self, address, size): return read(self,address,size,self.seed,self.style)

    def write(self, address, value, size):
        self.events.append(('write',size,address,value))
        for i,b in enumerate(value.to_bytes(size,'big')): self.data[(address+i)&MASK] = b


def scenario(address, trial):
    rng = random.Random(int(address,16)+trial)
    style = (0,2,1,3,0,2,0,2)[trial % 8]
    if trial < 32:
        args = [EDGES[trial % len(EDGES)]]*8
    elif trial < 64:
        args = [trial % 5]*8
        args[(trial//5) % 8] = EDGES[trial % len(EDGES)]
    elif trial < 128:
        args = [0x81000000,trial%5,trial%8,0x81001000,0,1,0,0]
        if trial & 8: args[2] = 0x81002000
        if trial & 16: args[1] = 0x81003000
    elif trial < 192:
        args = [0]*8
        args[(trial//8) % 8] = rng.getrandbits(32)
    else:
        args = [rng.randrange(8) for _ in range(8)]
        if trial & 4: args[0] = MASK-3
        if trial & 8: args[1] = args[0]
    data = {}
    if 64 <= trial < 128:
        # Acyclic synthetic object/table graph; scalar words interspersed
        # with forward pointers exercise traversal without assuming layouts.
        for i in range(5):
            base = 0x81000000+i*0x1000
            for offset in range(0,0x400,4):
                value = (0,1,3,(0x81000000+(i+1)*0x1000) if i<4 else 0)[(offset//4+trial)%4]
                for j,b in enumerate(value.to_bytes(4,'big')): data[base+offset+j] = b
    return args,rng.getrandbits(32),style,data


def verify_one(spec, words, library):
    address = spec['address'][2:]
    function = getattr(library,'tak_integer_'+address)
    function.argtypes = [c.POINTER(c.c_uint32), c.POINTER(c.c_uint32), c.POINTER(API)]
    function.restype = c.c_uint32
    visited, accepted, budget_rejections = set(),[],0
    for trial in range(256):
        args,seed,style,data = scenario(address,trial)
        original = Memory(seed,style,data)
        execution = set()
        registers = []
        try:
            expected = execute(words,args,original,budget=FUEL,visited=execution,final_registers=registers)
        except ValueError as error:
            if str(error) != 'PowerPC instruction budget exhausted': raise
            budget_rejections += 1
            continue
        native = Runtime(); native.data = dict(data)
        native.read = lambda a,size: read(native,a,size,seed,style)
        library.tak_integer_set_fuel(FUEL)
        output = (c.c_uint32*8)()
        actual = function((c.c_uint32*8)(*args),output,c.byref(native.runtime))
        native.clean()
        if library.tak_integer_exhausted():
            raise AssertionError(f'{address} trial {trial}: C exhausted fuel while original returned')
        if actual != expected:
            raise AssertionError(f'{address} trial {trial}: r3 {actual:08X} != {expected:08X}')
        if list(output) != registers[3:11]:
            raise AssertionError(f'{address} trial {trial}: integer return/register outputs differ')
        if native.events != original.events:
            n = next((i for i,pair in enumerate(zip(native.events,original.events)) if pair[0]!=pair[1]),
                     min(len(native.events),len(original.events)))
            raise AssertionError(f'{address} trial {trial}: trace {n}: '
                                 f'{native.events[n:n+3]} != {original.events[n:n+3]}')
        assert native.data == original.data,(address,trial,'final memory differs')
        visited |= execution
        accepted.append(trial)
        if len(accepted) == REQUIRED: break
    if len(accepted) != REQUIRED: return None
    return {'address':spec['address'],'original_name':spec['original_name'],
            'original_bytes':len(words)*4,'instructions_verified':len(words),
            'instructions_exercised':len(visited),'static_reachable_instructions':spec['static_reachable_instructions'],
            'unexercised_addresses':[f'0x{pc:08X}' for pc in sorted(set(words)-visited)],
            'differential_cases':len(accepted),'accepted_trials':accepted,
            'original_budget_rejections':budget_rejections,
            'scope':'Game or SDK/runtime indexed integer function; original types unresolved',
            'source':'src/recovered/integer_leaf_helpers.c'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--select',type=Path,help='Select 600 from provisional specs')
    args=parser.parse_args()
    specs=json.loads((args.select if args.select else SPECS).read_text())
    if isinstance(specs,dict): specs=specs['routines']
    if not args.select:
        assert len(specs)==600
        if SOURCE.read_text()!=render(specs): raise ValueError('Source/spec disagreement')
    words=load_functions([s['address'][2:] for s in specs])
    results,selected,rejected=[],[],[]
    with tempfile.TemporaryDirectory(prefix='tak-integer-models-') as tmp:
        source=Path(tmp)/'models.c'; source.write_text(render(specs))
        output=Path(tmp)/'models.dylib'
        subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O2',
                        '-DTAK_VERIFY_BUDGET','-dynamiclib','-I'+str(ROOT/'src/recovered'),
                        str(source),'-o',str(output)],check=True)
        library=c.CDLL(str(output))
        library.tak_integer_set_fuel.argtypes=[c.c_uint32];library.tak_integer_set_fuel.restype=None
        library.tak_integer_exhausted.argtypes=[];library.tak_integer_exhausted.restype=c.c_int
        for spec in specs:
            result=verify_one(spec,words[spec['address'][2:]],library)
            if result is None:
                if not args.select:raise AssertionError('Insufficient terminating cases: '+spec['address'])
                rejected.append(spec['address']);continue
            results.append(result);selected.append(spec)
            print(f'PASS {len(results)}: {spec["address"]}: 64 terminating original-PPC/C comparisons; '
                  f'{result["instructions_exercised"]}/{result["instructions_verified"]} instructions exercised',flush=True)
            if args.select and len(results)==600:break
    if len(results)!=600:raise ValueError(f'Only {len(results)} verified routines; need 600')
    if args.select:
        SPECS.write_text(json.dumps({'revision':'GJUE78 rev 0','kind':'Complete low-level integer C control flow',
                                    'function_count':600,'routines':selected},indent=2)+'\n')
        SOURCE.write_text(render(selected))
    summary={'revision':'GJUE78 rev 0','functions':len(results),
             'original_bytes':sum(r['original_bytes'] for r in results),
             'instructions_verified':sum(r['instructions_verified'] for r in results),
             'instructions_exercised':sum(r['instructions_exercised'] for r in results),
             'differential_cases':sum(r['differential_cases'] for r in results),
             'original_budget_rejections':sum(r['original_budget_rejections'] for r in results),
             'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'spec_sha256':hashlib.sha256(SPECS.read_bytes()).hexdigest(),
             'binary_matching':False,'selection_insufficient_cases':rejected,'routines':results}
    (ROOT/'analysis/integer-helpers-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f'PASS: 600 complete models, {summary["original_bytes"]} original bytes, '
          f'{summary["differential_cases"]} differential cases; '
          f'{summary["instructions_exercised"]}/{summary["instructions_verified"]} instructions exercised')


if __name__=='__main__':main()
