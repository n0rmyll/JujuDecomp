#!/usr/bin/env python3
"""Verify six routine byte reports and host semantic loader models."""
import ctypes as c
from pathlib import Path
import struct
import subprocess
import tempfile

from inspect_dbu import inspect
from decode_resource_arrays import decode, selected

ROOT = Path(__file__).resolve().parents[1]
ADDRESSES = ('801C5944', '801C59A4', '801C5A04', '801C5BAC', '801C5C34', '801B90D0')
R16 = c.CFUNCTYPE(c.c_uint16, c.c_uint32)
R32 = c.CFUNCTYPE(c.c_uint32, c.c_uint32)
W16 = c.CFUNCTYPE(None, c.c_uint32, c.c_uint16)
W32 = c.CFUNCTYPE(None, c.c_uint32, c.c_uint32)
PROCESS = c.CFUNCTYPE(None, c.c_uint32)


class Memory(c.Structure):
    _fields_ = [('read16', R16), ('read32', R32), ('write16', W16), ('write32', W32)]


class Target:
    def __init__(self):
        self.data = {}
        self.events = []
        self.missing = []
        self.callbacks = (R16(lambda a: self.read(a, 2)), R32(lambda a: self.read(a, 4)),
                          W16(lambda a, v: self.write(a, v, 2)),
                          W32(lambda a, v: self.write(a, v, 4)))
        self.api = Memory(*self.callbacks)

    def put(self, address, value, size):
        self.load(address, value.to_bytes(size, 'big'))

    def load(self, address, raw):
        for i, byte in enumerate(raw):
            self.data[(address+i) & 0xffffffff] = byte

    def get(self, address, size):
        return int.from_bytes(bytes(self.data[(address+i) & 0xffffffff]
                                    for i in range(size)), 'big')

    def read(self, address, size):
        self.events.append(('read', size, address))
        # Record invalid callback accesses outside ctypes, which otherwise
        # suppresses exceptions raised inside a callback.
        if any((address+i) & 0xffffffff not in self.data for i in range(size)):
            self.missing.append((address, size))
            return 0
        return self.get(address, size)

    def write(self, address, value, size):
        self.events.append(('write', size, address, value))
        self.put(address, value, size)


def main():
    for address in ADDRESSES:
        subprocess.run(['python3', str(ROOT/'tools/function_report.py'), f'fn_{address}'], check=True)
    with tempfile.TemporaryDirectory(prefix='tak-loaders-') as tmp:
        libpath = Path(tmp)/'loaders.dylib'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                        '-dynamiclib', str(ROOT/'src/recovered/resource_array.c'),
                        str(ROOT/'src/recovered/resource_loaders.c'), '-o', str(libpath)], check=True)
        lib = c.CDLL(str(libpath))
        loaders = []
        for address in ADDRESSES[:5]:
            fn = getattr(lib, f'tak_load_{address}')
            fn.argtypes = [c.c_uint32]*4 + [c.POINTER(Memory)]
            if address in ADDRESSES[3:5]:
                fn.argtypes += [PROCESS]
            fn.restype = c.c_uint32
            loaders.append(fn)

        p, h, o, s = 0x81000000, 0x82000000, 0x82000010, 0x82000014
        real_runs = records = 0
        for name in ('Preload', 'Hub'):
            archive = (ROOT/f'analysis/{name}.dbu').read_bytes()
            for chunk in inspect(archive)['chunks']:
                if int(chunk['type'], 16) not in selected:
                    continue
                raw = archive[chunk['payload_offset']:chunk['payload_offset']+chunk['payload_size']]
                directory = decode(raw)
                for index, fn in enumerate(loaders):
                    t = Target()
                    t.load(p, raw)
                    t.load(h, struct.pack('>HHI', 0x1234, 0xffff, len(raw)))
                    seen = []
                    callback = PROCESS(lambda item: seen.append(item))
                    args = [p, h, o, s, c.byref(t.api)]
                    result = fn(*args, *([callback] if index >= 3 else []))
                    assert result == 1 and not t.missing
                    assert t.get(o, 4) == p and t.get(s, 4) == len(raw)
                    assert t.get(h+2, 2) == (0xfffe if index >= 3 else 0xffff)
                    expected = bytearray(raw)
                    if directory['flags'] & 1:
                        struct.pack_into('>H', expected, 2, directory['flags'] | 4)
                        for i, offset in enumerate(directory['record_offsets']):
                            struct.pack_into('>I', expected, 4+4*i, p+offset)
                    assert bytes(t.data[p+i] for i in range(len(raw))) == expected
                    assert seen == ([p+offset for offset in directory['record_offsets']] if index >= 3 else [])
                    if index >= 3:
                        records += len(seen)
                    real_runs += 1

        # Output/header alias proves publication happens before the size read.
        for fn in loaders[:3]:
            t = Target()
            t.load(p, struct.pack('>HHI', 0, 2, 16))
            t.load(h, bytes(8))
            assert fn(p, h, h+4, h+4, c.byref(t.api)) == 1
            assert t.get(h+4, 4) == p and not t.missing
            assert t.events[-3:] == [('write', 4, h+4, p), ('read', 4, h+4), ('write', 4, h+4, p)]

        # Count changes by a record processor must affect the next loop test.
        synthetic = 0
        for fn in loaders[3:]:
            for count, changed in ((0, None), (3, 1), (1, 3), (65535, None)):
                t = Target()
                t.load(p, struct.pack('>HHI', count, 2, 16))
                t.load(h, struct.pack('>HHI', 0, 0x8001, 77))
                seen = []

                def process(item):
                    seen.append(item)
                    if len(seen) == 1 and changed is not None:
                        t.put(p, changed, 2)

                callback = PROCESS(process)
                assert fn(p, h, o, s, c.byref(t.api), callback) == 1
                final_count = count if changed is None else changed
                assert seen == [p+8+16*i for i in range(final_count)]
                assert t.get(h+2, 2) == 0x8000
                assert t.get(o, 4) == p and t.get(s, 4) == 77 and not t.missing
                synthetic += 1

        advance = lib.tak_dbu_advance_801B90D0
        advance.argtypes = [c.c_uint32, c.POINTER(Memory)]
        advance.restype = None
        advance_cases = 0
        for cursor in (0, 1, 0x80000000, 0xffffffff):
            for remaining in (0, 1, 0x80000000, 0xffffffff):
                for amount in (0, 1, 0x80000000, 0xffffffff):
                    t = Target()
                    t.put(0x80322e18, cursor, 4)
                    t.put(0x80322e1c, remaining, 4)
                    advance(amount, c.byref(t.api))
                    assert t.events == [('read', 4, 0x80322e18), ('read', 4, 0x80322e1c),
                                        ('write', 4, 0x80322e18, (cursor+amount) & 0xffffffff),
                                        ('write', 4, 0x80322e1c, (remaining-amount) & 0xffffffff)]
                    assert not t.missing
                    advance_cases += 1
        print(f'PASS: {real_runs} real archive loader runs, {records} processed records; '
              f'3 alias cases, {synthetic} loop cases, {advance_cases} cursor cases')


if __name__ == '__main__':
    main()
