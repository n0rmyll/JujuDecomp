#!/usr/bin/env python3
"""Recover subtype-19 bone trees and rigid GX vertex influences as skinned GLBs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from decode_models import decode_mesh, write_glb, unpack, word
from decode_resource_arrays import decode as directory
from inspect_dbu import inspect

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = [1.0 if i%5 == 0 else 0.0 for i in range(16)]


def multiply(a, b):
    return [sum(a[k*4+r]*b[c*4+k] for k in range(4)) for c in range(4) for r in range(4)]


def invert(matrix):
    rows=[[matrix[c*4+r] for c in range(4)]+[float(c==r) for c in range(4)] for r in range(4)]
    for k in range(4):
        pivot=max(range(k,4),key=lambda r:abs(rows[r][k]))
        if abs(rows[pivot][k])<1e-10:raise ValueError('Singular bind matrix')
        rows[k],rows[pivot]=rows[pivot],rows[k]
        divisor=rows[k][k];rows[k]=[v/divisor for v in rows[k]]
        for r in range(4):
            if r!=k:
                value=rows[r][k];rows[r]=[v-value*w for v,w in zip(rows[r],rows[k])]
    return [rows[r][4+c] for c in range(4) for r in range(4)]


def decode_skeleton(data, record_offset=0):
    if len(data)<148 or data[0]!=19 or not unpack(data,'H',2)[0]&0x40:
        raise ValueError('No supported embedded skeleton flag')
    if unpack(data,'H',2)[0]&1:
        raise ValueError('Skeleton shared from a preceding model record')
    end_uv=word(data,0x90)+8*word(data,0x8c)
    start=((record_offset+end_uv+31)&~31)-record_offset
    bones={}
    active=set()

    def visit(index, parent):
        if index in active or index in bones:
            raise ValueError('Cyclic or multiply parented bone hierarchy')
        if index>4096:
            raise ValueError('Implausible bone index')
        offset=start+index*240
        bind=list(unpack(data,'16f',offset)); inverse=list(unpack(data,'16f',offset+64))
        child,sibling=unpack(data,'2I',offset+128)
        raw=data[offset+176:offset+192].split(b'\0',1)[0]
        if not raw or any(v<32 or v>126 for v in raw):
            raise ValueError('Invalid bone name')
        if not all(math.isfinite(v) for v in bind+inverse):
            raise ValueError('Invalid bone matrix')
        error=max(abs(v-IDENTITY[i]) for i,v in enumerate(multiply(bind,inverse)))
        if error>0.05:
            raise ValueError(f'Bind/inverse mismatch ({error:.6g})')
        source_id=data[offset+201]
        bones[index]=dict(index=index,source_id=source_id,name=raw.decode('ascii'),parent=parent,
                          bind=bind,inverse_bind=invert(bind),stored_inverse_bind=inverse,source_offset=offset,
                          inverse_error=error)
        active.add(index)
        if child:visit(child,index)
        active.remove(index)
        if sibling:visit(sibling,parent)
    visit(0,None)
    ordered=[bones[k] for k in sorted(bones)]
    if len({b['source_id'] for b in ordered})!=len(ordered):
        raise ValueError('Duplicate source bone IDs')
    for b in ordered:
        b['local']=multiply(bones[b['parent']]['inverse_bind'],b['bind']) if b['parent'] is not None else b['bind']
    return dict(offset=start,bones=ordered)


def read_glb(path):
    data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+n]),bytearray(data[28+n:])


def save_glb(path, document, blob):
    document['buffers']=[dict(byteLength=len(blob))]
    encoded=json.dumps(document,separators=(',',':'),allow_nan=False).encode()
    encoded+=b' '*((-len(encoded))%4);blob.extend(b'\0'*((-len(blob))%4))
    path.write_bytes(struct.pack('<3I',0x46546c67,2,28+len(encoded)+len(blob))+
                     struct.pack('<I4s',len(encoded),b'JSON')+encoded+
                     struct.pack('<I4s',len(blob),b'BIN\0')+blob)


def add_accessor(document, blob, values, components, kind=5126, shape=None):
    while len(blob)%4:blob.append(0)
    fmt={5126:'f',5123:'H'}[kind]
    flat=[v for row in values for v in row] if components>1 else values
    raw=struct.pack('<'+fmt*len(flat),*flat)
    view=len(document['bufferViews'])
    document['bufferViews'].append(dict(buffer=0,byteOffset=len(blob),byteLength=len(raw)))
    blob.extend(raw)
    accessor=dict(bufferView=view,componentType=kind,count=len(values),
                  type=shape or {1:'SCALAR',3:'VEC3',4:'VEC4',16:'MAT4'}[components])
    if components==1:accessor.update(min=[min(values)],max=[max(values)])
    document['accessors'].append(accessor)
    return len(document['accessors'])-1


def attach_skin(path, mesh, skeleton):
    document,blob=read_glb(path);bones=skeleton['bones']
    indices={b['index']:i for i,b in enumerate(bones)}
    ids={b['source_id']:i for i,b in enumerate(bones)}
    if any(v['joint'] not in ids for v in mesh['vertices']):
        raise ValueError('Vertex palette references absent bone')
    root_nodes=[]
    for b in bones:
        node=dict(name=b['name'],matrix=b['local'])
        children=[1+indices[c['index']] for c in bones if c['parent']==b['index']]
        if children:node['children']=children
        if b['parent'] is None:root_nodes.append(1+indices[b['index']])
        document['nodes'].append(node)
    joint_accessor=add_accessor(document,blob,[(ids[v['joint']],0,0,0) for v in mesh['vertices']],4,5123)
    weight_accessor=add_accessor(document,blob,[(1.,0.,0.,0.) for v in mesh['vertices']],4)
    inverse=add_accessor(document,blob,[b['inverse_bind'] for b in bones],16)
    document['skins']=[dict(name=mesh['name']+'_skin',joints=list(range(1,len(bones)+1)),
                            inverseBindMatrices=inverse,skeleton=root_nodes[0])]
    document['nodes'][0]['skin']=0
    document['scenes'][0]['nodes']=[0]+root_nodes
    for p in document['meshes'][0]['primitives']:
        p['attributes'].update(JOINTS_0=joint_accessor,WEIGHTS_0=weight_accessor)
    save_glb(path,document,blob)


def material_bindings(data, chunks, archive):
    texture_root=ROOT/'assets/textures'
    manifest=texture_root/'manifest.json'
    if not manifest.exists():return {}
    entries=json.loads(manifest.read_text())['textures']
    bychunk={}
    for row in entries:
        if Path(row['archive']).name==archive:
            bychunk.setdefault(row['chunk'],{})[row['index']]=texture_root/row['png']
    result={};textures={};materials={}
    for c in chunks:
        kind=int(c['type'],16)
        if kind==0x998:textures={};materials={}
        if kind in (0x82,0x86):textures=bychunk.get(c['index'],{})
        if kind==0x67:
            p=data[c['payload_offset']:c['payload_offset']+c['payload_size']];materials={}
            for i,o in enumerate(directory(p)['record_offsets']):
                if p[o+4]==1 and not p[o+13]&0x10:
                    index=unpack(p,'h',o+6)[0]
                    if index in textures:materials[i]=textures[index]
        result[c['index']]=materials.copy()
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'assets/disc')
    parser.add_argument('--output',type=Path,default=ROOT/'assets/rigs')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    paths=[args.source] if args.source.is_file() else sorted(args.source.glob('*.dbu'))
    entries=[];errors=[]
    for path in paths:
        data=path.read_bytes();report=inspect(data);bindings=material_bindings(data,report['chunks'],path.name)
        for c in report['chunks']:
            kind=int(c['type'],16)
            if kind not in (0x20,0x21,0x22,0x23):continue
            p=data[c['payload_offset']:c['payload_offset']+c['payload_size']]
            offsets=directory(p)['record_offsets'] if kind in (0x22,0x23) else [0]
            shared=None
            for i,o in enumerate(offsets):
                b=p[o:offsets[i+1] if i+1<len(offsets) else len(p)]
                if len(b)<4 or b[0]!=19 or not unpack(b,'H',2)[0]&0x40:continue
                row=dict(archive=path.name,archive_sha256=report['sha256'],chunk=c['index'],index=i,
                         source_offset=c['payload_offset']+o,path_hint=c.get('preceding_path_marker'))
                target=None
                try:
                    if not unpack(b,'H',2)[0]&1:shared=decode_skeleton(b,o)
                    if shared is None:raise ValueError('Missing preceding shared skeleton')
                    mesh=decode_mesh(b,capture_skin=True)
                    safe=re.sub(r'[^A-Za-z0-9_.-]','_',mesh['name'])[:64] or 'unnamed'
                    relative=Path(path.name)/f'{c["index"]:04d}_{i:04d}_{safe}.glb'
                    target=args.output/relative
                    write_glb(mesh,target,bindings[c['index']]);attach_skin(target,mesh,shared)
                    rig_json=relative.with_suffix('.skeleton.json')
                    (args.output/rig_json).write_text(json.dumps(shared,indent=2)+'\n')
                    entries.append(dict(**row,name=mesh['name'],glb=relative.as_posix(),skeleton=rig_json.as_posix(),
                                        bones=len(shared['bones']),vertices=len(mesh['vertices']),
                                        triangles=sum(len(p['indices'])//3 for p in mesh['primitives'])))
                except (ValueError,struct.error) as error:
                    if target:target.unlink(missing_ok=True)
                    errors.append(dict(**row,error=str(error)))
        print(path.name,flush=True)
    result=dict(entries=entries,errors=errors,limitations='Rigid one-bone influences from GX palettes; bind-pose rigs only until animation conversion is verified.')
    (args.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Exported {len(entries)} skinned GLBs; {len(errors)} unresolved skeletal records')


if __name__=='__main__':main()
