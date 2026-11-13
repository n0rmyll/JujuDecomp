#!/usr/bin/env python3
"""Export observed 192-byte type-0x0601 records with conservative field names."""
import argparse
import json
import math
import struct
from pathlib import Path
from inspect_dbu import inspect
from decode_resource_arrays import decode

def decode_record(raw):
    if len(raw) != 192:
        raise ValueError('Expected exactly 192 bytes')
    def floats(offset, count):
        values = list(struct.unpack_from(f'>{count}f', raw, offset))
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nonfinite float in supported record fields')
        return values
    def text(offset):
        field = raw[offset:offset+32]
        if b'\0' not in field:
            raise ValueError('Unterminated 32-byte string')
        return field.split(b'\0', 1)[0].decode('ascii')
    return dict(flags_00=struct.unpack_from('>I', raw)[0],
                vector_04=floats(4, 3), vector_10=floats(0x10, 3),
                matrix_candidate_1c=floats(0x1c, 9),
                preset_40=text(0x40), scalar_60=floats(0x60, 1)[0],
                name_64=text(0x64), scalar_84=floats(0x84, 1)[0],
                words_88_8c=[f'0x{w:08X}' for w in struct.unpack_from('>2I', raw, 0x88)],
                scalars_90_98=floats(0x90, 3),
                unknown_9c_bf=raw[0x9c:].hex(), raw_hex=raw.hex())

def records(data):
    result = []
    for chunk in inspect(data)['chunks']:
        if chunk['type'] != '0x0601':
            continue
        p = chunk['payload_offset']
        payload = data[p:p+chunk['payload_size']]
        directory = decode(payload)
        if directory.get('stride') != 192:
            raise ValueError('Unsupported world-volume stride')
        for index, offset in enumerate(directory['record_offsets']):
            result.append(dict(chunk_index=chunk['index'], index=index,
                               file_offset=p+offset,
                               path_hint=chunk.get('preceding_path_marker'),
                               record=decode_record(payload[offset:offset+192])))
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = records(args.archive.read_bytes())
    args.output.write_text(json.dumps(dict(archive=args.archive.name,
        caveat='Spatial audio-volume interpretation is inferred from consumers; field names by offset remain authoritative. Raw bytes preserve unknown fields.',
        records=rows), indent=2)+'\n')
    print(f'{args.archive.name}: decoded {len(rows)} records; preserved 192 bytes per record.')
