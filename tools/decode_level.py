#!/usr/bin/env python3
"""Assemble an authored static world from verified 0x60 instance records."""
import argparse
import base64
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from decode_resource_arrays import decode as directory
from decode_rigs import ROOT, read_glb, save_glb
from inspect_dbu import inspect


def preview_group(name):
    """Name-based display convenience, not recovered engine visibility semantics."""
    if re.search(r'Skydome|swirly_clouds|Moon_Plane',name,re.I):return 'sky'
    if re.match(r'Background_|Bottom_Plane',name,re.I):return 'backdrop'
    if re.match(r'Coll_|Death_|None$',name,re.I):return 'helper'
    if re.search(r'Canopy|OuterTreeRing',name,re.I):return 'canopy'
    return 'scenery'


def decode_instances(payload, model_count):
    table=directory(payload)
    if table['mode']!='fixed stride' or table.get('stride')!=176:
        raise ValueError('Unsupported instance directory (expected 176-byte fixed stride)')
    rows=[]
    for index,offset in enumerate(table['record_offsets']):
        flags=struct.unpack_from('>H',payload,offset+2)[0]
        reference=struct.unpack_from('>I',payload,offset+0x78)[0]
        if flags&4:raise ValueError('Alternate 0x62 model references are unsupported')
        model=reference&0xffffff  # fn_801B92FC masks the resource tag byte.
        if model>=model_count:raise ValueError('Instance model index outside model array')
        matrix=list(struct.unpack_from('>16f',payload,offset+0x10))
        bounds=list(struct.unpack_from('>6f',payload,offset+0x60))
        if not all(math.isfinite(v) for v in matrix+bounds):raise ValueError('Non-finite instance transform or bounds')
        if any(abs(matrix[k])>1e-6 for k in (3,7,11)) or abs(matrix[15]-1)>1e-6:
            raise ValueError('Non-affine instance matrix')
        if any(bounds[k]>bounds[k+3] for k in range(3)):raise ValueError('Inverted instance bounds')
        aux=offset+struct.unpack_from('>I',payload,offset+0x94)[0]
        if aux<0 or aux+0x18>len(payload):raise ValueError('Instance auxiliary record outside payload')
        parent=struct.unpack_from('>I',payload,aux+0x14)[0]
        # Hub has no parents. Do not silently assume local/world semantics elsewhere.
        if parent!=0xffffffff:raise ValueError('Parented instance transforms are unsupported')
        rows.append(dict(index=index,record_offset=offset,flags=flags,model_reference=reference,
                         model_index=model,matrix=matrix,source_bounds=dict(min=bounds[:3],max=bounds[3:]),
                         parent=None,auxiliary_offset=aux))
    return rows


def accessor_values(g,blob,index):
    a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
    components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    fmt={5126:'f',5125:'I',5123:'H'}[a['componentType']];size=struct.calcsize(fmt)*components
    start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
    return [struct.unpack_from('<'+fmt*components,blob,start+i*stride) for i in range(a['count'])]


