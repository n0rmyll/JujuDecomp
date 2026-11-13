#!/usr/bin/env python3
"""Read DBU chunk boundaries recovered from GJUE78, without decoding assets."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

def header_size(flags):
    return (64 if flags & 2 else 32) if flags & 8 else (42 if flags & 2 else 10)

def inspect(data):
    prefix = re.fullmatch(rb'[0-9]+ *\n', data[:8])
    start = int(data[:8].strip()) if prefix else 0
    if start < 0 or start+32 > len(data):
        raise ValueError('Truncated file header')
    header = data[start:start+32]
    if header[8:10] != b'DB':
        raise ValueError('Unsupported DB signature')
    if struct.unpack_from('>I', header, 16)[0] == 0x100:
        endian = '>'
    elif struct.unpack_from('<I', header, 16)[0] == 0x100:
        endian = '<'
    else:
        raise ValueError('Unsupported version')
    version, flags, count, unknown = struct.unpack_from(endian+'4I', header, 16)
    if count > (len(data)-start-32)//10:
        raise ValueError('Impossible chunk count')
    cursor, chunks, path_hint = start+32, [], None
    for index in range(count):
        if cursor+10 > len(data):
            raise ValueError(f'Truncated chunk header at {cursor:#x}')
        kind, chunk_flags, size, field08 = struct.unpack_from(endian+'HHIH', data, cursor)
        length = header_size(chunk_flags)
        payload = cursor+length
        end = payload+size
        if end > len(data):
            raise ValueError(f'Chunk {index} exceeds file bounds')
        record = dict(index=index, header_offset=cursor, header_size=length,
                      type=f'0x{kind:04X}', flags=f'0x{chunk_flags:04X}',
                      unknown_08=field08, payload_offset=payload, payload_size=size)
        if kind == 0x998:
            raw = data[payload:end].split(b'\0', 1)[0]
            if raw and all(32 <= b < 127 for b in raw):
                path_hint = raw.decode('ascii')
                record['observed_path_marker'] = path_hint
        if path_hint:
            record['preceding_path_marker'] = path_hint
        chunks.append(record)
        cursor = end
    if cursor != len(data):
        raise ValueError(f'{len(data)-cursor} bytes remain after declared chunks')
    return dict(sha256=hashlib.sha256(data).hexdigest(), binary_header_offset=start,
                endian='little' if endian == '<' else 'big', version=version,
                file_flags=flags, unknown_header_1c=f'0x{unknown:08X}',
                chunk_count=count, end_offset=cursor,
                caveat='Chunk boundaries only; type semantics, flags beyond header sizing, and payload codecs remain unresolved. Path markers are observations, not standalone original-file reconstruction.',
                chunks=chunks)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = inspect(args.archive.read_bytes())
    except (ValueError, struct.error) as error:
        parser.exit(1, f'{args.archive.name}: {error}\n')
    report['archive'] = args.archive.name
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(f'{args.archive.name}: {report["chunk_count"]} chunks, {report["endian"]}-endian, exact EOF at {report["end_offset"]:#x}')

if __name__ == '__main__':
    main()
