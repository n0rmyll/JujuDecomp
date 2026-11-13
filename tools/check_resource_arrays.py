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
    loaded = ctypes.CDLL(str(lib))
    fn = loaded.tak_resource_array_item
    fn.argtypes = [ctypes.c_uint32, ctypes.c_uint32, read16, read32]
    fn.restype = ctypes.c_uint32
    write16 = ctypes.CFUNCTYPE(None, ctypes.c_uint32, ctypes.c_uint16)
    write32 = ctypes.CFUNCTYPE(None, ctypes.c_uint32, ctypes.c_uint32)
    relocate = loaded.tak_resource_array_relocate
    relocate.argtypes = [ctypes.c_uint32, read16, read32, write16, write32]
    relocate.restype = None
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
            r16 = read16(lambda address: struct.unpack_from('>H', memory, address-base)[0])
            r32 = read32(lambda address: struct.unpack_from('>I', memory, address-base)[0])
            w16 = write16(lambda address, value: struct.pack_into('>H', memory, address-base, value))
            w32 = write32(lambda address, value: struct.pack_into('>I', memory, address-base, value))
            expected = bytearray(raw)
            if directory['flags'] & 1:
                for i, offset in enumerate(directory['record_offsets']):
                    struct.pack_into('>I', expected, 4+4*i, (base+offset) & 0xffffffff)
                struct.pack_into('>H', expected, 2, directory['flags'] | 4)
            relocate(base, r16, r32, w16, w32)
            if memory != expected:
                raise SystemExit('Relocation changed unexpected archive bytes')
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
    # All flag combinations, zero/nonzero counts, wrapping additions, and
    # repeated invocation: bit 2 must not suppress a second relocation.
    for flags in range(16):
        for count in (0, 3):
            memory = bytearray(struct.pack('>HHIII', count, flags, 0, 0x7fffffff, 0xffffffff))
            r16 = read16(lambda address: struct.unpack_from('>H', memory, address-base)[0])
            r32 = read32(lambda address: struct.unpack_from('>I', memory, address-base)[0])
            w16 = write16(lambda address, value: struct.pack_into('>H', memory, address-base, value))
            w32 = write32(lambda address, value: struct.pack_into('>I', memory, address-base, value))
            for invocation in (1, 2):
                expected = bytearray(memory)
                if flags & 1:
                    struct.pack_into('>H', expected, 2, flags | 4)
                    for i in range(count):
                        value = struct.unpack_from('>I', expected, 4+4*i)[0]
                        struct.pack_into('>I', expected, 4+4*i, (value+base) & 0xffffffff)
                relocate(base, r16, r32, w16, w32)
                if memory != expected:
                    raise SystemExit(f'Relocation edge mismatch: flags={flags}, count={count}, call={invocation}')
    print(f'PASS: native C matched {checked} real offsets including relocation and index masking; {rejected} invalid directories rejected; 64 relocation edge cases')
