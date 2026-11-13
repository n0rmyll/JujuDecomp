#!/usr/bin/env python3
"""Render two sampled Tak walk poses from the exported animated GLB."""
import json
import math
from pathlib import Path
import struct
import zlib
from decode_rigs import ROOT, read_glb, multiply, IDENTITY
from decode_animations import compose,normalize
from decode_textures import png_bytes


def render(path,time,size=384):
    g,blob=read_glb(path)
    def accessor(index):
        a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];f={5126:'f',5123:'H',5125:'I'}[a['componentType']]
        return [struct.unpack_from('<'+f*n,blob,v['byteOffset']+i*n*struct.calcsize(f)) for i in range(a['count'])]
    poses=[dict(t=n.get('translation',[0,0,0]),q=n.get('rotation',[0,0,0,1]),s=n.get('scale',[1,1,1]),matrix=n.get('matrix')) for n in g['nodes']]
    animation=g['animations'][0]
    for channel in animation['channels']:
        sampler=animation['samplers'][channel['sampler']];times=[v[0] for v in accessor(sampler['input'])];values=accessor(sampler['output'])
        i=0
        while i<len(times)-2 and times[i+1]<time:i+=1
        j=min(i+1,len(times)-1);factor=max(0,min(1,(time-times[i])/(times[j]-times[i]))) if times[j]!=times[i] else 0
        value=[a*(1-factor)+b*factor for a,b in zip(values[i],values[j])]
        path_key={'translation':'t','rotation':'q','scale':'s'}[channel['target']['path']]
        poses[channel['target']['node']][path_key]=value
    parents={child:i for i,n in enumerate(g['nodes']) for child in n.get('children',[])};globals={}
    def global_matrix(i):
        if i not in globals:
            p=poses[i];local=p['matrix'] or compose(p['t'],p['q'],p['s'])
            globals[i]=multiply(global_matrix(parents[i]),local) if i in parents else local
        return globals[i]
    skin=g['skins'][0];inverse=accessor(skin['inverseBindMatrices']);palette=[multiply(global_matrix(i),inverse[k]) for k,i in enumerate(skin['joints'])]
    textures=[]
    for image in g.get('images',[]):
        view=g['bufferViews'][image['bufferView']];png=blob[view['byteOffset']:view['byteOffset']+view['byteLength']]
        w,h=struct.unpack_from('>2I',png,16);cursor=8;compressed=b''
        while cursor<len(png):
            n=struct.unpack_from('>I',png,cursor)[0]
            if png[cursor+4:cursor+8]==b'IDAT':compressed+=png[cursor+8:cursor+8+n]
            cursor+=n+12
        raw=zlib.decompress(compressed);assert all(raw[y*(w*4+1)]==0 for y in range(h))
        textures.append((w,h,raw))
    mesh=g['meshes'][0];a=mesh['primitives'][0]['attributes'];positions=accessor(a['POSITION']);joints=accessor(a['JOINTS_0']);weights=accessor(a['WEIGHTS_0']);uv=accessor(a['TEXCOORD_0']);projected=[]
    for p,js,ws in zip(positions,joints,weights):
        v=[sum(ws[j]*(palette[js[j]][r]*p[0]+palette[js[j]][4+r]*p[1]+palette[js[j]][8+r]*p[2]+palette[js[j]][12+r]) for j in range(4) if ws[j]) for r in range(3)]
        x,y,z=v;x,z=x*math.cos(.25)+z*math.sin(.25),-x*math.sin(.25)+z*math.cos(.25)
        projected.append((size/2+x*size*.5,size*.88-y*size*.5,z))
    out=bytearray(bytes([37,42,51,255])*(size*size));depth=[-math.inf]*(size*size)
    for primitive in mesh['primitives']:
        material=g['materials'][primitive['material']];texture=material['pbrMetallicRoughness'].get('baseColorTexture')
        tex=textures[g['textures'][texture['index']]['source']] if texture else None
        indices=[v[0] for v in accessor(primitive['indices'])]
        for i in range(0,len(indices),3):
            ids=indices[i:i+3];a,b,c=[projected[j] for j in ids];det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(det)<1e-8:continue
            for y in range(max(0,int(min(a[1],b[1],c[1]))),min(size,math.ceil(max(a[1],b[1],c[1])))):
                for x in range(max(0,int(min(a[0],b[0],c[0]))),min(size,math.ceil(max(a[0],b[0],c[0])))):
                    wa=((b[1]-c[1])*(x+.5-c[0])+(c[0]-b[0])*(y+.5-c[1]))/det
                    wb=((c[1]-a[1])*(x+.5-c[0])+(a[0]-c[0])*(y+.5-c[1]))/det;wc=1-wa-wb
                    if min(wa,wb,wc)<0:continue
                    z=wa*a[2]+wb*b[2]+wc*c[2];pos=y*size+x
                    if z<=depth[pos]:continue
                    color=bytes([180,180,180,255])
                    if tex:
                        w,h,raw=tex;u=sum(v*uv[j][0] for v,j in zip((wa,wb,wc),ids))%1;v=sum(v*uv[j][1] for v,j in zip((wa,wb,wc),ids))%1
                        offset=int(v*h)*(w*4+1)+1+int(u*w)*4;color=raw[offset:offset+4]
                    if color[3]<128:continue
                    depth[pos]=z;out[pos*4:pos*4+4]=color
    return out


def main():
    root=ROOT/'assets/animations';path=root/'Preload.dbu/0128_dave.glb'
    a,b=render(path,0),render(path,1/3);pixels=b''.join(a[y*384*4:(y+1)*384*4]+b[y*384*4:(y+1)*384*4] for y in range(384))
    (root/'tak-walk-preview.png').write_bytes(png_bytes(768,384,pixels))


if __name__=='__main__':main()
