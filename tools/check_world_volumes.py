#!/usr/bin/env python3
"""Validate native record reader against independent decoding of real archives."""
import ctypes
import struct
import subprocess
import tempfile
from pathlib import Path
from decode_world_volumes import records, decode_record

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='tak-volume-') as tmp:
    lib = Path(tmp)/'volume.dylib'
    subprocess.run(['clang', '-std=c99', '-Wall', '-Wextra', '-Werror', '-dynamiclib',
                    str(root/'src/recovered/world_volume.c'), '-o', str(lib)], check=True)
    fn = ctypes.CDLL(str(lib)).tak_world_volume_decode
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t,
                   ctypes.POINTER(ctypes.c_uint32)]
    fn.restype = ctypes.c_int
    total = 0
    for name in ('Hub', 'Burial'):
        rows = records((root/f'analysis/{name}.dbu').read_bytes())
        if not rows:
            raise SystemExit('No records in real sample')
        for row in rows:
            raw = bytes.fromhex(row['record']['raw_hex'])
            buffer = (ctypes.c_uint8*192).from_buffer_copy(raw)
            output = (ctypes.c_uint32*48)()
            if fn(buffer, 192, output) != 1 or list(output) != list(struct.unpack('>48I', raw)):
                raise SystemExit('Native record word mismatch')
            if struct.pack('>48I', *output) != raw:
                raise SystemExit('Record did not round-trip')
            for length in (0, 4, 191):
                if fn(buffer, length, output) != 0:
                    raise SystemExit('Native reader accepted short record')
            invalid = bytearray(raw)
            invalid[0x40:0x60] = b'X'*32
            try:
                decode_record(invalid)
            except ValueError:
                pass
            else:
                raise SystemExit('Unterminated string accepted')
            total += 1
    print(f'PASS: {total} real records/48 words each matched native C and round-tripped; short records and invalid strings rejected')
