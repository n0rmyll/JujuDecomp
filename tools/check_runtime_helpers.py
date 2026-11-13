#!/usr/bin/env python3
"""Original-byte and host behavior checks for fifteen runtime routines."""
import ctypes as c
import csv
from pathlib import Path
import struct
import subprocess
import tempfile

from check_resource_loaders import Target, R16, R32, W16, W32
from inspect_dbu import inspect
from decode_resource_arrays import decode, selected

ROOT = Path(__file__).resolve().parents[1]
ADDRESSES = ('801B90F4', '801B9190', '801B9244', '801C5A64', '8021311C',
             '80213480', '80213710', '80213744', '800E53C4', '800E53CC',
             '80211ED4', '80211F54', '8020F964', '80213708', '80280928')
R8 = c.CFUNCTYPE(c.c_uint8, c.c_uint32)
W8 = c.CFUNCTYPE(None, c.c_uint32, c.c_uint8)
CALL = c.CFUNCTYPE(c.c_uint32, *([c.c_uint32]*4))
COPY = c.CFUNCTYPE(None, *([c.c_uint32]*3))


class API(c.Structure):
    _fields_ = [('r8', R8), ('r16', R16), ('r32', R32), ('w8', W8),
                ('w16', W16), ('w32', W32), ('call', CALL), ('copy', COPY)]


class Runtime(Target):
    def __init__(self):
        super().__init__()
        self.handler = lambda target, a, b, d: 0
        self.errors = []
        self.callbacks2 = (R8(lambda a: self.read(a, 1)), self.callbacks[0], self.callbacks[1],
                           W8(lambda a, v: self.write(a, v, 1)), self.callbacks[2], self.callbacks[3],
                           CALL(self.call), COPY(self.copy))
        self.runtime = API(*self.callbacks2)

    def call(self, target, a, b, d):
        self.events.append(('call', target, a, b, d))
        try:
            return self.handler(target, a, b, d)
        except Exception as error:
            self.errors.append(error)
            return 0

    def copy(self, dst, src, length):
        self.events.append(('copy', dst, src, length))
        try:
            self.load(dst, bytes(self.data[src+i] for i in range(length)))
        except Exception as error:
            self.errors.append(error)

    def clean(self):
        assert not self.missing and not self.errors, (self.missing, self.errors)


