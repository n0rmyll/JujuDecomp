import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from decode_rigs import IDENTITY, multiply, invert, decode_skeleton, attach_skin, read_glb
from decode_models import write_glb
from decode_animations import parse_bank,sample,compose,decompose,pose,clip_poses,slerp,attach_animations


def skeleton_fixture():
    data=bytearray(32+480+160)
    data[0]=19;struct.pack_into('>H',data,2,0x40)
    struct.pack_into('>I',data,0x90,160)
    for i in range(2):
        offset=160+240*i;matrix=list(IDENTITY);matrix[12]=i*2
        struct.pack_into('>16f',data,offset,*matrix)
        inverse=list(IDENTITY);inverse[12]=-i*2
        struct.pack_into('>16f',data,offset+64,*inverse)
        data[offset+176:offset+181]=b'root\0' if i==0 else b'hand\0'
        data[offset+201]=i
    struct.pack_into('>I',data,160+128,1)
    return data


class RigTests(unittest.TestCase):
    def test_helper_metadata(self):
        data=skeleton_fixture()
        data[160+240+202:160+240+208]=bytes((1,25,50,75,1,0))
        bone=decode_skeleton(data)['bones'][1]
        self.assertEqual(bone['helper'],dict(mode=1,x=25,y=50,z=75,target=1,second_target=0))
        self.assertEqual(bone['pivot'],[0,0,0])

    def test_helper_rotation_about_object_pivot(self):
        # A translated parent distinguishes object-space skin deltas from joint TRS.
        import math
        def bone(index,parent,x,helper=None):
            bind=compose([x,0,0],[0,0,0,1],[1,1,1])
            return dict(index=index,source_id=index+1,name=f'b{index}',parent=parent,
                        bind=bind,inverse_bind=invert(bind),local=compose([x-(3 if parent==0 else 0),0,0],[0,0,0,1],[1,1,1]),
                        pivot=[x,0,0],helper=helper or {})
        bones=[bone(0,None,3),bone(1,0,5),bone(2,0,7,dict(mode=0,x=50,y=0,z=0,target=2,second_target=0))]
        track=dict(name='b1',rotation_basis=[1,0,0,0,1,0,0,0,1],channels={8:dict(keys=[(0,math.sqrt(.5))]),9:dict(keys=[(0,math.sqrt(.5))])})
        poses=clip_poses(bones,[track],0)
        delta=multiply(bones[0]['bind'],multiply(compose(*poses[2]),bones[2]['inverse_bind']))
        # Half of 90 degrees, preserving the helper's object-space pivot at x=7.
        self.assertAlmostEqual(delta[0],math.sqrt(.5))
        self.assertAlmostEqual(delta[1],math.sqrt(.5))
        self.assertAlmostEqual(delta[0]*7+delta[12],7)
        self.assertAlmostEqual(delta[1]*7+delta[13],0)
        bones[2]['helper'].update(mode=1,x=0,y=0,z=50)
        delta=multiply(bones[0]['bind'],multiply(compose(*clip_poses(bones,[track],0)[2]),bones[2]['inverse_bind']))
        self.assertAlmostEqual(delta[0],7/9)
        self.assertAlmostEqual(delta[1],4*math.sqrt(2)/9)
        # Blend the 45-degree first reference with a zero-weight identity second one.
        bones[2]['helper'].update(mode=0,x=50,y=50,z=0,second_target=1)
        delta=multiply(bones[0]['bind'],multiply(compose(*clip_poses(bones,[track],0)[2]),bones[2]['inverse_bind']))
        self.assertAlmostEqual(delta[0],math.cos(math.pi/8))
        self.assertAlmostEqual(delta[1],math.sin(math.pi/8))
        # X-only mode discards a reference's Z rotation.
        bones[2]['helper'].update(x=0,y=0,z=50,second_target=0)
        delta=multiply(bones[0]['bind'],multiply(compose(*clip_poses(bones,[track],0)[2]),bones[2]['inverse_bind']))
        for a,b in zip(delta,IDENTITY):self.assertAlmostEqual(a,b)
        bones[2]['helper']['target']=3
        with self.assertRaisesRegex(ValueError,'Cyclic'):clip_poses(bones,[track],0)
        bones[2]['helper']['target']=99
        with self.assertRaisesRegex(ValueError,'missing'):clip_poses(bones,[track],0)

    def test_slerp_shortest_arc(self):
        import math
        q=slerp([0,0,0,1],[0,0,-math.sqrt(.5),-math.sqrt(.5)],.5)
        self.assertAlmostEqual(q[2],math.sin(math.pi/8))
        self.assertAlmostEqual(q[3],math.cos(math.pi/8))

    def test_inverse_and_hierarchy(self):
        skeleton=decode_skeleton(skeleton_fixture())
        self.assertEqual([b['parent'] for b in skeleton['bones']],[None,0])
        self.assertEqual(skeleton['bones'][1]['local'][12],2)
        matrix=compose([3,4,5],[0,0,0,1],[2,3,4])
        for a,b in zip(multiply(matrix,invert(matrix)),IDENTITY):self.assertAlmostEqual(a,b)

    def test_skeleton_corruption(self):
        for offset,raw in ((160+128,struct.pack('>I',9999)),(160+240+132,struct.pack('>I',1)),(160,b'\0'*64)):
            data=skeleton_fixture();data[offset:offset+len(raw)]=raw
            with self.assertRaises(ValueError):decode_skeleton(data)

    def test_glb_joints_weights_and_inverse_bind(self):
        skeleton=decode_skeleton(skeleton_fixture())
        mesh=dict(name='test',vertices=[dict(position=(0,0,0),normal=None,uv=None,joint=j) for j in (0,1,1)],
                  primitives=[dict(material_index=0,indices=[0,1,2])])
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'test.glb';write_glb(mesh,path);attach_skin(path,mesh,skeleton)
            g,binary=read_glb(path);self.assertEqual(g['skins'][0]['joints'],[1,2])
            p=g['meshes'][0]['primitives'][0]
            a=g['accessors'][p['attributes']['JOINTS_0']];v=g['bufferViews'][a['bufferView']]
            self.assertEqual(a['componentType'],5123)
            self.assertEqual(struct.unpack_from('<12H',binary,v['byteOffset']),(0,0,0,0,1,0,0,0,1,0,0,0))
            skeleton['bones'][1]['helper'].update(target=1,x=50)
            bank=dict(clips=[dict(name='unbound',frames=1,tracks=[dict(name='missing',channels={})])])
            output=Path(temp)/'animated.glb'
            count,unmatched=attach_animations(path,output,skeleton,bank)
            self.assertEqual((count,unmatched),(0,['missing']))
            self.assertEqual(read_glb(output)[0]['animations'],[])

    def test_clip_parsing_and_quantization(self):
        data=bytearray(128);data[:4]=b'EQM\0';struct.pack_into('<H',data,6,1)
        data[24:32]=b'WALK\0\0\0\1';struct.pack_into('<2H',data,32,2,1)
        data[44:49]=b'hand\0';struct.pack_into('<H',data,60,1)
        struct.pack_into('<9f',data,64,1,0,0,0,1,0,0,0,1)
        struct.pack_into('<H',data,104,2)
        struct.pack_into('<HhHh',data,120,0,0,20,128)
        bank=parse_bank(data);track=bank['clips'][0]['tracks'][0]
        self.assertAlmostEqual(sample(track['channels'][0]['keys'],10),64*256/32767)
        t,q,s=pose(track,10,IDENTITY)
        self.assertAlmostEqual(t[0],256/32767);self.assertEqual(q,[0,0,0,1])
        with self.assertRaises(ValueError):parse_bank(data[:-4])

    def test_sampler_and_trs_roundtrip(self):
        self.assertEqual(sample([(0,2),(20,6)],10),4)
        self.assertEqual(sample([(0,2),(20,6)],-1),2)
        self.assertEqual(sample([(0,2),(20,6)],21),6)
        m=compose([1,2,3],[0,0,0.70710678,0.70710678],[2,3,4]);t,q,s=decompose(m)
        for a,b in zip(compose(t,q,s),m):self.assertAlmostEqual(a,b)
        hidden=dict(rotation_basis=[1,0,0,0,1,0,0,0,1],channels={4:dict(keys=[(0,0),(10,0)])})
        self.assertEqual(pose(hidden,0,IDENTITY)[2],[1,0,1])

    def test_real_tak_bind_skin(self):
        root=Path(__file__).resolve().parents[1]/'assets/rigs'
        manifest=root/'manifest.json'
        if not manifest.exists():self.skipTest('Local rigs unavailable')
        row=next((e for e in json.loads(manifest.read_text())['entries'] if e['name']=='Tak_meshShape'),None)
        if row is None:self.skipTest('Local Tak rig unavailable')
        bones=json.loads((root/row['skeleton']).read_text())['bones']
        self.assertEqual(len(bones),137)
        for bone in bones:
            for a,b in zip(multiply(bone['bind'],bone['inverse_bind']),IDENTITY):self.assertAlmostEqual(a,b,places=5)


if __name__=='__main__':unittest.main()
