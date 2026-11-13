#!/usr/bin/env python3
"""Render the exported coconut GLB as a small orthographic texture preview."""
import json
import math
from pathlib import Path
import struct
import zlib
from decode_textures import png_bytes

ROOT = Path(__file__).resolve().parents[1]


def main():
    root = ROOT/'assets/models'
    report = json.loads((root/'manifest.json').read_text())
    entry = next(e for e in report['entries'] if e['archive']=='Preload.dbu' and e['path_hint']=='weapons\\coconut.dbl')
    data = (root/entry['glb']).read_bytes()
    n = struct.unpack_from('<I', data, 12)[0]
    g = json.loads(data[20:20+n]); binary = data[28+n:]

    def access(index, fmt, width):
        a = g['accessors'][index]; v = g['bufferViews'][a['bufferView']]
        return [struct.unpack_from('<'+fmt*width, binary, v['byteOffset']+i*width*struct.calcsize(fmt)) for i in range(a['count'])]

    primitive = g['meshes'][0]['primitives'][0]
    positions = access(primitive['attributes']['POSITION'], 'f', 3)
    uv = access(primitive['attributes']['TEXCOORD_0'], 'f', 2)
    indices = [a[0] for a in access(primitive['indices'], 'I', 1)]
    image = g['images'][0]; v = g['bufferViews'][image['bufferView']]
    png = binary[v['byteOffset']:v['byteOffset']+v['byteLength']]
    tw, th = struct.unpack_from('>2I', png, 16)
    cursor=8; compressed=b''
    while cursor < len(png):
        length=struct.unpack_from('>I',png,cursor)[0]
        if png[cursor+4:cursor+8]==b'IDAT':compressed+=png[cursor+8:cursor+8+length]
        cursor+=12+length
    tex=zlib.decompress(compressed)
    assert all(tex[y*(tw*4+1)]==0 for y in range(th)), 'Expected exporter unfiltered RGBA PNG'
    minimum=[min(p[k] for p in positions) for k in range(3)]
    maximum=[max(p[k] for p in positions) for k in range(3)]
    center=[(a+b)/2 for a,b in zip(minimum,maximum)]
    scale=190/max(b-a for a,b in zip(minimum,maximum))
    projected=[]
    for p in positions:
        x,y,z=[p[k]-center[k] for k in range(3)]
        x,z=x*math.cos(.65)+z*math.sin(.65),-x*math.sin(.65)+z*math.cos(.65)
        y,z=y*math.cos(.25)-z*math.sin(.25),y*math.sin(.25)+z*math.cos(.25)
        projected.append((128+x*scale,128-y*scale,z))
    out=bytearray(bytes([37,42,51,255])*256*256); depth=[-math.inf]*(256*256)
    for i in range(0,len(indices),3):
        ids=indices[i:i+3]; a,b,c=[projected[j] for j in ids]
        det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(det)<1e-9:continue
        for y in range(max(0,int(min(a[1],b[1],c[1]))),min(256,math.ceil(max(a[1],b[1],c[1])))):
            for x in range(max(0,int(min(a[0],b[0],c[0]))),min(256,math.ceil(max(a[0],b[0],c[0])))):
                wa=((b[1]-c[1])*(x+.5-c[0])+(c[0]-b[0])*(y+.5-c[1]))/det
                wb=((c[1]-a[1])*(x+.5-c[0])+(a[0]-c[0])*(y+.5-c[1]))/det
                wc=1-wa-wb
                if min(wa,wb,wc)<0:continue
                z=wa*a[2]+wb*b[2]+wc*c[2]; pos=y*256+x
                if z<=depth[pos]:continue
                u=sum(w*uv[j][0] for w,j in zip((wa,wb,wc),ids))%1
                vv=sum(w*uv[j][1] for w,j in zip((wa,wb,wc),ids))%1
                offset=int(vv*th)*(tw*4+1)+1+int(u*tw)*4
                color=tex[offset:offset+4]
                if color[3]<128:continue
                depth[pos]=z;out[pos*4:pos*4+4]=color
    (root/'preview.png').write_bytes(png_bytes(256,256,out))


if __name__=='__main__':
    main()
