#!/usr/bin/env python3
"""Check assembled nodes against original instance bytes and source mesh exports."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from decode_level import ROOT,accessor_values
from decode_rigs import read_glb
from inspect_dbu import inspect
from decode_resource_arrays import decode as directory
from decode_level_actors import SUPPORTED_CLASSES,padded_string,cstring,replacement_path


def check(folder):
    manifest=json.loads((folder/'manifest.json').read_text());archive=ROOT/'assets/disc'/manifest['archive'];raw=archive.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['archive_sha256']:raise ValueError('Archive hash mismatch')
    chunks=inspect(raw)['chunks'];chunk=chunks[manifest['instance_chunk']]
    if chunk['type']!='0x0060':raise ValueError('Wrong instance chunk type')
    table=directory(raw[chunk['payload_offset']:chunk['payload_offset']+chunk['payload_size']])
    if table.get('stride')!=176 or table['count']!=manifest['instance_count']:raise ValueError('Source instance directory differs')
    exports=json.loads((ROOT/'assets/models/manifest.json').read_text())['entries']
    sources={r['index']:r for r in exports if r['archive']==manifest['archive'] and r['chunk']==manifest['model_chunk']}
    actor_sources={}
    if manifest.get('actors',{}).get('replacements'):
        for category in ('rigs','models'):
            for r in json.loads((ROOT/f'assets/{category}/manifest.json').read_text())['entries']:
                actor_sources[category,r['glb']]=r
    path=folder/(archive.stem+'.glb');framing=path.read_bytes()
    if struct.unpack_from('<3I',framing)!=(0x46546c67,2,len(framing)):raise ValueError('Invalid GLB framing')
    g,blob=read_glb(path);nodes=g['nodes'];meshes=g['meshes'];cache={}
    def accessor(i):
        if i not in cache:cache[i]=accessor_values(g,blob,i)
        return cache[i]
    for v in g['bufferViews']:
        start=v.get('byteOffset',0)
        if start%4 or start<0 or v['byteLength']<0 or start+v['byteLength']>len(blob):raise ValueError('Invalid buffer view range')
    for i,a in enumerate(g['accessors']):
        v=g['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        size={5126:4,5125:4,5123:2}[a['componentType']]*width
        if a.get('byteOffset',0)+(a['count']-1)*v.get('byteStride',size)+size>v['byteLength']:raise ValueError('Accessor outside view')
        if not all(math.isfinite(x) for row in accessor(i) for x in row):raise ValueError('Non-finite accessor')
    mesh_triangles={};mesh_positions={}
    for i,mesh in enumerate(meshes):
        mesh_triangles[i]=0;pos={}
        for p in mesh['primitives']:
            a=p['attributes'];positions=accessor(a['POSITION']);pos[a['POSITION']]=positions
            indices=[r[0] for r in accessor(p['indices'])]
            if not indices or len(indices)%3 or min(indices)<0 or max(indices)>=len(positions):raise ValueError('Invalid triangle indices')
            for key,index in a.items():
                if len(accessor(index))!=len(positions):raise ValueError('Mismatched vertex attributes')
            if not 0<=p['material']<len(g['materials']):raise ValueError('Invalid material reference')
            mesh_triangles[i]+=len(indices)//3
        mesh_positions[i]=[p for values in pos.values() for p in values]
    for material in g['materials']:
        texture=material['pbrMetallicRoughness'].get('baseColorTexture')
        if texture:
            if not 0<=g['textures'][texture['index']]['source']<len(g['images']):raise ValueError('Invalid image reference')
    image_hashes=[]
    for image in g['images']:
        v=g['bufferViews'][image['bufferView']];at=v.get('byteOffset',0);content=blob[at:at+v['byteLength']]
        if content[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Invalid embedded PNG')
        image_hashes.append(hashlib.sha256(content).hexdigest())
    if len(image_hashes)!=len(set(image_hashes)):raise ValueError('Duplicate embedded texture bytes')
    if len(nodes)!=manifest['instance_count'] or len(meshes)!=manifest['unique_meshes']:raise ValueError('Manifest scene count mismatch')
    if sorted(g['scenes'][g['scene']]['nodes'])!=list(range(len(nodes))):raise ValueError('Missing scene nodes')
    model_sources={};placed_triangles=0;overflow=0;nonproxy=0;actors=0
    for node,row in zip(nodes,manifest['instances']):
        at=row['source_offset'];matrix=list(struct.unpack_from('>16f',raw,at+0x10));reference=struct.unpack_from('>I',raw,at+0x78)[0]
        if at!=chunk['payload_offset']+table['record_offsets'][row['index']]:raise ValueError('Source instance offset differs')
        source=sources[row['model_index']]
        if row['model_glb']!=source['glb'] or source['archive_sha256']!=manifest['archive_sha256']:raise ValueError('Source mesh provenance differs')
        source_path=ROOT/'assets/models'/row['model_glb'];source_key=('models',row['model_glb']);actor=row.get('actor')
        if actor:
            actors+=1;env=chunks[actor['environment_chunk']]
            if env['type']!='0x0402':raise ValueError('Actor source is not an environment chunk')
            payload=raw[env['payload_offset']:env['payload_offset']+env['payload_size']]
            cls,cur=padded_string(payload,actor['record_offset']);name,cur=padded_string(payload,cur);override,_=padded_string(payload,cur)
            if cls not in SUPPORTED_CLASSES or (cls,name,override)!=(actor['actor_class'],actor['instance_name'],actor['model_override']):raise ValueError('Actor prefix differs from source bytes')
            aux=at+struct.unpack_from('>I',raw,at+0x94)[0];instance_name,_=cstring(raw,aux+0x20)
            if instance_name.lower()!=name.lower():raise ValueError('Actor linked to wrong instance name')
            if actor['environment_source_offset']!=env['payload_offset']+actor['record_offset']:raise ValueError('Actor source offset mismatch')
            if actor['instance_index']!=row['index'] or actor['instance_indices']!=[row['index']]:raise ValueError('Actor instance association differs')
            source_key=(actor['asset_category'],actor['asset_glb']);asset=actor_sources[source_key]
            if (asset.get('path_hint') or '').lower()!=replacement_path(override):raise ValueError('Actor override resolves to different resource')
            if asset['archive'] not in (manifest['archive'],'Preload.dbu'):raise ValueError('Actor asset comes from an unrelated level')
            if (asset['archive'],asset['chunk'],asset['index'],asset['archive_sha256'])!=(actor['asset_archive'],actor['asset_chunk'],actor['asset_index'],actor['asset_archive_sha256']):raise ValueError('Actor asset provenance mismatch')
            source_path=ROOT/'assets'/source_key[0]/source_key[1]
            if hashlib.sha256(source_path.read_bytes()).hexdigest()!=actor['asset_sha256']:raise ValueError('Actor source asset hash mismatch')
            if node['extras'].get('actor')!=actor or node['extras']['previewGroup']!='actors':raise ValueError('Actor node metadata mismatch')
        # Source floats are exactly representable as JSON numbers; no tolerance hides matrix changes.
        if node['matrix']!=matrix or row['matrix']!=matrix:raise ValueError('Instance transform differs from original bytes')
        if reference!=row['model_reference'] or reference&0xffffff!=row['model_index']:raise ValueError('Model reference differs from original bytes')
        if node['extras']['instanceIndex']!=row['index']:raise ValueError('Instance provenance mismatch')
        mi=node['mesh'];placed_triangles+=mesh_triangles[mi]
        if mi not in model_sources:
            sg,sb=read_glb(source_path);exported=meshes[mi]['primitives'];original=sg['meshes'][0]['primitives']
            if actor and actor['asset_category']=='rigs':
                from check_rig_exports import check as check_rig
                check_rig(source_path)
            if len(exported)!=len(original):raise ValueError('Source primitive count differs')
            for a,b in zip(exported,original):
                expected={k:v for k,v in b['attributes'].items() if not (actor and k.startswith(('JOINTS_','WEIGHTS_')))}
                if a['attributes'].keys()!=expected.keys():raise ValueError('Source attribute set differs')
                for key in a['attributes']:
                    if accessor(a['attributes'][key])!=accessor_values(sg,sb,b['attributes'][key]):raise ValueError('Source vertex attribute changed')
                if accessor(a['indices'])!=accessor_values(sg,sb,b['indices']):raise ValueError('Source triangle order changed')
                sm=sg['materials'][b['material']]['pbrMetallicRoughness'].get('baseColorTexture');tm=g['materials'][a['material']]['pbrMetallicRoughness'].get('baseColorTexture')
                if bool(sm)!=bool(tm):raise ValueError('Source texture binding changed')
                if sm:
                    si=sg['images'][sg['textures'][sm['index']]['source']];sv=sg['bufferViews'][si['bufferView']];so=sv.get('byteOffset',0)
                    if hashlib.sha256(sb[so:so+sv['byteLength']]).hexdigest()!=image_hashes[g['textures'][tm['index']]['source']]:raise ValueError('Source texture pixels changed')
            model_sources[mi]=source_key
        elif model_sources[mi]!=source_key:raise ValueError('Different source models share one mesh')
        source_bounds=list(struct.unpack_from('>6f',raw,at+0x60));lo=[math.inf]*3;hi=[-math.inf]*3
        for p in mesh_positions[mi]:
            for k in range(3):
                x=matrix[k]*p[0]+matrix[k+4]*p[1]+matrix[k+8]*p[2]+matrix[k+12];lo[k]=min(lo[k],x);hi[k]=max(hi[k],x)
        excess=max([0.]+[source_bounds[k]-lo[k] for k in range(3)]+[hi[k]-source_bounds[k+3] for k in range(3)])
        overflow=max(overflow,excess)
        if not row['box_proxy_candidate']:
            nonproxy=max(nonproxy,excess)
            if excess>.01:raise ValueError('Non-proxy geometry exceeds authored world bounds')
        if any(abs(x-y)>1e-8 for x,y in zip(lo+hi,row['export_bounds']['min']+row['export_bounds']['max'])):raise ValueError('Exported bounds mismatch')
    if placed_triangles!=manifest['triangles']:raise ValueError('Placed triangle count mismatch')
    if actors!=manifest.get('actors',{}).get('replacements',0):raise ValueError('Actor manifest count mismatch')
    return dict(instances=len(nodes),meshes=len(meshes),triangles=placed_triangles,images=len(image_hashes),
                actors=actors,maximum_bounds_overflow=overflow,maximum_nonproxy_bounds_overflow=nonproxy)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',nargs='?',type=Path,default=ROOT/'assets/levels/Hub')
    args=parser.parse_args();result=check(args.folder);print('PASS:',json.dumps(result))


if __name__=='__main__':main()
