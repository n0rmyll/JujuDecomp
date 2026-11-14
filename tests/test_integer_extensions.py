"""Compare new generated arithmetic against the independent word decoder."""
import ctypes as c
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from integer_recovery import render, translate
from ppc_leaf import execute
from check_runtime_helpers import Runtime, API
from check_call_helpers import Calls, INVOKE

ROOT=Path(__file__).resolve().parents[1]


class ExtensionComparisons(unittest.TestCase):
    def test_native_indirect_tail_dispatch(self):
        start=0x80001000
        spec=translate({'address':f'0x{start:08X}','name':'test','size':'12','ins':['bctr','li r3, 9','blr']},full_context=True,allow_calls=True)
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'dispatch.c';source.write_text(render([spec],full_context=True,allow_calls=True));lib=Path(tmp)/'dispatch.dylib'
            subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O2','-dynamiclib','-I'+str(ROOT/'src/recovered'),str(source),'-o',str(lib)],check=True)
            fn=c.CDLL(str(lib)).tak_call_80001000
            fn.argtypes=[c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(API),c.POINTER(Calls)];fn.restype=c.c_uint32
            for target,want in ((start+5,9),(0x80002003,17)):
                events=[]
                def invoke(address,state):events.append(address);state[3]=17
                callback=INVOKE(invoke);calls=Calls(callback);runtime=Runtime();initial=[0]*42;initial[33]=target;initial[32]=0x1234;output=(c.c_uint32*42)()
                actual=fn((c.c_uint32*42)(*initial),output,c.byref(runtime.runtime),c.byref(calls))
                self.assertEqual(actual,want)
                self.assertEqual(output[32],0x1234)
                self.assertEqual(events,[] if target==start+5 else [0x80002000])

    def test_native_integer_extensions(self):
        instructions=[('mulhw r3, r3, r4',75),('mulhwu r3, r3, r4',11),
                      ('divw r3, r3, r4',491),('divwu r3, r3, r4',459),
                      ('subfc r3, r3, r4',8)]
        specs=[];words=[]
        for i,(text,xo) in enumerate(instructions):
            start=0x80001000+i*0x100
            specs.append(translate({'address':f'0x{start:08X}','name':'test','size':'8','ins':[text,'blr']},full_context=True))
            words.append({start:(31<<26)|(3<<21)|(3<<16)|(4<<11)|(xo<<1),start+4:0x4e800020})
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'extensions.c';source.write_text(render(specs,full_context=True));lib=Path(tmp)/'extensions.dylib'
            subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O2','-dynamiclib','-I'+str(ROOT/'src/recovered'),str(source),'-o',str(lib)],check=True)
            library=c.CDLL(str(lib))
            values=(0,1,2,7,0x7fffffff,0x80000000,0xfffffff9,0xfffffffe,0xffffffff)
            for spec,original in zip(specs,words):
                fn=getattr(library,'tak_extended_'+spec['address'][2:])
                fn.argtypes=[c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(API)];fn.restype=c.c_uint32
                for a in values:
                    for b in values:
                        context=[0]*42;context[3:5]=[a,b];expected=[];runtime=Runtime()
                        try:result=execute(original,(a,b),runtime,initial_context=context,final_context=expected)
                        except ValueError as error:
                            self.assertEqual(str(error),'Undefined integer division');continue
                        output=(c.c_uint32*42)()
                        actual=fn((c.c_uint32*42)(*context),output,c.byref(runtime.runtime))
                        self.assertEqual(actual,result,(spec['address'],a,b))
                        self.assertEqual(list(output),expected)


if __name__=='__main__':unittest.main()
