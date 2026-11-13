import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from decode_level import decode_instances,SceneBuilder,accessor_values,preview_group
from decode_models import write_glb
from decode_rigs import IDENTITY,save_glb,read_glb
from decode_textures import png_bytes
from inspect_dbu import inspect


def fixture():
    data=bytearray(16+176+24)
    struct.pack_into('>HHI',data,0,1,10,176)
    struct.pack_into('>16f',data,16+16,*IDENTITY)
    struct.pack_into('>6f',data,16+0x60,-1,-1,-1,1,1,1)
    struct.pack_into('>I',data,16+0x94,176)
    struct.pack_into('>I',data,16+176+0x14,0xffffffff)
    return data


class LevelTests(unittest.TestCase):
    def test_instance_matrix_and_resource_tag(self):
        data=fixture();matrix=list(IDENTITY);matrix[0]=2;matrix[5]=3;matrix[10]=-4;matrix[12:15]=[5,6,7]
        struct.pack_into('>16f',data,32,*matrix);struct.pack_into('>I',data,16+0x78,0xab000002)
        row=decode_instances(data,3)[0]
        self.assertEqual(row['model_index'],2);self.assertEqual(row['model_reference'],0xab000002)
        self.assertEqual(row['matrix'],matrix);self.assertIsNone(row['parent'])

    def test_reject_unsupported_or_corrupt_instances(self):
        for offset,raw in ((2,struct.pack('>H',2)),(4,struct.pack('>I',175)),
                           (16+2,struct.pack('>H',4)),(16+0x78,struct.pack('>I',3)),
                           (32,struct.pack('>f',math.nan)),(32+12,struct.pack('>f',1)),
                           (16+0x94,struct.pack('>I',100000)),(16+176+20,bytes(4))):
            with self.subTest(offset=offset):
                data=fixture();data[offset:offset+len(raw)]=raw
                with self.assertRaises(ValueError):decode_instances(data,3)
        with self.assertRaises(ValueError):decode_instances(fixture()[:-1],3)

    def test_mesh_merge_references_texture_dedup_and_placement(self):
        vertices=[dict(position=p,uv=uv,normal=(0,0,1),joint=None) for p,uv in zip(((0,0,0),(1,0,0),(0,1,0)),((0,0),(1,0),(0,1)))]
        mesh=dict(name='test',vertices=vertices,primitives=[dict(indices=[0,1,2],material_index=0)])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);png=root/'image.png';png.write_bytes(png_bytes(1,1,bytes((255,0,0,255))))
            source=root/'source.glb';write_glb(mesh,source,{0:png})
            builder=SceneBuilder();a=builder.add_mesh(source);b=builder.add_mesh(source)
            self.assertEqual((a,b),(0,1));self.assertEqual(len(builder.g['images']),1)
            self.assertEqual(len(builder.g['materials']),1)
            # 90-degree Z rotation with nonuniform scale, followed by translation.
            matrix=[0,2,0,0,-3,0,0,0,0,0,4,0,10,2,3,1]
            for index,mi in enumerate((a,a,b)):
                row=dict(index=index,matrix=matrix,model_name='test',source_offset=16,flags=0,model_index=mi,
                         preview_group='scenery',source_bounds=dict(min=[7,2,3],max=[10,4,3]))
                builder.add_instance(row,mi)
                self.assertEqual(row['export_bounds'],dict(min=[7,2,3],max=[10,4,3]))
                self.assertEqual(row['bounds_overflow'],0)
            target=root/'scene.glb';save_glb(target,builder.g,builder.blob);g,blob=read_glb(target)
            self.assertEqual([n['mesh'] for n in g['nodes']],[0,0,1]);self.assertEqual(g['scenes'][0]['nodes'],[0,1,2])
            for m in g['meshes']:
                primitive=m['primitives'][0]
                self.assertEqual(accessor_values(g,blob,primitive['attributes']['POSITION']),[(0,0,0),(1,0,0),(0,1,0)])
                self.assertEqual(accessor_values(g,blob,primitive['indices']),[(0,),(1,),(2,)])

    def test_preview_filters_do_not_define_engine_visibility(self):
        for name,group in (('SkydomeShape1','sky'),('Background_Trees','backdrop'),('Coll_Core','helper'),('CanopyShape','canopy'),('Terrain','scenery')):
            self.assertEqual(preview_group(name),group)

    def test_real_hub_placements(self):
        root=Path(__file__).resolve().parents[1];path=root/'assets/disc/Hub.dbu'
        if not path.exists():self.skipTest('Local Hub unavailable')
        data=path.read_bytes();chunks=inspect(data)['chunks'];chunk=next(c for c in chunks if c['type']=='0x0060')
        payload=data[chunk['payload_offset']:chunk['payload_offset']+chunk['payload_size']];rows=decode_instances(payload,1017)
        self.assertEqual(len(rows),1888);self.assertEqual({r['model_index'] for r in rows},set(range(1017)))
        self.assertEqual(rows[0]['matrix'][12:15],[-39.300331115722656,0.5374190211296082,33.83863830566406])
        self.assertTrue(all(r['parent'] is None for r in rows))


if __name__=='__main__':unittest.main()
