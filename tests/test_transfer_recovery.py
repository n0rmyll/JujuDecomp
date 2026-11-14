"""Finite-domain scalar transfers: independent words versus generated native C."""
import ctypes as c
import random
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from transfer_recovery import translate,render
from ppc_leaf import execute
from check_integer_helpers import Memory,read
from check_runtime_helpers import Runtime,API

ROOT=Path(__file__).resolve().parents[1]
INVOKE=c.CFUNCTYPE(None,c.c_uint32,c.POINTER(c.c_uint32),c.POINTER(c.c_uint64))
class Calls(c.Structure):_fields_=[('invoke',INVOKE)]


class TransferTests(unittest.TestCase):
    def test_native_round_trip_signed_zero_and_normal_bits(self):
        ins=['lfs f1, 0(r3)','fmr f2, f1','stfs f2, 4(r3)','stfd f2, 8(r3)','lfd f3, 8(r3)','blr']
        words=[(48<<26)|(1<<21)|(3<<16),(63<<26)|(2<<21)|(1<<11)|(72<<1),
               (52<<26)|(2<<21)|(3<<16)|4,(54<<26)|(2<<21)|(3<<16)|8,
               (50<<26)|(3<<21)|(3<<16)|8,0x4e800020]
        row={'address':'0x80001000','name':'test','size':str(len(ins)*4),'ins':ins,'words':words}
        spec=translate(row);machine={0x80001000+i*4:w for i,w in enumerate(words)}
        rng=random.Random(42)
        values=[0,0x80000000,0x00800000,0x80800000,0x7f7fffff,0xff7fffff,0x3f800000,0xbf800000]
        values += [(rng.randrange(2)<<31)|(rng.randrange(1,255)<<23)|rng.randrange(1<<23) for _ in range(256)]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.c';path.write_text(render([spec]));lib=Path(tmp)/'test.dylib'
            subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O2','-dynamiclib','-I'+str(ROOT/'src/recovered'),str(path),'-o',str(lib)],check=True)
            fn=c.CDLL(str(lib)).tak_transfer_80001000
            fn.argtypes=[c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(c.c_uint64),c.POINTER(c.c_uint64),c.POINTER(API),c.POINTER(Calls)];fn.restype=c.c_uint32
            callback=INVOKE(lambda target,state,fp:None);calls=Calls(callback)
            for address in (0x1000,0xfffffff8):
                for raw in values:
                    data={(address+i)&0xffffffff:b for i,b in enumerate(raw.to_bytes(4,'big'))}
                    initial=[0]*42;initial[3]=address;fp=[0]*32;expected=[];expected_fp=[];original=Memory(0,0,data)
                    result=execute(machine,(address,),original,initial_context=initial,final_context=expected,initial_fpr=fp,final_fpr=expected_fp)
                    native=Runtime();native.data=dict(data);native.read=lambda a,size:read(native,a,size,0,0)
                    output=(c.c_uint32*42)();foutput=(c.c_uint64*32)()
                    actual=fn((c.c_uint32*42)(*initial),output,(c.c_uint64*32)(*fp),foutput,c.byref(native.runtime),c.byref(calls))
                    self.assertEqual(actual,result);self.assertEqual(list(output),expected);self.assertEqual(list(foutput),expected_fp)
                    self.assertEqual(native.events,original.events);self.assertEqual(native.data,original.data)
                    self.assertEqual(int.from_bytes(bytes(native.data[(address+4+i)&0xffffffff] for i in range(4)),'big'),raw)

    def test_native_callee_receives_and_updates_scalar_context(self):
        ins=['lfs f1, 0(r3)','bl fn_80002000','stfs f1, 4(r3)','blr']
        words=[(48<<26)|(1<<21)|(3<<16),0x48000ffd,(52<<26)|(1<<21)|(3<<16)|4,0x4e800020]
        # The linked branch is at 0x80001004, so its offset is 0xffc.
        spec=translate({'address':'0x80001000','name':'test','size':'16','ins':ins,'words':words})
        machine={0x80001000+i*4:w for i,w in enumerate(words)}
        def update(memory,target,state,fp):
            memory.events.append(('call',target,tuple(state),tuple(fp)))
            self.assertEqual(target,0x80002000)
            self.assertEqual(fp[1],0x3ff0000000000000)
            state[0]=0x1234;fp[1]=0xc000000000000000
        initial=[0]*42;initial[3]=0x1000;fp=[0]*32;data={0x1000+i:b for i,b in enumerate(bytes.fromhex('3f800000'))}
        original=Memory(0,0,data);out=[];fout=[]
        expected=execute(machine,(0x1000,),original,initial_context=initial,final_context=out,initial_fpr=fp,final_fpr=fout,floating_calls=lambda t,s,f:update(original,t,s,f))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'call.c';path.write_text(render([spec]));lib=Path(tmp)/'call.dylib'
            subprocess.run(['clang','-std=c11','-Wall','-Wextra','-Werror','-O2','-dynamiclib','-I'+str(ROOT/'src/recovered'),str(path),'-o',str(lib)],check=True)
            fn=c.CDLL(str(lib)).tak_transfer_80001000
            fn.argtypes=[c.POINTER(c.c_uint32),c.POINTER(c.c_uint32),c.POINTER(c.c_uint64),c.POINTER(c.c_uint64),c.POINTER(API),c.POINTER(Calls)];fn.restype=c.c_uint32
            native=Runtime();native.data=dict(data);native.read=lambda a,size:read(native,a,size,0,0)
            def invoke(target,pointer,scalar):
                state=list(pointer[:42]);floats=list(scalar[:32]);update(native,target,state,floats)
                for i,x in enumerate(state):pointer[i]=x
                for i,x in enumerate(floats):scalar[i]=x
            callback=INVOKE(invoke);calls=Calls(callback);output=(c.c_uint32*42)();foutput=(c.c_uint64*32)()
            actual=fn((c.c_uint32*42)(*initial),output,(c.c_uint64*32)(*fp),foutput,c.byref(native.runtime),c.byref(calls))
            self.assertEqual(actual,expected);self.assertEqual(list(output),out);self.assertEqual(list(foutput),fout)
            self.assertEqual(native.events,original.events);self.assertEqual(native.data,original.data)

    def test_reject_nonfinite_subnormal_and_inexact_singles(self):
        initial=[0]*42;initial[3]=0x1000
        for raw in (1,0x7f800000,0x7fc00001):
            memory=Memory(0,0,{0x1000+i:b for i,b in enumerate(raw.to_bytes(4,'big'))})
            with self.assertRaisesRegex(ValueError,'Outside floating transfer domain'):
                execute({0:(48<<26)|(1<<21)|(3<<16),4:0x4e800020},(0x1000,),memory,initial_context=initial,initial_fpr=[0]*32)
        fp=[0]*32;fp[1]=int.from_bytes(struct.pack('>d',0.1),'big')
        with self.assertRaisesRegex(ValueError,'Outside floating transfer domain'):
            execute({0:(52<<26)|(1<<21)|(3<<16),4:0x4e800020},(0x1000,),Memory(0,0,{}),initial_context=initial,initial_fpr=fp)

    def test_reject_arithmetic_and_recording_moves(self):
        for ins in (['fadds f1, f1, f2','blr'],['fmr. f1, f2','blr']):
            with self.assertRaises(ValueError):translate({'address':'0x80001000','name':'test','size':'8','ins':ins,'words':[0,0x4e800020]})


if __name__=='__main__':unittest.main()
