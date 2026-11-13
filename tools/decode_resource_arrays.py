#!/usr/bin/env python3
"""Decode generic array directories for selected verified handlers.

Chunk headers and payload directories can have different byte orders.
The selected GameCube payloads are big-endian. Object fields are not decoded.
"""
import json
import struct
from pathlib import Path
from inspect_dbu import inspect

root = Path(__file__).resolve().parents[1]
selected = {0x65, 0x6a, 0x601}

def decode(payload):
    if len(payload) < 4:
        raise ValueError('Truncated array header')
    count, flags = struct.unpack_from('>HH', payload)
    mode = flags & 3
    if mode == 1:
        if 4+4*count > len(payload):
            raise ValueError('Truncated offset directory')
        offsets = list(struct.unpack_from(f'>{count}I', payload, 4))
        if any(x < 4+4*count or x >= len(payload) for x in offsets):
            raise ValueError('Invalid record offset')
        if offsets != sorted(set(offsets)):
            raise ValueError('Non-increasing offsets in supported samples')
        return dict(count=count, flags=flags, mode='relative offsets before runtime relocation',
                    record_offsets=offsets,
                    caveat='Offsets are validated. Last record size and inter-record padding remain unknown.')
    if mode == 2:
        header = 16 if flags & 8 else 8
        if len(payload) < header:
            raise ValueError('Truncated stride directory')
        stride = struct.unpack_from('>I', payload, 4)[0]
        if not stride or header+count*stride > len(payload):
            raise ValueError('Invalid stride/count')
        return dict(count=count, flags=flags, mode='fixed stride', stride=stride,
                    record_offsets=[header+i*stride for i in range(count)],
                    trailing_bytes=len(payload)-header-count*stride)
    raise ValueError('Unsupported array mode')

def main():
    rows = []
    for name in ('Preload', 'Hub'):
        data = (root/f'analysis/{name}.dbu').read_bytes()
        for chunk in inspect(data)['chunks']:
            if int(chunk['type'], 16) not in selected:
                continue
            start, length = chunk['payload_offset'], chunk['payload_size']
            directory = decode(data[start:start+length])
            rows.append(dict(archive=name, chunk_index=chunk['index'], type=chunk['type'],
                             payload_offset=start, path_hint=chunk.get('preceding_path_marker'),
                             directory=directory))
    (root/'analysis/resource-arrays.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(f'Decoded {len(rows)} real array directories with {sum(x["directory"]["count"] for x in rows)} record offsets.')

if __name__ == '__main__':
    main()
