#!/usr/bin/env python3
"""Validate skin attributes, hierarchy/bind consistency, and animation accessors."""
import json
import math
from pathlib import Path
import struct
from decode_rigs import ROOT,read_glb,multiply,IDENTITY
from decode_animations import compose


def check(path):
    g,blob=read_glb(path)
    def accessor(index):
        a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        fmt={5126:'f',5123:'H',5125:'I'}[a['componentType']]
        size=struct.calcsize(fmt)*n*a['count']
        if v['byteOffset']%4 or v['byteOffset']+size>len(blob):raise ValueError('Invalid accessor bounds')
        return [struct.unpack_from('<'+fmt*n,blob,v['byteOffset']+i*n*struct.calcsize(fmt)) for i in range(a['count'])]
    for i in range(len(g['accessors'])):
        if not all(math.isfinite(v) for row in accessor(i) for v in row):raise ValueError('Non-finite attribute')
    skin=g['skins'][0]
    parents={child:i for i,node in enumerate(g['nodes']) for child in node.get('children',[])};worlds={}
    def world(i,active=None):
        if i in worlds:return worlds[i]
        active=set() if active is None else active
        if i in active:raise ValueError('Cyclic hierarchy')
        active.add(i);n=g['nodes'][i]
        local=n.get('matrix') or compose(n.get('translation',[0,0,0]),n.get('rotation',[0,0,0,1]),n.get('scale',[1,1,1]))
        worlds[i]=multiply(world(parents[i],active),local) if i in parents else local
        active.remove(i);return worlds[i]
    inverse=accessor(skin['inverseBindMatrices'])
    if len(inverse)!=len(skin['joints']):raise ValueError('Inverse matrix count')
    for j,i in enumerate(skin['joints']):
        if max(abs(v-IDENTITY[k]) for k,v in enumerate(multiply(world(i),inverse[j])))>0.006:raise ValueError('Bind reconstruction mismatch')
    for p in g['meshes'][0]['primitives']:
        a=p['attributes'];positions=accessor(a['POSITION']);joints=accessor(a['JOINTS_0']);weights=accessor(a['WEIGHTS_0'])
        if len(joints)!=len(positions) or len(weights)!=len(positions):raise ValueError('Attribute counts')
        if any(abs(sum(w)-1)>1e-6 or min(w)<0 for w in weights):raise ValueError('Invalid skin weight')
        if any(j>=len(skin['joints']) for row in joints for j in row):raise ValueError('Joint index bounds')
    for animation in g.get('animations',[]):
        for channel in animation['channels']:
            sampler=animation['samplers'][channel['sampler']];times=accessor(sampler['input']);values=accessor(sampler['output'])
            if len(times)!=len(values) or any(a[0]>=b[0] for a,b in zip(times,times[1:])):raise ValueError('Invalid animation keys')
            if channel['target']['path']=='rotation' and any(abs(sum(v*v for v in q)-1)>1e-4 for q in values):raise ValueError('Non-unit quaternion')
    return len(skin['joints']),len(g.get('animations',[]))


def main():
    count=motions=0
    for category in ('rigs','animations'):
        manifest=json.loads((ROOT/f'assets/{category}/manifest.json').read_text())
        for e in manifest['entries']:
            if 'glb' not in e:continue
            _,clips=check(ROOT/f'assets/{category}'/e['glb']);count+=1;motions+=clips
    print(f'PASS: {count} skinned GLBs; {motions} animation clips; bind pose, joints, weights, accessor bounds, times, and quaternions checked.')


if __name__=='__main__':main()