def main():
    for address in ADDRESSES:
        subprocess.run(['python3', str(ROOT/'tools/function_report.py'), f'fn_{address}'], check=True)
    with tempfile.TemporaryDirectory(prefix='tak-runtime-') as tmp:
        output = Path(tmp)/'runtime.dylib'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-dynamiclib',
                        str(ROOT/'src/recovered/runtime_helpers.c'),
                        str(ROOT/'src/recovered/resource_array.c'), '-o', str(output)], check=True)
        lib = c.CDLL(str(output))

        def run(address, t, *args):
            fn = getattr(lib, f'tak_fn_{address}')
            fn.argtypes = [c.c_uint32]*len(args) + [c.POINTER(API)]
            fn.restype = None if address in ('801B9244', '800E53CC', '80211ED4', '80211F54') else c.c_uint32
            result = fn(*args, c.byref(t.runtime))
            t.clean()
            return result

        # Cleanup: low-byte decisions, reset priority, null pointers, flag 8,
        # wrapping size difference, and exact external calls/store order.
        cleanup_cases = 0
        for mode in (0, 1, 2, 0x101, 0x100):
            for reset in (0, 1, 0x100, 0x101):
                for flags in (0, 8, 0xffffffff):
                    for pointer in (0, 0xfffffff0):
                        t = Runtime()
                        for offset, value in ((0, flags), (0x14, pointer), (0x18, 5)):
                            t.put(0x80322e00+offset, value, 4)
                        assert run('801B90F4', t, mode, reset) == 1
                        if reset & 255:
                            expected = [('write', 4, 0x80322e14, 0)]
                        elif mode & 255 == 1:
                            expected = [('read', 4, 0x80322e14)]
                            if pointer:
                                expected += [('call', 0x802061b8, pointer, 0, 0)]
                            expected += [('write', 4, 0x80322e14, 0)]
                        else:
                            expected = [('read', 4, 0x80322e00)]
                            if not flags & 8:
                                expected += [('read', 4, 0x80322e14), ('read', 4, 0x80322e18),
                                             ('call', 0x80205f64, pointer, (5-pointer) & 0xffffffff, 0)]
                        assert t.events == expected
                        cleanup_cases += 1

        # Both loader variants, bit preservation, aliasing and relocation.
        for address in ('801B9190', '801C5A64'):
            for alias in (False, True):
                t = Runtime()
                p, h, o, s = 0x81000000, 0x82000000, 0x82000010, 0x82000014
                if alias:
                    o = h+4
                t.load(p, struct.pack('>HHII', 2, 1, 12, 20))
                t.load(h, struct.pack('>HHI', 0, 0xffff, 123))
                assert run(address, t, p, h, o, s) == 1
                assert t.get(h+2, 2) == 0xfffe
                assert t.get(o, 4) == p and t.get(s, 4) == (p if alias else 123)
                assert t.get(p+4, 4) == (p+12 if address == '801B9190' else 12)
                assert t.events[-3:] == [('write', 4, o, p), ('read', 4, h+4),
                                         ('write', 4, s, p if alias else 123)]

        # The endian-changing helper is tested with little-endian versions of
        # real big-endian directories. Record bodies must remain unchanged.
        endian_cases = 0
        for name in ('Preload', 'Hub'):
            archive = (ROOT/f'analysis/{name}.dbu').read_bytes()
            for chunk in inspect(archive)['chunks']:
                if int(chunk['type'], 16) not in selected:
                    continue
                raw = archive[chunk['payload_offset']:chunk['payload_offset']+chunk['payload_size']]
                directory = decode(raw)
                little = bytearray(raw)
                count, flags = struct.unpack_from('>HH', raw)
                struct.pack_into('<HH', little, 0, count, flags)
                expected = bytearray(raw)
                p = 0x81000000
                if flags & 1:
                    struct.pack_into('>H', expected, 2, flags | 4)
                    for i, offset in enumerate(directory['record_offsets']):
                        struct.pack_into('<I', little, 4+4*i, offset)
                        struct.pack_into('>I', expected, 4+4*i, p+offset)
                t = Runtime()
                t.load(p, little)
                run('801B9244', t, p)
                assert bytes(t.data[p+i] for i in range(len(raw))) == expected
                endian_cases += 1
        # Zero-count relocation still sets bit 2, all other flag bits survive.
        for flags in (0, 1, 2, 3, 4, 5, 0xffff):
            t = Runtime()
            t.load(0x1000, struct.pack('<HH', 0, flags))
            run('801B9244', t, 0x1000)
            assert t.get(0x1000, 2) == 0
            assert t.get(0x1002, 2) == (flags | 4 if flags & 1 else flags)

        # Return normalization: low-byte booleans differ from whole-word test.
        wrapper_cases = 0
        for value in (*range(256), 0x100, 0xffffff00, 0xffffffff):
            for address, target, offset in (('80213710', 0x80211dd8, 0x478),
                                             ('80213744', 0x80282250, 0x4d8)):
                t = Runtime()
                t.handler = lambda *args: value
                assert run(address, t, 0xffffff00) == bool(value & 255)
                assert t.events == [('call', target, (0xffffff00+offset) & 0xffffffff, 0, 0)]
                wrapper_cases += 1
            t = Runtime()
            t.handler = lambda *args: value
            assert run('80280928', t, 0x1234, 0x5678) == bool(value)
            assert t.events == [('call', 0x80280bb4, 0x1234, 0x5678, 0)]
            t = Runtime()
            t.handler = lambda *args: value
            assert run('8021311C', t, 0x1234, 0x5678) == 1
            assert t.events == [('call', 0x802131a0, 0x1234, 0x5678, 0)]
            wrapper_cases += 2
        for first in (0, 1, 0x100, 0x101):
            for second in (0, 1, 0x100):
                t = Runtime()
                t.handler = lambda target, *args: first if target == 0x80211dd8 else second
                assert run('80213480', t, 0x1000) == bool(first & 255)
                expected = [('call', 0x80211dd8, 0x1478, 0, 0)]
                if first & 255:
                    expected += [('call', 0x80282250, 0x14d8, 0, 0)]
                assert t.events == expected

        for value in (*range(256), 0x100, 0xffffffff):
            t = Runtime()
            t.load(0x803312fb, b'ABC')
            run('800E53CC', t, value)
            assert run('800E53C4', t) == value & 255
            assert t.get(0x803312fb, 1) == 65 and t.get(0x803312fd, 1) == 67
            assert t.events == [('write', 1, 0x803312fc, value & 255), ('read', 1, 0x803312fc)]
        constant = lib.tak_fn_80213708
        constant.argtypes, constant.restype = [], c.c_uint32
        assert constant() == 1

        # Base constructor: allocation failure and constructor return forwarding.
        for allocation, constructed in ((0, 0), (0x2000, 0), (0x2000, 0x3000)):
            t = Runtime()
            t.load(0x1000, bytes([0xa5])*16)
            t.handler = lambda target, *args: allocation if target == 0x802062a8 else constructed
            assert run('8020F964', t, 0x1000) == 0x1000
            expected = [('write', 4, 0x1000, 0x802ef19c), ('write', 1, 0x1004, 0),
                        ('call', 0x802062a8, 0x6c, 0, 0)]
            if allocation:
                expected += [('call', 0x8017fd08, allocation, 0, 0)]
            expected += [('write', 4, 0x80332ca0, constructed), ('write', 1, 0x100c, 0)]
            assert t.events == expected
            assert all(t.data[0x1000+i] == 0xa5 for i in (5, 6, 7, 8, 9, 10, 11, 13, 14, 15))

        # All 16 device occupancy masks for both paired methods, including
        # callbacks which mutate a later slot and the pending-work field.
        device_cases = 0
        for address in ('80211ED4', '80211F54'):
            for mask in range(16):
                for mutate in (False, True):
                    t = Runtime()
                    obj, app = 0x1000, 0x8000
                    t.load(obj, bytes([0xa5])*0x60)
                    t.put(0x803320e0, app, 4)
                    source = bytes(range(48))
                    t.load(app+0x334, source)
                    t.put(obj+0x58, mask & 1, 1)
                    t.put(obj+0x5c, 0x7777 if mask & 2 else 0, 4)
                    expected_calls = []
                    for i in range(4):
                        device, table = 0x2000+0x100*i, 0x3000+0x100*i
                        t.put(obj+8+4*i, device if mask & (1 << i) else 0, 4)
                        t.put(device, table, 4)
                        t.put(table+0x28, 0x4000+i, 4)
                        t.put(table+0x2c, 0x5000+i, 4)
                    if address == '80211F54':
                        if mask & 1:
                            expected_calls.append(('call', 0x8011dcac, obj+0x48, 0, 0))
                        pending = 0x8888 if mutate and mask & 1 else (0x7777 if mask & 2 else 0)
                        if pending:
                            expected_calls.append(('call', 0x8011d5e8, pending, 0, 0))
                    occupied = [i for i in range(4) if mask & (1 << i)]
                    if mutate and 0 in occupied:
                        occupied = [i for i in occupied if i != 3]
                    for i in occupied:
                        expected_calls.append(('call', (0x4000 if address == '80211ED4' else 0x5000)+i,
                                               0x2000+0x100*i, 0, 0))

                    def handler(target, a, b, d):
                        if mutate and target == 0x8011dcac:
                            t.put(obj+0x5c, 0x8888, 4)
                        if mutate and target in (0x4000, 0x5000):
                            t.put(obj+20, 0, 4)
                        return 0

                    t.handler = handler
                    run(address, t, obj)
                    assert [event for event in t.events if event[0] == 'call'] == expected_calls
                    if address == '80211ED4':
                        assert t.events[:3] == [('read', 4, 0x803320e0),
                                                ('copy', obj+0x18, app+0x334, 48),
                                                ('write', 4, obj+0x5c, 0)]
                        assert bytes(t.data[obj+0x18+i] for i in range(48)) == source
                        assert t.get(obj+0x5c, 4) == 0
                    device_cases += 1

        rows = list(csv.DictReader((ROOT/'analysis/functions.csv').open()))
        total = sum(int(row['size']) for row in rows if row['name'] in {'fn_'+a for a in ADDRESSES})
        print(f'PASS: 15 routines, {total} original bytes; {cleanup_cases} cleanup cases, '
              f'{endian_cases} real endian-directory cases, {wrapper_cases} wrapper cases, '
              f'{device_cases} device cases; loader aliases, byte access and constructor branches')


if __name__ == '__main__':
    main()
