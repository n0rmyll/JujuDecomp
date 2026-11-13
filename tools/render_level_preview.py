#!/usr/bin/env python3
"""Independently rasterize static GLB scene nodes using their exported matrices."""
import argparse
import math
from pathlib import Path
import struct
import zlib
from decode_level import accessor_values
from decode_rigs import ROOT,read_glb
from decode_textures import png_bytes


def embedded_png(raw):
    if raw[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Expected PNG image')
    width,height,bits,color=struct.unpack_from('>IIBB',raw,16)
    if (bits,color)!=(8,6):raise ValueError('Expected exported RGBA8 texture')
    compressed=bytearray();cursor=8
    while cursor<len(raw):
        size=struct.unpack_from('>I',raw,cursor)[0]
        if raw[cursor+4:cursor+8]==b'IDAT':compressed.extend(raw[cursor+8:cursor+8+size])
        cursor+=size+12
    pixels=zlib.decompress(compressed);stride=width*4+1
    if len(pixels)!=stride*height or any(pixels[y*stride] for y in range(height)):
        raise ValueError('Expected unfiltered exporter PNG rows')
    return width,height,pixels


def render(path,size=1024,top=False,all_records=False,instance_indices=None):
    g,blob=read_glb(path);cache={}
    def accessor(i):
        if i not in cache:cache[i]=accessor_values(g,blob,i)
        return cache[i]
    textures=[]
    for image in g.get('images',[]):
        v=g['bufferViews'][image['bufferView']];offset=v.get('byteOffset',0)
        textures.append(embedded_png(blob[offset:offset+v['byteLength']]))
    meshes=[]
    for mesh in g['meshes']:
        parts=[]
        for p in mesh['primitives']:
            a=p['attributes'];mat=g['materials'][p['material']];texture=mat['pbrMetallicRoughness'].get('baseColorTexture')
            parts.append(dict(position=a['POSITION'],indices=[v[0] for v in accessor(p['indices'])],
                              uv=accessor(a['TEXCOORD_0']) if 'TEXCOORD_0' in a else None,
                              texture=textures[g['textures'][texture['index']]['source']] if texture else None))
        meshes.append(parts)
    yaw=-.65;pitch=math.pi/2 if top else .65
    sy,cy,sp,cp=math.sin(yaw),math.cos(yaw),math.sin(pitch),math.cos(pitch)
    def camera(p):
        x,y,z=p;right=x*cy-z*sy;back=x*sy+z*cy
        return right,y*cp-back*sp,y*sp+back*cp
    selected=[n for n in g['nodes'] if 'mesh' in n and (instance_indices is None or n.get('extras',{}).get('instanceIndex') in instance_indices)]
    bounds=g['extras']['bounds' if all_records else 'preview_bounds']
    if instance_indices is not None:
        if not selected:raise ValueError('No matching instances')
        lo=[math.inf]*3;hi=[-math.inf]*3
        for node in selected:
            m=node['matrix']
            for part in meshes[node['mesh']]:
                for p in accessor(part['position']):
                    for k in range(3):
                        x=sum(m[c*4+k]*p[c] for c in range(3))+m[12+k];lo[k]=min(lo[k],x);hi[k]=max(hi[k],x)
        bounds=dict(min=lo,max=hi)
    corners=[camera([bounds['max' if mask&(1<<k) else 'min'][k] for k in range(3)]) for mask in range(8)]
    lo=[min(p[k] for p in corners) for k in range(3)];hi=[max(p[k] for p in corners) for k in range(3)]
    width=size;height=round(size*.75);scale=min((width-40)/max(1e-6,hi[0]-lo[0]),(height-40)/max(1e-6,hi[1]-lo[1]));cx=(lo[0]+hi[0])/2;cy2=(lo[1]+hi[1])/2
    pixels=bytearray(bytes((36,46,57,255))*(width*height));depth=[-math.inf]*(width*height);triangle_count=0
    for node in selected:
        if 'mesh' not in node:continue
        if not all_records and node.get('extras',{}).get('previewGroup','scenery') not in ('scenery','actors'):continue
        if node.get('children') or 'matrix' not in node:raise ValueError('Expected flat matrix-authored nodes')
        m=node['matrix'];projected={}
        for part in meshes[node['mesh']]:
            key=part['position']
            if key not in projected:
                points=[]
                for p in accessor(key):
                    world=[sum(m[c*4+k]*p[c] for c in range(3))+m[12+k] for k in range(3)]
                    x,y,z=camera(world);points.append((width/2+(x-cx)*scale,height/2-(y-cy2)*scale,z))
                projected[key]=points
            points=projected[key];indices=part['indices'];tex=part['texture'];uv=part['uv']
            for i in range(0,len(indices),3):
                ids=indices[i:i+3];a,b,c=[points[j] for j in ids];det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                triangle_count+=1
                if abs(det)<1e-9:continue
                # Screen-space normal gives a subtle shape cue without game lighting.
                ab=[b[k]-a[k] for k in range(3)];ac=[c[k]-a[k] for k in range(3)]
                normal=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
                light=.65+.35*abs(normal[2])/(math.hypot(*normal) or 1)
                if tex and uv:
                    tw,th,raw=tex;us=[uv[j][0] for j in ids];vs=[uv[j][1] for j in ids]
                for y in range(max(0,math.floor(min(a[1],b[1],c[1]))),min(height,math.ceil(max(a[1],b[1],c[1])))):
                    for x in range(max(0,math.floor(min(a[0],b[0],c[0]))),min(width,math.ceil(max(a[0],b[0],c[0])))):
                        wa=((b[1]-c[1])*(x+.5-c[0])+(c[0]-b[0])*(y+.5-c[1]))/det
                        wb=((c[1]-a[1])*(x+.5-c[0])+(a[0]-c[0])*(y+.5-c[1]))/det;wc=1-wa-wb
                        if min(wa,wb,wc)<-1e-8:continue
                        z=wa*a[2]+wb*b[2]+wc*c[2];offset=y*width+x
                        if z<=depth[offset]:continue
                        color=(170,180,190,255)
                        if tex and uv:
                            u=(wa*us[0]+wb*us[1]+wc*us[2])%1;v=(wa*vs[0]+wb*vs[1]+wc*vs[2])%1
                            at=int(v*th)*(tw*4+1)+1+int(u*tw)*4;color=raw[at:at+4]
                        if color[3]<128:continue
                        pixels[offset*4:offset*4+4]=bytes([round(color[k]*light) for k in range(3)]+[255]);depth[offset]=z
    return png_bytes(width,height,pixels),triangle_count


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',nargs='?',type=Path,default=ROOT/'assets/levels/Hub/Hub.glb')
    parser.add_argument('--output',type=Path,default=ROOT/'assets/levels/Hub/preview.png')
    parser.add_argument('--size',type=int,default=1024);parser.add_argument('--top',action='store_true')
    parser.add_argument('--all',action='store_true',help='Include sky, backdrop and named helpers')
    parser.add_argument('--instance',type=int,action='append',help='Render and frame only these placement indices');args=parser.parse_args()
    png,count=render(args.glb,args.size,args.top,args.all,args.instance);args.output.write_bytes(png)
    print(f'Rendered {count} placed triangles to {args.output}')


if __name__=='__main__':main()
