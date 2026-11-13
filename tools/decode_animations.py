#!/usr/bin/env python3
"""Decode little-endian EQM motion banks and bake matched rigid skins to glTF."""
import bisect
import json
import math
from pathlib import Path
import re
import struct
from decode_rigs import ROOT, IDENTITY, read_glb, save_glb, add_accessor, multiply
from inspect_dbu import inspect


def read(data, fmt, offset):
    size=struct.calcsize('<'+fmt)
    if offset<0 or offset+size>len(data):raise ValueError('Truncated animation record')
    return struct.unpack_from('<'+fmt,data,offset)


def parse_bank(data):
    if data[:4]!=b'EQM\0':raise ValueError('Unsupported motion-bank signature')
    count=read(data,'H',6)[0]
    cursor=20+count*4
    if count>4096 or cursor>len(data):raise ValueError('Invalid clip directory')
    clips=[]
    for index in range(count):
        start=cursor
        read(data,'20s',cursor)
        name=data[cursor:cursor+7].split(b'\0',1)[0].decode('ascii')
        kind=data[cursor+7];frames,bones=read(data,'2H',cursor+8)
        if kind!=1:raise ValueError(f'Unsupported clip type {kind}')
        if bones>4096:raise ValueError('Invalid animation bone count')
        records=cursor+20;cursor=records+bones*60;tracks=[]
        read(data,'B',cursor-1)
        for i in range(bones):
            off=records+i*60
            name_bone=data[off:off+16].split(b'\0',1)[0].decode('ascii')
            mask,group=read(data,'2H',off+16)
            if mask & ~0x3ff:raise ValueError('Unsupported channel mask')
            rotation=list(read(data,'9f',off+20))
            if not all(math.isfinite(v) for v in rotation):raise ValueError('Invalid track matrix')
            channels={};flags=[bit for bit in range(10) if mask & (1<<bit)]
            keys=cursor+16*len(flags)
            for j,bit in enumerate(flags):
                header=cursor+j*16
                n,_,_,cached,cached_time,_=read(data,'HHIfHH',header)
                if not n:raise ValueError('Empty animated channel')
                values=[read(data,'Hh',keys+k*4) for k in range(n)]
                if any(a[0]>=b[0] for a,b in zip(values,values[1:])):raise ValueError('Non-increasing animation keys')
                scale=256/32767 if bit<3 else 128/32767 if bit<6 else 2/32767
                channels[bit]=dict(keys=[(t,v*scale) for t,v in values],raw_keys=values,
                                   source_offset=keys,cached_value=cached,cached_time=cached_time)
                keys+=4*n
            cursor=keys
            tracks.append(dict(name=name_bone,mask=mask,group=group,rotation_basis=rotation,channels=channels))
        cursor=(cursor+3)&~3
        clips.append(dict(name=name,index=index,source_offset=start,frames=frames,tracks=tracks))
    if len(data)-cursor>31 or cursor>len(data):raise ValueError(f'Unexpected motion-bank trailing bytes: {len(data)-cursor}')
    return dict(clips=clips,trailing_bytes=len(data)-cursor)


def sample(keys, time):
    if time<=keys[0][0]:return keys[0][1]
    if time>=keys[-1][0]:return keys[-1][1]
    i=bisect.bisect_right([k[0] for k in keys],time)-1
    t,a=keys[i];u,b=keys[i+1]
    return a+(b-a)*(time-t)/(u-t)


def normalize(q):
    length=math.sqrt(sum(v*v for v in q))
    if length<1e-12:return [0.,0.,0.,1.]
    return [v/length for v in q]


def quaternion(matrix):
    # Column-major orthonormal rotation to glTF xyzw quaternion.
    m=matrix;trace=m[0]+m[5]+m[10]
    if trace>0:
        s=math.sqrt(trace+1)*2;q=[(m[6]-m[9])/s,(m[8]-m[2])/s,(m[1]-m[4])/s,s/4]
    elif m[0]>m[5] and m[0]>m[10]:
        s=math.sqrt(1+m[0]-m[5]-m[10])*2;q=[s/4,(m[4]+m[1])/s,(m[8]+m[2])/s,(m[6]-m[9])/s]
    elif m[5]>m[10]:
        s=math.sqrt(1+m[5]-m[0]-m[10])*2;q=[(m[4]+m[1])/s,s/4,(m[9]+m[6])/s,(m[8]-m[2])/s]
    else:
        s=math.sqrt(1+m[10]-m[0]-m[5])*2;q=[(m[8]+m[2])/s,(m[9]+m[6])/s,s/4,(m[1]-m[4])/s]
    return normalize(q)


def compose(t,q,s):
    x,y,z,w=normalize(q)
    m=[1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w),0,
       2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w),0,
       2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y),0,*t,1]
    for k in range(3):
        for r in range(3):m[k*4+r]*=s[k]
    return m


def decompose(m):
    scale=[math.sqrt(sum(m[c*4+r]**2 for r in range(3))) for c in range(3)]
    if min(scale)<1e-10:raise ValueError('Degenerate transform')
    determinant=(m[0]*(m[5]*m[10]-m[9]*m[6])-m[4]*(m[1]*m[10]-m[9]*m[2])+m[8]*(m[1]*m[6]-m[5]*m[2]))
    if determinant<0:scale[0]*=-1
    rotation=list(m)
    for c in range(3):
        for r in range(3):rotation[c*4+r]/=scale[c]
    q=quaternion(rotation);t=list(m[12:15])
    if max(abs(a-b) for a,b in zip(compose(t,q,scale),m))>0.005:raise ValueError('Transform contains unsupported shear')
    return t,q,scale


