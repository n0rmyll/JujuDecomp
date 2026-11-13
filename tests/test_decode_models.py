import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from decode_models import decode_mesh, triangles, write_glb
from inspect_dbu import inspect


def model_fixture(wide=False):
    data = bytearray(400)
    data[0] = 19
    data[48:52] = b'test'
    struct.pack_into('>2I', data, 0x50, 3, 320)
    struct.pack_into('>2I', data, 0x74, 1, 160)
    struct.pack_into('>9f', data, 320, 0, 0, 0, 1, 0, 0, 0, 1, 0)
    commands = bytes([8, 0x50])+struct.pack('>I', (3 if wide else 2)<<9)
    commands += bytes([8, 0x60])+bytes(4)
    commands += bytes([0x93, 0, 3])+(struct.pack('>3H', 0, 1, 2) if wide else bytes([0, 1, 2]))
    struct.pack_into('>I', data, 180, len(commands))
    data[192:192+len(commands)] = commands
    return data


class ModelTests(unittest.TestCase):
    def test_triangle_winding(self):
        self.assertEqual(triangles(0x98, 5), [(0, 1, 2), (2, 1, 3), (2, 3, 4)])
        self.assertEqual(triangles(0xa0, 4), [(0, 1, 2), (0, 2, 3)])
        self.assertEqual(triangles(0x80, 4), [(0, 1, 2), (0, 2, 3)])
        with self.assertRaises(ValueError):
            triangles(0x90, 4)

    def test_index_widths_and_positions(self):
        for wide in (False, True):
            mesh = decode_mesh(model_fixture(wide))
            self.assertEqual([v['position'] for v in mesh['vertices']], [(0, 0, 0), (1, 0, 0), (0, 1, 0)])
            self.assertEqual(mesh['primitives'][0]['indices'], [0, 1, 2])

    def test_reject_bad_ranges_indices_commands_and_cycle(self):
        changes = [(0x54, struct.pack('>I', 399)), (0x78, struct.pack('>I', 399)),
                   (192, b'\x7f'), (207, b'\x09')]
        for offset, raw in changes:
            data = model_fixture()
            data[offset:offset+len(raw)] = raw
            with self.assertRaises(ValueError):
                decode_mesh(data)
        data = model_fixture()
        struct.pack_into('>I', data, 160, 0xfffffff0)
        with self.assertRaises(ValueError):
            decode_mesh(data)

    def test_glb_buffers_and_indices(self):
        mesh = decode_mesh(model_fixture())
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'test.glb'
            write_glb(mesh, path)
            data = path.read_bytes()
            magic, version, length, json_size = struct.unpack_from('<4I', data)
            self.assertEqual((magic, version, length), (0x46546c67, 2, len(data)))
            document = json.loads(data[20:20+json_size])
            binary = data[28+json_size:]
            for view in document['bufferViews']:
                self.assertEqual(view['byteOffset']%4, 0)
                self.assertLessEqual(view['byteOffset']+view['byteLength'], len(binary))
            prim = document['meshes'][0]['primitives'][0]
            accessor = document['accessors'][prim['indices']]
            view = document['bufferViews'][accessor['bufferView']]
            self.assertEqual(struct.unpack_from('<3I', binary, view['byteOffset']), (0, 1, 2))

    def test_real_coconut_closed_surface(self):
        path = Path(__file__).resolve().parents[1]/'assets/disc/Preload.dbu'
        if not path.exists():
            self.skipTest('Local archive unavailable')
        data = path.read_bytes()
        chunk = next(c for c in inspect(data)['chunks'] if c['type'] == '0x0020'
                     and c.get('preceding_path_marker') == 'weapons\\coconut.dbl')
        mesh = decode_mesh(data[chunk['payload_offset']:chunk['payload_offset']+chunk['payload_size']])
        indices = mesh['primitives'][0]['indices']
        from collections import Counter
        edges = Counter(tuple(sorted((a, b))) for i in range(0, len(indices), 3)
                        for a, b in ((indices[i], indices[i+1]), (indices[i+1], indices[i+2]),
                                     (indices[i+2], indices[i])))
        self.assertEqual((len(mesh['vertices']), len(indices)//3, len(edges)), (42, 80, 120))
        self.assertTrue(all(n == 2 for n in edges.values()))
        self.assertEqual(len(mesh['vertices'])-len(edges)+len(indices)//3, 2)


if __name__ == '__main__':
    unittest.main()
