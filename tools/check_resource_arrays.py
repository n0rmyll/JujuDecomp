#!/usr/bin/env python3
"""Compare native recovered array accessor with real archive directories."""
import ctypes
import struct
import subprocess
import tempfile
from pathlib import Path
from inspect_dbu import inspect
from decode_resource_arrays import decode, selected

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='tak-array-') as tmp:
    lib = Path(tmp)/'array.dylib'
    subprocess.run(['clang', '-std=c99', '-Wall', '-Wextra', '-Werror', '-dynamiclib',
                    str(root/'src/recovered/resource_array.c'), '-o', str(lib)], check=True)
    read16 = ctypes.CFUNCTYPE(ctypes.c_uint16, ctypes.c_uint32)
    read32 = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32)
    fn = ctypes.CDLL(str(lib)).tak_resource_array_item
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32, read16, read32]
    fn.restype = ctypes.c_uint32
    base, checked, rejected = 0x81000000, 0, 0
    for name in ('Preload', 'Hub'):
        data = (root/f'analysis/{name}.dbu').read_bytes()
        for chunk in inspect(data)['chunks']:
            if int(chunk['type'], 16) not in selected:
                continue
            start = chunk['payload_offset']
            raw = data[start:start+chunk['payload_size']]
            directory = decode(raw)
            memory = bytearray(raw)
            if directory['flags'] & 3 == 1:
                # fn_801B91FC adds the table base to each relative entry.
                for i, offset in enumerate(directory['record_offsets']):
                    struct.pack_into('>I', memory, 4+4*i, base+offset)
                struct.pack_into('>H', memory, 2, directory['flags'] | 4)
            r16 = read16(lambda address: struct.unpack_from('>H', memory, address-base)[0])
            r32 = read32(lambda address: struct.unpack_from('>I', memory, address-base)[0])
            if fn(0, 0, r16, r32) != 0:
                raise SystemExit('Null base must return zero')
            for i, offset in enumerate(directory['record_offsets']):
                if fn(base, i, r16, r32) != base+offset:
                    raise SystemExit(f'Accessor mismatch in {name} chunk {chunk["index"]}')
                if fn(base, i+0x1000000, r16, r32) != base+offset:
                    raise SystemExit('Original 24-bit index mask not preserved')
                checked += 1
            bad = bytearray(raw)
            struct.pack_into('>I', bad, 4, 0xffffffff)
            for corrupt in (raw[:3], bad):
                try:
                    decode(corrupt)
                except ValueError:
                    rejected += 1
                else:
                    raise SystemExit('Invalid directory accepted')
    print(f'PASS: native C matched {checked} real offsets including index masking; {rejected} invalid directories rejected')