def pose(track,time,bind_local):
    values=[0.,0.,0.,1.,1.,1.,0.,0.,0.,1.]
    for bit,ch in track['channels'].items():values[int(bit)]=sample(ch['keys'],time)
    basis=list(IDENTITY)
    for c in range(3):
        for r in range(3):basis[c*4+r]=track['rotation_basis'][c*3+r]
    _,_,base_scale=decompose(basis)
    # Both game initialization paths call 0x801EBB18 with 0.015625 (1/64).
    translation=[bind_local[12+r]+sum(basis[c*4+r]*values[c]/64 for c in range(3)) for r in range(3)]
    # Zero scale hides attachments in real clips; recover rotation independently.
    rotation_matrix=multiply(basis,compose([0.,0.,0.],values[6:10],[1.,1.,1.]))
    _,rotation,_=decompose(rotation_matrix)
    return translation,rotation,[values[3+k]*base_scale[k] for k in range(3)]


def attach_animations(source, output, skeleton, bank):
    document,blob=read_glb(source)
    bones=skeleton['bones']
    names={b['name'].lower():i for i,b in enumerate(bones)}
    for b,node in zip(bones,document['nodes'][1:]):
        t,q,s=decompose(b['local']);node.pop('matrix',None);node.update(translation=t,rotation=q,scale=s)
    animations=[];unmatched=set()
    for clip in bank['clips']:
        duration=max([t for track in clip['tracks'] for ch in track['channels'].values() for t,_ in ch['keys']]+[clip['frames']*10])
        ticks=list(range(0,duration+1,10))
        if ticks[-1]!=duration:ticks.append(duration)
        input_index=add_accessor(document,blob,[t/300 for t in ticks],1)
        animation=dict(name=clip['name'],samplers=[],channels=[])
        for track in clip['tracks']:
            index=names.get(track['name'].lower())
            if index is None:unmatched.add(track['name']);continue
            poses=[pose(track,t,bones[index]['local']) for t in ticks]
            # Choose continuous signs so glTF interpolation stays on the same quaternion arc.
            for i in range(1,len(poses)):
                if sum(a*b for a,b in zip(poses[i-1][1],poses[i][1]))<0:poses[i][1][:]=[-v for v in poses[i][1]]
            for channel,path in enumerate(('translation','rotation','scale')):
                values=[p[channel] for p in poses]
                output_index=add_accessor(document,blob,values,4 if path=='rotation' else 3)
                animation['samplers'].append(dict(input=input_index,output=output_index,interpolation='LINEAR'))
                animation['channels'].append(dict(sampler=len(animation['samplers'])-1,target=dict(node=index+1,path=path)))
        if animation['channels']:animations.append(animation)
    document['animations']=animations
    output.parent.mkdir(parents=True,exist_ok=True);save_glb(output,document,blob)
    return len(animations),sorted(unmatched)


def main():
    output=ROOT/'assets/animations';output.mkdir(parents=True,exist_ok=True)
    rigs=json.loads((ROOT/'assets/rigs/manifest.json').read_text())['entries']
    entries=[];errors=[];seen=set()
    for path in sorted((ROOT/'assets/disc').glob('*.dbu')):
        data=path.read_bytes()
        for chunk in inspect(data)['chunks']:
            if chunk['type']!='0x0100':continue
            hint=chunk.get('preceding_path_marker','')
            stem=hint.replace('\\','/').split('/')[-1].rsplit('.',1)[0].lower()
            payload=data[chunk['payload_offset']:chunk['payload_offset']+chunk['payload_size']]
            import hashlib
            digest=hashlib.sha256(payload).hexdigest()
            if digest in seen:continue
            seen.add(digest)
            row=dict(archive=path.name,chunk=chunk['index'],path_hint=hint,sha256=digest)
            try:
                bank=parse_bank(payload)
                relative=Path(path.name)/f'{chunk["index"]:04d}_{stem}.json'
                target=output/relative;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text(json.dumps(bank,separators=(',',':'))+'\n')
                row.update(json=relative.as_posix(),clips=len(bank['clips']))
                rig=next((r for r in rigs if (r.get('path_hint') or '').replace('\\','/').split('/')[-1].rsplit('.',1)[0].lower()==stem),None)
                if rig:
                    skeleton=json.loads((ROOT/'assets/rigs'/rig['skeleton']).read_text())
                    glb=relative.with_suffix('.glb')
                    count,unmatched=attach_animations(ROOT/'assets/rigs'/rig['glb'],output/glb,skeleton,bank)
                    row.update(glb=glb.as_posix(),animated_clips=count,unmatched_tracks=unmatched,rig=rig['glb'])
                entries.append(row)
            except (ValueError,struct.error) as error:errors.append(dict(**row,error=str(error)))
        print(path.name,flush=True)
    (output/'manifest.json').write_text(json.dumps(dict(entries=entries,errors=errors,
        limitations='Motion tracks sampled at 30 Hz from 300 Hz keys. Standalone clips; no gameplay blending, IK, mirrored motions or effects. Unmatched tracks are reported.'),indent=2)+'\n')
    print(f'Decoded {len(entries)} unique banks; {sum(e["clips"] for e in entries)} clips; {len(errors)} unresolved banks')


if __name__=='__main__':main()
