#!/usr/bin/env python3
"""Check GLB framing, array bounds, triangle indices and manifest counts."""
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]/'assets/models'


def main():
    report = json.loads((ROOT/'manifest.json').read_text())
    triangles = textured = 0
    seen = set()
    for entry in report['entries']:
        if entry['glb'] in seen:
            raise ValueError('Duplicate output path')
        seen.add(entry['glb'])
        data = (ROOT/entry['glb']).read_bytes()
        if struct.unpack_from('<3I', data) != (0x46546c67, 2, len(data)):
            raise ValueError('Invalid GLB header')
        length, tag = struct.unpack_from('<I4s', data, 12)
        if tag != b'JSON' or length%4:
            raise ValueError('Invalid JSON chunk')
        document = json.loads(data[20:20+length])
        size, tag = struct.unpack_from('<I4s', data, 20+length)
        binary = data[28+length:]
        if tag != b'BIN\0' or size != len(binary):
            raise ValueError('Invalid BIN chunk')
        for view in document['bufferViews']:
            if view['byteOffset']%4 or view['byteOffset']+view['byteLength'] > len(binary):
                raise ValueError('Invalid buffer view')
        for accessor in document['accessors']:
            view = document['bufferViews'][accessor['bufferView']]
            components = dict(SCALAR=1, VEC2=2, VEC3=3)[accessor['type']]
            if accessor['count']*components*4 != view['byteLength']:
                raise ValueError('Invalid accessor range')
        count_triangles = 0
        for primitive in document['meshes'][0]['primitives']:
            count = document['accessors'][primitive['attributes']['POSITION']]['count']
            if count != entry['vertices']:
                raise ValueError('Vertex manifest mismatch')
            a = document['accessors'][primitive['indices']]
            view = document['bufferViews'][a['bufferView']]
            indices = struct.unpack_from('<'+'I'*a['count'], binary, view['byteOffset'])
            if not indices or max(indices) >= count or len(indices)%3:
                raise ValueError('Invalid triangle indices')
            count_triangles += len(indices)//3
        if count_triangles != entry['triangles']:
            raise ValueError('Triangle manifest mismatch')
        triangles += count_triangles
        textured += bool(document.get('images'))
    print(f'PASS: {len(seen)} GLBs; {triangles} triangles; {textured} textured meshes; framing, ranges and indices verified.')


if __name__ == '__main__':
    main()
