#!/usr/bin/env python3
"""Export verified subtype-19 GX meshes from GJUE78 DBU files as static GLBs."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from decode_textures import archive_report
from decode_resource_arrays import decode as array_directory

ROOT = Path(__file__).resolve().parents[1]


def unpack(data, fmt, offset):
    size = struct.calcsize('>'+fmt)
    if offset < 0 or offset+size > len(data):
        raise ValueError(f'Out-of-bounds read at {offset:#x} ({size} bytes)')
    return struct.unpack_from('>'+fmt, data, offset)


def word(data, offset):
    return unpack(data, 'I', offset)[0]


def triangles(primitive, count):
    if primitive == 0x90:
        if count % 3:
            raise ValueError('Triangle count is not divisible by three')
        return [(i, i+1, i+2) for i in range(0, count, 3)]
    if primitive == 0x98:
        return [(i, i+1, i+2) if i%2 == 0 else (i+1, i, i+2) for i in range(count-2)]
    if primitive == 0xa0:
        return [(0, i, i+1) for i in range(1, count-1)]
    if primitive in (0x80, 0x88):
        if count % 4:
            raise ValueError('Quad count is not divisible by four')
        return [t for i in range(0, count, 4) for t in ((i, i+1, i+2), (i, i+2, i+3))]
    raise ValueError(f'Unsupported primitive {primitive:#x}')


def decode_mesh(data, capture_skin=False):
    if len(data) < 0x94 or data[0] != 19:
        raise ValueError('Unsupported model subtype (only 19 is decoded)')
    arrays = {0: (word(data, 0x50), word(data, 0x54), 12),
              1: (word(data, 0x84), word(data, 0x88), 3)}
    uv = (word(data, 0x8c), word(data, 0x90), 8)
    arrays.update({i: uv for i in range(4, 12)})
    for count, offset, stride in arrays.values():
        if count and (offset < 0x94 or offset+count*stride > len(data)):
            raise ValueError('Invalid vertex array range')
    vertices, primitives, lookup = [], [], {}
    registers = {}
    palette = {}
    node = word(data, 0x78)
    seen = set()
    if not node:
        raise ValueError('No display list')
    while node:
        if node in seen:
            raise ValueError('Cyclic display-list chain')
        seen.add(node)
        unpack(data, '8I', node)
        next_offset, material = unpack(data, '2I', node)
        size = word(data, node+0x14)
        cursor, end = node+32, node+32+size
        if end > len(data):
            raise ValueError('Display list exceeds model bounds')
        indices = []
        while cursor < end:
            command = data[cursor]
            cursor += 1
            if command in (0, 0x48):
                continue
            if command == 8:
                address, value = unpack(data, 'BI', cursor)
                registers[address] = value
                cursor += 5
                continue
            if command == 0x10:
                amount, _ = unpack(data, 'HH', cursor)
                cursor += 4+(amount+1)*4
                continue
            if command in (0x20, 0x28, 0x30, 0x38, 0x61):
                # Matrix index loads / BP state don't change the source attribute indices.
                value = unpack(data, 'I', cursor)[0]
                if command == 0x20:
                    address = value & 0xfff
                    if address%12:
                        raise ValueError('Unaligned position matrix palette load')
                    palette[address//12] = value >> 16
                cursor += 4
                continue
            if command & 0x80:
                count = unpack(data, 'H', cursor)[0]
                cursor += 2
                if 0x50 not in registers or 0x60 not in registers:
                    raise ValueError('Missing vertex descriptor registers')
                low, high = registers[0x50], registers[0x60]
                modes = [(low >> shift) & 3 for shift in (9, 11, 13, 15)]
                modes += [(high >> (2*i)) & 3 for i in range(8)]
                if modes[0] not in (2, 3):
                    raise ValueError('Position attribute is not indexed')
                corners = []
                for _ in range(count):
                    matrix = []
                    for bit in range(9):
                        if low & (1 << bit):
                            matrix.append(unpack(data, 'B', cursor)[0])
                            cursor += 1
                    attrs = {}
                    for attr, mode in enumerate(modes):
                        if not mode:
                            continue
                        if mode not in (2, 3):
                            raise ValueError('Direct attributes are not yet supported')
                        index = unpack(data, 'B' if mode == 2 else 'H', cursor)[0]
                        cursor += 1 if mode == 2 else 2
                        if attr in (2, 3):
                            # Renderer supplies colors from a separate runtime array.
                            # Consume their indices, but export without baked lighting.
                            continue
                        if attr not in arrays or index >= arrays[attr][0]:
                            raise ValueError(f'Attribute {attr} index {index} outside source array')
                        attrs[attr] = index
                    if any(matrix) and not capture_skin:
                        raise ValueError('Nonzero matrix index requires skeletal transforms')
                    joint = None
                    if capture_skin:
                        matrix_index = matrix[0] if low & 1 else registers.get(0x30, 0) & 63
                        if matrix_index%3 or matrix_index//3 not in palette:
                            raise ValueError('Unresolved position matrix palette slot')
                        joint = palette[matrix_index//3]
                        if any(matrix[1:]):
                            raise ValueError('Texture matrix indices are not yet supported')
                    key = (tuple(sorted(attrs.items())), joint)
                    if key not in lookup:
                        position = unpack(data, '3f', arrays[0][1]+attrs[0]*12)
                        normal = unpack(data, '3b', arrays[1][1]+attrs[1]*3) if 1 in attrs else None
                        if normal:
                            length = math.sqrt(sum(v*v for v in normal))
                            normal = tuple(v/length for v in normal) if length else None
                        coords = unpack(data, '2f', uv[1]+attrs[4]*8) if 4 in attrs else None
                        if not all(math.isfinite(v) for v in position+(coords or ())):
                            raise ValueError('Non-finite vertex data')
                        lookup[key] = len(vertices)
                        vertices.append(dict(position=position, normal=normal, uv=coords, joint=joint))
                    corners.append(lookup[key])
                for a, b, c in triangles(command & 0xf8, count):
                    tri = (corners[a], corners[b], corners[c])
                    if len(set(tri)) == 3:
                        indices.extend(tri)
                continue
            raise ValueError(f'Unsupported GX command {command:#x} at {cursor-1:#x}')
        if cursor != end:
            raise ValueError('Display-list command exceeds declared size')
        if indices:
            primitives.append(dict(material_index=material, indices=indices))
        node = node+next_offset if next_offset else 0
    if not primitives:
        raise ValueError('No triangles')
    name = data[0x30:0x50].split(b'\0', 1)[0].decode('ascii', errors='replace')
    return dict(name=name, vertices=vertices, primitives=primitives)


def write_glb(mesh, target, textures=None):
    blob = bytearray()
    document = dict(asset=dict(version='2.0', generator='TakDecomp subtype-19 static mesh exporter'),
                    scene=0, scenes=[dict(nodes=[0])], nodes=[dict(mesh=0, name=mesh['name'])],
                    meshes=[dict(primitives=[])], buffers=[], bufferViews=[], accessors=[], materials=[])

    def append(raw, **extra):
        while len(blob)%4:
            blob.append(0)
        view = len(document['bufferViews'])
        document['bufferViews'].append(dict(buffer=0, byteOffset=len(blob), byteLength=len(raw), **extra))
        blob.extend(raw)
        return view

    def accessor(values, components, kind):
        flat = [v for row in values for v in row] if components > 1 else values
        raw = struct.pack('<'+('f' if kind == 5126 else 'I')*len(flat), *flat)
        view = append(raw, target=34962 if kind == 5126 else 34963)
        record = dict(bufferView=view, componentType=kind, count=len(values),
                      type={1:'SCALAR', 2:'VEC2', 3:'VEC3'}[components])
        if components == 3 and kind == 5126:
            record.update(min=[min(v[k] for v in values) for k in range(3)],
                          max=[max(v[k] for v in values) for k in range(3)])
        document['accessors'].append(record)
        return len(document['accessors'])-1

    vertices = mesh['vertices']
    attrs = dict(POSITION=accessor([v['position'] for v in vertices], 3, 5126))
    if all(v['normal'] is not None for v in vertices):
        attrs['NORMAL'] = accessor([v['normal'] for v in vertices], 3, 5126)
    if any(v['uv'] is not None for v in vertices):
        # Untextured primitives can share this buffer with textured primitives.
        attrs['TEXCOORD_0'] = accessor([v['uv'] or (0., 0.) for v in vertices], 2, 5126)
    for primitive in mesh['primitives']:
        material = dict(name=f'source_material_{primitive["material_index"]}', doubleSided=True,
                        pbrMetallicRoughness=dict(metallicFactor=0, roughnessFactor=1))
        texture = (textures or {}).get(primitive['material_index'])
        if texture and 'TEXCOORD_0' in attrs:
            view = append(texture.read_bytes())
            image = len(document.setdefault('images', []))
            document['images'].append(dict(bufferView=view, mimeType='image/png'))
            document.setdefault('textures', []).append(dict(source=image))
            material['pbrMetallicRoughness']['baseColorTexture'] = dict(index=image)
            material['alphaMode'] = 'MASK'
            material['alphaCutoff'] = 0.5
        document['materials'].append(material)
        document['meshes'][0]['primitives'].append(dict(attributes=attrs.copy(),
            indices=accessor(primitive['indices'], 1, 5125), mode=4, material=len(document['materials'])-1))
    document['buffers'] = [dict(byteLength=len(blob))]
    encoded = json.dumps(document, separators=(',', ':'), allow_nan=False).encode()
    encoded += b' '*((-len(encoded))%4)
    blob.extend(b'\0'*((-len(blob))%4))
    total = 12+8+len(encoded)+8+len(blob)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(struct.pack('<3I', 0x46546c67, 2, total)+struct.pack('<I4s', len(encoded), b'JSON')+
                       encoded+struct.pack('<I4s', len(blob), b'BIN\0')+blob)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'assets/disc')
    parser.add_argument('--output', type=Path, default=ROOT/'assets/models')
    args = parser.parse_args()
    paths = [args.source] if args.source.is_file() else sorted(args.source.glob('*.dbu'))
    if not paths:
        parser.error('No DBU files found')
    args.output.mkdir(parents=True, exist_ok=True)
    texture_root = ROOT/'assets/textures'
    texture_manifest = texture_root/'manifest.json'
    texture_files = {}
    if texture_manifest.is_file():
        for row in json.loads(texture_manifest.read_text())['textures']:
            texture_files[(Path(row['archive']).name, row['chunk'], row['index'])] = texture_root/row['png']
    entries, errors = [], []
    for path in paths:
        data = path.read_bytes()
        report = archive_report(data)
        local_textures, materials = {}, {}
        for chunk in report['chunks']:
            kind = int(chunk['type'], 16)
            if kind == 0x998:
                local_textures, materials = {}, {}
            if kind in (0x82, 0x86):
                local_textures = {index: path_png for (archive, chunk_index, index), path_png in texture_files.items()
                                  if archive == path.name and chunk_index == chunk['index']}
            if kind == 0x67:
                payload = data[chunk['payload_offset']:chunk['payload_offset']+chunk['payload_size']]
                materials = {}
                for index, offset in enumerate(array_directory(payload)['record_offsets']):
                    # One local layer only. Global/special and multi-layer materials are unresolved.
                    if payload[offset+4] == 1 and not payload[offset+13] & 0x10:
                        texture_index = unpack(payload, 'h', offset+6)[0]
                        if texture_index in local_textures:
                            materials[index] = local_textures[texture_index]
            if kind not in (0x20, 0x21, 0x22, 0x23):
                continue
            start = chunk['payload_offset']
            payload = data[start:start+chunk['payload_size']]
            offsets = array_directory(payload)['record_offsets'] if kind in (0x22, 0x23) else [0]
            for i, off in enumerate(offsets):
                end = offsets[i+1] if i+1 < len(offsets) else len(payload)
                row = dict(archive=path.name, archive_sha256=report['sha256'], chunk=chunk['index'],
                           index=i, source_offset=start+off, path_hint=chunk.get('preceding_path_marker'))
                try:
                    mesh = decode_mesh(payload[off:end])
                    safe = re.sub(r'[^A-Za-z0-9_.-]', '_', mesh['name'])[:64] or 'unnamed'
                    relative = Path(path.name)/f'{chunk["index"]:04d}_{i:04d}_{safe}.glb'
                    write_glb(mesh, args.output/relative, materials)
                    entries.append(dict(**row, name=mesh['name'], glb=relative.as_posix(),
                                        vertices=len(mesh['vertices']), triangles=sum(len(p['indices'])//3 for p in mesh['primitives']),
                                        textured_primitives=sum(p['material_index'] in materials for p in mesh['primitives'])))
                except (ValueError, struct.error) as error:
                    errors.append(dict(**row, error=str(error)))
        print(f'{path.name}: processed', flush=True)
    result = dict(static_meshes_only=True, entries=entries, errors=errors,
                  error_counts=dict(Counter(e['error'] for e in errors)),
                  limitations='Source mesh coordinates; no scene placement, skeletal transforms, baked vertex colors, layered materials, or animation. Only single local texture layers are bound.')
    (args.output/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    from model_gallery import write_gallery
    write_gallery(args.output)
    print(f'Exported {len(entries)} meshes; {len(errors)} unresolved model records')


if __name__ == '__main__':
    main()