class SceneBuilder:
    """Merge static GLBs, retaining mesh instances and deduplicating texture bytes."""
    def __init__(self):
        self.g=dict(asset=dict(version='2.0',generator='TakDecomp static level assembler'),scene=0,
                    scenes=[dict(name='Authored static world',nodes=[])],nodes=[],meshes=[],
                    buffers=[],bufferViews=[],accessors=[],materials=[],images=[],textures=[])
        self.blob=bytearray();self.images={};self.textures={};self.materials={};self.positions={};self.triangles={}

    def view(self,raw,extra=None):
        while len(self.blob)%4:self.blob.append(0)
        index=len(self.g['bufferViews'])
        self.g['bufferViews'].append(dict(buffer=0,byteOffset=len(self.blob),byteLength=len(raw),**(extra or {})))
        self.blob.extend(raw);return index

    def add_mesh(self,path):
        source,blob=read_glb(path)
        if len(source['meshes'])!=1 or source.get('skins'):raise ValueError('Expected a single static source mesh')
        views={};accessors={};textures={};materials={}
        for i,image in enumerate(source.get('images',[])):
            v=source['bufferViews'][image['bufferView']];raw=bytes(blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
            key=(image['mimeType'],hashlib.sha256(raw).hexdigest())
            if key not in self.images:
                self.images[key]=len(self.g['images'])
                self.g['images'].append(dict(bufferView=self.view(raw),mimeType=image['mimeType']))
            for j,t in enumerate(source.get('textures',[])):
                if t['source']!=i:continue
                if 'sampler' in t:raise ValueError('Source texture samplers are unsupported')
                target=self.images[key]
                if target not in self.textures:
                    self.textures[target]=len(self.g['textures']);self.g['textures'].append(dict(source=target))
                textures[j]=self.textures[target]
        for i,mat in enumerate(source['materials']):
            mat=copy.deepcopy(mat);pbr=mat['pbrMetallicRoughness']
            if 'baseColorTexture' in pbr:pbr['baseColorTexture']['index']=textures[pbr['baseColorTexture']['index']]
            mat.pop('name',None);key=json.dumps(mat,sort_keys=True)
            if key not in self.materials:
                self.materials[key]=len(self.g['materials']);self.g['materials'].append(mat)
            materials[i]=self.materials[key]
        def accessor(index):
            if index not in accessors:
                a=copy.deepcopy(source['accessors'][index]);v=a['bufferView']
                if v not in views:
                    old=source['bufferViews'][v];offset=old.get('byteOffset',0)
                    views[v]=self.view(blob[offset:offset+old['byteLength']],{k:x for k,x in old.items() if k not in ('buffer','byteOffset','byteLength')})
                a['bufferView']=views[v];accessors[index]=len(self.g['accessors']);self.g['accessors'].append(a)
            return accessors[index]
        mesh=copy.deepcopy(source['meshes'][0]);mesh['name']=source['nodes'][0].get('name',path.stem)
        positions=[];position_accessors=set();triangles=0
        for p in mesh['primitives']:
            if p.get('mode',4)!=4:raise ValueError('Non-triangle source primitive')
            position=p['attributes']['POSITION']
            if position not in position_accessors:
                positions.extend(accessor_values(source,blob,position));position_accessors.add(position)
            triangles+=source['accessors'][p['indices']]['count']//3
            p['attributes']={k:accessor(v) for k,v in p['attributes'].items()}
            p['indices']=accessor(p['indices']);p['material']=materials[p['material']]
        index=len(self.g['meshes']);self.g['meshes'].append(mesh);self.positions[index]=positions;self.triangles[index]=triangles
        return index

    def add_instance(self,row,mesh):
        m=row['matrix'];lo=[math.inf]*3;hi=[-math.inf]*3
        for p in self.positions[mesh]:
            for k in range(3):
                v=m[k]*p[0]+m[4+k]*p[1]+m[8+k]*p[2]+m[12+k];lo[k]=min(lo[k],v);hi[k]=max(hi[k],v)
        row['export_bounds']=dict(min=lo,max=hi)
        row['bounds_overflow']=max([0.]+[row['source_bounds']['min'][k]-lo[k] for k in range(3)]+[hi[k]-row['source_bounds']['max'][k] for k in range(3)])
        index=len(self.g['nodes']);self.g['scenes'][0]['nodes'].append(index)
        self.g['nodes'].append(dict(mesh=mesh,matrix=m,name=f"{row['index']:04d} / {row['model_name']}",
                                    extras=dict(instanceIndex=row['index'],sourceOffset=row['source_offset'],sourceFlags=row['flags'],modelIndex=row['model_index'],previewGroup=row['preview_group'])))


def export_level(source,output):
    data=source.read_bytes();report=inspect(data);chunks=report['chunks']
    candidates=[c for c in chunks if c['type']=='0x0060']
    if len(candidates)!=1:raise ValueError('Expected exactly one instance array')
    instances=candidates[0];hint=instances.get('preceding_path_marker')
    models=[c for c in chunks if c['type'] in ('0x0022','0x0023') and c.get('preceding_path_marker')==hint]
    if len(models)!=1:raise ValueError('Expected one model array in the instance resource group')
    models=models[0];model_count=directory(data[models['payload_offset']:models['payload_offset']+models['payload_size']])['count']
    rows=decode_instances(data[instances['payload_offset']:instances['payload_offset']+instances['payload_size']],model_count)
    exports=json.loads((ROOT/'assets/models/manifest.json').read_text())['entries']
    by_index={r['index']:r for r in exports if r['archive']==source.name and r['chunk']==models['index']}
    needed={r['model_index'] for r in rows}
    if not needed<=by_index.keys():raise ValueError(f'Missing exported meshes: {sorted(needed-by_index.keys())}')
    if any(by_index[i]['archive_sha256']!=report['sha256'] for i in needed):raise ValueError('Source model manifest hash mismatch')
    builder=SceneBuilder();mapping={i:builder.add_mesh(ROOT/'assets/models'/by_index[i]['glb']) for i in sorted(needed)}
    for row in rows:
        mesh=by_index[row['model_index']];row.update(source_offset=instances['payload_offset']+row['record_offset'],
                                                  model_name=mesh['name'],model_glb=mesh['glb'],preview_group=preview_group(mesh['name']))
        row['box_proxy_candidate']=mesh['vertices']==8 and mesh['triangles']==12 and not mesh['textured_primitives']
        if row['box_proxy_candidate'] and row['preview_group']=='scenery':row['preview_group']='helper'
        builder.add_instance(row,mapping[row['model_index']])
    bounds={kind:[(min if kind=='min' else max)(r['export_bounds'][kind][k] for r in rows) for k in range(3)] for kind in ('min','max')}
    scenery=[r for r in rows if r['preview_group']=='scenery'] or rows
    preview_bounds={kind:[(min if kind=='min' else max)(r['export_bounds'][kind][k] for r in scenery) for k in range(3)] for kind in ('min','max')}
    manifest=dict(archive=source.name,archive_sha256=report['sha256'],path_hint=hint,instance_chunk=instances['index'],
                  model_chunk=models['index'],available_models=model_count,unique_meshes=len(needed),instance_count=len(rows),
                  triangles=sum(builder.triangles[mapping[r['model_index']]] for r in rows),embedded_images=len(builder.g['images']),
                  bounds=bounds,preview_bounds=preview_bounds,preview_group_counts={name:sum(r['preview_group']==name for r in rows) for name in ('scenery','sky','backdrop','helper','canopy')},
                  maximum_bounds_overflow=max(r['bounds_overflow'] for r in rows),instances=rows,
                  limitations='Authored static placements only. All source records retained; gameplay visibility, LOD selection, actors, skeletal motion, collision, particles, lighting and layered materials are not reconstructed.')
    manifest['maximum_nonproxy_bounds_overflow']=max([0.]+[r['bounds_overflow'] for r in rows if not r['box_proxy_candidate']])
    builder.g['scenes'][0]['name']=source.stem+' / authored static scene';builder.g['extras']={k:v for k,v in manifest.items() if k!='instances'}
    output.mkdir(parents=True,exist_ok=True);target=output/(source.stem+'.glb');save_glb(target,builder.g,builder.blob)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    viewer=(ROOT/'tools/level_viewer.html').read_text().replace('__LEVEL_GLB__',base64.b64encode(target.read_bytes()).decode())
    viewer=viewer.replace('__LEVEL_NAME__',source.stem).replace('__LEVEL_FILE__',target.name)
    (output/'index.html').write_text(viewer)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'assets/disc/Hub.dbu')
    parser.add_argument('--output',type=Path,default=ROOT/'assets/levels/Hub')
    args=parser.parse_args();m=export_level(args.source,args.output)
    print(f"{m['archive']}: {m['instance_count']} instances, {m['unique_meshes']} meshes, {m['triangles']} placed triangles; max bounds overflow {m['maximum_bounds_overflow']:.6g}")


if __name__=='__main__':main()
