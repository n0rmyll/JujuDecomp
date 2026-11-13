import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from decode_level_actors import padded_string,actor_prefixes,resolve_assets,resolve_level_actors,replacement_path
from decode_level import SceneBuilder,accessor_values
from decode_rigs import IDENTITY,attach_skin,read_glb,save_glb
from decode_models import write_glb
from inspect_dbu import inspect


def string(value):
    raw=value.encode('ascii')+b'\0'
    return raw+b'\xee'*((-len(raw))%4)


class ActorTests(unittest.TestCase):
    def test_padded_prefix_and_exact_instance_anchor(self):
        prefix=string('chicken')+string('Bird_01')+string('chicken')
        payload=bytes(16)+prefix+string('superchicken')+string('Bird_02')+string('chicken')
        rows=actor_prefixes(payload,{'bird_01':[5],'bird_02':[6]})
        self.assertEqual(len(rows),1)
        row=rows[0];self.assertEqual(row['instance_indices'],[5]);self.assertEqual(row['record_offset'],16)
        self.assertEqual(padded_string(payload,row['override_offset'])[0],'chicken')
        self.assertEqual(actor_prefixes(payload,{'other':[5]}),[])
        self.assertEqual(padded_string(bytes(4),0),('',4))

    def test_reject_bad_environment_strings(self):
        for data,offset in ((b'abcd',0),(b'x\0',0),(b'\xff\0\xee\xee',0),(b'\0'*8,1)):
            with self.assertRaises(ValueError):padded_string(data,offset)
        self.assertIsNone(replacement_path('None'));self.assertIsNone(replacement_path('../chicken'))
        self.assertEqual(replacement_path('Chicken'),'replace\\chicken.dbl')

    def test_asset_scope_fallback_and_ambiguity(self):
        prefix=dict(actor_class='chicken',instance_name='Bird',model_override='chicken',instance_indices=[5])
        rows=[dict(index=5,box_proxy_candidate=True)]
        def asset(archive):return dict(archive=archive,category='models',glb='bird.glb',name='bird',chunk=2,index=0,path_hint='replace\\chicken.dbl',archive_sha256='abc')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'models').mkdir();(root/'models/bird.glb').write_bytes(b'fixture')
            entries=[asset('OtherLevel.dbu'),asset('Preload.dbu'),asset('Hub.dbu')]
            bindings,errors=resolve_assets([prefix],rows,entries,'Hub.dbu',root)
            self.assertEqual(bindings[5]['asset_archive'],'Hub.dbu');self.assertEqual(errors,[])
            bindings,_=resolve_assets([prefix],rows,entries[:2],'Hub.dbu',root)
            self.assertEqual(bindings[5]['asset_archive'],'Preload.dbu')
            bindings,errors=resolve_assets([prefix],rows,[asset('Hub.dbu')]*2,'Hub.dbu',root)
            self.assertEqual(bindings,{});self.assertIn('ambiguous',errors[0]['reason'])
            ambiguous=dict(prefix,instance_indices=[5,6]);bindings,errors=resolve_assets([ambiguous],rows,entries,'Hub.dbu',root)
            self.assertEqual(bindings,{});self.assertIn('Ambiguous',errors[0]['reason'])
            missing=dict(prefix,model_override='None');bindings,errors=resolve_assets([missing],rows,entries,'Hub.dbu',root)
            self.assertEqual(bindings,{});self.assertIn('explicit',errors[0]['reason'])

    def test_freeze_validated_bind_pose_without_skin_attributes(self):
        mesh=dict(name='actor',vertices=[dict(position=p,uv=None,normal=(0,0,1),joint=0) for p in ((0,0,0),(1,0,0),(0,1,0))],
                  primitives=[dict(material_index=0,indices=[0,1,2])])
        bone=dict(index=0,source_id=0,parent=None,name='root',bind=IDENTITY,inverse_bind=IDENTITY,local=IDENTITY)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'actor.glb';write_glb(mesh,path);attach_skin(path,mesh,dict(bones=[bone]))
            builder=SceneBuilder()
            with self.assertRaises(ValueError):builder.add_mesh(path)
            index=builder.add_mesh(path,bind_pose=True);p=builder.g['meshes'][index]['primitives'][0]
            self.assertNotIn('JOINTS_0',p['attributes']);self.assertNotIn('WEIGHTS_0',p['attributes'])
            self.assertEqual(accessor_values(builder.g,builder.blob,p['attributes']['POSITION']),[(0,0,0),(1,0,0),(0,1,0)])
            g,b=read_glb(path);a=g['accessors'][g['skins'][0]['inverseBindMatrices']];v=g['bufferViews'][a['bufferView']]
            struct.pack_into('<f',b,v['byteOffset'],2);save_glb(path,g,b)
            with self.assertRaisesRegex(ValueError,'Bind'):SceneBuilder().add_mesh(path,bind_pose=True)

    def test_real_hub_actor_bindings(self):
        root=Path(__file__).resolve().parents[1];path=root/'assets/disc/Hub.dbu';manifest=root/'assets/levels/Hub/manifest.json'
        if not path.exists() or not manifest.exists():self.skipTest('Local Hub unavailable')
        raw=path.read_bytes();chunks=inspect(raw)['chunks'];rows=json.loads(manifest.read_text())['instances']
        bindings,report=resolve_level_actors(raw,chunks,chunks[179],rows,'Hub.dbu')
        self.assertEqual(len(bindings),20);self.assertEqual(report['unresolved'],[])
        self.assertEqual({i:b['actor_class'] for i,b in bindings.items() if b['actor_class'] in ('chicken','monkey','rhino')},
                         {1678:'chicken',1679:'chicken',1763:'monkey',1872:'rhino'})
        self.assertEqual(bindings[1764]['asset_archive'],'Preload.dbu')
        self.assertEqual(bindings[1871]['asset_category'],'models')
        self.assertEqual(len({(b['asset_category'],b['asset_glb']) for b in bindings.values()}),8)


if __name__=='__main__':unittest.main()
