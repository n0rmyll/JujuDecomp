#!/usr/bin/env python3
"""Check recovered C against real archive flags and reject corrupt boundaries."""
import ctypes
import subprocess
import tempfile
import struct
from pathlib import Path
from inspect_dbu import inspect

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='tak-dbu-') as tmp:
    library = Path(tmp) / 'dbu.dylib'
    subprocess.run(['clang', '-std=c99', '-Wall', '-Wextra', '-Werror', '-dynamiclib',
                    str(root/'src/recovered/dbu_chunk.c'), '-o', str(library)], check=True)
    function = ctypes.CDLL(str(library)).tak_dbu_chunk_header_size
    function.argtypes = [ctypes.c_uint16]
    function.restype = ctypes.c_uint32
    for flags, expected in ((0, 10), (2, 42), (8, 32), (10, 64), (0xffff, 64)):
        if function(flags) != expected:
            raise SystemExit('Recovered C flag branch mismatch')
    total = 0
    for name in ('Preload', 'Hub'):
        data = (root/f'analysis/{name}.dbu').read_bytes()
        report = inspect(data)
        for chunk in report['chunks']:
            if function(int(chunk['flags'], 16)) != chunk['header_size']:
                raise SystemExit('C and parser header sizes disagree')
        total += report['chunk_count']
        # Structurally equivalent big-endian header fixture; payloads unchanged.
        # This checks byte-order handling only, not big-endian asset decoding.
        swapped = bytearray(data)
        start = report['binary_header_offset']
        for offset in range(start+16, start+32, 4):
            swapped[offset:offset+4] = swapped[offset:offset+4][::-1]
        for chunk in report['chunks']:
            offset = chunk['header_offset']
            fields = struct.unpack_from('<HHIH', data, offset)
            struct.pack_into('>HHIH', swapped, offset, *fields)
        swapped_report = inspect(swapped)
        if swapped_report['endian'] != 'big' or swapped_report['chunks'] != report['chunks']:
            raise SystemExit('Endian fixture changed chunk interpretation')
        bad_size = bytearray(data)
        pos = report['chunks'][0]['header_offset']+4
        bad_size[pos:pos+4] = b'\xff'*4
        for corrupt in (data[:10], data[:-1], bad_size, data+b'\0'):
            try:
                inspect(corrupt)
            except ValueError:
                pass
            else:
                raise SystemExit('Corrupt/truncated archive unexpectedly accepted')
    print(f'PASS: native C sizing across {total} real chunks; all sizing branches; 2 endian fixtures; 8 corrupt cases rejected')
