import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from decode_rigs import IDENTITY, multiply, invert, decode_skeleton, attach_skin, read_glb
from decode_models import write_glb
from decode_animations import parse_bank,sample,compose,decompose,pose


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
